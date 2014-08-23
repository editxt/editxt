# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2014 Daniel Miller <millerdev@gmail.com>
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
from mocker import Mocker, expect, ANY, MATCH
from nose.tools import *
from editxt.test.test_document import property_value_util, get_content
from editxt.test.util import (assert_raises, gentest, make_file, TestConfig,
    replattr, tempdir, test_app)

import editxt.constants as const
import editxt.editor as mod
from editxt.controls.commandview import CommandView
from editxt.application import Application
from editxt.document import TextDocument
from editxt.editor import Editor
from editxt.project import Project
from editxt.window import Window, WindowController

log = logging.getLogger(__name__)

# log.debug("""TODO
#     implement Editor.pasteboard_data()
# """)


def verify_editor_interface(editor):
    from editxt.util import KVOProxy

    assert editor.id is not None
    assert not editor.is_dirty
    assert hasattr(editor, "file_path")

    dn = editor.name
    assert dn is not None
    icon = editor.icon()
    if isinstance(editor, Editor):
        assert editor.project is not None, editor.project
        assert icon is not None
        with assert_raises(AttributeError):
            editor.name = "something"
        assert editor.name == dn
        assert editor.is_leaf
        #assert not editor.expanded
    else:
        assert icon is None
        assert not editor.is_leaf
        assert editor.expanded

def test_editor_interface():
    with test_app("editor") as app:
        editor = app.windows[0].projects[0].editors[0]
        verify_editor_interface(editor)

def test_Editor_init():
    import editxt.document
    def test(kw):
        if "state" in kw:
            path = kw["state"]["path"]
        elif "path" in kw:
            path = kw["path"]
        else:
            path = None
            doc = kw["document"]
        m = Mocker()
        proj = m.mock(Project)
        doc_class = m.replace(editxt.document, 'TextDocument')
        default_state = m.replace(Editor, 'edit_state')
        if path is not None:
            doc = proj.window.app.document_with_path(path) >> "<document>"
        with m:
            result = Editor(proj, **kw)
            eq_(result.project, proj)
            eq_(result.document, doc)
            eq_(result.edit_state, kw.get("state", default_state))
    yield test, {"path": "/path"}
    yield test, {"state": {"path": "<document path>"}}
    yield test, {"document": "<document>"}

def test_Editor_project():
    with test_app("""
            window(A)
                project(0)
                    editor(a)*
                    editor(b)
            window(B)
                project(1)*
        """) as app:
        print(test_app.config(app))
        win_A, win_B = app.windows
        proj_0, = win_A.projects
        proj_1, = win_B.projects
        editor_a, editor_b = proj_0.editors
        editor_a.project = proj_1
        eq_(editor_a.project, proj_1)
        eq_(test_app.config(app),
            "window(A) project(0) editor(b)* window(B) project(1)*")

def test_Editor_window():
    def test(has_scroll_view):
        m = Mocker()
        win = m.mock(ak.NSWindow)
        doc = m.mock(TextDocument)
        dv = Editor(None, document=doc)
        if has_scroll_view:
            dv.scroll_view = sv = m.mock(ak.NSScrollView)
            sv.window() >> win
        else:
            win = None
        with m:
            result = dv.window()
            eq_(result, win)
    yield test, True
    yield test, False

def test_Editor_save():
    @gentest
    @test_app("editor")
    def test(app, path, prompt=False):
        prompt = (True,) if prompt else ()
        initial_content = None if "missing" in path else "initial"
        with make_file(path, content=initial_content) as real_path:
            m = Mocker()
            window = app.windows[0]
            editor = window.projects[0].editors[0]
            document = editor.document
            save_document_as = m.method(window.save_document_as)
            prompt_to_overwrite = m.method(window.prompt_to_overwrite)
            has_path_changed = m.method(document.file_changed_since_save)
            if os.path.isabs(path):
                document.file_path = path = real_path
            elif path:
                document.file_path = path
            document.text = "saved text"
            def save_prompt(document, callback):
                if "nodir" in path:
                    os.mkdir(os.path.dirname(real_path))
                print("saving as", real_path)
                callback(real_path)
            if prompt or path != real_path or "nodir" in path:
                expect(save_document_as(editor, ANY)).call(save_prompt)
            elif has_path_changed() >> ("moved" in path):
                expect(prompt_to_overwrite(editor, ANY)).call(save_prompt)
            called = []
            def callback():
                called.append(1)
            with m:
                editor.save(*prompt, callback=callback)
                eq_(get_content(real_path), "saved text")
                assert called, "callback not called"

    # prompt or no real path
    yield test("/existing.txt", prompt=True)
    yield test("missing.txt")
    yield test("/nodir/missing.txt")
    yield test("/moved.txt", prompt=True)

    # path changed, file exists
    yield test("/moved.txt")

    # else
    yield test("/existing.txt")
    yield test("/missing.txt")

def test_document_set_main_view_of_window():
    def test(c):
        m = Mocker()
        win = m.mock(ak.NSWindow)
        doc = m.mock(TextDocument)
        editor = Editor(None, document=doc)
        soft_wrap = m.property(editor, "soft_wrap")
        view = m.mock(ak.NSView)
        main = m.mock()
        text = m.mock(ak.NSTextView)
        scroll = m.mock(ak.NSScrollView)
        setup_main_view = m.replace(mod, 'setup_main_view')
        frame = view.bounds() >> ak.NSMakeRect(0, 0, 50, 16)
        if c.sv_is_none:
            eq_(editor.main_view, None)
            eq_(editor.text_view, None)
            eq_(editor.scroll_view, None)
            eq_(editor.command_view, None)
            setup_main_view(editor, frame) >> main
            main.top >> scroll
            main.bottom >> m.mock(CommandView)
            scroll.documentView() >> text
            soft_wrap.value = doc.app.config["soft_wrap"] >> c.soft_wrap
        else:
            editor.main_view = main
            editor.text_view = text
            editor.scroll_view = scroll
            main.setFrame_(frame)
        view.addSubview_(main)
        win.makeFirstResponder_(text)
        scroll.verticalRulerView().invalidateRuleThickness()
        doc.update_syntaxer()
        doc.check_for_external_changes(win)
        with m:
            editor.set_main_view_of_window(view, win)
    c = TestConfig()
    yield test, c(sv_is_none=True, soft_wrap=const.WRAP_NONE)
    yield test, c(sv_is_none=False, soft_wrap=const.WRAP_WORD)

def test_get_soft_wrap():
    def test(c):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = Editor(None, document=doc)
        if c.tv_is_none:
            dv.text_view = None
        else:
            tv = dv.text_view = m.mock(ak.NSTextView)
            tc = None if c.tc_is_none else m.mock(ak.NSTextContainer)
            (tv.textContainer() << tc).count(1, 2)
            if tc is not None:
                tc.widthTracksTextView() >> \
                    (True if c.mode == const.WRAP_WORD else False)
        with m:
            result = dv.soft_wrap
            eq_(result, c.mode)
    c = TestConfig(tv_is_none=False, tc_is_none=False)
    yield test, c(mode=const.WRAP_NONE)
    yield test, c(mode=const.WRAP_WORD)
    yield test, c(tv_is_none=True, mode=None)
    yield test, c(tc_is_none=True, mode=None)

def test_set_soft_wrap():
    def test(c):
        m = Mocker()
        doc = m.mock(TextDocument)
        wrap = (c.mode != const.WRAP_NONE)
        dv = Editor(None, document=doc)
        sv = dv.scroll_view = m.mock(ak.NSScrollView)
        tv = dv.text_view = m.mock(ak.NSTextView)
        tc = tv.textContainer() >> m.mock(ak.NSTextContainer)
        if wrap:
            size = sv.contentSize() >> m.mock(fn.NSRect)
            width = size.width >> 100.0
            tv.setFrameSize_(size)
            tv.sizeToFit()
        else:
            width = const.LARGE_NUMBER_FOR_TEXT
        tc.setContainerSize_(fn.NSMakeSize(width, const.LARGE_NUMBER_FOR_TEXT))
        tc.setWidthTracksTextView_(wrap)
        tv.setHorizontallyResizable_(not wrap)
        tv.setAutoresizingMask_(ak.NSViewWidthSizable
            if wrap else ak.NSViewWidthSizable | ak.NSViewHeightSizable)
        with m:
            dv.soft_wrap = c.mode
    c = TestConfig(mode=const.WRAP_NONE)
    yield test, c
    yield test, c(mode=const.WRAP_WORD)

def test_Editor_document_properties():
    def test(c):
        m = Mocker()
        regundo = m.replace(mod, 'register_undo_callback')
        repnl = m.replace(mod, 'replace_newlines')
        doc = m.mock(TextDocument)
        dv = Editor(None, document=doc)
        proxy = m.property(dv, 'proxy')
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
        undoman = x.doc.undoManager() >> x.m.mock(fn.NSUndoManager)
        undoman.isUndoing() >> c.undoing
        if not c.undoing:
            undoman.isRedoing() >> c.redoing
        if not (c.undoing or c.redoing):
            x.repnl(x.dv.text_view, const.EOLS[x.c.value])
        setattr(x.doc.props, c.attr, c.value)
        def _undo(undoman, undo):
            undo()
        expect(x.regundo(undoman, ANY)).call(_undo)
        setattr(x.dv.proxy, c.attr, c.default)
    c = TestConfig(do=do, attr="newline_mode",
        default=const.NEWLINE_MODE_UNIX, undoing=False, redoing=False)
    yield test, c(value=const.NEWLINE_MODE_UNIX, default=const.NEWLINE_MODE_MAC)
    yield test, c(value=const.NEWLINE_MODE_UNIX)
    yield test, c(value=const.NEWLINE_MODE_MAC)
    yield test, c(value=const.NEWLINE_MODE_WINDOWS)
    yield test, c(value=const.NEWLINE_MODE_UNICODE)
    yield test, c(value=const.NEWLINE_MODE_MAC, undoing=True)
    yield test, c(value=const.NEWLINE_MODE_MAC, redoing=True)

def test_Editor_prompt():
    from editxt.controls.alert import Alert
    eq_(ak.NSAlertSecondButtonReturn - ak.NSAlertFirstButtonReturn, 1)
    eq_(ak.NSAlertThirdButtonReturn - ak.NSAlertFirstButtonReturn, 2)
    def test(c):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = Editor(None, document=doc)
        dv_window = m.method(dv.window)
        alert_class = m.replace(mod, 'Alert')
        callback = m.mock(name="callback")
        win = dv_window() >> (m.mock(ak.NSWindow) if c.has_window else None)
        if c.has_window:
            alert = alert_class.alloc() >> m.mock(Alert); alert.init() >> alert
            alert.setAlertStyle_(ak.NSInformationalAlertStyle)
            alert.setMessageText_(c.message)
            if c.info:
                alert.setInformativeText_(c.info)
            buttons = []
            for i in range(c.buttons):
                text = "Button_%i" % i
                buttons.append(text)
                alert.addButtonWithTitle_(text)
            def do(window, callback):
                callback(ak.NSAlertFirstButtonReturn + c.response)
                return True
            expect(alert.beginSheetModalForWindow_withCallback_(win, ANY)).call(do)
        else:
            buttons = ["" for i in range(c.buttons)]
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

def test_Editor_change_indentation():
    TAB = const.INDENT_MODE_TAB
    SPC = const.INDENT_MODE_SPACE
    def test(c):
        m = Mocker()
        regundo = m.replace(mod, 'register_undo_callback')
        convert = m.replace(mod, 'change_indentation')
        doc = m.mock(TextDocument)
        dv = Editor(None, document=doc)
        tv = dv.text_view = m.mock(ak.NSTextView)
        if c.convert:
            old_indent = "\t" if c.oldm is TAB else (" " * c.olds)
            new_indent = "\t" if c.newm is TAB else (" " * c.news)
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
            undoman = doc.undoManager() >> m.mock(fn.NSUndoManager)
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
        dv = Editor(None, document=doc)
        m.property(dv, "soft_wrap")
        m.property(dv, "file_path")
        if c.tv_is_none:
            if c.set_state:
                dv.edit_state = state = dict(key="value")
            else:
                state = {}
        else:
            dv.text_view = m.mock(ak.NSTextView)
            dv.scroll_view = m.mock(ak.NSScrollView)
            sel = m.mock(fn.NSRange)
            sp = m.mock(fn.NSPoint)
            dv.text_view.selectedRange() >> sel
            dv.scroll_view.contentView().bounds().origin >> sp
            sel.location >> "<sel.location>"
            sel.length >> "<sel.length>"
            sp.x >> "<sp.x>"
            sp.y >> "<sp.y>"
            dv.soft_wrap >> c.soft_wrap
            state = dict(
                selection=["<sel.location>", "<sel.length>"],
                scrollpoint=["<sp.x>", "<sp.y>"],
                soft_wrap=c.soft_wrap,
            )
        (dv.file_path << ("<path>" if c.path_is_valid else None)).count(1, 2)
        if c.path_is_valid:
            state["path"] = "<path>"
        with m:
            result = dv.edit_state
            eq_(result, state)
            if c.tv_is_none and c.set_state:
                assert result is not state, "identity check should fail: must be a new (mutable) dict"
    c = TestConfig(tv_is_none=False, path_is_valid=True, soft_wrap=const.WRAP_WORD)
    yield test, c
    yield test, c(path_is_valid=False)
    yield test, c(soft_wrap=const.WRAP_NONE)
    yield test, c(tv_is_none=True, set_state=False)
    yield test, c(tv_is_none=True, set_state=True)

def test_set_edit_state():
    from editxt.util import KVOProxy
    def test(state=None, ts_len=0):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = Editor(None, document=doc)
        proxy_prop = m.property(dv, "proxy")
        if state is None:
            eq_state = state = {}
        else:
            eq_state = dict(state)
            eq_state.setdefault("selection", (0, 0))
            eq_state.setdefault("scrollpoint", (0, 0))
            eq_state.setdefault("soft_wrap", const.WRAP_NONE)
            point = eq_state["scrollpoint"]
            sel = eq_state["selection"]
            dv.text_view = m.mock(ak.NSTextView)
            dv.scroll_view = m.mock(ak.NSScrollView)
            proxy = proxy_prop.value >> m.mock(Editor)
            proxy.soft_wrap = eq_state["soft_wrap"]
            doc.text_storage.length() >> ts_len
            if ts_len - 1 > 0:
                dv.text_view.setSelectedRange_(fn.NSRange(ts_len - 1, 0))
            dv.scroll_view.documentView().scrollPoint_(fn.NSPoint(*point))
            if sel[0] < ts_len - 1:
                if sel[0] + sel[1] > ts_len - 1:
                    sel = (sel[0], ts_len - 1 - sel[0])
                dv.text_view.setSelectedRange_(fn.NSRange(*sel))
        with m:
            dv.edit_state = state
            if not isinstance(state, dict):
                eq_(state, eq_state)
    yield test, # tests case when (doc.text_view is None)
    yield test, {}
    yield test, {"selection": (1, 1)}
    yield test, {"scrollpoint": (1, 1)}
    yield test, {"soft_wrap": const.WRAP_NONE}
    yield test, {"scrollpoint": (0, 0), "selection": (0, 0), "soft_wrap": const.WRAP_NONE}
    yield test, {"scrollpoint": (5, 5), "selection": (5, 5), "soft_wrap": const.WRAP_WORD}
    yield test, {"scrollpoint": (0, 0), "selection": (0, 0)}, 2
    yield test, {"scrollpoint": (0, 0), "selection": (0, 1)}, 2
    yield test, {"scrollpoint": (0, 0), "selection": (0, 2)}, 2

def test_reset_edit_state():
    def test(_state_exists):
        m = Mocker()
        doc = m.mock(TextDocument)
        dv = Editor(None, document=doc)
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
#         dv = Editor(None, document=doc)
#         _file_path_property = Editor.file_path
#         try:
#             Editor.file_path = c.path
#             path_exists(c.path) >> c.path_exists
#             with m:
#                 result = list(dv.pasteboard_data())
#                 eq_(result, c.result)
#         finally:
#             Editor.file_path = _file_path_property
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
    def test(num_editors):
        m = Mocker()
        doc = m.mock(TextDocument)
        proj = m.mock(Project)
        dv = Editor(proj, document=doc)
        ed = proj.window >> m.mock(Window)
        app = doc.app >> m.mock(Application)
        app.iter_windows_with_editor_of_document(doc) >> (ed for x in range(num_editors))
        if num_editors == 1:
            ed.current_editor = dv
            info = app.context.put(dv.maybe_close) >> 42
            def doc_should_close(dv, selector, context):
                assert hasattr(TextDocument, "document_shouldClose_contextInfo_"), \
                    "missing selector: Editor document:shouldClose:contextInfo:"
            expect(doc.canCloseDocumentWithDelegate_shouldCloseSelector_contextInfo_(
                doc, "document:shouldClose:contextInfo:", info)).call(doc_should_close)
        else:
            ed.discard_and_focus_recent(dv)
        with m:
            dv.perform_close()
        eq_(TextDocument.document_shouldClose_contextInfo_.signature, b'v@:@ii')
    for num_editors in range(3):
        yield test, num_editors

def test_Editor_maybe_close():
    def test(should_close):
        m = Mocker()
        proj = m.mock(Project)
        editor = Editor(proj, document=m.mock(TextDocument))
        window = m.mock(Window)
        if should_close:
            (proj.window >> window).discard_and_focus_recent(editor)
        with m:
            editor.maybe_close(should_close)
    yield test, True
    yield test, False

def test_Editor_close():
    def test(c):
        with test_app(c.app) as app:
            m = Mocker()
            teardown_main_view = m.replace(mod, 'teardown_main_view')
            editor = app.windows[0].projects[0].editors[0]
            editor.text_view = None if c.tv_is_none else m.mock(ak.NSTextView)
            doc = editor.document
            if c.ts_is_none:
                doc.text_storage = None
            else:
                text_storage = doc.text_storage
                text_storage.setDelegate_(doc)
                remove_layout = m.method(text_storage.removeLayoutManager_)
            wc = editor.project.window.wc = m.mock(WindowController)
            if not (c.tv_is_none or c.ts_is_none):
                lm = editor.text_view.layoutManager() >> m.mock(ak.NSLayoutManager)
                remove_layout(lm)
            if c.main_is_none:
                editor.main_view = None
            else:
                editor.main_view = m.mock()
                teardown_main_view(editor.main_view)
            wc.setup_current_editor(ANY)
            with m:
                editor.close()
            eq_(editor.command_view, None)
            eq_(editor.scroll_view, None)
            eq_(editor.text_view, None)
            eq_(editor.document, None)
            eq_(editor.proxy, None)
            if c.close_doc:
                eq_(doc.text_storage, None)
                if not c.ts_is_none:
                    eq_(text_storage.delegate(), None)
            eq_(test_app.config(app), c.end)

    c = TestConfig(app="editor(a)",
        ts_is_none=False,
        tv_is_none=False,
        main_is_none=False,
        remove_window=True,
        close_doc=True,
        end="window project*",
    )
    yield test, c
    yield test, c(ts_is_none=True)
    yield test, c(tv_is_none=True)
    yield test, c(ts_is_none=True, tv_is_none=True)
    yield test, c(main_is_none=True)
    yield test, c(app="editor(a) editor(b)", end="window project editor(b)*")
    yield test, c(app="editor(a) editor(a)", end="window project editor(a)*",
                  close_doc=False)
    yield test, c(app="editor(a) window editor(a)",
                  end="window project* window project editor(a)",
                  close_doc=False)

def test_Editor_on_do_command():
    import editxt.platform.constants as const
    def test(command, setup_mocks):
        m = Mocker()
        doc = m.mock(TextDocument)
        editor = Editor(None, document=doc)
        textview = m.mock(ak.NSTextView)
        expected = setup_mocks(m, editor, textview)
        with m:
            result = editor.on_do_command(command)
            eq_(result, expected)

    yield test, "unknown command", lambda m, dv, tv: False

    def setup_mocks(m, editor, textview):
        cmd = m.replace(editor, "command_view", spec=CommandView)
        cmd.dismiss()
        return True
    yield test, const.ESCAPE, setup_mocks

