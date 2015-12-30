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
import logging
import os
import re
from contextlib import closing
from difflib import unified_diff
from itertools import islice
from tempfile import gettempdir

import AppKit as ak
import Foundation as fn
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import TestConfig, gentest, tempdir, replattr
from testil import CaptureLogging, Regex

import editxt.theme
import editxt.constants as const
import editxt.syntax as mod
from editxt.config import Config, String
from editxt.syntax import SyntaxFactory, Highlighter, SyntaxDefinition
from editxt.syntax import NoHighlight, PLAIN_TEXT, RE

log = logging.getLogger(__name__)

def test_SyntaxFactory_init():
    sf = SyntaxFactory()
    eq_(sf.registry, {"*.txt": PLAIN_TEXT})
    eq_(sf.definitions, [PLAIN_TEXT])

def test_SyntaxFactory_load_definitions():
    def test(c):
        m = Mocker()
        sf = SyntaxFactory()
        log = m.replace("editxt.syntax.log")
        glob = m.replace("glob.glob")
        exists = m.replace("os.path.exists")
        load = sf.load_definition = m.mock()
        if c.path and exists(c.path) >> c.exists:
            info = {
                "disabled": dict(name="dis", disabled=True, file_patterns=[]), # should cause info log

                # these should cause error log
                "incomplete1": {},
                "incomplete2": dict(name="none"),
                "incomplete3": dict(file_patterns=[]),

                # should only register twice despite duplication
                "python": dict(name="python", file_patterns=["*.py", "*.py", "*.pyw"]),

                "sql": dict(name="sequel", file_patterns=["*.sql"]),
                "text": dict(name="text", file_patterns=["*.txt"]),
                "text2": dict(name="text", file_patterns=["*.txt", "*.text"]),
                "text3": dict(name="text", disabled=True, file_patterns=["*.txt", "*.text"]),
            }
            glob(os.path.join(c.path, "*" + const.SYNTAX_DEF_EXTENSION)) >> sorted(info)
            def do(name):
                data = dict(info[name], id=name)
                if name.startswith("incomplete"):
                    raise Exception("incomplete definition: %r" % (data,))
                data.setdefault("disabled", False)
                if "file_patterns" in data:
                    data["file_patterns"] = data["file_patterns"]
                return type("sdef", (object,), data)()
            expect(load(ANY)).count(len(info)).call(do)
            for fname, data in sorted(info.items()):
                if fname.startswith("incomplete"):
                    log.error(ANY, fname, exc_info=True)
                else:
                    pats = ", ".join(sorted(set(data.get("file_patterns", []))))
                    stat = [data["name"], "[%s]" % pats]
                    if fname in ("text", "text2", "text4"):
                        stat.extend(["overrides", "*.txt"])
                    elif fname in ("disabled", "text3"):
                        stat.append("DISABLED")
                    stat.append(fname)
                    log.info(ANY, " ".join(stat))
            patterns = set(["*.py", "*.pyw", "*.sql", "*.text", "*.txt"])
        else:
            patterns = set(["*.txt"])
        with m:
            sf.load_definitions(c.path)
            eq_(set(sf.registry), patterns)
    c = TestConfig(path="/path/to/defs", exists=True)
    yield test, c
    yield test, c(path="")
    yield test, c(exists=False)

def test_SyntaxFactory_load_definition():
    import builtins
    defaults = dict(
        comment_token="",
        word_groups=(),
        delimited_ranges=(),
    )
    def test(c):
        with tempdir() as tmp:
            sf = SyntaxFactory()
            filename = os.path.join(tmp, "file")
            with open(filename, "w", encoding="utf-8") as fh:
                if c.error is not Exception:
                    fh.write("\n".join("{} = {!r}".format(k, v)
                        for k, v in c.info.items()))
                else:
                    fh.write("raise {}".format(c.error.__name__))
            values = dict(defaults)
            values.update(c.info)
            if c.error is None:
                res = sf.load_definition(filename)
                for name, value in values.items():
                    eq_(getattr(res, name), value, name)
            else:
                assert_raises(c.error, sf.load_definition, filename)
    c = TestConfig(error=None)
    yield test, c(info=dict(name="dis", file_patterns=[], disabled=True))
    yield test, c(info={}, error=Exception)
    yield test, c(info=dict(name="none"))
    yield test, c(info=dict(file_patterns=[]))
    yield test, c(info=dict(name="python", file_patterns=["*.py", "*.py", "*.pyw"]))
    yield test, c(info=dict(name="sequel", file_patterns=["*.sql"]))
    yield test, c(info=dict(name="text", file_patterns=["*.txt"], comment_token="X"))
    yield test, c(info=dict(name="text", file_patterns=["*.txt"]))

def test_SyntaxFactory_index_definitions():
    from editxt.valuetrans import SyntaxDefTransformer
    class FakeDef(object):
        def __init__(self, name):
            self.name = name
        def __repr__(self):
            return "<%s %x>" % (self.name, id(self))
    text1 = FakeDef("Plain Text")
    text2 = FakeDef("Plain Text")
    python = FakeDef("Python")
    sf = SyntaxFactory()
    sf.registry = {
        "*.txt": text1,
        "*.text": text2,
        "*.txtx": text1,
        "*.py": python,
    }
    defs = sorted([text1, text2, python], key=lambda d:(d.name, id(d)))
    m = Mocker()
    vt = m.replace(mod, 'NSValueTransformer')
    st = vt.valueTransformerForName_("SyntaxDefTransformer") >> \
        m.mock(SyntaxDefTransformer)
    st.update_definitions(defs)
    with m:
        sf.index_definitions()
    eq_(sf.definitions, defs)

def test_SyntaxFactory_get_definition():
    sf = SyntaxFactory()
    sf.registry["*.txt"] = "<syntax def>"
    eq_(sf.get_definition("somefile.txt"), "<syntax def>")
    eq_(sf.get_definition("somefile.text"), PLAIN_TEXT)

def test_Highlighter_syntaxdef_default():
    syn = Highlighter(None)
    eq_(syn.syntaxdef, PLAIN_TEXT) # check default
    eq_(syn.filename, None) # check default

def test_Highlighter_color_text():
    from objc import NULL
    from textwrap import dedent
    from editxt.platform.text import Text as BaseText
    from editxt.syntax import SYNTAX_RANGE, SYNTAX_TOKEN

    class Text(BaseText):
        def colors(self, highlighter):
            seen = set()
            lines = []
            length = len(self)
            full = rng = (0, length)
            fg_color = ak.NSForegroundColorAttributeName
            long_range = self.attribute_atIndex_longestEffectiveRange_inRange_
            while rng[1] > 0:
                key, xrng = long_range(SYNTAX_RANGE, rng[0], None, rng)
                lang = (highlighter.langs[key][0].name if key else "")
                if lang == highlighter.syntaxdef.name:
                    lang = ""
                #print(lang.strip(), xrng)
                level = 1 if lang else 0
                xend = sum(xrng)
                while True:
                    attr, attr_range = long_range(SYNTAX_TOKEN, xrng[0], None, full)
                    colr, x = long_range(fg_color, xrng[0], NULL, full)
                    text = self[attr_range[0]: sum(attr_range)]
                    if attr or colr and colr != "text_color" and text.strip():
                        if attr:
                            attr_name = attr
                        else:
                            # default text color, not a matched token
                            attr_name = "{} {} -".format(lang, colr)
                        print(attr_name.ljust(30), repr(text)[1:-1][:40])
                        attr = attr.rsplit(" ", 1)[-1] if attr else colr
                        language = lang if xrng[0] <= attr_range[0] else ("~" + lang)
                        language = language.replace(attr + ".", "$.")
                        lines.append("{}{} {}{}".format(
                            "  " * level,
                            text,
                            attr if attr == colr else "{} {}".format(attr, colr),
                            (" " + language) if language else "",
                        ))
                    start = sum(attr_range)
                    if start >= xend:
                        xend = start
                        break
                    xrng = (start, xend - start)
                rng = (xend, length - xend)
            return lines
    @gentest
    def test(lang, string, expect, edit=None):
        theme.reset()
        if isinstance(lang, Highlighter):
            hl = lang
        else:
            hl = Highlighter(theme)
            hl.syntaxdef = get_syntax_definition(lang)
        text = string if isinstance(string, Text) else Text(dedent(string))
        get_color = lambda value: value
        with replattr(editxt.theme, "get_color", get_color, sigcheck=False), \
            CaptureLogging(mod) as log:
            if edit:
                start, length, insert = edit
                text[(start, length)] = Text(insert)
                hl.color_text(text, (start, len(insert)))
            else:
                hl.color_text(text)
        errors = log.data.get("error")
        assert not errors, "Errors logged:\n" + "\n---\n\n".join(errors)
        a = text.colors(hl)
        b = dedent(expect).strip().split("\n") if expect else []
        assert a == b, "\n" + "\n".join(
                unified_diff(b, a, "expected", "actual", lineterm=""))

    def edit(lang, string, expect, *pairs):
        hl = Highlighter(theme)
        hl.syntaxdef = get_syntax_definition(lang)
        assert len(pairs) % 2 == 0, "got odd number of edit/expect pairs"
        text = Text(string)
        yield test(hl, text, expect)
        for edit, expect in zip(islice(pairs, 0, None, 2),
                                islice(pairs, 1, None, 2)):
            yield test(hl, text, expect, edit)

    config = Config(None, schema={"theme": {
        "text_color": String("text_color"),
        "syntax": {
            "default": {
                "attribute": String("attribute"),
                "builtin": String("builtin"),
                "comment": String("comment"),
                "group": String("group"),
                "header": String("header"),
                "keyword": String("keyword"),
                "name": String("name"),
                "operator": String("operator"),
                "punctuation": String("punctuation"),
                "string": String("string"),
                "string.multiline.single-quote": String("string.multiline.single-quote"),
                "tag": String("tag"),
                "value": String("value"),
            },
            "JavaScript": {
                "string": String("js.string")
            },
        },
    }})
    theme = editxt.theme.Theme(config)

    text = Text("def f(self, x): x # TODO")
    hl = Highlighter(theme)
    hl.syntaxdef = get_syntax_definition("python")
    hl.color_text(text)
    yield test(mod.PLAIN_TEXT, text, "")

    yield test("python",
        "def f(self, x): x # TODO",
        """
        def keyword
        self builtin
        # TODO comment.single-line comment
        """)
    yield test("python",
        "'\nfor x",
        """
        ' string.single-quote string
        for keyword
        """)
    yield test("python",
        '"\ndef f(',
        """
        " string.double-quote string
        def keyword
        """)
    yield test("python",
        r'''
        x = "\""
        y = "\\"
        z = "\\\""
        Q = "\\\\\""
        ''',
        r"""
        "\"" string.double-quote string
        "\\" string.double-quote string
        "\\\"" string.double-quote string
        "\\\\\"" string.double-quote string
        """)
    yield test("python",
        r"""
        x = r"\""
        y = r"\\"
        z = r"\\\""
        Q = r"\\\\\""
        """,
        r"""
        r" string.double-quote string
          \" operator.escape operator Regular Expression
        " string.double-quote string
        r" string.double-quote string
          \\ operator.escape operator Regular Expression
        " string.double-quote string
        r" string.double-quote string
          \\\" operator.escape operator Regular Expression
        " string.double-quote string
        r" string.double-quote string
          \\\\\" operator.escape operator Regular Expression
        " string.double-quote string
        """)
    yield test("python",
        "'''    for x",
        "'''    for x string.multiline.single-quote")
    yield test("python",
        "'''    for x'''",
        "'''    for x''' string.multiline.single-quote")
    yield test("python",
        '''"""A doc string\nWith multiple lines\n"""''',
        '''
        """A doc string string.multiline.double-quote string
        With multiple lines string.multiline.double-quote string
        """ string.multiline.double-quote string
        ''')
    yield from edit("python", "\ndef f(",
        """
        def keyword
        """,

        (0, 0, '"'),
        """
        " string.double-quote string
        def keyword
        """,

        (1, 0, '"'),
        """
        "" string.double-quote string
        def keyword
        """,

        (2, 0, '"'),
        '''
        """ string.multiline.double-quote string
        def f( string.multiline.double-quote string
        ''',

        (2, 1, ''),
        """
        "" string.double-quote string
        def keyword
        """,
        )
    yield from edit("python", "def\n",
        """
        def keyword
        """,

        (0, 4, ''), # bug: error on delete all content
        "",
        )
    yield from edit("python", r""" "word" """,
        """
        "word" string.double-quote string
        """,
        (1, 0, 'r'),
        """
        r" string.double-quote string
          word string Regular Expression
        " string.double-quote string
        """,
        (1, 1, ''),
        """
        "word" string.double-quote string
        """,
        )
    yield from edit("python", r"""r"(?P<xyz>)" """,
        """
        r" string.double-quote string
          (?P< group.named group Regular Expression
          xyz name Regular Expression
          > group.named group Regular Expression
          ) group Regular Expression
        " string.double-quote string
        """,
        (4, 0, ' '),
        """
        r" string.double-quote string
          ( string Regular Expression
          ? keyword Regular Expression
           P<xyz> string Regular Expression
          ) group Regular Expression
        " string.double-quote string
        """,
        (4, 1, ''),
        """
        r" string.double-quote string
          (?P< group.named group Regular Expression
          xyz name Regular Expression
          > group.named group Regular Expression
          ) group Regular Expression
        " string.double-quote string
        """,
        )
    yield from edit("python", '''
        r""" [\s] """
        []
        ' """ """ '
        ''',
        '''
        r""" string.multiline.double-quote string
          [ keyword.set keyword Regular Expression
          \s operator.class operator Regular Expression
          ] keyword.set keyword Regular Expression
        """ string.multiline.double-quote string
        ' """ """ ' string.single-quote string
        ''',
        (17, 1, ''),
        '''
        r""" string.multiline.double-quote string
          [ keyword.set keyword Regular Expression
          \s operator.class operator Regular Expression
        """ string.multiline.double-quote string
        ' """ """ ' string.single-quote string
        ''',
        (17, 0, ']'),
        '''
        r""" string.multiline.double-quote string
          [ keyword.set keyword Regular Expression
          \s operator.class operator Regular Expression
          ] keyword.set keyword Regular Expression
        """ string.multiline.double-quote string
        ' """ """ ' string.single-quote string
        ''',
        )

    yield test("markup",
        """<div""",
        """
        <div tag
        """)
    yield test("markup",
        """<div <span>""",
        """
        <div tag
        <span> tag
        """)
    yield test("markup",
        """<div tal:wrap='<span>'""",
        """
        <div tag
        tal:wrap attribute
        = tag.punctuation tag
        '<span>' value
        """)
    yield test("markup",
        """<div class='ext' data id="xpr"> </div>""",
        """
        <div tag
        class attribute
        = tag.punctuation tag
        'ext' value
        data attribute
        id attribute
        = tag.punctuation tag
        "xpr" value
        > tag
        </div> tag
        """)
    yield test("markup",
        """<!DOCTYPE>\n<div/>""",
        """
        <!DOCTYPE> tag.doctype tag
        <div/> tag
        """)
    yield test("markup",
        """<!DOCTYPE html encoding="utf-8">\n<div/>""",
        """
        <!DOCTYPE tag.doctype tag
        html attribute
        encoding attribute
        = tag.punctuation tag
        "utf-8" value
        > tag.doctype tag
        <div/> tag
        """)
    yield test("markup",
        """<!---->""",
        """<!----> comment""")
    yield test("markup",
        """<!-- <head><style> -->""",
        """<!-- <head><style> --> comment""")
    yield test("markup",
        """<div><![CDATA[ abc <xyz> 3&""",
        """
        <div> tag
        <![CDATA[ tag.cdata tag
        """)
    yield test("markup",
        """<div><![cdata[ abc <xyz> 3& ]]>""",
        """
        <div> tag
        <![cdata[ tag.cdata tag
        ]]> tag.cdata tag
        """)
    yield test("markup",
        "<style attr='value'></style>",
        """
        <style tag
        attr attribute
        = tag.punctuation tag
        'value' value
        ></style> tag
        """)
    yield test("markup",
        "<script>var x = 'y';</script>",
        """
        <script> tag
          var keyword JavaScript
          'y' string.single-quote js.string JavaScript
        </script> tag
        """)
    yield test("markup",
        "<style>.error { color: red; }</style>",
        """
        <style> tag
          .error selector-class text_color CSS
          { text_color CSS
          color attribute CSS
          : text_color CSS
          ; text_color CSS
          } text_color CSS
        </style> tag
        """)

    yield test("markdown",
        """
        ```Python
        def inc(arg):
            return arg + 1
        ```
        """,
        """
        ``` code text_color
        Python tag
          def keyword Python
          return keyword Python
        ``` code text_color
        """)

    yield test("markdown",
        """
        ```unknown-language-name
        def inc(arg):
            return arg + 1
        ```
        """,
        """
        ``` code text_color
        unknown-language-name text_color
        ``` code text_color
        """)

    yield test("markdown",
        """
        *Clojure REPL*

        ```clojure-repl
        user=> (defn f [x y]
          #_=>   (+ x y))
        #'user/f
        user=> (f 5 7)
        12
        user=> nil
        nil
        ```

        *Clojure*
        """,
        """
        *Clojure REPL* emphasis text_color
        ``` code text_color
        clojure-repl tag
          user=> meta text_color Clojure REPL
          ( text_color Clojure
          defn builtin-name text_color Clojure
          [ text_color Clojure
          ] text_color Clojure
            #_=> meta text_color Clojure REPL
          ( text_color Clojure
          + builtin-name text_color Clojure
          ) text_color Clojure
          user=> meta text_color Clojure REPL
          ( text_color Clojure
          f name Clojure
          5 number text_color Clojure
          7 number text_color Clojure
          ) text_color Clojure
          user=> meta text_color Clojure REPL
          nil literal text_color Clojure
        ``` code text_color
        *Clojure* emphasis text_color
        """)

    yield test("javascript",
        "var x = 'y';",
        """
        var keyword
        'y' string.single-quote js.string
        """)
    yield test("javascript",
        "var regex = /y*/ig;",
        """
        var keyword
        / regexp text_color
          * keyword Regular Expression
        /ig regexp text_color
        """)
    yield test("javascript",
        "/[x-z/ig - var;",
        """
        / regexp text_color
          [ keyword.set keyword Regular Expression
          - operator.range operator Regular Expression
        /ig regexp text_color
        var keyword
        """)

    yield test("regular-expression",
        r"^a(.)c$",
        """
        ^ keyword
        ( group
        . keyword
        ) group
        $ keyword
        """)

    yield test("regular-expression",
        r"a(?:(.))c",
        """
        (?:( group
        . keyword
        )) group
        """)

    yield test("regular-expression",
        r" good (?# junk ) good (?=aft.r)(?!n.t)",
        """
        (?# junk ) comment
        (?= group
        . keyword
        )(?! group
        . keyword
        ) group
        """)

    yield test("regular-expression",
        r"(?<=b.hind)(?<!n.t)",
        """
        (?<= group
        . keyword
        )(?<! group
        . keyword
        ) group
        """)

    yield test("regular-expression",
        r"(.)?abc(?(1).|$)",
        """
        ( group
        . keyword
        ) group
        ? keyword
        (?(1) group
        .|$ keyword
        ) group
        """)

    yield test("regular-expression",
        r"\1 \01 \7654 \999",
        r"""
        \1 group.ref group
        \01 operator.escape.char operator
        \765 operator.escape.char operator
        \99 group.ref group
        """)

    yield test("regular-expression",
        r"\A \b \B \w \W \Z \\ \. \u0a79 \U000167295",
        r"""
        \A operator.class operator
        \b operator.class operator
        \B operator.class operator
        \w operator.class operator
        \W operator.class operator
        \Z operator.class operator
        \\ operator.escape operator
        \. operator.escape operator
        \u0a79 operator.escape.char operator
        \U00016729 operator.escape.char operator
        """)

    yield test("regular-expression",
        r"[-\wa-z\-\S-]",
        r"""
        [ keyword.set keyword
        \w operator.class operator
        - operator.range operator
        \- operator.escape operator
        \S operator.class operator
        ] keyword.set keyword
        """)

    yield test("regular-expression",
        r" [^-\wa-z\-\S-] ",
        r"""
        [^ keyword.set.inverse keyword
        \w operator.class operator
        - operator.range operator
        \- operator.escape operator
        \S operator.class operator
        ] keyword.set.inverse keyword
        """)

    # TODO test and change match.lastgroup ??

    class lang:
        class sub:
            word_groups = [("keyword", ["for"])]
        word_groups = [("keyword", ["for", "in"])]
        delimited_ranges = [("tag", "[", ["]"], sub)]
    lang = make_definition(lang)
    yield from edit(lang, "for x in [y for y in z]:",
        """
        for keyword
        in keyword
        [ tag
        for keyword
        ] tag
        """,

        (9, 1, ""),
        """
        for keyword
        in keyword
        for keyword
        in keyword
        """,
        )
    yield from edit(lang, "for x in [y for y in z]:",
        """
        for keyword
        in keyword
        [ tag
        for keyword
        ] tag
        """,

        (4, 6, "[x for "),
        """
        for keyword
        [ tag
        for keyword
        for keyword
        ] tag
        """,
        )

    class xkw:
        word_groups = [("name", ["x"])]
    class lang:
        name = "transition"
        class params:
            delimited_ranges = [
                ("group", "(", [")"], xkw),
            ]
        class func_name:
            word_groups = [("name", [RE(r"[a-z]+")])]
        word_groups = [("keyword", ["end"])]
        delimited_ranges = [
            ("keyword", "def", [RE(r"$"), params], func_name),
            ("tag", RE(r"[a-z]+\("), [")"], xkw),
        ]
    lang = make_definition(lang)
    yield test(lang, "def f(x) x + do(x + 1) end",
        """
        def keyword
        f name
        ( group
        x name
        ) group
        do( tag
        x name
        ) tag
        end keyword
        """)

    class lang:
        name = "recursive"
        word_groups = [("keyword", ["def"])]
        class call:
            word_groups = [("tag", ["do"])]
            delimited_ranges = [None]
        delimited_ranges = [
            ("group", "(", [")"], call),
        ]
    lang.call.delimited_ranges[0] = lang.delimited_ranges[0]
    lang = make_definition(lang)
    yield test(lang, "def (def do(do (def)))",
        """
        def keyword
        ( group
        do tag
        ( group
        do tag
        ( group
        ))) group
        """)

    class lang:
        name = "start-end-lang-no-body"
        word_groups = [("keyword", ["def"])]
        default_text = const.DELIMITER
        class _lparen:
            word_groups = [("_lparen", ["("])]
        class _rparen:
            word_groups = [("_rparen", [")"])]
        delimited_ranges = [
            ("group", _lparen, [_rparen]),
        ]
    lang = make_definition(lang)
    yield test(lang, "def (do def) def",
        """
        def keyword
        ( text_color
        do def group
        ) text_color
        def keyword
        """)

    def test_err(msg, *args):
        with CaptureLogging(mod) as log:
            test.test(*args)
            eq_(log.data["exception"], [Regex(msg)])

    class lang:
        name = "non-advancing-range"
        delimited_ranges = [
            ("group", RE(r"(?=.)"), [RE(r"\b|\B")]),
        ]
    lang = make_definition(lang)
    yield test_err, "non-advancing range: index=0 ", lang, "a", ""

    class lang:
        name = "infinite-language-recursion"
        delimited_ranges = []
    lang.delimited_ranges.append(("group", RE(r"(?=.)"), [RE(r"x")], lang))
    lang = make_definition(lang)
    yield test_err, "max recursion exceeded", lang, "a", ""

def test_NoHighlight_wordinfo():
    nh = NoHighlight("Test", "")
    eq_(nh.wordinfo, None)

def get_syntax_definition(name, cache={}):
    if isinstance(name, NoHighlight):
        return name
    try:
        return cache[name].get(name)
    except KeyError:
        pass
    from os.path import abspath, dirname, join
    root = dirname(dirname(dirname(abspath(__file__))))
    loader = SyntaxFactory()
    loader.load_definitions(join(root, "resources/syntax"), False)
    cache[name] = loader
    return loader.get(name)

def make_definition(rules):
    NA = object()
    args = {"name": rules.__name__}
    for attr in SyntaxDefinition.ARGS:
        value = getattr(rules, attr, NA)
        if value is not NA:
            args[attr] = value
    reg = WeakrefableDict()
    sdef = SyntaxDefinition("", registry=reg, **args)
    sdef.root_registry = reg # maintain reference from root definition
    return sdef


class WeakrefableDict(dict): pass
