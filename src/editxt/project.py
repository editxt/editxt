# -*- coding: utf-8 -*-
# EditXT
# Copyright (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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
import codecs
import logging
import os
import sys
from itertools import count

from ConfigParser import SafeConfigParser
from StringIO import StringIO

import objc
from AppKit import *
from Foundation import *
#from NDAlias import NDAlias

import editxt.constants as const
from editxt import app
from editxt.document import TextDocumentView, TextDocument, doc_id_gen
from editxt.util import KVOList, untested


log = logging.getLogger("editxt.project")


class Project(NSObject):

    id = None # will be overwritten (put here for type api compliance for testing)

    @staticmethod
    def is_project_path(path):
        return path.endswith("." + const.PROJECT_EXT)

    @classmethod
    def create(cls):
        return cls.alloc().init()

    @classmethod
    def create_with_path(cls, path):
        return cls.create_with_serial({"path": path})

    @classmethod
    def create_with_serial(cls, serial):
        return cls.alloc().init_with_serial(serial)

    def init(self):
        self = super(Project, self).init()
        self.id = doc_id_gen.next()
        self.name = const.UNTITLED_PROJECT_NAME
        self.path = None
        self.expanded = True
        self.is_dirty = False
        self._documents = KVOList.alloc().init()
        self.reset_serial_cache()
        return self

    def init_with_serial(self, serial):
        self = self.init()
        self.deserialize(serial)
        self.reset_serial_cache()
        return self

    def serialize(self):
        if self.path is not None:
            return {"path": self.path}
        return self.serialize_full()

    def serialize_full(self):
        data = {"expanded": self.expanded}
        if self.path is not None:
            data["path"] = self.path
        if self.name != const.UNTITLED_PROJECT_NAME:
            data["name"] = self.name
        states = (d.edit_state for d in self._documents)
        documents = [s for s in states if "path" in s]
        if documents:
            data["documents"] = documents
        return data

    def deserialize(self, serial):
        if "path" in serial:
            self.path = serial["path"]
            plistData = NSData.dataWithContentsOfFile_(self.path)
            serial, format, error = NSPropertyListSerialization. \
                propertyListFromData_mutabilityOption_format_errorDescription_(
                    plistData, NSPropertyListImmutable, None, None)
        if serial:
            if "name" in serial:
                self.name = serial["name"]
            for doc_state in serial.get("documents", []):
                try:
                    self.create_document_view_with_state(doc_state)
                except Exception:
                    log.warn("cannot open document: %r" % (doc_state,))
            self.expanded = serial.get("expanded", True)
        if not self._documents:
            self.create_document_view()

    def reset_serial_cache(self):
        self.serial_cache = self.serialize_full()

    def save(self):
        if self.serial_cache != self.serialize_full():
            if self.path is not None:
                self.save_with_path(self.path)
            app.save_open_projects()
            self.reset_serial_cache()

    def save_with_path(self, path):
        data = NSMutableDictionary.alloc().init()
        data.update(self.serialize_full())
        data.writeToFile_atomically_(path, True)

#     def save_if_dirty(self):
#         if self.is_dirty:
#             self.save()

#     def _get_dirty(self):
#         return self.serial_cache == self.serialize()
#     def _set_dirty(self, value):
#         if not value:
#             self.reset_serial_cache()
#         app.item_changed(self)
#     is_dirty = property(_get_dirty, _set_dirty)

    def documents(self):
        return self._documents

    def dirty_documents(self):
        return (doc for doc in self._documents if doc.is_dirty)

    def icon(self):
        return None

    def can_rename(self):
        return self.path is None

    def displayName(self):
        if self.path is None:
            return self.name
        return os.path.split(self.path)[1][:-len(const.PROJECT_EXT) - 1]

    def setDisplayName_(self, name):
        if self.can_rename():
            self.name = name

    def properties(self):
        return None

    def setProperties_(self, value):
        pass

    def isLeaf(self):
        return False

    def isDocumentEdited(self):
        return False

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
            for dv in self.documents():
                if dv.document is doc:
                    return dv
        return None

    def create_document_view(self):
        dc = NSDocumentController.sharedDocumentController()
        doc, err = dc.makeUntitledDocumentOfType_error_(const.TEXT_DOCUMENT, None)
        if err:
            raise Exception(err)
        dc.addDocument_(doc)
        dv = TextDocumentView.create_with_document(doc)
        return self.append_document_view(dv)

    def create_document_view_with_state(self, state):
        dv = TextDocumentView.create_with_state(state)
        dv = self.append_document_view(dv)
        return dv

    def append_document_view(self, view):
        """Add view to the end of this projects document views

        Returns the appended view or an existing view in this project with the
        same document as the given view. You should always use the returned
        view after calling this method if you need to work with a view that
        belongs to this project.
        """
        for dv in self._documents:
            if dv is view or dv.document is view.document:
                return dv
        self._documents.append(view)
        #self.is_dirty = True
        return view

    def insert_document_view(self, index, view):
        """Insert view at index in this projects document views

        Returns the inserted view or an existing view in this project with the
        same document as the given view. You should always use the returned
        view after calling this method if you need to work with a view that
        belongs to this project.
        """
        for dv in self._documents:
            if dv is view or dv.document is view.document:
                return dv
        self._documents.insert(index, view)
        #self.is_dirty = True
        return view


    def remove_document_view(self, doc_view):
        """Remove view from this projects document views

        Does nothing if the view does not belong to this project.
        """
        if doc_view in self._documents:
            self._documents.remove(doc_view)
            #self.is_dirty = True

    def find_view_with_document(self, doc):
        for view in self._documents:
            if view.document is doc:
                return view
        return None

#     def set_primary_window_controller(self, wc):
#         if self._documents:
#             wc.activate_document_view(self._documents[0])

    def set_main_view_of_window(self, view, window):
        pass # TODO add project-specific view?

    def perform_close(self, editor):
        from editxt import app
        from editxt.application import DocumentSavingDelegate
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
        for dv in list(self._documents):
            dv.close()
        #self._documents.setItems_([])


#     @staticmethod
#     def isProjectURL_(url):
#         return url.path().endswith("." + const.PROJECT_EXT)
#
#     def _init(self):
#         super(Project, self).init()
#         self._docs = NSMutableArray.array()
#         self.controller = ProjectWindowController.alloc().initWithProject_(self)
#         self._alias = None
#         self._dirty = False
#         self._canSave = False
#
#     def init(self):
#         raise NotImplementedError("Project is not ready for this yet")
#         self._init()
#         self.controller.showWindow_(self)
#         self.newDocument()
#         self._canSave = True
#         return self
#
#     def init_with_path(self, path):
#         self._init()
#         self.loadWithPath_(path)
#         return self
#
#     def loadWithPath_(self, path):
#         self.filePath = path
#         data = {}
#         if os.path.exists(path):
#             plistData = NSData.dataWithContentsOfFile_(path);
#             data, format, error = NSPropertyListSerialization. \
#                 propertyListFromData_mutabilityOption_format_errorDescription_(
#                     plistData, NSPropertyListImmutable)
#
#         if data:
#             win = data.get("window", {})
#             fs = win.get("frame_string")
#             if fs: self.controller.window().setFrameFromString_(fs)
#             split = win.get("split")
#             if split is not None:
#                 self.controller.splitView.setDocbarWidth(split)
#             self.controller.showWindow_(self)
#
#             # open project documents
#             root = self.projectRootForPath_(path)
#             show = False
#             current = None
#             for item in data.get("documents", []):
#                 path = item.pop("path", None)
#                 if path is not None:
#                     path = os.path.join(root, path)
#                     if os.path.exists(path):
#                         path = os.path.abspath(path)
#                         doc = self.openDocumentWithPath_(path)
#                         if doc:
#                             if item.pop("is_current", False):
#                                 current = doc
#                             doc.documentState = item
#                         show = True
#
#             if current is not None:
#                 self.controller.docsController.setSelectedObjects_([current])
#         else:
#             self.controller.showWindow_(self)
#
#         if not self.docs:
#             self.newDocument()
#         self._canSave = True
#
#     def save(self):
#         if not self._canSave:
#             return
#         path = self.filePath
#         if path is None:
#             # PROBLEM this will overwrite another default project
#             # if two "default" projects are open simulatneously
#             path = self.defaultProjectPath()
#         self.saveWithPath_(path)
#
#     def saveWithPath_(self, path):
#         if not self._canSave:
#             return
#         log.debug("saving project: %r", path)
#         data = NSMutableDictionary.alloc().init()
#
#         win = self.controller.window()
#         if win is not None:
#             data    ["window"] = {
#                 "frame_string": win.stringWithSavedFrame(),
#                 "split": self.controller.splitView.docbarWidth(),
#             }
#
#         data["documents"] = docs = []
#         currdoc = self.currentDocument
#         root = self.projectRootForPath_(path)
#         for doc in self.documents():
#             fpath = doc.filePath()
#             if fpath and os.path.exists(fpath):
#                 docstate = doc.documentState
#                 docstate.update(
#                     path=(fpath if root == os.sep else relpath(fpath, root)),
#                     is_current=(doc is currdoc),
#                 )
#                 docs.append(docstate)
#
#         if self.isDefaultProjectPath_(path):
#             sdc = NSDocumentController.sharedDocumentController()
#             if not os.path.exists(sdc.appSupportPath()):
#                 sdc.createAppSupportFolder()
#
#         data.writeToFile_atomically_(path, True)
#         self.filePath = path
#
#     def saveAs_(self, sender):
#         panel = NSSavePanel.savePanel()
#         panel.setRequiredFileType_(const.PROJECT_EXT)
#         path = self.filePath
#         if path is None:
#             filename = None
#         else:
#             path, filename = os.path.split(path)
#         selector = "savePanelDidEnd:returnCode:contextInfo:"
#         panel.beginSheetForDirectory_file_modalForWindow_modalDelegate_didEndSelector_contextInfo_(
#             path, filename, self.controller.window(), self, selector, 0)
#
#     @objc.signature('v@:@ii')
#     def savePanelDidEnd_returnCode_contextInfo_(self, panel, code, context):
#         import pdb; pdb.set_trace()
#         if code == NSOKButton:
#             self.saveWithPath_(panel.URL().path())
#
#     def saveIfNecessary(self):
#         if self._dirty and self._canSave:
#             self.save()
#             return True
#         return False
#
#     def documentDraggedInSidebar(self):
#         if self._canSave:
#             self._dirty = True
#
#     def _get_filePath(self):
#         return None if self._alias is None else self._alias.path()
#     def _set_filePath(self, value):
#         if value is not None:
#             self._alias = NDAlias.aliasWithPath_(value)
#         else:
#             self._alias = None
#     filePath = property(_get_filePath, _set_filePath)
#
#     def projectRootForPath_(self, path):
#         # TODO remove support for absolute paths (should not be needed) ??
#         if self.isDefaultProjectPath_(path):
#             # the project root for the default project is the system root
#             return os.sep
#         path = os.path.split(path)[0]
#         return path if path else os.sep
#
#     @property
#     def docs(self):
#         return self.mutableArrayValueForKey_("documents")
#
#     @property
#     def dirtyDocuments(self):
#         docs = [doc for doc in self.docs if doc.isDocumentEdited()]
#         if docs or self._dirty:
#             docs.append(self)
#         return docs
#
#     @staticmethod
#     def defaultProjectPath():
#         sdc = NSDocumentController.sharedDocumentController()
#         return os.path.join(sdc.appSupportPath(), DEFAULT_PROJECT_NAME)
#
#     @staticmethod
#     def isDefaultProjectPath_(path):
#         if not path:
#             return os.sep
#         path = os.path.abspath(path)
#         dpth = Project.defaultProjectPath()
#         if os.path.exists(path) and os.path.exists(dpth):
#             return os.path.samefile(path, dpth)
#         return dpth == path
#
#     def newDocument(self):
#         sdc = NSDocumentController.sharedDocumentController()
#         doc, err = sdc.makeUntitledDocumentOfType_error_(const.TEXT_DOCUMENT)
#         if err: raise Exception(err) # HACK how should errors like this be handled?
#         doc.project = self
#         self.addDocument_(doc)
#         sdc.addDocument_(doc)
#         return doc
#
#     def openDocumentWithPath_(self, filepath):
#         url = NSURL.fileURLWithPath_(filepath)
#         sdc = NSDocumentController.sharedDocumentController()
#         doc = sdc.documentForURL_(url)
#         if doc is not None:
#             return doc
#         doc, err = sdc.makeDocumentWithContentsOfURL_ofType_error_(url, const.TEXT_DOCUMENT)
#         if doc is not None:
#             doc.project = self
#             self.addDocument_(doc)
#             sdc.addDocument_(doc)
#         return doc
#
#     def addDocument_(self, doc):
#         self.docs.append(doc)
#         if self.controller.docsController is not None:
#             self.controller.docsController.setSelectedObjects_([doc])
#         else:
#             doc.addWindowController_(self.controller)
#         if self._canSave:
#             self._dirty = True
#
#     def removeDocument_(self, doc):
# #         if doc is self.controller.document():
# #             # remove document from window controller to prevent this error:
# #             # ValueError: NSKeyValueNotifyingMutableArray.index(x): x not in list
# #             self.addWindowController_(self.controller)
#         self.docs.remove(doc)
#         self.controller.tableViewSelectionDidChange_(None)
#         if self._canSave:
#             self._dirty = True
#
#     def _getCurrentDocument(self):
#         docs = self.controller.docsController.selectedObjects()
#         if docs:
#             return docs[0]
#         return None
#     def _setCurrentDocument(self, doc):
#         doc.addWindowController_(self.controller)
#     currentDocument = property(_getCurrentDocument, _setCurrentDocument)
#
#     def documentChanged_(self, doc):
#         view = self.controller.tableView
#         if view:
#             # are we refreshing too much here?
#             # only the row (even just the close button cell) needs a refresh
#             view.setNeedsDisplayInRect_(view.frame())
#
#     def saveAndClose(self):
#         self.saveIfNecessary()
#         self.close()
#
#     def close(self):
#         log.debug("closing project: %r", self.filePath)
#         self._canSave = False
#         for doc in self.docs:
#             doc.close()
#         sdc = NSDocumentController.sharedDocumentController()
#         sdc.removeProject_(self)
#
#     # documents KVO implementation ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#     def documents(self):
#         return self._docs
#
#     def setDocuments_(self, value):
#         self._docs[:] = value
#
#     def countOfDocuments(self):
#         return len(self._docs)
#     countOfDocuments = objc.accessor(countOfDocuments)
#
#     def objectInDocumentsAtIndex_(self, idx):
#         return self._docs[idx]
#     objectInDocumentsAtIndex_ = objc.accessor(objectInDocumentsAtIndex_)
#
#     def insertObject_inDocumentsAtIndex_(self, obj, idx):
#         self._docs.insert(idx, obj)
#     insertObject_inDocumentsAtIndex_ = objc.accessor(insertObject_inDocumentsAtIndex_)
#
#     def removeObjectFromDocumentsAtIndex_(self, idx):
#         del self._docs[idx]
#     removeObjectFromDocumentsAtIndex_ = objc.accessor(removeObjectFromDocumentsAtIndex_)
#
#     def replaceObjectInDocumentsAtIndex_withObject_(self, idx, obj):
#         self._docs[idx] = obj
#     replaceObjectInDocumentsAtIndex_withObject_ = \
#         objc.accessor(replaceObjectInDocumentsAtIndex_withObject_)
#
# def relpath(path, reldir):
#     """Returns 'path' relative to 'reldir'.
#
#     This function was taken from the comments on this page:
#     http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/302594
#     """
#     # use normpath to ensure path separators are uniform
#     path = os.path.normpath(path)
#     # find length of reldir as prefix of path (or zero if it isn't)
#     prelen = len(os.path.commonprefix((
#             os.path.normcase(path),
#             # add a separator to get correct prefix length
#             # (normpath removes trailing separators)
#             os.path.normcase(os.path.normpath(reldir)) + os.sep
#         )))
#     return path[prelen:]

