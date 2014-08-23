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

import AppKit as ak
import Foundation as fn

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import eq_

from editxt.application import Application
from editxt.platform.mac.window import WindowController
from editxt.project import Project
from editxt.util import representedObject
from editxt.window import Window

from editxt.test.util import (do_method_pass_through, TestConfig, Regex,
    replattr, tempdir, test_app)

import editxt.platform.mac.window as mod

log = logging.getLogger(__name__)


def test_WindowController_passthrough_to_Window():
    WC = "WC"
    def test(*args):
        wc = WindowController(None)
        do_method_pass_through("window_", Window, wc, WC, *args)
    yield test, ("hoverButton_rowClicked_", "close_button_clicked"), (None, "<row>"), ("<row>",)
    yield test, ("windowWillClose_", "window_will_close"), ("<window>",), ()
    yield test, ("outlineView_writeItems_toPasteboard_", "write_items_to_pasteboard"), \
        ("<ov>", "<items>", "<pasteboard>"), ("<ov>", "<items>", "<pasteboard>"), \
        "<result>"
#    yield test, ("outlineView_acceptDrop_item_childIndex_", "accept_drop"), \
#        ("<ov>", "<drop>", "<item>", "<index>"), ("<ov>", "<drop>", "<item>", "<index>"), \
#        "<drag result>"
    yield test, ("outlineView_validateDrop_proposedItem_proposedChildIndex_", "validate_drop"), \
        ("<ov>", "<drop>", "<item>", "<index>"), ("<ov>", "<drop>", "<item>", "<index>"), \
        "<drag operation>"
    yield test, ("outlineView_shouldEditTableColumn_item_", "should_edit_item"), \
        ("<ov>", "<col>", "<item>"), ("<col>", "<item>"), "<should ediit>"
    yield test, ("save_", "save"), ("<sender>",), ()
    yield test, ("saveAs_", "save_as"), ("<sender>",), ()
    yield test, ("newProject_", "new_project"), ("<sender>",), ()
    yield test, ("togglePropertiesPane_", "toggle_properties_pane"), ("sender",), ()

def test_windowDidLoad():
    m = Mocker()
    window = m.mock(Window)
    wc = WindowController(window)
    window.window_did_load()
    with m:
        wc.windowDidLoad()

def test_syntaxDefNames():
    m = Mocker()
    wc = WindowController(None)
    wc.window_ = window_ = m.mock(Window)
    app = m.mock(Application)
    (window_.app << app).count(2)
    defs = [type("FakeDef", (object,), {"name": "Fake Syntax"})()]
    (app.syntaxdefs << defs).count(2)
    names = [d.name for d in defs]
    with m:
        eq_(wc.syntaxDefNames(), names)
        wc.setSyntaxDefNames_(None) # should be no-op
        eq_(wc.syntaxDefNames(), names)

def test_characterEncodings():
    wc = WindowController(None)
    names = fn.NSValueTransformer.valueTransformerForName_("CharacterEncodingTransformer").names
    eq_(wc.characterEncodings(), names)
    wc.setCharacterEncodings_(None) # should be no-op
    eq_(wc.characterEncodings(), names)

def test_outlineViewSelectionDidChange_():
    m = Mocker()
    window = m.mock(Window)
    ewc = WindowController(window)
    window.selected_editor_changed()
    with m:
        ewc.outlineViewSelectionDidChange_(None)

def test_outlineViewItemDidExpandCollapse():
    def test(c):
        m = Mocker()
        ed = m.mock(Window)
        ewc = WindowController(ed)
        n = m.mock() # ak.NSOutlineViewItemDid___Notification
        node = m.mock(ak.NSTreeControllerTreeNode); n.userInfo() >> {"NSObject": node}
        it = representedObject(node) >> m.mock(Project)
        it.expanded = c.exp
        with m:
            getattr(ewc, c.method)(n)
    c = TestConfig()
    yield c(method="outlineViewItemDidCollapse_", exp=False)
    yield c(method="outlineViewItemDidExpand_", exp=True)

def test_outlineView_shouldSelectItem_():
    m = Mocker()
    ov = m.mock(ak.NSOutlineView)
    window = m.mock(Window)
    ewc = WindowController(window)
    ewc.window_.should_select_item(ov, None)
    with m:
        ewc.outlineView_shouldSelectItem_(ov, None)

def test_outlineView_willDisplayCell_forTableColumn_item_():
    from editxt.controls.cells import ImageAndTextCell
    ewc = WindowController(None)
    m = Mocker()
    view = m.mock(ak.NSOutlineView)
    cell = m.mock(ImageAndTextCell)
    col, item, icon = m.mock(), m.mock(), m.mock()
    col.identifier() >> "name"
    representedObject(item).icon() >> icon
    cell.setImage_(icon)
    with m:
        ewc.outlineView_willDisplayCell_forTableColumn_item_(view, cell, col, item)

def test_outlineView_toolTipForCell_rect_tableColumn_item_mouseLocation_():
    m = Mocker()
    ed = m.mock(Window)
    ewc = WindowController(ed)
    ov = m.mock(ak.NSOutlineView)
    rect, item = m.mock(), m.mock()
    ed.tooltip_for_item(ov, item) >> "test tip"
    with m:
        result = ewc.outlineView_toolTipForCell_rect_tableColumn_item_mouseLocation_(
            ov, None, rect, None, item, None)
        assert len(result) == 2
        assert result[0] == "test tip"
        assert result[1] is rect

def test_WindowController_undo_manager():
    m = Mocker()
    win = m.mock(ak.NSWindow)
    window = m.mock(Window)
    wc = WindowController(window)
    wc.window_.undo_manager() >> "<undo_manager>"
    with m:
        result = wc.undo_manager()
        eq_(result, "<undo_manager>")

def test_windowDidBecomeKey_():
    m = Mocker()
    notif = m.mock()
    ed = m.mock(Window)
    wc = WindowController(ed)
    ed.window_did_become_key(notif.object() >> m.mock(ak.NSWindow))
    with m:
        wc.windowDidBecomeKey_(notif)

def test_windowShouldClose_():
    m = Mocker()
    win = m.mock(ak.NSWindow)
    window = m.mock(Window)
    wc = WindowController(window)
    wc.window_.window_should_close(win) >> "<should_close>"
    with m:
        result = wc.windowShouldClose_(win)
        eq_(result, "<should_close>")
