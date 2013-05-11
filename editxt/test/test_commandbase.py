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
import os
from contextlib import closing
from tempfile import gettempdir

from AppKit import *
from Foundation import *
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import TestConfig, untested, check_app_state, replattr

import editxt.commandbase as mod
import editxt.constants as const
from editxt.controls.textview import TextView
from editxt.commandbase import BaseCommandController, Options
from editxt.commandbase import SheetController, PanelController
from editxt.util import KVOProxy

log = logging.getLogger(__name__)

def setup(controller_class, nib_name="TestController"):
    def setup_controller(func):
        def wrapper():
            controller_class.NIB_NAME = nib_name
            controller_class.OPTIONS_DEFAULTS = {}
            try:
                func()
            finally:
                del controller_class.OPTIONS_DEFAULTS
                del controller_class.NIB_NAME
        wrapper.__name__ = func.__name__
        return wrapper
    return setup_controller
        
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CommandBar tests

def test_CommandBar_editor():
    editor = type('Editor', (object,), {})()
    cmd = mod.CommandBar(editor)
    eq_(cmd.editor, editor)
    # NOTE the following depends on CPython weakref behavior
    del editor
    eq_(cmd.editor, None)

def test_CommandBar_execute():
    from editxt.document import TextDocumentView
    from editxt.textcommand import TextCommandController
    def test(c):
        m = Mocker()
        editor = m.mock()
        beep = m.replace(mod, 'NSBeep')
        commander = m.replace(mod.app, 'text_commander', spec=TextCommandController)
        bar = mod.CommandBar(editor)
        args = c.text.split()
        if args and not c.current:
            editor.current_view >> None
            beep()
        elif args:
            view = editor.current_view >> m.mock(TextDocumentView)
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
                beep()
            else:
                view.text_view >> '<view>'
                res = expect(command('<view>', bar, '<args>'))
                if c.error:
                    res.throw(Exception('bang!'))
                    beep()
        with m:
            bar.execute(c.text)
    c = TestConfig(args='<args>', error=False, current=True)
    yield test, c(text='')
    yield test, c(text='cmd x y z', argstr='x y z', lookup='first')
    yield test, c(text='cmd  x y  z', argstr=' x y  z', lookup='first')
    yield test, c(text='cmd x ', argstr='x ', lookup='first', args=Exception())
    yield test, c(text='123 456', lookup='full')
    yield test, c(text='123 456', lookup='full', current=False)
    yield test, c(text='cmd', argstr='', lookup='first', args=None)
    yield test, c(text='123 456', lookup='full', args=None)
    yield test, c(text='123 456', lookup='full', error=True)

def test_get_completion_hints():
    from editxt.commandparser import CommandParser, Bool, Regex, VarArgs
    from editxt.document import TextDocumentView
    from editxt.textcommand import TextCommandController, command
    def test(c):
        m = Mocker()
        editor = m.mock()
        beep = m.replace(mod, 'NSBeep')
        commander = m.replace(mod.app, 'text_commander', spec=TextCommandController)
        bar = mod.CommandBar(editor)
        args = c.text.split()
        index = len(c.text) if c.index is None else c.index
        if args:
            @command(arg_parser=CommandParser(
                Bool('selection sel s', 'all a', True),
                Regex('sort_regex', True),
            ))
            def cmd(textview, sender, args):
                raise NotImplementedError("should not get here")
            commander.lookup(args[0]) >> (cmd if c.match == "simple" else None)
            if c.match == "parse":
                @command(arg_parser=CommandParser(
                    Regex('search_pattern'),
                    VarArgs("args"),
                ))
                def search(textview, sender, args):
                    raise NotImplementedError("should not get here")
                commander.lookup_full_command(c.text) >> (search, c.args)
            elif not c.match:
                commander.lookup_full_command(c.text) >> (None, None)
                commander.get_completions(c.text, index) >> "<commands>"
        with m:
            eq_(bar.get_completion_hints(c.text, index), c.expect)
    c = TestConfig(index=None, match="simple", args="<args>")
    yield test, c(text='', expect=("", []))
    yield test, c(text='cmd', expect=(" selection sort_regex", []))
    yield test, c(text='cmd ', expect=("selection sort_regex", []))
    yield test, c(text='cmd s', expect=(" sort_regex", []))
    yield test, c(text='cmd se', expect=("", []))
    yield test, c(text='cmd sel', expect=(" sort_regex", []))
    yield test, c(text='cmd sel ', expect=("sort_regex", []))
    yield test, c(text='cmd sel /', expect=("", []))
    yield test, c(text='cmd a', expect=(" sort_regex", []))
    yield test, c(text='cmd a ', expect=("sort_regex", []))
    yield test, c(text='cmd all', expect=(" sort_regex", []))
    yield test, c(text='cmd all ', expect=("sort_regex", []))
    yield test, c(text='cmd x', expect=("", []))
    yield test, c(text='cmd x ', expect=("", []))
    yield test, c(text='cmd  ', expect=("sort_regex", []))
    yield test, c(text='cmd  /', expect=("", []))
    yield test, c(text='cmd   ', expect=("", []))
    yield test, c(text='/', expect=("", []), match="parse")
    yield test, c(text='/x', expect=("", []), match="parse")
    yield test, c(text='/x ', expect=("", []), match="parse")
    yield test, c(text='/x/ ', expect=("...", []), match="parse")
    yield test, c(text='/x/  ', expect=("", []), match="parse")
    yield test, c(text='/x/ a', expect=("", []), match="parse")
    yield test, c(text='cmd', expect=("", "<commands>"), match=None)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# BaseCommandController tests

@setup(BaseCommandController)
def test_BaseCommandController_create():
    tv = None
    c1 = BaseCommandController.create()
    assert isinstance(c1, BaseCommandController)
    c2 = BaseCommandController.create()
    assert isinstance(c2, BaseCommandController)
    assert c1 is not c2

class OtherController(BaseCommandController): pass

@setup(BaseCommandController)
def test_BaseCommandController_shared_controller():
    cx = BaseCommandController.shared_controller()
    c1 = OtherController.shared_controller()
    assert isinstance(c1, OtherController), c1
    c2 = OtherController.shared_controller()
    assert c1 is c2, (c1, c2)

class FakeOptions(object):
    def __init__(self):
        self.load_count = 0
    def load(self):
        self.load_count += 1

@setup(BaseCommandController)
def test_BaseCommandController_options():
    with replattr(BaseCommandController, "OPTIONS_CLASS", FakeOptions):
        ctl = BaseCommandController.create()
        #assert isinstance(ctl.opts, FakeOptions), ctl.opts
        eq_(type(ctl.opts).__name__, "FakeOptions_KVOProxy")
        assert ctl.opts is ctl.options()
        obj = object()
        ctl.setOptions_(obj)
        eq_(ctl.options(), obj)

class FakeController(BaseCommandController):
    NIB_NAME = "FakeController"
    OPTIONS_KEY = "FakeController_options"
    OPTIONS_CLASS = Options
    OPTIONS_DEFAULTS = dict(
        key1="<value1>",
        key2="<value2>",
    )

def test_BaseCommandController_load_options():
    def test(c):
        m = Mocker()
        ud = m.replace(mod, 'NSUserDefaults')
        sd = ud.standardUserDefaults() >> m.mock(NSUserDefaults)
        ctl = FakeController.create()
        state = sd.dictionaryForKey_(ctl.OPTIONS_KEY) >> (
            ctl.OPTIONS_DEFAULTS if c.present else None)
        with m:
            ctl.load_options()
            opts = ctl.opts
            for key, value in ctl.OPTIONS_DEFAULTS.iteritems():
                eq_(getattr(opts, key), value)
    c = TestConfig()
    yield test, c(present=False)
    yield test, c(present=True)

def test_BaseCommandController_save_options():
    m = Mocker()
    ud = m.replace(mod, 'NSUserDefaults')
    sd = ud.standardUserDefaults() >> m.mock(NSUserDefaults)
    ctl = FakeController.create()
    opts = ctl.opts
    data = {}
    for key, value in ctl.OPTIONS_DEFAULTS.iteritems():
        data[key] = value
        setattr(opts, key, value)
    sd.setObject_forKey_(data, ctl.OPTIONS_KEY)
    with m:
        ctl.save_options()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SheetController tests

@setup(SheetController)
def test_SheetController_create_with_textview():
    tv = None
    c1 = SheetController.create_with_textview(tv)
    assert isinstance(c1, SheetController)
    c2 = SheetController.create_with_textview(tv)
    assert isinstance(c2, SheetController)
    assert c1 is not c2

@setup(SheetController)
def test_SheetController_begin_sheet():
    from editxt.controls.alert import Caller
    m = Mocker()
    tv = m.mock(TextView)
    slc = SheetController.create_with_textview(tv)
    def cb(callback):
        return callback.__name__ == "sheet_did_end" and callback.self is slc
    clr_class = m.replace(mod, "Caller")
    clr = clr_class.alloc().init(MATCH(cb)) >> m.mock(Caller)
    win = tv.window() >> m.mock(NSWindow)
    pnl = m.method(slc.window)() >> m.mock(NSPanel)
    nsapp = m.replace(mod, 'NSApp', spec=False)
    nsapp.beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(
        pnl, win, clr, "alertDidEnd:returnCode:contextInfo:", 0)
    with m:
        slc.begin_sheet(None)
