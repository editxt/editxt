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
from objc import super

from editxt.command.find import FindController
from editxt.datatypes import WeakProperty
from editxt.platform.app import beep
from editxt.platform.mac.views.util import font_smoothing

log = logging.getLogger(__name__)


class TextView(ak.NSTextView):

    app = WeakProperty()
    editor = WeakProperty() #objc.ivar("editor")

    def __new__(cls, editor, frame, container):
        self = cls.alloc().initWithFrame_textContainer_(frame, container)
        self.editor = editor
        self.app = editor.project.window.app
        return self

#    def dealloc(self):
#        self.editor = None
#        self.app = None
#        super().dealloc()

    def font(self):
        """Get the document's font

        :returns: NSFont object
        """
        return self.editor.font.font

    def focus(self):
        self.window().makeFirstResponder_(self)

    def goto_line(self, line):
        # TODO move this into editor
        if isinstance(line, (tuple, list)):
            line, select_start, select_len = line
        else:
            select_start = 0
            select_len = 0
        try:
            index = self.editor.line_numbers.index_of(line)
            range = (index + select_start, select_len)
            self.setSelectedRange_(range)
            self.scrollRangeToVisible_(range)
        except ValueError:
            beep()

    def scrollRangeToVisible_(self, rng):
        if rng[0] == self.textStorage().length() and rng[1] == 0:
            # HACK not sure why this is necessary
            # The regression it's working around was introduced in
            # 1ac32effc928b43392982c3b4d39d89639fd56b2 : Fixing line numbers
            rng = (self.textStorage().length() - 1, 1)
        super().scrollRangeToVisible_(rng)

    # Find panel amd text command interaction ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def performFindPanelAction_(self, sender):
        FindController.shared_controller(self.app).perform_action(sender)

    def doCommand_(self, sender):
        self.app.text_commander.do_command(self.editor, sender)

    def doCommandBySelector_(self, selector):
        if not self.app.text_commander.do_command_by_selector(self.editor, selector):
            super(TextView, self).doCommandBySelector_(selector)

    def validateUserInterfaceItem_(self, item):
        if item.action() == "performFindPanelAction:":
            find = FindController.shared_controller(self.app)
            return find.validate_action(item.tag())
        elif item.action() == "doCommand:":
            return self.app.text_commander.is_command_enabled(self.editor, item)
        return super(TextView, self).validateUserInterfaceItem_(item)

    # Drag/drop ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def readSelectionFromPasteboard_type_(self, pasteboard, type_):
        window = self.app.find_window_with_editor(self.editor)
        if window is not None:
            if window.accept_drop(None, pasteboard):
                return True
        return super(TextView, self).readSelectionFromPasteboard_type_(pasteboard, type_)

    # Right-margin guide ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def textContainerOrigin(self):
        """Remove left margin created by symmetrical textContainerInset

        HACK hard-coded 1.0 : the width of NSTextView's caret. If X is
        set to zero the caret disappears when it is located before/on
        the first character in the line (position zero).
        """
        origin = super().textContainerOrigin()
        inset = self.textContainerInset()
        return ak.NSMakePoint(1.0, origin.y)

    @property
    def margin_params(self):
        if hasattr(self, "_margin_params"):
            return self._margin_params
        font = self.editor.font.font
        charw = font.advancementForGlyph_(ord("8")).width
        origin = self.textContainerOrigin()
        padding = self.textContainer().lineFragmentPadding()
        nchars = self.app.config["theme.right_margin.position"]
        color1 = self.app.config["theme.right_margin.line_color"]
        color2 = self.app.config["theme.right_margin.margin_color"]
        color3 = self.app.config["theme.line_number_color"]
        margin = (charw * nchars + padding + origin.x) if nchars else None
        self._margin_params = mp = (margin, color1, color2, color3)
        return mp
    @margin_params.deleter
    def margin_params(self):
        if hasattr(self, "_margin_params"):
            del self._margin_params

    def drawViewBackgroundInRect_(self, rect):
        guideX, color1, color2, color3 = self.margin_params
        if guideX is not None:
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

    # Conditional font smoothing ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    drawRect_ = font_smoothing(ak.NSTextView.drawRect_)
