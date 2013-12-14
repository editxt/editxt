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
import math

import AppKit as ak
import Foundation as fn
from objc import pyobjc_unicode
from Quartz.CoreGraphics import CGRectIntersectsRect

from editxt.constants import ERROR, HTML, INFO, LARGE_NUMBER_FOR_TEXT
from editxt.controls.dualview import DualView, SHOULD_RESIZE

log = logging.getLogger(__name__)
ACTIVATE = "activate"
MESSAGE_COLORS = {INFO: None, ERROR: ak.NSColor.redColor()}

class CommandView(DualView):

    def initWithFrame_(self, rect):
        self.input = ContentSizedTextView.alloc().initWithFrame_(rect)
        self.input.scroller.setBorderType_(ak.NSBezelBorder)
        self.output = ContentSizedTextView.alloc().initWithFrame_(rect)
        self.output.scroller.setBorderType_(ak.NSBezelBorder)

        def input_height(rect=None):
            return 0 if self.command is None else self.input.preferred_height
        def output_height():
            return self.output.preferred_height if self.output.string() else 0
        super().init(rect,
            self.output.scroller, self.input.scroller, output_height, input_height)
        self.subview_offset_rect = fn.NSMakeRect(-1, -1, 2, 1)

        self.output.setEditable_(False)
        self.output.setSelectable_(True)
        self.input.setDelegate_(self)
        def text_did_change_handler(textview):
            if self.command is not None:
                text = textview.string()
                textview.placeholder = self.command.get_placeholder(text)
        self.input.text_did_change_handler = text_did_change_handler
        self.setHidden_(True)
        self.command = None
        self._last_completions = [None]
        ak.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "shouldResize:", SHOULD_RESIZE, self.input)
        return self

    def dealloc(self):
        self.input = None
        self.output = None
        self.command = None
        ak.NSNotificationCenter.defaultCenter().removeObserver_(self)
        super().dealloc()

    def __bool__(self):
        return self.command is not None or bool(self.output.string())

    @property
    def preferred_height(self):
        # top_height and bottom_height are members of DualView
        return self.top_height() + self.bottom_height()

    def activate(self, command, initial_text=""):
        new_activation = self.command is None
        if new_activation:
            self.command = command
            #self.performSelector_withObject_afterDelay_("selectText:", self, 0)
            # possibly use setSelectedRange
            # http://jeenaparadies.net/weblog/2009/apr/focus-a-nstextfield
            editor = command.window.current_editor
            if editor is not None:
                self.input.setFont_(editor.text_view.font())
            self.output.setString_("")
        if new_activation or initial_text:
            self.input.setString_(initial_text)
            self.should_resize()
        self.window().makeFirstResponder_(self.input)

    def deactivate(self):
        if self.command is not None:
            self.command, command = None, self.command
            editor = command.window.current_editor
            if editor is not None:
                self.window().makeFirstResponder_(editor.text_view)
            command.reset()
        self.should_resize()

    def dismiss(self):
        if self:
            self.output.setString_("")
            self.deactivate()

    def message(self, message, textview=None, msg_type=INFO):
        if msg_type == HTML:
            raise NotImplementedError("convert message to NSAttributedString")
        else:
            attrs = {}
            color = MESSAGE_COLORS[msg_type]
            if color is not None:
                attrs[ak.NSForegroundColorAttributeName] = color
            if textview is not None:
                attrs[ak.NSFontAttributeName] = textview.font()
            text = ak.NSAttributedString.alloc().initWithString_attributes_(
                message, attrs)
        self.output.setAttributedString_(text)
        if msg_type == ERROR:
            ak.NSBeep()
        self.should_resize()

    #def textDidEndEditing_(self, notification):
    #    self.deactivate()

    def textView_doCommandBySelector_(self, textview, selector):
        if selector == "cancelOperation:": # escape key
            self.deactivate()
            return True
        if selector == "insertTab:":
            self.complete(textview)
            return True
        if selector == "insertBacktab:":
            # ignore
            return True
        if selector == "moveUp:":
            #assert view is self, (view, self)
            self.navigate_history()
            return True
        if selector == "moveDown:":
            #assert view is self, (view, self)
            self.navigate_history(forward=True)
            return True
        if selector == "insertNewline:":
            text = textview.string()
            # TODO send cursor position instead of len(text)
            if not self.command.should_insert_newline(text, len(text)):
                self.command.execute(text)
                self.deactivate()
                return True
        return False

    def get_completions(self, textview, range=None):
        if range is None:
            range = textview.selectedRanges()[0].rangeValue()
        index = range.location + range.length
        text = textview.string()
        if index < len(text):
            text = text[:index]
        if self._last_completions[0] == text:
            return self._last_completions
        words, default_index = self.command.get_completions(text)
        self._last_completions = text, words, default_index
        return text, words, default_index

    def complete(self, textview):
        text, words, default_index = self.get_completions(textview)
        if len(words) == 1:
            # replace immediately with single suggestion
            word = words[0]
            index = len(text) - len(word)
            if index < 0:
                index = 0
            while index < len(text):
                if word.startswith(text[index:]):
                    break
                index += 1
            assert len(text) >= index, (text, index)
            range = (index, len(text) - index)
            word += " "
            if textview.shouldChangeTextInRange_replacementString_(range, word):
                textview.replaceCharactersInRange_withString_(range, word)
                textview.didChangeText()
        else:
            # show menu of replacements
            textview.complete_(self)

    def textView_completions_forPartialWordRange_indexOfSelectedItem_(
            self, textview, words, range, item_index):
        words, default_index = self.get_completions(textview, range)[1:]
        return [w + " " for w in words], default_index

    def navigate_history(self, forward=False):
        old_text = self.input.string()
        text = self.command.get_history(old_text, forward)
        if text is None:
            ak.NSBeep()
            return
        self.input.setString_(text)


class ContentSizedTextView(ak.NSTextView):

    def initWithFrame_(self, rect):
        super(ContentSizedTextView, self).initWithFrame_(rect)
        self.text_did_change_handler = lambda textview: None # no-op by default
        #self.setAllowsUndo_(True)
        self.setVerticallyResizable_(True)
        self.setMaxSize_(ak.NSMakeSize(LARGE_NUMBER_FOR_TEXT, LARGE_NUMBER_FOR_TEXT))
        self.setTextContainerInset_(ak.NSMakeSize(0.0, 2.0))
        self.setSmartInsertDeleteEnabled_(False)
        self.setRichText_(False)
        self.setUsesFontPanel_(False)
        self.setUsesFindPanel_(False)
        self._setup_scrollview(rect)

        # text attributes and machinery for placeholder drawing
        self.placeholder_attrs = ak.NSMutableDictionary.alloc() \
            .initWithDictionary_({
                ak.NSForegroundColorAttributeName: ak.NSColor.lightGrayColor(),
            })

        # text storage, container, and layout manager for height calculations
        self._h4w_text = ak.NSTextStorage.alloc().init()
        self._h4w_container = ak.NSTextContainer.alloc().initWithContainerSize_(
            ak.NSMakeSize(rect.size.width, LARGE_NUMBER_FOR_TEXT))
        layout = ak.NSLayoutManager.alloc().init()
        layout.addTextContainer_(self._h4w_container)
        self._h4w_text.addLayoutManager_(layout)

        ak.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "textDidChange:", ak.NSTextDidChangeNotification, self)
        self.placeholder = ""
        #self.setString_(u"")
        return self

    def dealloc(self):
        self.scroller = None
        super(ContentSizedTextView, self).dealloc()

    def _setup_scrollview(self, rect):
        self.scroller = scroller = ak.NSScrollView.alloc().initWithFrame_(rect)
        scroller.setHasHorizontalScroller_(False)
        scroller.setHasVerticalScroller_(True)
        scroller.setAutohidesScrollers_(True)
        scroller.setAutoresizingMask_(
            ak.NSViewWidthSizable | ak.NSViewHeightSizable)
        container = self.textContainer()
        #size = scroller.contentSize()
        container.setContainerSize_(
            ak.NSMakeSize(rect.size.width, LARGE_NUMBER_FOR_TEXT))
        container.setWidthTracksTextView_(True)
        self.setHorizontallyResizable_(False)
        self.setAutoresizingMask_(ak.NSViewWidthSizable)
        #self.setFrameSize_(size)
        self.sizeToFit()
        scroller.setDocumentView_(self)
        scroller

    @property
    def placeholder(self):
        """Placeholder is text to be displayed after main content text"""
        return self._placeholder
    @placeholder.setter
    def placeholder(self, value):
        self._placeholder = value
        text = self._h4w_text
        text.beginEditing()
        text.setAttributedString_(self.textStorage())
        if value:
            tlen = len(self.textStorage())
            text.replaceCharactersInRange_withString_((tlen, 0), value)
            text.setAttributes_range_(self.placeholder_attrs, (tlen, len(value)))
        text.endEditing()

    def reset_preferred_height(self):
        """Get preferred height for enclosing scroll view
        """
        scroller_size = self.scroller.frame().size
        container = self._h4w_container
        container.setContainerSize_(self.textContainer().containerSize())
        layout = container.layoutManager()
        if not self._h4w_text:
            # HACK layout.usedRectForTextContainer_ returns wrong height
            # when content length is zero
            height = layout.defaultLineHeightForFont_(self.font())
        else:
            # TODO minimal layout for changed text range
            layout.glyphRangeForTextContainer_(container)
            height = layout.usedRectForTextContainer_(container).size.height
        content_size = ak.NSScrollView \
            .contentSizeForFrameSize_hasHorizontalScroller_hasVerticalScroller_borderType_(
                scroller_size, False, False, self.scroller.borderType())
        border_width = scroller_size.height - content_size.height
        self.preferred_height \
            = height + self.textContainerInset().height * 2 + border_width

    def setFont_(self, value):
        super(ContentSizedTextView, self).setFont_(value)
        self.placeholder_attrs.setObject_forKey_(value, ak.NSFontAttributeName)
        if self._placeholder:
            range = (0, len(self._h4w_text))
            self._h4w_text.setAttributes_range_(self.placeholder_attrs, range)
        self.textDidChange_(None)

    def setString_(self, value):
        if isinstance(value, pyobjc_unicode):
            # Convert value to unicode to make setString_ work.
            # Have no idea why it does not work without this.
            value = str(value) # TODO revisit since upgrading to Python3
        super(ContentSizedTextView, self).setString_(value)
        self.textDidChange_(None)

    def setAttributedString_(self, value):
        self.textStorage().setAttributedString_(value)
        self.textDidChange_(None)

    def textDidChange_(self, notification):
        self.text_did_change_handler(self)
        self.reset_preferred_height()
        if self.preferred_height != self.scroller.frame().size.height:
            ak.NSNotificationCenter.defaultCenter() \
                .postNotificationName_object_(SHOULD_RESIZE, self)

    def drawRect_(self, rect):
        super(ContentSizedTextView, self).drawRect_(rect)
        if not self._placeholder:
            return
        # draw placeholder text after main content text
        # BUG 3-or-more-word placeholder does not draw properly when wrapped
        layout = self._h4w_container.layoutManager()
        glyph_range = layout \
            .glyphRangeForBoundingRectWithoutAdditionalLayout_inTextContainer_(
                rect, self._h4w_container)
        self.lockFocus()
        layout.drawGlyphsForGlyphRange_atPoint_(
            glyph_range, self.textContainerInset())
        self.unlockFocus()
