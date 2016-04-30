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
from contextlib import contextmanager

import objc
import AppKit as ak
import Foundation as fn
from objc import super

import editxt.constants as const
from editxt.command.find import FindController
from editxt.command.util import normalize_newlines
from editxt.datatypes import WeakProperty
from editxt.events import eventize
from editxt.platform.app import beep
from editxt.platform.mac.views.util import font_smoothing
from editxt.platform.mac.pasteboard import Pasteboard

log = logging.getLogger(__name__)


class TextViewDelegate(ak.NSObject):

    on_selection_changed = None

    def dealloc(self):
        self.on_selection_changed = None
        super().dealloc()

    def textViewDidChangeSelection_(self, notification):
        textview = notification.object()
        self.on_selection_changed(textview)


class TextView(ak.NSTextView):

    app = WeakProperty()
    editor = WeakProperty() #objc.ivar("editor")

    class events:
        selection_changed = eventize.attr("delegate.on_selection_changed")

    def __new__(cls, editor, frame, container):
        self = cls.alloc().initWithFrame_textContainer_(frame, container)
        eventize(self)
        self.editor = editor
        self.app = editor.project.window.app
        self.delegate = TextViewDelegate.alloc().init()
        self.on.selection_changed(editor.on_selection_changed)
        self.setDelegate_(self.delegate)
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
        length = self.textStorage().length()
        if rng[0] == length and rng[1] == 0:
            # HACK not sure why this is necessary
            # The regression it's working around was introduced in
            # 1ac32effc928b43392982c3b4d39d89639fd56b2 : Fixing line numbers
            rng = (length - 1, 1)
        if length:
            line = self.editor.line_numbers[min(sum(rng), length - 1)]
            self.editor.scroll_view.verticalRulerView().calculate_thickness(line)
        super().scrollRangeToVisible_(rng)

    # Find panel amd text command interaction ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def performFindPanelAction_(self, sender):
        FindController.shared_controller(self.app).perform_action(sender)

    def doMenuCommand_(self, sender):
        self.app.text_commander.do_menu_command(self.editor, sender)

    def doCommandBySelector_(self, selector):
        if not self.editor.do_command(selector):
            super(TextView, self).doCommandBySelector_(selector)

    def validateUserInterfaceItem_(self, item):
        if item.action() == "performFindPanelAction:":
            find = FindController.shared_controller(self.app)
            return find.validate_action(item.tag())
        elif item.action() == "doMenuCommand:":
            return self.app.text_commander \
                .is_menu_command_enabled(self.editor, item)
        return super(TextView, self).validateUserInterfaceItem_(item)

    # Drag/drop and copy/paste ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def readSelectionFromPasteboard_type_(self, pasteboard, type_):
        window = self.app.find_window_with_editor(self.editor)
        if window is not None:
            if window.accept_drop(None, pasteboard):
                return True
        return super(TextView, self).readSelectionFromPasteboard_type_(pasteboard, type_)

    def readablePasteboardTypes(self):
        with temporarily_disable_rich_text(self):
            return super().readablePasteboardTypes()

    def paste_(self, sender):
        self.pasteAsPlainText_(sender)

    def pasteAsPlainText_(self, sender):
        text = Pasteboard().text
        if text:
            self.insertText_(text)

    def pasteAsRichText_(self, sender):
        self.pasteAsPlainText_(sender)

    def insertText_(self, text):
        self.insertText_replacementRange_(text, self.selectedRange())

    def insertText_replacementRange_(self, text, rng):
        eol = const.EOLS[self.editor.newline_mode]
        text = normalize_newlines(text, eol)
        super().insertText_replacementRange_(text, rng)

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
        class params:
            background_color = self.app.theme.background_color
            line_color = self.app.theme["right_margin.line_color"]
            margin_color = self.app.theme["right_margin.margin_color"]
            line_number_color = self.app.theme.line_number_color
            margin = (charw * nchars + padding + origin.x) if nchars else None
        self._margin_params = mp = params
        return mp
    @margin_params.deleter
    def margin_params(self):
        if hasattr(self, "_margin_params"):
            del self._margin_params

    def drawViewBackgroundInRect_(self, rect):
        params = self.margin_params
        guideX = params.margin
        if guideX is not None:
            ak.NSGraphicsContext.currentContext().saveGraphicsState()
            params.line_color.set()
            ak.NSRectFill(fn.NSMakeRect(guideX, rect.origin.y, 1, rect.size.height))
            params.margin_color.set()
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

    def setTypingAttributes_(self, attrs):
        super().setTypingAttributes_(attrs)
        fg_color = ak.NSForegroundColorAttributeName
        if fg_color in attrs:
            theme = self.app.theme
            self.setInsertionPointColor_(attrs[fg_color])
            self.setSelectedTextAttributes_({
                ak.NSBackgroundColorAttributeName: theme.selection_color,
            })

    # Conditional font smoothing ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    drawRect_ = font_smoothing(ak.NSTextView.drawRect_)


@contextmanager
def temporarily_disable_rich_text(textview):
    """Temporarily disable rich text flag

    Hack/workaround for OS X 10.11: `TextView.setRichText_(False)` makes
    the textview drawing sluggish, which is especially noticeable when
    inserting new lines.

    According to the Cocoa documentation, the `richText` property was
    added in 10.10, but this program has been using `setRichText_()`
    since long before that, and there are abundant sources online that
    mentioned it's use long before 10.10 was released.
    """
    textview.setRichText_(False)
    try:
        yield
    finally:
        textview.setRichText_(True)
