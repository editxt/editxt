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

import AppKit as ak
import Foundation as fn

import editxt.constants as const
from editxt.datatypes import WeakProperty
from editxt.editor import Editor, CommandSubject
from editxt.document import DocumentController, TextDocument
from editxt.platform.app import add_recent_document
from editxt.platform.document import add_command_view
from editxt.platform.kvo import KVOList, KVOProxy
from editxt.undo import UndoManager
from editxt.platform.views import ListView


log = logging.getLogger(__name__)


class Project(CommandSubject):

    window = WeakProperty()
    document = None
    soft_wrap = None
    indent_mode = None
    indent_size = None
    newline_mode = None
    syntaxdef = None
    character_encoding = None
    text_view = None
    is_leaf = False

    @staticmethod
    def is_project_path(path):
        return path.endswith("." + const.PROJECT_EXT)

    def __init__(self, window, *, serial=None):
        self.id = next(DocumentController.id_gen)
        self.window = window
        self.proxy = KVOProxy(self)
        self.name = const.UNTITLED_PROJECT_NAME
        self.path = None
        self.expanded = True
        self.is_dirty = False
        self.undo_manager = UndoManager()
        self.editors = KVOList()
        self.recent = KVOList()
        self.main_view = None
        self.closing = False
        if serial is not None:
            self._deserialize(serial)
        self.reset_serial_cache()

    def serialize(self):
        data = {"expanded": self.expanded}
        if self.name != const.UNTITLED_PROJECT_NAME:
            data["name"] = str(self.name) # HACK dump_yaml doesn't like pyobjc_unicode
        if self.path is not None:
            data["path"] = self.path
        documents = [d.edit_state for d in self.editors]
        if documents:
            data["documents"] = documents
        if self.recent:
            data["recent"] = [str(r.path) for r in self.recent]
        return data

    def _deserialize(self, serial):
        if "path" in serial:
            self.path = serial["path"]
        if serial:
            if "name" in serial:
                self.name = serial["name"]
            for doc_state in serial.get("documents", []):
                try:
                    self.create_editor_with_state(doc_state)
                except Exception:
                    log.warn("cannot open document: %r" % (doc_state,))
            self.expanded = serial.get("expanded", True)
            if "recent" in serial:
                self.recent.extend(Recent(path) for path in serial["recent"])
        if not self.editors:
            self.create_editor()

    def reset_serial_cache(self):
        self.serial_cache = self.serialize()

    def save(self):
        if self.serial_cache != self.serialize():
            #if self.path is not None:
            #    self.save_with_path(self.path)
            self.app.save_window_states()
            self.reset_serial_cache()

    def save_with_path(self, path):
        raise NotImplementedError
        data = fn.NSMutableDictionary.alloc().init()
        data.update(self.serialize())
        data.writeToFile_atomically_(path, True)

    def should_close(self, callback):
        self.save()
        callback(True)

    def dirty_editors(self):
        return (e for e in self.editors if e.is_dirty)

    def icon(self):
        return None

    def can_rename(self):
        return True

    @property
    def app(self):
        return self.window.app

    @property
    def project(self):
        return self

    @property
    def file_path(self):
        return self.path

    def short_path(self, name=True):
        return self.path or ""

    def dirname(self):
        """Return a tuple: (directory, filename or None)"""
        if self.path:
            assert os.path.isabs(self.path), self.path
            return self.path
        return None

    def editor_for_path(self, path):
        """Get the editor for the given path

        Returns None if this project does not have a editor with path
        """
        raise NotImplementedError

    def create_editor(self, path=None):
        editor = Editor(self, path=path)
        self.insert_items([editor])
        return editor

    def create_editor_with_state(self, state):
        editor = Editor(self, state=state)
        self.insert_items([editor])
        return editor

    def insert_items(self, items, index=-1, action=None):
        """Insert items into project, creating editors as necessary

        :param items: An iterable yielding editors and/or documents.
        :param index: The index in this project's list of editors at
            which items should be inserted.
        :param action: What to do with items that already exist in this
            project:

            - None : insert new item(s), ignore existing item(s).
            - MOVE : move existing item(s) to index.
            - COPY : copy item(s) to index.

            An item is considered to be "existing" if there is another
            editor with the same path.
        :returns: A tuple: list of editors for the items that were
        inserted and the editor that should receive focus.
        """
        if index < 0:
            if self.window is not None:
                current = self.window.current_editor
                if current is not None:
                    try:
                        index = self.editors.index(current) + 1
                    except ValueError:
                        pass
            if index < 0:
                index = len(self.editors)
        is_move = action == const.MOVE
        is_copy = action == const.COPY
        focus = None
        inserted = []
        for item in items:
            if isinstance(item, Editor):
                editor, item = item, item.document
            else:
                if not isinstance(item, TextDocument):
                    raise ValueError("invalid item: {!r}".format(item))
                editor = next(self.iter_editors_of_document(item), None)
            if is_move and editor is not None:
                if editor.project is self:
                    vindex = self.editors.index(editor)
                    if vindex in [index - 1, index]:
                        # TODO why not set `focus = editor`?
                        inserted.append(editor)
                        continue
                    if vindex - index <= 0:
                        index -= 1
                    del self.editors[vindex]
                else:
                    editor.project = self
            elif is_copy or editor is None or editor.project is not self:
                editor = Editor(self, document=item)
            else:
                assert editor.project is self, (editor, editor.project)
                if editor in self.editors:
                    focus = editor
                    inserted.append(editor)
                    continue
            assert editor.project is self, (editor, editor.project, self)
            self._discard_recent(editor.file_path)
            self.editors.insert(index, editor)
            inserted.append(editor)
            focus = editor
            index += 1
        return inserted, focus

    def remove(self, editor):
        """Remove an editor from this project

        Adds the document to this projects recent documents. Does
        nothing if the editor is not in this project.
        """
        if not self.closing and editor in self.editors:
            update_current = editor in self.window.selected_items or \
                             not self.window.selected_items
            with self.window.suspend_recent_updates(update_current):
                self.editors.remove(editor)
                assert editor not in self.editors, (editor, self.editors)
                self._add_recent(editor.document)

    def iter_editors_of_document(self, document):
        for editor in self.editors:
            if editor.document is document:
                yield editor

    def _add_recent(self, document):
        """Add document to this projects recent documents

        Does nothing if the document does not have an absolute path or there are
        other editors with the same document in the project.
        """
        if os.path.isabs(document.file_path):
            itr = self.iter_editors_of_document(document)
            if next(itr, None) is None:
                self._discard_recent(document.file_path)
                self.recent.insert(0, Recent(document.file_path))
                add_recent_document(document.file_path)
                # TODO make limit customizable?
                if len(self.recent) > 20:
                    del self.recent[20:]

    def _discard_recent(self, path):
        """Discard recent items matching path"""
        for item in reversed(list(self.recent)):
            if item.path == path:
                self.recent.remove(item)
                item.close()

    def set_main_view_of_window(self, view, window):
        if self.main_view is None:
            def open_recent(item):
                self.window.current_editor = self.create_editor(item.path)
            self.listview = ListView(self.recent, RECENT_COLSPEC)
            self.listview.on.double_click(open_recent)
            self.main_view = add_command_view(
                self.listview.scroll, view.bounds(), self)
            self.command_view = self.main_view.bottom
        self.main_view.become_subview_of(view, focus=self.listview.view)

    def focus(self):
        if self is not self.window.current_editor:
            self.window.current_editor = self

    def interactive_close(self, do_close):
        def dirty_editors():
            def other_project_has(document):
                return any(editor.project is not self
                           for editor in app.iter_editors_of_document(document))
            app = self.app
            seen = set()
            for editor in self.editors:
                if editor.document in seen:
                    continue
                seen.add(editor.document)
                if editor.is_dirty and not other_project_has(editor.document):
                    yield editor
        def callback(should_close):
            if should_close:
                do_close()
        self.app.async_interactive_close(dirty_editors(), callback)

    def close(self):
        self.closing = True
        try:
            for editor in list(self.editors):
                editor.close()
            #self.editors.setItems_([])
        finally:
            self.closing = False
        self.window = None
        self.editors = None
        self.proxy = None
        self.main_view = None
        self.command_view = None

    def __repr__(self):
        return '<%s 0x%x name=%s>' % (type(self).__name__, id(self), self.name)


RECENT_COLSPEC = [
    {"name": "path", "title": "Recent Files"}
]


class Recent(object):

    def __init__(self, path):
        self.path = path
        self.proxy = KVOProxy(self)

    def __repr__(self):
        return "{}({!r})".format(type(self).__name__, self.path)

    @property
    def file_path(self):
        return self.path

    def close(self):
        self.proxy = None
