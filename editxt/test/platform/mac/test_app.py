# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2014 Daniel Miller <millerdev@gmail.com>
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

import AppKit as ak

from mocker import Mocker, expect, ANY, MATCH

import editxt.platform.mac.app as mod
from editxt.application import Application

from editxt.test.util import TestConfig, eq_, replattr, test_app

log = logging.getLogger(__name__)


def test_AppDelegate_actions():
    def test(action, app_method):
        delegate = mod.AppDelegate.alloc().init()
        m = Mocker()
        delegate.app = app = m.mock(Application)
        getattr(app, app_method)()
        with m:
            getattr(delegate, action)(None)
    
    yield test, "newWindow_", "create_window"
    yield test, "newProject_", "new_project"
    yield test, "newDocument_", "new_document"
    yield test, "openConfigFile_", "open_config_file"
    yield test, "openErrorLog_", "open_error_log"
    yield test, "openPath_", "open_path_dialog"
    yield test, "closeCurrentDocument_", "close_current_document"

    #yield test, "closeCurrentProject_", "close_current_project"
    #yield test, "saveProjectAs_", "save_project_as"
    #yield test, "togglePropertiesPane_", "close_current_document"

def test_applicationShouldOpenUntitledFile_():
    delegate = mod.AppDelegate.alloc().init()
    assert not delegate.applicationShouldOpenUntitledFile_(None)

def test_applicationWillFinishLaunching_():
    delegate = mod.AppDelegate.alloc().init()
    m = Mocker()
    delegate.app = app = m.mock(Application)
    nsapp = m.mock(ak.NSApplication)
    app.application_will_finish_launching(nsapp, delegate)
    with m:
        delegate.applicationWillFinishLaunching_(nsapp)

def test_applicationWillTerminate():
    delegate = mod.AppDelegate.alloc().init()
    m = Mocker()
    delegate.app = app = m.mock(Application)
    notif = m.mock() # ak.NSApplicationWillTerminateNotification
    nsapp = m.mock(ak.NSApplication)
    app.app_will_terminate(notif.object() >> nsapp)
    with m:
        delegate.applicationWillTerminate_(notif)
