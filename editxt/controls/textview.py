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
import re

import objc
import AppKit as ak
import Foundation as fn

from editxt.command.find import FindController
from editxt.datatypes import WeakProperty

log = logging.getLogger(__name__)


class TextView(ak.NSTextView):

    app = WeakProperty()
    doc_view = WeakProperty() #objc.ivar("doc_view")

    def __new__(cls, docview, frame, container):
        self = cls.alloc().initWithFrame_textContainer_(frame, container)
        self.doc_view = docview
        self.app = docview.project.editor.app
        return self

#    def dealloc(self):
#        self.doc_view = None
#        self.app = None
#        super().dealloc()

    def goto_line(self, num):
        eol = self.doc_view.document.eol
        assert len(eol) > 0, repr(eol)
        text = self.string()
        line = 1
        tlen = len(text)
        index = 0
        while line < num:
            frange = (index, tlen - index)
            found = text.rangeOfString_options_range_(eol, 0, frange)
            if not found.length:
                break
            index = found.location + found.length
            line += 1
        if line == num:
            range = (index, 0)
            self.setSelectedRange_(range)
            self.scrollRangeToVisible_(range)
        else:
            ak.NSBeep()

    # Find panel amd text command interaction ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def performFindPanelAction_(self, sender):
        FindController.shared_controller().perform_action(sender)

    def performTextCommand_(self, sender):
        self.app.text_commander.do_textview_command(self, sender)

    def doCommandBySelector_(self, selector):
        if not self.app.text_commander.do_textview_command_by_selector(self, selector):
            super(TextView, self).doCommandBySelector_(selector)

    def validateUserInterfaceItem_(self, item):
        if item.action() == "performFindPanelAction:":
            return FindController.shared_controller().validate_action(item.tag())
        elif item.action() == "performTextCommand:":
            return self.app.text_commander.is_textview_command_enabled(self, item)
        return super(TextView, self).validateUserInterfaceItem_(item)

    # Drag/drop ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def readSelectionFromPasteboard_type_(self, pasteboard, type_):
        editor = self.app.find_editor_with_document_view(self.doc_view)
        if editor is not None:
            items = editor.iter_dropped_paths(pasteboard)
            parent = editor.find_project_with_document_view(self.doc_view)
            index = len(editor.projects) if parent is None else -1
            result = editor.insert_items(items, parent, index, None)
            if result: return True
        return super(TextView, self).readSelectionFromPasteboard_type_(pasteboard, type_)

    # Right-margin guide ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @property
    def marginParams(self):
        # TODO invalidate the cached value when the document's font is changed
        try:
            return self._marginParams
        except AttributeError:
            pass
        nchars = self.app.config["right_margin.position"]
        if not nchars:
            self._marginParams = None
            return
        font = self.doc_view.document.default_text_attributes()[ak.NSFontAttributeName]
        charw = font.advancementForGlyph_(ord(" ")).width
        padding = self.textContainer().lineFragmentPadding()
        color1 = self.app.config["right_margin.line_color"]
        color2 = self.app.config["right_margin.margin_color"]
        self._marginParams = mp = (charw * nchars + padding, color1, color2)
        return mp

    def drawViewBackgroundInRect_(self, rect):
        if self.marginParams is not None:
            guideX, color1, color2 = self.marginParams
            ak.NSGraphicsContext.currentContext().saveGraphicsState()
            color1.set()
            ak.NSRectFill(fn.NSMakeRect(guideX, rect.origin.y, 1, rect.size.height))
            color2.set()
            ak.NSRectFill(fn.NSMakeRect(guideX + 1, rect.origin.y, 10**7, rect.size.height))
            ak.NSGraphicsContext.currentContext().restoreGraphicsState()
        super(TextView, self).drawViewBackgroundInRect_(rect)

    def setFrameSize_(self, size):
        """add space for scrolling beyond last line"""
        tc = self.textContainer()
        lm = self.layoutManager()
        sv = self.enclosingScrollView()
        height = size.height
        if not (tc is None or lm is None or sv is None):
            text_height = lm.usedRectForTextContainer_(tc).size.height
            extra_space = sv.contentSize().height * 0.75
            if text_height + extra_space > height:
                height = text_height + extra_space
        super(TextView, self).setFrameSize_(fn.NSMakeSize(size.width, height))
