# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
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
from AppKit import *
from Foundation import *
# from NDAlias import NDAlias

import editxt.constants as const

from editxt import app
from editxt.application import doc_id_gen
from editxt.constants import TEXT_DOCUMENT, LARGE_NUMBER_FOR_TEXT
from editxt.controls.alert import Alert
from editxt.controls.linenumberview import LineNumberView
from editxt.controls.statscrollview import StatusbarScrollView
from editxt.controls.textview import TextView
from editxt.syntax import SyntaxCache
from editxt.textcommand import replace_newlines, change_indentation
from editxt.util import KVOList, KVOProxy, KVOLink, untested, refactor
from editxt.util import fetch_icon, filestat, register_undo_callback

log = logging.getLogger(__name__)

class Error(Exception): pass

EOLREF = dict((ch, m) for m, ch in const.EOLS.iteritems())


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


class TextDocumentView(NSObject):

    id = None # will be overwritten (put here for type api compliance for testing)

    @classmethod
    def create_with_state(cls, state):
        dv = cls.create_with_path(state["path"])
        dv.edit_state = state
        return dv

    @classmethod
    def create_with_path(cls, path):
        doc = TextDocument.get_with_path(path)
        return cls.create_with_document(doc)

    @classmethod
    def create_with_document(cls, doc):
        return cls.alloc().init_with_document(doc)

    def init_with_document(self, document):
        self = super(TextDocumentView, self).init()
        self._documents = KVOList.alloc().init()
        self.id = doc_id_gen.next()
        self.project = None
        self.document = document
        self.text_view = None
        self.scroll_view = None
        self.props = KVOProxy(self)
        if isinstance(document, NSDocument):
            # HACK this should not be conditional (but it is for tests)
            self.kvolink = KVOLink([
                (document, "properties.indent_mode", self.props, "indent_mode"),
                (document, "properties.indent_size", self.props, "indent_size"),
                (document, "properties.newline_mode", self.props, "newline_mode"),
                (document, "properties.syntaxdef", self.props, "syntaxdef"),
                (document, "properties.character_encoding", self.props, "character_encoding"),
            ])
        return self

    def icon(self):
        return self.document.icon()

    def displayName(self):
        return self.document.displayName()

    def setDisplayName_(self, name):
        pass

    def properties(self):
        return self.props

    def setProperties_(self, value):
        pass

    def isLeaf(self):
        return True

    def documents(self):
        return self._documents

    def window(self):
        if self.scroll_view is not None:
            return self.scroll_view.window()
        return None

    @property
    def file_path(self):
        url = self.document.fileURL()
        return (unicode(url.path()) if url else None)

    @property
    def is_dirty(self):
        return self.document.isDocumentEdited()

    def set_main_view_of_window(self, view, window):
        frame = view.bounds()
        if self.scroll_view is None:
            lm = NSLayoutManager.alloc().init()
            self.document.text_storage.addLayoutManager_(lm)
            tc = NSTextContainer.alloc().initWithContainerSize_(frame.size)
            tc.setLineFragmentPadding_(10) # left margin
            lm.addTextContainer_(tc)

            self.scroll_view = sv = StatusbarScrollView.alloc().initWithFrame_(frame)
            sv.setHasHorizontalScroller_(True)
            sv.setHasVerticalScroller_(True)
            sv.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

            self.text_view = tv = TextView.alloc().initWithFrame_textContainer_(frame, tc)
            tv.setAllowsUndo_(True)
            tv.setVerticallyResizable_(True)
            tv.setMaxSize_(NSMakeSize(LARGE_NUMBER_FOR_TEXT, LARGE_NUMBER_FOR_TEXT))
            # setTextContainerInset() with height > 0 causes a strange bug with
            # the movement of the line number ruler (it moves down when
            # scrolling down near the top of the document)
            tv.setTextContainerInset_(NSMakeSize(0, 0)) # width/height
            tv.setDrawsBackground_(False)
            tv.setSmartInsertDeleteEnabled_(False)
            tv.setRichText_(False)
            tv.setUsesFontPanel_(False)
            tv.setUsesFindPanel_(True)
            tv.doc_view = self
            tv.setDelegate_(self)
#           #NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
#           #    self, "processEdit:", NSTextStorageDidProcessEditingNotification, store)
            attrs = self.document.default_text_attributes()
            tv.setTypingAttributes_(attrs)
            font = attrs[NSFontAttributeName]
            tv.setFont_(font)
            tv.setDefaultParagraphStyle_(attrs[NSParagraphStyleAttributeName])

            sv.setDocumentView_(tv)
#           sv.setHorizontalLineScroll_(font.advancementForGlyph_(ord(u" ")).width)
#           sv.setVerticalLineScroll_(tv.layoutManager().defaultLineHeightForFont_(font))

            # setup line number ruler
            StatusbarScrollView.setRulerViewClass_(LineNumberView)
            sv.setHasVerticalRuler_(True)
            #sv.verticalRulerView().invalidateRuleThickness()
            sv.setRulersVisible_(True)

            self.wrap_mode = const.LINE_WRAP_NONE
            self.reset_edit_state()
        else:
            # reset frame in case the window was resized
            self.scroll_view.setFrame_(frame)
        view.addSubview_(self.scroll_view)
        window.makeFirstResponder_(self.text_view)
        self.document.update_syntaxer()
        self.scroll_view.verticalRulerView().invalidateRuleThickness()
        self.document.check_for_external_changes(window)

    def _get_wrap_mode(self):
        if self.text_view is None:
            return None
        wrap = self.text_view.textContainer().widthTracksTextView()
        return const.LINE_WRAP_WORD if wrap else const.LINE_WRAP_NONE
    def _set_wrap_mode(self, value):
        wrap = value != const.LINE_WRAP_NONE
        tv = self.text_view
        tc = tv.textContainer()
        if wrap:
            mask = NSViewWidthSizable
            size = self.scroll_view.contentSize()
            width = size.width
        else:
            mask = NSViewNotSizable
            width = LARGE_NUMBER_FOR_TEXT
        # TODO
        # if selection is visible:
        #     get position of selection
        # else:
        #     get position top visible line
        tc.setContainerSize_(NSMakeSize(width, LARGE_NUMBER_FOR_TEXT))
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
    wrap_mode = property(_get_wrap_mode, _set_wrap_mode)

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
            self.props.newline_mode = old
        register_undo_callback(undoman, undo)

    @document_property
    def syntaxdef(self, new, old):
        self.document.syntaxdef = new

    @document_property
    def character_encoding(self, new, old):
        self.document.character_encoding = new

    def prompt(self, message, infotext, buttons, callback):
        window = self.window()
        if window is None:
            callback(len(buttons) - 1)
        else:
            self.alert = alert = Alert.alloc().init()
            alert.setAlertStyle_(NSInformationalAlertStyle)
            alert.setMessageText_(message)
            if infotext:
                alert.setInformativeText_(infotext)
            for button in buttons:
                alert.addButtonWithTitle_(button)
            def respond(response):
                callback(response - NSAlertFirstButtonReturn)
            alert.beginSheetModalForWindow_withCallback_(window, respond)

    def change_indentation(self, old_mode, old_size, new_mode, new_size, convert_text):
        if convert_text:
            old_indent = u"\t" if old_mode == const.INDENT_MODE_TAB else (u" " * old_size)
            new_indent = u"\t" if new_mode == const.INDENT_MODE_TAB else (u" " * new_size)
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
                wrap_mode=self.wrap_mode,
            )
        else:
            state = dict(getattr(self, "_state", {}))
        if self.file_path is not None:
            state["path"] = self.file_path
        return state
    def _set_edit_state(self, state):
        if self.text_view is not None:
            point = state.get("scrollpoint", [0, 0])
            sel = state.get("selection", [0, 0])
            self.props.wrap_mode = state.get("wrap_mode", const.LINE_WRAP_NONE)
            length = self.document.text_storage.length() - 1
            if length > 0:
                # HACK next line does not seem to work without this
                self.text_view.setSelectedRange_(NSRange(length, 0))
            self.scroll_view.documentView().scrollPoint_(NSPoint(*point))
            if sel[0] < length:
                if sel[0] + sel[1] > length:
                    sel = (sel[0], length - sel[0])
                self.text_view.setSelectedRange_(NSRange(*sel))
        else:
            self._state = state
    edit_state = property(_get_edit_state, _set_edit_state)

    def reset_edit_state(self):
        state = getattr(self, "_state", None)
        if state is not None:
            self.edit_state = state
            del self._state

    def perform_close(self, editor):
        if list(app.iter_editors_with_view_of_document(self.document)) == [editor]:
            info = app.context.put(editor)
            editor.current_view = self
            self.document.canCloseDocumentWithDelegate_shouldCloseSelector_contextInfo_(
                self, "document:shouldClose:contextInfo:", info)
        else:
            editor.discard_and_focus_recent(self)

    @objc.typedSelector('v@:@ii')
    def document_shouldClose_contextInfo_(self, doc, should_close, info):
        editor = app.context.pop(info)
        if should_close:
            editor.discard_and_focus_recent(self)

    def close(self):
        doc = self.document
        if self.project is not None and not self.project.closing:
            self.project.remove_document_view(self)
            self.project = None
        if doc is not None:
            if self.text_view is not None:
                self.scroll_view.removeFromSuperview()
                self.scroll_view.verticalRulerView().denotify()
                if doc.text_storage is not None:
                    doc.text_storage.removeLayoutManager_(self.text_view.layoutManager())
                self.text_view.setDelegate_(None)
                self.text_view = None
                self.scroll_view = None
            for wc in list(self.document.windowControllers()):
                if wc.editor.count_views_of_document(doc) == 0:
                    doc.removeWindowController_(wc)
            if app.count_views_of_document(doc) == 0:
                doc.close()
            self.document = None

    def __repr__(self):
        name = 'N/A' if self.document is None else self.displayName()
        return '<%s 0x%x name=%s>' % (type(self).__name__, id(self), name)

    # TextView delegate ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @untested
    def textViewDidChangeSelection_(self, notification):
        tv = notification.object()
        text = tv.string()
        range = tv.selectedRange()
        index = range.location if range.location < text.length() else (text.length() - 1)
        line = self.scroll_view.verticalRulerView().line_number_at_char_index(index)
        i = index
        while i > 0 and text[i - 1] != u"\n":
            i -= 1
        col = (index - i)
        sel = range.length
        self.scroll_view.statusView.updateLine_column_selection_(line, col, sel)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class UndoManager(NSUndoManager):
    """HACK custom undo manager that can prevent actions from being removed"""

    def init(self):
        self.should_remove = True
        return super(UndoManager, self).init()

    def removeAllActions(self):
        if self.should_remove:
            super(UndoManager, self).removeAllActions()


class TextDocument(NSDocument):

    @classmethod
    def get_with_path(cls, path):
        """Get a document with the given path

        Documents returned by this method have been added to the document
        controllers list of documents.
        """
        url = NSURL.fileURLWithPath_(path)
        dc = NSDocumentController.sharedDocumentController()
        doc = dc.documentForURL_(url)
        if doc is None:
            if os.path.exists(path):
                doctype, err = dc.typeForContentsOfURL_error_(url, None)
                doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(
                    url, doctype, None)
                if err is not None:
                    raise Error(err.localizedFailureReason())
                if doc is None:
                    raise Error("could not open document: %s" % path)
                dc.addDocument_(doc)
            else:
                doc, err = dc.makeUntitledDocumentOfType_error_(
                    const.TEXT_DOCUMENT, None)
                doc.setFileURL_(url)
                doc.update_syntaxer()
        return doc

    def init(self):
        super(TextDocument, self).init()
        self.setUndoManager_(UndoManager.alloc().init())
        self.id = doc_id_gen.next()
        self.icon_cache = (None, None)
        self.document_attrs = {
            NSDocumentTypeDocumentAttribute: NSPlainTextDocumentType,
            NSCharacterEncodingDocumentAttribute: NSUTF8StringEncoding,
        }
        self.text_storage = NSTextStorage.alloc().initWithString_attributes_(u"", {})
        self.syntaxer = SyntaxCache()
        self._filestat = None
        self.props = KVOProxy(self)
        self.indent_mode = const.INDENT_MODE_SPACE
        self.indent_size = 4 # should come from syntax definition
        self.newline_mode = const.NEWLINE_MODE_UNIX
        self.reset_text_attributes(self.indent_size)
        #self.save_hooks = []
        return self

    def properties(self):
        return self.props

    def setProperties_(self, value):
        pass

    @property
    def newline_mode(self):
        return self._newline_mode
    @newline_mode.setter
    def newline_mode(self, value):
        self._newline_mode = value
        self.eol = const.EOLS[value]

    @property
    def character_encoding(self):
        return self.document_attrs.get(NSCharacterEncodingDocumentAttribute)
    @character_encoding.setter
    def character_encoding(self, value):
        # TODO when value is None encoding should be removed from document_attrs
        if value is not None:
            self.document_attrs[NSCharacterEncodingDocumentAttribute] = value
        else:
            self.document_attrs.pop(NSCharacterEncodingDocumentAttribute, None)

    def reset_text_attributes(self, indent_size):
        font = NSFont.fontWithName_size_("Monaco", 10.0)
        spcw = font.screenFontWithRenderingMode_(NSFontDefaultRenderingMode) \
            .advancementForGlyph_(ord(u" ")).width
        ps = NSParagraphStyle.defaultParagraphStyle().mutableCopy()
        ps.setTabStops_([])
        ps.setDefaultTabInterval_(spcw * indent_size)
        ps = ps.copy()
        self._text_attributes = attrs = {
            NSFontAttributeName: font,
            NSParagraphStyleAttributeName: ps,
        }
        range = NSMakeRange(0, self.text_storage.length())
        self.text_storage.addAttributes_range_(attrs, range)
        for view in app.iter_views_of_document(self):
            if view.text_view is not None:
                view.text_view.setTypingAttributes_(attrs)
                view.text_view.setDefaultParagraphStyle_(ps)

    def default_text_attributes(self):
        return self._text_attributes

    def makeWindowControllers(self):
        editor = app.current_editor()
        if editor is None:
            editor = app.create_editor()
        view = TextDocumentView.create_with_document(self)
        editor.add_document_view(view)
        self.addWindowController_(editor.wc)
        editor.current_view = view

    def readFromData_ofType_error_(self, data, doctype, error):
        success, err = self.read_data_into_textstorage(data, self.text_storage)
        if success:
            self.analyze_content()
        return (success, err)

    def read_data_into_textstorage(self, data, text_storage):
        options = {NSDefaultAttributesDocumentOption: self.default_text_attributes()}
        options.update(self.document_attrs)
        while True:
            success, attrs, err = text_storage \
                .readFromData_options_documentAttributes_error_(
                    data, options, None, None)
            if success or NSCharacterEncodingDocumentAttribute not in options:
                if success:
                    self.document_attrs = attrs
                break
            if err:
                log.error(err)
            options.pop(NSCharacterEncodingDocumentAttribute, None)
        return success, err

    def dataOfType_error_(self, doctype, error):
        range = NSMakeRange(0, self.text_storage.length())
        attrs = self.document_attrs
        data, err = self.text_storage \
            .dataFromRange_documentAttributes_error_(range, attrs, None)
        if err is None:
            self.update_syntaxer()
            app.save_editor_states()
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
        from editxt.textcommand import iterlines
        text = self.text_storage.string()
        start, end, cend = text.getLineStart_end_contentsEnd_forRange_(
            None, None, None, (0, 0))
        if end != cend:
            eol = EOLREF.get(text[cend:end], const.NEWLINE_MODE_UNIX)
            self.newline_mode = eol
        mode = None
        for line in iterlines(text):
            if line.startswith(u"\t"):
                mode = const.INDENT_MODE_TAB
                if line.strip():
                    break
            elif line.startswith(u" "):
                mode = const.INDENT_MODE_SPACE
                if line.strip():
                    self.indent_size = len(line) - len(line.lstrip(u" "))
                    break
        if mode is not None:
            self.indent_mode = mode

    def is_externally_modified(self):
        """check if this document has been modified by another program"""
        url = self.fileURL()
        if url is not None and os.path.exists(url.path()):
            ok, mdate, err = url.getResourceValue_forKey_error_(
                None, NSURLContentModificationDateKey, None)
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
                if code == NSAlertFirstButtonReturn:
                    self.reload_document()
            alert = Alert.alloc().init()
            alert.setMessageText_(u"“%s” source document changed" % self.displayName())
            alert.setInformativeText_(u"Discard changes and reload?")
            alert.addButtonWithTitle_(u"Reload")
            alert.addButtonWithTitle_(u"Cancel")
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
        self.text_storage = NSTextStorage.alloc().init()
        try:
            ok, err = self.revertToContentsOfURL_ofType_error_(
                url, self.fileType(), None)
        finally:
            tempstore = self.text_storage
            self.text_storage = textstore
            undo.should_remove = True
        if not ok:
            log.error(u"could not reload document: %s", err)
            return # TODO report err
        textview = None
        for view in app.iter_views_of_document(self):
            textview = view.text_view
            if textview is not None:
                break
        text = tempstore.string()
        range = NSRange(0, textstore.length())
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
            textview.setSelectedRange_(NSRange(0, 0))
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
            if name != filename or (name.endswith(u".txt") and u"." in name[:-4]):
                panel.setNameFieldStringValue_(filename)
                exts = ["txt"]
                if u"." in filename:
                    ext = filename.rsplit(".", 1)[1]
                    if ext not in exts:
                        exts.insert(0, ext)
                panel.setAllowedFileTypes_(exts)
        except Exception:
            log.error("cannot prepare save panel...", exc_info=True)
        return True

    def _clearChanges(self):
        self.updateChangeCount_(NSChangeCleared)

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
            syntaxdef = app.syntax_factory.get_definition(filename)
            if self.syntaxdef is not syntaxdef:
                self.props.syntaxdef = syntaxdef
                self.syntaxer.color_text(self.text_storage)

    def textStorageDidProcessEditing_(self, notification):
        range = self.text_storage.editedRange()
        self.syntaxer.color_text(self.text_storage, range)

    def updateChangeCount_(self, ctype):
        super(TextDocument, self).updateChangeCount_(ctype)
        app.item_changed(self, ctype)

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

    def close(self):
        # remove window controllers here so NSDocument does not close the windows
        for wc in list(self.windowControllers()):
            self.removeWindowController_(wc)
        ts = self.text_storage
        if ts is not None and ts.delegate() is self:
            ts.setDelegate_(None)
        self.text_storage = None
        super(TextDocument, self).close()
