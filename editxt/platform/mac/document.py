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
import objc

import objc
import AppKit as ak
import Foundation as fn
from objc import super

from editxt.constants import LARGE_NUMBER_FOR_TEXT
from editxt.controls.dualview import DualView, SHOULD_RESIZE
from editxt.controls.linenumberview import LineNumberView
from editxt.controls.statscrollview import StatusbarScrollView
from editxt.controls.textview import TextView
from editxt.platform.mac.views import CommandView


def setup_main_view(editor, frame):
    """Setup main text view with command view for document
    """
    layout = ak.NSLayoutManager.alloc().init()
    editor.document.text_storage.addLayoutManager_(layout)
    container = ak.NSTextContainer.alloc().initWithContainerSize_(frame.size)
    container.setLineFragmentPadding_(0.0)
    layout.addTextContainer_(container)

    scroll = StatusbarScrollView.alloc().initWithFrame_(frame)
    scroll.setHasHorizontalScroller_(True)
    scroll.setHasVerticalScroller_(True)
    scroll.setAutoresizingMask_(ak.NSViewWidthSizable | ak.NSViewHeightSizable)

    text = TextView(editor, frame, container)
    text.setAllowsUndo_(True)
    text.setVerticallyResizable_(True)
    text.setMaxSize_(fn.NSMakeSize(LARGE_NUMBER_FOR_TEXT, LARGE_NUMBER_FOR_TEXT))
    # setTextContainerInset() with height > 0 causes a strange bug with
    # the movement of the line number ruler (it moves down when
    # scrolling down near the top of the document) (OS X 10.6 only?)
    attrs = editor.document.default_text_attributes()
    font = attrs[ak.NSFontAttributeName]
    half_char = font.advancementForGlyph_(ord("8")).width / 2
    # the inset width is overridden by our custom TextView.textContainerOrigin()
    text.setTextContainerInset_(fn.NSMakeSize(half_char, half_char)) # width/height
    text.setDrawsBackground_(False)
    text.setSmartInsertDeleteEnabled_(False)
    #text.setRichText_(False) # introduces drawing lag in 10.11
                              # workarounds in TextView copy/paste methods
    text.setUsesFontPanel_(False)
    text.setUsesFindPanel_(True)
    text.setTypingAttributes_(attrs)
    text.setFont_(font)
    text.setDefaultParagraphStyle_(attrs[ak.NSParagraphStyleAttributeName])
    scroll.setDocumentView_(text)

    # setup line number ruler
    StatusbarScrollView.setRulerViewClass_(LineNumberView)
    scroll.setHasVerticalRuler_(True)
    #scroll.verticalRulerView().invalidateRuleThickness()
    scroll.setRulersVisible_(True)

    main_view = add_command_view(scroll, frame, editor.project.window.command)
    main_view._text_delegate = TextViewDelegate.alloc().init_(editor)
    text.setDelegate_(main_view._text_delegate)

    return main_view


def add_command_view(document_scroller, frame, command_bar):
    command = CommandView.alloc().init_frame_(command_bar, frame)
    def doc_height():
        return document_scroller.contentSize().height
    def command_height():
        return command.preferred_height
    main_view = DualView.alloc().init(
        frame, document_scroller, command, doc_height, command_height)
    ak.NSNotificationCenter.defaultCenter() \
        .addObserver_selector_name_object_(
            main_view, "tile:", SHOULD_RESIZE, command)
    return main_view


def teardown_main_view(main_view):
    """The opposite of setup_main_view"""
    main_view.removeFromSuperview()
    main_view._text_delegate = None
    scroll = main_view.top
    scroll.verticalRulerView().denotify()
    text = scroll.documentView()
    text.setDelegate_(None)
    ak.NSNotificationCenter.defaultCenter().removeObserver_(main_view)


class TextViewDelegate(ak.NSObject):

    def init_(self, editor):
        self.on_do_command = editor.on_do_command
        self.on_selection_changed = editor.on_selection_changed
        return self

    def dealloc(self):
        self.on_do_command = None
        self.on_selection_changed = None
        super().dealloc()

    def textView_doCommandBySelector_(self, textview, selector):
        return self.on_do_command(selector)

    def textViewDidChangeSelection_(self, notification):
        textview = notification.object()
        self.on_selection_changed(textview)
