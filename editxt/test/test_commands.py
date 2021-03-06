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

from mocker import Mocker
import AppKit as ak
import Foundation as fn
from editxt.test.util import assert_raises, eq_, TestConfig, test_app

import editxt.constants as const
import editxt.commands as mod
from editxt.platform.text import Text

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
        mod.split_text,
        mod.join_lines,
        mod.sort_lines,
        mod.unique_lines,
        mod.reindent,
        mod.find,
        mod.ag,
        mod.blame,
        mod.diff,
        mod.flake8,
        mod.github_url,
        mod.grab,
        mod.markdown,
        mod.open_,
        mod.pathfind,
        mod.find_definition,
        mod.python,
        mod.sort_imports,
        mod.clear_highlighted_text,
        mod.docnav,
        mod.preferences,
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
        "moveToBeginningOfLineAndModifySelection:",
        "moveToLeftEndOfLineAndModifySelection:",
        #"moveToEndOfLine:",
        #"moveToRightEndOfLine:",
        #"moveToEndOfLineAndModifySelection:",
        #"moveToRightEndOfLineAndModifySelection:",
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
    def get_selection(string, expected=None):
        if '^' not in string and expected is not None:
            return expected, string
        num = string.count('^')
        assert num > 0, "no selection markers: {!r}".format(string)
        assert num < 3, "too many selection markers: {!r}".format(string)
        text = Text(string)
        i = text.find("^")
        if num == 1:
            sel = (i, 0)
        else:
            sel = (i, text.find('^', i + 1) - i - 1)
        if expected is not None:
            eq_(sel, expected)
        return sel, string.replace('^', '')

    def mark_selection(string_or_editor, sel=None):
        if isinstance(string_or_editor, str):
            if sel is None:
                if '^' in string_or_editor:
                    return string_or_editor
                raise Exception("no selection to add")
            string = string_or_editor
            if '^' in string:
                get_selection(string, sel)  # verify already marked
                return string
            text = Text(string)
        else:
            text = string_or_editor.text
            sel = string_or_editor.selection
        assert '^' not in text, repr(text)
        i, j = sel[0], sum(sel)
        if i == j:
            return text[:i] + '^' + text[i:]
        return text[:i] + '^' + text[i:j] + '^' + text[j:]

    from editxt.platform.mac.document import setup_scroll_view
    SAME = "<SAME AS INPUT>"
    tapp = test_app("editor")
    app = tapp.__enter__()
    editor = app.windows[0].projects[0].editors[0]
    editor.on_selection_changed = lambda *a: None
    editor.scroll_view = setup_scroll_view(editor, fn.NSMakeRect(0, 0, 100, 100))
    editor.text_view = editor.scroll_view.documentView()
    def teardown():
        editor.scroll_view.verticalRulerView().denotify()
        tapp.__exit__(None, None, None)
    def test(c):
        if c.eol != "\n":
            c.input = c.input.replace("\n", c.eol)
            c.output = c.output.replace("\n", c.eol)
        oldsel, input = get_selection(c.input, c._get("oldsel"))
        editor.document.indent_mode = c.mode
        editor.document.indent_size = c.size
        editor.document.eol = c.eol
        editor.text[:] = input
        editor.selection = oldsel
        c.setup(c, TestConfig(locals()))
        c.method(editor, None)
        if c.output == SAME:
            eq_(editor.text[:], input)
        elif 'newsel' in c or '^' in c.output:
            eq_(mark_selection(editor), mark_selection(c.output, c._get("newsel")))
        else:
            eq_(editor.text[:], c.output.replace('^', ''))
        if "newsel" in c or '^' in c.output:
            newsel = get_selection(c.output, c._get("newsel"))[0]
            eq_(editor.selection, fn.NSMakeRange(*newsel))
            if "prevchar" in c:
                prevchar = c.prevchar
                if c.eol != "\n":
                    prevchar = prevchar.replace("\n", c.eol)[-1]
                eq_(editor.text[(newsel[0] - 1, 1)], prevchar)

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

        yield test, c(input="  \n^  '\U0001f34c'\n  '", newsel=(5+i, 0), prevchar=' ')
        yield test, c(input="  \n ^ '\U0001f34c'\n  '", newsel=(5+i, 0), prevchar=' ')
        yield test, c(input="  \n  ^'\U0001f34c'\n  '", newsel=(3+i, 0), prevchar='\n')
        yield test, c(input="  \n  '^\U0001f34c'\n  '", newsel=(5+i, 0), prevchar=' ')
        yield test, c(input="  \n  '\U0001f34c'\n^  '", newsel=(12+i*2, 0), prevchar=' ')
        yield test, c(input="  \n  '\U0001f34c'\n ^ '", newsel=(12+i*2, 0), prevchar=' ')
        yield test, c(input="  \n  '\U0001f34c'\n  ^'", newsel=(10+i*2, 0), prevchar='\n')

    c = cbase(method=mod.select_to_beginning_of_line, output=SAME)
    for eol in eols:
        c = c(eol=eol)
        yield test, c(input="", oldsel=(0, 0), newsel=(0, 0))
        yield test, c(input=" ", oldsel=(0, 0), newsel=(0, 1))
        yield test, c(input=" ", oldsel=(0, 1), newsel=(1, 0))
        yield test, c(input=" ", oldsel=(1, 0), newsel=(0, 1))
        yield test, c(input="  ", oldsel=(0, 0), newsel=(0, 2))
        yield test, c(input="  ", oldsel=(0, 1), newsel=(0, 2))
        yield test, c(input="  ", oldsel=(0, 2), newsel=(2, 0))
        yield test, c(input="  ", oldsel=(1, 0), newsel=(0, 1))
        yield test, c(input="  ", oldsel=(1, 1), newsel=(0, 2))
        yield test, c(input="  ", oldsel=(2, 0), newsel=(0, 2))
        yield test, c(input="  x", oldsel=(0, 0), newsel=(0, 2))
        yield test, c(input="  x", oldsel=(0, 1), newsel=(0, 2))
        yield test, c(input="  x", oldsel=(0, 2), newsel=(2, 0))
        yield test, c(input="  x", oldsel=(0, 3), newsel=(2, 1))
        yield test, c(input="  x", oldsel=(1, 0), newsel=(0, 1))
        yield test, c(input="  x", oldsel=(1, 1), newsel=(0, 2))
        yield test, c(input="  x", oldsel=(2, 0), newsel=(0, 2))
        i = len(c.eol) - 1
        yield test, c(input="  \n ", oldsel=(0, 0), newsel=(0, 2))
        yield test, c(input="  \n ", oldsel=(0, 1), newsel=(0, 2))
        yield test, c(input="  \n ", oldsel=(0, 2), newsel=(2, 0))
        yield test, c(input="  \n ", oldsel=(0, 3+i), newsel=(2, 1+i))
        yield test, c(input="  \n ", oldsel=(1, 0), newsel=(0, 1))
        yield test, c(input="  \n ", oldsel=(1, 1), newsel=(0, 2))
        yield test, c(input="  \n ", oldsel=(2, 0), newsel=(0, 2))
        yield test, c(input="\n ", oldsel=(1+i, 0), newsel=(1+i, 1))
        yield test, c(input="    \n    ", oldsel=(5+i, 0), newsel=(5+i, 4))
        yield test, c(input="    \n    ", oldsel=(5+i, 1), newsel=(5+i, 4))
        yield test, c(input="    \n    ", oldsel=(5+i, 2), newsel=(5+i, 4))
        yield test, c(input="    \n    ", oldsel=(5+i, 3), newsel=(5+i, 4))
        yield test, c(input="    \n    ", oldsel=(5+i, 4), newsel=(9+i, 0))
        yield test, c(input="    \n    ", oldsel=(7+i, 0), newsel=(5+i, 2))
        yield test, c(input="    \n    ", oldsel=(7+i, 1), newsel=(5+i, 3))
        yield test, c(input="    \n    ", oldsel=(7+i, 2), newsel=(5+i, 4))
        yield test, c(input="    \n    ", oldsel=(9+i, 0), newsel=(5+i, 4))
        yield test, c(input="    \n    x", oldsel=(5+i, 0), newsel=(5+i, 4))
        yield test, c(input="    \n    x", oldsel=(5+i, 1), newsel=(5+i, 4))
        yield test, c(input="    \n    x", oldsel=(5+i, 2), newsel=(5+i, 4))
        yield test, c(input="    \n    x", oldsel=(5+i, 3), newsel=(5+i, 4))
        yield test, c(input="    \n    x", oldsel=(5+i, 4), newsel=(9+i, 0))
        yield test, c(input="    \n    x", oldsel=(5+i, 5), newsel=(9+i, 1))
        yield test, c(input="    \n    x", oldsel=(7+i, 0), newsel=(5+i, 2))
        yield test, c(input="    \n    x", oldsel=(7+i, 1), newsel=(5+i, 3))
        yield test, c(input="    \n    x", oldsel=(7+i, 2), newsel=(5+i, 4))
        yield test, c(input="    \n    x", oldsel=(7+i, 3), newsel=(5+i, 5))
        yield test, c(input="    \n    x", oldsel=(9+i, 0), newsel=(5+i, 4))
        yield test, c(input="    \n    \n", oldsel=(5+i, 0), newsel=(5+i, 4))
        yield test, c(input="    \n    \n", oldsel=(5+i, 1), newsel=(5+i, 4))
        yield test, c(input="    \n    \n", oldsel=(5+i, 2), newsel=(5+i, 4))
        yield test, c(input="    \n    \n", oldsel=(5+i, 3), newsel=(5+i, 4))
        yield test, c(input="    \n    \n", oldsel=(5+i, 4), newsel=(9+i, 0))
        yield test, c(input="    \n    \n", oldsel=(5+i, 5+i), newsel=(9+i, 1+i))
        yield test, c(input="    \n    \n", oldsel=(7+i, 0), newsel=(5+i, 2))
        yield test, c(input="    \n    \n", oldsel=(7+i, 1), newsel=(5+i, 3))
        yield test, c(input="    \n    \n", oldsel=(7+i, 2), newsel=(5+i, 4))
        yield test, c(input="    \n    \n", oldsel=(7+i, 3+i), newsel=(5+i, 5+i))
        yield test, c(input="    \n    \n", oldsel=(9+i, 0), newsel=(5+i, 4))
        yield test, c(input="    \n    \n", oldsel=(9+i, 1+i), newsel=(5+i, 5+i))

        yield test, c(input="  \n^  '\U0001f34c'\n  '",  newsel=(3+i, 2), prevchar='\n')
        yield test, c(input="  \n^ ^ '\U0001f34c'\n  '", newsel=(3+i, 2), prevchar='\n')
        yield test, c(input="  \n^  ^'\U0001f34c'\n  '", newsel=(5+i, 0), prevchar=' ')
        yield test, c(input="  \n^  '^\U0001f34c'\n  '", newsel=(5+i, 1), prevchar=' ')
        yield test, c(input="  \n ^ '\U0001f34c'\n  '",  newsel=(3+i, 1), prevchar='\n')
        yield test, c(input="  \n ^ ^'\U0001f34c'\n  '", newsel=(3+i, 2), prevchar='\n')
        yield test, c(input="  \n  ^'\U0001f34c'\n  '",  newsel=(3+i, 2), prevchar='\n')
        yield test, c(input="  \n  ^'^\U0001f34c'\n  '", newsel=(3+i, 3), prevchar='\n')
        yield test, c(input="  \n  '^\U0001f34c'\n  '",  newsel=(5+i, 1), prevchar=' ')
        yield test, c(input="  \n  '\U0001f34c'\n^  '",  newsel=(10+i*2, 2), prevchar='\n')
        yield test, c(input="  \n  '\U0001f34c'\n^ ^ '", newsel=(10+i*2, 2), prevchar='\n')
        yield test, c(input="  \n  '\U0001f34c'\n^  ^'", newsel=(12+i*2, 0), prevchar=' ')
        yield test, c(input="  \n  '\U0001f34c'\n^  '^", newsel=(12+i*2, 1), prevchar=' ')
        yield test, c(input="  \n  '\U0001f34c'\n ^ '",  newsel=(10+i*2, 1), prevchar='\n')
        yield test, c(input="  \n  '\U0001f34c'\n ^ ^'", newsel=(10+i*2, 2), prevchar='\n')
        yield test, c(input="  \n  '\U0001f34c'\n  ^'",  newsel=(10+i*2, 2), prevchar='\n')
        yield test, c(input="  \n  '\U0001f34c'\n  ^'^", newsel=(10+i*2, 3), prevchar='\n')
        yield test, c(input="  \n  '\U0001f34c'\n  '^",  newsel=(12+i*2, 1), prevchar=' ')

#    c = cbase(method=mod.move_to_end_of_line, output=SAME)
#    for eol in eols:
#        c = c(eol=eol)
#        yield test, c(input="", oldsel=(0, 0), newsel=(0, 0))
#        yield test, c(input=" ", oldsel=(0, 0), newsel=(1, 0))
#        yield test, c(input=" ", oldsel=(1, 0), newsel=(1, 0))
#        yield test, c(input="  ", oldsel=(0, 0), newsel=(2, 0))
#        yield test, c(input="  ", oldsel=(1, 0), newsel=(2, 0))
#        yield test, c(input="  ", oldsel=(2, 0), newsel=(2, 0))
#        yield test, c(input="  x", oldsel=(0, 0), newsel=(3, 0))
#        yield test, c(input="  x", oldsel=(1, 0), newsel=(3, 0))
#        yield test, c(input="  x", oldsel=(2, 0), newsel=(3, 0))
#        yield test, c(input="  \n ", oldsel=(0, 0), newsel=(2, 0))
#        yield test, c(input="  \n ", oldsel=(1, 0), newsel=(2, 0))
#        yield test, c(input="  \n ", oldsel=(2, 0), newsel=(2, 0))
#        i = len(c.eol) - 1
#        yield test, c(input="\n ", oldsel=(1 + i, 0), newsel=(2 + i, 0))
#        yield test, c(input="    \n    ", oldsel=(5 + i, 0), newsel=(9 + i, 0))
#        yield test, c(input="    \n    ", oldsel=(7 + i, 0), newsel=(9 + i, 0))
#        yield test, c(input="    \n    ", oldsel=(9 + i, 0), newsel=(9 + i, 0))
#        yield test, c(input="    \n    x", oldsel=(5 + i, 0), newsel=(10 + i, 0))
#        yield test, c(input="    \n    x", oldsel=(7 + i, 0), newsel=(10 + i, 0))
#        yield test, c(input="    \n    x", oldsel=(9 + i, 0), newsel=(10 + i, 0))
#        yield test, c(input="    \n    \n", oldsel=(5 + i, 0), newsel=(9 + i, 0))
#        yield test, c(input="    \n    \n", oldsel=(7 + i, 0), newsel=(9 + i, 0))
#        yield test, c(input="    \n    \n", oldsel=(9 + i, 0), newsel=(9 + i, 0))
#
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(3+i, 0), newsel=(9+i, 0), prevchar="'")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(4+i, 0), newsel=(9+i, 0), prevchar="'")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(5+i, 0), newsel=(9+i, 0), prevchar="'")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(6+i, 0), newsel=(9+i, 0), prevchar="'")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(10+i*2, 0), newsel=(13+i*2, 0), prevchar="'")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(11+i*2, 0), newsel=(13+i*2, 0), prevchar="'")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(12+i*2, 0), newsel=(13+i*2, 0), prevchar="'")
#    yield test, c(eol='\r\n', input="  \n  ", oldsel=(3, 0), newsel=(2, 0), prevchar=" ")
#
#    c = cbase(method=mod.select_to_end_of_line, output=SAME)
#    for eol in eols:
#        c = c(eol=eol)
#        yield test, c(input="", oldsel=(0, 0), newsel=(0, 0))
#        yield test, c(input=" ", oldsel=(0, 0), newsel=(0, 1))
#        yield test, c(input=" ", oldsel=(1, 0), newsel=(1, 0))
#        yield test, c(input="  ", oldsel=(0, 0), newsel=(0, 2))
#        yield test, c(input="  ", oldsel=(1, 0), newsel=(1, 1))
#        yield test, c(input="  ", oldsel=(2, 0), newsel=(2, 0))
#        yield test, c(input="  x", oldsel=(0, 0), newsel=(0, 3))
#        yield test, c(input="  x", oldsel=(1, 0), newsel=(1, 2))
#        yield test, c(input="  x", oldsel=(2, 0), newsel=(2, 1))
#        yield test, c(input="  \n ", oldsel=(0, 0), newsel=(0, 2))
#        yield test, c(input="  \n ", oldsel=(1, 0), newsel=(1, 1))
#        yield test, c(input="  \n ", oldsel=(2, 0), newsel=(2, 0))
#        i = len(c.eol) - 1
#        yield test, c(input="\n ", oldsel=(1+i, 0), newsel=(1+i, 1))
#        yield test, c(input="    \n    ", oldsel=(4, 1+i), newsel=(4, 5+i))
#        yield test, c(input="    \n    ", oldsel=(5+i, 0), newsel=(5+i, 4))
#        yield test, c(input="    \n    ", oldsel=(7+i, 0), newsel=(7+i, 2))
#        yield test, c(input="    \n    ", oldsel=(9+i, 0), newsel=(9+i, 0))
#        yield test, c(input="    \n    x", oldsel=(5+i, 0), newsel=(5+i, 5))
#        yield test, c(input="    \n    x", oldsel=(7+i, 0), newsel=(7+i, 3))
#        yield test, c(input="    \n    x", oldsel=(9+i, 0), newsel=(9+i, 1))
#        yield test, c(input="    \n    \n", oldsel=(5+i, 0), newsel=(5+i, 4))
#        yield test, c(input="    \n    \n", oldsel=(7+i, 0), newsel=(7+i, 2))
#        yield test, c(input="    \n    \n", oldsel=(9+i, 0), newsel=(9+i, 0))
#
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(3+i, 0), newsel=(3+i, 6), prevchar="\n")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(4+i, 0), newsel=(4+i, 5), prevchar=" ")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(5+i, 0), newsel=(5+i, 4), prevchar=" ")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(6+i, 0), newsel=(6+i, 3), prevchar="'")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(10+i*2, 0), newsel=(10+i*2, 3), prevchar="\n")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(11+i*2, 0), newsel=(11+i*2, 2), prevchar=" ")
#        yield test, c(input="  \n  '\U0001f34c'\n  '", oldsel=(12+i*2, 0), newsel=(12+i*2, 1), prevchar=" ")
#    yield test, c(eol='\r\n', input="  \n  ", oldsel=(3, 0), newsel=(2, 0), prevchar=" ")

    c = cbase(method=mod.insert_newline)
    uchar = '\U0001f34c'
    uchar4 = uchar * 4
    for eol in eols:
        c = c(eol=eol)
        yield test, c(input="", output="\n", oldsel=(0, 0))
        yield test, c(input=" ", output=" \n ", oldsel=(1, 0))
        yield test, c(input="  ", output="  \n  ", oldsel=(2, 0))
        yield test, c(input="    ", output=" \n ", oldsel=(1, 0))
        yield test, c(input="\t", output="\t\n\t", oldsel=(1, 0))
        yield test, c(input="a bc", output="a\nbc", oldsel=(1, 0))
        yield test, c(input="a bc", output="a\nc", oldsel=(1, 2))
        yield test, c(input="  a bc", output="\n  a bc", oldsel=(0, 0))
        yield test, c(input="  a bc", output="\n a bc", oldsel=(0, 1))
        yield test, c(input="  a bc", output=" \n a bc", oldsel=(1, 0))
        yield test, c(input="  a bc", output=" \n a bc", oldsel=(1, 1))
        yield test, c(input="  a bc", output="  a\n  bc", oldsel=(3, 0))
        yield test, c(input="  a bc", output="  a\n  bc", oldsel=(3, 1))
        yield test, c(input="  a bc", output="  a\n  c", oldsel=(3, 2))
        yield test, c(input="   a bc", output=" \n a bc", oldsel=(1, 0))
        yield test, c(input="   a bc", output="  \n  a bc", oldsel=(2, 0))
        i = len(eol) - 1
        yield test, c(input=" a\n b", output=" a\n b\n ", oldsel=(5 + i, 0))
        yield test, c(input="\n x", output="\n\n x", oldsel=(1 + i, 0))
        yield test, c(input=uchar4 + "\n    x^\n", output=uchar4 + "\n    x\n    ^\n")

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


    def setup(c, x):
        if c.mode == const.INDENT_MODE_TAB:
            x.editor.text_view.deleteBackward_(None)

    c = cbase(method=mod.delete_backward, setup=setup)
    for eol in eols:
        c = c(mode=const.INDENT_MODE_TAB, eol=eol)
        yield test, c(input="", output=SAME, oldsel=(0, 0), newsel=(0, 0), scroll=False)
        yield test, c(input="\t", output="", oldsel=(1, 0), newsel=(0, 0), scroll=False)
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
        yield test, c(input="\n    ", output="\n  ", oldsel=(5+i, 0), newsel=(3+i, 0))
        yield test, c(input="\n    ", output="\n  ", oldsel=(3+i, 0), newsel=(1+i, 0))
        yield test, c(input="\n    ", output="\n   ", oldsel=(2+i, 0), newsel=(1+i, 0))
        c = c(size=4)
        yield test, c(input="    ^", output="^")
        yield test, c(input="          ^", output="        ^")
        yield test, c(input="    x  ^", output="    x ^")
        yield test, c(input="    x   ^", output="    x  ^")
        yield test, c(input="    x    ^", output="    x   ^")
        yield test, c(input="    x     ^", output="    x   ^")
        yield test, c(input="    x      ^", output="    x   ^")
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
        yield test, c(input="\n           ^ ", output="\n        ^ ")
        uchar3 = uchar * 3
        yield test, c(input=uchar3 + "\n    ^x\n", output=uchar3 + "\n^x\n")
        yield test, c(input=uchar3 + "\n    x^\n", output=uchar3 + "\n    ^\n")
        yield test, c(input=uchar3 + "\n      ^\n", output=uchar3 + "\n    ^\n")

    teardown()

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
    fake_text_view = TestConfig(soft_wrap=lambda:const.WRAP_NONE)
    class editor:
        class project:
            path = os.path.expanduser("~/project")
        class document:
            class syntaxdef:
                name = "Unknown"
                comment_token = "x"
        text_view = object
        dirname = lambda:None
        font = Font("Mension", 15.0, False, None)
        highlight_selected_text = True
        indent_mode = const.INDENT_MODE_TAB
        indent_size = 2
        soft_wrap = const.WRAP_WORD
        updates_path_on_file_move = True
    def test(command, completions, placeholder):
        bar = CommandTester(mod.set_variable, editor=editor)
        eq_(bar.get_completions(command), (completions, None))
        eq_(bar.get_placeholder(command), placeholder)
    yield test, "set ", [
            "comment_token",
            "font",
            "highlight_selected_text",
            "indent",
            "language",
            "newline_mode",
            "project_path",
            "soft_wrap",
            "updates_path_on_file_move",
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
    yield test, "set updates_path_on_file_move ", ["yes", "no"], "yes"

    def test(command, attribute, value=None):
        with test_app("editor*") as app:
            m = Mocker()
            editor = app.windows[0].current_editor
            editor.text_view = fake_text_view
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
            editor.text_view = fake_text_view
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
            editor.text_view = fake_text_view
            do = CommandTester(mod.set_variable, editor=editor)
            do(command)
            eq_(editor.syntaxdef, lang)
    yield test, "set language py", "Python"
    yield test, "set lang plain", "Plain Text"

    # set comment_token
    def test(command, token):
        with test_app("editor*") as app:
            editor = app.windows[0].current_editor
            editor.text_view = fake_text_view
            do = CommandTester(mod.set_variable, editor=editor)
            do(command)
            eq_(editor.document.comment_token, token)
    yield test, "set comment_token #", "#"
    yield test, "set comment_token //", "//"
    yield test, "set comment_token", "//"

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
            args = '<args>'
            func(editor, args)
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

        class command_view:
            def append_message(msg, msg_type=const.INFO):
                if self.output is None:
                    self.output = msg
                else:
                    self.output += msg
                self.output_msg_type = msg_type

            def is_waiting(self, waiting=None):
                pass

        class editor:
            text_view = kw.pop("textview", None)
            file_path = None
            selection = classproperty(lambda cls: cls.text_view.selectedRange())
            text = Text(kw.pop("text", ""))

            def dirname():
                return None

            @classmethod
            def put(cls, text, rng, select=False):
                cls.text[rng] = text
                if select:
                    cls.selection = (rng[0], len(text))

        editor = kw.pop("editor", editor)
        if "sel" in kw and editor.text_view is None:

            class textview:
                _selection = kw["sel"]

                @staticmethod
                def string():
                    return str(editor.text)

                @classmethod
                def select(cls, rng):
                    cls._selection = rng

                @classmethod
                def selectedRange(cls):
                    return cls._selection

                @staticmethod
                def shouldChangeTextInRange_replacementString_(rng, text):
                    return True

                @staticmethod
                def didChangeText():
                    pass

            editor.text_view = textview
        if not isinstance(editor, type(Mocker().mock())):
            editor.message = message
            editor.command_view = kw.pop("command_view", command_view)
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
            self.commander.do_menu_command(self.editor, TestConfig(tag=lambda:tag))

    def __getattr__(self, name):
        return getattr(self.bar, name)


class classproperty:

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, type):
        return self.fget(type)
