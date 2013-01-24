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
import editxt.textcommand as mod
from editxt.textcommand import TextCommandController

log = logging.getLogger(__name__)


def test_command_decorator_defaults():
    @mod.command
    def cmd(textview, sender, args):
        pass

    assert cmd.is_text_command
    eq_(cmd.title, None)
    eq_(cmd.hotkey, None)
    eq_(cmd.names, ['cmd'])
    eq_(cmd.is_enabled(None, None), True)
    eq_(cmd.parse_args('abc def'), ['abc', 'def'])
    eq_(cmd.lookup_with_parse_args, False)


def test_command_decorator_with_args():
    @mod.command(names='abc', title='Title', hotkey=(',', 0),
        is_enabled=lambda *a:False,
        parse_args=lambda *a:42, lookup_with_parse_args=True)
    def cmd(textview, sender, args):
        pass

    assert cmd.is_text_command
    assert not hasattr(cmd, 'name')
    eq_(cmd.title, 'Title')
    eq_(cmd.hotkey, (',', 0))
    eq_(cmd.names, ['abc'])
    eq_(cmd.is_enabled(None, None), False)
    eq_(cmd.parse_args('abc def'), 42)
    eq_(cmd.lookup_with_parse_args, True)


def test_command_decorator_names():
    def test(input, output):
        @mod.command(names=input)
        def cmd(textview, sender, args):
            pass
        eq_(cmd.names, output)
    yield test, None, ['cmd']
    yield test, '', ['cmd']
    yield test, 'abc def', ['abc', 'def']
    yield test, ['abc', 'def'], ['abc', 'def']


def test_load_commands():
    import editxt.textcommand as tc
    cmds = tc.load_commands()
    eq_(cmds["text_menu_commands"], [
        tc.show_command_bar,
        tc.goto_line,
        tc.comment_text,
        tc.pad_comment_text,
        tc.indent_lines,
        tc.dedent_lines,
        tc.wrap_at_margin,
        tc.wrap_lines,
        tc.sort_lines,
        tc.reindent,
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
    from editxt.textcommand import is_comment_range
    def test(c):
        range = c.range if "range" in c else (0, len(c.text))
        eq_(is_comment_range(c.text, range, c.token), c.result)
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
    from editxt.textcommand import comment_line
    def test(c):
        eq_(comment_line(c.old, c.token, c.imode, c.isize, c.pad), c.new)
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
    from editxt.textcommand import uncomment_line
    def test(c):
        eq_(uncomment_line(c.old, c.token, c.imode, c.isize, c.pad), c.new)
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
    import editxt.textcommand as tc
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


    c = cbase(method=tc.move_to_beginning_of_line, output=SAME)
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

    c = cbase(method=tc.insert_newline)
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


    c = cbase(method=tc.indent_lines)
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


    c = cbase(method=tc.dedent_lines, scroll=False)
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

    c = cbase(method=tc.delete_backward, setup=setup)
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

    from editxt.textcommand import sort_lines, wrap_lines, reindent
    from editxt.sortlines import SortLinesController, sortlines
    from editxt.wraplines import WrapLinesController, wrap_selected_lines
    from editxt.changeindent import ChangeIndentationController

    for args in [False, True]:
        c = c(args=args)
        yield test, c(action=sort_lines, mod="sortlines",
            ctl=SortLinesController, func=sortlines)
        yield test, c(action=wrap_lines, mod="wraplines",
            ctl=WrapLinesController, func=wrap_selected_lines)

    yield test, c(action=reindent, mod="changeindent",
        ctl=ChangeIndentationController, func=None, args=False)

def test_wrap_to_margin_guide():
    from editxt.textcommand import wrap_at_margin
    from editxt.wraplines import WrapLinesController, wrap_selected_lines
    m = Mocker()
    tv = m.mock(NSTextView)
    wrap = m.replace('editxt.wraplines.wrap_selected_lines')
    ctl_class = m.replace('editxt.wraplines.WrapLinesController')
    ctl = ctl_class.shared_controller() >> m.mock(WrapLinesController)
    opts = m.replace("editxt.commandbase.Options")() >> m.mock()
    wrap_opts = ctl.opts >> m.mock()
    opts.wrap_column = const.DEFAULT_RIGHT_MARGIN
    opts.indent = wrap_opts.indent >> "<indent>"
    wrap(tv, opts)
    with m:
        wrap_at_margin(tv, None, None)

# def test():
#   assert False, "stop"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Other text mangling utility functions that didn't have anywhere else to go

def test_replace_newlines():
    from editxt.textcommand import replace_newlines
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
            replace_newlines(tv, c.eol)
    c = TestConfig(eol=const.EOLS[const.NEWLINE_MODE_UNIX])
    yield test, c(input=u"", output=u"")
    yield test, c(input=u"\r\n", output=u"\n")
    yield test, c(input=u"\n\r\n", output=u"\n\n")
    yield test, c(input=u"\r \n", output=u"\n \n")
    yield test, c(input=u"\r \n \u2028", output=u"\n \n \n")
    yield test, c(input=u"\r \r\n\n \u2028", output=u"\n \n\n \n")

def test_change_indentation():
    from editxt.document import TextDocument
    from editxt.textcommand import change_indentation
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
            change_indentation(tv, c.old, c.new, c.size)
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextControllerCommand tests

def test_TextCommandController_init():
    m = Mocker()
    menu = m.mock(NSMenu)
    with m:
        ctl = TextCommandController(menu)
        eq_(ctl.menu, menu)
        eq_(ctl.commands, {})
        eq_(ctl.commands_by_path, {})
        eq_(ctl.input_handlers, {})
        eq_(ctl.editems, {})

def test_TextCommandController_lookup():
    def test(c):
        m = Mocker()
        menu = m.mock(NSMenu)
        ctl = TextCommandController(menu)
        for command in c.commands:
            ctl.add_command(command, None)
        eq_(ctl.lookup(c.lookup), c.result)
    @mod.command(names="cmd cm")
    def cmd(*args):
        pass
    @mod.command(names="cmd")
    def cm2(*args):
        pass
    @mod.command
    def no(*args):
        pass
    c = TestConfig(commands=[], lookup='cmd', result=None)
    yield test, c
    yield test, c(commands=[no])
    yield test, c(commands=[cmd], result=cmd)
    yield test, c(commands=[cmd, cm2], result=cm2)
    yield test, c(commands=[cmd, cm2], lookup='cm', result=cmd)

def test_TextCommandController_lookup_full_command():
    def test(c):
        m = Mocker()
        menu = m.mock(NSMenu)
        ctl = TextCommandController(menu)
        for command in c.commands:
            ctl.add_command(command, None)
            menu.insertItem_atIndex_(ANY, ANY)
        eq_(ctl.lookup_full_command(c.lookup), c.result)
    @mod.command(names="cm")
    def cmd(*args):
        pass
    @mod.command(parse_args=mod.parse_line_number, lookup_with_parse_args=True)
    def num(*args):
        pass
    c = TestConfig(commands=[], lookup='cmd', result=(None, None))
    yield test, c
    yield test, c(commands=[cmd])
    yield test, c(commands=[num])
    yield test, c(commands=[num], lookup='123', result=(num, 123))

def test_TextCommandController_load_commands():
    def test(c):
        m = Mocker()
        menu = m.mock(NSMenu)
        ctl = TextCommandController(menu)
        handlers = ctl.input_handlers = m.mock(dict)
        add = m.method(ctl.add_command)
        mod = m.mock(dict)
        m.method(ctl.iter_command_modules)() >> [("<path>", mod)]
        cmds = []; mod.get("text_menu_commands", []) >> cmds
        for i in xrange(c.commands):
            cmd = "<command %s>" % i
            add(cmd, "<path>")
            cmds.append(cmd)
        hnds = mod.get("input_handlers", {}) >> {}
        for i in xrange(c.handlers):
            hnds["handle%s" % i] = "<handle %s>" % i
        handlers.update(hnds)
        with m:
            ctl.load_commands()
    c = TestConfig()
    yield test, c(commands=0, handlers=0)
    yield test, c(commands=2, handlers=2)

def test_TextCommandController_add_command():
    def test(c):
        m = Mocker()
        menu = m.mock(NSMenu)
        mi_class = m.replace(mod, 'NSMenuItem')
        ctl = TextCommandController(menu)
        handlers = m.replace(ctl, 'input_handlers')
        validate = m.method(ctl.validate_hotkey)
        cmd = m.mock()
        cmd.names >> []
        cmd.lookup_with_parse_args >> False
        tag = cmd._TextCommandController__tag = ctl.tagger.next() + 1
        validate(cmd.hotkey >> "<hotkey>") >> ("<hotkey>", "<keymask>")
        mi = mi_class.alloc() >> m.mock(NSMenuItem)
        (cmd.title << "<title>").count(2)
        mi.initWithTitle_action_keyEquivalent_(
            '<title>', "performTextCommand:" ,"<hotkey>") >> mi
        mi.setKeyEquivalentModifierMask_("<keymask>")
        mi.setTag_(tag)
        menu.insertItem_atIndex_(mi, tag)
        with m:
            ctl.add_command(cmd, None)
            assert ctl.commands[tag] is cmd, (ctl.commands[tag], cmd)
    c = TestConfig()
    yield test, c
    #yield test, c

def test_TextCommandController_validate_hotkey():
    tc = TextCommandController(None)
    eq_(tc.validate_hotkey(None), (u"", 0))
    eq_(tc.validate_hotkey(("a", 1)), ("a", 1))
    assert_raises(AssertionError, tc.validate_hotkey, ("a", "b", "c"))

def test_TextCommandController_is_textview_command_enabled():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        mi = m.mock(NSMenuItem)
        tv = m.mock(NSTextView)
        tc = m.mock()
        tcc = TextCommandController(None)
        cmds = m.replace(tcc, 'commands')
        cmds.get(mi.tag() >> 42) >> (tc if c.has_command else None)
        if c.has_command:
            if c.error:
                expect(tc.is_enabled(tv, mi)).throw(Exception)
                lg.error("%s.is_enabled failed", ANY, exc_info=True)
            else:
                tc.is_enabled(tv, mi) >> c.enabled
        with m:
            result = tcc.is_textview_command_enabled(tv, mi)
            eq_(result, c.enabled)
    c = TestConfig(has_command=True, enabled=False)
    yield test, c(has_command=False)
    yield test, c(error=True)
    yield test, c(error=False)
    yield test, c(error=False, enabled=True)

def test_TextCommandController_do_textview_command():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        mi = m.mock(NSMenuItem)
        tv = m.mock(NSTextView)
        tc = m.mock()
        tcc = TextCommandController(None)
        cmds = m.replace(tcc, 'commands')
        cmds.get(mi.tag() >> 42) >> (tc if c.has_command else None)
        if c.has_command:
            tc(tv, mi, None)
            if c.error:
                m.throw(Exception)
                lg.error("%s.execute failed", ANY, exc_info=True)
        with m:
            tcc.do_textview_command(tv, mi)
    c = TestConfig(has_command=True)
    yield test, c(has_command=False)
    yield test, c(error=True)
    yield test, c(error=False)

def test_TextCommandController_do_textview_command_by_selector():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        tv = m.mock(NSTextView)
        tcc = TextCommandController(None)
        sel = "<selector>"
        callback = m.mock()
        handlers = m.replace(tcc, 'input_handlers')
        cmd = handlers.get(sel) >> (callback if c.has_selector else None)
        if c.has_selector:
            callback(tv, None, None)
            if c.error:
                m.throw(Exception)
                lg.error("%s failed", callback, exc_info=True)
        with m:
            result = tcc.do_textview_command_by_selector(tv, sel)
            eq_(result, c.result)
    c = TestConfig(has_selector=True, result=False)
    yield test, c(has_selector=False)
    yield test, c(error=True)
    yield test, c(error=False, result=True)
