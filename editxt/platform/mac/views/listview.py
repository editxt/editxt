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
from objc import super

from editxt.events import eventize
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
    """

    class events:
        double_click = eventize.call('delegate.setup_double_click')
        selection_changed = eventize.attr('delegate.on_selection_changed')

    def __init__(self, items, colspec):
        eventize(self)
        self.items = items
        self.colspec = colspec
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
            title = spec.get("title", name.title()) or ""
            keypath = "arrangedObjects" if attr is None else ("arrangedObjects." + attr)
            column = ak.NSTableColumn.alloc().initWithIdentifier_(name)
            column.bind_toObject_withKeyPath_options_(ak.NSValueBinding, ctrl, keypath, None)
            column.setResizingMask_(1) # NSTableColumnAutoresizingMask
            column.headerCell().setStringValue_(title)
            column.setEditable_(spec.get("editable", False))
            view.addTableColumn_(column)
        if all(c.get("title", 1) is None for c in self.colspec):
            view.setHeaderView_(None)

        self.delegate = TableDelegate.alloc().init_content_(view, ctrl)
        view.setDelegate_(self.delegate)

    @property
    def preferred_height(self):
        header = 1 if self.view.headerView() is None \
                   else self.view.headerView().frame().size.height
        space = self.view.intercellSpacing().height
        return (self.view.rowHeight() + space) * len(self.items) + header

    def become_subview_of(self, view, focus=True):
        self.scroll.setFrame_(view.bounds())
        view.addSubview_(self.scroll)
        if focus:
            assert view.window() is not None, "cannot focus view: %r" % (view,)
            view.window().makeFirstResponder_(self.view)

    @property
    def title(self):
        if self.view.headerView() is None:
            return None
        return self.view.tableColumns()[0].headerCell().stringValue()

    @title.setter
    def title(self, value):
        if value is None:
            if self.view.headerView() is not None:
                self.view.setHeaderView_(None)
        else:
            if self.view.headerView() is None:
                header = ak.NSTableHeaderView.alloc().init()
                header.setTableView_(self.view)
                self.view.setHeaderView_(header)
            cell = self.view.tableColumns()[0].headerCell()
            cell.setStringValue_(value)
            # is it always desirable to elide middle?
            cell.setLineBreakMode_(ak.NSLineBreakByTruncatingMiddle)
            self.view.headerView().setNeedsDisplay_(True)

    @property
    def selected_row(self):
        """Get the last selected row"""
        return self.view.selectedRow()

    def select(self, indexes, extend=False):
        """Select the given indexes
        """
        if indexes is None:
            first = None
            indexes = ak.NSIndexSet.indexSet()
        elif not isinstance(indexes, set):
            first = indexes
            indexes = ak.NSIndexSet.indexSetWithIndex_(indexes)
        else:
            first = indexes[0]
            raise NotImplementedError
        self.view.selectRowIndexes_byExtendingSelection_(indexes, extend)
        if first is not None:
            self.view.scrollRowToVisible_(first)

    def close(self):
        self.view.setDelegate_(None)
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
        self.on_selection_changed = None
        self.double_click_callback = None
        return self

    def setup_double_click(self, callback):
        if self.double_click_callback is not None:
            raise NotImplementedError("cannot add multiple dobule click actions")
        self.double_click_callback = callback
        self.table.setTarget_(self)
        self.table.setDoubleAction_(b"onDoubleClick:")

    def onDoubleClick_(self, sender):
        row = self.table.clickedRow()
        items = self.content.arrangedObjects()
        if row >= 0 and row < len(items):
            self.double_click_callback(proxy_target(items[row]))

    def tableViewSelectionDidChange_(self, notification):
        if self.on_selection_changed is None:
            return
        table = notification.object()
        if table.numberOfSelectedRows() < 1:
            self.on_selection_changed([])
        elif table.numberOfSelectedRows() > 1:
            raise NotImplementedError
        else:
            item = self.content.arrangedObjects()[table.selectedRow()]
            self.on_selection_changed([proxy_target(item)])

    def close(self):
        self.table.setTarget_(None)
        self.table = None
        self.content = None
