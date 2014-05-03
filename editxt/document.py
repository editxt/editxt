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

import AppKit as ak
import Foundation as fn
# from NDAlias import NDAlias

import editxt.constants as const
import editxt.platform.constants as platform_const

from editxt.application import doc_id_gen
from editxt.command.util import calculate_indent_mode_and_size
from editxt.controls.alert import Alert
from editxt.platform.kvo import KVOProxy
from editxt.syntax import SyntaxCache
from editxt.util import (untested, refactor,
    fetch_icon, filestat, WeakProperty)

log = logging.getLogger(__name__)

EOLREF = dict((ch, m) for m, ch in const.EOLS.items())




class UndoManager(fn.NSUndoManager):
    """HACK custom undo manager that can prevent actions from being removed"""

    def init(self):
        self.should_remove = True
        return super(UndoManager, self).init()

    def removeAllActions(self):
        if self.should_remove:
            super(UndoManager, self).removeAllActions()


class TextDocument(ak.NSDocument):

    app = WeakProperty()

    def init(self):
        super(TextDocument, self).init()
        self.setUndoManager_(UndoManager.alloc().init())
        self.id = next(doc_id_gen)
        self.icon_cache = (None, None)
        self.document_attrs = {
            ak.NSDocumentTypeDocumentAttribute: ak.NSPlainTextDocumentType,
            ak.NSCharacterEncodingDocumentAttribute: fn.NSUTF8StringEncoding,
        }
        self.text_storage = ak.NSTextStorage.alloc().initWithString_attributes_("", {})
        self.syntaxer = SyntaxCache()
        self._filestat = None
        self.props = KVOProxy(self)

        # FIXME reclaim from Application.document_with_path
        self.indent_mode = const.INDENT_MODE_SPACE
        self.indent_size = 4
        self.newline_mode = const.NEWLINE_MODE_UNIX
        self.highlight_selected_text = True
        self.reset_text_attributes(self.indent_size, False)

        #self.save_hooks = []
        return self

    @property
    def name(self):
        return self.displayName()

    @property
    def file_path(self):
        url = self.fileURL()
        return (url.path() if url else None)
    @file_path.setter
    def file_path(self, value):
        self.setFileURL_(fn.NSURL.fileURLWithPath_(value))

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
        font = ak.NSFont.fontWithName_size_("Monaco", 10.0)
        spcw = font.screenFontWithRenderingMode_(ak.NSFontDefaultRenderingMode) \
            .advancementForGlyph_(ord(" ")).width
        ps = ak.NSParagraphStyle.defaultParagraphStyle().mutableCopy()
        ps.setTabStops_([])
        ps.setDefaultTabInterval_(spcw * indent_size)
        ps = ps.copy()
        self._text_attributes = attrs = {
            ak.NSFontAttributeName: font,
            ak.NSParagraphStyleAttributeName: ps,
        }
        range = fn.NSMakeRange(0, self.text_storage.length())
        self.text_storage.addAttributes_range_(attrs, range)
        if not reset_views:
            return
        for editor in self.app.iter_editors_of_document(self):
            if editor.text_view is not None:
                editor.text_view.setTypingAttributes_(attrs)
                editor.text_view.setDefaultParagraphStyle_(ps)

    def default_text_attributes(self):
        return self._text_attributes

    def makeWindowControllers(self):

        # HACK use global because self.app is not yet set
        from editxt import app
        self.app = app

        window = self.app.current_window()
        if window is None:
            window = self.app.create_window()
        window.insert_items([self])

    def readFromData_ofType_error_(self, data, doctype, error):
        success, err = self.read_data_into_textstorage(data, self.text_storage)
        if success:
            self.analyze_content()
        return (success, err)

    def read_data_into_textstorage(self, data, text_storage):
        options = {ak.NSDefaultAttributesDocumentOption: self.default_text_attributes()}
        options.update(self.document_attrs)
        while True:
            success, attrs, err = text_storage \
                .readFromData_options_documentAttributes_error_(
                    data, options, None, None)
            if success or ak.NSCharacterEncodingDocumentAttribute not in options:
                if success:
                    self.document_attrs = attrs
                break
            if err:
                log.error(err)
            options.pop(ak.NSCharacterEncodingDocumentAttribute, None)
        return success, err

    def dataOfType_error_(self, doctype, error):
        range = fn.NSMakeRange(0, self.text_storage.length())
        attrs = self.document_attrs
        data, err = self.text_storage \
            .dataFromRange_documentAttributes_error_(range, attrs, None)
        if err is None:
            try:
                self.update_syntaxer()
                self.app.save_window_states()
            except Exception:
                log.error("unexpected error", exc_info=True)
#             if self.project is not None:
#                 self.project.save()
#                 self.updateSyntaxer()
#             if self.text_view is not None:
#                 # make the undo manager recognize edits after save
#                 self.text_view.breakUndoCoalescing()
        return (data, err)

    def setFileModificationDate_(self, date):
        super(TextDocument, self).setFileModificationDate_(date)
        self._filestat = None

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

    def is_externally_modified(self):
        """check if this document has been modified by another program"""
        url = self.fileURL()
        if url is not None and os.path.exists(url.path()):
            ok, mdate, err = url.getResourceValue_forKey_error_(
                None, fn.NSURLContentModificationDateKey, None)
            if ok:
                return self.fileModificationDate() != mdate
        return None

    def check_for_external_changes(self, window):
        if not self.is_externally_modified():
            return
        if self.isDocumentEdited():
            if window is None:
                return # ignore change (no gui for alert)
            stat = filestat(self.fileURL().path())
            if self._filestat == stat:
                return
            self._filestat = stat
            def callback(code):
                if code == ak.NSAlertFirstButtonReturn:
                    self.reload_document()
            alert = Alert.alloc().init()
            alert.setMessageText_("“%s” source document changed" % self.displayName())
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
        url = self.fileURL()
        if url is None or not os.path.exists(url.path()):
            return
        undo = self.undoManager()
        undo.should_remove = False
        textstore = self.text_storage
        self.text_storage = ak.NSTextStorage.alloc().init()
        try:
            ok, err = self.revertToContentsOfURL_ofType_error_(
                url, self.fileType(), None)
        finally:
            tempstore = self.text_storage
            self.text_storage = textstore
            undo.should_remove = True
        if not ok:
            log.error("could not reload document: %s", err)
            return # TODO report err
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
            self.performSelector_withObject_afterDelay_("_clearChanges", self, 0)
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
        url = self.fileURL()
        key = "" if url is None else url.path()
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
        filename = self.lastComponentOfFileName()
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
        return "<%s 0x%x %s>" % (type(self).__name__, id(self), self.displayName())

    @objc.typedSelector(b'v@:@ii')
    def document_shouldClose_contextInfo_(self, doc, should_close, info):
        self.app.context.pop(info)(should_close)

    def close(self):
        # remove window controllers here so NSDocument does not close the windows
        for wc in list(self.windowControllers()):
            self.removeWindowController_(wc)
        ts = self.text_storage
        if ts is not None and ts.delegate() is self:
            ts.setDelegate_(None)
        self.text_storage = None
        self.props = None
        super(TextDocument, self).close()
