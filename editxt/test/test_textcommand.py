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
from editxt.commandparser import ArgumentError, CommandParser, Int, Options
from editxt.commands import command
from editxt.textcommand import TextCommandController

log = logging.getLogger(__name__)


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
    @command(names="cmd cm")
    def cmd(*args):
        pass
    @command(names="cmd")
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
        menu = m.mock(NSMenu)
        ctl = TextCommandController(menu)
        for command in c.commands:
            ctl.add_command(command, None)
            menu.insertItem_atIndex_(ANY, ANY)
        eq_(ctl.lookup_full_command(c.lookup), c.result)
    @command(names="cm")
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
        cmd.lookup_with_arg_parser >> False
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
