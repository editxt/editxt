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
import editxt.platform.mac.views as mac_views
from editxt.constants import INFO
from editxt.events import eventize
from editxt.platform.mac.views import *
from editxt.platform.mac.views.menu import Menu, MenuItem

class ListView(object):
    """A test list view"""

    events = mac_views.ListView.events

    def __init__(self, items, colspec):
        eventize(self)
        self.items = items
        self.view = None
        self.frame = None
        self.scroll = None
        self.title = None
        self.selected_row = -1
        class delegate:
            on_selection_changed = None
            def setup_double_click(callback):
                pass
        self.delegate = delegate

    def select(self, index):
        self.selected_row = index if index is not None else -1
        self.delegate.on_selection_changed(
            [] if self.selected_row < 0 else [self.items[self.selected_row]])

    def become_subview_of(self, view):
        self.parent_view = view


class CommandView(object):
    """Test command view"""

    class KEYS:
        """The values of these constants are opaque

        Use ``editxt.platform.views.CommandView.KEYS`` to reference them
        """
        ESC = "Esc"
        TAB = "Tab"
        BACK_TAB = "BackTab"
        UP = "Up"
        DOWN = "Down"
        ENTER = "Enter"
        SELECTION_CHANGED = "SelectionChanged"

    def __init__(self):
        from editxt.textcommand import AutoCompleteMenu
        self.completions = AutoCompleteMenu()
        self.completions.on.selection_changed(self.propose_completion)
        self.command = None
        self.output_text = ""
        self._last_completions = [None]

    def activate(self, command_bar, text, select=False):
        self.command = command_bar
        self.command_text = text
        if select:
            self.command_text_selected_range = (0, len(text))
        else:
            self.command_text_selected_range = (len(text), 0)

    def replace_command_text_range(self, range, text):
        before = self.command_text[:range[0]]
        after = self.command_text[sum(range):]
        self.command_text = before + text + after

    def propose_completion(self, items):
        self.command.propose_completion(self, items)

    def message(self, message, msg_type=INFO):
        self.output_text = message

    def is_waiting(self, waiting=None):
        if waiting is not None:
            self.waiting = waiting
        return getattr(self, "waiting", False)

    def deactivate(self):
        if self.command is not None:
            self.completions.items = []
            self.command_text = None
            #self.command.reset()
        self.command = None

    def dismiss(self):
        self.output_text = ""
        self.deactivate()
        self.is_waiting(False)

    def should_resize(self):
        pass
