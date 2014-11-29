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
import json
import logging
from os.path import join

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import eq_, assert_raises
import AppKit as ak
import Foundation as fn
from editxt.test.util import gentest, TestConfig, tempdir, test_app

import editxt.constants as const
import editxt.textcommand as mod
from editxt.command.parser import (ArgumentError, CommandParser, Options,
    Choice, Int, Regex, CompleteWord, CompletionsList)
from editxt.commands import command
from editxt.platform.views import CommandView
from editxt.test.test_commands import CommandTester
from editxt.textcommand import CommandManager

log = logging.getLogger(__name__)


class IllBehaved(Int):
    def get_placeholder(self, text, index):
        raise Exception("bang!")
    def get_completions(self, token):
        raise Exception("bang!")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CommandBar tests

def test_CommandBar_window():
    window = type('Window', (object,), {})()
    text_commander = type('CommandManager', (object,), {})()
    cmd = mod.CommandBar(window, text_commander)
    eq_(cmd.window, window)
    eq_(cmd.text_commander, text_commander)
    # NOTE the following depends on CPython weakref behavior
    del window, text_commander
    eq_(cmd.window, None)
    eq_(cmd.text_commander, None)

def test_CommandBar_on_key_press():
    @command(arg_parser=CommandParser(
        Choice(*"test_1 test_2 test_3 text".split()),
        Choice(('forward', False), ('reverse xyz', True), name='reverse'),
        Regex('sort_regex', True),
    ))
    def cmd(editor, sender, args):
        pass

    @command(arg_parser=CommandParser(Int('number')))
    def count(editor, sender, args):
        raise NotImplementedError("should not get here")

    @command(arg_parser=CommandParser(IllBehaved("bang")))
    def ill(editor, sender, args):
        raise NotImplementedError("should not get here")

    NA = object()

    @gentest
    def test(text, command_key, *,
            new_text=NA,
            complete=None,
            default_complete=None,
            new_complete=None,
            new_default_complete=None,
            completions_select_range=None,
            sel=None,
            new_sel=None,
            expect=True,
            has_command=True
        ):
        view = CommandView()
        bar = CommandTester(cmd, count, ill, textview=object, command_view=view)
        bar.activate(text)
        if complete:
            view.completions.items = complete
        if default_complete:
            print("selected completion:", complete.index(default_complete))
            view.completions.select(complete.index(default_complete))
            view.command_text = text
        if sel:
            view.command_text_selected_range = sel
        if completions_select_range:
            view.completions.select_range = completions_select_range

        result = bar.on_key_command(command_key, view)
        eq_(result, expect)
        eq_(view.completions.items,
            (complete or []) if new_complete is None else new_complete)
        eq_(view.completions.selected_item, new_default_complete)
        eq_(view.command_text, text if new_text is NA else new_text)
        if sel is not None or new_sel is not None:
            eq_(view.command_text_selected_range, sel if new_sel is None else new_sel)
        eq_(view.command, bar.bar if has_command else None)

    SEL = CommandView.KEYS.SELECTION_CHANGED
    ESC = CommandView.KEYS.ESC
    TAB = CommandView.KEYS.TAB
    BACK_TAB = CommandView.KEYS.BACK_TAB
    UP = CommandView.KEYS.UP
    DOWN = CommandView.KEYS.DOWN
    ENTER = CommandView.KEYS.ENTER

    yield test("c", SEL)
    yield test("c", SEL, complete=["cmd", "count", "ill"], new_complete=["cmd", "count"])

    yield test("", TAB, new_complete=["cmd", "count", "ill"])
    yield test("", TAB, complete=["cmd", "count", "ill"])
    yield test("c", TAB, new_complete=["cmd", "count"])
    yield test("c", TAB, complete=["cmd", "count"], new_complete=["cmd", "count"])
    yield test("cm", TAB, new_text="cmd ")
    yield test("cm", TAB, complete=["cmd"], new_text="cmd ", new_complete=[])
    yield test("cmd t", TAB,
        complete=[CompleteWord(w, overlap=1) for w in ["test_1", "test_2"]],
        new_text="cmd test_",
        new_complete=["test_1", "test_2"])

    #yield test("", DOWN)
    yield test("", DOWN, new_text="cmd ",
        complete=["cmd", "count", "ill"], new_default_complete="cmd")
    yield test("cmd ", DOWN, new_text="count ",
        complete=["cmd", "count", "ill"], completions_select_range=(0, 4),
        default_complete="cmd", new_default_complete="count")

    #yield test("", UP)
    yield test("", UP, new_text="ill ",
        complete=["cmd", "count", "ill"], new_default_complete="ill")
    yield test("ill ", UP, new_text="count ",
        complete=["cmd", "count", "ill"], completions_select_range=(0, 4),
        default_complete="ill", new_default_complete="count")

    yield test("cmd ", ENTER, new_text=None, has_command=False)

    yield test("c", ESC, new_text=None, has_command=False)
    yield test("c", ESC,
        completions_select_range=(0, 1), sel=(1, 0), new_sel=(0, 1),
        complete=["cmd", "count", "ill"], new_complete=[])

    yield test("c", BACK_TAB)

def test_CommandBar_execute():
    from editxt.editor import Editor
    from editxt.textcommand import CommandManager
    def test(c):
        m = Mocker()
        window = m.mock()
        beep = m.replace(ak, 'NSBeep')
        commander = m.mock(CommandManager)
        bar = mod.CommandBar(window, commander)
        message = m.replace(bar, "message")
        args = c.text.split()
        if args and not c.current:
            window.current_editor >> None
            beep()
        elif args:
            editor = window.current_editor >> m.mock(Editor)
            command = m.mock()
            if c.lookup == 'first':
                commander.lookup(args[0]) >> command
                if isinstance(c.args, Exception):
                    expect(command.arg_parser.parse(c.argstr)).throw(c.args)
                else:
                    command.arg_parser.parse(c.argstr) >> c.args
            elif c.lookup == 'full':
                commander.lookup(args[0]) >> None
                if c.args is None:
                    commander.lookup_full_command(c.text) >> (None, None)
                else:
                    commander.lookup_full_command(c.text) >> (command, c.args)
            else:
                assert c.lookup == None, c.lookup
            if c.args is None or isinstance(c.args, Exception):
                if isinstance(c.args, Exception):
                    kw = {"exc_info": True}
                else:
                    kw = {}
                message(c.msg, **kw)
            else:
                res = command(editor, bar, '<args>')
                if c.error:
                    expect(res).throw(Exception('bang!'))
                    message(ANY, exc_info=True)
                elif not c.text.startswith(" "):
                    res >> c.msg
                    history = commander.history >> m.mock(mod.CommandHistory)
                    history.append(c.text)
                    if c.msg:
                        message(c.msg, msg_type=const.INFO)
        with m:
            bar.execute(c.text)
    c = TestConfig(args='<args>', error=False, current=True,
                   msg=None, exc_info=None)
    yield test, c(text='')
# these tests are too fragile (bad use of mocks)
#    yield test, c(text='cmd x y z', argstr='x y z', lookup='first')
#    yield test, c(text='cmd x y z', argstr='x y z', lookup='first', msg="msg")
#    yield test, c(text=' cmd x y z', argstr='x y z', lookup='first')
#    yield test, c(text='cmd  x y  z', argstr=' x y  z', lookup='first')
#    yield test, c(text='cmd x ', argstr='x ', lookup='first', args=Exception(),
#                  msg='argument parse error: x ', exc_info=True)
    yield test, c(text='123 456', lookup='full')
    yield test, c(text='123 456', lookup='full', msg="message for you, sir!")
    yield test, c(text='123 456', lookup='full', current=False)
#    yield test, c(text='cmd', argstr='', lookup='first', args=None,
#                  msg='invalid command arguments: ')
    yield test, c(text='123 456', lookup='full', args=None,
                  msg='unknown command: 123 456')
    yield test, c(text='123 456', lookup='full', error=True)

def test_CommandBar_get_placeholder():
    def test(c):
        m = Mocker()
        beep = m.replace(ak, 'NSBeep')
        @command(arg_parser=CommandParser(
            Choice(('selection', True), ('all', False)),
            Choice(('no', False), ('yes', True)),
            Regex('sort_regex', True),
        ))
        def cmd(editor, sender, args):
            raise NotImplementedError("should not get here")
        @command(arg_parser=CommandParser(
            Regex('search_pattern', replace=c.replace),
            Choice(('yep', False), ('yes', True)),
        ), lookup_with_arg_parser=True)
        def search(editor, sender, args):
            raise NotImplementedError("should not get here")
        @command(arg_parser=CommandParser(IllBehaved("bang")))
        def ill(editor, sender, args):
            raise NotImplementedError("should not get here")
        bar = CommandTester(cmd, search, ill)
        with m:
            eq_(bar.get_placeholder(c.text), c.expect)
    c = TestConfig(replace=False)
    yield test, c(text='', expect="")
    yield test, c(text='cmd', expect=" selection no sort_regex")
    yield test, c(text='cmd ', expect="selection no sort_regex")
    yield test, c(text='cmd s', expect="election no sort_regex")
    yield test, c(text='cmd sx', expect="")
    yield test, c(text='cmd sel', expect="ection no sort_regex")
    yield test, c(text='cmd sel ', expect="no sort_regex")
    yield test, c(text='cmd sel /', expect="//")
    yield test, c(text='cmd a', expect="ll no sort_regex")
    yield test, c(text='cmd a ', expect="no sort_regex")
    yield test, c(text='cmd all', expect=" no sort_regex")
    yield test, c(text='cmd all ', expect="no sort_regex")
    yield test, c(text='cmd x', expect="")
    yield test, c(text='cmd x ', expect="")
    yield test, c(text='cmd   ', expect="sort_regex")
    yield test, c(text='cmd  /', expect="//")
    yield test, c(text='cmd   :', expect="::")
    yield test, c(text='/', expect="/ yep")
    yield test, c(text='/x', expect="/ yep")
    yield test, c(text='/x ', expect="/ yep")
    yield test, c(text='/x/ ', expect="yep")
    yield test, c(text='/x/  ', expect="")
    yield test, c(text='/x/ y', expect="...")
    yield test, c(text='/x/ y ', expect="")
    yield test, c(text='/x/ a', expect="")
    c = c(replace=True)
    yield test, c(text='/', expect="// yep")
    yield test, c(text='/     ', expect="// yep")
    yield test, c(text='/x', expect="// yep")
    yield test, c(text='/x ', expect="// yep")
    yield test, c(text='/x/ ', expect="/ yep")
    yield test, c(text='/x/  ', expect="/ yep")
    yield test, c(text='/x//', expect=" yep")
    yield test, c(text='/x//i', expect=" yep")
    yield test, c(text='/x// ', expect="yep")
    yield test, c(text='/x// y', expect="...")
    yield test, c(text='/x// y ', expect="")
    yield test, c(text='/x// a', expect="")
    yield test, c(text='ill', expect="")

def test_CommandBar_get_completions():
    class HexDigit(Int):
        def get_completions(self, token):
            return CompletionsList("0123456789abcdef") #, selected_index=3)

    def test(c):
        m = Mocker()
        beep = m.replace(ak, 'NSBeep')

        @command(arg_parser=CommandParser(
            Choice(('selection', True), ('all', False)),
            Choice(('forward', False), ('reverse xyz', True), name='reverse'),
            Regex('sort_regex', True),
        ))
        def cmd(editor, sender, args):
            raise NotImplementedError("should not get here")

        @command(arg_parser=CommandParser(
            Regex('search_pattern'),
            Choice(('yes', True), ('no', False)),
        ), lookup_with_arg_parser=True)
        def search(editor, sender, args):
            raise NotImplementedError("should not get here")

        @command(arg_parser=CommandParser(Int('number')), is_enabled=lambda *a: False)
        def count(editor, sender, args):
            raise NotImplementedError("should not get here")

        @command(arg_parser=CommandParser(HexDigit('hex')))
        def hex(editor, sender, args):
            raise NotImplementedError("should not get here")

        @command(arg_parser=CommandParser(IllBehaved("bang")))
        def ill(editor, sender, args):
            raise NotImplementedError("should not get here")

        bar = CommandTester(cmd, search, count, hex, ill, textview=object)
        with m:
            eq_(bar.get_completions(c.text), (c.expect, c.select))
    c = TestConfig(select=None)
    yield test, c(text='x', expect=[])
    yield test, c(text='', expect=["cmd", "hex", "ill", "search"])
    yield test, c(text='c', expect=["cmd"])
    yield test, c(text='cm', expect=["cmd"])
    yield test, c(text='cmd', expect=["cmd"])
    yield test, c(text='cmx', expect=[])
    yield test, c(text='cmd ', expect=["selection", "all"])
    yield test, c(text='cmd s', expect=["selection"])
    yield test, c(text='cmd se', expect=["selection"])
    yield test, c(text='cmd selection', expect=["selection"])
    yield test, c(text='cmd sec', expect=[])
    yield test, c(text='cmd s ', expect=["forward", "reverse"])
    yield test, c(text='cmd s r', expect=["reverse"])
    yield test, c(text='cmd s x', expect=["xyz"])
    yield test, c(text='hex ', expect=list("0123456789abcdef"))
    yield test, c(text='/', expect=[])
    yield test, c(text='/ ', expect=[])
    yield test, c(text='/a', expect=[])
    yield test, c(text='/abc/ ', expect=["yes", "no"])
    yield test, c(text='ill ', expect=[])

def test_CommandBar_common_prefix():
    word_list = [
        "test_ab",
        "test_ba",
        "test_bab",
        "text_xyz",
    ]
    bar = CommandTester()

    @gentest
    def test(word, expect, complete=""):
        delim = lambda:"/"
        overlap = len(word) - 2 if len(word) > 2 else 0
        words = [CompleteWord(w, delim, overlap)
                 for w in word_list if w.startswith(word)]
        prefix = bar.common_prefix(words)
        eq_(prefix, expect)
        if complete is not None:
            eq_(prefix.complete(), prefix + complete)
            eq_(prefix.overlap, overlap)

    yield test("x", "", None)
    yield test("", "te", None)
    yield test("t", "te")
    yield test("tes", "test_")
    yield test("test_a", "test_ab", "/")
    yield test("test_b", "test_ba")
    yield test("tex", "text_xyz", "/")

def test_CommandBar_auto_complete():
    @command(arg_parser=CommandParser(
        Choice(('selection', True), ('all', False), ('self', None)),
        Choice(('forward', False), ('reverse xyz', True), name='reverse'),
        Regex('sort_regex', True),
    ))
    def cmd(editor, sender, args):
        raise NotImplementedError("should not get here")
    bar = CommandTester(cmd)

    @gentest
    def test(text, word, range, expect):
        eq_(bar.auto_complete(text, word, range), expect)

    yield test("c", "cmd", (1, 0), ("cmd ", (0, 1), (1, 3)))
    yield test("cm", "cmd", (2, 0), ("cmd ", (0, 2), (2, 2)))
    yield test("cmd", "cmd", (3, 0), ("cmd ", (0, 3), (3, 1)))
    yield test("cmxyz", "cmd", (2, 3), ("cmd ", (0, 5), (2, 2)))
    yield test("cmd sel", "select", (7, 0), ("select ", (4, 3), (7, 4)))

    yield test("c sel", "cmd", (1, 0), ("cmd", (0, 1), (1, 2)))

    word = CompleteWord("dir", lambda:"/")
    yield test("d", word, (1, 0), ("dir/", (0, 1), (1, 3)))
    yield test("d/file.txt", word, (1, 0), ("dir", (0, 1), (1, 2)))

    word = CompleteWord("Dir", lambda:"/", overlap=1)
    yield test("d", word, (1, 0), ("Dir/", (0, 1), (1, 3)))
    yield test("d/file.txt", word, (1, 0), ("Dir", (0, 1), (1, 2)))

    word = CompleteWord("DIR", lambda:"/", overlap=2)
    yield test("di", word, (2, 0), ("DIR/", (0, 2), (2, 2)))
    yield test("di/file.txt", word, (2, 0), ("DIR", (0, 2), (2, 1)))

def test_CommandBar_get_history():
    def test(nav):
        with tempdir() as tmp:
            history = mod.CommandHistory(tmp)
            for item in reversed("abc"):
                history.append(item)
            window = type("FakeWindow", (object,), {})()
            commander = CommandManager(history)
            bar = mod.CommandBar(window, commander)

            for input, direction, history in nav:
                dirchar = "v" if direction else "A"
                print("{}({!r}, {!r})".format(dirchar, input, history))
                eq_(bar.get_history(input, forward=direction), history)

    A = lambda input, history: (input, False, history) # moveUp
    v = lambda input, history: (input, True, history)  # moveDown

    yield test, [
        A("", "a"),
        v("a", ""),
        v("", None),
        v("", None),
    ]

    yield test, [
        A("!", "a"),
        A("a", "b"),
        A("by", "c"),
        A("c", None),
        A("c", None),
        v("c", "by"),
        v("bz", "a"),
        A("a", "bz"),
        v("bz", "a"),
        v("a", "!"),
        v("!", None),
        v("!", None),
    ]

    yield test, [
        A("", "a"),
        A("x", "b"),
        v("b", "x"),
        v("a", ""),
        A("", "a"),
    ]

    yield test, [
        A("x", "a"),
        v("a", "x"),
        A("x", "a"),
        v("a", "x"),
        A("x", "a"),
    ]

    yield test, [
        A("-", "a"),
        A("ax", "b"),
        v("b", "ax"),
        A("ax", "b"),
        v("b", "ax"),
        A("ax", "b"),
        v("b", "ax"),
        v("ax", "-"),
    ]

def test_CommandBar_get_history_concurrently():
    with tempdir() as tmp:
        history = mod.CommandHistory(tmp)
        for item in reversed("abc"):
            history.append(item)
        window = type("FakeWindow", (object,), {})()
        commander = CommandManager(history)
        bar1 = mod.CommandBar(window, commander)
        bar2 = mod.CommandBar(window, commander)
        bar3 = mod.CommandBar(window, commander)
        bar4 = mod.CommandBar(window, commander)

        eq_(bar1.get_history("x"), "a")

        eq_(bar2.get_history(""), "a")
        eq_(bar2.get_history("y"), "b")

        eq_(bar3.get_history(""), "a")
        eq_(bar3.get_history("a"), "b")
        eq_(bar3.get_history("z"), "c") # <-- "z" will move to 0 (with "b")

        history.append("b")

        # current index "a", "x" in new command buffer
        eq_(bar1.get_history("a"), "c")
        eq_(bar1.get_history("c"), None)
        eq_(bar1.get_history("c", True), "a")
        eq_(bar1.get_history("a", True), "b")
        eq_(bar1.get_history("b", True), "x")
        eq_(bar1.get_history("x", True), None)

        # current index "b", "y" at 0
        eq_(bar2.get_history("B"), "y") # <-- "B" now at 0
        eq_(bar2.get_history("y"), "c")
        eq_(bar2.get_history("c"), None)
        eq_(bar2.get_history("c", True), "y")
        eq_(bar2.get_history("y", True), "B")
        eq_(bar2.get_history("B", True), "")
        eq_(bar2.get_history("", True), None)

        # current index "c", "z" at 1
        eq_(bar3.get_history("c"), None)
        eq_(bar3.get_history("C", True), "a")
        eq_(bar3.get_history("a"), "C")
        eq_(bar3.get_history("C", True), "a")
        eq_(bar3.get_history("a", True), "z")
        eq_(bar3.get_history("z", True), "") # <-- "z" moved to 0
        eq_(bar3.get_history("", True), None)

        eq_(bar4.get_history("A", True), None)
        eq_(bar4.get_history("A"), "b")
        eq_(bar4.get_history("b"), "a")
        eq_(bar4.get_history("a"), "c")
        eq_(bar4.get_history("c"), None)
        eq_(bar4.get_history("c", True), "a")
        eq_(bar4.get_history("a", True), "b")
        eq_(bar4.get_history("b", True), "A")
        eq_(bar4.get_history("A", True), None)

def test_CommandBar_history_reset_on_execute():
    from editxt.editor import Editor
    from editxt.textcommand import CommandHistory, CommandManager
    with tempdir() as tmp:
        m = Mocker()
        window = m.mock()
        history = CommandHistory(tmp)
        commander = CommandManager(history)
        bar = mod.CommandBar(window, commander)
        args = ["cmd"]
        editor = m.mock(Editor)
        (window.current_editor << editor).count(2)
        @command
        def cmd(editor, sender, args):
            pass
        commander.add_command(cmd, None, None)
        with m:
            bar.get_history("cmd")
            bar.execute("cmd")
            eq_(bar.history_view, None)
            eq_(list(history), ["cmd"])

def test_CommandBar_message():
    from editxt.editor import Editor
    def test(c):
        m = Mocker()
        window = m.mock()
        commander = m.mock(CommandManager)
        sys_exc_info = m.replace(mod.sys, "exc_info")
        format_exc = m.replace(mod.traceback, "format_exception")
        bar = mod.CommandBar(window, commander)
        editor = window.current_editor >> m.mock(Editor)
        kw = {}
        if c.exc_info is not None:
            kw["exc_info"] = c.exc_info
            exc_info = sys_exc_info() >> ("<type>", "<exc>", "<tb>")
            format_exc(*exc_info) >> ["Traceback", "...", "Error!"]
        editor.message(c.msg, msg_type=const.ERROR)
        with m:
            bar.message(c.text, **kw)
    c = TestConfig(text="command error", exc_info=None)
    yield test, c(msg="command error")
    yield test, c(msg="command error\n\nTraceback...Error!", exc_info=True)

def test_CommandBar_handle_link():
    from editxt.editor import Editor
    @gentest
    def test(link, expect, config="", goto=None):
        with test_app("project*") as app:
            m = Mocker()
            command = app.windows[0].command
            goto_line = m.replace(Editor, "goto_line")
            if goto is not None:
                goto_line(goto)
            with m:
                eq_(command.handle_link(link), expect)
            if config:
                eq_(test_app(app).state, "window project " + config)
    yield test("http://google.com", False)
    yield test("xt://open/file.txt", True, "editor[file.txt 0]*")
    yield test("xt://open//file.txt", True, "editor[/file.txt 0]*")
    yield test("xt://open//file.txt?goto=3", True, "editor[/file.txt 0]*", goto=3)
    yield test("xt://open//file.txt?goto=3.10.2", True, "editor[/file.txt 0]*", goto=(3, 10, 2))
    yield test("xt://preferences", True, "editor[/.profile/config.yaml 0]*")

def test_CommandBar_reset():
    with tempdir() as tmp:
        window = type("Window", (object,), {})()
        history = mod.CommandHistory(tmp)
        commander = mod.CommandManager(history)
        bar = mod.CommandBar(window, commander)
        eq_(bar.get_history(""), None)
        assert bar.history_view is not None
        assert bar.history_view in history.views
        bar.reset()
        eq_(bar.history_view, None)
        assert bar.history_view not in history.views

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextControllerCommand tests

def test_CommandManager_init():
    m = Mocker()
    menu = m.mock(ak.NSMenu)
    with m:
        ctl = CommandManager("<history>")
        eq_(ctl.history, "<history>")
        eq_(ctl.commands, {})
        eq_(ctl.commands_by_path, {})
        eq_(ctl.input_handlers, {})
        eq_(ctl.editems, {})

def test_CommandManager_lookup():
    def test(c):
        m = Mocker()
        menu = m.mock(ak.NSMenu)
        ctl = CommandManager("<history>")
        for command in c.commands:
            ctl.add_command(command, None, menu)
        eq_(ctl.lookup(c.lookup), c.result)
    @command(name="cmd cm")
    def cmd(*args):
        pass
    @command(name="cmd")
    def cm2(*args):
        pass
    @command
    def no(*args):
        pass
    c = TestConfig(commands=[], lookup='cmd', result=None)
    yield test, c
    yield test, c(commands=[no])
    yield test, c(commands=[cmd], result=cmd)
    yield test, c(commands=[cmd, cm2], result=cm2)
    yield test, c(commands=[cmd, cm2], lookup='cm', result=cmd)

def test_CommandManager_lookup_full_command():
    def test(c):
        m = Mocker()
        menu = m.mock(ak.NSMenu)
        ctl = CommandManager("<history>")
        for command in c.commands:
            ctl.add_command(command, None, menu)
            menu.insertItem_atIndex_(ANY, ANY)
        eq_(ctl.lookup_full_command(c.lookup), c.result)
    @command(name="cm")
    def cmd(*args):
        pass
    @command(
        arg_parser=CommandParser(Int("value")),
        lookup_with_arg_parser=True)
    def num(*args):
        pass
    c = TestConfig(commands=[], lookup='cmd', result=(None, None))
    yield test, c
    yield test, c(commands=[cmd])
    yield test, c(commands=[num])
    yield test, c(commands=[num], lookup='123', result=(num, Options(value=123)))

def test_CommandManager_load_commands():
    def test(c):
        m = Mocker()
        menu = m.mock(ak.NSMenu)
        ctl = CommandManager("<history>")
        handlers = ctl.input_handlers = m.mock(dict)
        add = m.method(ctl.add_command)
        mod = m.mock(dict)
        m.method(ctl.iter_command_modules)() >> [("<path>", mod)]
        cmds = []; mod.get("text_menu_commands", []) >> cmds
        for i in range(c.commands):
            cmd = "<command %s>" % i
            add(cmd, "<path>", menu)
            cmds.append(cmd)
        hnds = mod.get("input_handlers", {}) >> {}
        for i in range(c.handlers):
            hnds["handle%s" % i] = "<handle %s>" % i
        handlers.update(hnds)
        with m:
            ctl.load_commands(menu)
    c = TestConfig()
    yield test, c(commands=0, handlers=0)
    yield test, c(commands=2, handlers=2)

def test_CommandManager_add_command():
    def test(c):
        m = Mocker()
        menu = m.mock(ak.NSMenu)
        mi_class = m.replace(ak, 'NSMenuItem')
        ctl = CommandManager("<history>")
        handlers = m.replace(ctl, 'input_handlers')
        validate = m.method(ctl.validate_hotkey)
        cmd = m.mock()
        cmd.names >> []
        cmd.lookup_with_arg_parser >> False
        cmd.config >> None
        tag = cmd._CommandManager__tag = next(ctl.tagger) + 1
        validate(cmd.hotkey >> "<hotkey>") >> ("<hotkey>", "<keymask>")
        mi = mi_class.alloc() >> m.mock(ak.NSMenuItem)
        (cmd.title << "<title>").count(2)
        mi.initWithTitle_action_keyEquivalent_(
            '<title>', "doCommand:" ,"<hotkey>") >> mi
        mi.setKeyEquivalentModifierMask_("<keymask>")
        mi.setTag_(tag)
        menu.insertItem_atIndex_(mi, tag)
        with m:
            ctl.add_command(cmd, None, menu)
            assert ctl.commands[tag] is cmd, (ctl.commands[tag], cmd)
    c = TestConfig()
    yield test, c
    #yield test, c

def test_CommandManager_validate_hotkey():
    tc = CommandManager("<history>")
    eq_(tc.validate_hotkey(None), ("", 0))
    eq_(tc.validate_hotkey(("a", 1)), ("a", 1))
    assert_raises(AssertionError, tc.validate_hotkey, ("a", "b", "c"))

def test_CommandManager_is_command_enabled():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        mi = m.mock(ak.NSMenuItem)
        tv = m.mock(ak.NSTextView)
        tc = m.mock()
        tcc = CommandManager("<history>")
        cmds = m.replace(tcc, 'commands')
        cmds.get(mi.tag() >> 42) >> (tc if c.has_command else None)
        if c.has_command:
            if c.error:
                expect(tc.is_enabled(tv, mi)).throw(Exception)
                lg.error("%s.is_enabled failed", ANY, exc_info=True)
            else:
                tc.is_enabled(tv, mi) >> c.enabled
        with m:
            result = tcc.is_command_enabled(tv, mi)
            eq_(result, c.enabled)
    c = TestConfig(has_command=True, enabled=False)
    yield test, c(has_command=False)
    yield test, c(error=True)
    yield test, c(error=False)
    yield test, c(error=False, enabled=True)

def test_CommandManager_do_command():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        mi = m.mock(ak.NSMenuItem)
        tv = m.mock(ak.NSTextView)
        tc = m.mock()
        tcc = CommandManager("<history>")
        cmds = m.replace(tcc, 'commands')
        cmds.get(mi.tag() >> 42) >> (tc if c.has_command else None)
        if c.has_command:
            tc(tv, mi, None)
            if c.error:
                m.throw(Exception)
                lg.error("%s.execute failed", ANY, exc_info=True)
        with m:
            tcc.do_command(tv, mi)
    c = TestConfig(has_command=True)
    yield test, c(has_command=False)
    yield test, c(error=True)
    yield test, c(error=False)

def test_CommandManager_do_command_by_selector():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        tv = m.mock(ak.NSTextView)
        tcc = CommandManager("<history>")
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
            result = tcc.do_command_by_selector(tv, sel)
            eq_(result, c.result)
    c = TestConfig(has_selector=True, result=False)
    yield test, c(has_selector=False)
    yield test, c(error=True)
    yield test, c(error=False, result=True)
