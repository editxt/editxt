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
import os

from editxt.events import eventize
from editxt.util import WeakProperty
from editxt.test.util import test_app

log = logging.getLogger(__name__)


class WindowController(object):

    window_ = WeakProperty()
    frame_string = ""
    splitter_pos = 0
    properties_hidden = False

    def __init__(self, window):
        self.window_ = window
        self.prompts = []
        self.selected_items = []

    def document(self):
        return None

    def window(self):
        return None

    def setup_current_editor(self, editor):
        from editxt.editor import Editor
        self.selected_items = [editor]
        return isinstance(editor, Editor)

    def is_current_view(self, editor_main_view):
        if editor_main_view is None:
            return False
        return self.selected_items and \
            self.selected_items[0].main_view is editor_main_view

    def undo_manager(self):
        return self.window_.undo_manager()

    def on_dirty_status_changed(self, editor, dirty):
        pass

    def open_documents(self, directory, filename, open_paths_callback):
        if directory == os.path.expanduser("~"):
            name = "~"
        elif os.path.isabs(directory):
            name = directory[len(test_app(self.window_.app).tmp):]
        self.prompts.append("open %s" % name)
        if "cancel" not in name:
            log.info("open %s", directory)
            open_paths_callback([os.path.join(directory, "file.txt")])

    def save_document_as(self, directory, filename, save_with_path):
        self.prompts.append("save " + filename)
        if directory is not None and filename.endswith(".save"):
            log.info("save '%s' to %s", filename, directory)
        else:
            if directory is None:
                reason = "cannot save to relative path"
            else:
                reason = "filename does not end with '.save'"
            log.info("save '%s' canceled (%s)", filename, reason)
            directory = None
        save_with_path(directory)

    def prompt_to_close(self, file_path, save_discard_or_cancel, save_as):
        self.prompts.append("close " + os.path.basename(file_path))
        if file_path.endswith(".save"):
            action = "save" + ("..." if save_as else "")
            response = True
        elif file_path.endswith(".dont_save"):
            action = "don't save"
            response = False
        else:
            action = "cancel"
            response = None
        log.info("prompt to close %s -> %s", file_path, action)
        save_discard_or_cancel(response)

    # XXX the following are still Objective-C-ish
    # TODO create Pythonic API for these functions

    def setShouldCascadeWindows_(self, value):
        pass

    def windowDidBecomeKey_(self, window):
        raise NotImplementedError

    def showWindow_(self, sender):
        pass


class OutputPanel(object):

    handle_close = None

    class events:
        close = eventize.attr("handle_close")

    def __init__(self, command, text, rect=None):
        self.command = command
        self.text = text
        self.rect = rect
        eventize(self)

    def is_waiting(self, waiting=None):
        if waiting is not None:
            self.waiting = waiting
        return getattr(self, "waiting", False)

    def show(self, window):
        pass
