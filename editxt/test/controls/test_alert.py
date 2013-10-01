# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
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
import os

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import eq_
import AppKit as ak
import Foundation as fn

from editxt.controls.alert import Alert, Caller

log = logging.getLogger(__name__)


def test_Caller_alertDidEnd_returnCode_contextInfo_signature():
    assert Caller.alertDidEnd_returnCode_contextInfo_.signature == 'v@:@ii'

def test_beginSheetModalForWindow_withCallback_():
    m = Mocker()
    alert = Alert.alloc().init()
    beginSheet = m.method(alert.beginSheetModalForWindow_modalDelegate_didEndSelector_contextInfo_)
    callback = m.mock()
    win = m.mock(ak.NSWindow)
    def do(win, dgt, sel, context):
        dgt.alertDidEnd_returnCode_contextInfo_(alert, 42, 0)
    expect(beginSheet(win, ANY, "alertDidEnd:returnCode:contextInfo:", 0)).call(do)
    callback(42)
    with m:
        alert.beginSheetModalForWindow_withCallback_(win, callback)
