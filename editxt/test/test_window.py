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
from collections import defaultdict
from functools import partial

import AppKit as ak
import Foundation as fn

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import *

import editxt
import editxt.constants as const
from editxt.application import Application, DocumentController, DocumentSavingDelegate
from editxt.window import WindowController, Window
from editxt.document import Editor, TextDocument
from editxt.platform.kvo import proxy_target
from editxt.project import Project
from editxt.test.noseplugins import slow_skip
from editxt.util import representedObject

from editxt.test.util import (do_method_pass_through, TestConfig, Regex,
    replattr, tempdir, test_app)

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
    def test(args):
        ed = Window(editxt.app, **args)
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
    def test(state):
        import editxt.platform.views as cells
        from editxt.window import BUTTON_STATE_SELECTED
        from editxt.util import load_image
        m = Mocker()
        ed = Window(editxt.app, state)
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

        wc.setShouldCloseDocument_(False)
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
    def test(data):
        m = Mocker()
        ed = Window(editxt.app)
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
    def test(c):
        m = Mocker()
        def exists(path):
            return True
        ed = Window(editxt.app)
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
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
        ed.wc = m.mock(WindowController)
        ed.projects = projs = []
        ed.recent = m.mock(RecentItemStack)
        app = m.replace(ed, 'app')
        new_current_editor = None
        cv = m.property(ed, "current_editor")
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
        recent = list(reversed(c.recent))
        while True:
            ident = ed.recent.pop() >> (recent.pop() if recent else None)
            if ident is None:
                break
            item = lookup.get(ident)
            if item is not None:
                cv.value = new_current_editor = item
                if not recent:
                    current_ident = ident
                recent.append(ident)
                break
        bool(ed.recent); m.result(bool(recent))
        if not recent:
            if c.hier and new_current_editor is not None:
                ed.recent.push(new_current_editor.id >> c.hier[0].id)
            else:
                if new_current_editor is None:
                    ed.current_editor >> None
                else:
                    ed.recent.push(new_current_editor.id >> current_ident)
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
    ed = Window(editxt.app)
    ed._current_editor = obj = object()
    eq_(ed.current_editor, obj)

def test_set_current_editor():
    from editxt.util import RecentItemStack
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
        wc = ed.wc = m.mock(WindowController)
        insert_items = m.method(ed.insert_items)
        ed.recent = m.mock(RecentItemStack)
        dv = (None if c.editor_class is None else m.mock(c.editor_class))
        if c.editor_is_current:
            ed._current_editor = dv
        else:
            ed._current_editor = m.mock(ak.NSView)
            mv = wc.mainView >> m.mock(ak.NSView)
            sv = m.mock(ak.NSView)
            (mv.subviews() << [sv]).count(1, 2)
            if c.editor_class is not None:
                if c.has_selection:
                    if c.editor_is_selected:
                        sel = [dv]
                    else:
                        sel = [m.mock()]
                        wc.docsController.selected_objects = [dv]
                else:
                    sel = []
                wc.docsController.selected_objects >> sel
                ed.recent.push(dv.id >> m.mock())
            if c.editor_class is Editor:
                dv.main_view >> (sv if c.view_is_main else None)
                if not c.view_is_main:
                    sv.removeFromSuperview()
                    doc = dv.document >> m.mock(TextDocument)
                    win = m.mock(ak.NSWindow)
                    wc.window() >> win
                    with m.order():
                        doc.addWindowController_(wc)
                        dv.set_main_view_of_window(mv, win)
                    find_project_with_editor = \
                        m.method(ed.find_project_with_editor)
                    if c.proj_is_none:
                        find_project_with_editor(dv) >> None
                        insert_items([dv])
                    else:
                        find_project_with_editor(dv) >> m.mock(Project)
            else:
                sv.removeFromSuperview()
                wc.setDocument_(None)
        with m:
            ed.current_editor = dv
        assert ed._current_editor is dv
    c = TestConfig(editor_is_current=False, editor_class=Editor)
    yield test, c(editor_is_current=True)
    yield test, c(editor_class=None, has_selection=False)
    c = c(editor_is_selected=True, has_selection=True)
    yield test, c(editor_class=None, editor_is_selected=False)
    for is_main in (True, False):
        for no_project in (True, False):
            yield test, c(view_is_main=is_main, proj_is_none=no_project)
    yield test, c(editor_class=Project)

def test_selected_editor_changed():
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
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
    from editxt.util import RecentItemStack
    ed = Window(editxt.app)
    real = ed.recent
    assert real is not None
    ed.suspend_recent_updates()
    assert ed.recent is not real
    assert isinstance(ed.recent, RecentItemStack)

def test_resume_recent_updates():
    from editxt.util import RecentItemStack
    ed = Window(editxt.app)
    real = ed.recent
    ed.suspend_recent_updates()
    ed.resume_recent_updates()
    eq_(ed.recent, real)

def test_new_project():
    m = Mocker()
    ed = Window(editxt.app)
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
    def test(c):
        m = Mocker()
        nsanim = m.replace(ak, 'NSViewAnimation')
        nsdict = m.replace(fn, 'NSDictionary')
        nsval = m.replace(fn, 'NSValue')
        nsarr = m.replace(fn, 'NSArray')
        ed = Window(editxt.app)
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
    ed = Window(editxt.app)
    doc = object()
    proj = Project(ed)
    dv = Editor(proj, document=doc)
    proj.insert_items([dv])
    assert dv.document is doc
    ed.projects.append(proj)
    eq_(ed.find_project_with_editor(dv), proj)
    dv = object()
    eq_(ed.find_project_with_editor(dv), None)

def test_find_project_with_path():
    def test(c):
        m = Mocker()
        def exists(path):
            return True
        def samefile(f1, f2):
            eq_(f2, c.path)
            return f1 == f2
        ed = Window(editxt.app)
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
    def test(docsController_is_not_none, path_config, create=False):
        proj = None
        m = Mocker()
        ed = Window(editxt.app)
        ed.wc = m.mock(WindowController)
        tc = m.mock(ak.NSTreeController)
        ed.wc.docsController >> (tc if docsController_is_not_none else None)
        ip_class = m.replace(fn, 'NSIndexPath')
        proj_class = m.replace(mod, 'Project')
        if docsController_is_not_none:
            path = m.mock(fn.NSIndexPath)
            tc.selectionIndexPath() >> (path if path_config is not None else None)
            if path_config is not None:
                index = path_config[0]
                path.indexAtPosition_(0) >> index
                path2 = m.mock(fn.NSIndexPath)
                ip_class.indexPathWithIndex_(index) >> path2
                proxy = m.mock()
                tc.objectAtArrangedIndexPath_(path2) >> proj
        if create and proj is None:
            proj = proj_class(ed) >> Project(ed)
        with m:
            result = ed.get_current_project(create=create)
            eq_(result, proj)
    for create in (True, False):
        yield test, True, None, create
        yield test, False, None, create
    yield test, True, [0]
    yield test, True, [0, 0]

def test_Window_iter_editors_of_document():
    DOC = "the document we're looking for"
    def test(config, total_editors):
        ed = Window(editxt.app)
        m = Mocker()
        editors = []
        doc = m.mock(TextDocument)
        ed.projects = projs = []
        for proj_has_editor in config:
            proj = m.mock(Project)
            projs.append(proj)
            dv = (m.mock(Editor) if proj_has_editor else None)
            proj.find_editor_with_document(doc) >> dv
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
        with m:
            ed = Window(editxt.app)
            result_tip = ed.tooltip_for_item(view, item)
            eq_(result_tip, (None if null_path else tip))
    for doctype in (TextDocument, Project, None):
        yield test, doctype, True
        yield test, doctype, False

def test_should_edit_item():
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
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
    def test(row, num_rows, doc_class=None):
        m = Mocker()
        ed = Window(editxt.app)
        ed.wc = m.mock(WindowController)
        ed.recent = m.mock()
        dv = ed.wc.docsView >> m.mock(ak.NSOutlineView)
        dv.numberOfRows() >> num_rows
        if row < num_rows:
            item = m.mock()
            dv.itemAtRow_(row) >> item
            item2 = m.mock(doc_class)
            dv.realItemForOpaqueItem_(item) >> item2
            item2.perform_close()
        with m:
            ed.close_button_clicked(row)
    yield test, 0, 0
    yield test, 1, 0
    for doc_class in (Project, Editor):
        yield test, 0, 1, doc_class

def test_window_did_become_key():
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
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

def test_window_should_close():
    import editxt.application
    def test(c):
        m = Mocker()
        win = m.mock(ak.NSWindow)
        dsd_class = m.replace('editxt.application.DocumentSavingDelegate')
        window = Window(editxt.app)
        window.wc = m.mock(WindowController)
        app = m.replace(window, 'app')
        dsd = m.mock(DocumentSavingDelegate)
        dirty_docs = []
        projs = window.projects = []
        for p in c.projs:
            proj = m.mock(Project)
            projs.append(proj)
            eds = app.find_windows_with_project(proj) >> []
            if p.num_eds == 1:
                eds.append(window)
                docs = proj.dirty_editors() >> []
                for i in range(p.num_dirty_docs):
                    dv = m.mock(Editor)
                    doc = dv.document >> m.mock(TextDocument)
                    docs.append(dv)
                    app.iter_windows_with_editor_of_document(doc) >> \
                        (window for x in range(p.app_views))
                    if p.app_views == 1:
                        dirty_docs.append(dv)
                dirty_docs.append(proj)
            else:
                eds.extend(m.mock(Window) for x in range(p.num_eds))
        def match_dd(idd):
            eq_(list(idd), dirty_docs)
            return True
        def match_cb(callback):
            callback(c.should_close)
            return True
        if c.should_close:
            win.close()
        dsd_class.alloc() >> dsd
        dsd.init_callback_(MATCH(match_dd), MATCH(match_cb)) >> dsd
        dsd.save_next_document()
        with m:
            result = window.window_should_close(win)
            eq_(result, False)
    p = lambda ne, nd, av=1: TestConfig(num_eds=ne, num_dirty_docs=nd, app_views=av)
    c = TestConfig(projs=[], should_close=True)
    yield test, c
    yield test, c(should_close=False)
    yield test, c(projs=[p(0, 1)])
    for num_dirty_docs in (0, 1, 2):
        yield test, c(projs=[p(1, num_dirty_docs)], should_close=False)
    yield test, c(projs=[p(2, 1)])
    yield test, c(projs=[p(1, 1), p(1, 2)])

def test_window_will_close():
    def test(window_settings_loaded, num_projects):
        m = Mocker()
        ed = Window(editxt.app)
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
    def test(c):
        settings = dict(
            frame_string="<frame string>",
            splitter_pos="<splitter_pos>",
            properties_hidden=c.props_hidden,
        )
        m = Mocker()
        ed = Window(editxt.app)
        ed.wc = m.mock(WindowController)
        ed.wc.window().stringWithSavedFrame() >> settings["frame_string"]
        ed.wc.splitView.fixedSideThickness() >> settings["splitter_pos"]
        ed.wc.propsViewButton.state() >> (ak.NSOnState if c.props_hidden else ak.NSOffState)
        with m:
            result = ed.window_settings
            eq_(result, settings)
    c = TestConfig()
    yield test, c(props_hidden=True)
    yield test, c(props_hidden=False)

def test_set_window_settings_with_null_settings():
    ed = Window(editxt.app)
    m = Mocker()
    settings = m.mock(dict)
    settings.get("frame_string") >> None
    settings.get("splitter_pos") >> None
    settings.get("properties_hidden", False) >> False
    with m:
        ed.window_settings = settings

def test_set_window_settings():
    from editxt.controls.splitview import ThinSplitView
    m = Mocker()
    ed = Window(editxt.app)
    ed.wc = m.mock(WindowController)
    fs = "<test frame string>"
    sp = "<test splitter position>"
    (ed.wc.window() >> m.mock(ak.NSWindow)).setFrameFromString_(fs)
    ed.wc.setShouldCascadeWindows_(False)
    (ed.wc.splitView >> m.mock(ThinSplitView)).setFixedSideThickness_(sp)
    ed.wc.propsViewButton.setState_(ak.NSOnState)
    prop_view = ed.wc.propsView >> m.mock(ak.NSView)
    prop_rect = prop_view.frame() >> m.mock(fn.NSRect)
    tree_view = ed.wc.docsScrollview >> m.mock(ak.NSScrollView)
    tree_rect = tree_view.frame() >> m.mock(fn.NSRect)
    tree_rect.size.height = (tree_rect.size.height >> 50) + (prop_rect.size.height >> 50) - 1
    tree_rect.origin.y = prop_rect.origin.y >> 20
    tree_view.setFrame_(tree_rect)
    prop_rect.size.height = 0.0
    prop_view.setFrame_(prop_rect)
    with m:
        ed.window_settings = dict(frame_string=fs, splitter_pos=sp, properties_hidden=True)

def test_close():
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
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
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
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
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
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
    def test(config):
        m = Mocker()
        ed = Window(editxt.app)
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
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
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
    def test(c):
        m = Mocker()
        ed = Window(editxt.app, None)
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
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
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
    class MatchingName(object):
        def __init__(self, name, rmap):
            self.name = name
            self.rmap = rmap
        def __repr__(self):
            return '<MatchingName %s>' % self.name
        def __eq__(self, other):
            return other.name == self.name or (
                # lower case -> upper case: new editor of document
                other.name == self.name.lower()
                and
                self.rmap[self.name.lower()] != other
            )
        def __ne__(self, other):
            return not self.__eq__(other)

    def test(c):
        def get_parent_index(drop, offset=0):
            if any(v in '0123456789' for v in drop[0]):
                assert all(v in '0123456789' for v in drop[0]), drop
                return None, pindex
            return project, dindex + offset
        def namechar(item, seen=set()):
            name = test_app.name(item, app)
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
                        editor.document.setFileURL_(fn.NSURL.fileURLWithPath_(char))
                        name_to_item[char] = editor

            for char in c.drop[0]:
                if char not in name_to_item and char not in '0123456789':
                    name_to_item[char] = TextDocument.alloc().init()
                    name_to_item[char].setFileURL_(fn.NSURL.fileURLWithPath_(char))

            items = [name_to_item[char] for char in c.drop[0]] if c.focus else []

            m = Mocker()
            window = app.windows[0]
            get_current_project = m.method(window.get_current_project)
            current_editor = m.property(window, 'current_editor')
            if c.focus:
                current_editor.value = MatchingName(c.focus, name_to_item)

            if "current_project" in c:
                args = ()
                parent = const.CURRENT
                index = -1
                if c.current_project is None:
                    def callback(**kw):
                        proj = Project(window)
                        window.projects.append(proj)
                        return proj
                else:
                    callback = lambda **k:name_to_item[c.current_project]
                expect(get_current_project(create=True)).call(callback)
            else:
                if parent is None:
                    if c.drop[0] and not c.drop[0][0].isdigit():
                        def callback(**kw):
                            proj = Project(window)
                            window.projects.append(proj)
                            return proj
                        expect(get_current_project(create=True)).call(callback)
                else:
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
    # so ' 0abc 1 2de| 3fa' is...
    #   window
    #       project 0
    #           document a
    #           document b
    #           document c
    #       project 1
    #       project 2
    #           document d
    #           document e
    #   window
    #       project 3
    #           document f
    #           document a
    #
    # drop=(<dropped item(s)>, <drop index in init>)

    config = TestConfig(init=' 0abc 1 2de', focus='')

    c = config(action=const.MOVE)
    yield test, c(drop=('', 0), final=' 0abc 1 2de')
    yield test, c(drop=('', 1), final=' 0abc 1 2de')
    yield test, c(drop=('', 2), final=' 0abc 1 2de')
    yield test, c(drop=('', 3), final=' 0abc 1 2de')
    yield test, c(drop=('', 4), final=' 0abc 1 2de')
    yield test, c(drop=('', 5), final=' 0abc 1 2de')
    yield test, c(drop=('', 6), final=' 0abc 1 2de')
    yield test, c(drop=('', 7), final=' 0abc 1 2de')
    yield test, c(drop=('', 8), final=' 0abc 1 2de')
    yield test, c(drop=('', 9), final=' 0abc 1 2de')
    yield test, c(drop=('', 10), final=' 0abc 1 2de')
    yield test, c(drop=('', 11), final=' 0abc 1 2de')

    yield test, c(drop=('a', 0), final=' 0bc 1 2de 3a', focus='a')
    yield test, c(drop=('a', 1), final=' 0bca 1 2de', focus='a')
    yield test, c(drop=('a', 2), final=' 0abc 1 2de')
    yield test, c(drop=('a', 3), final=' 0abc 1 2de')
    yield test, c(drop=('a', 4), final=' 0bac 1 2de', focus='a')
    yield test, c(drop=('a', 5), final=' 0bca 1 2de', focus='a')
    yield test, c(drop=('a', 6), final=' 0bc 1a 2de', focus='a')
    yield test, c(drop=('a', 7), final=' 0bc 1a 2de', focus='a')
    yield test, c(drop=('a', 8), final=' 0bc 1 2dea', focus='a')
    yield test, c(drop=('a', 9), final=' 0bc 1 2ade', focus='a')
    yield test, c(drop=('a', 10), final=' 0bc 1 2dae', focus='a')
    yield test, c(drop=('a', 11), final=' 0bc 1 2dea', focus='a')

    yield test, c(drop=('f', 0), final=' 0abc 1 2de 3F', focus='F')
    yield test, c(drop=('f', 1), final=' 0abcF 1 2de', focus='F')
    yield test, c(drop=('f', 2), final=' 0Fabc 1 2de', focus='F')
    yield test, c(drop=('f', 3), final=' 0aFbc 1 2de', focus='F')
    yield test, c(drop=('f', 4), final=' 0abFc 1 2de', focus='F')
    yield test, c(drop=('f', 5), final=' 0abcF 1 2de', focus='F')
    yield test, c(drop=('f', 6), final=' 0abc 1F 2de', focus='F')
    yield test, c(drop=('f', 7), final=' 0abc 1F 2de', focus='F')
    yield test, c(drop=('f', 8), final=' 0abc 1 2deF', focus='F')
    yield test, c(drop=('f', 9), final=' 0abc 1 2Fde', focus='F')
    yield test, c(drop=('f', 10), final=' 0abc 1 2dFe', focus='F')
    yield test, c(drop=('f', 11), final=' 0abc 1 2deF', focus='F')

    yield test, c(drop=('2', 0), final=' 0abc 1 2de', focus='2')
    yield test, c(drop=('2', 1), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 2), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 3), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 4), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 5), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 6), final=' 0abc 2de 1', focus='2')
    yield test, c(drop=('2', 7), final=' 0abc 2de 1', focus='2')
    yield test, c(drop=('2', 8), final=' 0abc 1 2de')
    yield test, c(drop=('2', 9), final=' 0abc 1 2de')
    yield test, c(drop=('2', 10), final=' 0abc 1 2de')
    yield test, c(drop=('2', 11), final=' 0abc 1 2de')

    c = config(action=const.COPY)
    yield test, c(drop=('', 0), final=' 0abc 1 2de')
    yield test, c(drop=('', 1), final=' 0abc 1 2de')
    yield test, c(drop=('', 2), final=' 0abc 1 2de')
    yield test, c(drop=('', 3), final=' 0abc 1 2de')
    yield test, c(drop=('', 4), final=' 0abc 1 2de')
    yield test, c(drop=('', 5), final=' 0abc 1 2de')
    yield test, c(drop=('', 6), final=' 0abc 1 2de')
    yield test, c(drop=('', 7), final=' 0abc 1 2de')
    yield test, c(drop=('', 8), final=' 0abc 1 2de')
    yield test, c(drop=('', 9), final=' 0abc 1 2de')
    yield test, c(drop=('', 10), final=' 0abc 1 2de')
    yield test, c(drop=('', 11), final=' 0abc 1 2de')

    yield test, c(drop=('a', 0), final=' 0abc 1 2de 3A', focus='A')
    yield test, c(drop=('a', 1), final=' 0abcA 1 2de', focus='A')
    yield test, c(drop=('a', 2), final=' 0Aabc 1 2de', focus='A')
    yield test, c(drop=('a', 3), final=' 0aAbc 1 2de', focus='A')
    yield test, c(drop=('a', 4), final=' 0abAc 1 2de', focus='A')
    yield test, c(drop=('a', 5), final=' 0abcA 1 2de', focus='A')
    yield test, c(drop=('a', 6), final=' 0abc 1A 2de', focus='A')
    yield test, c(drop=('a', 7), final=' 0abc 1A 2de', focus='A')
    yield test, c(drop=('a', 8), final=' 0abc 1 2deA', focus='A')
    yield test, c(drop=('a', 9), final=' 0abc 1 2Ade', focus='A')
    yield test, c(drop=('a', 10), final=' 0abc 1 2dAe', focus='A')
    yield test, c(drop=('a', 11), final=' 0abc 1 2deA', focus='A')

    c = config(action=None)
    yield test, c(drop=('', 0), final=' 0abc 1 2de')
    yield test, c(drop=('', 1), final=' 0abc 1 2de')
    yield test, c(drop=('', 2), final=' 0abc 1 2de')
    yield test, c(drop=('', 3), final=' 0abc 1 2de')
    yield test, c(drop=('', 4), final=' 0abc 1 2de')
    yield test, c(drop=('', 5), final=' 0abc 1 2de')
    yield test, c(drop=('', 6), final=' 0abc 1 2de')
    yield test, c(drop=('', 7), final=' 0abc 1 2de')
    yield test, c(drop=('', 8), final=' 0abc 1 2de')
    yield test, c(drop=('', 9), final=' 0abc 1 2de')
    yield test, c(drop=('', 10), final=' 0abc 1 2de')
    yield test, c(drop=('', 11), final=' 0abc 1 2de')

    yield test, c(drop=('a', 0), final=' 0abc 1 2de 3A', focus='A')
    yield test, c(drop=('a', 1), final=' 0abc 1 2de', focus='a')
    yield test, c(drop=('a', 2), final=' 0abc 1 2de', focus='a')
    yield test, c(drop=('a', 3), final=' 0abc 1 2de', focus='a')
    yield test, c(drop=('a', 4), final=' 0abc 1 2de', focus='a')
    yield test, c(drop=('a', 5), final=' 0abc 1 2de', focus='a')
    yield test, c(drop=('a', 6), final=' 0abc 1A 2de', focus='A')
    yield test, c(drop=('a', 7), final=' 0abc 1A 2de', focus='A')
    yield test, c(drop=('a', 8), final=' 0abc 1 2deA', focus='A')
    yield test, c(drop=('a', 9), final=' 0abc 1 2Ade', focus='A')
    yield test, c(drop=('a', 10), final=' 0abc 1 2dAe', focus='A')
    yield test, c(drop=('a', 11), final=' 0abc 1 2deA', focus='A')

    yield test, c(drop=('f', 0), final=' 0abc 1 2de 3F', focus='F')
    yield test, c(drop=('f', 1), final=' 0abcF 1 2de', focus='F')
    yield test, c(drop=('f', 2), final=' 0Fabc 1 2de', focus='F')
    yield test, c(drop=('f', 3), final=' 0aFbc 1 2de', focus='F')
    yield test, c(drop=('f', 4), final=' 0abFc 1 2de', focus='F')
    yield test, c(drop=('f', 5), final=' 0abcF 1 2de', focus='F')
    yield test, c(drop=('f', 6), final=' 0abc 1F 2de', focus='F')
    yield test, c(drop=('f', 7), final=' 0abc 1F 2de', focus='F')
    yield test, c(drop=('f', 8), final=' 0abc 1 2deF', focus='F')
    yield test, c(drop=('f', 9), final=' 0abc 1 2Fde', focus='F')
    yield test, c(drop=('f', 10), final=' 0abc 1 2dFe', focus='F')
    yield test, c(drop=('f', 11), final=' 0abc 1 2deF', focus='F')

    # cannot copy project yet
#    yield test, c(drop=('2', 0), final=' 0abc 1 2de')
#    yield test, c(drop=('2', 1), final=' 2de 0abc 1', focus='2')
#    yield test, c(drop=('2', 2), final=' 2de 0abc 1', focus='2')
#    yield test, c(drop=('2', 3), final=' 2de 0abc 1', focus='2')
#    yield test, c(drop=('2', 4), final=' 2de 0abc 1', focus='2')
#    yield test, c(drop=('2', 5), final=' 2de 0abc 1', focus='2')
#    yield test, c(drop=('2', 6), final=' 0abc 2de 1', focus='2')
#    yield test, c(drop=('2', 7), final=' 0abc 2de 1', focus='2')
#    yield test, c(drop=('2', 8), final=' 0abc 1 2de')
#    yield test, c(drop=('2', 9), final=' 0abc 1 2de')
#    yield test, c(drop=('2', 10), final=' 0abc 1 2de')
#    yield test, c(drop=('2', 11), final=' 0abc 1 2de')

    c = config(action=None, current_project='2')
    yield test, c(drop=('a', 0), final=' 0abc 1 2deA', focus='A')
    yield test, c(drop=('a', 1), final=' 0abc 1 2deA', focus='a')
    yield test, c(drop=('a', 2), final=' 0abc 1 2deA', focus='a')
    yield test, c(drop=('a', 3), final=' 0abc 1 2deA', focus='a')
    yield test, c(drop=('a', 4), final=' 0abc 1 2deA', focus='a')
    yield test, c(drop=('a', 5), final=' 0abc 1 2deA', focus='a')
    yield test, c(drop=('a', 6), final=' 0abc 1 2deA', focus='A')
    yield test, c(drop=('a', 7), final=' 0abc 1 2deA', focus='A')
    yield test, c(drop=('a', 8), final=' 0abc 1 2deA', focus='A')
    yield test, c(drop=('a', 9), final=' 0abc 1 2deA', focus='A')
    yield test, c(drop=('a', 10), final=' 0abc 1 2deA', focus='A')
    yield test, c(drop=('a', 11), final=' 0abc 1 2deA', focus='A')

    c = config(action=None, current_project=None)
    yield test, c(drop=('a', 0), final=' 0abc 1 2de 3A', focus='A')
    yield test, c(drop=('a', 1), final=' 0abc 1 2de 3A', focus='a')
    yield test, c(drop=('a', 2), final=' 0abc 1 2de 3A', focus='a')
    yield test, c(drop=('a', 3), final=' 0abc 1 2de 3A', focus='a')
    yield test, c(drop=('a', 4), final=' 0abc 1 2de 3A', focus='a')
    yield test, c(drop=('a', 5), final=' 0abc 1 2de 3A', focus='a')
    yield test, c(drop=('a', 6), final=' 0abc 1 2de 3A', focus='A')
    yield test, c(drop=('a', 7), final=' 0abc 1 2de 3A', focus='A')
    yield test, c(drop=('a', 8), final=' 0abc 1 2de 3A', focus='A')
    yield test, c(drop=('a', 9), final=' 0abc 1 2de 3A', focus='A')
    yield test, c(drop=('a', 10), final=' 0abc 1 2de 3A', focus='A')
    yield test, c(drop=('a', 11), final=' 0abc 1 2de 3A', focus='A')

    c = config(init=' 0a | 1bc', action=const.MOVE)
    yield test, c(drop=('b', 1), final=' 0ab | 1c', focus='b')
    yield test, c(drop=('b', 2), final=' 0ba | 1c', focus='b')

    yield test, c(drop=('1', 0), final=' 0a 1bc |', focus='1')
    yield test, c(drop=('1', 1), final=' 1bc 0a |', focus='1')

    yield test, c(drop=('a', 6), final=' 0 | 1bca', focus='a') # should fail (item inserted in wrong window)

def test_undo_manager():
    def test(c):
        m = Mocker()
        ed = Window(editxt.app)
        wc = ed.wc = m.mock(WindowController)
        if not c.has_doc:
            doc = None
        else:
            doc = m.mock(ak.NSDocument)
            doc.undoManager() >> "<undo_manager>"
        wc.document() >> doc
        with m:
            result = ed.undo_manager()
            if c.has_doc:
                eq_(result, "<undo_manager>")
            else:
                assert isinstance(result, fn.NSUndoManager), result
    c = TestConfig(has_doc=True)
    yield test, c
    yield test, c(has_doc=False)
