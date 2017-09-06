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
from objc import pyobjc_unicode, python_method, super

from editxt.command.parser import CompletionsList
from editxt.constants import ERROR, HTML, INFO, LARGE_NUMBER_FOR_TEXT
from editxt.platform.mac.app import beep
from editxt.platform.mac.font import get_font_from_view
from editxt.platform.mac.views.dualview import DualView, SHOULD_RESIZE
from editxt.platform.mac.views.util import font_smoothing
from editxt.platform.kvo import KVOList, KVOProxy
from editxt.util import load_image, WeakProperty

log = logging.getLogger(__name__)
ACTIVATE = "activate"
MESSAGE_COLORS = {INFO: None, ERROR: ak.NSColor.redColor()}

class CommandView(DualView):

    editor = WeakProperty()

    class KEYS:
        ESC = "cancelOperation:"
        TAB = "insertTab:"
        BACK_TAB = "insertBacktab:"
        UP = "moveUp:"
        DOWN = "moveDown:"
        ENTER = "insertNewline:"
        SELECTION_CHANGED = None

    def init_frame_(self, editor, rect):
        from editxt.textcommand import AutoCompleteMenu
        self.active = False
        self.undo_manager = fn.NSUndoManager.alloc().init()
        self.output = ContentSizedTextView(editor.app, rect)
        self.output.scroller.setBorderType_(ak.NSBezelBorder)
        self.completions = AutoCompleteMenu()
        self.completions.on.selection_changed(self.propose_completion)
        self.completions.view.view.setRefusesFirstResponder_(True) # HACK deep reach
        self.completions.scroller.setBorderType_(ak.NSBezelBorder)
        self.input = ContentSizedTextView(editor.app, rect)
        self.input.scroller.setBorderType_(ak.NSBezelBorder)

        def completions_height():
            return self.completions.preferred_height if self.completions else 0
        def input_height(rect=None):
            return self.input.preferred_height
        self.input_group = DualView.alloc().init(rect,
            self.completions.scroller, self.input.scroller,
            completions_height, input_height,
            offset_rect=fn.NSMakeRect(-1, -1, 2, 1))
        self.completions.on.items_changed(self.input_group.should_resize)
        ak.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self.input_group, "shouldResize:", SHOULD_RESIZE, self.input)

        def input_group_height():
            group = self.input_group
            return 0 if not self.active \
                     else (group.top_height() + group.bottom_height() - 1)
        def output_height():
            return self.output.preferred_height if self.output.string() else 0
        super().init(rect,
            self.output.scroller, self.input_group,
            output_height, input_group_height,
            offset_rect=fn.NSMakeRect(-1, -1, 2, 1))

        self.output.setEditable_(False)
        self.output.setSelectable_(True)
        self.output.setLinkTextAttributes_({
            ak.NSCursorAttributeName: ak.NSCursor.pointingHandCursor()
        })
        self.output.setDelegate_(self)
        self.setup_output_popout_button()
        self.input.setDelegate_(self)
        def text_did_change_handler(textview):
            if self.active:
                text = textview.string()
                textview.placeholder = self.command.get_placeholder(text)
        self.input.text_did_change_handler = text_did_change_handler
        self.setHidden_(True)
        self.editor = editor
        self.command = editor.project.window.command
        self.spinner = None
        ak.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "shouldResize:", SHOULD_RESIZE, self.input_group)
        return self

    def dealloc(self):
        self.input = None
        self.completions = None
        self.output = None
        self.spinner = None
        self.popout_button = None
        self.command = None
        ak.NSNotificationCenter.defaultCenter().removeObserver_(self)
        ak.NSNotificationCenter.defaultCenter().removeObserver_(self.input_group)
        self.input_group = None
        super().dealloc()

    def __bool__(self):
        return self.active or bool(self.output.string())

    @property
    def preferred_height(self):
        # top_height and bottom_height are members of DualView
        return self.top_height() + self.bottom_height()

    @property
    def command_text(self):
        return self.input.string()

    @command_text.setter
    def command_text(self, value):
        self.input.text_data = get_text_data(value, INFO, self.editor)

    @python_method
    def replace_command_text_range(self, range, text):
        if self.input.shouldChangeTextInRange_replacementString_(range, text):
            self.input.replaceCharactersInRange_withString_(range, text)
            self.input.didChangeText()
        else:
            # is this the right thing to do here?
            raise RuntimeError("cannot replace text")

    @property
    def command_text_selected_range(self):
        return self.input.selectedRanges()[0].rangeValue()

    @command_text_selected_range.setter
    def command_text_selected_range(self, value):
        self.input.setSelectedRange_(value)

    @property
    def output_text(self):
        return self.output.textStorage()

    @python_method
    def activate(self, command, initial_text="", select=False):
        new_activation = not self.active
        self.active = True
        editor = self.editor
        if new_activation:
            #self.performSelector_withObject_afterDelay_("selectText:", self, 0)
            # possibly use setSelectedRange
            # http://jeenaparadies.net/weblog/2009/apr/focus-a-nstextfield
            self.output.text_data = get_text_data("", INFO, editor)
        else:
            editor.stop_output()
        if new_activation or initial_text:
            self.input.text_data = get_text_data(initial_text, INFO, editor)
            if select and initial_text:
                self.command_text_selected_range = (0, len(initial_text))
            self.should_resize()
        if self.window() is not None:
            self.window().makeFirstResponder_(self.input)

    def deactivate(self):
        editor = self.editor
        editor.stop_output()
        if self.active:
            self.completions.items = []
            self.active = False
            if self.window() is not None:
                self.window().makeFirstResponder_(editor.text_view)
            self.command.reset()
        self.should_resize()

    def dismiss(self):
        if self:
            self.output.text_data = get_text_data("", INFO, self.editor)
            self.is_waiting(False)
            self.deactivate()

    @python_method
    def message(self, message, msg_type=INFO):
        if not message:
            self.dismiss()
            return
        text_data = get_text_data(message, msg_type, self.editor)
        self.output.text_data = text_data
        self.window().__last_output = text_data
        if msg_type == ERROR:
            beep()
        self.should_resize()

    @python_method
    def append_message(self, message, msg_type=INFO):
        if not message:
            return
        self.output.append_text(message, msg_type)
        if self.window() is not None:
            self.window().__last_output = self.output.text_data
        self.should_resize()

    @python_method
    def show_last_message(self):
        try:
            text_data = self.window().__last_output
        except AttributeError:
            text_data = None
        if text_data and text_data["text"]:
            self.output.text_data = text_data
            self.should_resize()
        else:
            beep()

    @python_method
    def propose_completion(self, items):
        self.command.propose_completion(self, items)

    def textView_doCommandBySelector_(self, textview, selector):
        if textview is self.input:
            return self.command.on_key_command(selector, self)
        elif selector == self.KEYS.ESC:
            self.dismiss()
            return True
        return False

    def textViewDidChangeSelection_(self, notification):
        if notification.object() is self.input:
            self.command.on_key_command(self.KEYS.SELECTION_CHANGED, self)

    def textView_clickedOnLink_atIndex_(self, textview, link, index):
        event = ak.NSApp.currentEvent()
        meta = bool(event.modifierFlags() & ak.NSCommandKeyMask)
        textview.visited_link(index)
        return self.editor.handle_link(str(link), meta)

    def commandHelp_(self, sender):
        if self.active:
            self.command.show_help(self.command_text)
        else:
            beep()

    def is_waiting(self, waiting=None):
        if waiting is not None:
            self.waiting = waiting
            if waiting:
                if self.spinner is None:
                    rect = ak.NSMakeRect(
                        self.output.frame().size.width - 32,  # right
                        2,   # top
                        16,  # width
                        16,  # height
                    )
                    self.spinner = ak.NSProgressIndicator.alloc().initWithFrame_(rect)
                    self.spinner.setControlSize_(ak.NSSmallControlSize)
                    self.spinner.setStyle_(ak.NSProgressIndicatorSpinningStyle)
                    self.output.addSubview_(self.spinner)
                elif self.spinner.isHidden():
                    self.spinner.setHidden_(False)
                self.spinner.startAnimation_(self)
            elif self.spinner is not None:
                self.spinner.setHidden_(True)
                self.spinner.stopAnimation_(self)
        return getattr(self, "waiting", False)

    def setup_output_popout_button(self):
        button = ak.NSButton.alloc().initWithFrame_(
            ak.NSMakeRect(0, 0, 16, 16))
        button.setButtonType_(ak.NSMomentaryChangeButton)
        button.setImage_(load_image("popout-button.png"))
        button.setAlternateImage_(load_image("popout-button-alt.png"))
        button.setImagePosition_(ak.NSImageOnly)
        button.setBezelStyle_(ak.NSInlineBezelStyle)
        button.setBordered_(False)
        button.setAutoresizingMask_(ak.NSViewMaxYMargin)
        self.output.addSubview_(button)
        image_size = button.image().size()
        button.setFrame_(ak.NSMakeRect(
            self.output.frame().size.width - image_size.width, # right,
            2, # top
            image_size.width,
            image_size.height,
        ))
        button.setTarget_(self)
        button.setAction_("popoutButtonClicked:")
        self.popout_button = button

    def popoutButtonClicked_(self, sender):
        from editxt.platform.views import screen_rect
        rect = screen_rect(self.output)
        rect.origin.y -= self.popout_button.image().size().height
        self.editor.create_output_panel(self.output.text_data, rect)

    def undoManagerForTextView_(self, textview):
        return self.undo_manager


def get_text_data(text, msg_type, editor):
    font = get_font_from_view(editor.text_view, editor.app)
    return {
        "text": _get_attributed_string(text, msg_type, font.font),
        "font": font,
    }


def _get_attributed_string(text, msg_type, font):
    if msg_type == HTML:
        raise NotImplementedError("convert text to NSAttributedString")
    elif not isinstance(text, ak.NSAttributedString):
        attrs = {}
        color = MESSAGE_COLORS[msg_type]
        if color is not None:
            attrs[ak.NSForegroundColorAttributeName] = color
        attrs[ak.NSFontAttributeName] = font
        text = ak.NSAttributedString.alloc().initWithString_attributes_(
            str(text),  # str(...) because objc.pyobjc_unicode -> empty string
            attrs,
        )
    return text


class ContentSizedTextView(ak.NSTextView):

    app = WeakProperty()

    def __new__(cls, app, rect):
        self = cls.alloc().initWithFrame_(rect)
        self.app = app
        self._font = app.default_font
        return self

    def initWithFrame_(self, rect):
        super(ContentSizedTextView, self).initWithFrame_(rect)
        self.text_did_change_handler = lambda textview: None # no-op by default
        self.setAllowsUndo_(True)
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
        self.preferred_height = rect.size.height
        self._visited_links = []
        return self

    def dealloc(self):
        self.scroller = None
        super(ContentSizedTextView, self).dealloc()

    @python_method
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

    @property
    def text_data(self):
        return {
            "font": self._font,
            # copy so future changes do not affect this value
            "text": self.textStorage().copy(),
            # do not copy so future visited links are referenced
            "visited_links": self._visited_links,
        }
    @text_data.setter
    def text_data(self, value):
        self.layoutManager().removeTemporaryAttribute_forCharacterRange_(
            ak.NSForegroundColorAttributeName, (0, len(self.textStorage())))

        self._font = font = value["font"]
        self.setFont_(font.font)
        self.font_smoothing = font.smooth
        self.placeholder_attrs.setObject_forKey_(font.font, ak.NSFontAttributeName)

        self.textStorage().setAttributedString_(value["text"])

        link_ranges = value.get("visited_links", [])
        for rng in link_ranges:
            self._mark_visited_link(rng)
        self._visited_links = link_ranges

        self.undoManager().removeAllActions()
        self.textDidChange_(None)

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

    @python_method
    def visited_link(self, index):
        link_range = self._get_link_range(index)
        if link_range is not None:
            self._mark_visited_link(link_range)
            self._visited_links.append(link_range)

    @python_method
    def _mark_visited_link(self, link_range):
        self.layoutManager().addTemporaryAttribute_value_forCharacterRange_(
            ak.NSForegroundColorAttributeName,
            self.app.theme["visited_link_color"],
            link_range,
        )

    @python_method
    def _get_link_range(self, index):
        store = self.textStorage()
        info, rng = store.attribute_atIndex_longestEffectiveRange_inRange_(
            ak.NSLinkAttributeName,
            index,
            None,
            (0, store.length())
        )
        return rng if info is not None else None

    @python_method
    def append_text(self, text, msg_type):
        text = _get_attributed_string(text, msg_type, self._font.font)
        store = self.textStorage()
        range = (store.length(), 0)
        store.replaceCharactersInRange_withAttributedString_(range, text)
        self.textDidChange_(None)

    def textDidChange_(self, notification):
        if self._placeholder:
            self.placeholder = self._placeholder
        elif self._h4w_text != self.textStorage():
            self._h4w_text.setAttributedString_(self.textStorage())
        self.text_did_change_handler(self)
        self.reset_preferred_height()
        if self.preferred_height != self.scroller.frame().size.height:
            ak.NSNotificationCenter.defaultCenter() \
                .postNotificationName_object_(SHOULD_RESIZE, self)

    @font_smoothing
    def drawRect_(self, rect):
        super(ContentSizedTextView, self).drawRect_(rect)
        if not self._placeholder or self.isHiddenOrHasHiddenAncestor():
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
