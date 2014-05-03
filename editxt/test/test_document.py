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
from contextlib import closing

import AppKit as ak
import Foundation as fn
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import assert_raises, TestConfig, replattr, test_app

import editxt.constants as const
import editxt.document as mod
from editxt.constants import TEXT_DOCUMENT
from editxt.application import Application, DocumentController
from editxt.document import TextDocument
from editxt.editor import Editor
from editxt.window import Window, WindowController

log = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextDocument tests

def test_TextDocument_init():
    ident = next(DocumentController.id_gen) + 1
    doc = TextDocument.alloc().init()
    eq_(doc.id, ident)
    eq_(doc.icon_cache, (None, None))
    eq_(doc.document_attrs, {
        ak.NSDocumentTypeDocumentAttribute: ak.NSPlainTextDocumentType,
        ak.NSCharacterEncodingDocumentAttribute: fn.NSUTF8StringEncoding,
    })
    assert doc.text_storage is not None
    assert doc.syntaxer is not None
    eq_(doc._filestat, None)
    eq_(doc.indent_size, 4)
    assert doc.props is not None
    #eq_(doc.save_hooks, [])

def property_value_util(c, doc=None):
    with test_app() as app:
        if doc is None:
            doc = TextDocument.alloc().init()
            doc.app = app
        eq_(getattr(doc, c.attr), c.default)
        setattr(doc, c.attr, c.value)
        eq_(getattr(doc, c.attr), c.value)

def test_TextDocument_properties():
    c = TestConfig(attr="indent_size", default=4)
    yield property_value_util, c(value=3)
    yield property_value_util, c(value=4)
    yield property_value_util, c(value=5)
    yield property_value_util, c(value=8)

    c = TestConfig(attr="indent_mode", default=const.INDENT_MODE_SPACE)
    yield property_value_util, c(value=const.INDENT_MODE_TAB)
    yield property_value_util, c(value=const.INDENT_MODE_SPACE)

    c = TestConfig(attr="newline_mode", default=const.NEWLINE_MODE_UNIX)
    yield property_value_util, c(value=const.NEWLINE_MODE_UNIX)
    yield property_value_util, c(value=const.NEWLINE_MODE_MAC)
    yield property_value_util, c(value=const.NEWLINE_MODE_WINDOWS)
    yield property_value_util, c(value=const.NEWLINE_MODE_UNICODE)

    c = TestConfig(attr="text", default="")
    yield property_value_util, c(value="abc")

    c = TestConfig(attr="character_encoding", default=fn.NSUTF8StringEncoding)
    for encoding in const.CHARACTER_ENCODINGS:
        yield property_value_util, c(value=encoding)
    def test():
        doc = TextDocument.alloc().init()
        doc.character_encoding = 42
        eq_(doc.document_attrs[ak.NSCharacterEncodingDocumentAttribute], 42)
        doc.character_encoding = None
        assert ak.NSCharacterEncodingDocumentAttribute not in doc.document_attrs
    yield test,

def test_TextDocument_eol():
    def test(c):
        doc = TextDocument.alloc().init()
        doc.newline_mode = c.mode
        eq_(doc.eol, const.EOLS[c.mode])
    c = TestConfig()
    yield test, c(mode=const.NEWLINE_MODE_UNIX)
    yield test, c(mode=const.NEWLINE_MODE_MAC)
    yield test, c(mode=const.NEWLINE_MODE_WINDOWS)
    yield test, c(mode=const.NEWLINE_MODE_UNICODE)

# def test_TextDocument_indent_size():
#     def test(c):
#         m = Mocker()
#         regundo = m.replace("editxt.util.register_undo_callback", passthrough=False)
#         doc = TextDocument.alloc().init()
#         #undoer = m.method(doc.undoManager)
#         reset = m.method(doc.reset_text_attributes)
#         callback = []
#         if c.size is not None and c.size != doc.indent_size:
#             def cb(arg):
#                 callback.append(arg)
#                 return hasattr(arg, "__call__")
#             expect(regundo(doc.undoManager(), MATCH(cb))).count(2)
#             expect(reset(ANY)).count(2)
#         with m:
#             doc.indent_size = c.size
#             if c.size is None or c.size == 4:
#                 eq_(doc.indent_size, 4) # default
#                 eq_(callback, [])
#             else:
#                 eq_(doc.indent_size, c.size)
#                 callback[0]()
#                 eq_(doc.indent_size, 4)
#                 eq_(len(callback), 2)
#
#     def fail(c, exc):
#         doc = TextDocument.alloc().init()
#         try:
#             doc.indent_size = c.size
#         except Exception as ex:
#             if not isinstance(ex, exc):
#                 raise
#         else:
#             raise AssertionError("test should raise %s" % exc.__name__)
#     c = TestConfig(size=None)
#     yield test, c
#     yield test, c(size=4) # default size
#     yield test, c(size=5)
#     yield test, c(size=7)
#     yield fail, c(size=NSDecimalNumber.decimalNumberWithString_("5")), TypeError

def test_TextDocument_default_text_attributes():
    doc = TextDocument.alloc().init()
    attrs = doc.default_text_attributes()
    assert ak.NSFontAttributeName in attrs
    assert ak.NSParagraphStyleAttributeName in attrs
    assert attrs is doc.default_text_attributes()

def test_TextDocument_reset_text_attributes():
    INDENT_SIZE = 42
    m = Mocker()
    ps_class = m.replace(ak, 'NSParagraphStyle')
    doc = TextDocument.alloc().init()
    doc.app = app = m.mock(Application)
    ts = doc.text_storage = m.mock(ak.NSTextStorage)
    undoer = m.method(doc.undoManager)
    font = ak.NSFont.fontWithName_size_("Monaco", 10.0)
    spcw = font.screenFontWithRenderingMode_(ak.NSFontDefaultRenderingMode) \
        .advancementForGlyph_(ord(" ")).width
    ps = ps_class.defaultParagraphStyle().mutableCopy() >> m.mock()
    ps.setTabStops_([])
    ps.setDefaultTabInterval_(spcw * INDENT_SIZE)
    real_ps = ps.copy() >> "<paragraph style>"
    attrs = {ak.NSFontAttributeName: font, ak.NSParagraphStyleAttributeName: real_ps}
    ts.addAttributes_range_(attrs, fn.NSMakeRange(0, ts.length() >> 20))
    editors = [
        (m.mock(Editor), m.mock(ak.NSTextView)),
        (m.mock(Editor), None),
    ]
    app.iter_editors_of_document(doc) >> (dv for dv, tv in editors)
    for dv, tv in editors:
        (dv.text_view << tv).count(1 if tv is None else 3)
        if tv is not None:
            tv.setTypingAttributes_(attrs)
            tv.setDefaultParagraphStyle_(real_ps)
    with m:
        doc.reset_text_attributes(INDENT_SIZE)
        eq_(doc.default_text_attributes(), attrs)

def test_setFileModificationDate_():
    from datetime import datetime
    dt = fn.NSDate.date()
    doc = TextDocument.alloc().init()
    eq_(doc.fileModificationDate(), None)
    eq_(doc._filestat, None)
    doc._filestat = "<checked>"
    doc.setFileModificationDate_(dt)
    eq_(doc._filestat, None)
    eq_(doc.fileModificationDate(), dt)

def test_is_externally_modified():
    def test(c):
        """check if this document has been externally modified

        is_externally_modified returns True, False or None. If a file exists at the
        path of this document then return (True if the document has been modified by
        another program else False). However, if there is no file at the path of
        this document this function will return None.
        """
        m = Mocker()
        doc = TextDocument.alloc().init()
        def exists(path):
            return c.exists
        fileURL = m.method(doc.fileURL)
        modDate = m.method(doc.fileModificationDate)
        url = fileURL() >> (None if c.url_is_none else m.mock(fn.NSURL))
        path = "<path>"
        if not c.url_is_none:
            url.path() >> path
            if c.exists:
                url.getResourceValue_forKey_error_(
                    None, fn.NSURLContentModificationDateKey, None) \
                    >> (c.date_ok, c.loc_stat, None)
                if c.date_ok:
                    modDate() >> c.ext_stat
        with replattr(os.path, 'exists', exists), m:
            eq_(doc.is_externally_modified(), c.rval)
    c = TestConfig(url_is_none=False, exists=True)
    yield test, c(url_is_none=True, rval=None)
    yield test, c(exists=False, rval=None)
    yield test, c(ext_stat=1, loc_stat=None, date_ok=False, rval=None)
    yield test, c(ext_stat=1, loc_stat=None, date_ok=True, rval=True)
    yield test, c(ext_stat=1, loc_stat=1, date_ok=True, rval=False)
    yield test, c(ext_stat=1, loc_stat=0, date_ok=True, rval=True)
    yield test, c(ext_stat=1, loc_stat=2, date_ok=True, rval=True)

def test_check_for_external_changes():
    from editxt.controls.alert import Alert
    def test(c):
        def filestat(path):
            return c.modstat
        def end(): # this allows us to return early (reducing nested if's)
            with replattr(mod, 'filestat', filestat), m:
                eq_(doc._filestat, c.prestat)
                doc.check_for_external_changes(win)
                eq_(doc._filestat,
                    (c.prestat if not c.extmod or c.win_is_none else c.modstat))
        m = Mocker()
        doc = TextDocument.alloc().init()
        win = None
        nsa_class = m.replace(mod, 'Alert')
        alert = m.mock(Alert)
        displayName = m.method(doc.displayName)
        isdirty = m.method(doc.isDocumentEdited)
        reload = m.method(doc.reload_document)
        m.method(doc.is_externally_modified)() >> c.extmod
        if not c.extmod:
            return end()
        if isdirty() >> c.isdirty:
            if c.win_is_none:
                return end()
            win = m.mock(ak.NSWindow)
            if c.prestat is not None:
                doc._filestat = c.prestat
            path = (m.method(doc.fileURL)() >> m.mock(fn.NSURL)).path() >> "<path>"
            #filestat(path) >> c.modstat
            if c.prestat == c.modstat:
                return end()
            (nsa_class.alloc() >> alert).init() >> alert
            displayName() >> "test.txt"
            alert.setMessageText_("“test.txt” source document changed")
            alert.setInformativeText_("Discard changes and reload?")
            alert.addButtonWithTitle_("Reload")
            alert.addButtonWithTitle_("Cancel")
            def callback(win, method):
                method(ak.NSAlertFirstButtonReturn if c.reload else None)
                return True
            expect(alert.beginSheetModalForWindow_withCallback_(win, ANY)) \
                .call(callback)
            if c.reload:
                reload()
        else:
            reload()
        end()
    c = TestConfig(extmod=True, isdirty=True, prestat=None)
    yield test, c(extmod=None)
    yield test, c(extmod=False)
    yield test, c(isdirty=False, win_is_none=True)
    yield test, c(isdirty=True, win_is_none=True)
    yield test, c(isdirty=True, win_is_none=False, modstat=1, reload=True)
    yield test, c(isdirty=True, win_is_none=False, modstat=1, prestat=1)
    yield test, c(isdirty=True, win_is_none=False, modstat=1, prestat=0, reload=True)
    yield test, c(isdirty=True, win_is_none=False, modstat=1, prestat=0, reload=False)

def test_reload_document():
    def test(c):
        def end():
            with replattr(os.path, 'exists', exists), m:
                doc.reload_document()
                eq_(doc.text_storage, doc_ts)
        m = Mocker()
        def exists(path):
            return c.exists
        doc = TextDocument.alloc().init()
        perform_clear_undo = m.method(doc.performSelector_withObject_afterDelay_)
        doc.app = app = m.mock(Application)
        doc_log = m.replace(mod, 'log')
        ts_class = m.replace(ak, 'NSTextStorage')
        fileURL = m.method(doc.fileURL)
        fw = m.mock(ak.NSFileWrapper)
        ts = m.mock(ak.NSTextStorage)
        doc_ts = doc.text_storage = m.mock(ak.NSTextStorage)
        url = fileURL() >> (None if c.url_is_none else m.mock(fn.NSURL))
        if c.url_is_none:
            return end()
        path = url.path() >> "<path>"
        if not c.exists:
            return end()
        undo = m.method(doc.undoManager)() >> m.mock(fn.NSUndoManager)
        undo.should_remove = False
        (ts_class.alloc() >> ts).init() >> ts
        m.method(doc.revertToContentsOfURL_ofType_error_)(
            url, m.method(doc.fileType)() >> "<type>", None) \
            >> (c.read2_success, "<err>")
        undo.should_remove = True
        if not c.read2_success:
            doc_log.error(ANY, "<err>")
            return end()
        tv = m.mock(ak.NSTextView)
        def editors():
            for text_view_exists in c.view_state:
                editor = m.mock(Editor)
                editor.text_view >> (tv if text_view_exists else None)
                yield editor
        editors = list(editors()) # why on earth is the intermediate var necessary?
        # I don't know, but it turns to None if we don't do it!! ???
        app.iter_editors_of_document(doc) >> editors
        text = ts.string() >> "<string>"
        range = fn.NSRange(0, doc_ts.length() >> 10)
        if not any(c.view_state):
            # TODO reload without undo
            doc_ts.replaceCharactersInRange_withString_(range, text)
            undo.removeAllActions()
            return end()
        if tv.shouldChangeTextInRange_replacementString_(range, text) >> True:
            # TODO get edit_state of each document view
            # TODO diff the two text blocks and change chunks of text
            # throughout the document (in a single undo group if possible)
            # also adjust edit states if possible
            # see http://www.python.org/doc/2.5.2/lib/module-difflib.html
            doc_ts.replaceCharactersInRange_withString_(range, text)
            tv.didChangeText()
            tv.breakUndoCoalescing()
            # TODO restore edit states
            # HACK use timed invocation to allow didChangeText notification
            # to update change count before _clearUndo is invoked
            perform_clear_undo("_clearChanges", doc, 0)
            tv.setSelectedRange_(fn.NSRange(0, 0)) # TODO remove
            m.method(doc.update_syntaxer)()
        end()
    from editxt.test.util import profile
    c = TestConfig(url_is_none=False, exists=True, is_reg_file=True,
        read2_success=True, view_state=[True])
    # view_state is a list of flags: text_view_exists
    yield test, c(url_is_none=True)
    yield test, c(exists=False)
    yield test, c(is_reg_file=False)
    yield test, c(view_state=[])
    yield test, c(view_state=[False])
    yield test, c(view_state=[False, True])
    yield test, c(read2_success=False)
    yield test, c

def test_clearChanges():
    m = Mocker()
    doc = TextDocument.alloc().init()
    m.method(doc.updateChangeCount_)(ak.NSChangeCleared)
    with m:
        doc._clearChanges()


class TestTextDocument(MockerTestCase):

    def test_untitled_displayName(self):
        dc = ak.NSDocumentController.sharedDocumentController()
        doc, err = dc.makeUntitledDocumentOfType_error_(TEXT_DOCUMENT, None)
        assert doc.displayName() == "Untitled"

    def test_titled_displayName(self):
        dc = ak.NSDocumentController.sharedDocumentController()
        path = self.makeFile(content="", prefix="text", suffix="txt")
        url = fn.NSURL.fileURLWithPath_(path)
        doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(url, TEXT_DOCUMENT, None)
        assert doc.displayName() == os.path.split(path)[1]

    def test_readData_ofType(self):
        dc = ak.NSDocumentController.sharedDocumentController()
        content = "test content"
        path = self.makeFile(content=content, prefix="text", suffix=".txt")
        url = fn.NSURL.fileURLWithPath_(path)
        doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(url, TEXT_DOCUMENT, None)
        assert doc.text_storage.string() == content

    def test_saveDocument(self):
        m = Mocker()
        app = m.mock(Application)
        dc = ak.NSDocumentController.sharedDocumentController()
        path = self.makeFile(content="", prefix="text", suffix=".txt")
        file = open(path)
        with closing(open(path)) as file:
            assert file.read() == ""
        url = fn.NSURL.fileURLWithPath_(path)
        doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(url, TEXT_DOCUMENT, None)
        doc.app = app
        content = "test content"
        m.method(doc.update_syntaxer)()
        doc.text_storage.mutableString().appendString_(content)
        app.save_window_states()
        with m:
            doc.saveDocument_(None)
            with closing(open(path)) as file:
                saved_content = file.read()
            assert saved_content == content, "got %r" % saved_content

    def test_icon_cache(self):
        dc = ak.NSDocumentController.sharedDocumentController()
        doc, err = dc.makeUntitledDocumentOfType_error_(TEXT_DOCUMENT, None)
        eq_(doc.icon_cache, (None, None))
        icon = doc.icon()
        assert isinstance(icon, ak.NSImage)
        eq_(doc.icon_cache, ("", icon))

def test_readFromData_ofType_error_():
    def test(c):
        m = Mocker()
        data = "<data>"
        typ = m.mock()
        doc = TextDocument.alloc().init()
        doc.text_storage = ts = m.mock(ak.NSTextStorage)
        m.method(doc.read_data_into_textstorage)(data, ts) >> (c.success, None)
        analyze = m.method(doc.analyze_content)
        if c.success:
            analyze()
        with m:
            result = doc.readFromData_ofType_error_(data, typ, None)
            eq_(result, (c.success, None))
    c = TestConfig(success=True)
    yield test, c
    yield test, c(success=False)

def test_read_data_into_textstorage():
    def test(c):
        m = Mocker()
        data = "<data>"
        typ = m.mock()
        doc = TextDocument.alloc().init()
        doc.document_attrs = INIT_ATTRS = {"attr": 0,
            ak.NSCharacterEncodingDocumentAttribute: "<encoding>"}
        ts = m.mock(ak.NSTextStorage)
        analyze = m.method(doc.analyze_content)
        m.method(doc.default_text_attributes)() >> "<text attributes>"
        (ts.readFromData_options_documentAttributes_error_(data, ANY, None, None)
            << (c.success, "<attrs>", None)).count(1 if c.success else 2)
        with m:
            result = doc.read_data_into_textstorage(data, ts)
            eq_(result, (c.success, None))
            eq_(doc.document_attrs, ("<attrs>" if c.success else INIT_ATTRS))
    c = TestConfig(success=True)
    yield test, c
    yield test, c(success=False)

# options = {NSDefaultAttributesDocumentOption: self.default_text_attributes()}
# options.update(self.document_attrs)
# success, self.document_attrs = self.text_storage.\
#     readFromData_options_documentAttributes_(data, options)
# return (success, None)

def test_analyze_content():
    def test(c):
        if c.eol_char != "\n":
            c.text = c.text.replace("\n", eol_char)
        m = Mocker()
        doc = TextDocument.alloc().init()
        m.property(doc, "newline_mode")
        m.property(doc, "indent_mode")
        m.property(doc, "indent_size")
        doc.text_storage = ts = m.mock(ak.NSTextStorage)
        ts.string() >> fn.NSString.stringWithString_(c.text)
        if "eol" in c:
            doc.newline_mode = c.eol
        if "imode" in c:
            doc.indent_mode = c.imode
        if "isize" in c:
            doc.indent_size = c.isize
        with m:
            doc.analyze_content()
    eols = [(mode, const.EOLS[mode]) for mode in [
        const.NEWLINE_MODE_UNIX,
        const.NEWLINE_MODE_MAC,
        const.NEWLINE_MODE_WINDOWS,
        const.NEWLINE_MODE_UNICODE,
    ]]
    TAB = const.INDENT_MODE_TAB
    SPC = const.INDENT_MODE_SPACE
    c = TestConfig(text="", eol_char="\n")
    yield test, c
    for eol, eol_char in eols:
        yield test, c(text="\n", eol=eol, eol_char=eol_char)
        yield test, c(text="\n\r", eol=eol, eol_char=eol_char)
        yield test, c(text="\n\u2028", eol=eol, eol_char=eol_char)
        yield test, c(text="abc\ndef\r", eol=eol, eol_char=eol_char)
        #yield test, c(text=u"\u2029", eol=eol, eol_char=eol_char) # TODO make ths test pass
    yield test, c(text="\t")
    yield test, c(text="  ")
    yield test, c(text="\tx", imode=TAB)
    yield test, c(text=" x", imode=SPC)
    yield test, c(text="  x", imode=SPC, isize=2)
    yield test, c(text="  \n   x", imode=SPC, isize=3, eol=const.NEWLINE_MODE_UNIX)
    yield test, c(text="  x\n     x", imode=SPC, isize=2, eol=const.NEWLINE_MODE_UNIX)

def test_makeWindowControllers():
    "TODO where to move this method?"
#    import editxt
#    import editxt.editor
#    def test(ed_is_none):
#        doc = TextDocument.alloc().init()
#        m = Mocker()
#        app = m.mock(Application)
#        dv_class = m.replace(editxt.editor, 'Editor')
#        dv = m.mock(Editor)
#        ed = m.mock(Window)
#        app.current_window() >> (None if ed_is_none else ed)
#        if ed_is_none:
#            app.create_window() >> ed
#        ed.insert_items([doc])
#        with m, replattr(editxt, "app", app): # HACK replace global
#            doc.makeWindowControllers()
#            eq_(doc.app, app)
#    yield test, True
#    yield test, False

def test_get_syntaxdef():
    from editxt.syntax import SyntaxCache, SyntaxDefinition
    m = Mocker()
    doc = TextDocument.alloc().init()
    syn = doc.syntaxer = m.mock(SyntaxCache)
    sd = syn.syntaxdef >> m.mock(SyntaxDefinition)
    with m:
        eq_(doc.syntaxdef, sd)

def test_set_syntaxdef():
    from editxt.syntax import SyntaxCache, SyntaxDefinition
    m = Mocker()
    sd = m.mock(SyntaxDefinition)
    doc = TextDocument.alloc().init()
    syn = doc.syntaxer = m.mock(SyntaxCache)
    with m.order():
        syn.syntaxdef = sd
        syn.color_text(doc.text_storage)
    with m:
        doc.syntaxdef = sd

def test_update_syntaxer():
    from editxt.syntax import SyntaxCache, SyntaxDefinition
    def test(c):
        m = Mocker()
        doc = TextDocument.alloc().init()
        doc.app = app = m.mock(Application)
        doc.text_storage = ts = m.mock(ak.NSTextStorage)
        m.property(doc, "syntaxdef")
        m.property(doc, "props")
        syn = doc.syntaxer = m.mock(SyntaxCache)
        ts.delegate() >> (doc if c.delset else None)
        if not c.delset:
            ts.setDelegate_(doc)
        syn.filename >> "<filename %s>" % ("0" if c.namechange else "1")
        new = m.method(doc.lastComponentOfFileName)() >> "<filename 1>"
        if c.namechange:
            syn.filename = new
            sdef = app.syntax_factory.get_definition(new) >> m.mock(SyntaxDefinition)
            doc.syntaxdef >> (None if c.newdef else sdef)
            if c.newdef:
                doc.props.syntaxdef = sdef
                syn.color_text(ts)
        with m:
            doc.update_syntaxer()
    c = TestConfig(delset=False, namechange=False)
    yield test, c
    yield test, c(delset=True)
    yield test, c(namechange=True, newdef=False)
    yield test, c(namechange=True, newdef=True)

def test_TextDocument_comment_token():
    from editxt.syntax import SyntaxCache, SyntaxDefinition
    m = Mocker()
    doc = TextDocument.alloc().init()
    syn = doc.syntaxer = m.mock(SyntaxCache)
    syn.syntaxdef.comment_token >> "#"
    with m:
        eq_(doc.comment_token, "#")

def test_textStorageDidProcessEditing_():
    from editxt.syntax import SyntaxCache
    m = Mocker()
    doc = TextDocument.alloc().init()
    ts = doc.text_storage = m.mock(ak.NSTextStorage)
    syn = doc.syntaxer = m.mock(SyntaxCache)
    range = ts.editedRange() >> m.mock(fn.NSRange)
    syn.color_text(ts, range)
    with m:
        doc.textStorageDidProcessEditing_(None)

# def test_document_set_primary_window_controller():
#     def test(wc_has_doc, sv_in_subviews, doc_in_proj):
#         doc = TextDocument.alloc().init()
#         m = Mocker()
#         wc = m.mock(WindowController)
#         view = m.mock(NSView)
#         doc.scroll_view = view
#         wc.document() >> (doc if wc_has_doc else None)
#         if wc_has_doc:
#             wc.mainView.subviews() >> ([view] if sv_in_subviews else [])
#             if not sv_in_subviews:
#                 wc.setDocument_(doc)
#         else:
#             doc.addWindowController_ = add_wc = m.mock()
#             add_wc(wc) # simulate function call
#         wc.controller.find_project_with_document(doc) >> (1 if doc_in_proj else None)
#         if not doc_in_proj:
#             wc.add_document(doc)
#         with m:
#             doc.set_primary_window_controller(wc)
#     yield test, True, True, True
#     yield test, True, False, True
#     yield test, True, True, False
#     yield test, True, False, False
#     yield test, False, False, True
#     yield test, False, False, False

def test_TextDocument_close():
    m = Mocker()
    doc = TextDocument.alloc().init()
    wcs = m.method(doc.windowControllers)
    rwc = m.method(doc.removeWindowController_)
    wc = m.mock(WindowController)
    wcs() >> [wc]
    rwc(wc)
    with m:
        doc.close()
    eq_(doc.text_storage, None)
    eq_(doc.props, None)
