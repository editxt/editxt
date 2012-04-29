# -*- coding: utf-8 -*-
# EditXT
# Copyright (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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
from AppKit import *
from Foundation import *

import editxt.constants as const
from editxt import app
from editxt.findpanel import FindController

log = logging.getLogger("editxt.controls.textview")


class TextView(NSTextView):

    doc_view = objc.ivar("doc_view")

    # Find panel amd TextCommand interaction ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def performFindPanelAction_(self, sender):
        FindController.shared_controller().perform_action(sender)

    def performTextCommand_(self, sender):
        app.text_commander.do_textview_command(self, sender)

    def doCommandBySelector_(self, selector):
        if not app.text_commander.do_textview_command_by_selector(self, selector):
            super(TextView, self).doCommandBySelector_(selector)

    def validateUserInterfaceItem_(self, item):
        if item.action() == "performFindPanelAction:":
            return FindController.shared_controller().validate_action(item.tag())
        elif item.action() == "performTextCommand:":
            return app.text_commander.is_textview_command_enabled(self, item)
        return super(TextView, self).validateUserInterfaceItem_(item)

    # Drag/drop ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def readSelectionFromPasteboard_type_(self, pasteboard, type_):
        editor = app.find_editor_with_document_view(self.doc_view)
        if editor is not None:
            items = editor.iter_dropped_paths(pasteboard)
            parent = editor.find_project_with_document_view(self.doc_view)
            index = len(editor.projects) if parent is None else -1
            result = editor.accept_dropped_items(items, parent, index, None)
            if result: return True
        return super(TextView, self).readSelectionFromPasteboard_type_(pasteboard, type_)

    # Right-margin guide ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @property
    def marginParams(self):
        # TODO invalidate the cached value when the document's font is changed
        try:
            return self._marginParams
        except AttributeError:
            drm = const.DEFAULT_RIGHT_MARGIN
            font = self.doc_view.document.default_text_attributes()[NSFontAttributeName]
            charw = font.advancementForGlyph_(ord(u" ")).width
            padding = self.textContainer().lineFragmentPadding()
            color1 = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.9, 0.9, 0.9, 1.0)
            color2 = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.97, 0.97, 0.97, 1.0)
            self._marginParams = mp = (charw * drm + padding, color1, color2)
            return mp

    def drawViewBackgroundInRect_(self, rect):
        guideX, color1, color2 = self.marginParams
        NSGraphicsContext.currentContext().saveGraphicsState()
        color1.set()
        NSRectFill(NSMakeRect(guideX, rect.origin.y, 1, rect.size.height))
        color2.set()
        NSRectFill(NSMakeRect(guideX + 1, rect.origin.y, 10**7, rect.size.height))
        NSGraphicsContext.currentContext().restoreGraphicsState()
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
        super(TextView, self).setFrameSize_(NSMakeSize(size.width, height))

    # Scrolling ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#     def adjustScroll_(self, rect):
#         vrect = self.superview().documentVisibleRect()
#         # calculate based on distance scrolled
#         deltaY = rect.origin.y - vrect.origin.y
#         lm = self.layoutManager()
#         glyph = lm.glyphIndexForPoint_inTextContainer_(rect.origin, self.textContainer())
#         lrect = lm.lineFragmentRectForGlyphAtIndex_effectiveRange_(glyph)[0]
#         if abs(deltaY) == lrect.size.height:
#             pass
#         elif abs(deltaY) > lrect.size.height / 2:
#             if deltaY < 0:
#                 # scroll up
#                 rect.origin.y = lrect.origin.y
#             elif deltaY > 0:
#                 # scroll down
#                 rect.origin.y = lrect.origin.y + lrect.size.height
#         else:
#             rect.origin.y -= deltaY
#         log.debug((deltaY, rect.origin))
#         return rect

#     def didChangeText(self):
#         lm = self.layoutManager()
#         range = self.rangeForUserTextChange()

