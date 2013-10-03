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
import time

import objc
import AppKit as ak
import Foundation as fn

log = logging.getLogger(__name__)


class EditorWindow(ak.NSWindow):
    """NSWindow subclass that provides mouseMoved events to registered subviews"""

    @property
    def mouse_moved_responders(self):
        try:
            mmr = self._mouse_moved_responders
        except AttributeError:
            mmr = self._mouse_moved_responders = set()
        return mmr

    def add_mouse_moved_responder(self, responder):
        self.mouse_moved_responders.add(responder)
        self.setAcceptsMouseMovedEvents_(True)

    def remove_mouse_moved_responder(self, responder):
        self.mouse_moved_responders.discard(responder)
        if not self.mouse_moved_responders:
            self.setAcceptsMouseMovedEvents_(False)

    def mouseMoved_(self, event):
        super(EditorWindow, self).mouseMoved_(event)
        for responder in self.mouse_moved_responders:
            if responder is not self.firstResponder():
                responder.mouseMoved_(event)

    def undoManager(self):
        return self.windowController().undo_manager()

