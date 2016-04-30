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

import AppKit as ak
import Foundation as fn
from mocker import Mocker, MockerTestCase, expect, ANY
from nose.tools import *
from editxt.test.util import TestConfig, untested

import editxt.constants as const
import editxt.platform.mac.views.textview as mod
from editxt.editor import Editor
from editxt.platform.mac.views import TextView

log = logging.getLogger(__name__)

# log.debug("""TODO
#     implement Editor.pasteboard_data()
# """)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def test_TextView_performFindPanelAction_():
    from editxt.command.find import FindController
    m = Mocker()
    tv = TextView.alloc().init()
    app = tv.app = m.mock("editxt.application.Application")
    fc = m.replace(mod, "FindController")
    sender = m.mock()
    (fc.shared_controller(app) >> m.mock(FindController)).perform_action(sender)
    with m:
        tv.performFindPanelAction_(sender)

def test_TextView_doCommand_():
    from editxt.textcommand import CommandManager
    m = Mocker()
    tv = TextView.alloc().init()
    app = tv.app = m.mock()
    editor = tv.editor = m.mock(Editor)
    tc = app.text_commander >> m.mock(CommandManager)
    sender = m.mock()
    tc.do_command(editor, sender)
    with m:
        tv.doCommand_(sender)

def test_TextView_doCommandBySelector_():
    from editxt.textcommand import CommandManager
    m = Mocker()
    tv = TextView.alloc().init()
    app = tv.app = m.mock()
    editor = tv.editor = m.mock(Editor)
    tc = app.text_commander >> m.mock(CommandManager)
    selector = m.mock()
    editor.do_command(selector) >> False
    tc.do_command_by_selector(editor, selector) >> True # omit super call
    with m:
        tv.doCommandBySelector_(selector)

def test_TextView_validateUserInterfaceItem_():
    from editxt.command.find import FindController
    from editxt.textcommand import CommandManager
    def test(c):
        m = Mocker()
        fc = m.replace(mod, "FindController")
        tv = TextView.alloc().init()
        app = tv.app = m.mock()
        editor = tv.editor = m.mock(Editor)
        item = m.mock(ak.NSMenuItem)
        expectation = (item.action() << c.action)
        if c.action == "performFindPanelAction:":
            tag = item.tag() >> 42
            (fc.shared_controller(app) >> m.mock(FindController)). \
                validate_action(tag) >> True
        elif c.action == "doCommand:":
            expectation.count(2)
            tc = app.text_commander >> m.mock(CommandManager)
            tc.is_command_enabled(editor, item) >> True
        else:
            raise NotImplementedError # left untested because I don't know how to mock a super call
        with m:
            assert tv.validateUserInterfaceItem_(item)
    c = TestConfig()
    yield test, c(action="performFindPanelAction:")
    yield test, c(action="doCommand:")

def test_TextView_setFrameSize():
    def test(c):
        m = Mocker()
        tv = TextView.alloc().initWithFrame_(fn.NSMakeRect(0, 0, 100, 100)) # x, y, w, h
        tc = m.method(tv.textContainer)() >> (m.mock(ak.NSTextContainer) if c.setup else None)
        lm = m.method(tv.layoutManager)() >> (m.mock(ak.NSLayoutManager) if c.setup else None)
        sv = m.method(tv.enclosingScrollView)() >> (m.mock(ak.NSScrollView) if c.setup else None)
        height = 100
        if c.setup:
            lm.usedRectForTextContainer_(tc) >> fn.NSMakeRect(0, 0, 100, c.content_height)
            sv.contentSize() >> fn.NSMakeSize(100, 100) # w, h
            if c.content_height + 75 > 100:
                height = c.content_height + 75
        with m:
            tv.setFrameSize_(fn.NSMakeSize(100, height))
            eq_(tv.frameSize(), fn.NSMakeSize(100, c.final_height))
    c = TestConfig(setup=True, content_height=100, final_height=175)
    yield test, c
    yield test, c(content_height=10, final_height=100)
    yield test, c(setup=False, final_height=100)

