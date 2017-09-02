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
from objc import super

log = logging.getLogger(__name__)


class Caller(fn.NSObject):

    def __new__(cls, callback):
        self = cls.alloc().init()
        self.callback = callback
        return self

    @objc.typedSelector(b'v@:@ii')
    def alertDidEnd_returnCode_contextInfo_(self, alert, code, context):
        self.callback(code, lambda:alert.window().orderOut_(self))


class Alert(ak.NSAlert):
    """Python-friendly alert class

    WARNING it is not safe to invoke beginSheet...withCallback_() multiple
    times simultaneously on a single Alert instance.
    """

    def beginSheetModalForWindow_withCallback_(self, window, callback):
        self.caller = Caller(callback)
        self.beginSheetModalForWindow_modalDelegate_didEndSelector_contextInfo_(
            window, self.caller, "alertDidEnd:returnCode:contextInfo:", 0)
