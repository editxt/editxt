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
from editxt.document import TextDocumentView, TextDocument, doc_id_gen
from editxt.platform.kvo import KVOList, KVOProxy


log = logging.getLogger(__name__)


class Project(object):

    id = None # will be overwritten (put here for type api compliance for testing)
    editor = WeakProperty()
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

    def __init__(self, editor, *, serial=None):
        self.id = next(doc_id_gen)
        self.editor = editor
        self.proxy = KVOProxy(self)
        self.name = const.UNTITLED_PROJECT_NAME
        self.path = None
        self.expanded = True
        self.is_dirty = False
        self.documents = KVOList()
        self.closing = False
        if serial is not None:
            self._deserialize(serial)
        self.reset_serial_cache()

    def serialize(self):
        data = {"expanded": self.expanded}
        if self.name != const.UNTITLED_PROJECT_NAME:
            data["name"] = str(self.name) # HACK dump_yaml doesn't like pyobjc_unicode
        states = (d.edit_state for d in self.documents)
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
                    self.create_document_view_with_state(doc_state)
                except Exception:
                    log.warn("cannot open document: %r" % (doc_state,))
            self.expanded = serial.get("expanded", True)
        if not self.documents:
            self.create_document_view()

    def reset_serial_cache(self):
        self.serial_cache = self.serialize()

    def save(self):
        if self.serial_cache != self.serialize():
            if self.path is not None:
                self.save_with_path(self.path)
            self.editor.app.save_editor_states()
            self.reset_serial_cache()

    def save_with_path(self, path):
        raise NotImplementedError
        data = fn.NSMutableDictionary.alloc().init()
        data.update(self.serialize())
        data.writeToFile_atomically_(path, True)

    def dirty_documents(self):
        return (doc for doc in self.documents if doc.is_dirty)

    def icon(self):
        return None

    def can_rename(self):
        return self.path is None

    @property
    def file_path(self):
        return self.path

    def document_view_for_path(self, path):
        """Get the document view for the given path

        Returns None if this project does not have a document with path
        """
        raise NotImplementedError

    def document_view_for_document(self, doc): # is this needed?
        """Get the document view for the given document

        Returns None if this project does not have a view of doc.
        """
        # TODO test
        if doc is not None:
            for dv in self.documents:
                if dv.document is doc:
                    return dv
        return None

    def create_document_view(self):
        dc = ak.NSDocumentController.sharedDocumentController()
        doc, err = dc.makeUntitledDocumentOfType_error_(const.TEXT_DOCUMENT, None)
        if err:
            raise Exception(err)
        dc.addDocument_(doc)
        dv = TextDocumentView(self, document=doc)
        self.append_document_view(dv)
        return dv

    def create_document_view_with_state(self, state):
        dv = TextDocumentView(self, state=state)
        self.append_document_view(dv)
        return dv

    def append_document_view(self, view):
        """Add view to the end of this projects document views"""
        self.documents.append(view)
        view.project = self

    def insert_document_view(self, index, view):
        """Insert view at index in this projects document views
        """
        self.documents.insert(index, view)
        view.project = self

    def remove_document_view(self, doc_view):
        """Remove view from this projects document views

        Does nothing if the view does not belong to this project.
        """
        if doc_view in self.documents:
            self.documents.remove(doc_view)
            doc_view.project = None
            #self.is_dirty = True

    def find_view_with_document(self, doc):
        for view in self.documents:
            if view.document is doc:
                return view
        return None

    def set_main_view_of_window(self, view, window):
        pass # TODO add project-specific view?

    def perform_close(self):
        from editxt.application import DocumentSavingDelegate
        editor = self.editor
        app = editor.app
        if app.find_editors_with_project(self) == [editor]:
            def dirty_docs():
                for dv in self.dirty_documents():
                    itr = app.iter_editors_with_view_of_document(dv.document)
                    if list(itr) == [editor]:
                        yield dv
                yield self
            def callback(should_close):
                if should_close:
                    editor.discard_and_focus_recent(self)
            saver = DocumentSavingDelegate.alloc().\
                init_callback_(dirty_docs(), callback)
            saver.save_next_document()
        else:
            editor.discard_and_focus_recent(self)

    def close(self):
        self.closing = True
        try:
            for dv in list(self.documents):
                dv.close()
            #self.documents.setItems_([])
        finally:
            self.closing = False
        self.editor = None
        self.documents = None
        self.proxy = None

    def __repr__(self):
        return '<%s 0x%x name=%s>' % (type(self).__name__, id(self), self.name)
