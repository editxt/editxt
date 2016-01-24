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

from mocker import Mocker, expect, ANY, MATCH
import AppKit as ak
import Foundation as fn
from editxt.test.command import FakeTextView
from editxt.test.util import assert_raises, eq_, TestConfig, replattr, test_app

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
        mod.ack,
        mod.diff,
        mod.grab,
        mod.open_,
        mod.pathfind,
        mod.python,
        mod.clear_highlighted_text,
        mod.docnav,
        mod.reload_config,
        mod.set_variable,
        mod.help,
        mod.debug,
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
    yield test, c(old="", new="x ")
    yield test, c(old="\n", new="x \n")
    yield test, c(old="abc\n", new="x abc\n")
    yield test, c(old="\tabc\n", new="x \tabc\n")
    yield test, c(old="  abc\n", new="x   abc\n")
    c = c(isize=2, imode=const.INDENT_MODE_SPACE)
    yield test, c(old="abc\n", new="x abc\n")
    yield test, c(old="  abc\n", new="x  abc\n")
    yield test, c(old="    abc\n", new="x    abc\n")
    c = c(isize=3)
    yield test, c(old="abc\n", new="x abc\n")
    yield test, c(old="   abc\n", new="x  abc\n")
    yield test, c(old="      abc\n", new="x     abc\n")
    c = c(isize=4)
    yield test, c(old="abc\n", new="x abc\n")
    yield test, c(old="    abc\n", new="x   abc\n")
    yield test, c(old="        abc\n", new="x       abc\n")

    c = c(imode=const.INDENT_MODE_TAB, isize=2, pad=False)
    yield test, c(old="", new="x")
    yield test, c(old="\n", new="x\n")
    yield test, c(old="abc\n", new="xabc\n")
    yield test, c(old="\tabc\n", new="x\tabc\n")
    yield test, c(old="  abc\n", new="x  abc\n")
    c = c(isize=2, imode=const.INDENT_MODE_SPACE)
    yield test, c(old="abc\n", new="xabc\n")
    yield test, c(old="  abc\n", new="x  abc\n")
    yield test, c(old="    abc\n", new="x    abc\n")
    c = c(isize=3)
    yield test, c(old="abc\n", new="xabc\n")
    yield test, c(old="   abc\n", new="x   abc\n")
    yield test, c(old="      abc\n", new="x      abc\n")
    c = c(isize=4)
    yield test, c(old="abc\n", new="xabc\n")
    yield test, c(old="    abc\n", new="x    abc\n")
    yield test, c(old="        abc\n", new="x        abc\n")

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
    from editxt.editor import Editor
    from editxt.document import TextDocument
    SAME = "<SAME AS INPUT>"
    def test(c):
        if c.eol != "\n":
            c.input = c.input.replace("\n", c.eol)
            c.output = c.output.replace("\n", c.eol)
        result = TestConfig()
        default = False
        m = Mocker()
        editor = m.mock(Editor)
        tv = editor.text_view >> m.mock(ak.NSTextView)
        (editor.document.indent_mode << c.mode).count(0, None)
        (editor.document.indent_size << c.size).count(0, None)
        (editor.document.eol << c.eol).count(0, None)
        sel = fn.NSMakeRange(*c.oldsel); (tv.selectedRange() << sel).count(0, None)
        (tv.string() << fn.NSString.stringWithString_(c.input)).count(0, None)
        (tv.shouldChangeTextInRange_replacementString_(ANY, ANY) << True).count(0, None)
        ts = m.mock(ak.NSTextStorage); (tv.textStorage() << ts).count(0, None)
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
            c.method(editor, None)
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
        yield test, c(input="", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=" ", oldsel=(0, 0), newsel=(1, 0))
        yield test, c(input=" ", oldsel=(1, 0), newsel=(0, 0))
        yield test, c(input="  ", oldsel=(0, 0), newsel=(2, 0))
        yield test, c(input="  ", oldsel=(1, 0), newsel=(2, 0))
        yield test, c(input="  ", oldsel=(2, 0), newsel=(0, 0))
        yield test, c(input="  x", oldsel=(0, 0), newsel=(2, 0))
        yield test, c(input="  x", oldsel=(1, 0), newsel=(2, 0))
        yield test, c(input="  x", oldsel=(2, 0), newsel=(0, 0))
        yield test, c(input="  \n ", oldsel=(0, 0), newsel=(2, 0))
        yield test, c(input="  \n ", oldsel=(1, 0), newsel=(2, 0))
        yield test, c(input="  \n ", oldsel=(2, 0), newsel=(0, 0))
        i = len(c.eol) - 1
        yield test, c(input="\n ", oldsel=(1 + i, 0), newsel=(2 + i, 0))
        yield test, c(input="    \n    ", oldsel=(5 + i, 0), newsel=(9 + i, 0))
        yield test, c(input="    \n    ", oldsel=(7 + i, 0), newsel=(9 + i, 0))
        yield test, c(input="    \n    ", oldsel=(9 + i, 0), newsel=(5 + i, 0))
        yield test, c(input="    \n    x", oldsel=(5 + i, 0), newsel=(9 + i, 0))
        yield test, c(input="    \n    x", oldsel=(7 + i, 0), newsel=(9 + i, 0))
        yield test, c(input="    \n    x", oldsel=(9 + i, 0), newsel=(5 + i, 0))
        yield test, c(input="    \n    \n", oldsel=(5 + i, 0), newsel=(9 + i, 0))
        yield test, c(input="    \n    \n", oldsel=(7 + i, 0), newsel=(9 + i, 0))
        yield test, c(input="    \n    \n", oldsel=(9 + i, 0), newsel=(5 + i, 0))

    c = cbase(method=mod.insert_newline)
    for eol in eols:
        c = c(eol=eol)
        yield test, c(input="", output="\n", oldsel=(0, 0))
        yield test, c(input=" ", output=" \n ", oldsel=(1, 0))
        yield test, c(input="  ", output="  \n  ", oldsel=(2, 0))
        yield test, c(input="    ", output=" \n ", oldsel=(1, 0))
        yield test, c(input="\t", output="\t\n\t", oldsel=(1, 0))
        yield test, c(input="  a bc", output="  a\n  bc", oldsel=(3, 0))
        yield test, c(input="  a bc", output="  a\n  c", oldsel=(3, 1))
        yield test, c(input="a bc", output="a\nbc", oldsel=(1, 0))
        i = len(eol) - 1
        yield test, c(input=" a\n b", output=" a\n b\n ", oldsel=(5 + i, 0))
        yield test, c(input="\n x", output="\n\n x", oldsel=(1 + i, 0))


    c = cbase(method=mod.indent_lines)
    for eol in eols:
        i = len(eol) - 1
        c = c(eol=eol, mode=const.INDENT_MODE_TAB, scroll=False)
        yield test, c(input="", output="\t", oldsel=(0, 0), scroll=True)
        yield test, c(input="\t", output="\t\t", oldsel=(0, 0), scroll=True)
        yield test, c(input="x", output="\tx", oldsel=(0, 1), newsel=(0, 2))
        yield test, c(input="x\nxyz\n", output="\tx\nxyz\n", oldsel=(0, 1), newsel=(0, 3+i))
        yield test, c(input="x\nxyz\n", output="x\n\txyz\n", oldsel=(3, 1), newsel=(2+i, 5+i))
        yield test, c(input="x\nxyz\n", output="\tx\n\txyz\n", oldsel=(0, 4), newsel=(0, 8+2*i))
        yield test, c(input="x\n\nx\n", output="\tx\n\n\tx\n", oldsel=(0, 4+2*i), newsel=(0, 7+3*i))
        yield test, c(input="x \n\nx\n", output="\tx \n\n\tx\n", oldsel=(0, 5+2*i), newsel=(0, 8+3*i))
        c = c(mode=const.INDENT_MODE_SPACE, size=2)
        yield test, c(input="", output="  ", oldsel=(0, 0), scroll=True)
        yield test, c(input=" ", output="  ", oldsel=(1, 0), scroll=True)
        yield test, c(input="  ", output="    ", oldsel=(0, 0), scroll=True)
        yield test, c(input="x", output="  x", oldsel=(0, 1), newsel=(0, 3))
        yield test, c(input="x\n\nx\n", output="  x\n\n  x\n", oldsel=(0, 4+2*i), newsel=(0, 9+3*i))
        yield test, c(input="x\nxyz\n", output="  x\nxyz\n", oldsel=(0, 1), newsel=(0, 4+i))
        yield test, c(input="x\nxyz\n", output="x\n  xyz\n", oldsel=(3, 1), newsel=(2+i, 6+i))
        yield test, c(input="x\nxyz\n", output="  x\n  xyz\n", oldsel=(0, 4), newsel=(0, 10+2*i))
        yield test, c(input="x\rxyz\n", output="  x\r  xyz\n", oldsel=(0, 4), newsel=(0, 10+i))
        yield test, c(input="x\u2028xyz\n", output="  x\u2028  xyz\n", oldsel=(0, 4), newsel=(0, 10+i))
        # TODO convert leading tabs to spaces (and vice versa)
        #yield test, c(input=u"\tx\n\txyz\n", output=u"    x\n    xyz\n",
        #    oldsel=(0, 6), newsel=(0, 14+2*i))
        c = c(size=4)
        yield test, c(input="", output="    ", oldsel=(0, 0), scroll=True)
        yield test, c(input=" ", output="    ", oldsel=(1, 0), scroll=True)
        yield test, c(input="  ", output="      ", oldsel=(0, 0), scroll=True)
        yield test, c(input=" x", output=" x  ", oldsel=(2, 0), scroll=True)


    c = cbase(method=mod.dedent_lines, scroll=False)
    for eol in eols:
        i = len(eol) - 1
        c = c(eol=eol, mode=const.INDENT_MODE_TAB, size=2)
        yield test, c(input="\t", output="", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input="\t\t", output="", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input="\tx", output="x", oldsel=(0, 1), newsel=(0, 1))
        yield test, c(input="\tx", output="x", oldsel=(1, 1), newsel=(0, 1))
        yield test, c(input="\tx\nxyz\n", output="x\nxyz\n", oldsel=(0, 1), newsel=(0, 2+i))
        yield test, c(input="x\n\txyz\n", output="x\nxyz\n", oldsel=(3, 1), newsel=(2+i, 4+i))
        yield test, c(input="\tx\n\txyz\n", output="x\nxyz\n", oldsel=(0, 5), newsel=(0, 6+2*i))
        yield test, c(input="\tx\n\n\tx\n", output="x\n\nx\n", oldsel=(0, 5+2*i), newsel=(0, 5+3*i))
        yield test, c(input="\tx \n\n\tx\n", output="x \n\nx\n", oldsel=(0, 8+3*i), newsel=(0, 6+3*i))
        yield test, c(input="  x \n\n  x\n", output="x \n\nx\n", oldsel=(0, 9+3*i), newsel=(0, 6+3*i))
        yield test, c(input="   x \n\n   x\n", output=" x \n\n x\n", oldsel=(0, 11+3*i), newsel=(0, 8+3*i))
        c = c(mode=const.INDENT_MODE_SPACE, size=2)
        yield test, c(input="  ", output="", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input="    ", output="", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input="  x", output="x", oldsel=(0, 3), newsel=(0, 1))
        yield test, c(input="  x\n\n  x\n", output="x\n\nx\n", oldsel=(0, 6+2*i), newsel=(0, 5+3*i))
        yield test, c(input="  x\nxyz\n", output="x\nxyz\n", oldsel=(0, 1), newsel=(0, 2+i))
        yield test, c(input="x\n  xyz\n", output="x\nxyz\n", oldsel=(5, 1), newsel=(2+i, 4+i))
        yield test, c(input="  x\n  xyz\n", output="x\nxyz\n", oldsel=(0, 7), newsel=(0, 6+2*i))
        yield test, c(input="  x\r  xyz\n", output="x\rxyz\n", oldsel=(0, 7), newsel=(0, 6+i))
        yield test, c(input="  x\u2028  xyz\n", output="x\u2028xyz\n", oldsel=(0, 7), newsel=(0, 6+i))
        # TODO convert leading tabs to spaces (and vice versa)
        c = c(size=4)
        yield test, c(input="    ", output="", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input="      ", output="", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=" x  ", output="x  ", oldsel=(2, 0), newsel=(0, 3))


    def setup(m, c, x):
        if c.mode == const.INDENT_MODE_TAB:
            x.tv.deleteBackward_(None)

    c = cbase(method=mod.delete_backward, setup=setup)
    for eol in eols:
        c = c(mode=const.INDENT_MODE_TAB, eol=eol)
        yield test, c(input="", output=SAME, oldsel=(0, 0), newsel=(0, 0), scroll=False)
        yield test, c(input="\t", output=SAME, oldsel=(1, 0), newsel=(0, 0), scroll=False)
        c = c(mode=const.INDENT_MODE_SPACE, size=2)
        yield test, c(input="", output=SAME, oldsel=(0, 0), newsel=(0, 0), scroll=False)
        yield test, c(input="  ", output=SAME, oldsel=(0, 0), newsel=(0, 0), scroll=False)
        yield test, c(input="  ", output=" ", oldsel=(1, 0), newsel=(0, 0))
        yield test, c(input="x", output="", oldsel=(1, 0), newsel=(0, 0))
        yield test, c(input="xx", output="x", oldsel=(1, 0), newsel=(0, 0))
        yield test, c(input="xx", output="x", oldsel=(2, 0), newsel=(1, 0))
        yield test, c(input="x ", output="x", oldsel=(2, 0), newsel=(1, 0))
        yield test, c(input="x  ", output="x ", oldsel=(3, 0), newsel=(2, 0))
        yield test, c(input="x   ", output="x ", oldsel=(4, 0), newsel=(2, 0))
        yield test, c(input="  ", output="", oldsel=(2, 0), newsel=(0, 0))
        yield test, c(input="   ", output="  ", oldsel=(3, 0), newsel=(2, 0))
        yield test, c(input="    ", output="  ", oldsel=(4, 0), newsel=(2, 0))
        i = len(eol) - 1
        yield test, c(input="\n    ", output="\n  ", oldsel=(5+i, 0), newsel=(2+i, 0))
        yield test, c(input="\n    ", output="\n  ", oldsel=(3+i, 0), newsel=(1+i, 0))
        yield test, c(input="\n    ", output="\n   ", oldsel=(2+i, 0), newsel=(1+i, 0))
        c = c(size=4)
        yield test, c(input="\n    ", output="\n", oldsel=(5+i, 0), newsel=(1+i, 0))
        yield test, c(input="\nx ", output="\nx", oldsel=(3+i, 0), newsel=(2+i, 0))
        yield test, c(input="\nx  ", output="\nx ", oldsel=(4+i, 0), newsel=(3+i, 0))
        yield test, c(input="\nx   ", output="\nx  ", oldsel=(5+i, 0), newsel=(4+i, 0))
        yield test, c(input="\nx    ", output="\nx   ", oldsel=(6+i, 0), newsel=(5+i, 0))
        yield test, c(input="\nx     ", output="\nx   ", oldsel=(7+i, 0), newsel=(5+i, 0))
        yield test, c(input="\nx       ", output="\nx   ", oldsel=(9+i, 0), newsel=(5+i, 0))
        yield test, c(input="\nx         ", output="\nx       ", oldsel=(11+i, 0), newsel=(9+i, 0))
        yield test, c(input="\n     ", output="\n    ", oldsel=(6+i, 0), newsel=(5+i, 0))
        yield test, c(input="\n      ", output="\n    ", oldsel=(7+i, 0), newsel=(5+i, 0))
        yield test, c(input="\n       ", output="\n    ", oldsel=(8+i, 0), newsel=(5+i, 0))
        yield test, c(input="\n        ", output="\n    ", oldsel=(9+i, 0), newsel=(5+i, 0))

def test_reload_config():
    from editxt.config import Config
    m = Mocker()
    tv = m.mock(ak.NSTextView)
    tv.app.reload_config()
    with m:
        mod.reload_config(tv, None)

def test_clear_highlighted_text():
    from editxt.editor import Editor
    m = Mocker()
    editor = m.mock(Editor)
    editor.finder.mark_occurrences("")
    do = CommandTester(mod.clear_highlighted_text, editor=editor)
    with m:
        do("clear_highlighted_text")

def test_set_variable():
    from editxt.platform.font import Font
    class editor:
        class project:
            path = os.path.expanduser("~/project")
        class document:
            class syntaxdef:
                name = "Unknown"
        text_view = object
        dirname = lambda:None
        font = Font("Mension", 15.0, False, None)
        highlight_selected_text = True
        indent_mode = const.INDENT_MODE_TAB
        indent_size = 2
        soft_wrap = const.WRAP_WORD
    def test(command, completions, placeholder):
        bar = CommandTester(mod.set_variable, editor=editor)
        eq_(bar.get_completions(command), (completions, None))
        eq_(bar.get_placeholder(command), placeholder)
    yield test, "set ", [
            "font",
            "highlight_selected_text",
            "indent",
            "language",
            "newline_mode",
            "project_path",
            "soft_wrap",
        ], "variable ..."
    yield test, "set fo", ["font"], "nt {face} {size} {smooth}".format(
        face=editor.font.face,
        size=editor.font.size,
        smooth=("smooth" if editor.font.smooth else "jagged"),
    )
    yield test, "set high", ["highlight_selected_text"], "light_selected_text no"
    yield test, "set in", ["indent"], "dent 2 tab"
    yield test, "set indent 4 ", ["space", "tab"], "tab"
    yield test, "set project_path ", [], "~/project"
    yield test, "set s", ["soft_wrap"], "oft_wrap no"
    yield test, "set soft_wrap", ["soft_wrap"], " no"
    yield test, "set soft_wrap ", ["yes", "no"], "no"
    yield test, "set soft_wrap o", ["on", "off"], "..."
    yield test, "set soft_wrap x", [], ""

    def test(command, attribute, value=None):
        with test_app("editor*") as app:
            m = Mocker()
            editor = app.windows[0].current_editor
            editor.text_view = TestConfig(textContainer=lambda:None)
            proxy = editor.proxy = m.mock()
            do = CommandTester(mod.set_variable, editor=editor)
            if isinstance(attribute, Exception):
                with assert_raises(type(attribute), msg=str(attribute)):
                    do(command)
            else:
                setattr(proxy, attribute, value)
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

    # set_project_variable
    def test(command, attr, value, *value_before):
        with test_app("project editor*") as app:
            project = app.windows[0].projects[0]
            do = CommandTester(mod.set_variable, editor=project.editors[0])
            if value_before:
                eq_(getattr(project, attr), *value_before)
                eq_(len(value_before), 1, value_before)
            do(command)
            eq_(getattr(project, attr), value)
    yield test, "set project_path ~/project", "path", os.path.expanduser("~/project"), None

    def test(command, size, mode):
        with test_app("editor*") as app:
            editor = app.windows[0].current_editor
            editor.text_view = TestConfig(textContainer=lambda:None)
            do = CommandTester(mod.set_variable, editor=editor)
            do(command)
            eq_(editor.indent_size, size)
            eq_(editor.indent_mode, mode)
    yield test, "set indent", 4, const.INDENT_MODE_SPACE
    yield test, "set indent 3", 3, const.INDENT_MODE_SPACE
    yield test, "set indent 8 t", 8, const.INDENT_MODE_TAB

    # set syntax
    def test(command, name):
        class factory:
            definitions = [
                TestConfig(name="Plain Text", wordinfo=None),
                TestConfig(name="Python", wordinfo=None),
            ]
        if name is not None:
            for sdef in factory.definitions:
                if sdef.name == name:
                    lang = sdef
                    break
            else:
                assert False, "unknown syntax definition: " % name
        with test_app("editor*") as app:
            app.syntax_factory = factory
            editor = app.windows[0].current_editor
            editor.text_view = TestConfig(textContainer=lambda:None)
            do = CommandTester(mod.set_variable, editor=editor)
            do(command)
            eq_(getattr(editor, "syntaxdef"), lang)
    yield test, "set language py", "Python"
    yield test, "set lang plain", "Plain Text"

def test_panel_actions():
    from editxt.editor import Editor
    import sys
    def test(c):
        m = Mocker()
        editor = m.mock(Editor)
        ctl_class = m.replace("editxt.command.{}.{}".format(c.mod, c.ctl.__name__))
        if c.func is not None:
            func = m.replace("editxt.command.{}.{}".format(c.mod, c.func.__name__))
        if c.args:
            tv = editor.text_view >> m.mock(ak.NSTextView)
            args = '<args>'
            func(tv, args)
        else:
            args = None
            ctl = ctl_class(editor) >> m.mock(c.ctl)
            ctl.begin_sheet(None)
        with m:
            c.action(editor, args)
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
        if kw.get("output"):
            assert "error" not in kw, \
                "CommandTester: cannot use both 'output' and 'error' kwargs"
            self.output = None
        class menu:
            @staticmethod
            def addItem_(item):
                pass
        def message(msg, msg_type=const.INFO):
            if kw.get("output"):
                self.output = msg
                self.output_msg_type = msg_type
                return
            if kw.get("error"):
                eq_(msg, kw["error"])
                return
            if isinstance(msg, Exception):
                raise msg
            raise AssertionError(msg)
        class editor:
            text_view = kw.pop("textview", object)
            command_view = kw.pop("command_view", object)
        editor = kw.pop("editor", editor)
        if not isinstance(editor, type(Mocker().mock())):
            editor.message = message
        class window:
            current_editor = editor
        with test_app() as app:
            commander = textcommand.CommandManager(
                kw.pop("history", []), app)
            for command in commands:
                commander.add_command(command, None, menu)
        self.bar = textcommand.CommandBar(kw.pop("window", window), commander)
        self.editor = editor
        self.commands = commands
        # keep references (CommandBar uses weakref)
        self.window = window
        self.commander = commander

    def __call__(self, command):
        if command is not None:
            self.bar.execute(command)
        else:
            assert len(self.commands) == 1, "ambiguous command invocation"
            tag = self.commands[0].name
            self.commander.do_command(self.editor, TestConfig(tag=lambda:tag))

    def __getattr__(self, name):
        return getattr(self.bar, name)
