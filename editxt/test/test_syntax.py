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
from contextlib import closing
from difflib import unified_diff
from itertools import islice
from tempfile import gettempdir

import AppKit as ak
import Foundation as fn
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import TestConfig, gentest, tempdir

import editxt.constants as const
import editxt.syntax as mod
from editxt.config import Config, String
from editxt.syntax import SyntaxFactory, Highlighter, SyntaxDefinition
from editxt.syntax import NoHighlight, PLAIN_TEXT, RE
from editxt.theme import Theme

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
                    data["file_patterns"] = set(data["file_patterns"])
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
                    if name == "file_patterns":
                        value = set(value)
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
    config = Config(None, schema={"theme": {
        "text_color": String(default="text_color"),
        "syntax": {}
    }})
    config.data = {"theme": {"syntax": {
        "default": {
            "keyword": "keyword",
            "builtin": "builtin",
            "operator": "operator",
            "string": "string",
            "string.multiline.single-quote": "string.multiline.single-quote",
            "comment": "comment",
            "tag": "tag",
            "attribute": "attribute",
            "value": "value",
            "punctuation": "punctuation",
        },
        "JavaScript": {
            "string": "js.string"
        },
    }}}
    theme = Theme(config)

    class Text(BaseText):
        def colors(self, highlighter):
            seen = set()
            lines = []
            length = len(self)
            full = rng = (0, length)
            fg_color = ak.NSForegroundColorAttributeName
            long_range = self.attribute_atIndex_longestEffectiveRange_inRange_
            while rng[1] > 0:
                lang, xrng = long_range(SYNTAX_RANGE, rng[0], None, rng)
                lang = (" " + highlighter.langs[lang].name) if lang else ""
                #print(lang, xrng)
                level = len(lang.split()) if lang else 0
                xend = sum(xrng)
                while True:
                    attr, attr_range = long_range(SYNTAX_TOKEN, xrng[0], None, full)
                    colr, x = long_range(fg_color, xrng[0], NULL, full)
                    if attr:
                        print(attr)
                        attr = attr.rsplit(" ", 1)[-1]
                        language = lang if xrng[0] <= attr_range[0] else (" ~" + lang[1:])
                        language = language.replace(attr + ".", "$.")
                        lines.append("{}{} {}{}".format(
                            "  " * level,
                            self[attr_range[0]: sum(attr_range)],
                            attr if attr == colr else "{} {}".format(attr, colr),
                            language,
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
        if isinstance(lang, Highlighter):
            hl = lang
        else:
            hl = Highlighter(theme)
            hl.syntaxdef = get_syntax_definition(lang)
        text = string if isinstance(string, Text) else Text(string)
        if edit:
            start, length, insert = edit
            text.replaceCharactersInRange_withAttributedString_(
                    (start, length), Text(insert).store)
            hl.color_text(text, (start, len(insert)))
        else:
            hl.color_text(text)
        a = text.colors(hl)
        b = dedent(expect).strip().split("\n") if expect else []
        assert a == b, "\n" + "\n".join(
                unified_diff(b, a, "expected", "actual", lineterm=""))

    def edit(lang, string, expect, *pairs):
        hl = Highlighter(theme)
        hl.syntaxdef = get_syntax_definition(lang)
        hl.theme = theme
        assert len(pairs) % 2 == 0, "got odd number of edit/expect pairs"
        text = Text(string)
        yield test(hl, text, expect)
        for edit, expect in zip(islice(pairs, 0, None, 2),
                                islice(pairs, 1, None, 2)):
            yield test(hl, text, expect, edit)

    text = Text("def f(self, x): x # TODO")
    hl = Highlighter(theme)
    hl.syntaxdef = get_syntax_definition("python")
    hl.theme = theme
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
        "'''    for x",
        "'''    for x string.multiline.single-quote")
    yield test("python",
        "'''    for x'''",
        "'''    for x''' string.multiline.single-quote")
    yield test("python",
        '''"""A doc string\nWith multiple lines\n"""''',
        '''
        """A doc string string.multiline.double-quote string
          With multiple lines string.multiline.double-quote string Python
          """ string.multiline.double-quote string Python
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
          def f( string.multiline.double-quote string Python
        ''',

        (2, 1, ''),
        """
        "" string.double-quote string
        def keyword
        """,
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
          tal:wrap attribute Markup
          = punctuation Markup
          '<span>' value Markup
        """)
    yield test("markup",
        """<div class='ext' data id="xpr"> </div>""",
        """
        <div tag
          class attribute Markup
          = punctuation Markup
          'ext' value Markup
          data attribute Markup
          id attribute Markup
          = punctuation Markup
          "xpr" value Markup
          > tag Markup
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
          html attribute Markup
          encoding attribute Markup
          = punctuation Markup
          "utf-8" value Markup
          > tag.doctype tag Markup
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
          ]]> tag.cdata tag Markup
        """)
    yield test("markup",
        "<style attr='value'></style>",
        """
        <style tag
          attr attribute Markup
          = punctuation Markup
          'value' value Markup
          ></style> tag Markup
        """)
    yield test("markup",
        "<script>var x = 'y';</script>",
        """
        <script> tag
          var keyword JavaScript
          'y' string.single-quote js.string JavaScript
          </script> tag JavaScript
        """)
#    yield test("markup",
#        "<style>.error { color: red; }</style>",
#        """
#        <style> tag
#          .error class css
#          { punctuation css
#          color attribute css
#          : punctuation css
#          red value css
#          ; punctuation css
#          } punctuation css
#          </style> tag css
#        """)

    yield test("javascript",
        "var x = 'y';",
        """
        var keyword
        'y' string.single-quote js.string
        """)

    # TODO test and change match.lastgroup ??

    class lang:
        name = "lang"
        class sub:
            word_groups = [("keyword", ["for"])]
        word_groups = [("keyword", ["for", "in"])]
        delimited_ranges = [("tag", "[", ["]"], sub)]
    lang = get_syntax_definition("python").make_definition("lang", lang)
    yield from edit(lang, "for x in [y for y in z]:",
        """
        for keyword
        in keyword
        [ tag
          for keyword lang
          ] tag lang
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
          for keyword lang
          ] tag lang
        """,

        (4, 6, "[x for "),
        """
        for keyword
        [ tag
          for keyword lang
          for keyword lang
          ] tag lang
        """,
        )

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
