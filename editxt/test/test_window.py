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
import re
from collections import defaultdict
from functools import partial

import AppKit as ak
import Foundation as fn

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import *

import editxt.constants as const
from editxt.application import Application
from editxt.window import WindowController, Window
from editxt.document import DocumentController, TextDocument
from editxt.editor import Editor
from editxt.platform.kvo import proxy_target
from editxt.project import Project
from editxt.test.noseplugins import slow_skip
from editxt.util import representedObject

from editxt.test.util import (do_method_pass_through, gentest, make_dirty,
    TestConfig, Regex, replattr, tempdir, test_app)

import editxt.window as mod

log = logging.getLogger(__name__)
# log.debug("""TODO test
#     Window.iter_dropped_paths
#     Window.iter_dropped_id_list
# """)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Window tests

# log.debug("""TODO implement
# """)

def test_WindowConroller__init__():
    @test_app
    def test(app, args):
        ed = Window(app, **args)
        assert len(ed.projects) == 0
        assert len(ed.recent) == 0
        assert ed.wc is not None
        if args:
            assert ed.state is args["state"]
        eq_(ed.command.window, ed)
    c = TestConfig()
    yield test, {}
    yield test, {"state": "<state data>"}

def test_window_did_load():
    @test_app
    def test(app, state):
        import editxt.platform.views as cells
        from editxt.window import BUTTON_STATE_SELECTED
        from editxt.util import load_image
        m = Mocker()
        ed = Window(app, state)
        wc = ed.wc = m.mock(WindowController)
        _setstate = m.method(ed._setstate)
        new_project = m.method(ed.new_project)
        load_image_cache = {}
        _load_image = m.mock()
        def load_image(name):
            try:
                img = load_image_cache[name]
                _load_image(name)
            except KeyError:
                img = load_image_cache[name] = m.mock()
                _load_image(name) >> img
            return img

        wc.docsView.setRefusesFirstResponder_(True)
        wc.plusButton.setRefusesFirstResponder_(True)
        wc.plusButton.setImage_(load_image(const.PLUS_BUTTON_IMAGE))
        wc.propsViewButton.setRefusesFirstResponder_(True)
        wc.propsViewButton.setImage_(load_image(const.PROPS_DOWN_BUTTON_IMAGE))
        wc.propsViewButton.setAlternateImage_(load_image(const.PROPS_UP_BUTTON_IMAGE))

        win = ed.wc.window() >> m.mock(ak.NSWindow)
        note_ctr = m.replace(fn, 'NSNotificationCenter')
        note_ctr.defaultCenter().addObserver_selector_name_object_(
            ed.wc, "windowDidBecomeKey:", ak.NSWindowDidBecomeKeyNotification, win)

        wc.cleanImages = {
            cells.BUTTON_STATE_HOVER: load_image(const.CLOSE_CLEAN_HOVER),
            cells.BUTTON_STATE_NORMAL: load_image(const.CLOSE_CLEAN_NORMAL),
            cells.BUTTON_STATE_PRESSED: load_image(const.CLOSE_CLEAN_PRESSED),
            BUTTON_STATE_SELECTED: load_image(const.CLOSE_CLEAN_SELECTED),
        }
        wc.dirtyImages = {
            cells.BUTTON_STATE_HOVER: load_image(const.CLOSE_DIRTY_HOVER),
            cells.BUTTON_STATE_NORMAL: load_image(const.CLOSE_DIRTY_NORMAL),
            cells.BUTTON_STATE_PRESSED: load_image(const.CLOSE_DIRTY_PRESSED),
            BUTTON_STATE_SELECTED: load_image(const.CLOSE_DIRTY_SELECTED),
        }

        wc.docsView.registerForDraggedTypes_(
            [const.DOC_ID_LIST_PBOARD_TYPE, ak.NSFilenamesPboardType])

        _setstate(state)
        if state:
            ed.projects = [m.mock(Project)]
        else:
            new_project()

        with replattr(mod, 'load_image', load_image), m:
            ed.window_did_load()
            eq_(len(ed.projects), (1 if state else 0))
            assert ed._state is None
            #assert ed.window_settings == "<settings>"
    yield test, None
    yield test, "<serial data>"

def test__setstate():
    from itertools import count
    from editxt.util import RecentItemStack
    keygen = count()
    class Item(dict):
        def __init__(self, **kwargs):
            self["id"] = next(keygen)
            self.update(kwargs)
        @property
        def proxy(self):
            return self
        @property
        def _target(self):
            return self
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)
    @test_app
    def test(app, data):
        m = Mocker()
        ed = Window(app)
        ed.wc = m.mock(WindowController)
        ed.discard_and_focus_recent = m.method(ed.discard_and_focus_recent)
        project_class = m.replace(mod, 'Project')
        ed.recent = m.mock(RecentItemStack)
        ws = m.property(ed, 'window_settings')
        projects = []
        if data:
            for serial in data.get("project_serials", []):
                proj = project_class(ed, serial=serial) >> Item()
                projects.append(proj)
            for pi, di in data.get("recent_items", []):
                if pi < 1:
                    while len(ed.projects) <= pi:
                        docs = []
                        proj = Item(editors=docs)
                        projects.append(proj)
                        ed.projects.append(proj)
                    proj = ed.projects[pi]
                    if di == "<project>":
                        ed.recent.push(proj.id)
                    else:
                        if di < 2:
                            while len(proj.editors) <= di:
                                proj.editors.append(Item())
                            ed.recent.push(docs[di].id)
            ed.discard_and_focus_recent(None)
            if 'window_settings' in data:
                ws.value = data['window_settings']
        with m:
            ed._setstate(data)
            eq_(list(ed.projects), projects)
    yield test, None
    yield test, dict()
    yield test, dict(project_serials=["<serial>"])
    yield test, dict(recent_items=[[0, 2], [0, 0], [0, "<project>"], [0, 1], [1, 0]])
    yield test, dict(window_settings="<window_settings>")

def test_state():
    @test_app
    def test(app, c):
        m = Mocker()
        def exists(path):
            return True
        ed = Window(app)
        ed.projects = projs = []
        ed.recent = c.recent
        m.property(ed, 'window_settings').value >> '<settings>'
        psets = []
        items = {}
        for i, p in enumerate(c.projs):
            proj = m.mock(Project)
            projs.append(proj)
            pserial = proj.serialize() >> ("proj_%i" % p.id)
            psets.append(pserial)
            # setup for recent items
            proj.id >> p.id
            items[p.id] = [i, "<project>"]
            docs = proj.editors >> []
            offset = 0
            for j, d in enumerate(p.docs):
                editor = m.mock(Editor)
                docs.append(editor)
                if d > 0:
                    path = "/path/do/file%s.txt" % d
                    (editor.file_path << path).count(2)
                    editor.id >> d
                    items[d] = [i, j - offset]
                else:
                    offset += 1
                    editor.file_path >> None
        rits = [items[ri] for ri in c.recent if ri in items]
        data = {'window_settings': '<settings>'}
        if psets:
            data["project_serials"] = psets
        if rits:
            data["recent_items"] = rits
        with replattr(os.path, 'exists', exists), m:
            eq_(ed.state, data)
    c = TestConfig(window='<settings>')
    p = lambda ident, docs=(), **kw:TestConfig(id=ident, docs=docs, **kw)
    yield test, c(projs=[], recent=[])
    yield test, c(projs=[p(42)], recent=[42])
    yield test, c(projs=[p(42, docs=[35])], recent=[35, 42])
    yield test, c(projs=[p(42, docs=[-32, 35])], recent=[35, 42])

def test_discard_and_focus_recent():
    from editxt.util import RecentItemStack
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        ed.wc = m.mock(WindowController)
        ed.projects = projs = []
        ed.recent = m.mock(RecentItemStack)
        app = m.replace(ed, 'app')
        new_current_editor = None
        cv = m.property(ed, "current_editor")
        @mod.contextmanager
        def suspend():
            yield
        m.method(ed.suspend_recent_updates)() >> suspend()
        lookup = {}
        for p in c.hier:
            proj = m.mock(Project)
            proj.id >> p.id
            docs = []
            for d in p.docs:
                dv = m.mock(Editor)
                dv.id >> d.id
                docs.append(dv)
                if c.id in (p.id, d.id):
                    ed.recent.discard(d.id)
                    dv.project >> proj
                    dv.close()
                else:
                    lookup[d.id] = dv
            proj.editors >> docs
            if p.id == c.id:
                ed.recent.discard(p.id)
                proj.close()
            else:
                lookup[p.id] = proj
            projs.append(proj)
        item = m.mock()
        item.id >> c.id
        with m:
            ed.discard_and_focus_recent(item)
    item = lambda i, **kw: TestConfig(id=i, **kw)
    c = TestConfig(id=2, recent=[], hier=[ # hierarchy of items in the window
        item(0, docs=[item(1), item(2), item(3)]),
        item(4, docs=[item(5), item(6), item(7)]),
        item(8, docs=[item(9), item(12), item(13)]),
    ])
    yield test, c(id=42, hier=[])
    yield test, c(id=42)
    yield test, c
    yield test, c(recent=[0, 10])
    yield test, c(recent=[10, 0])
    yield test, c(recent=[20, 2])
    yield test, c(recent=[2, 20])
    yield test, c(id=0, recent=[0, 10, 2, 1, 3, 5, 7])

def test_get_current_editor():
    with test_app() as app:
        ed = Window(app)
        ed._current_editor = obj = object()
        eq_(ed.current_editor, obj)

def test_set_current_editor():
    from editxt.util import RecentItemStack
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        wc = ed.wc = m.mock(WindowController)
        insert_items = m.method(ed.insert_items)
        ed.recent = m.mock(RecentItemStack)
        find_project_with_editor = m.method(ed.find_project_with_editor)
        dv = (None if c.editor_class is None else m.mock(c.editor_class))
        if c.editor_is_current:
            ed._current_editor = dv
        elif c.editor_class is not None:
            ed.recent.push(dv.id >> m.mock())
            setup = c.editor_class is Editor and not c.view_is_main
            wc.setup_current_editor(dv) >> setup
            if setup:
                if c.proj_is_none:
                    find_project_with_editor(dv) >> None
                    insert_items([dv])
                else:
                    find_project_with_editor(dv) >> m.mock(Project)
        with m:
            ed.current_editor = dv
        assert ed._current_editor is dv
    c = TestConfig(editor_is_current=False, editor_class=Editor)
    yield test, c(editor_is_current=True)
    yield test, c(editor_class=None)
    for is_main in (True, False):
        for no_project in (True, False):
            yield test, c(view_is_main=is_main, proj_is_none=no_project)
    yield test, c(editor_class=Project)

def test_selected_editor_changed():
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        ed.wc = wc = m.mock(WindowController)
        cv = m.property(ed, "current_editor")
        sel = [m.mock() for x in range(c.numsel)]
        wc.docsController.selected_objects >> sel
        if sel:
            if c.is_current_selected:
                cv.value >> sel[0]
            else:
                cv.value >> m.mock()
                cv.value = sel[0]
        with m:
            ed.selected_editor_changed()
    c = TestConfig(numsel=0)
    yield test, c
    for ics in (True, False):
        yield test, c(numsel=1, is_current_selected=ics)
        yield test, c(numsel=5, is_current_selected=ics)

def test_suspend_recent_updates():
    def test(c):
        with test_app(c.init) as app:
            window = app.windows[0]
            editor = window.current_editor
            real = window.recent
            assert real is not None
            with window.suspend_recent_updates():
                assert window.recent is not real
                window.recent.push(editor.id + 42)
                if c.remove:
                    item = test_app.get(c.remove, app)
                    if isinstance(item, Editor):
                        item.project.editors.remove(item)
                    else:
                        item.window.projects.remove(item)
            eq_(test_app.config(app), c.final)
    c = TestConfig(remove=None)
    yield test, c(init="editor*", final="window project editor*")
    yield test, c(init="editor(1)* editor(2)",
                  final="window project editor(1)* editor(2)")
    yield test, c(init="editor(1)* editor(2)", remove="editor(1)",
                  final="window project editor(2)*")
    yield test, c(init="editor(1)* editor(2)", remove="editor(2)",
                  final="window project editor(1)*")
    yield test, c(init="project(a) editor(1)* project(b) editor(2)",
                  final="window project(b) editor(2)*", remove="project(a)")

def test_save_methods():
    def test(cfg, save, prompt=False):
        with test_app(cfg) as app:
            m = Mocker()
            window = app.windows[0]
            current = window.current_editor
            if save is not None:
                method = m.method(current.save)
                if save:
                    method(prompt=prompt)
            with m:
                (window.save_as if prompt else window.save)()

    yield test, "window", None
    yield test, "project*", False
    yield test, "project* editor", False
    yield test, "editor*", True
    yield test, "editor*", True, True

def test_save_document_as():
    assert hasattr(Window, "save_document_as")

def test_prompt_to_overwrite():
    assert hasattr(Window, "prompt_to_overwrite")

def test__directory_and_filename():
    def test(path, directory, name, mkdir=False):
        if os.path.isabs(path):
            path = path.lstrip(os.path.sep)
            assert not os.path.isabs(path), path
            with tempdir() as tmp:
                path = os.path.join(tmp, path)
                if mkdir:
                    assert not os.path.exists(os.path.dirname(path)), path
                    os.mkdir(os.path.dirname(path))
                result = Window._directory_and_filename(path)
                result = (result[0][len(tmp):] or "/"), result[1]
        else:
            result = Window._directory_and_filename(path)
        eq_(result, (directory, name))
    yield test, "file.txt", None, "file.txt"
    yield test, "/file.txt", "/", "file.txt"
    yield test, "somedir/file.txt", None, "file.txt"
    yield test, "/somedir/file.txt", "/", "file.txt"
    yield test, "/somedir/file.txt", "/somedir", "file.txt", True

def test_new_project():
    with test_app() as app:
        m = Mocker()
        ed = Window(app)
        m.property(ed, "current_editor").value = ANY
        m.method(Project.create_editor)() >> m.mock()
        with m:
            result = ed.new_project()
            assert result in ed.projects, ed.projects
            eq_(list(result.editors), [])
            eq_(result.window, ed)

def test_toggle_properties_pane():
    from editxt.controls.splitview import ThinSplitView
    slow_skip()
    @test_app
    def test(app, c):
        m = Mocker()
        nsanim = m.replace(ak, 'NSViewAnimation')
        nsdict = m.replace(fn, 'NSDictionary')
        nsval = m.replace(fn, 'NSValue')
        nsarr = m.replace(fn, 'NSArray')
        ed = Window(app)
        ed.wc = wc = m.mock(WindowController)
        tree_view = m.mock(ak.NSScrollView); (wc.docsScrollview << tree_view).count(2)
        prop_view = m.mock(ak.NSView); (wc.propsView << prop_view).count(2, 3)
        tree_rect = tree_view.frame() >> m.mock(fn.NSRect)
        prop_rect = prop_view.frame() >> m.mock(fn.NSRect)
        wc.propsViewButton.state() >> (ak.NSOnState if c.is_on else ak.NSOffState)
        if c.is_on:
            prop_rect.size.height >> 10
            tree_rect.size.height = (tree_rect.size.height >> 20) + 9
            tree_rect.origin.y = prop_rect.origin.y >> 4
            prop_rect.size.height = 0.0
        else:
            tree_rect.size.height = (tree_rect.size.height >> 216.0) - 115.0
            if c.mid_resize:
                (prop_rect.size.height << 100.0).count(2)
                tree_rect.size.height = (tree_rect.size.height >> 100.0) + 99.0
            else:
                prop_rect.size.height >> 0
            tree_rect.origin.y = (prop_rect.origin.y >> 0) + 115.0
            prop_rect.size.height = 116.0
            prop_view.setHidden_(False)
        resize_tree = nsdict.dictionaryWithObjectsAndKeys_(
            tree_view, ak.NSViewAnimationTargetKey,
            (nsval.valueWithRect_(tree_rect) >> m.mock()), ak.NSViewAnimationEndFrameKey,
            None,
        ) >> m.mock(fn.NSDictionary)
        resize_props = nsdict.dictionaryWithObjectsAndKeys_(
            prop_view, ak.NSViewAnimationTargetKey,
            (nsval.valueWithRect_(prop_rect) >> m.mock()), ak.NSViewAnimationEndFrameKey,
            None,
        ) >> m.mock(fn.NSDictionary)
        anims = nsarr.arrayWithObjects_(resize_tree, resize_props, None) >> m.mock(fn.NSArray)
        anim = nsanim.alloc() >> m.mock(ak.NSViewAnimation)
        anim.initWithViewAnimations_(anims) >> anim
        anim.setDuration_(0.25)
        anim.startAnimation()
        with m:
            ed.toggle_properties_pane()
    c = TestConfig()
    yield test, c(is_on=True)
    yield test, c(is_on=False, mid_resize=True)
    yield test, c(is_on=False, mid_resize=False)

def test_find_project_with_editor():
    with test_app() as app:
        ed = Window(app)
        doc = app.document_with_path(None)
        proj = Project(ed)
        dv = Editor(proj, document=doc)
        proj.insert_items([dv])
        assert dv.document is doc
        ed.projects.append(proj)
        eq_(ed.find_project_with_editor(dv), proj)
        dv = object()
        eq_(ed.find_project_with_editor(dv), None)

def test_find_project_with_path():
    @test_app
    def test(app, c):
        m = Mocker()
        def exists(path):
            return True
        def samefile(f1, f2):
            eq_(f2, c.path)
            return f1 == f2
        ed = Window(app)
        ed.projects = projects = []
        found_proj = None
        for path in c.paths:
            proj = m.mock(Project)
            projects.append(proj)
            if found_proj is None:
                proj.file_path >> path
                if path is None:
                    continue
                if path == c.path:
                    found_proj = proj
        with replattr(
            (os.path, 'exists', exists),
            (os.path, 'samefile', samefile),
        ), m:
            result = ed.find_project_with_path(c.path)
            eq_(result, found_proj)
    def path(i):
        return "/path/to/proj_%s.%s" % (i, const.PROJECT_EXT)
    c = TestConfig(path=path(1), paths=[])
    yield test, c
    yield test, c(paths=[None])
    yield test, c(paths=[path(1)])
    yield test, c(paths=[path(0), path(1)])
    yield test, c(paths=[path(0), path(1), path(2), path(1)])

def test_get_current_project():
    def test(cfg, index, create=False, after=None):
        args = {"create": True} if create else {}
        with test_app(cfg) as app:
            window = app.windows[0]
            result = window.get_current_project(**args)
            eq_(test_app.config(app), after or cfg)
            if index is None:
                eq_(result, None)
            else:
                eq_(result, window.projects[index])
    yield test, "window", None
    yield test, "window", 0, True, "window project[0]"
    yield test, "window project", 0
    yield test, "window project* project", 0
    yield test, "window project project*", 1
    yield test, "window project -project*", 1
    yield test, "window project project editor*", 1
    yield test, "window project editor project editor", 0
    yield test, "window -project editor project editor", 1

def test_Window_iter_editors_of_document():
    DOC = "the document we're looking for"
    @test_app
    def test(app, config, total_editors):
        ed = Window(app)
        m = Mocker()
        editors = []
        doc = m.mock(TextDocument)
        ed.projects = projs = []
        for proj_has_editor in config:
            proj = m.mock(Project)
            projs.append(proj)
            dv = (m.mock(Editor) if proj_has_editor else None)
            proj.iter_editors_of_document(doc) >> ([] if dv is None else [dv])
            if dv is not None:
                editors.append(dv)
        with m:
            result = list(ed.iter_editors_of_document(doc))
            eq_(result, editors)
            eq_(len(result), total_editors)
    yield test, [], 0
    yield test, [False], 0
    yield test, [True], 1
    yield test, [False, True, True, False, True], 3

def test_tool_tip_for_item():
    def test(doctype, null_path):
        m = Mocker()
        view = m.mock(ak.NSOutlineView)
        if doctype is not None:
            tip = "test_tip"
            doc = m.mock(doctype)
            (doc.file_path << (None if null_path else tip)).count(1, 2)
        else:
            tip = doc = None
        item = m.mock()
        view.realItemForOpaqueItem_(item) >> doc
        with m, test_app() as app:
            ed = Window(app)
            result_tip = ed.tooltip_for_item(view, item)
            eq_(result_tip, (None if null_path else tip))
    for doctype in (TextDocument, Project, None):
        yield test, doctype, True
        yield test, doctype, False

def test_should_edit_item():
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        item = m.mock()
        col = m.mock(ak.NSTableColumn)
        if (col.isEditable() >> c.col_is_editable):
            obj = m.mock(Project if c.item_is_project else Editor)
            if c.item_is_project:
                obj.can_rename() >> c.can_rename
            representedObject(item) >> obj
        with m:
            result = ed.should_edit_item(col, item)
            eq_(result, c.result)
    c = TestConfig(col_is_editable=True, item_is_project=True, result=False)
    yield test, c(col_is_editable=False)
    yield test, c(item_is_project=False)
    yield test, c(can_rename=False)
    yield test, c(can_rename=True, result=True)

def test_close_button_clicked():
    @test_app
    def test(app, row, num_rows, doc_class=None):
        m = Mocker()
        ed = Window(app)
        ed.wc = m.mock(WindowController)
        ed.recent = m.mock()
        dv = ed.wc.docsView >> m.mock(ak.NSOutlineView)
        dv.numberOfRows() >> num_rows
        discard = m.method(ed.discard_and_focus_recent)
        if row < num_rows:
            item = m.mock()
            dv.itemAtRow_(row) >> item
            real_item = dv.realItemForOpaqueItem_(item) >> m.mock(doc_class)
            discard(real_item)
            def callback(do_close):
                do_close()
            expect(real_item.interactive_close(ANY)).call(callback)
        with m:
            ed.close_button_clicked(row)
    yield test, 0, 0
    yield test, 1, 0
    for doc_class in (Project, Editor):
        yield test, 0, 1, doc_class

def test_window_did_become_key():
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        win = m.mock(ak.NSWindowController)
        cv = m.property(ed, "current_editor")
        dv = cv.value >> (m.mock(c.editor_type) if c.has_current else None)
        if c.has_current and c.editor_type is Editor:
            dv.document.check_for_external_changes(win)
        with m:
            ed.window_did_become_key(win)
    c = TestConfig(has_current=False, editor_type=Editor)
    yield test, c
    yield test, c(has_current=True)
    yield test, c(has_current=True, editor_type=Project)

def test_Window_should_close():
    @gentest
    def test(config, prompts=[], should_close=False, close=True):
        calls = []
        def do_close():
            calls.append("close")
        with test_app(config) as app:
            window = app.windows[0]
            for win in app.windows:
                for project in win.projects:
                    for editor in project.editors:
                        if "dirty" in editor.file_path:
                            make_dirty(editor.document)
            result = window.should_close(do_close)
            eq_(window.wc.prompts, prompts)
            eq_(calls, ["close"] if close and not should_close else [])
            eq_(result, should_close)

    yield test("editor", should_close=True)
    yield test("editor(dirty)", ["close dirty"], close=False)
    yield test("editor(dirty.save)", ["close dirty.save", "save dirty.save"], close=False) # cancel save
    yield test("editor(/dirty.save)", ["close dirty.save"])
    yield test("editor(/dirty.dont_save)", ["close dirty.dont_save"])
    yield test("editor(dirty) window project editor(dirty)", should_close=True)

def test_window_will_close():
    @test_app
    def test(app, window_settings_loaded, num_projects):
        m = Mocker()
        ed = Window(app)
        ed.window_settings_loaded = window_settings_loaded
        app = m.replace(ed, 'app')
        with m.order():
            app.discard_window(ed)
        with m:
            ed.window_will_close()
    yield test, True, 0
    yield test, False, 0
    yield test, False, 1
    yield test, False, 3

def test_get_window_settings():
    @test_app
    def test(app, c):
        settings = dict(
            frame_string="<frame string>",
            splitter_pos="<splitter_pos>",
            properties_hidden=c.props_hidden,
        )
        m = Mocker()
        ed = Window(app)
        ed.wc = m.mock(WindowController)
        ed.wc.frame_string >> settings["frame_string"]
        ed.wc.splitter_pos >> settings["splitter_pos"]
        ed.wc.properties_hidden >> (ak.NSOnState if c.props_hidden else ak.NSOffState)
        with m:
            result = ed.window_settings
            eq_(result, settings)
    c = TestConfig()
    yield test, c(props_hidden=True)
    yield test, c(props_hidden=False)

def test_set_window_settings_with_null_settings():
    with test_app() as app:
        ed = Window(app)
        m = Mocker()
        settings = m.mock(dict)
        settings.get("frame_string") >> None
        settings.get("splitter_pos") >> None
        settings.get("properties_hidden", False) >> False
        with m:
            ed.window_settings = settings

def test_set_window_settings():
    from editxt.controls.splitview import ThinSplitView
    with test_app() as app:
        m = Mocker()
        ed = Window(app)
        ed.wc = m.mock(WindowController)
        fs = "<test frame string>"
        sp = "<test splitter position>"
        ed.wc.frame_string = fs
        ed.wc.splitter_pos = sp
        ed.wc.properties_hidden = True
        with m:
            ed.window_settings = dict(frame_string=fs, splitter_pos=sp, properties_hidden=True)

def test_close():
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        ed.wc = wc = m.mock(WindowController)
        ed.projects = []
        ed.window_settings_loaded = c.ws_loaded
        for x in range(3):
            proj = m.mock(Project)
            proj.close()
            ed.projects.append(proj)
        #wc.docsController.setContent_(None)
        with m:
            if not c.wc_is_none:
                assert ed.wc is not None
                assert list(ed.projects)
            ed.close()
            assert not ed.window_settings_loaded
            #assert ed.wc is None
            #assert not list(ed.projects)
    c = TestConfig(wc_is_none=False)
    yield test, c(wc_is_none=True, ws_loaded=False)
    for wsl in (True, False):
        yield test, c(ws_loaded=wsl)

# drag/drop tests ~~~~~~~~~~~~~~~~~~~~~~~

def test_is_project_drag():
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        ed.iter_dropped_id_list = m.method(ed.iter_dropped_id_list)
        pb = m.mock(ak.NSPasteboard)
        result_items = []
        info = m.mock() #NSDraggingInfo
        items = []
        pb = info.draggingPasteboard() >> m.mock(ak.NSPasteboard)
        pb.availableTypeFromArray_(ed.supported_drag_types) >> c.accepted_type
        if c.accepted_type == const.DOC_ID_LIST_PBOARD_TYPE:
            id_list = pb.propertyListForType_(const.DOC_ID_LIST_PBOARD_TYPE) >> m.mock()
            ed.iter_dropped_id_list(id_list) >> items
            factories = dict(
                p=(lambda:m.mock(Project)),
                d=(lambda:m.mock(Editor)),
            )
        elif c.accepted_type == ak.NSFilenamesPboardType:
            pb.propertyListForType_(ak.NSFilenamesPboardType) >> items
            factories = dict(
                p=(lambda:"/path/to/project." + const.PROJECT_EXT),
                d=(lambda:"/path/to/document.txt"),
            )
        else:
            factories = None
        if factories is not None:
            for it in c.items:
                items.append(factories[it]())
        with m:
            result = ed.is_project_drag(info)
            eq_(result, c.result)
    c = TestConfig(result=False)
    yield test, c(items="", accepted_type="unknown type")
    for atype in (const.DOC_ID_LIST_PBOARD_TYPE, ak.NSFilenamesPboardType):
        for items in ("d", "p", "pdp", "ppp"):
            result = not items.replace("p", "")
            yield test, c(items=items, accepted_type=atype, result=result)

def test_write_items_to_pasteboard():
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        ov = m.mock(ak.NSOutlineView)
        pb = m.mock(ak.NSPasteboard)
        def path_exists(path):
            return True
        items = []
        if c.items:
            types = [const.DOC_ID_LIST_PBOARD_TYPE]
            data = defaultdict(list)
            for ident, item in enumerate(c.items):
                opaque = object() # outline view item
                items.append(opaque)
                dragitem = m.mock(item.type)
                ov.realItemForOpaqueItem_(opaque) >> dragitem
                assert hasattr(item.type, "id"), "unknown attribute: %s.id" % item.type.__name__
                dragitem.id >> ident
                data[const.DOC_ID_LIST_PBOARD_TYPE].append(ident)
                dragitem.file_path >> item.path
                if item.path is not None:
                    if ak.NSFilenamesPboardType not in data:
                        types.append(ak.NSFilenamesPboardType)
                    data[ak.NSFilenamesPboardType].append(item.path)
            if data:
                pb.declareTypes_owner_(types, None)
                for dtype, ddata in data.items():
                    pb.setPropertyList_forType_(ddata, dtype)
        with replattr(os.path, 'exists', path_exists), m:
            result = ed.write_items_to_pasteboard(ov, items, pb)
            eq_(result, c.result)
    c = TestConfig(result=True)
    yield test, c(items=[], result=False)
    item = TestConfig(type=Editor, path="/path/to/file")
    yield test, c(items=[item])
    yield test, c(items=[item(type=Project)])
    yield test, c(items=[item(type=Project), item])
    yield test, c(items=[item(path=None)])
    yield test, c(items=[item(type=Project, path=None)])

def test_validate_drop():
    @test_app
    def test(app, config):
        m = Mocker()
        ed = Window(app)
        ed.wc = m.mock(WindowController)
        ov = m.mock(ak.NSOutlineView)
        # TODO investigate where NSDraggingInfo went during the upgrade to 10.5
        info = m.mock() #NSDraggingInfo)
        item = m.mock()
        index = 0
        ed.is_project_drag = m.method(ed.is_project_drag)
        ed.is_project_drag(info) >> config.is_proj
        if config.is_proj:
            if not config.item_is_none:
                obj = "<item.observedObject>"
                representedObject(item) >> obj
                if config.path_is_none:
                    path = None
                else:
                    path = m.mock(fn.NSIndexPath)
                    path.indexAtPosition_(0) >> config.path_index
                    ov.setDropItem_dropChildIndex_(None, config.path_index)
                ed.wc.docsController.indexPathForObject_(obj) >> path
            else:
                item = None
                index = config.index
                if index < 0:
                    ed.projects = ["<proj>"] * config.num_projs
                    ov.setDropItem_dropChildIndex_(None, config.num_projs)
        else:
            if not config.item_is_none:
                if config.item_is_proj:
                    index = config.index
                    obj = m.mock(type=Project)
                    if index < 0:
                        obj.editors >> (["<doc>"] * config.proj_docs)
                        ov.setDropItem_dropChildIndex_(item, config.proj_docs)
                else:
                    obj = m.mock(type=Editor)
                representedObject(item) >> obj
            else:
                item = None
                index = config.index
                if config.index < 0:
                    ed.projects = ["<proj>"] * (config.last_proj_index + 1)
                    if config.last_proj_index > -1:
                        path = fn.NSIndexPath.indexPathWithIndex_(config.last_proj_index)
                        proj = m.mock(Project)
                        node = m.mock()
                        ed.wc.docsController.nodeAtArrangedIndexPath_(path) >> node
                        representedObject(node) >> proj
                        proj.editors >> (["<doc>"] * config.proj_docs)
                        ov.setDropItem_dropChildIndex_(node, config.proj_docs)
                    else:
                        ov.setDropItem_dropChildIndex_(None, -1)
        with m:
            result = ed.validate_drop(ov, info, item, index)
            eq_(result, config.result)
    cfg = TestConfig(is_proj=True, item_is_none=False, result=ak.NSDragOperationGeneric)
    for i in (-1, 0, 1, 2):
        yield test, cfg(item_is_none=True, index=i, num_projs=2)
    yield test, cfg(path_is_none=True, result=ak.NSDragOperationNone)
    for p in (0, 1, 2):
        yield test, cfg(path_is_none=False, path_index=p)
    cfg = cfg(is_proj=False)
    for i in (-1, 0, 2):
        yield test, cfg(item_is_proj=True, index=i, proj_docs=2)
    yield test, cfg(item_is_proj=False, result=ak.NSDragOperationNone)
    cfg = cfg(item_is_none=True)
    yield test, cfg(index=-1, last_proj_index=-1)
    yield test, cfg(index=-1, last_proj_index=0, proj_docs=0)
    yield test, cfg(index=-1, last_proj_index=0, proj_docs=2)
    yield test, cfg(index=-1, last_proj_index=2, proj_docs=2)
    yield test, cfg(index=0, result=ak.NSDragOperationNone)
    yield test, cfg(index=1)
    yield test, cfg(index=2)

def test_accept_drop():
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        ed.wc = m.mock(WindowController)
        ed.insert_items = m.method(ed.insert_items)
        ed.iter_dropped_id_list = m.method(ed.iter_dropped_id_list)
        ed.iter_dropped_paths = m.method(ed.iter_dropped_paths)
        ov = m.mock(ak.NSOutlineView)
        # TODO investigate where NSDraggingInfo went during the upgrade to 10.5
        parent = None if c.item_is_none else m.mock()
        index = 0
        act = None
        items = m.mock()
        pb = m.mock(ak.NSPasteboard)
        pb.availableTypeFromArray_(ed.supported_drag_types) >> c.accepted_type
        if c.accepted_type == const.DOC_ID_LIST_PBOARD_TYPE:
            id_list = pb.propertyListForType_(const.DOC_ID_LIST_PBOARD_TYPE) >> m.mock()
            ed.iter_dropped_id_list(id_list) >> items
            act = const.MOVE
        elif c.accepted_type == ak.NSFilenamesPboardType:
            paths = pb.propertyListForType_(ak.NSFilenamesPboardType) >> m.mock()
            items = ed.iter_dropped_paths(paths) >> items
        else:
            items = None
            assert c.accepted_type is None
        if items is not None:
            ed.insert_items(items, parent, index, act) >> c.result
        with m:
            result = ed.accept_drop(ov, pb, parent, index)
            eq_(result, c.result)
    c = TestConfig(result=True, item_is_none=False)
    yield test, c(accepted_type=const.DOC_ID_LIST_PBOARD_TYPE)
    yield test, c(accepted_type=ak.NSFilenamesPboardType)
    yield test, c(accepted_type=ak.NSFilenamesPboardType, item_is_none=True)
    yield test, c(accepted_type=None, result=False)

def test_iter_dropped_id_list():
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app, None)
        app = m.replace(ed, 'app')
        result_items = []
        if c.has_ids:
            ids = []
            for it in c.ids:
                ids.append(it.id)
                item = m.mock()
                app.find_item_with_id(it.id) >> (item if it.found else None)
                if it.found:
                    result_items.append(item)
        else:
            ids = None
        with m:
            result = list(ed.iter_dropped_id_list(ids))
            eq_(result, result_items)
    c = TestConfig(has_ids=True)
    ix = lambda id, found=True: TestConfig(id=id, found=found)
    yield test, c(has_ids=False)
    yield test, c(ids=[])
    yield test, c(ids=[ix(0)])
    yield test, c(ids=[ix(0), ix(1)])
    yield test, c(ids=[ix(0, False)])
    yield test, c(ids=[ix(0), ix(1, False)])

def test_iter_dropped_paths():
    def doc(num, tmp):
        path = os.path.join(tmp, "doc%s.txt" % num)
        with open(path, mode="w") as fh:
            fh.write('doc')
        return path
    def sym(num, tmp):
        path = os.path.join(tmp, "doc%s.sym" % num)
        os.symlink(path + ".txt", path)
        return path
    def proj(num, tmp):
        path = os.path.join(tmp, "proj_%s" % num)
        os.mkdir(path)
        return path
    @test_app
    def test(app, c):
        m = Mocker()
        ed = Window(app)
        app = m.replace(ed, 'app')
        dc = m.mock(DocumentController)
        result_items = []
        with tempdir() as tmp:
            if c.has_paths:
                paths = []
                for it in c.paths:
                    path = it.create(tmp)
                    paths.append(path)
                    if it.ignored:
                        continue
                    doc = app.document_with_path(path) \
                        >> m.mock(path, spec=TextDocument)
                    result_items.append(doc)
            else:
                paths = None
            with m:
                result = list(ed.iter_dropped_paths(paths))
                eq_(result, result_items)
    c = TestConfig(has_paths=True)
    def path(create, ignored=False, num=[0]):
        num[0] += 1
        if create is None:
            return TestConfig(create=(lambda tmp: None), ignored=ignored)
        return TestConfig(create=partial(create, num[0]), ignored=ignored)
    yield test, c(has_paths=False)
    yield test, c(paths=[])
    yield test, c(paths=[path(None)])
    yield test, c(paths=[path(doc)])
    yield test, c(paths=[path(sym)])
    yield test, c(paths=[path(doc), path(sym), path(doc)])
    yield test, c(paths=[path(proj, ignored=True)])
#    yield test, c(paths=[path(proj)])
#    yield test, c(paths=[path(proj), path(doc), path(proj)])
    #yield test, c(paths=[path(proj, is_open=False)])

def test_insert_items():
    def test(c):
        def get_parent_index(drop, offset=0):
            if any(v in '0123456789' for v in drop[0]):
                assert all(v in '0123456789' for v in drop[0]), drop
                return None, pindex
            return project, dindex + offset
        def namechar(item, seen=set()):
            name = test_app.name(item, app)
            name = name[len(type(item).__name__):]
            assert name.startswith(("(", "[", "<")), name
            assert name.endswith((")", "]", ">")), name
            name = name[1:-1]
            assert name not in seen, (item, name)
            seen.add(name)
            return name

        config = []
        pindex = dindex = -1
        project = None
        for i, char in enumerate(c.init + ' '):
            if char == "|":
                config.append("window")
                pindex = dindex = -1
                continue
            if char == ' ':
                if i == c.drop[1]:
                    offset = 1 if project is not None else 0
                    parent, index = get_parent_index(c.drop, offset)
                dindex = -1
                continue
            if char == "*":
                config[-1] += "*"
                if i == c.drop[1]:
                    raise ValueError("invalid drop index: {!r}".format(c.drop))
                continue
            name = "({})".format(char)
            if char in '0123456789':
                item = project = "project" + name
                pindex += 1
            else:
                item = "editor" + name
                dindex += 1
            config.append(item)
            if i == c.drop[1]:
                parent, index = get_parent_index(c.drop)

        config = " ".join(config)
        print(config)
        with test_app(config) as app:
            name_to_item = {}
            for window in app.windows:
                for project in window.projects:
                    char = namechar(project)
                    project.name = char
                    name_to_item[char] = project
                    for editor in project.editors:
                        char = namechar(editor)
                        editor.document.file_path = char
                        name_to_item[char] = editor

            for char in c.drop[0]:
                if char not in name_to_item and char not in '0123456789':
                    name_to_item[char] = TextDocument(app, char)

            items = [name_to_item[char] for char in c.drop[0]] \
                    if "*" in c.final and c.init != c.final else []

            m = Mocker()
            window = app.windows[0]
            if "project" in c:
                eq_(c.drop[1], -1, "invalid test configuration; drop index "
                                   "must be -1 when project is specified")
                parent = c.project
                index = c.drop[1]
                if c.project == const.CURRENT:
                    args = ()
                elif c.project is None:
                    args = (None,)
                else:
                    args = (name_to_item[c.project],)
            else:
                if parent is not None:
                    parent = name_to_item[parent[8:-1]]
                args = (parent, index, c.action)

            print('drop(%s) %s at %s of %s' % (c.action, c.drop[0], index, parent))
            with m:
                result = window.insert_items(items, *args)

            eq_(result, items)

            final = ["window"]
            for char in c.final:
                if char == " ":
                    continue
                if char == "|":
                    final.append("window")
                    continue
                if char == "*":
                    final[-1] += "\\*"
                    continue
                name = r"\({}\)".format(char)
                if char in "0123456789":
                    if char not in c.init:
                        name = r"\[.\]"
                    final.append("project" + name)
                    continue
                if char.isupper():
                    name = "\[{} .\]".format(char.lower())
                final.append("editor" + name)
            final = "^" + " ".join(final) + "$"
            eq_(test_app.config(app), Regex(final, repr=final.replace("\\", "")))

            def eq(a, b):
                msg = lambda:"{} != {}".format(
                    test_app.name(a, app),
                    test_app.name(b, app),
                )
                eq_(a, b, msg)
            for window in app.windows:
                for project in window.projects:
                    eq(project.window, window)
                    for editor in project.editors:
                        eq(editor.project, project)

    # number = project
    # letter in range a-f = document
    # letter in rnage A-F = new editor of document
    # space before project allows drop on project (insert at end)
    # pipe (|) delimits windows
    # so ' 0ab*c 1 2de| 3*fa' is...
    #   window
    #       project 0
    #           document a
    #           document b (currently selected)
    #           document c
    #       project 1
    #       project 2
    #           document d
    #           document e
    #   window
    #       project 3 (currently selected)
    #           document f
    #           document a
    #
    # drop=(<dropped item(s)>, <drop index in init>)

    config = TestConfig(init=' 0ab*c 1 2de')

    c = config(action=const.MOVE)
    yield test, c(drop=('', 0), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 1), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 2), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 3), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 5), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 6), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 7), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 8), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 9), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 10), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 11), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 12), final=' 0ab*c 1 2de')

    yield test, c(drop=('a', 0), final=' 0bca* 1 2de')
    yield test, c(drop=('a', 1), final=' 0bca* 1 2de')
    yield test, c(drop=('a', 2), final=' 0ab*c 1 2de')
    yield test, c(drop=('a', 3), final=' 0ab*c 1 2de')
    yield test, c(drop=('a', 5), final=' 0ba*c 1 2de')
    yield test, c(drop=('a', 6), final=' 0bca* 1 2de')
    yield test, c(drop=('a', 7), final=' 0bc 1a* 2de')
    yield test, c(drop=('a', 8), final=' 0bc 1a* 2de')
    yield test, c(drop=('a', 9), final=' 0bc 1 2dea*')
    yield test, c(drop=('a', 10), final=' 0bc 1 2a*de')
    yield test, c(drop=('a', 11), final=' 0bc 1 2da*e')
    yield test, c(drop=('a', 12), final=' 0bc 1 2dea*')

    yield test, c(drop=('f', 0), final=' 0abcF* 1 2de')
    yield test, c(drop=('f', 1), final=' 0abcF* 1 2de')
    yield test, c(drop=('f', 2), final=' 0F*abc 1 2de')
    yield test, c(drop=('f', 3), final=' 0aF*bc 1 2de')
    yield test, c(drop=('f', 5), final=' 0abF*c 1 2de')
    yield test, c(drop=('f', 6), final=' 0abcF* 1 2de')
    yield test, c(drop=('f', 7), final=' 0abc 1F* 2de')
    yield test, c(drop=('f', 8), final=' 0abc 1F* 2de')
    yield test, c(drop=('f', 9), final=' 0abc 1 2deF*')
    yield test, c(drop=('f', 10), final=' 0abc 1 2F*de')
    yield test, c(drop=('f', 11), final=' 0abc 1 2dF*e')
    yield test, c(drop=('f', 12), final=' 0abc 1 2deF*')

    yield test, c(drop=('2', 0), final=' 0abc 1 2*de')
    yield test, c(drop=('2', 1), final=' 2*de 0abc 1')
    yield test, c(drop=('2', 2), final=' 2*de 0abc 1')
    yield test, c(drop=('2', 3), final=' 2*de 0abc 1')
    yield test, c(drop=('2', 5), final=' 2*de 0abc 1')
    yield test, c(drop=('2', 6), final=' 2*de 0abc 1')
    yield test, c(drop=('2', 7), final=' 0abc 2*de 1')
    yield test, c(drop=('2', 8), final=' 0abc 2*de 1')
    yield test, c(drop=('2', 9), final=' 0ab*c 1 2de')
    yield test, c(drop=('2', 10), final=' 0ab*c 1 2de')
    yield test, c(drop=('2', 11), final=' 0ab*c 1 2de')
    yield test, c(drop=('2', 12), final=' 0ab*c 1 2de')

    c = config(action=const.COPY)
    yield test, c(drop=('', 0), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 1), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 2), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 3), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 5), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 6), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 7), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 8), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 9), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 10), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 11), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 12), final=' 0ab*c 1 2de')

    yield test, c(drop=('a', 0), final=' 0abcA* 1 2de')
    yield test, c(drop=('a', 1), final=' 0abcA* 1 2de')
    yield test, c(drop=('a', 2), final=' 0A*abc 1 2de')
    yield test, c(drop=('a', 3), final=' 0aA*bc 1 2de')
    yield test, c(drop=('a', 5), final=' 0abA*c 1 2de')
    yield test, c(drop=('a', 6), final=' 0abcA* 1 2de')
    yield test, c(drop=('a', 7), final=' 0abc 1A* 2de')
    yield test, c(drop=('a', 8), final=' 0abc 1A* 2de')
    yield test, c(drop=('a', 9), final=' 0abc 1 2deA*')
    yield test, c(drop=('a', 10), final=' 0abc 1 2A*de')
    yield test, c(drop=('a', 11), final=' 0abc 1 2dA*e')
    yield test, c(drop=('a', 12), final=' 0abc 1 2deA*')

    c = config(action=None)
    yield test, c(drop=('', 0), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 1), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 2), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 3), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 5), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 6), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 7), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 8), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 9), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 10), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 11), final=' 0ab*c 1 2de')
    yield test, c(drop=('', 12), final=' 0ab*c 1 2de')

    yield test, c(drop=('a', 0), final=' 0a*bc 1 2de')
    yield test, c(drop=('a', 1), final=' 0a*bc 1 2de')
    yield test, c(drop=('a', 2), final=' 0a*bc 1 2de')
    yield test, c(drop=('a', 3), final=' 0a*bc 1 2de')
    yield test, c(drop=('a', 5), final=' 0a*bc 1 2de')
    yield test, c(drop=('a', 6), final=' 0a*bc 1 2de')
    yield test, c(drop=('a', 7), final=' 0abc 1A* 2de')
    yield test, c(drop=('a', 8), final=' 0abc 1A* 2de')
    yield test, c(drop=('a', 9), final=' 0abc 1 2deA*')
    yield test, c(drop=('a', 10), final=' 0abc 1 2A*de')
    yield test, c(drop=('a', 11), final=' 0abc 1 2dA*e')
    yield test, c(drop=('a', 12), final=' 0abc 1 2deA*')

    yield test, c(drop=('f', 0), final=' 0abcF* 1 2de')
    yield test, c(drop=('f', 1), final=' 0abcF* 1 2de')
    yield test, c(drop=('f', 2), final=' 0F*abc 1 2de')
    yield test, c(drop=('f', 3), final=' 0aF*bc 1 2de')
    yield test, c(drop=('f', 5), final=' 0abF*c 1 2de')
    yield test, c(drop=('f', 6), final=' 0abcF* 1 2de')
    yield test, c(drop=('f', 7), final=' 0abc 1F* 2de')
    yield test, c(drop=('f', 8), final=' 0abc 1F* 2de')
    yield test, c(drop=('f', 9), final=' 0abc 1 2deF*')
    yield test, c(drop=('f', 10), final=' 0abc 1 2F*de')
    yield test, c(drop=('f', 11), final=' 0abc 1 2dF*e')
    yield test, c(drop=('f', 12), final=' 0abc 1 2deF*')

    # cannot copy project yet
#    yield test, c(drop=('2', 0), final=' 0abc 1 2de')
#    yield test, c(drop=('2', 1), final=' 2de 0abc 1')
#    yield test, c(drop=('2', 2), final=' 2de 0abc 1')
#    yield test, c(drop=('2', 3), final=' 2de 0abc 1')
#    yield test, c(drop=('2', 4), final=' 2de 0abc 1')
#    yield test, c(drop=('2', 5), final=' 2de 0abc 1')
#    yield test, c(drop=('2', 6), final=' 0abc 2de 1')
#    yield test, c(drop=('2', 7), final=' 0abc 2de 1')
#    yield test, c(drop=('2', 8), final=' 0abc 1 2de')
#    yield test, c(drop=('2', 9), final=' 0abc 1 2de')
#    yield test, c(drop=('2', 10), final=' 0abc 1 2de')
#    yield test, c(drop=('2', 11), final=' 0abc 1 2de')

    c = config(action=None, init=' 0ab*c 1 2de')
    yield test, c(drop=('a', -1), final=' 0a*bc 1 2de', project=const.CURRENT)
    yield test, c(drop=('a', -1), final=' 0a*bc 1 2de', project=None)
    yield test, c(drop=('a', -1), final=' 0abc 1 2deA*', project='2')

    c = config(action=None, init=' 0abc 1* 2de')
    yield test, c(drop=('a', -1), final=' 0abc 1A* 2de', project=const.CURRENT)
    yield test, c(drop=('a', -1), final=' 0abc 1A* 2de', project=None)
    yield test, c(drop=('a', -1), final=' 0abc 1 2deA*', project='2')

    c = config(action=None, init=' 0abc 1 2de*')
    yield test, c(drop=('a', -1), final=' 0abc 1 2deA*', project=const.CURRENT)
    yield test, c(drop=('a', -1), final=' 0abc 1 2deA*', project=None)
    yield test, c(drop=('a', -1), final=' 0abc 1 2deA*', project='2')

    c = config(init=' 0a | 1bc', action=const.MOVE)
    yield test, c(drop=('b', 1), final=' 0ab* | 1c*')
    yield test, c(drop=('b', 2), final=' 0b*a | 1c*')

    yield test, c(drop=('1', 0), final=' 0a 1*bc |')
    yield test, c(drop=('1', 1), final=' 1*bc 0a |')

    # TODO implement move
#    c = config(init=' 0a* | 1b*c', action=const.MOVE)
#    yield test, c(drop=('b', 1), final=' 0ab* | 1c*')
#    yield test, c(drop=('b', 2), final=' 0b*a | 1c*')
#
#    yield test, c(drop=('1', 0), final=' 0a 1b*c |')
#    yield test, c(drop=('1', 1), final=' 1b*c 0a |')

    #yield test, c(drop=('a', 6), final=' 0 | 1bca*') # should fail (item inserted in wrong window)

def test_undo_manager():
    @gentest
    def test(config, has_doc=True, check_editor=True):
        with test_app(config) as app:
            window = app.windows[0]
            result = window.undo_manager
            if has_doc:
                eq_(result, window.current_editor.undo_manager)
            else:
                eq_(result, None)
                if check_editor:
                    eq_(window.current_editor, None)
    yield test("window", has_doc=False)
    yield test("window project", has_doc=False)
    yield test("window project* editor", has_doc=False, check_editor=False)
    yield test("window project editor* editor")
    yield test("window project editor editor*")
