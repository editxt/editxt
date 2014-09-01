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


def text_storage_edit_connector(text_storage, on_text_edit):
    """Connect text storage edit events to on_text_edit

    :param text_storage: NSTextStorage instance.
    :param on_text_edit: A function that will be called when the text storage
    processes editing. The function must accept a single argument: the range of
    text that was edited.
    """
    return TextStorageDelegate.alloc().init_callback_(text_storage, on_text_edit)

class TextStorageDelegate(ak.NSObject):

    def init_callback_(self, target, on_text_edit):
        target.setDelegate_(self)
        self.target = target
        self.on_text_edit = on_text_edit
        return self

    def disconnect(self):
        self.target.setDelegate_(None)
        self.target = None

    def dealloc(self):
        self.target = None
        self.on_text_edit = None
        super().dealloc()

    def textStorageDidProcessEditing_(self, notification):
        store = notification.object()
        self.on_text_edit(store.editedRange())


def setup_main_view(editor, frame):
    """Setup main text view with command view for document
    """
    layout = ak.NSLayoutManager.alloc().init()
    editor.document.text_storage.addLayoutManager_(layout)
    container = ak.NSTextContainer.alloc().initWithContainerSize_(frame.size)
    container.setLineFragmentPadding_(10) # left margin
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
    # scrolling down near the top of the document)
    text.setTextContainerInset_(fn.NSMakeSize(0, 0)) # width/height
    text.setDrawsBackground_(False)
    text.setSmartInsertDeleteEnabled_(False)
    text.setRichText_(False)
    text.setUsesFontPanel_(False)
    text.setUsesFindPanel_(True)
    attrs = editor.document.default_text_attributes()
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

    def doc_height():
        return scroll.contentSize().height
    def command_height():
        return command.preferred_height
    main_view = DualView.alloc().init(
        frame, scroll, command, doc_height, command_height, 0.2)
    ak.NSNotificationCenter.defaultCenter() \
        .addObserver_selector_name_object_(
            main_view, "tile:", SHOULD_RESIZE, command)
    main_view._text_delegate = TextViewDelegate.alloc().init_(editor)
    text.setDelegate_(main_view._text_delegate)

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
