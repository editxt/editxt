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
from editxt.editor import Editor
from editxt.document import DocumentController, TextDocument
from editxt.platform.kvo import KVOList, KVOProxy


log = logging.getLogger(__name__)


class Project(object):

    id = None # will be overwritten (put here for type api compliance for testing)
    window = WeakProperty()
    document = None
    soft_wrap = None
    indent_mode = None
    indent_size = None
    newline_mode = None
    syntaxdef = None
    character_encoding = None
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
        self.editors = KVOList()
        self.closing = False
        if serial is not None:
            self._deserialize(serial)
        self.reset_serial_cache()

    @property
    def summary_info(self):
        """Returns a 4-tuple: ``icon, name, is_dirty, self``"""
        return (None, self.name, self.is_dirty, self)

    def serialize(self):
        data = {"expanded": self.expanded}
        if self.name != const.UNTITLED_PROJECT_NAME:
            data["name"] = str(self.name) # HACK dump_yaml doesn't like pyobjc_unicode
        states = (d.edit_state for d in self.editors)
        documents = [s for s in states if "path" in s]
        if documents:
            data["documents"] = documents
        return data

    def _deserialize(self, serial):
        if "path" in serial:
            self.path = serial["path"]
            plistData = fn.NSData.dataWithContentsOfFile_(self.path)
            serial, format, error = fn.NSPropertyListSerialization. \
                propertyListFromData_mutabilityOption_format_errorDescription_(
                    plistData, fn.NSPropertyListImmutable, None, None)
        if serial:
            if "name" in serial:
                self.name = serial["name"]
            for doc_state in serial.get("documents", []):
                try:
                    self.create_editor_with_state(doc_state)
                except Exception:
                    log.warn("cannot open document: %r" % (doc_state,))
            self.expanded = serial.get("expanded", True)
        if not self.editors:
            self.create_editor()

    def reset_serial_cache(self):
        self.serial_cache = self.serialize()

    def save(self):
        if self.serial_cache != self.serialize():
            if self.path is not None:
                self.save_with_path(self.path)
            self.window.app.save_window_states()
            self.reset_serial_cache()

    def save_with_path(self, path):
        raise NotImplementedError
        data = fn.NSMutableDictionary.alloc().init()
        data.update(self.serialize())
        data.writeToFile_atomically_(path, True)

    def dirty_editors(self):
        return (e for e in self.editors if e.is_dirty)

    def icon(self):
        return None

    def can_rename(self):
        return self.path is None

    @property
    def file_path(self):
        return self.path

    def editor_for_path(self, path):
        """Get the editor for the given path

        Returns None if this project does not have a editor with path
        """
        raise NotImplementedError

    def create_editor(self):
        document = self.window.app.document_with_path(None)
        editor = Editor(self, document=document)
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
            index = len(self.editors)
        is_move = action == const.MOVE
        is_copy = action == const.COPY
        focus = None
        inserted = []
        for item in items:
            inserted.append(item)
            if isinstance(item, Editor):
                editor, item = item, item.document
            else:
                if not isinstance(item, TextDocument):
                    raise ValueError("invalid item: {!r}".format(item))
                editor = self.find_editor_with_document(item)
            if is_move and editor is not None:
                if editor.project is self:
                    vindex = self.editors.index(editor)
                    if vindex in [index - 1, index]:
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
                    continue
            assert editor.project is self, (editor, editor.project, self)
            self.editors.insert(index, editor)
            focus = editor
            index += 1
        return inserted, focus

    def find_editor_with_document(self, doc):
        for editor in self.editors:
            if editor.document is doc:
                return editor
        return None

    def set_main_view_of_window(self, view, window):
        pass # TODO add project-specific view?

    def perform_close(self):
        from editxt.application import DocumentSavingDelegate
        window = self.window
        app = window.app
        if app.find_windows_with_project(self) == [window]:
            def dirty_docs():
                for editor in self.dirty_editors():
                    itr = app.iter_windows_with_editor_of_document(editor.document)
                    if list(itr) == [window]:
                        yield editor
                yield self
            def callback(should_close):
                if should_close:
                    window.discard_and_focus_recent(self)
            saver = DocumentSavingDelegate.alloc().\
                init_callback_(dirty_docs(), callback)
            saver.save_next_document()
        else:
            window.discard_and_focus_recent(self)

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

    def __repr__(self):
        return '<%s 0x%x name=%s>' % (type(self).__name__, id(self), self.name)
