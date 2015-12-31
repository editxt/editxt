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
import runpy
import string
from fnmatch import fnmatch
from itertools import chain, count, groupby
from weakref import WeakValueDictionary

import AppKit as ak
from Foundation import NSRange, NSUnionRange, NSValueTransformer
from objc import NULL

# from pygments.formatter import Formatter
# from pygments.lexers import get_lexer_by_name
# from pygments.styles import get_style_by_name

import editxt.constants as const
from editxt.datatypes import WeakProperty

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
            names = glob.glob(os.path.join(path, "*" + const.SYNTAX_DEF_EXTENSION))
            for filename in sorted(names, key=lambda n: n.lower()):
                try:
                    sdef = self.load_definition(filename)
                    file_patterns = sorted(set(sdef.file_patterns))
                    if not sdef.disabled:
                        overrides = []
                        for pattern in file_patterns:
                            if pattern in self.registry:
                                overrides.append(pattern)
                            self.registry[pattern] = sdef
                        self.by_id[sdef.id] = sdef
                except Exception:
                    log.error("error loading syntax definition: %s", filename, exc_info=True)
                else:
                    stat = [sdef.name, "[%s]" % ", ".join(file_patterns)]
                    if sdef.disabled:
                        stat.append("DISABLED")
                    elif overrides:
                        stat.extend(["overrides", ", ".join(overrides)])
                    stat.append(filename)
                    if log_info:
                        log.info("syntax definition: %s", " ".join(stat))

    def load_definition(self, filename):
        ns = {
            "DELIMITER": const.DELIMITER,
            "DynamicRange": DynamicRange,
            "re": re,
            "RE": RE,
            "registry": self,
        }
        ns = runpy.run_path(filename, ns)
        factory = ns.pop("SyntaxDefinition", SyntaxDefinition)
        kwargs = {a: ns[a] for a in factory.ARGS if a in ns}
        base = ns.get("__base__")
        if base is not None:
            kwargs.update((a, getattr(base, a))
                          for a in factory.ARGS
                          if a not in ns and hasattr(base, a))
        if "name" not in kwargs:
            kwargs["name"] = os.path.basename(filename)[:-len(const.SYNTAX_DEF_EXTENSION)]
        sdef = factory(filename, **kwargs)
        if base is not None and sdef.name == base.name:
            # drop base definition since a new definition is replacing it
            for pat in base.file_patterns:
                if self.registry.get(pat) is base:
                    del self.registry[pat]
        return sdef

    def index_definitions(self):
        unique = dict((id(sd), sd) for sd in self.registry.values())
        defs = sorted(unique.values(), key=lambda d:(d.name.lower(), id(d)))
        self.definitions[:] = defs
        sd = NSValueTransformer.valueTransformerForName_("SyntaxDefTransformer")
        sd.update_definitions(defs)

    @staticmethod
    def lang_key(id_):
        if isinstance(id_, tuple):
            return id_
        return id_.lower().replace(" ", "-")

    def __setitem__(self, id_, value):
        assert isinstance(id_, tuple), id_
        self.by_id[id_] = value

    def __getitem__(self, id_):
        return self.by_id[self.lang_key(id_)]

    def get(self, id_, default=None):
        return self.by_id.get(self.lang_key(id_), default)

    def get_definition(self, filename):
        for pattern, sdef in self.registry.items():
            if fnmatch(filename, pattern):
                return sdef
        return PLAIN_TEXT


class Highlighter(object):

    def __init__(self, theme):
        self.syntaxdef = PLAIN_TEXT
        self.theme = theme
        self.langs = None
        self.filename = None

    @property
    def syntaxdef(self):
        return self._syntaxdef
    @syntaxdef.setter
    def syntaxdef(self, value):
        self._syntaxdef = value
        self.langs = None

    def __repr__(self):
        return "<{} {}>".format(type(self).__name__, self.syntaxdef.name)

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
                fg_name = ak.NSForegroundColorAttributeName
                add_attribute = text.addAttribute_value_range_
                add_attribute(fg_name, self.theme.text_color, rng)
            return

        tlen = text.length()
        if not tlen:
            return
        if minrange is not None and self.langs is not None:
            start = max(minrange[0] - 1, 0)
            string = text.string()
            whitespace = lang.whitespace
            start = max(minrange[0] - 1, 0)
            while start > 0:
                if string[start] in whitespace:
                    break
                start -= 1
            long_range = text.attribute_atIndex_longestEffectiveRange_inRange_
            token, adjrange = long_range(SYNTAX_TOKEN, start, None, (0, tlen))
            minrange = NSUnionRange(minrange, adjrange)
            offset = minrange[0]
            minend = sum(minrange)
            #log.debug("%s %s %s %s", token, offset, minend, minrange)
        else:
            self.langs = {}
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
        langs = self.langs
        end = prevend = offset
        key = ""
        null = NULL
        can_exit_early = False
        if offset > 0:
            xkey, ignore = get_attribute(x_range, offset, null)
            if xkey:
                key = xkey
                lang, ignore = langs[xkey]

        while lang is not None:
            wordinfo = lang.wordinfo
            text_color = theme.get_syntax_color(lang.text_color)
            #log.debug("key=%s offset=%s", key, offset)
            for match in lang.regex.finditer(string, offset):
                info = wordinfo.get(match.lastgroup)
                #log.debug("    %s %r\n        %s\n        key: %s",
                #            match.lastgroup, info, match, key)
                if info is None:
                    log.error("invalid syntax match: %r", match)
                    continue
                start, end = match.span()

                if prevend != start:
                    # clear unhighlighted range
                    assert prevend < start, (prevend, start)
                    prevrange = (prevend, start - prevend)
                    rem_attribute(x_token, prevrange)
                    add_attribute(fg_name, text_color, prevrange)
                prevend = end

                if start != end:
                    rng = (start, end - start)

                    if end > minend and end + 1 < tlen and start:
                        # check for early exit (same color & language)
                        rplus = ((start - 1), end - start + 2)
                        if info.event:
                            # extend if at beginning or end of delimited range
                            if info.next and info.next.text_color == info:
                                alt = (info, (rng[0], rng[1] + 1))
                            else:
                                alt = None
                        else:
                            alt = None
                        info_rng = long_range(x_token, start, None, rplus)
                        if (info, rng) == info_rng or alt == info_rng:
                            xkey, ignore = get_attribute(x_range, start, null)
                            if xkey == (key or None):
                                # require two token matches before early exit
                                if can_exit_early:
                                    xrng = (offset, end - offset)
                                    if key:
                                        add_attribute(x_range, key, xrng)
                                    else:
                                        rem_attribute(x_range, xrng)
                                    return
                                else:
                                    can_exit_early = True
                            else:
                                can_exit_early = False
                        else:
                            can_exit_early = False

                    color = theme.get_syntax_color(info)
                    #log.debug("%s %s %s", rng, info, color)
                    if color:
                        add_attribute(x_token, info, rng)
                        add_attribute(fg_name, color, rng)

                elif not info.event:
                    if start == tlen:
                        lang = None
                        break
                    raise Error("non-advancing match: "
                                "index={} group={} {} {}".format(
                                    start,
                                    match.lastgroup,
                                    lang.regex,
                                    lang,
                                ))
                if info.event:
                    #log.debug("key=%s offset=%s length=%s %s", 
                    #    key, offset, end - offset, "+" if key else "-")
                    if key:
                        add_attribute(x_range, key, (offset, start - offset))
                    else:
                        rem_attribute(x_range, (offset, start - offset))

                    lang = info.next
                    if start != end:
                        xkey = info.lang.key if info.lang else key
                        if xkey:
                            if info.lang and xkey not in langs:
                                langs[xkey] = (info.lang, start)
                            add_attribute(x_range, xkey, rng)
                        else:
                            rem_attribute(x_range, rng)
                    elif lang and langs.get(lang.key, (None, end - 1))[1] == end:
                        # FIXME could hit this due to self.langs holding stale start value?
                        raise Error("non-advancing range: index={} {} {}".format(
                            start,
                            match,
                            info.next.regex,
                        ))

                    if lang is not None:
                        langs[lang.key] = (lang, start)
                        key = lang.key
                    else:
                        key = ''

                    offset = end
                    break # exit for
            else:
                break # exit while
        if offset < end:
            if key:
                add_attribute(x_range, key, (offset, end - offset))
            else:
                rem_attribute(x_range, (offset, end - offset))
        if end < tlen:
            rng = (end, tlen - end)
            rem_attribute(x_range, rng)
            rem_attribute(x_token, rng)
            add_attribute(fg_name, self.theme.text_color, rng)


class NoHighlight(object):

    wordinfo = None

    def __init__(self, name, comment_token, disabled=False, _id=None):
        self.name = name
        self.id = _id or name.lower().replace(" ", "-")
        self.comment_token = comment_token
        self.disabled = disabled

    def __repr__(self):
        return "<%s %s %s>" % (type(self).__name__, self.name, self.id)


class SyntaxDefinition(NoHighlight):
    """Syntax definition

    `<name>` is a symbolic name such as "keyword" or "comment.single-line".
    Names are used to associate theme colors with matched tokens.

    :param filename: The filename from which this definition was loaded.
    :param name: Human-readable name.
    :param file_patterns: Globbing patterns for matching filenames.
    :param rules: a list of two-, three-, or four-tuples:
        ```
        [
            # word group : two-tuple
            (<color name>, <list of words: str or RE objects>),
            ('keyword', ['true', 'false', 'undefined', 'alert']),

            # delimited range : three-tuple or four-tuple
            (
                <color name>,
                <start delimiter string, RE, or definition type>,
                <list of end delimiters: string, RE, or definition type>,
                <(optional) syntax definition type or name>,
            ),
            ('comment.multi-line', '<!--', ['-->']),
            ('string.double-quoted', '"', ['"', '\n']),
            ('tag', RE('<style(?:\s[^>]*?)?>'), ['</style>'], 'css'),
        ]
        ```
        Word groups are two-tuples consisting of a color name and a list
        of words (literal or `RE` objects for more complex patterns).

        Delimited ranges are three- or four-tuples. Start or end
        delimiters may be a *syntax definition type*, which is an object
        with a `rules` attribute. When a syntax definition type is
        specified as the start delimiter, any matched rule in the
        definition will immediately transition to the (optional) syntax
        definition type of the start delimiter's range. When a syntax
        definition type is specified as an end delimiter, any matched
        rule in the definition will immedately end the range and
        transition to the end delimiter's rules.

        Color names are strings like 'keyword', 'string.single-quoted',
        etc. defined in themes. They are mapped to actual colors during
        syntax highlighting. Dotted color names are matched to the most
        specific color found in the theme, starting with the left-most
        part of the name. So 'string.single-quoted' may match the full
        string or simply 'string'. If no match is found then the default
        text color will be used. A `default_text_color` attribute may be
        specified on a syntax definition type to set the default text
        color for the range; the `DELIMITER` constant signifies the same
        color as the range delimiter.
    :param comment_token: The comment token to use when block-commenting
        a region of text.
    :param disabled: True if this definition is disabled.
    :param flags: Regular expression flags for this language.
    """

    ARGS = {
        "name",
        "file_patterns",
        "rules",
        "comment_token",
        "disabled",
        "flags",
        "whitespace",
        "default_text_color",
        "registry",

        # deprecated
        "word_groups",
        "delimited_ranges",
    }

    whitespace = " \r\n\t\u2028\u2029"
    registry = WeakProperty()

    def __init__(self, filename, name, *, file_patterns=(),
            rules=(), word_groups=(), delimited_ranges=(),
            comment_token="", disabled=False, flags=re.MULTILINE,
            whitespace=whitespace, default_text_color="", registry=None,
            _id=None, _lang_ids=None, _ends=None, _next=None, _key=""):
        super().__init__(name, comment_token, disabled, _id=_id)
        self.filename = filename
        self.file_patterns = list(file_patterns)
        if rules:
            self.rules = rules
            if word_groups or delimited_ranges:
                log.warn("%s %s: `word_groups` and `delimited_ranges` are "
                    "deprecated and should not be used with `rules`",
                    filename, name)
        else:
            self.rules = list(word_groups) + list(delimited_ranges)
        self.ends = _ends
        self.next = _next
        self.key = _key
        self.flags = flags
        self.whitespace = whitespace
        self.default_text_color = default_text_color
        self.registry = registry
        self.lang_ids = _lang_ids or ("%x" % i for i in count())

    def _init(self):
        wordinfo = {}
        groups = []
        idgen = count()
        for phrase, ident, info in self.iter_group_info(idgen):
            groups.append(phrase)
            wordinfo[ident] = info
        self._wordinfo = wordinfo
        try:
            self._regex = re.compile("|".join(groups), self.flags)
        except re.error as err:
            msg = "cannot compile groups for %s: %s\n%r" % (self.name, err, groups)
            log.warn(msg, exc_info=True)
            raise Error(msg)
        color_name = self.default_text_color
        if color_name == const.DELIMITER:
            # use theme default if parent has not specified a color
            color_name = "text_color"
        self._text_color = self.get_color(color_name)
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

    @property
    def text_color(self):
        try:
            return self._text_color
        except AttributeError:
            self._init()
        return self._text_color

    def iter_group_info(self, idgen=None):
        """
        :yields: Three-tuples:
        ```
        (
            <phrase regexp named group>,
            <phrase group name>,
            <MatchInfo>,
        )
        ```
        If `idgen` is `None` then the second element in the yielded
        tuple will be `None`, and only start patterns will be yielded.
        """
        if self.ends and idgen is not None:
            for end in self.ends:
                assert end.next is not None or r'\Z' in end.pattern, end
                ident = "e%s" % next(idgen)
                phrase = "(?P<{}>{})".format(ident, end.pattern)
                info = MatchInfo(end.name, end.next, end.lang)
                yield phrase, ident, info
            parent_ends = self.ends
        else:
            parent_ends = [End(r"\Z", self.next, self.get_color(), self)]
        yield from self.iter_groups(idgen, parent_ends)

    def iter_groups(self, idgen, parent_ends):
        def lookup_syntax(sdef, owner, ends, ndef=None, **kw):
            if is_syntax_class(sdef):
                sdef = self.make_definition(sdef, owner, ends, ndef, **kw)
            elif not hasattr(sdef, "make_definition"):
                sdef = self.get_compiled_definition(sdef)
                if sdef is not None and (ends or ndef or kw):
                    sdef = self.make_definition(sdef, owner, ends, ndef, **kw)
            elif isinstance(sdef, DynamicRange):
                sdef = sdef.make_definition(
                            self, lookup_syntax, name, ends, ndef, **kw)
            elif ends or ndef or kw:
                sdef = self.make_definition(sdef, owner, ends, ndef, **kw)
            return sdef

        def endify(name, tokens):
            next_def = self.next or self
            color = self.get_color(name)
            def keyfunc(t, transition_key=count(start=1)):
                return 0 if isinstance(t, (str, RE)) else next(transition_key)
            for transition, token in groupby(tokens, key=keyfunc):
                if not transition:
                    token = [t for t in token if may_match(t)]
                    if token:
                        if len(token) == 1:
                            token = escape(token[0])
                        else:
                            token = r"(?:{})".format(disjunction(token))
                        yield End(token, next_def, color, self)
                else:
                    token = next(token)
                    sdef = lookup_syntax(token, self.name, parent_ends, next_def)
                    for phrase, ident, color_ in sdef.iter_group_info():
                        yield End(phrase, sdef, color_, sdef)

        class unknown:
            rules = []

        def compile_range(name, start, ends, sdef):
            if idgen is None:
                return lookahead(escape(start)), None, self.get_color(name)
            if sdef:
                key = sdef
                if not (is_syntax_class(key) or hasattr(key, "make_definition")):
                    sdef = self.get_compiled_definition(key, unknown)
                color_name = getattr(sdef, "default_text_color", None)
                if color_name is const.DELIMITER:
                    color_name = name
                elif not color_name:
                    color_name = self.default_text_color
                overrides = {"default_text_color": color_name}
                sdef = lookup_syntax(sdef, name, ends, overrides=overrides)
                assert sdef is not None, (name, start, ends, key)
            else:
                # ranges without nested syntax rules are broken into lines to
                # minimize the range that needs to be re-highlighted on edit
                color = self.get_color(name)
                ends = [End(r".*?{}".format(e.pattern), e.next, color, self)
                        for e in ends]
                class lines:
                    rules = [(name, [RE(r".+?$")])]
                    default_text_color = name
                lines.__name__ = "{}.lines".format(name)
                sdef = self.make_definition(lines, name, ends)
            ident = "r%s" % next(idgen)
            phrase = "(?P<{}>{})".format(ident, escape(start))
            return phrase, ident, MatchInfo(self.get_color(name), sdef, self)

        for rule in self.rules:
            try:
                if len(rule) < 3:
                    # word group
                    name, tokens = rule
                    ident = None
                    phrase = disjunction(tokens)
                    if idgen is not None:
                        ident = "w%s" % next(idgen)
                        phrase = "(?P<{}>{})".format(ident, phrase)
                        info = MatchInfo(self.get_color(name), self.next)
                    else:
                        phrase = lookahead(phrase)
                        info = self.get_color(name)
                    yield phrase, ident, info
                    continue

                # delimited range
                name, start, ends, *sdef = rule
                if sdef:
                    if len(sdef) > 1:
                        log.warn("malformed delimited range: %r", rule)
                    sdef = sdef[0]
                else:
                    sdef = None
                ends = list(unique(chain(endify(name, ends), parent_ends)))
                if isinstance(start, (str, RE)):
                    yield compile_range(name, start, ends, sdef)
                else:
                    if sdef:
                        ndef = lookup_syntax(sdef, name, ends)
                    else:
                        class delim_color:
                            default_text_color = name
                            rules = []
                        delim_color.__name__ = name
                        ndef = self.make_definition(delim_color, name, ends)
                    if not ndef:
                        ndef = self.make_definition(unknown, name, ends)
                    #import bug; bug.trace()
                    start_def = lookup_syntax(start, name, parent_ends, ndef)
                    assert start_def, (self, name, start, ends, ndef)
                    yield from start_def.iter_group_info(idgen)
            except Error:
                raise
            except Exception:
                log.error("rule error: %s", rule, exc_info=True)

    def get_color(self, name="text_color"):
        if " " in name:
            value = name.replace(" ", "_")
            log.warn("invalid color name: converting %r to %r", name, value)
            name = value
        if name.startswith("_") or not name:
            name = "text_color"  # theme default text color
        return self.name + " " + name

    def get_compiled_definition(self, key, default=None):
        try:
            sdef = self.registry[key]
        except KeyError:
            log.debug("unknown syntax definition: %r", key)
            sdef = default
        except Exception:
            log.debug("bad syntax key: %s", key, exc_info=True)
            sdef = default
        return sdef

    def make_definition(self, source_definition, name, ends, next_def=None,
                        *, overrides=None):
        end_key = (self.next,) if self.next else ()
        end_key += (next_def,) if next_def else ()
        def_key = (name, source_definition) + end_key + tuple(unique(ends))
        if overrides:
            def_key += tuple(sorted(overrides.items()))
        sdef = self.registry.get(def_key)
        if sdef is None:
            NA = object()
            args = {
                "name": self.name,
                "flags": self.flags,
                "registry": self.registry,
            }
            for attr in self.ARGS:
                value = getattr(source_definition, attr, NA)
                if value is not NA:
                    args[attr] = value
            if overrides:
                args.update(overrides)
            ident = next(self.lang_ids)
            args.update(
                _id=ident,
                _lang_ids=self.lang_ids,
                _ends=ends,
                _next=next_def,
                _key=(self.key + " " + ident) if self.key else ident
            )
            if len(args["_key"]) > 200:
                raise Error("max recursion exceeded: {} {}".format(def_key, args))
            #log.debug("make_definition %s/%s\n  %s", self.name, def_key,
            #    "\n  ".join("%s: %r" % it for it in sorted(args.items())))
            #print(self.name, (self.id, args["_key"]), name)
            sdef = type(self)(self.filename, **args)
            self.registry[def_key] = sdef
        return sdef


class MatchInfo(str):

    __slots__ = ('event', 'next', 'lang')

    def __new__(cls, value, next=None, lang=None):
        info = super().__new__(cls, value)
        info.event = next is not None
        info.next = next
        info.lang = lang
        return info

    def __repr__(self):
        return super().__repr__() + ("n" if self.next else "")


PLAIN_TEXT = NoHighlight("Plain Text", "x")
EMPTY_REGEX = re.compile("")
WORD_CHAR = re.compile(r"\w", re.UNICODE)


class DynamicRange:
    class _none:
        default_text_color = const.DELIMITER
        rules = []
    def __init__(self, lang_pattern, color_name=""):
        if isinstance(lang_pattern, str):
            lang_pattern = re.compile(lang_pattern, re.MULTILINE)
        self.lang_pattern = lang_pattern
        self.color_name = color_name
    def make_definition(self, parent, lookup_syntax, *args, **kw):
        ident = next(parent.lang_ids)
        none = parent.make_definition(self._none, *args, **kw)
        sdef = type(self)(self.lang_pattern, self.color_name)
        sdef.key = (parent.key + " " + ident) if parent.key else ident
        sdef.parent = parent
        sdef.lookup_syntax = lookup_syntax
        sdef.syntax_args = (args, kw)
        sdef.color = parent.get_color(self.color_name)
        sdef.none = MatchInfo(parent.get_color(), none, parent)
        return sdef
    @property
    def regex(self):
        return self
    @property
    def wordinfo(self):
        return self
    @property
    def text_color(self):
        return self.parent.text_color
    def finditer(self, string, offset):
        match = self.lang_pattern.match(string, offset)
        if match:
            self.last_match_value = match.group(0).strip()
        else:
            self.last_match_value = ""
            match = EMPTY_REGEX.match(string, offset)
        return [match]
    def get(self, key):
        # HACK must be called after `finditer` as in `Highlighter.scan`
        name = self.last_match_value
        if name:
            args, kw = self.syntax_args
            sdef = self.lookup_syntax(name, *args, **kw)
            if sdef is not None:
                return MatchInfo(self.color, sdef, self.parent)
        return self.none


class RE(object):
    next = None
    def __init__(self, pattern):
        self.pattern = pattern
    def __repr__(self):
        return "RE(%r)" % (self.pattern,)
    def __eq__(self, other):
        return isinstance(other, type(self)) and self.pattern == other.pattern
    def __ne__(self, other):
        return not (self == other)
    def __hash__(self):
        return hash((RE, self.pattern))


class End(RE):
    def __init__(self, pattern, next_def, name, lang):
        self.pattern = pattern
        self.next = next_def
        self.name = name
        self.lang = lang
    def __repr__(self):
        next_name = self.next.name if self.next else None
        return "<End %r %s %s>" % (self.pattern, self.name, next_name)
    def __eq__(self, other):
        return isinstance(other, type(self)) \
            and self.pattern == other.pattern \
            and self.next == other.next \
            and self.name == other.name
    def __hash__(self):
        return hash((End, self.pattern, self.next, self.name))


def is_syntax_class(obj):
    return hasattr(obj, "rules") \
        or hasattr(obj, "word_groups") \
        or hasattr(obj, "delimited_ranges")

def lookahead(pattern):
    # could return wrong result sometimes, probaby doesn't matter
    if pattern.startswith("(?=") and pattern.endswith(")"):
            # and ")" not in pattern[3:-1]:
        return pattern
    return r"(?={})".format(pattern)

def escape(token, word_char=None):
    if hasattr(token, "pattern"):
        return token.pattern
    token = re.escape(token)
    if word_char and token:
        if word_char.match(token[0]):
            token = r"\b" + token
        if word_char.match(token[-1]):  # does wrong thing for r"\n"
            token = token + r"\b"
    return token.replace(re.escape("\n"), "\\n")

def disjunction(tokens):
    return "|".join(escape(t, WORD_CHAR) for t in tokens)

def may_match(token, patterns=[r"\b\B", r"\B\b"]):
    return escape(token) not in patterns

def unique(items):
    seen = set()
    return (item for item in items if item not in seen and not seen.add(item))
