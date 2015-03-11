# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
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
from itertools import chain, count
from weakref import WeakValueDictionary

import AppKit as ak
from Foundation import NSRange, NSUnionRange, NSValueTransformer
from objc import NULL

# from pygments.formatter import Formatter
# from pygments.lexers import get_lexer_by_name
# from pygments.styles import get_style_by_name

import editxt.constants as const
from editxt.datatypes import WeakProperty
from editxt.util import get_color

log = logging.getLogger(__name__)


SYNTAX_TOKEN = "XToken"
SYNTAX_RANGE = "XRange"

class Error(Exception): pass


class SyntaxFactory():

    def __init__(self):
        self.registry = {"*.txt": PLAIN_TEXT}
        self.definitions = [PLAIN_TEXT]
        self.by_id = {PLAIN_TEXT.id: PLAIN_TEXT}

    def load_definitions(self, path, log_info=True):
        if path and os.path.exists(path):
            for filename in glob.glob(os.path.join(path, "*" + const.SYNTAX_DEF_EXTENSION)):
                try:
                    sdef = self.load_definition(filename)
                    if not sdef.disabled:
                        overrides = []
                        for pattern in sdef.file_patterns:
                            if pattern in self.registry:
                                overrides.append(pattern)
                            self.registry[pattern] = sdef
                        self.by_id[sdef.id] = sdef
                except Exception:
                    log.error("error loading syntax definition: %s", filename, exc_info=True)
                else:
                    stat = [sdef.name, "[%s]" % ", ".join(sorted(sdef.file_patterns))]
                    if sdef.disabled:
                        stat.append("DISABLED")
                    elif overrides:
                        stat.extend(["overrides", ", ".join(overrides)])
                    stat.append(filename)
                    if log_info:
                        log.info("syntax definition: %s", " ".join(stat))

    def load_definition(self, filename):
        ns = {
            "re": re,
            "RE": RE,
            "name": os.path.basename(filename)[:-len(const.SYNTAX_DEF_EXTENSION)],
            "file_patterns": [],
            "registry": self,
        }
        with open(filename) as fh:
            exec(fh.read(), ns)
        ns.pop("RE", None)
        ns.pop("__builtins__", None)
        factory = ns.pop("SyntaxDefinition", SyntaxDefinition)
        kwargs = {a: ns[a] for a in factory.ARGS if a in ns}
        return factory(filename, **kwargs)

    def index_definitions(self):
        unique = dict((id(sd), sd) for sd in self.registry.values())
        defs = sorted(unique.values(), key=lambda d:(d.name, id(d)))
        self.definitions[:] = defs
        sd = NSValueTransformer.valueTransformerForName_("SyntaxDefTransformer")
        sd.update_definitions(defs)

    def get(self, id_):
        return self.by_id.get(id_)

    def get_definition(self, filename):
        for pattern, sdef in self.registry.items():
            if fnmatch(filename, pattern):
                return sdef
        return PLAIN_TEXT


class Highlighter(object):

    def __init__(self, app=None):
        self.syntaxdef = PLAIN_TEXT
        self.theme = Theme(app.config.lookup("theme.syntax", True) if app else {})
        self.filename = None

    @property
    def syntaxdef(self):
        return self._syntaxdef
    @syntaxdef.setter
    def syntaxdef(self, value):
        self._syntaxdef = value
        self.langs = {}

    def color_text(self, text, minrange=None):
        if text.editedMask() == ak.NSTextStorageEditedAttributes:
            return # we don't care if only attributes changed

        lang = self.syntaxdef
        if lang is None or not lang.wordinfo:
            if not minrange or minrange[0] == 0:
                rng = (0, text.length())
                rem_attribute = text.removeAttribute_range_
                rem_attribute(SYNTAX_TOKEN, rng)
                rem_attribute(SYNTAX_RANGE, rng)
                rem_attribute(ak.NSForegroundColorAttributeName, rng)
            return

        tlen = text.length()
        if minrange is not None:
            start = max(minrange[0] - 1, 0)
            #string = text.string()
            #whitespace = WHITESPACE
            #start = max(minrange[0] - 1, 0)
            #while start > 0:
            #    if string[start] in whitespace:
            #        break
            #    start -= 1
            long_range = text.attribute_atIndex_longestEffectiveRange_inRange_
            token, adjrange = long_range(SYNTAX_TOKEN, start, None, (0, tlen))
            minrange = NSUnionRange(minrange, adjrange)
            offset = minrange[0]
            minend = sum(minrange)
            #log.debug("%s %s %s %s", start, token, adjrange, minrange)
        else:
            offset = 0
            minend = tlen

        text.beginEditing()
        try:
            self.scan(lang, text, offset, minend, tlen)
        except Exception:
            log.exception("syntax highlight error")
        finally:
            text.endEditing()

    def scan(self, lang, text, offset, minend, tlen):
        x_range = SYNTAX_RANGE
        x_token = SYNTAX_TOKEN
        fg_name = ak.NSForegroundColorAttributeName
        long_range = text.attribute_atIndex_longestEffectiveRange_inRange_
        add_attribute = text.addAttribute_value_range_
        rem_attribute = text.removeAttribute_range_
        get_attribute = text.attribute_atIndex_effectiveRange_

        string = text.string()
        theme = self.theme
        end = prevend = offset
        cache = self.langs
        langs = []
        state = ""
        null = NULL
        if offset > 0:
            key, ignore = text.attribute_atIndex_effectiveRange_(
                                x_range, offset, NULL)
            if key:
                langs.append(lang)
                state = key
                lang = cache[key]
                while " " in key:
                    key = key.rsplit(" ", 1)[0]
                    langs.insert(1, cache[key])

        while True:
            wordinfo = lang.wordinfo
            #log.debug("state=%s offset=%s", state, offset)
            for match in lang.regex.finditer(string, offset):
                info = wordinfo.get(match.lastgroup)
                #log.debug("    %s %r\n        %s\n        state: %s",
                #            match.lastgroup, info, match, state)
                if info is None:
                    log.error("invalid syntax match: %r", match)
                    continue
                start, end = match.span()
                if start != end:
                    rng = (start, end - start)
                    if prevend != start:
                        # clear unhighlighted range
                        assert prevend < start, (prevend, start)
                        prevrange = (prevend, start - prevend)
                        rem_attribute(x_token, prevrange)
                        rem_attribute(fg_name, prevrange)
                    prevend = end

                    if end > minend and end + 1 < tlen:
                        # check for early exit (same color & language)
                        rplus = ((start - 1) if start else 0, end - start + 2)
                        if (info, rng) == long_range(x_token, start, None, rplus):
                            key, ignore = get_attribute(x_range, start, null)
                            if key == (state or None):
                                xrng = (offset, end - offset)
                                if state:
                                    add_attribute(x_range, state, xrng)
                                else:
                                    rem_attribute(x_range, xrng)
                                return

                    color = theme.get(info)
                    #log.debug("%s %s %s", rng, name, color)
                    if color:
                        add_attribute(x_token, info, rng)
                        add_attribute(fg_name, color, rng)

                else:
                    assert info.event, "non-advancing match: " \
                        "index={} group={} {} {}".format(
                            start,
                            match.lastgroup,
                            lang.regex,
                            lang,
                        )
                if info.event:
                    #log.debug("state=%s offset=%s length=%s %s", 
                    #    state, offset, end - offset, "+" if state else "-")
                    if state:
                        add_attribute(x_range, state, (offset, end - offset))
                    else:
                        rem_attribute(x_range, (offset, end - offset))
                    if info.end:
                        state = state.rsplit(" ", 1)[0] if " " in state else ""
                        lang = langs.pop()
                    if info.next:
                        langs.append(lang)
                        lang = info.next
                        state = (state + " " + lang.id) if state else lang.id
                        cache[state] = lang
                    offset = end
                    break # exit for
            else:
                break # exit while
        if offset < end:
            if state:
                add_attribute(x_range, state, (offset, end - offset))
            else:
                rem_attribute(x_range, (offset, end - offset))
        if end < tlen:
            rng = (end, tlen - end)
            rem_attribute(x_range, rng)
            rem_attribute(x_token, rng)
            rem_attribute(fg_name, rng)


class NoHighlight(object):

    wordinfo = None

    def __init__(self, name, comment_token, disabled=False, _id=None):
        self.name = name
        self.id = _id or name.lower().replace(" ", "-")
        self.comment_token = comment_token
        self.disabled = disabled

    def __repr__(self):
        return "<%s : %s>" % (type(self).__name__, self.name)


class SyntaxDefinition(NoHighlight):
    """Syntax definition

    `<name>` is a symbolic name such as "keyword" or "comment.single-line".
    Names are used to associate theme colors with matched tokens.

    :param filename: The filename from which this definition was loaded.
    :param name: Human-readable name.
    :param file_patterns: Globbing patterns for matching filenames.
    :param word_groups: a sequence of two-tuples associating word-tokens
        with a color:
        ```
        [
            (<name>, ['word1', 'word2']),
            ...
        ]
        ```
        Use `RE` objects in place of words for more complex patterns.
    :param delimited_ranges: a list of four-tuples associating a set of
        delimiters with a color and optional syntax definition:
        ```
        [
            (
                <name>,
                <start delimiter string, RE, or definition type>,
                <list of end delimiters>,
                <(optional) syntax definition type or name>,
            ),
            ('comment.multi-line', '<!--', ['-->']),
            ('string.double-quoted', '"', ['"', '\n']),
            ('tag', '<style(?:\s[^>]*?)?>', ['</style>'], 'css'),
        ]
        ```
        Ranges that have a syntax definition will use the associated
        theme color for the delimiters only, while ranges without a
        syntax definition will use the color for the entire range.
        
        The start delimiter may be a *syntax definition type*, which is
        an object with at least one of the attributes `word_groups` or
        `delimited_ranges`. Each token in the start definition (which
        may itself be a delimited range with nested definitions) will
        immediately transition to the nested syntax defintion.

    :param ends: A two-tuple (<name>, [<end token>, ...])
        For internal use only. If any of these tokens are matched it ends the
        syntax definition, which is not a supported operation for a top-level
        definition.
    :param comment_token: The comment token to use when block-commenting
        a region of text.
    :param disabled: True if this definition is disabled.
    :param flags: Regular expression flags for this language.
    """

    ARGS = {
        "name",
        "file_patterns",
        "word_groups",
        "delimited_ranges",
        "ends",
        "comment_token",
        "disabled",
        "flags",
        "registry",
    }

    registry = WeakProperty()

    def __init__(self, filename, name, file_patterns=(),
        word_groups=(), delimited_ranges=(), ends=None,
        comment_token="", disabled=False, flags=0, registry=None, _id=None):
        super().__init__(name, comment_token, disabled, _id=_id)
        self.filename = filename
        self.file_patterns = set(file_patterns)
        self.word_groups = word_groups
        self.delimited_ranges = delimited_ranges
        self.ends = ends
        self.flags = flags | re.MULTILINE
        self.registry = registry
        self.lang_ids = (str(i) for i in count())

    def _init(self):
        wordinfo = {}
        groups = []
        for phrase, ident, info in self.iter_group_info():
            groups.append(phrase)
            wordinfo[ident] = info
        self._wordinfo = wordinfo
        self._regex = re.compile("|".join(groups), self.flags)
        log.debug("file: %s\n"
                  "name: %s\n"
                  "id: %s\n"
                  "regexp: %s\n"
                  "wordinfo: %s",
            self.filename,
            self.name,
            self.id,
            self._regex.pattern,
            wordinfo,
        )

    @property
    def wordinfo(self):
        try:
            return self._wordinfo
        except AttributeError:
            self._init()
        return self._wordinfo

    @property
    def regex(self):
        try:
            return self._regex
        except AttributeError:
            self._init()
        return self._regex

    def iter_group_info(self, idgen=None):
        """
        :yields: Three-tuples like
        ```
        (
            <phrase regexp named group>,
            <phrase group name>,
            <MatchInfo>,
        )
        ```
        """
        idgen = idgen or ("g%i" % i for i in count())
        if self.ends:
            yield from self.iter_words(iter(["end"]), [self.ends], True)
        yield from self.iter_words(idgen, self.word_groups)
        yield from self.iter_ranges(idgen)

    def iter_words(self, idgen, word_groups, end=False):
        word_char = re.compile(r"\w")
        for name, tokens in word_groups:
            ident = next(idgen)
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
            phrase = "(?P<{}>{})".format(ident, "|".join(wordgroup))
            yield phrase, ident, MatchInfo(name, end=end)

    def iter_ranges(self, idgen):
        def lookup_syntax(owner, sdef, *unknown, ends=None):
            if unknown:
                log.warn("extra delimited range params: %s", unknown)
            if hasattr(sdef, "word_groups") or hasattr(sdef, "delimited_ranges"):
                sdef = self.make_definition(owner, sdef, ends)
            elif not hasattr(sdef, "clone"):
                sdef_name = sdef
                sdef = (self.registry or {}).get(sdef_name)
                if not sdef:
                    log.warn("unknown syntax definition: %r", sdef_name)
                elif ends:
                    sdef = sdef.clone(owner, ends)
            return sdef

        class unknown:
            word_groups = []

        def compile_range(name, start, ends, sdef):
            ident = next(idgen)
            ends = list(ends) + [RE("\Z")]
            if sdef:
                sdef = lookup_syntax(name, *sdef, ends=ends)
                if not sdef:
                    sdef = self.make_definition(name, unknown, ends)
            else:
                # ranges without nested syntax rules are broken into lines to
                # minimize the range that needs to be re-highlighted on edit
                endxp = "|".join(escape(e) for e in ends)
                ends = [RE(r".*?(?:{})".format(endxp))]
                class lines:
                    word_groups = [(name, [RE(r".+?$")])]
                lines.__name__ = "{}.lines".format(name)
                sdef = self.make_definition(name, lines, ends)
            phrase = "(?P<{}>{})".format(ident, escape(start))
            return phrase, ident, MatchInfo(name, sdef)

        for name, start, ends, *sdef in self.delimited_ranges:
            try:
                if isinstance(start, (str, RE)):
                    yield compile_range(name, start, ends, sdef)
                else:
                    ends = list(ends) + [RE("\Z")]
                    start_def = lookup_syntax(name, start)
                    assert start_def, (self, name, start, ends, sdef)
                    next_def = lookup_syntax(name, *sdef, ends=ends)
                    if not next_def:
                        next_def = self.make_definition(name, unknown, ends)
                    for phrase, ident, info in start_def.iter_group_info(idgen):
                        if info.next is None:
                            info.next = next_def
                        else:
                            end_info = info.next.wordinfo["end"]
                            assert end_info.next is None, info.next
                            assert end_info.end, info.next
                            end_info.next = next_def
                        assert not info.end, (self, name, start_def, phrase, info)
                        yield phrase, ident, info
            except Exception:
                log.error("delimited range error: %s %s %s %s",
                          name, start, ends, sdef, exc_info=True)

    def make_definition(self, name, rules, ends=None):
        log.debug("make: %s/%s", self.name, rules.__name__)
        NA = object()
        args = {
            "name": "{}/{}".format(self.name, rules.__name__),
            "_id": next(self.lang_ids),
            "flags": self.flags,
        }
        for attr in self.ARGS:
            value = getattr(rules, attr, NA)
            if value is not NA:
                args[attr] = value
        if ends is not None:
            args["ends"] = (name, ends)
        return type(self)(self.filename, **args)

    def clone(self, name, ends):
        log.debug("clone: %s for %s", self.name, name)
        args = {a: getattr(self, a) for a in self.ARGS - {"ends"}}
        args["_id"] = next(self.lang_ids)
        args["ends"] = (name, ends)
        return type(self)(self.filename, **args)


class MatchInfo(str):

    __slots__ = ('event', 'next', 'end')

    def __new__(cls, value, next=None, end=False):
        info = super().__new__(cls, value)
        info.event = end or next is not None
        info.next = next
        info.end = end
        return info

    def __repr__(self):
        return "".join([x for x in [
            super().__repr__(),
            "n" if self.next else "",
            "e" if self.end else "",
        ] if x])


class Theme(object):

    def __init__(self, data):
        self.data = data

    def get(self, name):
        try:
            return self.data[name]
        except KeyError:
            next_name = name
        value = None
        if name:
            while "." in next_name:
                next_name = next_name.rsplit(".", 1)[0]
                try:
                    value = self.data[next_name]
                    break
                except KeyError:
                    continue
        self.data[name] = value
        return value


PLAIN_TEXT = NoHighlight("Plain Text", "x")
WHITESPACE = " \r\n\t\u2028\u2029"


class RE(object):
    def __init__(self, pattern):
        self.pattern = pattern
    def __repr__(self):
        return "RE(%r)" % (self.pattern,)


def escape(token):
    if hasattr(token, "pattern"):
        return token.pattern
    token = re.escape(token)
    return token.replace(re.escape("\n"), "\\n")
