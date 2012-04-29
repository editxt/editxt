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
from __future__ import with_statement

import logging
import os
from contextlib import closing
from tempfile import gettempdir

from AppKit import *
from Foundation import *
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import TestConfig, untested, check_app_state

import editxt.constants as const
from editxt.constants import TEXT_DOCUMENT
from editxt.application import DocumentController
from editxt.editor import Editor, EditorWindowController
from editxt.document import TextDocument, TextDocumentView
from editxt.project import Project
from editxt.util import KVOList

log = logging.getLogger(__name__)

# log.debug("""TODO
#     implement TextDocumentView.pasteboard_data()
# """)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextDocumentView tests


def verify_document_view_interface(dv):
    from editxt.util import KVOProxy

    assert dv.id is not None
    assert not dv.is_dirty
    assert hasattr(dv, "file_path")
    assert isinstance(dv.documents(), KVOList)

    dn = dv.displayName()
    assert dn is not None
    icon = dv.icon()
    if isinstance(dv, TextDocumentView):
        assert icon is not None
        dv.setDisplayName_("something") # should be a no-op
        assert dv.displayName() == dn
        eq_(type(dv.properties()).__name__, "TextDocumentView_KVOProxy")
        assert dv.isLeaf()
        #assert not dv.expanded
    else:
        assert icon is None
        assert not dv.isLeaf()
        assert dv.expanded
        eq_(dv.properties(), None)

#   from editxt.errorlog import ErrorLog
#   proj = Project.create()
#   td = TextDocument.alloc().init()
#   el = ErrorLog.alloc().init()
#   try:
#       for doc in [
#           proj,
#           TextDocumentView.alloc().init_with_document(el),
#       ]:
#           yield do_document_id, doc
#           yield do_document_icon, doc
#           yield do_document_displayName, doc
#           yield do_document_properties, doc
#           yield do_document_isLeaf, doc
#           yield do_document_is_dirty, doc
#           yield do_document_file_path, doc
#           yield do_document_documents, doc
#       yield do_project_isExpanded, proj
#   finally:
#       td.close()

def test_document_view_interface():
    td = TextDocument.alloc().init()
    try:
        view = TextDocumentView.alloc().init_with_document(td)
        verify_document_view_interface(view)
    finally:
        td.close()

def test_create_with_state():
    state = {"path": "<document path>"}
    m = Mocker()
    dv = m.mock(TextDocumentView)
    create_with_path = m.method(TextDocumentView.create_with_path)
    create_with_path(state["path"]) >> dv
    dv.edit_state = state
    with m:
        result = TextDocumentView.create_with_state(state)
        eq_(result, dv)

def test_create_with_path():
    print type(TextDocumentView.create_with_document)
    path = "<path>"
    doc = "<document>"
    dv = "<doc view>"
    m = Mocker()
    get_with_path = m.method(TextDocument.get_with_path)
    create_with_document = m.method(TextDocumentView.create_with_document)
    get_with_path(path) >> doc
    create_with_document(doc) >> dv
    with m:
        result = TextDocumentView.create_with_path(path)
        eq_(result, dv)

def test_create_with_document():
    doc = "<document>"
    dv = "<doc view>"
    m = Mocker()
    cls = m.mock(TextDocumentView)
    cls.alloc().init_with_document(doc) >> dv
    print type(TextDocumentView.create_with_document)
    print dir(TextDocumentView.create_with_document)
    with m:
        result = TextDocumentView.create_with_document.callable(cls, doc)
        eq_(result, dv)

def test_TextDocumentView_window():
    def test(has_scroll_view):
        m = Mocker()
        win = m.mock(NSWindow)
        doc = m.mock(TextDocument)
        dv = TextDocumentView.alloc().init_with_document(doc)
        if has_scroll_view:
            dv.scroll_view = sv = m.mock(NSScrollView)
            sv.window() >> win
        else:
            win = None
        with m:
            result = dv.window()
            eq_(result, win)
    yield test, True
    yield test, False

def test_document_set_main_view_of_window():
    from editxt.constants import LARGE_NUMBER_FOR_TEXT
    from editxt.controls.linenumberview import LineNumberView
    from editxt.controls.textview import TextView
    from editxt.controls.statscrollview import StatusbarScrollView

    def test(c):
        m = Mocker()

        win = m.mock(NSWindow)
        doc = m.mock(TextDocument)
        ts = m.mock(NSTextStorage)
        dv = TextDocumentView.alloc().init_with_document(doc)
        m.property(dv, "wrap_mode")
        ewc = m.mock(EditorWindowController)
        dv.props = props = m.mock(dict)
        view = m.mock(NSView)
        tv = m.mock(TextView)
        sv = m.mock(StatusbarScrollView)
        frame = (view.bounds() >> m.mock())
        if c.sv_is_none:
            lm_class = m.replace("editxt.document.NSLayoutManager")
            lm = m.mock(NSLayoutManager)
            lm_class.alloc().init() >> lm
            doc.text_storage >> ts
            ts.addLayoutManager_(lm)
            tc_class = m.replace("editxt.document.NSTextContainer")
            tc = m.mock(NSTextContainer)
            tc_class.alloc() >> tc
            size = m.mock(NSSize)
            frame.size >> size
            tc.initWithContainerSize_(size) >> tc
            tc.setLineFragmentPadding_(10) # left margin
            lm.addTextContainer_(tc)
            #tc.setWidthTracksTextView_(False)
            #tc.setContainerSize_(NSMakeSize(LARGE_NUMBER_FOR_TEXT, LARGE_NUMBER_FOR_TEXT))

            sv_class = m.replace("editxt.controls.statscrollview.StatusbarScrollView")
            sv_class.alloc().initWithFrame_(frame) >> sv
            sv.setHasHorizontalScroller_(True)
            sv.setHasVerticalScroller_(True)
            sv.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

            tv_class = m.replace("editxt.controls.textview.TextView")
            tv_class.alloc() >> tv
            tv.initWithFrame_textContainer_(frame, tc) >> tv
            #tv.layoutManager().replaceTextStorage_(doc.text_storage)
            tv.setAllowsUndo_(True)
            tv.setVerticallyResizable_(True)
            #tv.setHorizontallyResizable_(True)
            tv.setMaxSize_(NSMakeSize(LARGE_NUMBER_FOR_TEXT, LARGE_NUMBER_FOR_TEXT))
            tv.setTextContainerInset_(NSMakeSize(0, 0)) # top (and bottom?) margin
            tv.setDrawsBackground_(False)
            tv.setSmartInsertDeleteEnabled_(False)
            tv.setRichText_(False)
            tv.setUsesFontPanel_(False)
            tv.setUsesFindPanel_(True)
            tv.doc_view = dv
            tv.setDelegate_(dv)
            attrs = m.mock()
            doc.default_text_attributes() >> attrs
            tv.setTypingAttributes_(attrs)
            font = m.mock()
            attrs[NSFontAttributeName] >> font
            tv.setFont_(font)
            psan = m.mock()
            attrs[NSParagraphStyleAttributeName] >> psan
            tv.setDefaultParagraphStyle_(psan)

            sv.setDocumentView_(tv)

            sv_class.setRulerViewClass_(LineNumberView)
            sv.setHasVerticalRuler_(True)
            sv.setRulersVisible_(True)

            dv.wrap_mode = const.LINE_WRAP_NONE
            m.method(dv.reset_edit_state)()
            assert dv.scroll_view is None
            assert dv.text_view is None
        else:
            dv.text_view = tv
            dv.scroll_view = sv
            sv.setFrame_(frame)
        view.addSubview_(sv)
        win.makeFirstResponder_(tv)
        sv.verticalRulerView().invalidateRuleThickness()
        doc.update_syntaxer()
        doc.check_for_external_changes(win)

        with m:
            dv.set_main_view_of_window(view, win)
        assert dv.scroll_view is sv
        assert dv.text_view is tv
    c = TestConfig()
    yield test, c(sv_is_none=True, wrap_mode=const.LINE_WRAP_NONE)
    yield test, c(sv_is_none=False, wrap_mode=const.LINE_WRAP_WORD)

def test_get_wrap_mode():
    def test(c):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = TextDocumentView.alloc().init_with_document(doc)
        if c.tv_is_none:
            dv.text_view = None
        else:
            tv = dv.text_view = m.mock(NSTextView)
            tc = tv.textContainer() >> m.mock(NSTextContainer)
            tc.widthTracksTextView() >> (True if c.mode == const.LINE_WRAP_WORD else False)
        with m:
            result = dv.wrap_mode
            eq_(result, c.mode)
    c = TestConfig(tv_is_none=False)
    yield test, c(mode=const.LINE_WRAP_NONE)
    yield test, c(mode=const.LINE_WRAP_WORD)
    yield test, c(tv_is_none=True, mode=None)

def test_set_wrap_mode():
    def test(c):
        m = Mocker()
        doc = m.mock(TextDocument)
        wrap = (c.mode != const.LINE_WRAP_NONE)
        dv = TextDocumentView.alloc().init_with_document(doc)
        sv = dv.scroll_view = m.mock(NSScrollView)
        tv = dv.text_view = m.mock(NSTextView)
        tc = tv.textContainer() >> m.mock(NSTextContainer)
        if wrap:
            size = sv.contentSize() >> m.mock(NSRect)
            width = size.width >> 100.0
            tv.setFrameSize_(size)
            tv.sizeToFit()
        else:
            width = const.LARGE_NUMBER_FOR_TEXT
        tc.setContainerSize_(NSMakeSize(width, const.LARGE_NUMBER_FOR_TEXT))
        tc.setWidthTracksTextView_(wrap)
        tv.setHorizontallyResizable_(not wrap)
        tv.setAutoresizingMask_(NSViewWidthSizable if wrap else NSViewNotSizable)
        with m:
            dv.wrap_mode = c.mode
    c = TestConfig(mode=const.LINE_WRAP_NONE)
    yield test, c
    yield test, c(mode=const.LINE_WRAP_WORD)

def test_TextDocumentView_document_properties():
    def test(c):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = TextDocumentView.create_with_document(doc)
        dv.props = m.mock() # KVOProxy
        with m.order():
            (getattr(doc, c.attr) << c.default).count(2 if c.value != c.default else 3)
            if c.value != c.default:
                c.do(TestConfig(**locals()))
                getattr(doc, c.attr) >> c.value
        with m:
            property_value_util(c, dv)

    def do(x):
        change = x.m.method(x.dv.change_indentation)
        x.doc.indent_mode >> x.c.mode
        if x.c.mode == const.INDENT_MODE_TAB:
            change(x.c.mode, x.c.default, x.c.mode, x.c.value, c.convert)
        elif x.c.default != x.c.value:
            x.doc.props.indent_size = x.c.value
    c = TestConfig(do=do, attr="indent_size", default=4, convert=True)
    for m in (const.INDENT_MODE_TAB, const.INDENT_MODE_SPACE):
        yield test, c(mode=m, value=4) # same as default
        yield test, c(mode=m, value=3)
        yield test, c(mode=m, value=5)
        yield test, c(mode=m, value=5, convert=False)

    def do(x):
        if x.c.default != x.c.value:
            x.doc.props.indent_mode = x.c.value
    c = TestConfig(do=do, attr="indent_mode", default=const.INDENT_MODE_TAB, convert=True)
    yield test, c(value=const.INDENT_MODE_SPACE)
    yield test, c(value=const.INDENT_MODE_TAB)
    yield test, c(value=const.INDENT_MODE_TAB, convert=False)
    yield test, c(value=const.INDENT_MODE_TAB, default=const.INDENT_MODE_SPACE)

    def do(x):
        c, m = x.c, x.m
        regundo = m.replace("editxt.util.register_undo_callback", passthrough=False)
        rep = m.replace("editxt.textcommand.replace_newlines")
        undoman = x.doc.undoManager() >> x.m.mock(NSUndoManager)
        undoman.isUndoing() >> c.undoing
        if not c.undoing:
            undoman.isRedoing() >> c.redoing
        if not (c.undoing or c.redoing):
            rep(x.dv.text_view, const.EOLS[x.c.value])
        setattr(x.doc.props, c.attr, c.value)
        def _undo(undoman, undo):
            undo()
        expect(regundo(undoman, ANY)).call(_undo)
        setattr(x.dv.props, c.attr, c.default)
    c = TestConfig(do=do, attr="newline_mode",
        default=const.NEWLINE_MODE_UNIX, undoing=False, redoing=False)
    yield test, c(value=const.NEWLINE_MODE_UNIX, default=const.NEWLINE_MODE_MAC)
    yield test, c(value=const.NEWLINE_MODE_UNIX)
    yield test, c(value=const.NEWLINE_MODE_MAC)
    yield test, c(value=const.NEWLINE_MODE_WINDOWS)
    yield test, c(value=const.NEWLINE_MODE_UNICODE)
    yield test, c(value=const.NEWLINE_MODE_MAC, undoing=True)
    yield test, c(value=const.NEWLINE_MODE_MAC, redoing=True)

def test_TextDocumentView_prompt():
    from editxt.controls.alert import Alert
    eq_(NSAlertSecondButtonReturn - NSAlertFirstButtonReturn, 1)
    eq_(NSAlertThirdButtonReturn - NSAlertFirstButtonReturn, 2)
    def test(c):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = TextDocumentView.create_with_document(doc)
        dv_window = m.method(dv.window)
        alert_class = m.replace(Alert, passthrough=False)
        callback = m.mock(name="callback")
        win = dv_window() >> (m.mock(NSWindow) if c.has_window else None)
        if c.has_window:
            alert = alert_class.alloc() >> m.mock(Alert); alert.init() >> alert
            alert.setAlertStyle_(NSInformationalAlertStyle)
            alert.setMessageText_(c.message)
            if c.info:
                alert.setInformativeText_(c.info)
            buttons = []
            for i in xrange(c.buttons):
                text = "Button_%i" % i
                buttons.append(text)
                alert.addButtonWithTitle_(text)
            def do(window, callback):
                callback(NSAlertFirstButtonReturn + c.response)
                return True
            expect(alert.beginSheetModalForWindow_withCallback_(win, ANY)).call(do)
        else:
            buttons = ["" for i in xrange(c.buttons)]
        callback(c.response)
        with m:
            dv.prompt(c.message, c.info, buttons, callback)
    c = TestConfig(message="Do it?", info="Really?", has_window=True)
    yield test, c(buttons=1, response=0)
    yield test, c(buttons=2, response=0)
    yield test, c(buttons=2, response=1)
    yield test, c(buttons=2, has_window=False, response=1)
    yield test, c(buttons=3, response=0)
    yield test, c(buttons=3, response=1)
    yield test, c(buttons=3, has_window=False, response=2)
    # TODO test with zero buttons - should raise error

def test_TextDocumentView_change_indentation():
    TAB = const.INDENT_MODE_TAB
    SPC = const.INDENT_MODE_SPACE
    def test(c):
        m = Mocker()
        regundo = m.replace("editxt.util.register_undo_callback", passthrough=False)
        convert = m.replace("editxt.textcommand.change_indentation", passthrough=False)
        doc = m.mock(TextDocument)
        dv = TextDocumentView.create_with_document(doc)
        tv = dv.text_view = m.mock(NSTextView)
        if c.convert:
            old_indent = u"\t" if c.oldm is TAB else (u" " * c.olds)
            new_indent = u"\t" if c.newm is TAB else (u" " * c.news)
            convert(tv, old_indent, new_indent, c.news)
        if c.oldm != c.newm:
            doc.props.indent_mode = c.newm
        if c.olds != c.news:
            doc.props.indent_size = c.news
        if c.convert or c.convert is None:
            undo_change = m.mock(); undo_change(c.newm, c.news, c.oldm, c.olds, None)
            def _undo(undoman, undo):
                dv.change_indentation = undo_change
                undo()
            undoman = doc.undoManager() >> m.mock(NSUndoManager)
            expect(regundo(undoman, ANY)).call(_undo)
        with m:
            dv.change_indentation(c.oldm, c.olds, c.newm, c.news, c.convert)
    c = TestConfig(undoing=False, redoing=False, convert=True, undo=None)
    for cnv in (True, False):
        yield test, c(oldm=TAB, olds=2, newm=TAB, news=4, convert=cnv)
        yield test, c(oldm=SPC, olds=2, newm=SPC, news=4, convert=cnv)
        yield test, c(oldm=TAB, olds=4, newm=SPC, news=4, convert=cnv)
        yield test, c(oldm=SPC, olds=4, newm=TAB, news=4, convert=cnv)
        yield test, c(oldm=SPC, olds=2, newm=TAB, news=4, convert=cnv)
    yield test, c(oldm=TAB, olds=4, newm=SPC, news=4, convert=None)
    yield test, c(oldm=SPC, olds=2, newm=TAB, news=4, convert=None)

def test_get_edit_state():
    from editxt.util import KVOProxy
    def test(c):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = TextDocumentView.alloc().init_with_document(doc)
        m.property(dv, "wrap_mode")
        m.property(dv, "file_path")
        if c.tv_is_none:
            if c.set_state:
                dv.edit_state = state = dict(key="value")
            else:
                state = {}
        else:
            dv.text_view = m.mock(NSTextView)
            dv.scroll_view = m.mock(NSScrollView)
            sel = m.mock(NSRange)
            sp = m.mock(NSPoint)
            dv.text_view.selectedRange() >> sel
            dv.scroll_view.contentView().bounds().origin >> sp
            sel.location >> "<sel.location>"
            sel.length >> "<sel.length>"
            sp.x >> "<sp.x>"
            sp.y >> "<sp.y>"
            dv.wrap_mode >> c.wrap_mode
            state = dict(
                selection=("<sel.location>", "<sel.length>"),
                scrollpoint=("<sp.x>", "<sp.y>"),
                wrap_mode=c.wrap_mode,
            )
        (dv.file_path << ("<path>" if c.path_is_valid else None)).count(1, 2)
        if c.path_is_valid:
            state["path"] = "<path>"
        with m:
            result = dv.edit_state
            eq_(result, state)
            if c.tv_is_none and c.set_state:
                assert result is not state, "identity check should fail: must be a new (mutable) dict"
    c = TestConfig(tv_is_none=False, path_is_valid=True, wrap_mode=const.LINE_WRAP_WORD)
    yield test, c
    yield test, c(path_is_valid=False)
    yield test, c(wrap_mode=const.LINE_WRAP_NONE)
    yield test, c(tv_is_none=True, set_state=False)
    yield test, c(tv_is_none=True, set_state=True)

def test_set_edit_state():
    from editxt.util import KVOProxy
    def test(state=None, ts_len=0):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = TextDocumentView.alloc().init_with_document(doc)
        #m.property(dv, "wrap_mode")
        props = dv.props = m.mock(KVOProxy)
        if state is None:
            eq_state = state = m.mock()
        else:
            eq_state = dict(state)
            eq_state.setdefault("selection", (0, 0))
            eq_state.setdefault("scrollpoint", (0, 0))
            eq_state.setdefault("wrap_mode", const.LINE_WRAP_NONE)
            point = eq_state["scrollpoint"]
            sel = eq_state["selection"]
            dv.text_view = m.mock(NSTextView)
            dv.scroll_view = m.mock(NSScrollView)
            props.wrap_mode = eq_state["wrap_mode"]
            doc.text_storage.length() >> ts_len
            if ts_len - 1 > 0:
                dv.text_view.setSelectedRange_(NSRange(ts_len - 1, 0))
            dv.scroll_view.documentView().scrollPoint_(NSPoint(*point))
            if sel[0] < ts_len - 1:
                if sel[0] + sel[1] > ts_len - 1:
                    sel = (sel[0], ts_len - 1 - sel[0])
                dv.text_view.setSelectedRange_(NSRange(*sel))
        with m:
            dv.edit_state = state
            if not isinstance(state, dict):
                eq_(state, eq_state)
    yield test, # tests case when (doc.text_view is None)
    yield test, {}
    yield test, {"selection": (1, 1)}
    yield test, {"scrollpoint": (1, 1)}
    yield test, {"wrap_mode": const.LINE_WRAP_NONE}
    yield test, {"scrollpoint": (0, 0), "selection": (0, 0), "wrap_mode": const.LINE_WRAP_NONE}
    yield test, {"scrollpoint": (5, 5), "selection": (5, 5), "wrap_mode": const.LINE_WRAP_WORD}
    yield test, {"scrollpoint": (0, 0), "selection": (0, 0)}, 2
    yield test, {"scrollpoint": (0, 0), "selection": (0, 1)}, 2
    yield test, {"scrollpoint": (0, 0), "selection": (0, 2)}, 2

def test_reset_edit_state():
    def test(_state_exists):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = TextDocumentView.alloc().init_with_document(doc)
        m.property(dv, "edit_state")
        _state = m.mock(name="state")
        if _state_exists:
            dv._state  = _state
            dv.edit_state = _state
        else:
            assert getattr(dv, "_state", None) is None
        with m:
            dv.reset_edit_state()
            assert getattr(dv, "_state", None) is None
    yield test, True
    yield test, False

# def test_pasteboard_data():
#     def test(c):
#         m = Mocker()
#         doc = m.mock(TextDocument)
#         path_exists = m.replace("os.path.exists", passthrough=False)
#         dv = TextDocumentView.create_with_document(doc)
#         _file_path_property = TextDocumentView.file_path
#         try:
#             TextDocumentView.file_path = c.path
#             path_exists(c.path) >> c.path_exists
#             with m:
#                 result = list(dv.pasteboard_data())
#                 eq_(result, c.result)
#         finally:
#             TextDocumentView.file_path = _file_path_property
#     c = TestConfig(path="/path/to/document.txt", index_path="<index path>", path_exists=True)
#     yield test, c(path_exists=False, result=[(const.INDEX_PATH_PBOARD_TYPE, c.index_path)])
#     yield test, c(result=[
#         (const.INDEX_PATH_PBOARD_TYPE, c.index_path),
#         (NSFilenamesPboardType, c.path),
#     ])


#     def tableView_writeRowsWithIndexes_toPasteboard_(self, tv, indexes, pboard):
#         log.debug("tableView_writeRowsWithIndexes_toPasteboard_")
#         data = NSKeyedArchiver.archivedDataWithRootObject_(indexes)
#         pboard.declareTypes_owner_([TableViewIndexesDataType], self)
#         pboard.setData_forType_(data, TableViewIndexesDataType)
#         return True


def test_perform_close():
    from editxt.application import Application
    def test(num_views):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = TextDocumentView.alloc().init_with_document(doc)
        app = m.replace("editxt.app", type=Application)
        ed = m.mock(Editor)
        app.iter_editors_with_view_of_document(doc) >> (ed for x in xrange(num_views))
        if num_views == 1:
            key = app.context.put(ed) >> 42
            ed.current_view = dv
            def doc_should_close(dv, selector, context):
                assert hasattr(dv, "document_shouldClose_contextInfo_"), \
                    "missing selector: TextDocumentView document:shouldClose:contextInfo:"
            expect(doc.canCloseDocumentWithDelegate_shouldCloseSelector_contextInfo_(
                dv, "document:shouldClose:contextInfo:", key)).call(doc_should_close)
        else:
            ed.discard_and_focus_recent(dv)
        with m:
            dv.perform_close(ed)
    for num_views in xrange(3):
        yield test, num_views

def test_document_shouldClose_contextInfo_():
    from editxt.application import Application
    def test(should_close):
        m = Mocker()
        app = m.replace("editxt.app", type=Application)
        doc = m.mock(TextDocument)
        dv = TextDocumentView.alloc().init_with_document(doc)
        ed = m.mock(Editor)
        app.context.pop(42) >> ed
        if should_close:
            ed.discard_and_focus_recent(dv)
        with m:
            dv.document_shouldClose_contextInfo_(doc, should_close, 42)
        eq_(TextDocumentView.document_shouldClose_contextInfo_.signature, 'v@:@ii')
    yield test, True
    yield test, False

def test_TextDocumentView_close():
    from editxt.application import Application
    from editxt.editor import Editor
    def test(c):
        m = Mocker()
        doc = m.mock(TextDocument)
        proj = m.mock(Project)
        dv = TextDocumentView.alloc().init_with_document(doc)
        app = m.replace("editxt.app", Application)
        if c.tv_is_none:
            dv.scroll_view = None
            dv.text_view = None
        else:
            dv.scroll_view = sv = m.mock(NSScrollView)
            dv.text_view = tv = m.mock(NSTextView)
            sv.removeFromSuperview()
            sv.verticalRulerView().denotify()
            doc.text_storage >> None if c.ts_is_none else m.mock(NSTextStorage)
            if not c.ts_is_none:
                lm = tv.layoutManager() >> m.mock(NSLayoutManager)
                doc.text_storage.removeLayoutManager_(lm)
            tv.setDelegate_(None)
        wcs = []
        doc.windowControllers() >> wcs
        for w in c.wcs:
            wc = m.mock(EditorWindowController)
            wcs.append(wc)
            ed = wc.editor >> m.mock(Editor)
            if (ed.count_views_of_document(doc) >> w.num_views) == 0:
                doc.removeWindowController_(wc)
        if (app.count_views_of_document(doc) >> c.app_views) < 1:
            doc.close()
        with m:
            dv.close()
        assert dv.scroll_view is None
        assert dv.text_view is None
        assert dv.document is None
    c = TestConfig(app_views=0, wcs=[], tv_is_none=False, ts_is_none=False)
    wc = lambda n:TestConfig(num_views=n)
    yield test, c
    yield test, c(ts_is_none=True)
    yield test, c(tv_is_none=True)
    for num_views in (1, 2):
        for num_wcs in (0, 1, 3):
            yield test, c(wcs=[wc(i) for i in xrange(num_wcs)])
        yield test, c(wcs=[wc(0) for i in xrange(2)])
    yield test, c(app_views=1)

@check_app_state
def test_KVOProxy_create():
    from editxt.util import KVOProxy
    def test(class_, factory):
        m = Mocker()
        proxy = m.replace("editxt.util.KVOProxy")
        def cb(value):
            return isinstance(value, class_)
        proxy(MATCH(cb)) >> m.mock(KVOProxy)
        with m:
            obj = factory(class_)
            eq_(obj.props, obj.properties())
    yield test, TextDocumentView, lambda c: c.create_with_document(None)
    yield test, TextDocument, lambda c: c.alloc().init()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextDocument tests

# def mocktest(testfunc):
#     tests = []
#     def test_collector(*args, **kw):
#         test = args[0]
#         args = args[1:]
#         config = TestConfig(**kw)
#         tests.append((test, config, args))
#     def test():
#         testfunc(test_collector)
#         for test, config, args in tests:
#             yield (test, Mocker()) + args + ((config,) if config else ())
#     return test
#
# @mocktest
# def test_check_for_external_changes(t):
#     def test(m, is_xyz):
#         with m:
#             assert is_xyz
#     t(test, True)
#     t(test, False)

def test_TextDocument_init():
    from editxt.document import doc_id_gen
    ident = doc_id_gen.next() + 1
    doc = TextDocument.alloc().init()
    eq_(doc.id, ident)
    eq_(doc.icon_cache, (None, None))
    eq_(doc.document_attrs, {
        NSDocumentTypeDocumentAttribute: NSPlainTextDocumentType,
        NSCharacterEncodingDocumentAttribute: NSUTF8StringEncoding,
    })
    assert doc.text_storage is not None
    assert doc.syntaxer is not None
    eq_(doc._filestat, None)
    eq_(doc.indent_size, 4)
    assert doc.props is not None
    #eq_(doc.save_hooks, [])

def property_value_util(c, doc=None):
    if doc is None:
        doc = TextDocument.alloc().init()
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

    c = TestConfig(attr="character_encoding", default=NSUTF8StringEncoding)
    for encoding in const.CHARACTER_ENCODINGS:
        yield property_value_util, c(value=encoding)
    def test():
        doc = TextDocument.alloc().init()
        doc.character_encoding = 42
        eq_(doc.document_attrs[NSCharacterEncodingDocumentAttribute], 42)
        doc.character_encoding = None
        assert NSCharacterEncodingDocumentAttribute not in doc.document_attrs
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
#         except Exception, ex:
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
    assert NSFontAttributeName in attrs
    assert NSParagraphStyleAttributeName in attrs
    assert attrs is doc.default_text_attributes()

def test_TextDocument_reset_text_attributes():
    INDENT_SIZE = 42
    m = Mocker()
    app = m.replace("editxt.app")
    ps_class = m.replace(NSParagraphStyle, passthrough=False)
    doc = TextDocument.alloc().init()
    ts = doc.text_storage = m.mock(NSTextStorage)
    undoer = m.method(doc.undoManager)
    font = NSFont.fontWithName_size_("Monaco", 10.0)
    spcw = font.screenFontWithRenderingMode_(NSFontDefaultRenderingMode) \
        .advancementForGlyph_(ord(u" ")).width
    ps = ps_class.defaultParagraphStyle().mutableCopy() >> m.mock()
    ps.setTabStops_([])
    ps.setDefaultTabInterval_(spcw * INDENT_SIZE)
    real_ps = ps.copy() >> "<paragraph style>"
    attrs = {NSFontAttributeName: font, NSParagraphStyleAttributeName: real_ps}
    ts.addAttributes_range_(attrs, NSMakeRange(0, ts.length() >> 20))
    views = [
        (m.mock(TextDocumentView), m.mock(NSTextView)),
        (m.mock(TextDocumentView), None),
    ]
    app.iter_views_of_document(doc) >> (dv for dv, tv in views)
    for dv, tv in views:
        (dv.text_view << tv).count(1 if tv is None else 3)
        if tv is not None:
            tv.setTypingAttributes_(attrs)
            tv.setDefaultParagraphStyle_(real_ps)
    with m:
        doc.reset_text_attributes(INDENT_SIZE)
        eq_(doc.default_text_attributes(), attrs)

def test_setFileModificationDate_():
    from datetime import datetime
    dt = NSDate.date()
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
        exists = m.replace("os.path.exists")
        fileURL = m.method(doc.fileURL)
        modDate = m.method(doc.fileModificationDate)
        url = fileURL() >> (None if c.url_is_none else m.mock(NSURL))
        path = "<path>"
        if not c.url_is_none:
            url.path() >> path
            if (exists(path) >> c.exists):
                url.getResourceValue_forKey_error_(
                    None, NSURLContentModificationDateKey, None) \
                    >> (c.date_ok, c.loc_stat, None)
                if c.date_ok:
                    modDate() >> c.ext_stat
        with m:
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
        def end(): # this allows us to return early (reducing nested if's)
            with m:
                eq_(doc._filestat, c.prestat)
                doc.check_for_external_changes(win)
                eq_(doc._filestat,
                    (c.prestat if not c.extmod or c.win_is_none else c.modstat))
        m = Mocker()
        doc = TextDocument.alloc().init()
        win = None
        nsa_class = m.replace(Alert, passthrough=False)
        alert = m.mock(Alert)
        displayName = m.method(doc.displayName)
        isdirty = m.method(doc.isDocumentEdited)
        filestat = m.replace("editxt.util.filestat")
        reload = m.method(doc.reload_document)
        m.method(doc.is_externally_modified)() >> c.extmod
        if not c.extmod:
            return end()
        if isdirty() >> c.isdirty:
            if c.win_is_none:
                return end()
            win = m.mock(NSWindow)
            if c.prestat is not None:
                doc._filestat = c.prestat
            path = (m.method(doc.fileURL)() >> m.mock(NSURL)).path() >> "<path>"
            filestat(path) >> c.modstat
            if c.prestat == c.modstat:
                return end()
            (nsa_class.alloc() >> alert).init() >> alert
            displayName() >> "test.txt"
            alert.setMessageText_(u"“test.txt” source document changed")
            alert.setInformativeText_(u"Discard changes and reload?")
            alert.addButtonWithTitle_(u"Reload")
            alert.addButtonWithTitle_(u"Cancel")
            def callback(win, method):
                method(NSAlertFirstButtonReturn if c.reload else None)
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
                eq_(doc.text_storage, doc_ts)
        m = Mocker()
        doc = TextDocument.alloc().init()
        perform_clear_undo = m.method(doc.performSelector_withObject_afterDelay_)
        app = m.replace("editxt.app", passthrough=False)
        doc_log = m.replace("editxt.document.log")
        fileURL = m.method(doc.fileURL)
        fw = m.mock(NSFileWrapper)
        ts = m.mock(NSTextStorage)
        doc_ts = doc.text_storage = m.mock(NSTextStorage)
        url = fileURL() >> (None if c.url_is_none else m.mock(NSURL))
        if c.url_is_none:
            return end()
        exists = m.replace("os.path.exists")
        path = url.path() >> "<path>"
        if not exists(path) >> c.exists:
            return end()
        undo = m.method(doc.undoManager)() >> m.mock(NSUndoManager)
        undo.should_remove = False
        ts_class = m.replace(NSTextStorage, passthrough=False)
        (ts_class.alloc() >> ts).init() >> ts
        m.method(doc.revertToContentsOfURL_ofType_error_)(
            url, m.method(doc.fileType)() >> "<type>", None) \
            >> (c.read2_success, "<err>")
        undo.should_remove = True
        if not c.read2_success:
            doc_log.error(ANY, "<err>")
            return end()
        tv = m.mock(NSTextView)
        def views():
            for text_view_exists in c.view_state:
                view = m.mock(TextDocumentView)
                view.text_view >> (tv if text_view_exists else None)
                yield view
        views = list(views()) # why on earth is the intermediate var necessary?
        # I don't know, but it turns to None if we don't do it!! ???
        app.iter_views_of_document(doc) >> views
        text = ts.string() >> "<string>"
        range = NSRange(0, doc_ts.length() >> 10)
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
            tv.setSelectedRange_(NSRange(0, 0)) # TODO remove
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
    m.method(doc.updateChangeCount_)(NSChangeCleared)
    with m:
        doc._clearChanges()

class TestTextDocument(MockerTestCase):

    def test_get_with_path_1(self):
        dc = NSDocumentController.sharedDocumentController()
        eq_(len(dc.documents()), 0)
        path = self.makeFile(content="", suffix="txt")
        doc = TextDocument.get_with_path(path)
        assert isinstance(doc, TextDocument)
        assert os.path.samefile(path, doc.fileURL().path())
        doc.close()
        eq_(len(dc.documents()), 0)


    def test_get_with_path_2(self):
        path = self.makeFile(content="", suffix="txt")
        url = NSURL.fileURLWithPath_(path)
        dc = NSDocumentController.sharedDocumentController()
        eq_(len(dc.documents()), 0)
        doc1, err = dc.openDocumentWithContentsOfURL_display_error_(url, False, None)
        doc2 = TextDocument.get_with_path(path)
        assert doc1 is doc2
        doc1.close()
        eq_(len(dc.documents()), 0)

    def test_get_with_path_fails(self):
        from tempfile import mktemp
        from editxt.document import Error
        path = mktemp(suffix="txt")
        assert_raises(Error, TextDocument.get_with_path, path)
        assert not os.path.exists(path), \
            "critical failure: %s exists (but should not)" % path

    def test_untitled_displayName(self):
        dc = NSDocumentController.sharedDocumentController()
        doc, err = dc.makeUntitledDocumentOfType_error_(TEXT_DOCUMENT, None)
        assert doc.displayName() == "Untitled"

    def test_titled_displayName(self):
        dc = NSDocumentController.sharedDocumentController()
        path = self.makeFile(content="", prefix="text", suffix="txt")
        url = NSURL.fileURLWithPath_(path)
        doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(url, TEXT_DOCUMENT, None)
        assert doc.displayName() == os.path.split(path)[1]

    def test_readData_ofType(self):
        dc = NSDocumentController.sharedDocumentController()
        content = "test content"
        path = self.makeFile(content=content, prefix="text", suffix=".txt")
        url = NSURL.fileURLWithPath_(path)
        doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(url, TEXT_DOCUMENT, None)
        assert doc.text_storage.string() == content

    def test_saveDocument(self):
        from editxt.application import Application
        m = Mocker()
        app = m.replace("editxt.app", type=Application, passthrough=False)
        dc = NSDocumentController.sharedDocumentController()
        path = self.makeFile(content="", prefix="text", suffix=".txt")
        file = open(path)
        with closing(open(path)) as file:
            assert file.read() == ""
        url = NSURL.fileURLWithPath_(path)
        doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(url, TEXT_DOCUMENT, None)
        content = "test content"
        m.method(doc.update_syntaxer)()
        doc.text_storage.mutableString().appendString_(content)
        app.item_changed(doc, 2)
        app.save_open_projects()
        with m:
            doc.saveDocument_(None)
            with closing(open(path)) as file:
                saved_content = file.read()
            assert saved_content == content, "got %r" % saved_content

    def test_icon_cache(self):
        dc = NSDocumentController.sharedDocumentController()
        doc, err = dc.makeUntitledDocumentOfType_error_(TEXT_DOCUMENT, None)
        eq_(doc.icon_cache, (None, None))
        icon = doc.icon()
        assert isinstance(icon, NSImage)
        eq_(doc.icon_cache, ("", icon))

#     def test_icon_for_real_file(self):
#         from editxt.util import fetch_icon
#         dc = NSDocumentController.sharedDocumentController()
#         path = self.makeFile(content="", prefix="text", suffix=".txt")
#         url = NSURL.fileURLWithPath_(path)
#         doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(url, TEXT_DOCUMENT)
#         assert doc.icon().TIFFRepresentation() == fetch_icon(doc.file_path).TIFFRepresentation()

#     def _setup_new_document_with_main_view(self):
#         class MockView(object):
#             def bounds(self):
#                 return NSMakeRect(0, 0, 200, 200)
#             def addSubview_(self, view):
#                 pass
#         dc = NSDocumentController.sharedDocumentController()
#         content = "test content"
#         path = self.makeFile(content=content, prefix="text", suffix=".txt")
#         url = NSURL.fileURLWithPath_(path)
#         doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(url, TEXT_DOCUMENT)
#         doc.makeWindowControllers()
#         doc.set_main_view(MockView())
#         return doc
#
#     def test_document_font_after_load(self):
#         doc = self._setup_new_document_with_main_view()
#         attrs = doc.default_text_attributes()
#         assert doc.text_view.font() == attrs[NSFontAttributeName]

#     def test_document_is_in_project_documents(self):
#         dc = NSDocumentController.sharedDocumentController()
#         wcs = []
#         for x in xrange(3):
#             doc = self._setup_new_document_with_main_view()
#             prj = doc.project
#             assert doc in prj.documents()
#             wc = doc.windowControllers()[0]
#             if wcs:
#                 assert wc in wcs
#             else:
#                 wcs.append(wc)

def test_get_with_path():
    from editxt.document import TEXT_DOCUMENT, Error
    def test(c):
        assert not os.path.exists(c.path), c.path
        m = Mocker()
        dc = m.method(NSDocumentController.sharedDocumentController)() >> \
            m.mock(NSDocumentController)
        dc.typeForContentsOfURL_error_(ANY, None) >> (TEXT_DOCUMENT, None)
        dc.documentForURL_(ANY) >> None
        dc.makeDocumentWithContentsOfURL_ofType_error_(
            ANY, TEXT_DOCUMENT, None) >> (None, None)
        with m:
            assert_raises(Error, TextDocument.get_with_path, c.path)
        assert not os.path.exists(c.path), c.path
    c = TestConfig(path="/file.txt")
    yield test, c

def test_readFromData_ofType_error_():
    def test(c):
        m = Mocker()
        data = "<data>"
        typ = m.mock()
        doc = TextDocument.alloc().init()
        doc.text_storage = ts = m.mock(NSTextStorage)
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
            NSCharacterEncodingDocumentAttribute: "<encoding>"}
        ts = m.mock(NSTextStorage)
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
        doc.text_storage = ts = m.mock(NSTextStorage)
        ts.string() >> NSString.stringWithString_(c.text)
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
        yield test, c(text=u"\n", eol=eol, eol_char=eol_char)
        yield test, c(text=u"\n\r", eol=eol, eol_char=eol_char)
        yield test, c(text=u"\n\u2028", eol=eol, eol_char=eol_char)
        yield test, c(text=u"abc\ndef\r", eol=eol, eol_char=eol_char)
        #yield test, c(text=u"\u2029", eol=eol, eol_char=eol_char) # TODO make ths test pass
    yield test, c(text=u"\t", imode=TAB)
    yield test, c(text=u"  ", imode=SPC)
    yield test, c(text=u"  x", imode=SPC, isize=2)
    yield test, c(text=u"  \n   x", imode=SPC, isize=3, eol=const.NEWLINE_MODE_UNIX)
    yield test, c(text=u"  x\n     x", imode=SPC, isize=2, eol=const.NEWLINE_MODE_UNIX)

def test_makeWindowControllers():
    def test(ed_is_none):
        from editxt.application import Application
        doc = TextDocument.alloc().init()
        m = Mocker()
        app = m.replace("editxt.app", type=Application)
        dv_class = m.replace("editxt.document.TextDocumentView")
        dv = m.mock(TextDocumentView)
        ed = m.mock(Editor)
        app.current_editor() >> (None if ed_is_none else ed)
        if ed_is_none:
            app.create_editor() >> ed
        dv_class.create_with_document(doc) >> dv
        ed.add_document_view(dv)
        add_ed = m.method(doc.addWindowController_)
        add_ed(ed.wc >> m.mock(EditorWindowController)) # simulate function call
        ed.current_view = dv
        with m:
            doc.makeWindowControllers()
    yield test, True
    yield test, False

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
        app = m.replace("editxt.app", passthrough=False)
        doc = TextDocument.alloc().init()
        doc.text_storage = ts = m.mock(NSTextStorage)
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
    ts = doc.text_storage = m.mock(NSTextStorage)
    syn = doc.syntaxer = m.mock(SyntaxCache)
    range = ts.editedRange() >> m.mock(NSRange)
    syn.color_text(ts, range)
    with m:
        doc.textStorageDidProcessEditing_(None)

def test_updateChangeCount_():
    from editxt.application import Application
    m = Mocker()
    doc = TextDocument.alloc().init()
    app = m.replace("editxt.app", type=Application, passthrough=False)
    ctype = 0
    app.item_changed(doc, ctype)
    with m:
        doc.updateChangeCount_(ctype)

#     def updateChangeCount_(self, changeType, flag=[]):
#         super(TextDocument, self).updateChangeCount_(changeType)
#         proj = self.project
#         if proj:
#             proj.documentChanged_(self)

# def test_document_set_primary_window_controller():
#     def test(wc_has_doc, sv_in_subviews, doc_in_proj):
#         doc = TextDocument.alloc().init()
#         m = Mocker()
#         wc = m.mock(EditorWindowController)
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
    wc = m.mock(EditorWindowController)
    wcs() >> [wc]
    rwc(wc)
    with m:
        doc.close()
    assert doc.text_storage is None
