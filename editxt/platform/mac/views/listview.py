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

import objc
import AppKit as ak
import Foundation as fn

from editxt.platform.kvo import proxy_target

log = logging.getLogger(__name__)


class ListView(object):
    """A list view

    :param items: A KVOList instance containing the items to be displayed in
    the listview.
    :param colspec: A list of dicts with configuration data for each column in
    the list. Expected keys:

        name - column name (required).
        title - optional column title, default to title-cased ``name``.
        attr - optional name of attribute to be retrieved from item
            to be displayed in the column. If omitted use the value
            of "name". If ``None``, the entire object is returned.
        value - optional function used to transform the column value
            (item.attribute) to a display value for the column.
        type - optional column type, default is "text".
        editable - True if editable. Defaults is False.

    The following optional parameters must be specified as keyword arguments:

    :param on_double_click: optional function to be called when an item in the
    list is double-clicked. It is called with one argument: the item.
    """

    def __init__(self, items, colspec, *, on_double_click=None):
        self.items = items
        self.colspec = colspec
        self.on_double_click = on_double_click
        self._init_table()

    def _init_table(self):
        self.controller = ctrl = ak.NSArrayController.alloc().init()
        self.view = view = ak.NSTableView.alloc().init()
        self.scroll = scroll = ak.NSScrollView.alloc().init()
        scroll.setHasHorizontalScroller_(True)
        scroll.setHasVerticalScroller_(True)
        scroll.setAutoresizingMask_(ak.NSViewWidthSizable | ak.NSViewHeightSizable)
        scroll.setDocumentView_(view)

        ctrl.bind_toObject_withKeyPath_options_("contentArray", self.items, "items", None)
        view.bind_toObject_withKeyPath_options_("content", ctrl, "arrangedObjects", None)
        for spec in self.colspec:
            name = spec["name"]
            attr = spec["attr"] if "attr" in spec else name
            title = spec.get("title", name.title())
            keypath = "arrangedObjects" if attr is None else ("arrangedObjects." + attr)
            column = ak.NSTableColumn.alloc().initWithIdentifier_(name)
            column.bind_toObject_withKeyPath_options_(ak.NSValueBinding, ctrl, keypath, None)
            column.setResizingMask_(1) # NSTableColumnAutoresizingMask
            column.headerCell().setStringValue_(title)
            column.setEditable_(spec.get("editable", False))
            view.addTableColumn_(column)

        self.delegate = TableDelegate.alloc().init_content_(view, ctrl)
        if self.on_double_click is not None:
            self.delegate.setup_double_click(self.on_double_click)

    def become_subview_of(self, view, focus=True):
        self.scroll.setFrame_(view.bounds())
        view.addSubview_(self.scroll)
        if focus:
            assert view.window() is not None, "cannot focus view: %r" % (view,)
            view.window().makeFirstResponder_(self.view)

    def close(self):
        self.delegate.close()
        self.delegate = None
        self.scroll.setDocumentView_(None)
        self.scroll = None
        self.controller.unbind("contentArray")
        self.view.unbind("content")
        self.controller = None
        self.view = None


class TableDelegate(ak.NSObject):

    def init_content_(self, table, content):
        self = super().init()
        self.table = table
        self.content = content
        return self

    def setup_double_click(self, callback):
        self.double_click_callback = callback
        self.table.setTarget_(self)
        self.table.setDoubleAction_(b"onDoubleClick:")

    def onDoubleClick_(self, sender):
        row = self.table.clickedRow()
        items = self.content.arrangedObjects()
        if row >= 0 and row < len(items):
            self.double_click_callback(proxy_target(items[row]))

    def close(self):
        self.table.setTarget_(None)
        self.table = None
        self.content = None