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

from editxt.platform.views import BUTTON_STATE_NORMAL
from editxt.util import WeakProperty

log = logging.getLogger(__name__)


class WindowController(object):

    window_ = WeakProperty()

    def __init__(self, window):
        self.window_ = window
        self.current_editor = None

    def document(self):
        return None

    def window(self):
        return None

    def undo_manager(self):
        return self.window_.undo_manager()

    # XXX the following are still Objective-C-ish
    # TODO create Pythonic API for these functions

    def setDocument_(self, document):
        pass

    def setShouldCascadeWindows_(self, value):
        pass

    def setShouldCloseDocument_(self, value):
        pass

    def windowDidBecomeKey_(self, window):
        raise NotImplementedError
