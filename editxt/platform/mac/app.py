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
import objc
import AppKit as ak
import Foundation as fn


class AppDelegate(ak.NSObject):

    app = None # set by editxt.platform.mac.main.run
    textMenu = objc.IBOutlet()
    textEditCommandsMenu = objc.IBOutlet()

    def openPath_(self, sender):
        self.app.open_path_dialog()

    def closeCurrentDocument_(self, sender):
        self.app.close_current_document()

    def closeCurrentProject_(self, sender):
        raise NotImplementedError()

    def saveProjectAs_(self, sender):
        raise NotImplementedError()

    def newDocument_(self, sender):
        self.app.new_document()

    def newProject_(self, sender):
        self.app.new_project()

    def newWindow_(self, sender):
        self.app.create_window()

    def openConfigFile_(self, sender):
        self.app.open_config_file()

    def openErrorLog_(self, sender):
        self.app.open_error_log()

    def applicationWillFinishLaunching_(self, app):
        self.app.application_will_finish_launching(app, self)

    def application_openFiles_(self, app, filenames):
        self.app.open_documents_with_paths(filenames)
        app.replyToOpenOrPrint_(0) # success

    def applicationShouldOpenUntitledFile_(self, app):
        return False

    def applicationShouldTerminate_(self, app):
        def callback(answer):
            app.replyToApplicationShouldTerminate_(answer)
        answer = self.app.should_terminate(callback)
        return ak.NSTerminateLater if answer is callback else answer

    def applicationWillTerminate_(self, notification):
        self.app.will_terminate()


def add_recent_document(path):
    """Add file to File > Open Recent menu"""
    url = fn.NSURL.fileURLWithPath_(path)
    ak.NSDocumentController.sharedDocumentController() \
        .noteNewRecentDocumentURL_(url)
