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
import functools

from AppKit import *
from Foundation import *
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import TestConfig, untested, check_app_state, replattr

import editxt.commandbase as mod
from editxt.controls.textview import TextView
from editxt.commandbase import BaseCommandController, Options
from editxt.commandbase import SheetController, PanelController
from editxt.util import KVOProxy

log = logging.getLogger(__name__)

def setup(controller_class, nib_name="TestController"):
    def setup_controller(func):
        @functools.wraps(func)
        def wrapper():
            controller_class.NIB_NAME = nib_name
            try:
                func()
            finally:
                del controller_class.NIB_NAME
        return wrapper
    return setup_controller
        
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

@setup(BaseCommandController)
def test_BaseCommandController_options():
    class FakeOptions(Options): pass
    with replattr(BaseCommandController, "OPTIONS_FACTORY", FakeOptions):
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
    OPTIONS_FACTORY = lambda s:Options(key1="<default x>", key2="<default y>")

def test_BaseCommandController_load_options():
    def test(c):
        m = Mocker()
        ud = m.replace(mod, 'NSUserDefaults')
        sd = ud.standardUserDefaults() >> m.mock(NSUserDefaults)
        ctl = FakeController.create()
        if c.present:
            values = {"key1": "<val x>", "key2": "<val y>"}
            state = sd.dictionaryForKey_(ctl.OPTIONS_KEY) >> values
        else:
            values = {"key1": "<default x>", "key2": "<default y>"}
            state = sd.dictionaryForKey_(ctl.OPTIONS_KEY) >> None
        with m:
            ctl.load_options()
            opts = ctl.opts
            for key, value in values.iteritems():
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
    opts.other_option = "should not be saved"
    data = {}
    for key, value in {"key1": "<default x>", "key2": "<default y>"}.items():
        data[key] = value
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
