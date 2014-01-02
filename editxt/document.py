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

import objc
import AppKit as ak
import Foundation as fn
# from NDAlias import NDAlias

import editxt.constants as const
import editxt.platform.constants as platform_const

from editxt.application import doc_id_gen
from editxt.command.find import Finder, FindOptions
from editxt.command.util import (calculate_indent_mode_and_size,
    change_indentation, iterlines, replace_newlines)
from editxt.constants import TEXT_DOCUMENT, LARGE_NUMBER_FOR_TEXT
from editxt.controls.alert import Alert
from editxt.platform.document import setup_main_view, teardown_main_view
from editxt.platform.kvo import KVOList, KVOProxy, KVOLink
from editxt.syntax import SyntaxCache
from editxt.util import (untested, refactor,
    fetch_icon, filestat, register_undo_callback, WeakProperty)

log = logging.getLogger(__name__)

EOLREF = dict((ch, m) for m, ch in const.EOLS.items())


def document_property(do):
    name = do.__name__
    def fget(self):
        if self.document is None:
            return None
        return getattr(self.document, name)
    def fset(self, value):
        old = getattr(self.document, name)
        if value != old:
            do(self, value, old)
    return property(fget, fset)


class Editor(object):
    """Editor

    Reference graph:
        strong:
            app -> window -> KVOProxy(project) -> KVOProxy(self)
        weak:
            self -> project -> window -> app
    """

    id = None # will be overwritten (put here for type api compliance for testing)
    project = WeakProperty()
    is_leaf = True

    def __init__(self, project, *, document=None, path=None, state=None):
        if state is not None:
            assert document is None, (state, document)
            assert path is None, (state, path)
            path = state["path"]
        if path is not None:
            assert document is None, (path, document)
            document = project.window.app.document_with_path(path)
        assert document is not None, (project, path, state)
        self.editors = KVOList.alloc().init()
        self.id = next(doc_id_gen)
        self.project = project
        self.document = document
        self.proxy = KVOProxy(self)
        self.main_view = None
        self.text_view = None
        self.scroll_view = None
        self.command_view = None
        if isinstance(document, ak.NSDocument):
            # HACK this should not be conditional (but it is for tests)
            self.kvolink = KVOLink([
                (document, "isDocumentEdited", self.proxy, "is_dirty"),
                (self.proxy, "icon", self.proxy, "summary_info"),
                (self.proxy, "name", self.proxy, "summary_info"),
                (self.proxy, "is_dirty", self.proxy, "summary_info"),
                (document, "indent_mode", self.proxy, "indent_mode"),
                (document, "indent_size", self.proxy, "indent_size"),
                (document, "newline_mode", self.proxy, "newline_mode"),
                (document, "syntaxdef", self.proxy, "syntaxdef"),
                (document, "character_encoding", self.proxy, "character_encoding"),
                (document, "highlight_selected_text", self.proxy, "highlight_selected_text"),
            ])
        if state is not None:
            self.edit_state = state

    def icon(self):
        return self.document.icon()

    @property
    def name(self):
        return self.document.displayName()

    @property
    def summary_info(self):
        """Returns a 4-tuple: ``icon, name, is_dirty, self``"""
        return (self.icon, self.name, self.is_dirty, self)

    def window(self):
        """Return the native window of this view (NOT a editxt.window.Window)"""
        if self.scroll_view is not None:
            return self.scroll_view.window()
        return None

    @property
    def file_path(self):
        return self.document.file_path

    @property
    def is_dirty(self):
        return self.document.isDocumentEdited()

    def set_main_view_of_window(self, view, window):
        frame = view.bounds()
        if self.scroll_view is None:
            self.main_view = setup_main_view(self, frame)
            self.scroll_view = self.main_view.top
            self.command_view = self.main_view.bottom
            self.text_view = self.scroll_view.documentView() # HACK deep reach
            self.soft_wrap = self.document.app.config["soft_wrap"]
            self.reset_edit_state()
        else:
            self.main_view.setFrame_(frame)
        view.addSubview_(self.main_view)
        window.makeFirstResponder_(self.text_view)
        self.document.update_syntaxer()
        self.scroll_view.verticalRulerView().invalidateRuleThickness()
        self.document.check_for_external_changes(window)

    def _get_soft_wrap(self):
        if self.text_view is None or self.text_view.textContainer() is None:
            return None
        wrap = self.text_view.textContainer().widthTracksTextView()
        return const.WRAP_WORD if wrap else const.WRAP_NONE
    def _set_soft_wrap(self, value):
        wrap = value != const.WRAP_NONE
        tv = self.text_view
        tc = tv.textContainer()
        if wrap:
            mask = ak.NSViewWidthSizable
            size = self.scroll_view.contentSize()
            width = size.width
        else:
            mask = ak.NSViewWidthSizable | ak.NSViewHeightSizable
            width = LARGE_NUMBER_FOR_TEXT
        # TODO
        # if selection is visible:
        #     get position of selection
        # else:
        #     get position top visible line
        tc.setContainerSize_(fn.NSMakeSize(width, LARGE_NUMBER_FOR_TEXT))
        tc.setWidthTracksTextView_(wrap)
        tv.setHorizontallyResizable_(not wrap)
        tv.setAutoresizingMask_(mask)
        if wrap:
            #tv.setConstrainedFrameSize_(size) #doesn't seem to work
            tv.setFrameSize_(size)
            tv.sizeToFit()
        # TODO
        # if selection was visible:
        #     put selection as near to where it was as possible
        # else:
        #     put top visible line at the top of the scroll view
    soft_wrap = property(_get_soft_wrap, _set_soft_wrap)

    @document_property
    def indent_size(self, new, old):
        mode = self.document.indent_mode
        if mode == const.INDENT_MODE_TAB:
            self.change_indentation(mode, old, mode, new, True)
        elif new != old:
            self.document.props.indent_size = new

    @document_property
    def indent_mode(self, new, old):
        if new != old:
            self.document.props.indent_mode = new

    @document_property
    def newline_mode(self, new, old):
        undoman = self.document.undoManager()
        if not (undoman.isUndoing() or undoman.isRedoing()):
            replace_newlines(self.text_view, const.EOLS[new])
        self.document.props.newline_mode = new
        def undo():
            self.proxy.newline_mode = old
        register_undo_callback(undoman, undo)

    @document_property
    def syntaxdef(self, new, old):
        self.document.syntaxdef = new

    @document_property
    def character_encoding(self, new, old):
        self.document.character_encoding = new

    @document_property
    def highlight_selected_text(self, new, old):
        if not new:
            self.finder.mark_occurrences("")
        self.document.highlight_selected_text = new

    def prompt(self, message, infotext, buttons, callback):
        window = self.window()
        if window is None:
            callback(len(buttons) - 1)
        else:
            self.alert = alert = Alert.alloc().init()
            alert.setAlertStyle_(ak.NSInformationalAlertStyle)
            alert.setMessageText_(message)
            if infotext:
                alert.setInformativeText_(infotext)
            for button in buttons:
                alert.addButtonWithTitle_(button)
            def respond(response):
                callback(response - ak.NSAlertFirstButtonReturn)
            alert.beginSheetModalForWindow_withCallback_(window, respond)

    def change_indentation(self, old_mode, old_size, new_mode, new_size, convert_text):
        if convert_text:
            old_indent = "\t" if old_mode == const.INDENT_MODE_TAB else (" " * old_size)
            new_indent = "\t" if new_mode == const.INDENT_MODE_TAB else (" " * new_size)
            change_indentation(self.text_view, old_indent, new_indent, new_size)
        if old_mode != new_mode:
            self.document.props.indent_mode = new_mode
        if old_size != new_size:
            self.document.props.indent_size = new_size
        if convert_text or convert_text is None:
            def undo():
                self.change_indentation(new_mode, new_size, old_mode, old_size, None)
            register_undo_callback(self.document.undoManager(), undo)

    def _get_edit_state(self):
        if self.text_view is not None:
            sel = self.text_view.selectedRange()
            sp = self.scroll_view.contentView().bounds().origin
            state = dict(
                selection=[sel.location, sel.length],
                scrollpoint=[sp.x, sp.y],
                soft_wrap=self.soft_wrap,
            )
        else:
            state = dict(getattr(self, "_state", {}))
        if self.file_path is not None:
            state["path"] = str(self.file_path)
        return state
    def _set_edit_state(self, state):
        if self.text_view is not None:
            point = state.get("scrollpoint", [0, 0])
            sel = state.get("selection", [0, 0])
            self.proxy.soft_wrap = state.get("soft_wrap", const.WRAP_NONE)
            length = self.document.text_storage.length() - 1
            if length > 0:
                # HACK next line does not seem to work without this
                self.text_view.setSelectedRange_(fn.NSRange(length, 0))
            self.scroll_view.documentView().scrollPoint_(fn.NSPoint(*point))
            if sel[0] < length:
                if sel[0] + sel[1] > length:
                    sel = (sel[0], length - sel[0])
                self.text_view.setSelectedRange_(fn.NSRange(*sel))
        else:
            self._state = state
    edit_state = property(_get_edit_state, _set_edit_state)

    def reset_edit_state(self):
        state = getattr(self, "_state", None)
        if state is not None:
            self.edit_state = state
            del self._state

    def message(self, msg, msg_type=const.INFO):
        """Display a message in the command view"""
        self.command_view.message(msg, self.text_view, msg_type)

    def perform_close(self):
        app = self.document.app
        window = self.project.window
        windows = list(app.iter_windows_with_editor_of_document(self.document))
        if windows == [window]:
            window.current_editor = self
            info = app.context.put(self.maybe_close)
            self.document.canCloseDocumentWithDelegate_shouldCloseSelector_contextInfo_(
                self.document, "document:shouldClose:contextInfo:", info)
        else:
            window.discard_and_focus_recent(self)

    def maybe_close(self, should_close):
        if should_close:
            self.project.window.discard_and_focus_recent(self)

    def close(self):
        project = self.project
        if project is not None and not project.closing:
            project.remove_editor(self)
        doc = self.document
        if self.text_view is not None and doc.text_storage is not None:
            doc.text_storage.removeLayoutManager_(self.text_view.layoutManager())
        if next(doc.app.iter_editors_of_document(doc), None) is None:
            doc.close()
        elif (project is not None and
              next(project.window.iter_editors_of_document(doc), None) is None):
            doc.removeWindowController_(project.window.wc)
        self.document = None
        if self.main_view is not None:
            teardown_main_view(self.main_view)
            self.main_view = None
        self.project = None
        self.text_view = None
        self.scroll_view = None
        self.command_view = None
        self.proxy = None

    def __repr__(self):
        name = 'N/A' if self.document is None else self.name
        return '<%s 0x%x name=%s>' % (type(self).__name__, id(self), name)

    # TextView delegate ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @property
    def finder(self):
        try:
            finder = self._finder
        except Exception:
            finder = self._finder = Finder(
                (lambda:self.text_view),
                FindOptions(ignore_case=False, wrap_around=False),
                self.document.app,
            )
        return finder

    def on_do_command(self, command):
        if command == platform_const.ESCAPE:
            self.command_view.dismiss()
            return True
        return False

    def on_selection_changed(self, textview):
        text = textview.string()
        range = textview.selectedRange()
        index = range.location if range.location < text.length() else (text.length() - 1)
        line = self.scroll_view.verticalRulerView().line_number_at_char_index(index)
        i = index
        while i > 0 and text[i - 1] != "\n":
            i -= 1
        col = (index - i)
        sel = range.length
        self.scroll_view.status_view.updateLine_column_selection_(line, col, sel)

        if self.document.highlight_selected_text:
            ftext = text.substringWithRange_(range)
            if len(ftext.strip()) < 3 or " " in ftext:
                ftext = ""
            self.finder.mark_occurrences(ftext)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
