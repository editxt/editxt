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
import objc
import os
from itertools import count

import AppKit as ak
import Foundation as fn
# from NDAlias import NDAlias

import editxt.constants as const
import editxt.platform.constants as platform_const

from editxt.command.util import calculate_indent_mode_and_size
from editxt.controls.alert import Alert
from editxt.platform.events import call_later
from editxt.platform.kvo import KVOProxy
from editxt.syntax import SyntaxCache
from editxt.undo import UndoManager
from editxt.util import (untested, refactor,
    fetch_icon, filestat, WeakProperty)

log = logging.getLogger(__name__)

EOLREF = dict((ch, m) for m, ch in const.EOLS.items())


class DocumentController(object):
    """A document controller maintains a set of open documents

    The purpose of a document controller is to make sure that it has
    a single document object for a given path at all times.
    """

    id_gen = count()

    def __init__(self, app):
        self.app = app
        self.documents = {}

    def __len__(self):
        return len(self.documents)

    def __iter__(self):
        return iter(self.documents.values())

#    def new_document(self):
#        """Create a new untitled document
#        """
#        return TextDocument(self.app)

    def get_document(self, path):
        """Get a document object for the given path

        :returns: A new or existing document.
        """
        try:
            document = self.documents[path]
        except KeyError:
            document = self.documents[path] = TextDocument(self.app, path)
        return document

    def change_document_path(self, old_path, document):
        """Change a document's path

        :param old_path: The old path of the document
        :param document: The document, which has been moved, and which has a
        file_path attribute pointing to its new location on disk.
        """
        assert document.has_real_path(), document
        self.documents.pop(old_path, None)
        self.documents[document.file_path] = document

#    def close_document(self, document):
#        """Close document
#
#        Discard document from the set of open documents.
#        """

#    # TODO is this method needed?
#    def is_document_open(self, path):
#        """Return true if a document is open for the given path
#        """

    def discard(self, document):
        """Remove document from controller"""
        self.documents.pop(document.file_path, None)


class TextDocument(object):

    app = WeakProperty()

    def __init__(self, app, path=None):
        #self.setUndoManager_(UndoManager.alloc().init())
        self.app = app
        self.file_path = path or const.UNTITLED_DOCUMENT_NAME
        self.id = next(DocumentController.id_gen)
        self.icon_cache = (None, None)
        self.document_attrs = {
            ak.NSDocumentTypeDocumentAttribute: ak.NSPlainTextDocumentType,
            ak.NSCharacterEncodingDocumentAttribute: fn.NSUTF8StringEncoding,
        }
        self.undo_manager = UndoManager.alloc().init();
        self.syntaxer = SyntaxCache()
        self.props = KVOProxy(self)

        # FIXME reclaim from Application.document_with_path
        self.indent_mode = const.INDENT_MODE_SPACE
        self.indent_size = 4
        self.newline_mode = const.NEWLINE_MODE_UNIX
        self.highlight_selected_text = True

        #self.save_hooks = []

    @property
    def name(self):
        return os.path.basename(self.file_path)

    @property
    def file_path(self):
        return self._filepath
    @file_path.setter
    def file_path(self, value):
        old_path = getattr(self, "_filepath", None)
        self._filepath = value
        self._refresh_file_mtime() # TODO should this (always) happen here?
        if hasattr(self, "_filepath") and self.has_real_path():
            self.app.documents.change_document_path(old_path, self)

    @property
    def file_mtime(self):
        return self._filestat.st_mtime if self._filestat else None

    @property
    def text_storage(self):
        try:
            return self._text_storage
        except AttributeError:
            self._text_storage = \
                ak.NSTextStorage.alloc().initWithString_attributes_("", {})
        self._load()
        return self._text_storage
    @text_storage.setter
    def text_storage(self, value):
        self._text_storage = value

    @property
    def text(self):
        return self.text_storage.mutableString()
    @text.setter
    def text(self, value):
        self.text_storage.mutableString().setString_(value)
        self.reset_text_attributes(self.indent_size)

    @property
    def newline_mode(self):
        return self._newline_mode
    @newline_mode.setter
    def newline_mode(self, value):
        self._newline_mode = value
        self.eol = const.EOLS[value]

    @property
    def character_encoding(self):
        return self.document_attrs.get(ak.NSCharacterEncodingDocumentAttribute)
    @character_encoding.setter
    def character_encoding(self, value):
        # TODO when value is None encoding should be removed from document_attrs
        if value is not None:
            self.document_attrs[ak.NSCharacterEncodingDocumentAttribute] = value
        else:
            self.document_attrs.pop(ak.NSCharacterEncodingDocumentAttribute, None)

    def reset_text_attributes(self, indent_size, reset_views=True):
        attrs = self.default_text_attributes(indent_size)
        ps = attrs[ak.NSParagraphStyleAttributeName]
        range = fn.NSMakeRange(0, self.text_storage.length())
        self.text_storage.addAttributes_range_(attrs, range)
        if not reset_views:
            return
        for editor in self.app.iter_editors_of_document(self):
            if editor.text_view is not None:
                editor.text_view.setTypingAttributes_(attrs)
                editor.text_view.setDefaultParagraphStyle_(ps)

    def default_text_attributes(self, indent_size=None):
        if indent_size is None:
            try:
                return self._text_attributes
            except AttributeError:
                indent_size = self.indent_size
        font = ak.NSFont.fontWithName_size_("Monaco", 10.0)
        spcw = font.screenFontWithRenderingMode_(ak.NSFontDefaultRenderingMode) \
            .advancementForGlyph_(ord("8")).width
        ps = ak.NSParagraphStyle.defaultParagraphStyle().mutableCopy()
        ps.setTabStops_([])
        ps.setDefaultTabInterval_(spcw * indent_size)
        ps = ps.copy()
        self._text_attributes = attrs = {
            ak.NSFontAttributeName: font,
            ak.NSParagraphStyleAttributeName: ps,
        }
        return attrs

    def makeWindowControllers(self):
        # TODO remove this method?
        window = self.app.current_window()
        if window is None:
            window = self.app.create_window()
        window.insert_items([self])

    def _load(self):
        """Load the document's file contents from disk

        :returns: True if the file was loaded from disk, otherwise False.
        """
        if self.file_exists():
            data = ak.NSData.dataWithContentsOfFile_(self.file_path)
            success, err = self.read_from_data(data)
            log.error(err) # TODO display error in progress bar
            if success:
                self.analyze_content()
            return success
        return False

    def read_from_data(self, data):
        options = {ak.NSDefaultAttributesDocumentOption: self.default_text_attributes()}
        options.update(self.document_attrs)
        while True:
            success, attrs, err = self._text_storage \
                .readFromData_options_documentAttributes_error_(
                    data, options, None, None)
            if success or ak.NSCharacterEncodingDocumentAttribute not in options:
                if success:
                    # TODO this might fix the intermittent font bug
                    #self.reset_text_attributes(self.indent_size, False)
                    self.document_attrs = attrs
                break
            if err:
                log.error(err)
            options.pop(ak.NSCharacterEncodingDocumentAttribute, None)
        return success, err

    def save(self):
        """Save the document to disk

        :raises: Error if the document does not have a real path.
        """
        if not self.has_real_path():
            raise Error("document path is not set")
        if self.write_to_file(self.file_path):
            for action in [
                self._refresh_file_mtime,
                self.undo_manager.savepoint,
                self.app.save_window_states,
                self.update_syntaxer,
            ]:
                try:
                    action()
                except Exception:
                    log.error("unexpected error", exc_info=True)

    def write_to_file(self, path):
        """Write the document's content to the given file path

        The given file path must be an absolute path.
        """
        if os.path.isabs(path):
            data, err = self.data()
        else:
            err = "cannot write to relative file path: %s" % path
        if err is not None:
            log.error(err)
            return False
        data.writeToFile_atomically_(path, True)
        return True

    def data(self):
        range = fn.NSMakeRange(0, self.text_storage.length())
        attrs = self.document_attrs
        data, err = self.text_storage \
            .dataFromRange_documentAttributes_error_(range, attrs, None)
        return (data, err)

    def analyze_content(self):
        text = self.text_storage.string()
        start, end, cend = text.getLineStart_end_contentsEnd_forRange_(
            None, None, None, (0, 0))
        if end != cend:
            eol = EOLREF.get(text[cend:end], const.NEWLINE_MODE_UNIX)
            self.newline_mode = eol
        mode, size = calculate_indent_mode_and_size(text)
        if size is not None:
            self.indent_size = size
        if mode is not None:
            self.indent_mode = mode

    def has_real_path(self):
        return os.path.isabs(self.file_path)

    def file_exists(self):
        """Return True if this file has no absolute path on disk"""
        return self.has_real_path() and os.path.exists(self.file_path)

    def _refresh_file_mtime(self):
        if self.file_exists():
            self._filestat = filestat(self.file_path)
            return
        self._filestat = None

    def is_externally_modified(self):
        """check if this document has been modified by another program

        :returns: True if the file has been modified by another program,
        otherwise False, and None if the file cannot be accessed.
        """
        if self.file_exists():
            stat = filestat(self.file_path)
            if stat is not None:
                return self._filestat != stat
        return None

    def check_for_external_changes(self, window):
        if not self.is_externally_modified():
            return
        if self.isDocumentEdited():
            if window is None:
                return # ignore change (no gui for alert)
            stat = filestat(self.file_path)
            if self._filestat == stat: # TODO is this check necessary?
                return
            self._filestat = stat
            def callback(code):
                if code == ak.NSAlertFirstButtonReturn:
                    self.reload_document()
            alert = Alert.alloc().init()
            alert.setMessageText_("“%s” source document changed" % self.name)
            alert.setInformativeText_("Discard changes and reload?")
            alert.addButtonWithTitle_("Reload")
            alert.addButtonWithTitle_("Cancel")
            alert.beginSheetModalForWindow_withCallback_(window, callback)
        else:
            self.reload_document()

    @refactor("improve undo after reload - use difflib to replace changed text only")
    def reload_document(self):
        """Reload document with the given URL

        This implementation allows the user to undo beyond the reload. The
        down-side is that it may use a lot of memory if the document is very
        large.
        """
        path = self.file_path
        if not self.file_exists():
            return
        undo = self.undo_manager
        undo.should_remove = False
        textstore = self._text_storage
        self._text_storage = ak.NSTextStorage.alloc().init()
        try:
            ok = self._load()
        finally:
            tempstore = self._text_storage
            self._text_storage = textstore
            undo.should_remove = True
        if not ok:
            return
        textview = None
        for editor in self.app.iter_editors_of_document(self):
            textview = editor.text_view
            if textview is not None:
                break
        text = tempstore.string()
        range = fn.NSRange(0, textstore.length())
        if textview is None:
            textstore.replaceCharactersInRange_withString_(range, text)
            undo.removeAllActions()
        elif textview.shouldChangeTextInRange_replacementString_(range, text):
            #state = self.documentState
            textstore.replaceCharactersInRange_withString_(range, text)
            #self.documentState = state
            textview.didChangeText()
            textview.breakUndoCoalescing()
            # HACK use timed invocation to allow didChangeText notification
            # to update change count before _clearUndo is invoked
            call_later(0, self._clearChanges)
            textview.setSelectedRange_(fn.NSRange(0, 0))
            self.update_syntaxer()

    @untested
    def prepareSavePanel_(self, panel):
        try:
            panel.setCanSelectHiddenExtension_(True)
            panel.setExtensionHidden_(False)
            panel.setAllowsOtherFileTypes_(True)
            name = panel.nameFieldStringValue() # 10.6 API
            url = self.fileURL()
            if url is not None:
                filename = url.lastPathComponent()
                directory = url.URLByDeletingLastPathComponent()
                panel.setDirectoryURL_(directory) # 10.6 API
            else:
                filename = name
                name += ".txt"
            if name != filename or (name.endswith(".txt") and "." in name[:-4]):
                panel.setNameFieldStringValue_(filename)
                exts = ["txt"]
                if "." in filename:
                    ext = filename.rsplit(".", 1)[1]
                    if ext not in exts:
                        exts.insert(0, ext)
                panel.setAllowedFileTypes_(exts)
        except Exception:
            log.error("cannot prepare save panel...", exc_info=True)
        return True

    def _clearChanges(self):
        self.updateChangeCount_(ak.NSChangeCleared)

    def icon(self):
        path = self.file_path
        key = "" if path is None else path
        old_key, data = self.icon_cache
        if old_key is None or old_key != key:
            data = fetch_icon(key)
            self.icon_cache = (key, data)
        return data

    @property
    def comment_token(self):
        return self.syntaxer.syntaxdef.comment_token

    def _get_syntaxdef(self):
        return self.syntaxer.syntaxdef
    def _set_syntaxdef(self, value):
        self.syntaxer.syntaxdef = value
        self.syntaxer.color_text(self.text_storage)
    syntaxdef = property(_get_syntaxdef, _set_syntaxdef)

    def update_syntaxer(self):
        if self.text_storage.delegate() is not self:
            self.text_storage.setDelegate_(self)
        filename = os.path.basename(self.file_path)
        if filename != self.syntaxer.filename:
            self.syntaxer.filename = filename
            syntaxdef = self.app.syntax_factory.get_definition(filename)
            if self.syntaxdef is not syntaxdef:
                self.props.syntaxdef = syntaxdef
                self.syntaxer.color_text(self.text_storage)

    def textStorageDidProcessEditing_(self, notification):
        range = self.text_storage.editedRange()
        self.syntaxer.color_text(self.text_storage, range)

    def updateChangeCount_(self, ctype):
        # This makes isDocumentEdited KVO compliant, but it will not work if
        # there are private (inside Cocoa) updates to the change count.
        # http://prod.lists.apple.com/archives/cocoa-dev/2013/Oct/msg00459.html
        self.willChangeValueForKey_("isDocumentEdited")
        super().updateChangeCount_(ctype)
        self.didChangeValueForKey_("isDocumentEdited")

    def updateChangeCountWithToken_forSaveOperation_(self, token, operation):
        # http://prod.lists.apple.com/archives/cocoa-dev/2013/Oct/msg00462.html
        self.willChangeValueForKey_("isDocumentEdited")
        super().updateChangeCountWithToken_forSaveOperation_(token, operation)
        self.didChangeValueForKey_("isDocumentEdited")

#     def set_primary_window_controller(self, wc):
#         if wc.document() is self:
#             if self.scroll_view not in wc.mainView.subviews():
#                 wc.setDocument_(self)
#         else:
#             self.addWindowController_(wc)
#         if wc.controller.find_project_with_document(self) is None:
#             wc.add_document(self)

    def __repr__(self):
        return "<%s 0x%x %s>" % (type(self).__name__, id(self), self.name)

    @objc.typedSelector(b'v@:@ii')
    def document_shouldClose_contextInfo_(self, doc, should_close, info):
        self.app.context.pop(info)(should_close)

    def close(self):
        # remove window controllers here so NSDocument does not close the windows
        ts = self.text_storage
        if ts is not None and ts.delegate() is self:
            ts.setDelegate_(None)
        self.text_storage = None
        self.props = None
        self.app.document_closed(self)

    # -- TODO refactor NSDocument compat --------------------------------------

    def displayName(self):
        return self.name

    def isDocumentEdited(self):
        # TODO write tests. Make this work with undo beyond save
        return self.undo_manager.has_unsaved_actions()

    def undoManager(self):
        return self.undo_manager

    def setHasUndoManager_(self, value):
        if not value:
            self.undo_manager = None
        # TODO tell thing that uses undo manager that it should ignore it

    def canCloseDocumentWithDelegate_shouldCloseSelector_contextInfo_(
            self, delegate, should_close, info):
        raise NotImplementedError

    def setLastComponentOfFileName_(self, name):
        path, trash = os.path.split(self.file_path)
        if path:
            self.file_path = os.path.join(path, name)
        else:
            self.file_path = name


class Error(Exception):
    """Document error"""
