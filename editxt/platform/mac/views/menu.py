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
import logging
from itertools import count

import AppKit as ak
import Foundation as fn
from objc import Category, IBOutlet, python_method, super

from editxt.util import parse_hotkey, representedObject, WeakProperty

log = logging.getLogger(__name__)


class Menu:

    def __init__(self, items):
        self.items = items
        self.target = MenuTarget.alloc().init()

    def make_native_menu(self, title=""):
        menu = ak.NSMenu.alloc().initWithTitle_(title)
        for item in self.items:
            menu.addItem_(item.make_native_item(self.target))
        return menu


class MenuItem:

    def __init__(self, title, callback, hotkey=None, *, is_enabled=None):
        self.title = title
        self.callback = callback
        self.hotkey = hotkey
        self.is_enabled = is_enabled

    def make_native_item(self, target):
        tag = target.add_callback(self.callback)
        key, mask = parse_hotkey(self.hotkey or "")
        item = ak.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            self.title,
            target.action_selector,
            key,
        )
        item.setKeyEquivalentModifierMask_(mask)
        item.setTag_(tag)
        item.setTarget_(target)
        return item


class MenuTarget(ak.NSObject):

    action_selector = b"invokeItemCallbackForMenuItem:"
    current_object = WeakProperty()

    def init(self):
        self.map = {}
        self.tags = count(1)
        return self

    @python_method
    def add_callback(self, callback):
        tag = next(self.tags)
        self.map[tag] = callback
        return tag

    def invokeItemCallbackForMenuItem_(self, item):
        self.map[item.tag()](self.current_object)
