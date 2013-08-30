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
from __future__ import with_statement
import logging

from mocker import Mocker, expect, ANY, MATCH
from AppKit import *
from Foundation import *
from editxt.test.util import assert_raises, eq_, TestConfig, replattr

import editxt.constants as const
import editxt.commands as mod
from editxt.command.parser import ArgumentError, CommandParser, Int, Options

log = logging.getLogger(__name__)


def test_load_commands():
    cmds = mod.load_commands()
    eq_(cmds["text_menu_commands"], [
        mod.show_command_bar,
        mod.goto_line,
        mod.comment_text,
        mod.pad_comment_text,
        mod.indent_lines,
        mod.dedent_lines,
        mod.wrap_at_margin,
        mod.wrap_lines,
        mod.sort_lines,
        mod.reindent,
        mod.find,
        mod.clear_highlighted_text,
        mod.reload_config,
        mod.set_variable,
    ])
    eq_(set(cmds["input_handlers"]), set([
        "insertTab:",
        "insertBacktab:",
        "insertNewline:",
        "moveToBeginningOfLine:",
        "moveToLeftEndOfLine:",
        #"moveToBeginningOfLineAndModifySelection:",
        "deleteBackward:",
        #"deleteforward:",
    ]))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# built-in text command and input handler tests

def test_is_comment_range():
    def test(c):
        range = c.range if "range" in c else (0, len(c.text))
        eq_(mod.is_comment_range(c.text, range, c.token), c.result)
    c = TestConfig(token="x", result=False)
    yield test, c(text="")
    yield test, c(text="x\n\n")
    yield test, c(text="\n\n\n")
    yield test, c(text="\nx\n\n")
    yield test, c(text="\nx\nx\n")
    yield test, c(text="  z zyx\n\tx zyx\n")
    yield test, c(text="  x\n\tabc\n x\n\n")
    yield test, c(text="\nx\n\n", range=(1, 3))
    c = c(result=True)
    yield test, c(text="x")
    yield test, c(text="x\n")
    yield test, c(text="x\nx\n")
    yield test, c(text="x\nx\n\n\n")
    yield test, c(text="  x\n\tx\n x\n\n")
    yield test, c(text="  x zyx\n\tx zyx\n")
    yield test, c(text="\nx\n\n", range=(1, 1))
    yield test, c(text="\nx\n\n", range=(1, 2))
    yield test, c(text="\nx\nx\n", range=(1, 4))

def test_comment_line():
    def test(c):
        eq_(mod.comment_line(c.old, c.token, c.imode, c.isize, c.pad), c.new)
    c = TestConfig(token="x", imode=const.INDENT_MODE_TAB, isize=2, pad=True)
    yield test, c(old=u"", new=u"x ")
    yield test, c(old=u"\n", new=u"x \n")
    yield test, c(old=u"abc\n", new=u"x abc\n")
    yield test, c(old=u"\tabc\n", new=u"x \tabc\n")
    yield test, c(old=u"  abc\n", new=u"x   abc\n")
    c = c(isize=2, imode=const.INDENT_MODE_SPACE)
    yield test, c(old=u"abc\n", new=u"x abc\n")
    yield test, c(old=u"  abc\n", new=u"x  abc\n")
    yield test, c(old=u"    abc\n", new=u"x    abc\n")
    c = c(isize=3)
    yield test, c(old=u"abc\n", new=u"x abc\n")
    yield test, c(old=u"   abc\n", new=u"x  abc\n")
    yield test, c(old=u"      abc\n", new=u"x     abc\n")
    c = c(isize=4)
    yield test, c(old=u"abc\n", new=u"x abc\n")
    yield test, c(old=u"    abc\n", new=u"x   abc\n")
    yield test, c(old=u"        abc\n", new=u"x       abc\n")

    c = c(imode=const.INDENT_MODE_TAB, isize=2, pad=False)
    yield test, c(old=u"", new=u"x")
    yield test, c(old=u"\n", new=u"x\n")
    yield test, c(old=u"abc\n", new=u"xabc\n")
    yield test, c(old=u"\tabc\n", new=u"x\tabc\n")
    yield test, c(old=u"  abc\n", new=u"x  abc\n")
    c = c(isize=2, imode=const.INDENT_MODE_SPACE)
    yield test, c(old=u"abc\n", new=u"xabc\n")
    yield test, c(old=u"  abc\n", new=u"x  abc\n")
    yield test, c(old=u"    abc\n", new=u"x    abc\n")
    c = c(isize=3)
    yield test, c(old=u"abc\n", new=u"xabc\n")
    yield test, c(old=u"   abc\n", new=u"x   abc\n")
    yield test, c(old=u"      abc\n", new=u"x      abc\n")
    c = c(isize=4)
    yield test, c(old=u"abc\n", new=u"xabc\n")
    yield test, c(old=u"    abc\n", new=u"x    abc\n")
    yield test, c(old=u"        abc\n", new=u"x        abc\n")

def test_uncomment_line():
    def test(c):
        eq_(mod.uncomment_line(c.old, c.token, c.imode, c.isize, c.pad), c.new)
    c = TestConfig(token="x", imode=const.INDENT_MODE_TAB, isize=4, pad=True)
    yield test, c(old="", new="")
    yield test, c(old="\n", new="\n")
    yield test, c(old="x \n", new="\n")
    yield test, c(old="x abc\n", new="abc\n")
    yield test, c(old="  xabc\n", new="  abc\n")
    yield test, c(old="  x abc\n", new="  abc\n")
    yield test, c(old="\txabc\n", new="\tabc\n")
    yield test, c(old="\tx abc\n", new="\tabc\n")
    yield test, c(old="\tx\tabc\n", new="\t\tabc\n")
    yield test, c(old="\tx \tabc\n", new="\t\tabc\n")
    c = c(token="xx")
    yield test, c(old="", new="")
    yield test, c(old="\n", new="\n")
    yield test, c(old="x \n", new="x \n")
    yield test, c(old="xx \n", new="\n")
    c = c(token="x", imode=const.INDENT_MODE_SPACE)
    yield test, c(old="", new="")
    yield test, c(old="\n", new="\n")
    yield test, c(old="x \n", new="\n")
    #yield test, c(old="x       \n", new="\n")
    #yield test, c(old="x  \t   \n", new="\n")
    c = c(isize=2)
    yield test, c(old="xabc\n", new="abc\n")
    yield test, c(old="x abc\n", new="abc\n")
    yield test, c(old="x  abc\n", new="  abc\n")
    yield test, c(old="x   abc\n", new="  abc\n")
    yield test, c(old="x    abc\n", new="    abc\n")
    yield test, c(old="x     abc\n", new="    abc\n")
    c = c(isize=3)
    yield test, c(old="xabc\n", new="abc\n")
    yield test, c(old="x abc\n", new="abc\n")
    yield test, c(old="x  abc\n", new="   abc\n")
    yield test, c(old="x   abc\n", new="   abc\n")
    yield test, c(old="x    abc\n", new="   abc\n")
    yield test, c(old="x     abc\n", new="      abc\n")
    yield test, c(old="x      abc\n", new="      abc\n")
    yield test, c(old="x       abc\n", new="      abc\n")
    c = c(isize=4)
    yield test, c(old="xabc\n", new="abc\n")
    yield test, c(old="x abc\n", new="abc\n")
    yield test, c(old="x  abc\n", new="    abc\n")
    yield test, c(old="x   abc\n", new="    abc\n")
    yield test, c(old="x    abc\n", new="    abc\n")
    yield test, c(old="x     abc\n", new="    abc\n")
    yield test, c(old="x      abc\n", new="        abc\n")
    yield test, c(old="x       abc\n", new="        abc\n")
    yield test, c(old="x        abc\n", new="        abc\n")
    yield test, c(old="x         abc\n", new="        abc\n")

    c = c(imode=const.INDENT_MODE_TAB, isize=4, pad=False)
    yield test, c(old="", new="")
    yield test, c(old="\n", new="\n")
    yield test, c(old="x \n", new=" \n")
    yield test, c(old="x abc\n", new=" abc\n")
    yield test, c(old="  xabc\n", new="  abc\n")
    yield test, c(old="  x abc\n", new="   abc\n")
    yield test, c(old="\txabc\n", new="\tabc\n")
    yield test, c(old="\tx abc\n", new="\t abc\n")
    yield test, c(old="\tx\tabc\n", new="\t\tabc\n")
    yield test, c(old="\tx \tabc\n", new="\t \tabc\n")
    c = c(token="xx")
    yield test, c(old="", new="")
    yield test, c(old="\n", new="\n")
    yield test, c(old="x \n", new="x \n")
    yield test, c(old="xx \n", new=" \n")
    c = c(token="x", imode=const.INDENT_MODE_SPACE)
    yield test, c(old="", new="")
    yield test, c(old="\n", new="\n")
    yield test, c(old="x \n", new=" \n")
    c = c(isize=2)
    yield test, c(old="xabc\n", new="abc\n")
    yield test, c(old="x abc\n", new=" abc\n")
    yield test, c(old="x  abc\n", new="  abc\n")
    yield test, c(old="x   abc\n", new="   abc\n")
    yield test, c(old="x    abc\n", new="    abc\n")
    yield test, c(old="x     abc\n", new="     abc\n")
    c = c(isize=3)
    yield test, c(old="xabc\n", new="abc\n")
    yield test, c(old="x abc\n", new=" abc\n")
    yield test, c(old="x  abc\n", new="  abc\n")
    yield test, c(old="x   abc\n", new="   abc\n")
    yield test, c(old="x    abc\n", new="    abc\n")
    yield test, c(old="x     abc\n", new="     abc\n")
    yield test, c(old="x      abc\n", new="      abc\n")
    yield test, c(old="x       abc\n", new="       abc\n")
    c = c(isize=4)
    yield test, c(old="xabc\n", new="abc\n")
    yield test, c(old="x abc\n", new=" abc\n")
    yield test, c(old="x  abc\n", new="  abc\n")
    yield test, c(old="x   abc\n", new="   abc\n")
    yield test, c(old="x    abc\n", new="    abc\n")
    yield test, c(old="x     abc\n", new="     abc\n")
    yield test, c(old="x      abc\n", new="      abc\n")
    yield test, c(old="x       abc\n", new="       abc\n")
    yield test, c(old="x        abc\n", new="        abc\n")
    yield test, c(old="x         abc\n", new="         abc\n")

def test_text_commands():
    from editxt.document import TextDocument
    SAME = "<SAME AS INPUT>"
    def test(c):
        if c.eol != u"\n":
            c.input = c.input.replace(u"\n", c.eol)
            c.output = c.output.replace(u"\n", c.eol)
        result = TestConfig()
        default = False
        m = Mocker()
        tv = m.mock(NSTextView)
        (tv.doc_view.document.indent_mode << c.mode).count(0, None)
        (tv.doc_view.document.indent_size << c.size).count(0, None)
        (tv.doc_view.document.eol << c.eol).count(0, None)
        sel = NSMakeRange(*c.oldsel); (tv.selectedRange() << sel).count(0, None)
        (tv.string() << NSString.stringWithString_(c.input)).count(0, None)
        (tv.shouldChangeTextInRange_replacementString_(ANY, ANY) << True).count(0, None)
        ts = m.mock(NSTextStorage); (tv.textStorage() << ts).count(0, None)
        c.setup(m, c, TestConfig(locals()))
        def do_text(sel, repl):
            result.text = c.input[:sel[0]] + repl + c.input[sel[0] + sel[1]:]
        expect(ts.replaceCharactersInRange_withString_(ANY, ANY)).call(do_text).count(0, None)
        def do_sel(sel):
            result.sel = sel
        expect(tv.setSelectedRange_(ANY)).call(do_sel).count(0, None)
        expect(tv.didChangeText()).count(0, None)
        if c.scroll:
            tv.scrollRangeToVisible_(ANY)
        with m:
            c.method(tv, None, None)
            if "text" in result:
                eq_(result.text, c.output)
            else:
                eq_(c.output, SAME)
            if "sel" in result:
                eq_(result.sel, c.newsel)

    eols = [const.EOLS[mode] for mode in [
        const.NEWLINE_MODE_UNIX,
        const.NEWLINE_MODE_MAC,
        const.NEWLINE_MODE_WINDOWS,
        const.NEWLINE_MODE_UNICODE,
    ]]
    cbase = TestConfig(mode=const.INDENT_MODE_TAB, size=4, setup=lambda*a:None, scroll=True)


    c = cbase(method=mod.move_to_beginning_of_line, output=SAME)
    for eol in eols:
        c = c(eol=eol)
        yield test, c(input=u"", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=u" ", oldsel=(0, 0), newsel=(1, 0))
        yield test, c(input=u" ", oldsel=(1, 0), newsel=(0, 0))
        yield test, c(input=u"  ", oldsel=(0, 0), newsel=(2, 0))
        yield test, c(input=u"  ", oldsel=(1, 0), newsel=(2, 0))
        yield test, c(input=u"  ", oldsel=(2, 0), newsel=(0, 0))
        yield test, c(input=u"  x", oldsel=(0, 0), newsel=(2, 0))
        yield test, c(input=u"  x", oldsel=(1, 0), newsel=(2, 0))
        yield test, c(input=u"  x", oldsel=(2, 0), newsel=(0, 0))
        yield test, c(input=u"  \n ", oldsel=(0, 0), newsel=(2, 0))
        yield test, c(input=u"  \n ", oldsel=(1, 0), newsel=(2, 0))
        yield test, c(input=u"  \n ", oldsel=(2, 0), newsel=(0, 0))
        i = len(c.eol) - 1
        yield test, c(input=u"\n ", oldsel=(1 + i, 0), newsel=(2 + i, 0))
        yield test, c(input=u"    \n    ", oldsel=(5 + i, 0), newsel=(9 + i, 0))
        yield test, c(input=u"    \n    ", oldsel=(7 + i, 0), newsel=(9 + i, 0))
        yield test, c(input=u"    \n    ", oldsel=(9 + i, 0), newsel=(5 + i, 0))
        yield test, c(input=u"    \n    x", oldsel=(5 + i, 0), newsel=(9 + i, 0))
        yield test, c(input=u"    \n    x", oldsel=(7 + i, 0), newsel=(9 + i, 0))
        yield test, c(input=u"    \n    x", oldsel=(9 + i, 0), newsel=(5 + i, 0))
        yield test, c(input=u"    \n    \n", oldsel=(5 + i, 0), newsel=(9 + i, 0))
        yield test, c(input=u"    \n    \n", oldsel=(7 + i, 0), newsel=(9 + i, 0))
        yield test, c(input=u"    \n    \n", oldsel=(9 + i, 0), newsel=(5 + i, 0))

    c = cbase(method=mod.insert_newline)
    for eol in eols:
        c = c(eol=eol)
        yield test, c(input=u"", output=u"\n", oldsel=(0, 0))
        yield test, c(input=u" ", output=u" \n ", oldsel=(1, 0))
        yield test, c(input=u"  ", output=u"  \n  ", oldsel=(2, 0))
        yield test, c(input=u"    ", output=u" \n ", oldsel=(1, 0))
        yield test, c(input=u"\t", output=u"\t\n\t", oldsel=(1, 0))
        yield test, c(input=u"  a bc", output=u"  a\n  bc", oldsel=(3, 0))
        yield test, c(input=u"  a bc", output=u"  a\n  c", oldsel=(3, 1))
        yield test, c(input=u"a bc", output=u"a\nbc", oldsel=(1, 0))
        i = len(eol) - 1
        yield test, c(input=u" a\n b", output=u" a\n b\n ", oldsel=(5 + i, 0))
        yield test, c(input=u"\n x", output=u"\n\n x", oldsel=(1 + i, 0))


    c = cbase(method=mod.indent_lines)
    for eol in eols:
        i = len(eol) - 1
        c = c(eol=eol, mode=const.INDENT_MODE_TAB, scroll=False)
        yield test, c(input=u"", output=u"\t", oldsel=(0, 0), scroll=True)
        yield test, c(input=u"\t", output=u"\t\t", oldsel=(0, 0), scroll=True)
        yield test, c(input=u"x", output=u"\tx", oldsel=(0, 1), newsel=(0, 2))
        yield test, c(input=u"x\nxyz\n", output=u"\tx\nxyz\n", oldsel=(0, 1), newsel=(0, 3+i))
        yield test, c(input=u"x\nxyz\n", output=u"x\n\txyz\n", oldsel=(3, 1), newsel=(2+i, 5+i))
        yield test, c(input=u"x\nxyz\n", output=u"\tx\n\txyz\n", oldsel=(0, 4), newsel=(0, 8+2*i))
        yield test, c(input=u"x\n\nx\n", output=u"\tx\n\n\tx\n", oldsel=(0, 4+2*i), newsel=(0, 7+3*i))
        yield test, c(input=u"x \n\nx\n", output=u"\tx \n\n\tx\n", oldsel=(0, 5+2*i), newsel=(0, 8+3*i))
        c = c(mode=const.INDENT_MODE_SPACE, size=2)
        yield test, c(input=u"", output=u"  ", oldsel=(0, 0), scroll=True)
        yield test, c(input=u" ", output=u"  ", oldsel=(1, 0), scroll=True)
        yield test, c(input=u"  ", output=u"    ", oldsel=(0, 0), scroll=True)
        yield test, c(input=u"x", output=u"  x", oldsel=(0, 1), newsel=(0, 3))
        yield test, c(input=u"x\n\nx\n", output=u"  x\n\n  x\n", oldsel=(0, 4+2*i), newsel=(0, 9+3*i))
        yield test, c(input=u"x\nxyz\n", output=u"  x\nxyz\n", oldsel=(0, 1), newsel=(0, 4+i))
        yield test, c(input=u"x\nxyz\n", output=u"x\n  xyz\n", oldsel=(3, 1), newsel=(2+i, 6+i))
        yield test, c(input=u"x\nxyz\n", output=u"  x\n  xyz\n", oldsel=(0, 4), newsel=(0, 10+2*i))
        yield test, c(input=u"x\rxyz\n", output=u"  x\r  xyz\n", oldsel=(0, 4), newsel=(0, 10+i))
        yield test, c(input=u"x\u2028xyz\n", output=u"  x\u2028  xyz\n", oldsel=(0, 4), newsel=(0, 10+i))
        # TODO convert leading tabs to spaces (and vice versa)
        #yield test, c(input=u"\tx\n\txyz\n", output=u"    x\n    xyz\n",
        #    oldsel=(0, 6), newsel=(0, 14+2*i))
        c = c(size=4)
        yield test, c(input=u"", output=u"    ", oldsel=(0, 0), scroll=True)
        yield test, c(input=u" ", output=u"    ", oldsel=(1, 0), scroll=True)
        yield test, c(input=u"  ", output=u"      ", oldsel=(0, 0), scroll=True)
        yield test, c(input=u" x", output=u" x  ", oldsel=(2, 0), scroll=True)


    c = cbase(method=mod.dedent_lines, scroll=False)
    for eol in eols:
        i = len(eol) - 1
        c = c(eol=eol, mode=const.INDENT_MODE_TAB, size=2)
        yield test, c(input=u"\t", output=u"", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=u"\t\t", output=u"", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=u"\tx", output=u"x", oldsel=(0, 1), newsel=(0, 1))
        yield test, c(input=u"\tx", output=u"x", oldsel=(1, 1), newsel=(0, 1))
        yield test, c(input=u"\tx\nxyz\n", output=u"x\nxyz\n", oldsel=(0, 1), newsel=(0, 2+i))
        yield test, c(input=u"x\n\txyz\n", output=u"x\nxyz\n", oldsel=(3, 1), newsel=(2+i, 4+i))
        yield test, c(input=u"\tx\n\txyz\n", output=u"x\nxyz\n", oldsel=(0, 5), newsel=(0, 6+2*i))
        yield test, c(input=u"\tx\n\n\tx\n", output=u"x\n\nx\n", oldsel=(0, 5+2*i), newsel=(0, 5+3*i))
        yield test, c(input=u"\tx \n\n\tx\n", output=u"x \n\nx\n", oldsel=(0, 8+3*i), newsel=(0, 6+3*i))
        yield test, c(input=u"  x \n\n  x\n", output=u"x \n\nx\n", oldsel=(0, 9+3*i), newsel=(0, 6+3*i))
        yield test, c(input=u"   x \n\n   x\n", output=u" x \n\n x\n", oldsel=(0, 11+3*i), newsel=(0, 8+3*i))
        c = c(mode=const.INDENT_MODE_SPACE, size=2)
        yield test, c(input=u"  ", output=u"", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=u"    ", output=u"", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=u"  x", output=u"x", oldsel=(0, 3), newsel=(0, 1))
        yield test, c(input=u"  x\n\n  x\n", output=u"x\n\nx\n", oldsel=(0, 6+2*i), newsel=(0, 5+3*i))
        yield test, c(input=u"  x\nxyz\n", output=u"x\nxyz\n", oldsel=(0, 1), newsel=(0, 2+i))
        yield test, c(input=u"x\n  xyz\n", output=u"x\nxyz\n", oldsel=(5, 1), newsel=(2+i, 4+i))
        yield test, c(input=u"  x\n  xyz\n", output=u"x\nxyz\n", oldsel=(0, 7), newsel=(0, 6+2*i))
        yield test, c(input=u"  x\r  xyz\n", output=u"x\rxyz\n", oldsel=(0, 7), newsel=(0, 6+i))
        yield test, c(input=u"  x\u2028  xyz\n", output=u"x\u2028xyz\n", oldsel=(0, 7), newsel=(0, 6+i))
        # TODO convert leading tabs to spaces (and vice versa)
        c = c(size=4)
        yield test, c(input=u"    ", output=u"", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=u"      ", output=u"", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=u" x  ", output=u"x  ", oldsel=(2, 0), newsel=(0, 3))


    def setup(m, c, x):
        if c.mode == const.INDENT_MODE_TAB:
            x.tv.deleteBackward_(None)

    c = cbase(method=mod.delete_backward, setup=setup)
    for eol in eols:
        c = c(mode=const.INDENT_MODE_TAB, eol=eol)
        yield test, c(input=u"", output=SAME, oldsel=(0, 0), newsel=(0, 0), scroll=False)
        yield test, c(input=u"\t", output=SAME, oldsel=(1, 0), newsel=(0, 0), scroll=False)
        c = c(mode=const.INDENT_MODE_SPACE, size=2)
        yield test, c(input=u"", output=SAME, oldsel=(0, 0), newsel=(0, 0), scroll=False)
        yield test, c(input=u"  ", output=SAME, oldsel=(0, 0), newsel=(0, 0), scroll=False)
        yield test, c(input=u"  ", output=u" ", oldsel=(1, 0), newsel=(0, 0))
        yield test, c(input=u"x", output=u"", oldsel=(1, 0), newsel=(0, 0))
        yield test, c(input=u"xx", output=u"x", oldsel=(1, 0), newsel=(0, 0))
        yield test, c(input=u"xx", output=u"x", oldsel=(2, 0), newsel=(1, 0))
        yield test, c(input=u"x ", output=u"x", oldsel=(2, 0), newsel=(1, 0))
        yield test, c(input=u"x  ", output=u"x ", oldsel=(3, 0), newsel=(2, 0))
        yield test, c(input=u"x   ", output=u"x ", oldsel=(4, 0), newsel=(2, 0))
        yield test, c(input=u"  ", output=u"", oldsel=(2, 0), newsel=(0, 0))
        yield test, c(input=u"   ", output=u"  ", oldsel=(3, 0), newsel=(2, 0))
        yield test, c(input=u"    ", output=u"  ", oldsel=(4, 0), newsel=(2, 0))
        i = len(eol) - 1
        yield test, c(input=u"\n    ", output=u"\n  ", oldsel=(5+i, 0), newsel=(2+i, 0))
        yield test, c(input=u"\n    ", output=u"\n  ", oldsel=(3+i, 0), newsel=(1+i, 0))
        yield test, c(input=u"\n    ", output=u"\n   ", oldsel=(2+i, 0), newsel=(1+i, 0))
        c = c(size=4)
        yield test, c(input=u"\n    ", output=u"\n", oldsel=(5+i, 0), newsel=(1+i, 0))
        yield test, c(input=u"\nx ", output=u"\nx", oldsel=(3+i, 0), newsel=(2+i, 0))
        yield test, c(input=u"\nx  ", output=u"\nx ", oldsel=(4+i, 0), newsel=(3+i, 0))
        yield test, c(input=u"\nx   ", output=u"\nx  ", oldsel=(5+i, 0), newsel=(4+i, 0))
        yield test, c(input=u"\nx    ", output=u"\nx   ", oldsel=(6+i, 0), newsel=(5+i, 0))
        yield test, c(input=u"\nx     ", output=u"\nx   ", oldsel=(7+i, 0), newsel=(5+i, 0))
        yield test, c(input=u"\nx       ", output=u"\nx   ", oldsel=(9+i, 0), newsel=(5+i, 0))
        yield test, c(input=u"\nx         ", output=u"\nx       ", oldsel=(11+i, 0), newsel=(9+i, 0))
        yield test, c(input=u"\n     ", output=u"\n    ", oldsel=(6+i, 0), newsel=(5+i, 0))
        yield test, c(input=u"\n      ", output=u"\n    ", oldsel=(7+i, 0), newsel=(5+i, 0))
        yield test, c(input=u"\n       ", output=u"\n    ", oldsel=(8+i, 0), newsel=(5+i, 0))
        yield test, c(input=u"\n        ", output=u"\n    ", oldsel=(9+i, 0), newsel=(5+i, 0))

def test_reload_config():
    from editxt import app
    from editxt.config import Config
    m = Mocker()
    config = m.mock(Config)
    config.reload()
    tv = m.mock(NSTextView)
    with m, replattr(app, "config", config):
        mod.reload_config(tv, "<sender>", None)

def test_clear_highlighted_text():
    from editxt.controls.textview import TextView
    m = Mocker()
    tv = m.mock(TextView)
    view = tv.doc_view.finder.mark_occurrences("")
    do = CommandTester(mod.clear_highlighted_text, textview=tv)
    with m:
        do("clear_highlighted_text")

def test_set_variable():
    from editxt.document import TextDocumentView
    from editxt.controls.textview import TextView

    def test(command, completions, placeholder):
        bar = CommandTester(mod.set_variable)
        comps = (completions, (0 if completions else -1))
        eq_(bar.get_completions(command), comps)
        eq_(bar.get_placeholder(command), placeholder)
    yield test, "set ", [
            "highlight_selected_text",
            "indent",
            "newline_mode",
            "soft_wrap",
        ], "variable ..."
    yield test, "set in", ["indent"], "dent 4 space"
    yield test, "set indent 4 ", ["space", "tab"], "space"
    yield test, "set s", ["soft_wrap"], "oft_wrap yes"
    yield test, "set soft_wrap", ["soft_wrap"], " yes"
    yield test, "set soft_wrap ", ["yes", "no"], "yes"
    yield test, "set soft_wrap o", ["on", "off"], "..."
    yield test, "set soft_wrap x", None, ""

    def test(command, attribute, value=None):
        m = Mocker()
        tv = m.mock(TextView)
        view = tv.doc_view >> m.mock(TextDocumentView)
        do = CommandTester(mod.set_variable, textview=tv)
        if isinstance(attribute, Exception):
            with assert_raises(type(attribute), msg=str(attribute)), m:
                do(command)
        else:
            setattr(view.props >> m.mock(), attribute, value)
            with m:
                do(command)
    c = TestConfig()
    yield test, "set", AssertionError("nothing set")
    yield test, "set newline_mode Unix", "newline_mode", const.NEWLINE_MODE_UNIX
    yield test, "set newline_mode unix", "newline_mode", const.NEWLINE_MODE_UNIX
    yield test, "set newline_mode cr", "newline_mode", const.NEWLINE_MODE_MAC
    yield test, "set newline_mode \\n", "newline_mode", const.NEWLINE_MODE_UNIX
    yield test, "set newline_mode win", "newline_mode", const.NEWLINE_MODE_WINDOWS
    yield test, "set soft_wrap on", "soft_wrap", const.WRAP_WORD
    yield test, "set soft_wrap off", "soft_wrap", const.WRAP_NONE

    def test(command, size, mode):
        m = Mocker()
        tv = m.mock(TextView)
        view = tv.doc_view >> m.mock(TextDocumentView)
        props = view.props >> m.mock()
        setattr(props, "indent_size", size)
        setattr(props, "indent_mode", mode)
        do = CommandTester(mod.set_variable, textview=tv)
        with m:
            do(command)
    yield test, "set indent", 4, const.INDENT_MODE_SPACE
    yield test, "set indent 3", 3, const.INDENT_MODE_SPACE
    yield test, "set indent 8 t", 8, const.INDENT_MODE_TAB

def test_panel_actions():
    import sys
    def test(c):
        m = Mocker()
        tv = m.mock(NSTextView)
        ctl_class = m.replace("editxt.command.{}.{}".format(c.mod, c.ctl.__name__))
        if c.func is not None:
            func = m.replace("editxt.command.{}.{}".format(c.mod, c.func.__name__))
        if c.args:
            args = '<args>'
            func(tv, args)
        else:
            args = None
            ctl = ctl_class(tv) >> m.mock(c.ctl)
            ctl.begin_sheet('<sender>')
        with m:
            c.action(tv, '<sender>', args)
    c = TestConfig()

    from editxt.command.sortlines import SortLinesController, sortlines
    from editxt.command.wraplines import WrapLinesController, wrap_selected_lines
    from editxt.command.changeindent import ChangeIndentationController

    for args in [False, True]:
        c = c(args=args)
        yield test, c(action=mod.sort_lines, mod="sortlines",
            ctl=SortLinesController, func=sortlines)
        yield test, c(action=mod.wrap_lines, mod="wraplines",
            ctl=WrapLinesController, func=wrap_selected_lines)

    yield test, c(action=mod.reindent, mod="changeindent",
        ctl=ChangeIndentationController, func=None, args=False)

# def test():
#   assert False, "stop"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Test helpers
import editxt.textcommand as textcommand

class CommandTester(object):

    def __init__(self, *commands, **kw):
        class menu:
            @staticmethod
            def insertItem_atIndex_(item, tag):
                pass
        class editor:
            class current_view:
                text_view = kw.pop("textview", None)
                class scroll_view:
                    class commandView:
                        @staticmethod
                        def message(msg, textview=None, **kw):
                            if isinstance(msg, Exception):
                                raise msg
                            raise AssertionError(msg)
        commander = textcommand.TextCommandController(
            kw.pop("history", []))
        for command in commands:
            commander.add_command(command, None, menu)
        self.bar = textcommand.CommandBar(kw.pop("editor", editor), commander)
        # keep references (CommandBar uses weakref)
        self.refs = (editor, commander)

    def __call__(self, command):
        with replattr(textcommand, "NSBeep", lambda:None): # HACK
            self.bar.execute(command)

    def __getattr__(self, name):
        return getattr(self.bar, name)
