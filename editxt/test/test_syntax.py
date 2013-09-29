# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
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
from tempfile import gettempdir

from AppKit import *
from Foundation import *
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import TestConfig, untested, check_app_state

import editxt.constants as const
import editxt.syntax as mod
from editxt.syntax import SyntaxFactory, SyntaxCache, SyntaxDefinition
from editxt.syntax import NoHighlight, PLAIN_TEXT

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
                "disabled": dict(name="dis", disabled=True, filepatterns=[]), # should cause info log

                # these should cause error log
                "incomplete1": {},
                "incomplete2": dict(name="none"),
                "incomplete3": dict(filepatterns=[]),

                # should only register twice despite duplication
                "python": dict(name="python", filepatterns=["*.py", "*.py", "*.pyw"]),

                "sql": dict(name="sequel", filepatterns=["*.sql"]),
                "text": dict(name="text", filepatterns=["*.txt"]),
                "text2": dict(name="text", filepatterns=["*.txt", "*.text"]),
                "text3": dict(name="text", disabled=True, filepatterns=["*.txt", "*.text"]),
            }
            glob(os.path.join(c.path, "*" + const.SYNTAX_DEF_EXTENSION)) >> sorted(info)
            def do(name):
                data = dict(info[name])
                if name.startswith("incomplete"):
                    raise Exception("incomplete definition: %r" % (data,))
                data.setdefault("disabled", False)
                if "filepatterns" in data:
                    data["filepatterns"] = set(data["filepatterns"])
                return type("sdef", (object,), data)()
            expect(load(ANY)).count(len(info)).call(do)
            for fname, data in sorted(info.items()):
                if fname.startswith("incomplete"):
                    log.error(ANY, fname, exc_info=True)
                else:
                    pats = ", ".join(sorted(set(data.get("filepatterns", []))))
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
    defaults = dict(
        comment_token="",
        word_groups=[],
        delimited_ranges=[],
    )
    def test(c):
        m = Mocker()
        sf = SyntaxFactory()
        execf = m.replace(__builtins__, 'execfile', dict=True)
        def do(filename, ns):
            ns.update(__builtins__="__builtins__")
            return ns.update(c.info)
        if c.error is not Exception:
            expect(execf("<filename>", ANY)).call(do)
        else:
            expect(execf("<filename>", ANY)).throw(c.error)
        values = dict(defaults)
        values.update(c.info)
        with m:
            if c.error is None:
                res = sf.load_definition("<filename>")
                for name, value in values.items():
                    if name == "filepatterns":
                        value = set(value)
                    eq_(getattr(res, name), value, name)
            else:
                assert_raises(c.error, sf.load_definition, "<filename>")
    c = TestConfig(error=None)
    yield test, c(info=dict(name="dis", filepatterns=[], disabled=True))
    yield test, c(info={}, error=Exception)
    yield test, c(info=dict(name="none"), error=TypeError)
    yield test, c(info=dict(filepatterns=[]), error=TypeError)
    yield test, c(info=dict(name="python", filepatterns=["*.py", "*.py", "*.pyw"]))
    yield test, c(info=dict(name="sequel", filepatterns=["*.sql"]))
    yield test, c(info=dict(name="text", filepatterns=["*.txt"], comment_token="X"))
    yield test, c(info=dict(name="text", filepatterns=["*.txt"]))

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

def test_SyntaxCache_syntaxdef_default():
    syn = SyntaxCache()
    eq_(syn.syntaxdef, PLAIN_TEXT) # check default
    eq_(syn.filename, None) # check default

def test_SyntaxCache_syntaxdef():
    m = Mocker()
    syn = SyntaxCache()
    syn.cache.append("something")
    sd = m.mock(SyntaxDefinition)
    with m:
        assert syn.syntaxdef is not sd
        syn.syntaxdef = sd
        eq_(syn.cache, [])
        eq_(syn.syntaxdef, sd)
        syn.cache.append("something")
        eq_(syn.cache, ["something"])
        eq_(syn.syntaxdef, sd)

def test_NoHighlight_scan():
    def test(c):
        m = Mocker()
        nh = NoHighlight("Test", "")
        setcolor = m.mock()
        def check(x, arg, y, z):
            assert isinstance(arg, NSRange), "wrong value: %r" % (arg,)
            eq_(arg, NSRange(len(c.value) - 1, 0))
        if c.offset == 0:
            expect(setcolor(None, ANY, 0, None)).call(check)
        with m:
            nh.scan(c.value, setcolor, c.offset)
    c = TestConfig(offset=0, value="")
    yield test, c
    yield test, c(value="abc")
    yield test, c(offset=1)

