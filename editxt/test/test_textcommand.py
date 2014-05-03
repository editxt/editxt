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
from editxt.test.util import TestConfig, tempdir

import editxt.constants as const
import editxt.textcommand as mod
from editxt.command.parser import ArgumentError, CommandParser, Int, Options
from editxt.commands import command
from editxt.test.test_commands import CommandTester
from editxt.textcommand import TextCommandController

log = logging.getLogger(__name__)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CommandBar tests

def test_CommandBar_window():
    window = type('Window', (object,), {})()
    text_commander = type('TextCommandController', (object,), {})()
    cmd = mod.CommandBar(window, text_commander)
    eq_(cmd.window, window)
    eq_(cmd.text_commander, text_commander)
    # NOTE the following depends on CPython weakref behavior
    del window, text_commander
    eq_(cmd.window, None)
    eq_(cmd.text_commander, None)

def test_CommandBar_execute():
    from editxt.editor import Editor
    from editxt.textcommand import TextCommandController
    def test(c):
        m = Mocker()
        window = m.mock()
        beep = m.replace(ak, 'NSBeep')
        commander = m.mock(TextCommandController)
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
                editor.text_view >> '<view>'
                res = command('<view>', bar, '<args>')
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
    yield test, c(text='cmd x y z', argstr='x y z', lookup='first')
    yield test, c(text='cmd x y z', argstr='x y z', lookup='first', msg="msg")
    yield test, c(text=' cmd x y z', argstr='x y z', lookup='first')
    yield test, c(text='cmd  x y  z', argstr=' x y  z', lookup='first')
    yield test, c(text='cmd x ', argstr='x ', lookup='first', args=Exception(),
                  msg='argument parse error: x ', exc_info=True)
    yield test, c(text='123 456', lookup='full')
    yield test, c(text='123 456', lookup='full', msg="message for you, sir!")
    yield test, c(text='123 456', lookup='full', current=False)
    yield test, c(text='cmd', argstr='', lookup='first', args=None,
                  msg='invalid command arguments: ')
    yield test, c(text='123 456', lookup='full', args=None,
                  msg='unknown command: 123 456')
    yield test, c(text='123 456', lookup='full', error=True)

def test_CommandBar_get_placeholder():
    from editxt.command.parser import CommandParser, Choice, Regex, VarArgs
    def test(c):
        m = Mocker()
        beep = m.replace(ak, 'NSBeep')
        @command(arg_parser=CommandParser(
            Choice(('selection', True), ('all', False)),
            Choice(('no', False), ('yes', True)),
            Regex('sort_regex', True),
        ))
        def cmd(textview, sender, args):
            raise NotImplementedError("should not get here")
        @command(arg_parser=CommandParser(
            Regex('search_pattern', replace=c.replace),
            Choice(('yep', False), ('yes', True)),
            VarArgs("args", placeholder="..."),
        ), lookup_with_arg_parser=True)
        def search(textview, sender, args):
            raise NotImplementedError("should not get here")
        bar = CommandTester(cmd, search)
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
    yield test, c(text='/', expect="/ yep ...")
    yield test, c(text='/x', expect="/ yep ...")
    yield test, c(text='/x ', expect="/ yep ...")
    yield test, c(text='/x/ ', expect="yep ...")
    yield test, c(text='/x/  ', expect="...")
    yield test, c(text='/x/ y', expect="... ...")
    yield test, c(text='/x/ y ', expect="")
    yield test, c(text='/x/ a', expect="")
    c = c(replace=True)
    yield test, c(text='/', expect="// yep ...")
    yield test, c(text='/     ', expect="// yep ...")
    yield test, c(text='/x', expect="// yep ...")
    yield test, c(text='/x ', expect="// yep ...")
    yield test, c(text='/x/ ', expect="/ yep ...")
    yield test, c(text='/x/  ', expect="/ yep ...")
    yield test, c(text='/x//', expect=" yep ...")
    yield test, c(text='/x//i', expect=" yep ...")
    yield test, c(text='/x// ', expect="yep ...")
    yield test, c(text='/x// y', expect="... ...")
    yield test, c(text='/x// y ', expect="")
    yield test, c(text='/x// a', expect="")

def test_CommandBar_get_completions():
    from editxt.command.parser import CommandParser, Choice, Regex, VarArgs
    def test(c):
        m = Mocker()
        beep = m.replace(ak, 'NSBeep')
        @command(arg_parser=CommandParser(
            Choice(('selection', True), ('all', False)),
            Choice(('forward', False), ('reverse xyz', True), name='reverse'),
            Regex('sort_regex', True),
        ))
        def cmd(textview, sender, args):
            raise NotImplementedError("should not get here")
        @command(arg_parser=CommandParser(
            Regex('search_pattern'),
            Choice(('yes', True), ('no', False)),
        ), lookup_with_arg_parser=True)
        def search(textview, sender, args):
            raise NotImplementedError("should not get here")
        bar = CommandTester(cmd, search)
        with m:
            eq_(bar.get_completions(c.text), c.expect)
    c = TestConfig()
    yield test, c(text='x', expect=([], -1))
    yield test, c(text='', expect=(["cmd", "search"], 0))
    yield test, c(text='c', expect=(["cmd"], 0))
    yield test, c(text='cm', expect=(["cmd"], 0))
    yield test, c(text='cmd', expect=(["cmd"], 0))
    yield test, c(text='cmx', expect=([], -1))
    yield test, c(text='cmd ', expect=(["selection", "all"], 0))
    yield test, c(text='cmd s', expect=(["selection"], 0))
    yield test, c(text='cmd se', expect=(["selection"], 0))
    yield test, c(text='cmd selection', expect=(["selection"], 0))
    yield test, c(text='cmd sec', expect=(None, -1))
    yield test, c(text='cmd s ', expect=(["forward", "reverse"], 0))
    yield test, c(text='cmd s r', expect=(["reverse"], 0))
    yield test, c(text='cmd s x', expect=(["xyz"], 0))
    yield test, c(text='/', expect=([], -1))
    yield test, c(text='/ ', expect=([], -1))
    yield test, c(text='/a', expect=([], -1))
    yield test, c(text='/abc/ ', expect=(["yes", "no"], 0))

def test_CommandBar_get_history():
    def test(nav):
        with tempdir() as tmp:
            history = mod.CommandHistory(tmp)
            for item in reversed("abc"):
                history.append(item)
            window = type("FakeWindow", (object,), {})()
            commander = TextCommandController(history)
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
        commander = TextCommandController(history)
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
    from editxt.textcommand import CommandHistory, TextCommandController
    with tempdir() as tmp:
        m = Mocker()
        window = m.mock()
        history = CommandHistory(tmp)
        commander = TextCommandController(history)
        bar = mod.CommandBar(window, commander)
        args = ["cmd"]
        editor = window.current_editor >> m.mock(Editor)
        editor.text_view >> '<view>'
        @command
        def cmd(textview, sender, args):
            pass
        commander.add_command(cmd, None, None)
        with m:
            bar.get_history("cmd")
            bar.execute("cmd")
            eq_(bar.history_view, None)
            eq_(list(history), ["cmd"])

def test_CommandBar_message():
    from editxt.controls.commandview import CommandView
    from editxt.editor import Editor
    def test(c):
        m = Mocker()
        window = m.mock()
        commander = m.mock(TextCommandController)
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

def test_CommandBar_reset():
    with tempdir() as tmp:
        window = type("Window", (object,), {})()
        history = mod.CommandHistory(tmp)
        commander = mod.TextCommandController(history)
        bar = mod.CommandBar(window, commander)
        eq_(bar.get_history(""), None)
        assert bar.history_view is not None
        assert bar.history_view in history.views
        bar.reset()
        eq_(bar.history_view, None)
        assert bar.history_view not in history.views

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextControllerCommand tests

def test_TextCommandController_init():
    m = Mocker()
    menu = m.mock(ak.NSMenu)
    with m:
        ctl = TextCommandController("<history>")
        eq_(ctl.history, "<history>")
        eq_(ctl.commands, {})
        eq_(ctl.commands_by_path, {})
        eq_(ctl.input_handlers, {})
        eq_(ctl.editems, {})

def test_TextCommandController_lookup():
    def test(c):
        m = Mocker()
        menu = m.mock(ak.NSMenu)
        ctl = TextCommandController("<history>")
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

def test_TextCommandController_lookup_full_command():
    def test(c):
        m = Mocker()
        menu = m.mock(ak.NSMenu)
        ctl = TextCommandController("<history>")
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

def test_TextCommandController_load_commands():
    def test(c):
        m = Mocker()
        menu = m.mock(ak.NSMenu)
        ctl = TextCommandController("<history>")
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

def test_TextCommandController_add_command():
    def test(c):
        m = Mocker()
        menu = m.mock(ak.NSMenu)
        mi_class = m.replace(ak, 'NSMenuItem')
        ctl = TextCommandController("<history>")
        handlers = m.replace(ctl, 'input_handlers')
        validate = m.method(ctl.validate_hotkey)
        cmd = m.mock()
        cmd.names >> []
        cmd.lookup_with_arg_parser >> False
        tag = cmd._TextCommandController__tag = next(ctl.tagger) + 1
        validate(cmd.hotkey >> "<hotkey>") >> ("<hotkey>", "<keymask>")
        mi = mi_class.alloc() >> m.mock(ak.NSMenuItem)
        (cmd.title << "<title>").count(2)
        mi.initWithTitle_action_keyEquivalent_(
            '<title>', "performTextCommand:" ,"<hotkey>") >> mi
        mi.setKeyEquivalentModifierMask_("<keymask>")
        mi.setTag_(tag)
        menu.insertItem_atIndex_(mi, tag)
        with m:
            ctl.add_command(cmd, None, menu)
            assert ctl.commands[tag] is cmd, (ctl.commands[tag], cmd)
    c = TestConfig()
    yield test, c
    #yield test, c

def test_TextCommandController_validate_hotkey():
    tc = TextCommandController("<history>")
    eq_(tc.validate_hotkey(None), ("", 0))
    eq_(tc.validate_hotkey(("a", 1)), ("a", 1))
    assert_raises(AssertionError, tc.validate_hotkey, ("a", "b", "c"))

def test_TextCommandController_is_textview_command_enabled():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        mi = m.mock(ak.NSMenuItem)
        tv = m.mock(ak.NSTextView)
        tc = m.mock()
        tcc = TextCommandController("<history>")
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
        mi = m.mock(ak.NSMenuItem)
        tv = m.mock(ak.NSTextView)
        tc = m.mock()
        tcc = TextCommandController("<history>")
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
        tv = m.mock(ak.NSTextView)
        tcc = TextCommandController("<history>")
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
