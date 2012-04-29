# -*- coding: utf-8 -*-
# EditXT
# Copyright (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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
import glob
import logging
import os
import re
import string
from fnmatch import fnmatch
from itertools import chain, izip, count

from AppKit import *
from Foundation import NSRange, NSUnionRange

# from pygments.formatter import Formatter
# from pygments.lexers import get_lexer_by_name
# from pygments.styles import get_style_by_name

import editxt.constants as const

log = logging.getLogger(__name__)


SYNTAX_RANGE_ATTRIBUTE = u"SYNTAX_RANGE_ATTRIBUTE"

class Error(Exception): pass
class StopHighlight(Error): pass


class SyntaxFactory():

    def __init__(self):
        self.registry = {"*.txt": PLAIN_TEXT}
        self.definitions = [PLAIN_TEXT]

    def load_definitions(self, path):
        if path and os.path.exists(path):
            for filename in glob.glob(os.path.join(path, "*" + const.SYNTAX_DEF_EXTENSION)):
                try:
                    sdef = self.load_definition(filename)
                    if not sdef.disabled:
                        overrides = []
                        for pattern in sdef.filepatterns:
                            if pattern in self.registry:
                                overrides.append(pattern)
                            self.registry[pattern] = sdef
                except Exception:
                    log.error("error loading syntax definition: %s", filename, exc_info=True)
                else:
                    stat = [sdef.name, "[%s]" % ", ".join(sorted(sdef.filepatterns))]
                    if sdef.disabled:
                        stat.append("DISABLED")
                    elif overrides:
                        stat.extend(["overrides", ", ".join(overrides)])
                    stat.append(filename)
                    log.info("syntax definition: %s", " ".join(stat))

    def load_definition(self, filename):
        ns = {"RE": RE}
        execfile(filename, ns)
        ns.pop("RE", None)
        ns.pop("__builtins__", None)
        factory = ns.pop("SyntaxDefinition", SyntaxDefinition)
        return factory(filename, **ns)

    def index_definitions(self):
        unique = dict((id(sd), sd) for sd in self.registry.itervalues())
        defs = sorted(unique.itervalues(), key=lambda d:(d.name, id(d)))
        self.definitions[:] = defs
        sd = NSValueTransformer.valueTransformerForName_("SyntaxDefTransformer")
        sd.update_definitions(defs)

    def get_definition(self, filename):
        for pattern, sdef in self.registry.iteritems():
            if fnmatch(filename, pattern):
                return sdef
        return PLAIN_TEXT


class SyntaxCache(object):

    def __init__(self):
        self.cache = []
        self._syntaxdef = PLAIN_TEXT
        self.filename = None

    def _get_syntaxdef(self):
        return self._syntaxdef
    def _set_syntaxdef(self, value):
        if value is not self._syntaxdef:
            del self.cache[:]
            self._syntaxdef = value
    syntaxdef = property(_get_syntaxdef, _set_syntaxdef)

    def color_text(self, ts, minrange=None):
        if ts.editedMask() == NSTextStorageEditedAttributes:
            return # we don't care if only attributes changed
        sdef = self._syntaxdef
        if sdef is None:
            return
        text = ts.string()
        tlen = ts.length()

        if minrange is not None:
            adjrange = self.adjust(minrange.location, ts.changeInLength())
            minrange = NSUnionRange(minrange, adjrange)
            i = minrange.location - 1
            if i < 0:
                i = 0
            else:
                while i > 0 and text[i] != u"\n":
                    i -= 1
            prerange, info = self.get(i)
            if prerange is None:
                prerange = NSRange(i, 0)
            minrange = NSUnionRange(minrange, prerange)
            minstart = minrange.location
            minend = minrange.location + minrange.length
        else:
            minstart = 0
            minend = tlen

        def setcolor(color, range, prevend, info, ts=ts, cache=self, minend=minend):
            prevcache = cache.get(range.location)
            prevend = max(min(prevend, range.location), 0)
            rangelen = max((range.location - prevend) + range.length, 0)
            prevrange = NSRange(prevend, rangelen)
            cache.clear(prevrange)
            ts.removeAttribute_range_(NSForegroundColorAttributeName, prevrange)
            if color is not None:
                ts.addAttribute_value_range_(NSForegroundColorAttributeName, color, range)
                cache.set(range, info)
            if range.location + range.length > minend and (range, info) == prevcache:
                raise StopHighlight()

        try:
            sdef.scan(text, setcolor, minstart)
        except StopHighlight:
            pass

    def adjust(self, index, changelen):
        if changelen < 0:
            cache = self.cache
            del cache[index:index-changelen]
            start = end = index
            if index < len(cache):
                # [(0,3), (1,2), <snip> (1,2), (2,1)]

                # clear overlapping range before adjustment
                if index > 0:
                    hit = cache[index - 1]
                    if hit and hit[1] > 1:
                        start = index - (hit[0] + 1)
                        for i in xrange(hit[0] + 1):
                            if i < 0:
                                # this should never happen
                                start = 0
                                break
                            cache[index - 1 - i] = None

                # clear overlapping range after adjustment
                hit = cache[index]
                if hit and hit[0] > 0:
                    end = index + hit[1]
                    for i in xrange(hit[1]):
                        cache[index + i] = None

            return NSRange(start, end - start)
        self.cache[index:index] = [None for i in xrange(changelen)]
        return NSRange(index, changelen)

    def get(self, index):
        try:
            value = self.cache[index]
        except IndexError:
            return (None, None)
        if value is None:
            return (None, None)
        return NSRange(index - value[0], value[0] + value[1]), value[2]

    def set(self, range, info):
        cache = self.cache
        while range.location > len(cache):
            cache.append(None)
        for i in xrange(range.length):
            try:
                cache[range.location + i] = (i, range.length - i, info)
            except IndexError:
                cache.append((i, range.length - i, info))

    def clear(self, range):
        cache = self.cache
        if range.location + range.length >= len(cache):
            del cache[range.location:]
        try:
            for i in xrange(range.length):
                cache[range.location + i] = None
            next_index = range.location + range.length + 1
            next = cache[next_index]
            if next and next[0] > 0:
                for i in xrange(next[1]):
                    cache[next_index + i] = None
        except IndexError:
            pass


class NoHighlight(object):

    def __init__(self, name, comment_token, disabled=False):
        self.name = name
        self.comment_token = comment_token
        self.disabled = disabled

    def scan(self, text, setcolor, offset=0):
        if offset == 0:
            setcolor(None, NSRange(len(text) - 1, 0), 0, None)

    def __repr__(self):
        return "<%s : %s>" % (type(self).__name__, self.name)


class SyntaxDefinition(NoHighlight):

    def __init__(self, filename, name, filepatterns, word_groups=(),
        delimited_ranges=(), comment_token="", disabled=False, flags=0):
        """Syntax definition

        arguments:
            word_groups - a sequence of two-tuples associating word-tokens with
                a color:  [ (['word1', 'word2'], <RRGGBB color string>) ]
            delimited_ranges - a list of four-tuples associating a set of
                delimiters with a color and a syntax definition:
                [
                    (
                        <start delimiter>,
                        <list of end delimiters>,
                        <RRGGBB color string>,
                        <SyntaxDefinition instance> or None
                    ),
                    ('<!--', ['-->'], 'RRGGBB', None),
                    ('"', ['"', '\n'], 'RRGGBB', None),
                    ('<?', ['?>'], 'RRGGBB', "php"),
                ]
        """
        super(SyntaxDefinition, self).__init__(name, comment_token, disabled)
        def escape(token):
            if hasattr(token, "pattern"):
                return token.pattern
            token = re.escape(token)
            return token.replace(re.escape("\n"), "\\n")
        namegen = ("g%i" % i for i in count())
        self.filename = filename
        self.filepatterns = set(filepatterns)
        self.word_groups = list(word_groups)
        self.delimited_ranges = list(delimited_ranges)
        self.wordinfo = wordinfo = {}
        flags |= re.DOTALL
        groups = []

        word_char = re.compile(r"\w")
        for tokens, color in word_groups:
            name = namegen.next()
            color = self.getColor(color)
            wordgroup = []
            for token in tokens:
                if hasattr(token, "pattern"):
                    word = token.pattern
                else:
                    word = escape(token)
                    if word_char.match(token[0]):
                        word = r"\b" + word
                    if word_char.match(token[-1]):
                        word = word + r"\b"
                wordgroup.append(word)
            groups.append("(?P<%s>%s)" % (name, "|".join(wordgroup)))
            wordinfo[name] = (color, name)

        for start, ends, color, sdef in delimited_ranges:
            name = namegen.next()
            color = self.getColor(color)
            phrase = "(?P<%s>(%s).*?(%s))" % (
                name,
                escape(start),
                "|".join(escape(token) for token in chain(ends, [RE("$")]))
            )
            groups.append(phrase)
            endxp = re.compile(".*?" + "|".join(escape(token) for token in ends), flags)
            wordinfo[name] = (color, name) #, endxp)

        self.regex = re.compile("|".join(groups), flags)

    def scan(self, text, setcolor, offset=0):
        info = self.wordinfo
        prevend = offset
        for match in self.regex.finditer(text, offset):
            data = info.get(match.lastgroup)
            if data is None:
                log.error("invalid syntax match: %r", match.groups())
                continue
            thestart = match.start()
            thisend = match.end()
            range = NSRange(thestart, thisend - thestart)
            setcolor(data[0], range, prevend, data[1])
            prevend = range.location + range.length
        setcolor(None,  NSRange(len(text) - 1, 0), prevend, None)

    _colorCache = {}

    @staticmethod
    def getColor(value, cache=_colorCache):
        if isinstance(value, NSColor):
            return value
        try:
            return cache[value]
        except KeyError:
            assert len(value) == 6, "invalid color value: %r" % value
            r = int(value[:2], 16) / 255.0
            g = int(value[2:4], 16) / 255.0
            b = int(value[4:], 16) / 255.0
            color = cache[value] = NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0)
            return color


PLAIN_TEXT = NoHighlight("Plain Text", "x")


class RE(object):
    def __init__(self, pattern):
        self.pattern = pattern
    def __repr__(self):
        return "RE(%r)" % (self.pattern,)
