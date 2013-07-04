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
from nose.tools import eq_, assert_raises
from AppKit import *
from Foundation import *
from editxt.test.util import TestConfig

import editxt.constants as const
import editxt.commands as mod
from editxt.commandparser import ArgumentError, CommandParser, Int, Options

log = logging.getLogger(__name__)


def test_command_decorator_defaults():
    @mod.command
    def cmd(textview, sender, args):
        pass

    assert cmd.is_text_command
    eq_(cmd.title, None)
    eq_(cmd.hotkey, None)
    eq_(cmd.name, 'cmd')
    eq_(cmd.is_enabled(None, None), True)
    eq_(cmd.arg_parser.parse('abc def'), Options(args=['abc', 'def']))
    eq_(cmd.lookup_with_arg_parser, False)


def test_command_decorator_with_args():
    @mod.command(name='abc', title='Title', hotkey=(',', 0),
        is_enabled=lambda *a:False,
        arg_parser=CommandParser(Int("value")), lookup_with_arg_parser=True)
    def cmd(textview, sender, args):
        pass

    assert cmd.is_text_command
    eq_(cmd.title, 'Title')
    eq_(cmd.hotkey, (',', 0))
    eq_(cmd.name, 'abc')
    eq_(cmd.is_enabled(None, None), False)
    with assert_raises(ArgumentError):
        cmd.arg_parser.parse('abc def')
    eq_(cmd.arg_parser.parse('42'), Options(value=42))
    eq_(cmd.lookup_with_arg_parser, True)


def test_command_decorator_names():
    def test(input, output):
        @mod.command(name=input)
        def cmd(textview, sender, args):
            pass
        eq_(cmd.name, output[0])
        eq_(cmd.names, output)
    yield test, None, ['cmd']
    yield test, '', ['cmd']
    yield test, 'abc def', ['abc', 'def']
    yield test, ['abc', 'def'], ['abc', 'def']


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

def test_find_command():
    from editxt.findpanel import Finder, FindOptions
    def test(c):
        assert int(c.regex) + int(c.match_word) < 2, c
        opts = FindOptions(**{opt: c[key] for key, opt in {
            "find": "find_text",
            "replace": "replace_text",
            "regex": "regular_expression",
            "ignore_case": "ignore_case",
            "match_word": "match_entire_word",
            "wrap": "wrap_around",
        }.items()})
        m = Mocker()
        tv = m.mock(NSTextView)
        finder_cls = m.replace("editxt.findpanel.Finder")
        def check_opts(get_tv, args):
            eq_(get_tv(), tv)
            eq_(args, opts)
        finder = m.mock(Finder)
        (finder_cls(ANY, ANY) << finder).call(check_opts)
        getattr(finder, c.action)("<sender>")
        with m:
            args = mod.find.arg_parser.parse(c.input)
            mod.find(tv, "<sender>", args)

    c = TestConfig(find="", replace="", regex=True, ignore_case=False,
                   match_word=False, wrap=True, action="find_next")
    yield test, c(input=u"")
    yield test, c(input=u"/abc", find="abc")
    yield test, c(input=u";abc", find="abc")
    yield test, c(input=u";abc\;", find=r"abc\;")
    yield test, c(input=u"/\/abc\//", find=r"\/abc\/")
    yield test, c(input=u"/abc/def", find="abc", replace="def")
    yield test, c(input=u"/abc/def/", find="abc", replace="def")
    yield test, c(input=u"/abc/def/i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=u" abc def i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=u";abc;def;i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=u"#abc#def#i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=u",abc,def,i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=u"'abc'def'i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=u'"abc"def"i', find="abc", replace="def", ignore_case=True)
    yield test, c(input=u" ab\ c def i", find=r"ab\ c", replace="def", ignore_case=True)
    yield test, c(input=u"/abc// n", find="abc", action="find_next")
    yield test, c(input=u"/abc// p", find="abc", action="find_previous")
    yield test, c(input=u"/abc// previous", find="abc", action="find_previous")
    yield test, c(input=u"/abc// o", find="abc", action="replace_one")
    yield test, c(input=u"/abc// a", find="abc", action="replace_all")
    yield test, c(input=u"/abc// s", find="abc", action="replace_all_in_selection")
    yield test, c(input=u"/abc//  r", find="abc", regex=True)
    yield test, c(input=u"/abc//  l", find="abc", regex=False, match_word=False)
    yield test, c(input=u"/abc//  w", find="abc", regex=False, match_word=True)
    yield test, c(input=u"/abc//   n", find="abc", wrap=False)

def test_panel_actions():
    import sys
    def test(c):
        m = Mocker()
        tv = m.mock(NSTextView)
        mod = m.replace(sys.modules, "editxt." + c.mod, dict=True)
        ctl_class = getattr(mod, c.ctl.__name__)
        if c.func is not None:
            func = getattr(mod, c.func.__name__) >> m.mock(c.func)
        if c.args:
            args = '<args>'
            func(tv, args)
        else:
            args = None
            ctl = ctl_class.create_with_textview(tv) >> m.mock(c.ctl)
            ctl.begin_sheet('<sender>')
        with m:
            c.action(tv, '<sender>', args)
    c = TestConfig()

    from editxt.sortlines import SortLinesController, sortlines
    from editxt.wraplines import WrapLinesController, wrap_selected_lines
    from editxt.changeindent import ChangeIndentationController

    for args in [False, True]:
        c = c(args=args)
        yield test, c(action=mod.sort_lines, mod="sortlines",
            ctl=SortLinesController, func=sortlines)
        yield test, c(action=mod.wrap_lines, mod="wraplines",
            ctl=WrapLinesController, func=wrap_selected_lines)

    yield test, c(action=mod.reindent, mod="changeindent",
        ctl=ChangeIndentationController, func=None, args=False)

def test_wrap_to_margin_guide():
    from editxt.wraplines import WrapLinesController, wrap_selected_lines
    m = Mocker()
    tv = m.mock(NSTextView)
    wrap = m.replace('editxt.wraplines.wrap_selected_lines')
    ctl_class = m.replace('editxt.wraplines.WrapLinesController')
    ctl = ctl_class.shared_controller() >> m.mock(WrapLinesController)
    opts = m.replace("editxt.commands.Options")() >> m.mock()
    wrap_opts = ctl.opts >> m.mock()
    opts.wrap_column = const.DEFAULT_RIGHT_MARGIN
    opts.indent = wrap_opts.indent >> "<indent>"
    wrap(tv, opts)
    with m:
        mod.wrap_at_margin(tv, None, None)

# def test():
#   assert False, "stop"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Other text mangling utility functions that didn't have anywhere else to go

def test_replace_newlines():
    def test(c):
        result = []
        m = Mocker()
        tv = m.mock(NSTextView)
        tv.string() >> c.input
        sel = tv.selectedRange() >> m.mock(NSRange)
        if c.input != c.output:
            rng = NSMakeRange(0, len(c.input))
            tv.shouldChangeTextInRange_replacementString_(rng, ANY) >> True
            ts = tv.textStorage() >> m.mock(NSTextStorage)
            ts.replaceCharactersInRange_withString_(rng, c.output)
            tv.didChangeText()
            tv.setSelectedRange_(sel)
        with m:
            mod.replace_newlines(tv, c.eol)
    c = TestConfig(eol=const.EOLS[const.NEWLINE_MODE_UNIX])
    yield test, c(input=u"", output=u"")
    yield test, c(input=u"\r\n", output=u"\n")
    yield test, c(input=u"\n\r\n", output=u"\n\n")
    yield test, c(input=u"\r \n", output=u"\n \n")
    yield test, c(input=u"\r \n \u2028", output=u"\n \n \n")
    yield test, c(input=u"\r \r\n\n \u2028", output=u"\n \n\n \n")

def test_change_indentation():
    from editxt.document import TextDocument
    def test(c):
        if c.eol != u"\n":
            c.input = c.input.replace(u"\n", c.eol)
            c.output = c.output.replace(u"\n", c.eol)
        result = []
        m = Mocker()
        tv = m.mock(NSTextView)
        reset = (c.new == u"\t")
        if c.old != c.new or reset:
            tv.string() >> c.input
            rng = NSMakeRange(0, len(c.input))
            tv.shouldChangeTextInRange_replacementString_(rng, c.output) >> True
            if reset:
                doc = tv.doc_view.document >> m.mock(TextDocument)
                doc.reset_text_attributes(c.size)
            if c.input != c.output:
                sel = tv.selectedRange() >> NSRange(*c.sel)
                ts = tv.textStorage() >> m.mock(NSTextStorage)
                ts.replaceCharactersInRange_withString_(rng, c.output)
                if sel.location > len(c.output):
                    sel = NSRange(len(c.output), 0)
                elif sel.location + sel.length > len(c.output):
                    sel = NSRange(sel.location, len(c.output) - sel.location)
                tv.setSelectedRange_(sel)
            tv.didChangeText()
        with m:
            mod.change_indentation(tv, c.old, c.new, c.size)
    c = TestConfig(old=u"  ", new=u"   ", size=4, sel=(0, 0))
    for mode in [
        const.NEWLINE_MODE_UNIX,
        const.NEWLINE_MODE_MAC,
        const.NEWLINE_MODE_WINDOWS,
        const.NEWLINE_MODE_UNICODE,
    ]:
        c = c(eol=const.EOLS[mode])
        yield test, c(old=u"  ", new=u"  ", input=u"", output=u"")
        yield test, c(old=u"\t", new=u"\t", input=u"", output=u"")
        c = c(old=u"  ", new=u"   ", size=3)
        yield test, c(input=u"", output=u"")
        yield test, c(input=u"  \n", output=u"   \n")
        yield test, c(input=u"  x\n", output=u"   x\n")
        yield test, c(input=u"   x\n", output=u"    x\n")
        yield test, c(input=u"    x\n", output=u"      x\n")
        yield test, c(input=u"    x    \n", output=u"      x    \n")
        yield test, c(input=u"  x\n    y\n", output=u"   x\n      y\n")
        c = c(old=u"  ", new=u"\t", size=3)
        yield test, c(input=u"", output=u"")
        yield test, c(input=u"  \n", output=u"\t\n")
        yield test, c(input=u"  x\n", output=u"\tx\n")
        yield test, c(input=u"   x\n", output=u"\t x\n")
        yield test, c(input=u"    x\n", output=u"\t\tx\n")
        yield test, c(input=u"    x    \n", output=u"\t\tx    \n")
        yield test, c(input=u"  x\n    y\n", output=u"\tx\n\t\ty\n", sel=(8, 2))
        yield test, c(input=u"  x\n    y\n", output=u"\tx\n\t\ty\n", sel=(6, 4))
        c = c(old=u"\t", new=u"   ", size=3)
        yield test, c(input=u"", output=u"")
        yield test, c(input=u"\t\n", output=u"   \n")
        yield test, c(input=u"\tx\n", output=u"   x\n")
        yield test, c(input=u"\t x\n", output=u"    x\n")
        yield test, c(input=u"\t\tx\n", output=u"      x\n")
        yield test, c(input=u"\t\tx\t\t\n", output=u"      x\t\t\n")
        yield test, c(input=u"\tx\n\t\ty\n", output=u"   x\n      y\n")

