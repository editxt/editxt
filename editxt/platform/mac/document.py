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

from editxt.constants import LARGE_NUMBER_FOR_TEXT
from editxt.controls.commandview import CommandView
from editxt.controls.dualview import DualView, SHOULD_RESIZE
from editxt.controls.linenumberview import LineNumberView
from editxt.controls.statscrollview import StatusbarScrollView
from editxt.controls.textview import TextView


def setup_main_view(docview, frame):
    """Setup main text view with command view for document
    """
    layout = ak.NSLayoutManager.alloc().init()
    docview.document.text_storage.addLayoutManager_(layout)
    container = ak.NSTextContainer.alloc().initWithContainerSize_(frame.size)
    container.setLineFragmentPadding_(10) # left margin
    layout.addTextContainer_(container)

    scroll = StatusbarScrollView.alloc().initWithFrame_(frame)
    scroll.setHasHorizontalScroller_(True)
    scroll.setHasVerticalScroller_(True)
    scroll.setAutoresizingMask_(ak.NSViewWidthSizable | ak.NSViewHeightSizable)

    text = TextView(docview, frame, container)
    text.setAllowsUndo_(True)
    text.setVerticallyResizable_(True)
    text.setMaxSize_(fn.NSMakeSize(LARGE_NUMBER_FOR_TEXT, LARGE_NUMBER_FOR_TEXT))
    # setTextContainerInset() with height > 0 causes a strange bug with
    # the movement of the line number ruler (it moves down when
    # scrolling down near the top of the document)
    text.setTextContainerInset_(fn.NSMakeSize(0, 0)) # width/height
    text.setDrawsBackground_(False)
    text.setSmartInsertDeleteEnabled_(False)
    text.setRichText_(False)
    text.setUsesFontPanel_(False)
    text.setUsesFindPanel_(True)
    attrs = docview.document.default_text_attributes()
    text.setTypingAttributes_(attrs)
    font = attrs[ak.NSFontAttributeName]
    text.setFont_(font)
    text.setDefaultParagraphStyle_(attrs[ak.NSParagraphStyleAttributeName])
    scroll.setDocumentView_(text)

    # setup line number ruler
    StatusbarScrollView.setRulerViewClass_(LineNumberView)
    scroll.setHasVerticalRuler_(True)
    #scroll.verticalRulerView().invalidateRuleThickness()
    scroll.setRulersVisible_(True)

    command = CommandView.alloc().initWithFrame_(frame)

    delegate = TextViewDelegate.alloc().init_(docview)
    text.setDelegate_(delegate)

    def doc_height():
        return scroll.contentSize().height
    def command_height():
        return command.preferred_height
    main_view = DualView.alloc().init(
        frame, scroll, command, doc_height, command_height, 0.2)
    ak.NSNotificationCenter.defaultCenter() \
        .addObserver_selector_name_object_(
            main_view, "tile:", SHOULD_RESIZE, command)

    return main_view


def teardown_main_view(main_view):
    """The opposite of setup_main_view"""
    main_view.removeFromSuperview()
    scroll = main_view.top
    scroll.verticalRulerView().denotify()
    text = scroll.documentView()
    text.setDelegate_(None)
    ak.NSNotificationCenter.defaultCenter().removeObserver_(main_view)


class TextViewDelegate(ak.NSObject):

    def init_(self, docview):
        self.on_do_command = docview.on_do_command
        self.on_selection_changed = docview.on_selection_changed

    def dealloc(self):
        self.on_do_command = None
        self.on_selection_changed = None
        super().dealloc()

    def textView_doCommandBySelector_(self, textview, selector):
        return self.on_do_command(selector)

    def textViewDidChangeSelection_(self, notification):
        textview = notification.object()
        self.on_selection_changed(textview)
