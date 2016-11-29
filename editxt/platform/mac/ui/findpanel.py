# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2016 Daniel Miller <millerdev@gmail.com>
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

import AppKit as ak
import Foundation as fn
from objc import super

import editxt.constants as const
from editxt.platform.app import beep


class FindPanel(ak.NSObject):

    def __new__(cls, controller):
        return cls.alloc().init_(controller)

    def init_(self, controller):
        self.controller = controller
        self.controller.options.app = controller.app # HACK for recent_finds binding
        self.window = _setup(self)
        return self

    def options(self):
        return self.controller.options

    def setOptions_(self, value):
        self.controller.options = value

    def panelFindNext_(self, sender):
        # TODO make controller method names follow python naming convention
        self.controller.panelFindNext_(sender)

    def panelFindPrevious_(self, sender):
        self.controller.panelFindPrevious_(sender)

    def panelReplace_(self, sender):
        self.controller.panelReplace_(sender)

    def panelReplaceAll_(self, sender):
        self.controller.panelReplaceAll_(sender)

    def panelReplaceAllInSelection_(self, sender):
        self.controller.panelReplaceAllInSelection_(sender)

    def panelCountFindText_(self, sender):
        self.controller.panelCountFindText_(sender)

    def panelCountReplaceText_(self, sender):
        self.controller.panelCountReplaceText_(sender)

    def panelMarkAll_(self, sender):
        self.controller.panelMarkAll_(sender)

    def recentFindSelected_(self, sender):
        self.controller.recentFindSelected_(sender)

    def recentReplaceSelected_(self, sender):
        self.controller.recentReplaceSelected_(sender)

    def regexHelp_(self, sender):
        self.controller.regexHelp_(sender)

    def show(self):
        self.window.makeKeyAndOrderFront_(self)


def _setup(obj):
    rect = ak.NSMakeRect(80, 220, 510, 228)
    mask = (
        ak.NSTitledWindowMask |
        ak.NSClosableWindowMask |
        ak.NSResizableWindowMask
    )
    window = ak.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        rect, mask, ak.NSBackingStoreBuffered, True)
    window.setTitle_("Find & Replace")
    window.setMinSize_(ak.NSMakeSize(510, 250))
    window.setLevel_(ak.NSFloatingWindowLevel)

    find_text = obj.find_text = ak.NSTextField.alloc().initWithFrame_(
        ak.NSMakeRect(20, 11, 346, 56))
    find_text.setAutoresizingMask_(ak.NSViewWidthSizable | ak.NSViewHeightSizable)
    find_text.setAllowsEditingTextAttributes_(False)
    find_text.setEditable_(True)
    find_text.setFont_(ak.NSFont.fontWithName_size_("Monaco", 12))
    find_text.setLineBreakMode_(ak.NSLineBreakByWordWrapping)
    find_text.setPlaceholderString_("Find")
    find_text.setUsesSingleLineMode_(False)
    find_text.bind_toObject_withKeyPath_options_(
        "value", obj, "options.find_text", {
            ak.NSContinuouslyUpdatesValueBindingOption: 1,
            ak.NSRaisesForNotApplicableKeysBindingOption: 1,
        })

    replace_text = obj.replace_text = ak.NSTextField.alloc().initWithFrame_(
        ak.NSMakeRect(20, 85, 346, 56))
    replace_text.setAutoresizingMask_(ak.NSViewWidthSizable | ak.NSViewHeightSizable)
    replace_text.setAllowsEditingTextAttributes_(False)
    replace_text.setEditable_(True)
    replace_text.setFont_(ak.NSFont.fontWithName_size_("Monaco", 12))
    replace_text.setLineBreakMode_(ak.NSLineBreakByWordWrapping)
    replace_text.setPlaceholderString_("Replace")
    replace_text.setUsesSingleLineMode_(False)
    replace_text.bind_toObject_withKeyPath_options_(
        "value", obj, "options.replace_text", {
            ak.NSContinuouslyUpdatesValueBindingOption: 1,
            ak.NSRaisesForNotApplicableKeysBindingOption: 1,
        })

    recents_menu = obj.recents_menu = ak.NSPopUpButton.alloc().initWithFrame_(
        ak.NSMakeRect(369, 48, 16, 17))
    recents_menu.setAutoresizingMask_(ak.NSViewMinXMargin | ak.NSViewMinYMargin)
    recents_menu.cell().setArrowPosition_(ak.NSPopUpArrowAtBottom)
    recents_menu.cell().setBezelStyle_(ak.NSShadowlessSquareBezelStyle)
    recents_menu.cell().setBordered_(False)
    recents_menu.setLineBreakMode_(ak.NSLineBreakByTruncatingTail)
    recents_menu.setPreferredEdge_(ak.NSMaxYEdge)
    recents_menu.setPullsDown_(True)
    recents_menu.setTarget_(obj)
    recents_menu.setAction_("recentFindSelected:")
    recents_menu.bind_toObject_withKeyPath_options_(
        "contentValues", obj, "options.recent_finds", {
            ak.NSInsertsNullPlaceholderBindingOption: 1,
            ak.NSRaisesForNotApplicableKeysBindingOption: 1,
        })

    show_find_matches = obj.show_find_matches = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(369, 11, 16, 23))
    show_find_matches.setTitle_("\u2713")
    show_find_matches.setAlternateTitle_("Count occurrences")
    show_find_matches.setBezelStyle_(ak.NSSmallSquareBezelStyle)
    show_find_matches.setControlSize_(ak.NSSmallControlSize)
    show_find_matches.setAutoresizingMask_(ak.NSViewMinXMargin | ak.NSViewMaxYMargin)
    show_find_matches.setTarget_(obj)
    show_find_matches.setAction_("panelCountFindText:")

    show_replace_matches = obj.show_replace_matches = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(369, 85, 16, 23))
    show_replace_matches.setTitle_("\u2713")
    show_replace_matches.setAlternateTitle_("Count occurrences")
    show_replace_matches.setBezelStyle_(ak.NSSmallSquareBezelStyle)
    show_replace_matches.setControlSize_(ak.NSSmallControlSize)
    show_replace_matches.setAutoresizingMask_(ak.NSViewMinXMargin | ak.NSViewMaxYMargin)
    show_replace_matches.setTarget_(obj)
    show_replace_matches.setAction_("panelCountReplaceText:")

    find_next = obj.find_next = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(387, 37, 109, 32))
    find_next.setTitle_("Next")
    find_next.setBezelStyle_(ak.NSRoundedBezelStyle)
    find_next.setAutoresizingMask_(ak.NSViewMinXMargin | ak.NSViewMinYMargin)
    find_next.setTarget_(obj)
    find_next.setAction_("panelFindNext:")
    window.setDefaultButtonCell_(find_next.cell())

    find_prev = obj.find_prev = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(387, 5, 109, 32))
    find_prev.setTitle_("Previous")
    find_prev.setBezelStyle_(ak.NSRoundedBezelStyle)
    find_prev.setAutoresizingMask_(ak.NSViewMinXMargin | ak.NSViewMinYMargin)
    find_prev.setTarget_(obj)
    find_prev.setAction_("panelFindPrevious:")

    replace_one = obj.replace_one = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(387, 113, 109, 32))
    replace_one.setTitle_("Replace")
    replace_one.setBezelStyle_(ak.NSRoundedBezelStyle)
    replace_one.setAutoresizingMask_(ak.NSViewMinXMargin | ak.NSViewMinYMargin)
    replace_one.setTarget_(obj)
    replace_one.setAction_("panelReplace:")

    replace_all = obj.replace_all = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(387, 81, 109, 32))
    replace_all.setTitle_("Replace All")
    replace_all.setBezelStyle_(ak.NSRoundedBezelStyle)
    replace_all.setAutoresizingMask_(ak.NSViewMinXMargin | ak.NSViewMinYMargin)
    replace_all.setTarget_(obj)
    replace_all.setAction_("panelReplaceAll:")

    replace_in_selection = obj.replace_in_selection = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(387, 49, 109, 32))
    replace_in_selection.setTitle_("In Selection")
    replace_in_selection.setBezelStyle_(ak.NSRoundedBezelStyle)
    replace_in_selection.setAutoresizingMask_(ak.NSViewMinXMargin | ak.NSViewMinYMargin)
    replace_in_selection.setTarget_(obj)
    replace_in_selection.setAction_("panelReplaceAllInSelection:")

    cancel = obj.cancel = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(387, 12, 109, 32))
    cancel.setTitle_("Cancel")
    cancel.setBezelStyle_(ak.NSRoundedBezelStyle)
    cancel.setAutoresizingMask_(ak.NSViewMinXMargin | ak.NSViewMaxYMargin)
    cancel.setTarget_(obj)
    cancel.setAction_("performClose:")

    icase_checkbox = obj.icase_checkbox = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(18, 61, 151, 18))
    icase_checkbox.setTitle_("Ignore Case")
    icase_checkbox.setButtonType_(ak.NSSwitchButton)
    icase_checkbox.setState_(ak.NSOffState)
    icase_checkbox.setAutoresizingMask_(ak.NSViewMaxXMargin | ak.NSViewMaxYMargin)
    icase_checkbox.bind_toObject_withKeyPath_options_(
        "value", obj, "options.ignore_case", {
            ak.NSRaisesForNotApplicableKeysBindingOption: 1,
        })

    match_word_checkbox = obj.match_word_checkbox = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(18, 41, 151, 18))
    match_word_checkbox.setTitle_("Match Entire Word")
    match_word_checkbox.setButtonType_(ak.NSSwitchButton)
    match_word_checkbox.setState_(ak.NSOffState)
    match_word_checkbox.setAutoresizingMask_(ak.NSViewMaxXMargin | ak.NSViewMaxYMargin)
    match_word_checkbox.bind_toObject_withKeyPath_options_(
        "value", obj, "options.match_entire_word", {
            ak.NSRaisesForNotApplicableKeysBindingOption: 1,
        })

    regex_checkbox = obj.regex_checkbox = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(18, 21, 151, 18))
    regex_checkbox.setTitle_("Regular Expression")
    regex_checkbox.setButtonType_(ak.NSSwitchButton)
    regex_checkbox.setState_(ak.NSOffState)
    regex_checkbox.setAutoresizingMask_(ak.NSViewMaxXMargin | ak.NSViewMaxYMargin)
    regex_checkbox.bind_toObject_withKeyPath_options_(
        "value", obj, "options.regular_expression", {
            ak.NSRaisesForNotApplicableKeysBindingOption: 1,
        })

    regex_help = obj.regex_help = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(166, 17, 21, 23))
    regex_help.setAlternateTitle_("Regular Expression Help")
    regex_help.setTitle_("")
    regex_help.setBezelStyle_(ak.NSHelpButtonBezelStyle)
    regex_help.setAutoresizingMask_(ak.NSViewMaxXMargin | ak.NSViewMaxYMargin)
    regex_help.setTarget_(obj)
    regex_help.setAction_("regexHelp:")

    wrap_checkbox = obj.wrap_checkbox = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(204, 61, 164, 18))
    wrap_checkbox.setTitle_("Wrap Around")
    wrap_checkbox.setButtonType_(ak.NSSwitchButton)
    wrap_checkbox.setState_(ak.NSOffState)
    wrap_checkbox.setAutoresizingMask_(ak.NSViewMaxXMargin | ak.NSViewMaxYMargin)
    wrap_checkbox.bind_toObject_withKeyPath_options_(
        "value", obj, "options.wrap_around", {
            ak.NSRaisesForNotApplicableKeysBindingOption: 1,
        })

    pyrep_checkbox = obj.pyrep_checkbox = ak.NSButton.alloc().initWithFrame_(
        ak.NSMakeRect(204, 41, 164, 18))
    pyrep_checkbox.setTitle_("Python Replace")
    pyrep_checkbox.setButtonType_(ak.NSSwitchButton)
    pyrep_checkbox.setState_(ak.NSOffState)
    pyrep_checkbox.setAutoresizingMask_(ak.NSViewMaxXMargin | ak.NSViewMaxYMargin)
    pyrep_checkbox.bind_toObject_withKeyPath_options_(
        "value", obj, "options.python_replace", {
            ak.NSRaisesForNotApplicableKeysBindingOption: 1,
        })

    status_label = obj.status_label = ak.NSTextField.alloc().initWithFrame_(
        ak.NSMakeRect(203, 18, 166, 17))
    status_label.setAutoresizingMask_(ak.NSViewWidthSizable | ak.NSViewMaxYMargin)
    status_label.setBackgroundColor_(
        ak.NSColor.colorWithCatalogName_colorName_("System", "controlColor"))
    status_label.setBezeled_(False)
    status_label.setDrawsBackground_(False)
    status_label.setEditable_(False)
    status_label.setFont_(ak.NSFont.fontWithName_size_("Monaco", 12))
    status_label.setLineBreakMode_(ak.NSLineBreakByWordWrapping)
    status_label.setUsesSingleLineMode_(False)

    top = ak.NSView.alloc().initWithFrame_(ak.NSMakeRect(0, 141, 510, 87))
    top.setAutoresizingMask_(
        ak.NSViewMinXMargin | ak.NSViewMaxXMargin | ak.NSViewMinYMargin |
        ak.NSViewWidthSizable | ak.NSViewHeightSizable)

    top.addSubview_(find_text)
    top.addSubview_(recents_menu)
    top.addSubview_(show_find_matches)

    top.addSubview_(find_next)
    top.addSubview_(find_prev)

    bot = ak.NSView.alloc().initWithFrame_(ak.NSMakeRect(0, 0, 510, 141))
    bot.setAutoresizingMask_(
        ak.NSViewMinXMargin | ak.NSViewMaxXMargin | ak.NSViewMaxYMargin |
        ak.NSViewWidthSizable | ak.NSViewHeightSizable)

    bot.addSubview_(replace_text)
    bot.addSubview_(show_replace_matches)

    bot.addSubview_(icase_checkbox)
    bot.addSubview_(match_word_checkbox)
    bot.addSubview_(regex_checkbox)
    bot.addSubview_(regex_help)
    bot.addSubview_(wrap_checkbox)
    bot.addSubview_(pyrep_checkbox)
    bot.addSubview_(status_label)

    bot.addSubview_(replace_one)
    bot.addSubview_(replace_all)
    bot.addSubview_(replace_in_selection)
    bot.addSubview_(cancel)

    main = window.contentView()
    main.addSubview_(top)
    main.addSubview_(bot)

    return window
