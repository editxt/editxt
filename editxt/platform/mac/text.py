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


class Text(object):

    def __init__(self, value=""):
        self.store = ak.NSTextStorage.alloc() \
            .initWithString_attributes_(value, {})
        self._delegate = TextStorageDelegate.alloc().init_(self.store)

    def on_edit(self, callback):
        return self._delegate.register_edit_callback(callback)

    def __getattr__(self, name):
        return getattr(self.store, name)

    def __getitem__(self, index):
        """Get a string for the given index or slice"""
        string = self.store.string()
        rng = index_to_range(index, string.length())
        return string.substringWithRange_(rng)

    def __setitem__(self, index, value):
        rng = index_to_range(index, len(self))
        self.store.replaceCharactersInRange_withString_(rng, value)

    def __len__(self):
        return self.store.length()

    def __str__(self):
        return self.store.string()

    def __repr__(self):
        return repr(self.store.string())

    def iter_line_ranges(self, start=0, stop=None):
        """Generate line ranges

        Start and stop are hexichar (what Apple calls *unichar*)
        indexes, which are UTF-16-encoded code units.
        See http://www.objc.io/issue-9/unicode.html for more details
        on measuring the length of a string.

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
