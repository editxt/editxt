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
import functools
from contextlib import contextmanager

import AppKit as ak
import Foundation as fn
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import (TestConfig, untested, check_app_state, replattr,
    tempdir)

import editxt
import editxt.command.base as mod
from editxt.controls.textview import TextView
from editxt.command.base import CommandController
from editxt.command.base import SheetController, PanelController
from editxt.command.parser import ArgumentError, CommandParser, Int, Options
from editxt.textcommand import CommandHistory
from editxt.util import KVOProxy

log = logging.getLogger(__name__)


@mod.command(name='abc', title='Title', hotkey=(',', 0),
    is_enabled=lambda *a:False,
    arg_parser=CommandParser(Int("value")), lookup_with_arg_parser=True)
def dummy_command(textview, sender, args):
    assert False, "this command is not meant to be executed"

def setup(controller_class, nib_name="TestController"):
    def setup_controller(func):
        @functools.wraps(func)
        def wrapper():
            assert not hasattr(controller_class, 'COMMAND')
            assert not hasattr(controller_class, 'NIB_NAME')
            controller_class.COMMAND = dummy_command
            controller_class.NIB_NAME = nib_name
            try:
                func()
            finally:
                del controller_class.COMMAND
                del controller_class.NIB_NAME
        return wrapper
    return setup_controller

@contextmanager
def replace_history():
    with tempdir() as tmp:
        history = CommandHistory(tmp)
        with replattr(editxt.app.text_commander, "history", history):
            yield history

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# command decorator tests

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
    cmd = dummy_command
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


def test_load_options():
    def test(argstr=None, value=None):
        with replace_history() as history:
            if argstr:
                history.append(argstr)
            options = mod.load_options(dummy_command, history)
            eq_(options, Options(value=value))
    yield test, "abc 123", 123
    yield test, "345", 345
    yield test, "xyz"
    yield test,


def test_save_options():
    def test(options, hist, command=dummy_command):
        with replace_history() as history:
            mod.save_options(options, command, history)
            eq_(next(iter(history), None), hist)

    yield test, Options(value=123), "123"
    yield test, Options(value=None), "abc"

    @mod.command(arg_parser=CommandParser(Int("value", default=42)))
    def xyz(textview, sender, options): pass

    yield test, Options(value=345), "xyz 345", xyz
    yield test, Options(value=42), "xyz", xyz

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CommandController tests

class OtherController(PanelController): pass

@setup(PanelController)
def test_PanelController_shared_controller():
    cx = PanelController.shared_controller()
    c1 = OtherController.shared_controller()
    assert isinstance(c1, OtherController), c1
    c2 = OtherController.shared_controller()
    assert c1 is c2, (c1, c2)

@setup(CommandController)
def test_CommandController_options():
    with replace_history() as history:
        ctl = FakeController()
        eq_(ctl.history, history)
        assert ctl.options is ctl.gui.options()
        obj = object()
        ctl.gui.setOptions_(obj)
        eq_(ctl.options, obj)

class FakeController(CommandController):
    COMMAND = dummy_command
    NIB_NAME = "FakeController"

def test_CommandController_load_options():
    def test(hist, expect):
        with replace_history() as history:
            ctl = FakeController()
            eq_(ctl.history, history)
            if hist:
                history.append(hist)
            ctl.load_options()
            eq_(ctl.options.__dict__["_target"], expect)
    yield test, None, Options(value=None)
    yield test, "123", Options(value=123)

def test_CommandController_save_options():
    with replace_history() as history:
        eq_(next(iter(history), None), None)
        slc = FakeController()
        slc.options = Options(value=42)
        slc.save_options()
        eq_(next(iter(history)), "42")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SheetController tests

@setup(SheetController)
def test_SheetController_begin_sheet():
    from editxt.controls.alert import Caller
    m = Mocker()
    tv = m.mock(TextView)
    slc = SheetController(tv)
    def cb(callback):
        return callback.__name__ == "sheet_did_end" and callback.__self__ is slc
    clr_class = m.replace(mod, "Caller")
    clr = clr_class.alloc().init(MATCH(cb)) >> m.mock(Caller)
    win = tv.window() >> m.mock(ak.NSWindow)
    pnl = m.method(slc.gui.window)() >> m.mock(ak.NSPanel)
    nsapp = m.replace(ak, 'NSApp', spec=False)
    nsapp.beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(
        pnl, win, clr, "alertDidEnd:returnCode:contextInfo:", 0)
    with m:
        slc.begin_sheet(None)
