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
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import (assert_raises, gentest, TestConfig, replattr,
    tempdir, test_app, make_file, CaptureLog)

import editxt.constants as const
import editxt.document as mod
from editxt.constants import TEXT_DOCUMENT
from editxt.application import Application, DocumentController
from editxt.document import TextDocument
from editxt.editor import Editor
from editxt.util import filestat
from editxt.window import Window, WindowController

log = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextDocument tests

@test_app
def test_TextDocument_init(app):
    ident = next(DocumentController.id_gen) + 1
    doc = TextDocument(app)
    eq_(doc.id, ident)
    eq_(doc.icon_cache, (None, None))
    eq_(doc.document_attrs, {
        ak.NSDocumentTypeDocumentAttribute: ak.NSPlainTextDocumentType,
        ak.NSCharacterEncodingDocumentAttribute: fn.NSUTF8StringEncoding,
    })
    #assert doc.text_storage is not None
    assert doc.syntaxer is not None
    eq_(doc._filestat, None)
    eq_(doc.indent_size, 4)
    assert doc.props is not None
    #eq_(doc.save_hooks, [])

def property_value_util(c, doc=None):
    with test_app() as app:
        if doc is None:
            doc = TextDocument(app)
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
    @test_app
    def test(app):
        doc = TextDocument(app)
        doc.character_encoding = 42
        eq_(doc.document_attrs[ak.NSCharacterEncodingDocumentAttribute], 42)
        doc.character_encoding = None
        assert ak.NSCharacterEncodingDocumentAttribute not in doc.document_attrs
    yield test,

def test_TextDocument_eol():
    @test_app
    def test(app, c):
        doc = TextDocument(app)
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
#         doc = TextDocument(None)
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
#         doc = TextDocument(None)
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

@test_app
def test_TextDocument_default_text_attributes(app):
    doc = TextDocument(app)
    attrs = doc.default_text_attributes()
    assert ak.NSFontAttributeName in attrs
    assert ak.NSParagraphStyleAttributeName in attrs
    assert attrs is doc.default_text_attributes()

@test_app
def test_TextDocument_reset_text_attributes(app):
    INDENT_SIZE = 42
    m = Mocker()
    ps_class = m.replace(ak, 'NSParagraphStyle')
    doc = TextDocument(app)
    with m.off_the_record():
        ts = doc.text_storage = m.mock(ak.NSTextStorage)
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
    m.method(app.iter_editors_of_document)(doc) >> (dv for dv, tv in editors)
    for dv, tv in editors:
        (dv.text_view << tv).count(1 if tv is None else 3)
        if tv is not None:
            tv.setTypingAttributes_(attrs)
            tv.setDefaultParagraphStyle_(real_ps)
    with m:
        doc.reset_text_attributes(INDENT_SIZE)
        eq_(doc.default_text_attributes(), attrs)

@test_app
def test__refresh_file_mtime(app):
    from datetime import datetime
    dt = fn.NSDate.date()
    doc = TextDocument(app)
    eq_(doc.file_mtime, None)
    eq_(doc._filestat, None)
    doc._filestat = "<checked>"
    doc._refresh_file_mtime()
    eq_(doc._filestat, None)

def test_is_externally_modified():
    def test(c):
        """check if this document has been externally modified

        is_externally_modified returns True, False or None. If a file exists at the
        path of this document then return True if the document has been modified by
        another program else False. However, if there is no file at the path of
        this document this function will return None.
        """
        with make_file() as path, test_app() as app:
            if not c.exists:
                path += "-not-found"
            doc = TextDocument(app, (None if c.url_is_none else path))
            if c.exists:
                if c.change == "modify":
                    stat = filestat(path)
                    with open(path, "a", encoding="utf-8") as file:
                        file.write("more data")
                    assert stat != filestat(path)
                elif c.change == "remove":
                    os.remove(path)
            eq_(doc.is_externally_modified(), c.rval)
    c = TestConfig(url_is_none=False, exists=True, change=None)
    yield test, c(url_is_none=True, rval=None)
    yield test, c(exists=False, rval=None)
    yield test, c(change="remove", rval=None) # this also no access for other reasons (permission denied, etc.)
    yield test, c(change="modify", rval=True)
    yield test, c(rval=False)

def test_TextDocument_has_real_path():
    def test(path, result):
        with test_app() as app:
            doc = TextDocument(app, path)
            eq_(doc.has_real_path(), result)
    yield test, "no", False
    yield test, "/yes", True

def test_TextDocument_file_changed_since_save():
    @gentest
    @test_app
    def test(app, expected, actions=(), create=True):
        with make_file(content="" if create else None) as path:
            m = Mocker()
            doc = app.document_with_path(path)
            for action in actions:
                if action == "move":
                    new_path = path + ".moved"
                    os.rename(path, new_path)
                    path = doc.file_path = new_path
                elif action == "save":
                    doc.save()
                else:
                    assert action == "modify", action
                    with open(path, "a") as file:
                        file.write("modified")
            result = doc.file_changed_since_save()
            eq_(result, expected)
    yield test(False)
    yield test(True, ["move"])
    yield test(True, ["save", "move"])
    yield test(True, ["modify"])
    yield test(True, ["save", "modify"])
    yield test(True, ["modify", "move"])
    yield test(True, ["move", "save", "modify"])
    yield test(False, ["move", "save"])
    yield test(False, ["modify", "save"])
    yield test(False, ["modify", "move", "save"])
    yield test(None, create=False)

def test_check_for_external_changes():
    from editxt.controls.alert import Alert
    @test_app
    def test(app, c):
        def filestat(path):
            return c.modstat
        def end(): # this allows us to return early (reducing nested if's)
            with replattr(mod, 'filestat', filestat), m:
                eq_(doc._filestat, c.prestat)
                doc.check_for_external_changes(win)
                eq_(doc._filestat,
                    (c.prestat if not c.extmod or c.win_is_none else c.modstat))
        m = Mocker()
        doc = TextDocument(app, "test.txt")
        win = None
        nsa_class = m.replace(mod, 'Alert')
        alert = m.mock(Alert)
        isdirty = m.method(doc.is_dirty)
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
            path = doc.file_path
            #filestat(path) >> c.modstat
            if c.prestat == c.modstat:
                return end()
            (nsa_class.alloc() >> alert).init() >> alert
            alert.setMessageText_("“test.txt” source document changed")
            alert.setInformativeText_("Discard changes and reload?")
            alert.addButtonWithTitle_("Reload")
            alert.addButtonWithTitle_("Cancel")
            def callback(win, method):
                method(ak.NSAlertFirstButtonReturn if c.reload else None, lambda:None)
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
            with m:
                doc.reload_document()
                eq_(doc.text, text)
        text = "edit"
        config = " ".join("project" for x in c.view_state)
        with make_file(content="disk") as path, test_app(config) as app:
            if c.url_is_none:
                path = "not-saved"
            elif not c.exists:
                path += "-not-found"
            m = Mocker()
            call_later = m.replace(mod, "call_later")
            doc = TextDocument(app, path)
            doc.text = text
            if c.url_is_none or not c.exists:
                return end()
            undo = doc.undo_manager = m.mock(fn.NSUndoManager)
            with m.order():
                undo.should_remove = False
                undo.should_remove = True
            if not c.read2_success:
                os.remove(path)
                os.mkdir(path)
                return end()
            text = "disk"
            tv = m.mock(ak.NSTextView)
            for i, text_view_exists in enumerate(c.view_state):
                project = app.windows[0].projects[i]
                editor = Editor(project, document=doc)
                editor.text_view = (tv if text_view_exists else None)
                project.editors.append(editor)
            if not any(c.view_state):
                # TODO reload without undo
                #doc_ts.replaceCharactersInRange_withString_(range, text)
                undo.removeAllActions()
                return end()
            range = fn.NSRange(0, 4)
            if tv.shouldChangeTextInRange_replacementString_(range, text) >> True:
                # TODO get edit_state of each document view
                # TODO diff the two text blocks and change chunks of text
                # throughout the document (in a single undo group if possible)
                # also adjust edit states if possible
                # see http://www.python.org/doc/2.5.2/lib/module-difflib.html
                #doc_ts.replaceCharactersInRange_withString_(range, text)
                tv.didChangeText()
                tv.breakUndoCoalescing()
                # TODO restore edit states
                # HACK use timed invocation to allow didChangeText notification
                # to update change count before _clearUndo is invoked
                call_later(0, doc.clear_dirty)
                tv.setSelectedRange_(fn.NSRange(0, 0)) # TODO remove
                m.method(doc.update_syntaxer)()
            end()
    from editxt.test.util import profile
    c = TestConfig(url_is_none=False, exists=True,
        read2_success=True, view_state=[True])
    # view_state is a list of flags: text_view_exists
    yield test, c(url_is_none=True)
    yield test, c(exists=False)
    yield test, c(view_state=[])
    yield test, c(view_state=[False])
    yield test, c(view_state=[False, True])
    yield test, c(read2_success=False)
    yield test, c

@test_app
def test_clear_dirty(app):
    m = Mocker()
    doc = TextDocument(app)
    m.method(doc.undo_manager.savepoint)()
    with m:
        doc.clear_dirty()

def test_TextDocument__load():
    def test(path_type):
        # rules:
        # - relative path means new file, not yet saved (do not read, start with blank file)
        # - absolute path means file should be read from disk
        #   - if file exists, attempt to read it
        #   - if not exists, start with empty file
        content = "test content"
        with make_file(content=content) as path, test_app() as app:
            if path_type == "relative":
                path = None
            elif path_type == "abs-missing":
                os.remove(path)
            else:
                eq_(path_type, "abs-exists")
            doc = app.document_with_path(path)
            if path_type == "abs-exists":
                content = "content changed"
                with open(path, "w") as fh:
                    fh.write(content)
                assert doc.is_externally_modified()
            else:
                content = ""
            eq_(doc.text, content) # triggers doc._load()
            assert not doc.is_externally_modified()
    yield test, "relative"
    yield test, "abs-missing"
    yield test, "abs-exists"


def setup_path(tmp, path):
    if path is not None:
        if os.path.isabs(path):
            path = path.lstrip(os.path.sep)
            assert not os.path.isabs(path), path
            result = os.path.join(tmp, path)
            if "existing" in path:
                with open(result, "w") as file:
                    file.write("initial")
        else:
            result = path
    else:
        result = None
    return result, get_content(result)

def get_content(path):
    if path is not None and os.path.isabs(path) and os.path.exists(path):
        with open(path) as file:
            return file.read()
    return None

def test_TextDocument_save():
    @gentest
    def test(path, saved=True):
        with tempdir() as tmp, test_app() as app:
            path, begin_content = setup_path(tmp, path)
            doc = app.document_with_path(path)
            end_content = "modified"
            m = Mocker()
            undo = doc.undo_manager = m.mock(mod.UndoManager)
            if saved:
                m.method(doc.update_syntaxer)()
                undo.savepoint()
            doc.text = end_content
            with m:
                if saved:
                    doc.save()
                    eq_(get_content(doc.file_path), end_content)
                else:
                    with assert_raises(mod.Error):
                        doc.save()
                    eq_(get_content(doc.file_path), begin_content)

    yield test("/existing-file.txt")
    yield test("/file.txt")
    yield test("/nodir/file.txt", saved=False)
    yield test("file.txt", saved=False)
    yield test(path=None, saved=False)

def test_TextDocument_write_to_path():
    @gentest
    def test(path, error=None):
        with tempdir() as tmp, test_app() as app:
            doc_path = os.path.join(tmp, "other")
            path, begin_content = setup_path(tmp, path)
            doc = app.document_with_path(doc_path)
            end_content = "modified"
            doc.text = end_content
            try:
                doc.write_to_file(path)
            except Exception as err:
                if not error:
                    raise
                eq_(get_content(path), begin_content)
                eq_(str(err), error)
            else:
                assert not error, "expected error: %s" % error
                eq_(get_content(path), end_content)
            eq_(doc.file_path, doc_path)
            assert not os.path.exists(doc_path), doc_path

    yield test("/file")
    yield test("file", error="cannot write to relative path: file")


def test_TextDocument_displayName():
    def test(title):
        with test_app() as app, make_file(title or "not used") as path:
            doc = app.document_with_path(path if title else None)
            eq_(doc.displayName(), title or "untitled")
    yield test, None
    yield test, "file.txt"

@test_app
def test_TextDocument_is_dirty(app):
    doc = TextDocument(app)
    eq_(doc.is_dirty(), False)
    # TODO more tests for is_dirty?

@test_app
def test_TextDocument_icon_cache(app):
    doc = TextDocument(app)
    eq_(doc.icon_cache, (None, None))
    icon = doc.icon()
    assert isinstance(icon, ak.NSImage)
    eq_(doc.icon_cache, ("untitled", icon))

def test_read_data_into_textstorage():
    @test_app
    def test(app, success):
        m = Mocker()
        data = "<data>"
        doc = TextDocument(app)
        doc.document_attrs = INIT_ATTRS = {"attr": 0,
            ak.NSCharacterEncodingDocumentAttribute: "<encoding>"}
        with m.off_the_record():
            ts = doc.text_storage = m.mock(ak.NSTextStorage)
        analyze = m.method(doc.analyze_content)
        m.method(doc.default_text_attributes)() >> "<text attributes>"
        (ts.readFromData_options_documentAttributes_error_(data, ANY, None, None)
            << (success, "<attrs>", None)).count(1 if success else 2)
        with m:
            result = doc.read_from_data(data)
            eq_(result, (success, None))
            eq_(doc.document_attrs, ("<attrs>" if success else INIT_ATTRS))
    yield test, True
    yield test, False

# options = {NSDefaultAttributesDocumentOption: self.default_text_attributes()}
# options.update(self.document_attrs)
# success, self.document_attrs = self.text_storage.\
#     readFromData_options_documentAttributes_(data, options)
# return (success, None)

def test_analyze_content():
    @test_app
    def test(app, c):
        if c.eol_char != "\n":
            c.text = c.text.replace("\n", eol_char)
        m = Mocker()
        doc = TextDocument(app)
        eq_((doc.newline_mode, doc.indent_mode, doc.indent_size),
            (const.NEWLINE_MODE_UNIX, const.INDENT_MODE_SPACE, 4),
            'invalid initial state')
        with m.off_the_record():
            doc.text_storage = ts = m.mock(ak.NSTextStorage)
        ts.string() >> fn.NSString.stringWithString_(c.text)
        with m:
            doc.analyze_content()
        eq_((doc.newline_mode, doc.indent_mode, doc.indent_size),
            (
                c._get("eol", const.NEWLINE_MODE_UNIX),
                c._get("imode", const.INDENT_MODE_SPACE),
                c._get("isize", 4),
            ))
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
#        doc = TextDocument(None)
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

@test_app
def test_get_syntaxdef(app):
    from editxt.syntax import SyntaxCache, SyntaxDefinition
    m = Mocker()
    doc = TextDocument(app)
    syn = doc.syntaxer = m.mock(SyntaxCache)
    sd = syn.syntaxdef >> m.mock(SyntaxDefinition)
    with m:
        eq_(doc.syntaxdef, sd)

@test_app
def test_set_syntaxdef(app):
    from editxt.syntax import SyntaxDefinition
    m = Mocker()
    sd = m.mock(SyntaxDefinition)
    doc = TextDocument(app)
    m.method(doc.syntaxer.color_text)(doc.text_storage)
    with m:
        doc.syntaxdef = sd
        eq_(doc.syntaxer.syntaxdef, sd)

def test_update_syntaxer():
    from editxt.syntax import SyntaxCache, SyntaxDefinition, SyntaxFactory
    @test_app
    def test(app, c):
        m = Mocker()
        doc = TextDocument(app)
        with m.off_the_record():
            doc.text_storage = ts = m.mock(ak.NSTextStorage)
        app.syntax_factory = m.mock(SyntaxFactory)
        m.property(doc, "syntaxdef")
        m.property(doc, "props")
        syn = doc.syntaxer = m.mock(SyntaxCache)
        syn.filename >> "<filename %s>" % ("0" if c.namechange else "1")
        new = doc.file_path = "<filename 1>"
        if c.namechange:
            syn.filename = new
            sdef = app.syntax_factory.get_definition(new) >> m.mock(SyntaxDefinition)
            doc.syntaxdef >> (None if c.newdef else sdef)
            if c.newdef:
                doc.props.syntaxdef = sdef
                syn.color_text(ts)
        with m:
            doc.update_syntaxer()
    c = TestConfig(namechange=False)
    yield test, c
    yield test, c(namechange=True, newdef=False)
    yield test, c(namechange=True, newdef=True)

@test_app
def test_TextDocument_comment_token(app):
    from editxt.syntax import SyntaxCache, SyntaxDefinition
    m = Mocker()
    doc = TextDocument(app)
    syn = doc.syntaxer = m.mock(SyntaxCache)
    syn.syntaxdef.comment_token >> "#"
    with m:
        eq_(doc.comment_token, "#")

@test_app
def test_TextDocument_on_text_edit(app):
    from editxt.syntax import SyntaxCache
    m = Mocker()
    doc = TextDocument(app)
    with m.off_the_record():
        ts = doc.text_storage = m.mock(ak.NSTextStorage)
    syn = doc.syntaxer = m.mock(SyntaxCache)
    range = (0, 20)
    syn.color_text(ts, range)
    with m:
        doc.on_text_edit(range)

def test_TextDocument_close():
    with test_app() as app:
        doc = TextDocument(app)
        ts = doc.text_storage
        assert ts is not None
        assert doc._text_storage_edit_connector is not None
        doc.close()
        eq_(doc.text_storage, None)
        assert not hasattr(doc, "_text_storage_edit_connector")
        eq_(doc.props, None)
