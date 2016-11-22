# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2015 Daniel Miller <millerdev@gmail.com>
#
# This file is part of EditXT, a programmer's text editor for Mac OS X,
# which can be found at http://editxt.org/.
#
# EditXT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EditXT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EditXT.  If not, see <http://www.gnu.org/licenses/>.
import AppKit as ak
import Foundation as fn
from objc import NULL

from editxt.command.find import Match


class Text(object):
    """Text storage class

    All indexes used by this class are hexichar indexes (what Apple
    calls *unichar*), which are UTF-16-encoded code units.
    See https://www.objc.io/issues/9-strings/unicode/ for more details.
    """

    def __init__(self, value=""):
        self.store = ak.NSTextStorage.alloc() \
            .initWithString_attributes_(value, {})
        self._delegate = TextStorageDelegate.alloc().init_(self.store)
        self._surrogates = []
        def prune_surrogates(rng):
            items = self._surrogates
            if items is None:
                rng = self.string().rangeOfCharacterFromSet_options_range_(
                        UNICODE_SUPPLEMENTARY_PLANES, 0, rng)
                if rng[0] != ak.NSNotFound:
                    self._surrogates = [rng[0]]
            else:
                start = rng[0]
                while items and items[-1] > start:
                    items.pop()
        self.on_edit(prune_surrogates)

    def on_edit(self, callback):
        return self._delegate.register_edit_callback(callback)

    def __getattr__(self, name):
        # TODO remove this
        # - python code should not need direct access to NSTextStorage
        # - all non-python code should use self.store directly
        return getattr(self.store, name)

    def __getitem__(self, index):
        """Get a string for the given index or slice

        Index must be a hexichar index. In the case of slices or ranges,
        all must use hexichar indices.
        """
        string = self.store.string()
        rng = index_to_range(index, string.length())
        return string.substringWithRange_(rng)

    def __setitem__(self, index, value):
        rng = index_to_range(index, len(self))
        if isinstance(value, Text):
            value = value.store
        if isinstance(value, ak.NSAttributedString):
            self.store.replaceCharactersInRange_withAttributedString_(rng, value)
        else:
            self.store.replaceCharactersInRange_withString_(rng, value)

    def __contains__(self, value):
        return self.store.string().containsString_(value)

    def __len__(self):
        return self.store.length()

    def __str__(self):
        return self.store.string()

    def __repr__(self):
        return repr(self.store.string())

    def iter_line_ranges(self, start=0, stop=None):
        """Generate line ranges

        :param start: Hexichar index from which to start iterating.
        The default is zero (0).
        :param stop: The last hexichar index to consider. The default is
        the last hexichar index.
        :yields: Two-tuples `(location, length)`. `location` is the
        beginning of the line in hexichars, and `length` is the length
        of the line including newline character(s) in hexichars.
        """
        string = self.store.string()
        index = start
        if stop is None:
            stop = string.length()
        while index < stop:
            rng = string.lineRangeForRange_((index, 0))
            yield rng
            index = sum(rng)

    def iterlines(self, start=0, stop=None):
        """Generate lines of text

        See `iter_line_ranges`
        """
        store = self.store.string()
        for rng in self.iter_line_ranges(start, stop):
            yield store.substringWithRange_(rng)

    def ends_with_newline(self):
        string = self.store.string()
        length = string.length()
        x, end, contents_end = string.getLineStart_end_contentsEnd_forRange_(
                                            NULL, None, None, (length - 1, 0))
        return end != contents_end

    def find(self, sub, start=None, end=None):
        """Locale-aware find"""
        return self._find(sub, start, end)

    def rfind(self, sub, start=None, end=None):
        """Locale-aware reverse find"""
        return self._find(sub, start, end, True)

    def _find(self, sub, start, end, reverse=False):
        if start is None:
            start = 0
        else:
            start = index_to_range(start, 0)[0]
        if end is None:
            end = len(self)
        else:
            end = index_to_range(end, 0)[0]
        assert start >= 0, start
        assert end >= start, (start, end)
        rng = (start, end - start)
        options = fn.NSBackwardsSearch if reverse else 0
        i = self.string().rangeOfString_options_range_locale_(
            sub, options, rng, ak.NSLocale.currentLocale())[0]
        return -1 if i == fn.NSNotFound else i

    def search(self, regex, pos=None, endpos=None):
        """Search this text with the given regex

        Indexes passed to this object are expected to be NSString
        hexichar indexes. Indexes retrieved from the resulting match
        object (if any) will be NSString hexichar indexes.
        """
        pos = 0 if pos is None else self._codepoint_index(pos)
        end = self._codepoint_index(len(self) if endpos is None else pos)
        match = regex.search(self.string(), pos)
        return TextMatch(match, self) if match is not None else None

    def finditer(self, regex, pos=None, endpos=None):
        """Iterfind on this text with the given regex

        Indexes passed to this object are expected to be NSString
        hexichar indexes. Indexes retrieved from the resulting match
        object (if any) will be NSString hexichar indexes.
        """
        pos = 0 if pos is None else self._codepoint_index(pos)
        end = self._codepoint_index(len(self) if endpos is None else endpos)
        for match in regex.finditer(self.string(), pos, end):
            yield TextMatch(match, self)

    def _codepoint_index(self, hexichar_index):
        """hexichar index -> codepoint index"""
        if self._surrogates is None:
            return hexichar_index
        return self._convert_index(hexichar_index, -1)

    def _hexichar_index(self, codepoint_index):
        """codepoint index -> hexichar index"""
        if self._surrogates is None:
            return codepoint_index
        return self._convert_index(codepoint_index)

    def _convert_index(self, index, direction=1):
        """Convert from Unicode code point index to NSString hexichar index

        Or the opposite if direction is `-1`
        """
        surrs = self._surrogates
        length = len(self)
        if index < 0 or index > length:
            raise IndexError("index {} out of bounds; string length {}".format(
                index, length))
        # TODO binary search
        for i in surrs:
            if i >= index:
                return index
            index += direction
        get_range = self.string().rangeOfCharacterFromSet_options_range_
        notfound = ak.NSNotFound
        chars = UNICODE_SUPPLEMENTARY_PLANES # surrogate pairs
        start = (surrs[-1] + 1) if surrs else 0
        while start < length:
            rng = get_range(chars, 0, (start, length - start))
            i = rng[0]
            if i == notfound:
                break
            assert rng[1] == 2, rng
            surrs.append(i)
            if i > index:
                return index
            index += direction
            start = sum(rng)
        if not surrs:
            self._surrogates = None
        else:
            surrs.append(length + 1)
        return index

    def count_chars(self, chars, start, end=None):
        """Count the number of characters starting at index

        :param chars: A set of characters to match while counting.
        Counting stops when a character is found that is not in this
        set.
        :param start: The index from which to start counting.
        :param end: The index at which to stop counting. Defaults to the
        length of the string.
        :returns: A number greater than or equal to zero.
        """
        string = self.store.string()
        length = string.length()
        if start < 0:
            raise NotImplementedError('not tested, or needed yet')
        if end is None or end > length:
            end = length
        elif end < 0:
            raise NotImplementedError('not tested, or needed yet')
        index = start
        # TODO test with emoji (characterAtIndex_ will fail)
        while index < end and string.characterAtIndex_(index) in chars:
            index += 1
        return index - start


def composed_length(string, enumerate=False):
    """Get the length of the string as seen by a human

    :param string: A string.
    :param enumerate: If true, loop over each character (slower, but
    possibly more accurate).
    """
    if enumerate:
        def block(substring, sub_range, enclosing_range, stop):
            nonlocal length
            length += 1
        length = 0
        range = (0, string.length())
        string.enumerateSubstringsInRange_options_usingBlock_(
            range, ak.NSStringEnumerationByComposedCharacterSequences, block)
        return length;
    return len(string.precomposedStringWithCanonicalMapping());


def index_to_range(index, length):
    if isinstance(index, int):
        return (index, 1)
    if isinstance(index, (tuple, fn.NSRange)):
        return index
    if not isinstance(index, slice) or index.step is not None:
        raise ValueError("cannot convert {!r} to range".format(index))
    start = min(0 if index.start is None else index.start, length)
    if start < 0:
        start = convert_negative_index(start, length, 0)
    stop = min(length if index.stop is None else index.stop, length)
    if stop < 0:
        stop = convert_negative_index(stop, length, 0)
    if start > stop:
        raise ValueError(index)
    return start, stop - start


def convert_negative_index(index, length, underflow=None):
    if index >= 0:
        raise ValueError("expected negative index")
    value = length + index
    if value < 0:
        if underflow is None:
            raise IndexError(index)
        value = underflow
    return value


class TextStorageDelegate(ak.NSObject):

    def init_(self, target):
        target.setDelegate_(self)
        self.target = target
        self.callbacks = set()
        return self

    def register_edit_callback(self, callback):
        self.callbacks.add(callback)
        return lambda: self.callbacks.discard(callback)

    def dealloc(self):
        target, self.target = self.target, None
        if target is not None:
            target.setDelegate_(None)
        self.callbacks = None

    def textStorageDidProcessEditing_(self, notification):
        store = notification.object()
        for callback in list(self.callbacks):
            callback(store.editedRange())


UNICODE_SUPPLEMENTARY_PLANES = ak.NSCharacterSet.characterSetWithRange_((0x10000, 0xFFFFF))


class TextMatch(Match):

    def __init__(self, match, text):
        super().__init__(match)
        self.text = text

    def __repr__(self):
        try:
            value = "{!r} span={}".format(self[0], self.span())
        except Exception:
            value = repr(self.match)
        return "<{} {}>".format(type(self).__name__, value)

    def __str__(self):
        return repr(self)

    def start(self, *group):
        return self.text._hexichar_index(self.match.start(*group))

    def end(self, *group):
        return self.text._hexichar_index(self.match.end(*group))

    def span(self, *group):
        start, end = self.match.span(*group)
        return self.text._hexichar_index(start), self.text._hexichar_index(end)

    def range(self, *group):
        """Get a range tuple (offset, length) for the group"""
        start, end = self.span(*group)
        return (start, end - start)
