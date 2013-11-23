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

import AppKit as ak
import Foundation as fn

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import *

import editxt
import editxt.constants as const
from editxt.application import Application, DocumentController, DocumentSavingDelegate
from editxt.editor import EditorWindowController, Editor
from editxt.document import TextDocumentView, TextDocument
from editxt.project import Project
from editxt.test.noseplugins import slow_skip
from editxt.util import representedObject

from editxt.test.util import do_method_pass_through, TestConfig, replattr

import editxt.editor as mod

log = logging.getLogger(__name__)
# log.debug("""TODO test
#     Editor.iter_dropped_paths
#     Editor.iter_dropped_id_list
# """)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Editor tests

# log.debug("""TODO implement
# """)

def test_EditorConroller__init__():
    def test(c):
        ed = Editor(editxt.app, *c.args)
        assert len(ed.projects) == 0
        assert len(ed.recent) == 0
        if c.args:
            assert ed.wc is c.args[0]
        if len(c.args) > 1:
            assert ed.state is c.args[1]
        eq_(ed.command.editor, ed)
    c = TestConfig(args=())
    yield test, c(args=("<window controller>",))
    yield test, c(args=("<window controller>", "<state data>"))

def test_window_did_load():
    def test(state):
        import editxt.controls.cells as cells
        from editxt.editor import BUTTON_STATE_SELECTED
        from editxt.util import load_image
        m = Mocker()
        ed = Editor(editxt.app, m.mock(EditorWindowController), state)
        wc = ed.wc
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
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)
    def test(data):
        m = Mocker()
        ed = Editor(editxt.app, m.mock(EditorWindowController))
        ed.discard_and_focus_recent = m.method(ed.discard_and_focus_recent)
        create_with_serial = m.method(Project.create_with_serial)
        ed.recent = m.mock(RecentItemStack)
        ws = m.property(ed, 'window_settings')
        projects = []
        if data:
            for serial in data.get("project_serials", []):
                proj = create_with_serial(serial) >> Item()
                projects.append(proj)
            for pi, di in data.get("recent_items", []):
                if pi < 1:
                    while len(ed.projects) <= pi:
                        docs = []
                        proj = Item(documents=docs)
                        projects.append(proj)
                        ed.projects.append(proj)
                    proj = ed.projects[pi]
                    if di == "<project>":
                        ed.recent.push(proj.id)
                    else:
                        if di < 2:
                            while len(proj.documents) <= di:
                                proj.documents.append(Item())
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
        ed = Editor(editxt.app, None)
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
            docs = proj.documents >> []
            offset = 0
            for j, d in enumerate(p.docs):
                dv = m.mock(TextDocumentView)
                docs.append(dv)
                if d > 0:
                    path = "/path/do/file%s.txt" % d
                    (dv.file_path << path).count(2)
                    dv.id >> d
                    items[d] = [i, j - offset]
                else:
                    offset += 1
                    dv.file_path >> None
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
        ed = Editor(editxt.app, m.mock(EditorWindowController))
        ed.projects = projs = []
        ed.recent = m.mock(RecentItemStack)
        app = m.replace(ed, 'app')
        new_current_view = None
        cv = m.property(ed, "current_view")
        lookup = {}
        for p in c.hier:
            proj = m.mock(Project)
            proj.id >> p.id
            docs = []
            for d in p.docs:
                dv = m.mock(TextDocumentView)
                dv.id >> d.id
                docs.append(dv)
                if c.id in (p.id, d.id):
                    ed.recent.discard(d.id)
                    proj.remove_document_view(dv)
                    dv.close()
                else:
                    lookup[d.id] = dv
            proj.documents >> docs
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
                cv.value = new_current_view = item
                if not recent:
                    current_ident = ident
                recent.append(ident)
                break
        bool(ed.recent); m.result(bool(recent))
        if not recent:
            if c.hier and new_current_view is not None:
                ed.recent.push(new_current_view.id >> c.hier[0].id)
            else:
                if new_current_view is None:
                    ed.current_view >> None
                else:
                    ed.recent.push(new_current_view.id >> current_ident)
        item = m.mock()
        item.id >> c.id
        with m:
            ed.discard_and_focus_recent(item)
    item = lambda i, **kw: TestConfig(id=i, **kw)
    c = TestConfig(id=2, recent=[], hier=[ # hierarchy of items in the editor
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

def test_get_current_view():
    ed = Editor(editxt.app, None)
    ed._current_view = obj = object()
    eq_(ed.current_view, obj)

def test_set_current_view():
    from editxt.util import RecentItemStack
    def test(c):
        m = Mocker()
        wc = m.mock(EditorWindowController)
        ed = Editor(editxt.app, wc)
        add_document_view = m.method(ed.add_document_view)
        ed.recent = m.mock(RecentItemStack)
        dv = (None if c.view_class is None else m.mock(c.view_class))
        if c.view_is_current:
            ed._current_view = dv
        else:
            ed._current_view = m.mock(ak.NSView)
            mv = wc.mainView >> m.mock(ak.NSView)
            sv = m.mock(ak.NSView)
            (mv.subviews() << [sv]).count(1, 2)
            if c.view_class is not None:
                if c.has_selection:
                    if c.view_is_selected:
                        sel = [dv]
                    else:
                        sel = [m.mock()]
                        wc.docsController.setSelectedObject_(dv)
                else:
                    sel = []
                wc.docsController.selectedObjects() >> sel
                ed.recent.push(dv.id >> m.mock())
            if c.view_class is TextDocumentView:
                dv.dual_view >> (sv if c.view_is_main else None)
                if not c.view_is_main:
                    sv.removeFromSuperview()
                    doc = dv.document >> m.mock(TextDocument)
                    win = m.mock(ak.NSWindow)
                    wc.window() >> win
                    with m.order():
                        doc.addWindowController_(wc)
                        dv.set_main_view_of_window(mv, win)
                    find_project_with_document_view = \
                        m.method(ed.find_project_with_document_view)
                    if c.proj_is_none:
                        find_project_with_document_view(dv) >> None
                        add_document_view(dv)
                    else:
                        find_project_with_document_view(dv) >> m.mock(Project)
            else:
                sv.removeFromSuperview()
                wc.setDocument_(None)
        with m:
            ed.current_view = dv
        assert ed._current_view is dv
    c = TestConfig(view_is_current=False, view_class=TextDocumentView)
    yield test, c(view_is_current=True)
    yield test, c(view_class=None, has_selection=False)
    c = c(view_is_selected=True, has_selection=True)
    yield test, c(view_class=None, view_is_selected=False)
    for vim in (True, False):
        for pin in (True, False):
            yield test, c(view_is_main=vim, proj_is_none=pin)
    yield test, c(view_class=Project)

def test_selected_view_changed():
    def test(c):
        m = Mocker()
        wc = m.mock(EditorWindowController)
        ed = Editor(editxt.app, wc)
        cv = m.property(ed, "current_view")
        sel = [m.mock() for x in range(c.numsel)]
        wc.docsController.selectedObjects() >> sel
        if sel:
            if c.is_current_selected:
                cv.value >> sel[0]
            else:
                cv.value >> m.mock()
                cv.value = sel[0]
        with m:
            ed.selected_view_changed()
    c = TestConfig(numsel=0)
    yield test, c
    for ics in (True, False):
        yield test, c(numsel=1, is_current_selected=ics)
        yield test, c(numsel=5, is_current_selected=ics)

def test_suspend_recent_updates():
    from editxt.util import RecentItemStack
    ed = Editor(editxt.app, None)
    real = ed.recent
    assert real is not None
    ed.suspend_recent_updates()
    assert ed.recent is not real
    assert isinstance(ed.recent, RecentItemStack)

def test_resume_recent_updates():
    from editxt.util import RecentItemStack
    ed = Editor(editxt.app, None)
    real = ed.recent
    ed.suspend_recent_updates()
    ed.resume_recent_updates()
    eq_(ed.recent, real)

def test_new_project():
    m = Mocker()
    ed = Editor(editxt.app, None)
    cv = m.property(ed, "current_view")
    view = m.method(Project.create_document_view)() >> m.mock(TextDocumentView)
    cv.value = view
    with m:
        result = ed.new_project()
        assert result in ed.projects, ed.projects
        assert not result.documents, result.documents

def test_toggle_properties_pane():
    from editxt.controls.splitview import ThinSplitView
    slow_skip()
    def test(c):
        m = Mocker()
        nsanim = m.replace(ak, 'NSViewAnimation')
        nsdict = m.replace(fn, 'NSDictionary')
        nsval = m.replace(fn, 'NSValue')
        nsarr = m.replace(fn, 'NSArray')
        wc = m.mock(EditorWindowController)
        ed = Editor(editxt.app, wc)
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

def test_find_project_with_document_view():
    ed = Editor(editxt.app, None)
    doc = object()
    proj = Project.create()
    dv = TextDocumentView(proj, document=doc)
    proj.append_document_view(dv)
    assert dv.document is doc
    ed.projects.append(proj)
    assert ed.find_project_with_document_view(dv) is proj
    dv = object()
    assert ed.find_project_with_document_view(dv) is None

def test_find_project_with_path():
    def test(c):
        m = Mocker()
        def exists(path):
            return True
        def samefile(f1, f2):
            eq_(f2, c.path)
            return f1 == f2
        ed = Editor(editxt.app, None)
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
        ed = Editor(editxt.app, m.mock(EditorWindowController))
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
                proj = m.mock(Project)
                tc.objectAtArrangedIndexPath_(path2) >> proj
        if create and proj is None:
            proj = m.mock(Project)
            proj_class.create() >> proj
        with m:
            result = ed.get_current_project(create=create)
            eq_(result, proj)
    for create in (True, False):
        yield test, True, None, create
        yield test, False, None, create
    yield test, True, [0]
    yield test, True, [0, 0]

def test_add_document_view():
    def test(has_view):
        m = Mocker()
        ed = Editor(editxt.app, None)
        doc = TextDocument.alloc().init()
        dv = TextDocumentView(None, document=doc)
        assert dv.project is None, dv.project
        proj = Project.create()
        if has_view:
            proj.append_document_view(dv)
        m.method(ed.get_current_project)(create=True) >> proj
        with m:
            ed.add_document_view(dv)
        eq_(len(proj.documents), 1, proj.documents)
    yield test, False
    yield test, True

def test_Editor_iter_views_of_document():
    DOC = "the document we're looking for"
    def test(config, total_views):
        ed = Editor(editxt.app, None)
        m = Mocker()
        views = []
        doc = m.mock(TextDocument)
        ed.projects = projs = []
        for proj_has_view in config:
            proj = m.mock(Project)
            projs.append(proj)
            dv = (m.mock(TextDocumentView) if proj_has_view else None)
            proj.find_view_with_document(doc) >> dv
            if dv is not None:
                views.append(dv)
        with m:
            result = list(ed.iter_views_of_document(doc))
            eq_(result, views)
            eq_(len(result), total_views)
    yield test, [], 0
    yield test, [False], 0
    yield test, [True], 1
    yield test, [False, True, True, False, True], 3

def test_item_changed():
    def test(c):
        m = Mocker()
        ed = Editor(editxt.app, m.mock(EditorWindowController))
        vw = ed.wc.docsView >> (None if c.view_is_none else m.mock(ak.NSOutlineView))
        item = None
        if not (c.view_is_none or c.item_is_none):
            objs = []
            found = None
            for row, otype in enumerate(c.objs):
                if otype.lower() == "p":
                    obj = m.mock(name="<%sroject%i>" % (otype, row))
                    if not found:
                        if otype == "P":
                            found = (row, obj)
                        else:
                            obj.document >> None
                elif otype.lower() == "d":
                    obj = m.mock(name="docview%i" % row)
                    if not found:
                        doc = obj.document >> m.mock(name="<%socument%i>" % (otype, row))
                        if otype == "D":
                            found = (row, doc)
                objs.append((row, obj))
            if found:
                row, item = found
                eq_(c.row, row)
                vw.setNeedsDisplayInRect_(vw.rectOfRow_(row) >> m.mock(fn.NSRect))
            else:
                eq_(c.row, None)
                item = m.mock(name="<unknown>")
            vw.iterVisibleObjects() >> objs
        with m:
            ed.item_changed(item, 0)
    c = TestConfig(view_is_none=False, item_is_none=False)
    yield test, c(view_is_none=True, item_is_none=True)
    yield test, c(view_is_none=True)
    yield test, c(item_is_none=True)
    yield test, c(objs=["p", "d", "d"], row=None)
    yield test, c(objs=["P", "d", "d", "P"], row=0)
    yield test, c(objs=["p", "d", "D", "P"], row=2)

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
            ed = Editor(editxt.app, None)
            result_tip = ed.tooltip_for_item(view, item)
            eq_(result_tip, (None if null_path else tip))
    for doctype in (TextDocument, Project, None):
        yield test, doctype, True
        yield test, doctype, False

def test_should_edit_item():
    def test(c):
        m = Mocker()
        ed = Editor(editxt.app, None)
        item = m.mock()
        col = m.mock(ak.NSTableColumn)
        if (col.isEditable() >> c.col_is_editable):
            obj = m.mock(Project if c.item_is_project else TextDocumentView)
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
        ed = Editor(editxt.app, m.mock(EditorWindowController))
        ed.recent = m.mock()
        dv = ed.wc.docsView >> m.mock(ak.NSOutlineView)
        dv.numberOfRows() >> num_rows
        if row < num_rows:
            item = m.mock()
            dv.itemAtRow_(row) >> item
            item2 = m.mock(doc_class)
            dv.realItemForOpaqueItem_(item) >> item2
            item2.perform_close(ed)
        with m:
            ed.close_button_clicked(row)
    yield test, 0, 0
    yield test, 1, 0
    for doc_class in (Project, TextDocumentView):
        yield test, 0, 1, doc_class

def test_window_did_become_key():
    def test(c):
        m = Mocker()
        ed = Editor(editxt.app, None)
        win = m.mock(ak.NSWindowController)
        cv = m.property(ed, "current_view")
        dv = cv.value >> (m.mock(c.view_type) if c.has_current else None)
        if c.has_current and c.view_type is TextDocumentView:
            dv.document.check_for_external_changes(win)
        with m:
            ed.window_did_become_key(win)
    c = TestConfig(has_current=False, view_type=TextDocumentView)
    yield test, c
    yield test, c(has_current=True)
    yield test, c(has_current=True, view_type=Project)

def test_window_should_close():
    import editxt.application
    def test(c):
        m = Mocker()
        win = m.mock(ak.NSWindow)
        dsd_class = m.replace('editxt.application.DocumentSavingDelegate')
        editor = Editor(editxt.app, m.mock(EditorWindowController))
        app = m.replace(editor, 'app')
        dsd = m.mock(DocumentSavingDelegate)
        dirty_docs = []
        projs = editor.projects = []
        for p in c.projs:
            proj = m.mock(Project)
            projs.append(proj)
            eds = app.find_editors_with_project(proj) >> []
            if p.num_eds == 1:
                eds.append(editor)
                docs = proj.dirty_documents() >> []
                for i in range(p.num_dirty_docs):
                    dv = m.mock(TextDocumentView)
                    doc = dv.document >> m.mock(TextDocument)
                    docs.append(dv)
                    app.iter_editors_with_view_of_document(doc) >> \
                        (editor for x in range(p.app_views))
                    if p.app_views == 1:
                        dirty_docs.append(dv)
                dirty_docs.append(proj)
            else:
                eds.extend(m.mock(Editor) for x in range(p.num_eds))
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
            result = editor.window_should_close(win)
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
        ed = Editor(editxt.app, None)
        ed.window_settings_loaded = window_settings_loaded
        app = m.replace(ed, 'app')
        with m.order():
            app.discard_editor(ed)
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
        ed = Editor(editxt.app, m.mock(EditorWindowController))
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
    ed = Editor(editxt.app, None)
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
    ed = Editor(editxt.app, m.mock(EditorWindowController))
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
        wc = m.mock(EditorWindowController)
        ed = Editor(editxt.app, wc)
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
        ed = Editor(editxt.app, None)
        ed.iter_dropped_id_list = m.method(ed.iter_dropped_id_list)
        pb = m.mock(ak.NSPasteboard)
        result_items = []
        info = m.mock() #NSDraggingInfo
        items = []
        pb = info.draggingPasteboard() >> m.mock(ak.NSPasteboard)
        pb.availableTypeFromArray_(ed.supported_drag_types) >> c.accepted_type
        if c.accepted_type == const.DOC_ID_LIST_PBOARD_TYPE:
            ed.iter_dropped_id_list(pb) >> items
            factories = dict(
                p=(lambda:m.mock(Project)),
                d=(lambda:m.mock(TextDocumentView)),
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
        ed = Editor(editxt.app, None)
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
    item = TestConfig(type=TextDocumentView, path="/path/to/file")
    yield test, c(items=[item])
    yield test, c(items=[item(type=Project)])
    yield test, c(items=[item(type=Project), item])
    yield test, c(items=[item(path=None)])
    yield test, c(items=[item(type=Project, path=None)])

def test_validate_drop():
    def test(config):
        m = Mocker()
        ed = Editor(editxt.app, m.mock(EditorWindowController))
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
                        obj.documents >> (["<doc>"] * config.proj_docs)
                        ov.setDropItem_dropChildIndex_(item, config.proj_docs)
                else:
                    obj = m.mock(type=TextDocumentView)
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
                        proj.documents >> (["<doc>"] * config.proj_docs)
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
        ed = Editor(editxt.app, m.mock(EditorWindowController))
        ed.insert_items = m.method(ed.insert_items)
        ed.iter_dropped_id_list = m.method(ed.iter_dropped_id_list)
        ed.iter_dropped_paths = m.method(ed.iter_dropped_paths)
        ov = m.mock(ak.NSOutlineView)
        # TODO investigate where NSDraggingInfo went during the upgrade to 10.5
        info = m.mock() #NSDraggingInfo
        item = None if c.item_is_none else m.mock()
        parent = None if c.item_is_none else m.mock()
        index = 0
        act = None
        items = m.mock()
        pb = info.draggingPasteboard() >> m.mock(ak.NSPasteboard)
        pb.availableTypeFromArray_(ed.supported_drag_types) >> c.accepted_type
        if c.accepted_type == const.DOC_ID_LIST_PBOARD_TYPE:
            ed.iter_dropped_id_list(pb) >> items
            act = const.MOVE
        elif c.accepted_type == ak.NSFilenamesPboardType:
            ed.iter_dropped_paths(pb) >> items
        else:
            items = None
            assert c.accepted_type is None
        if items is not None:
            if not c.item_is_none:
                representedObject(item) >> parent
            ed.insert_items(items, parent, index, act) >> c.result
        with m:
            result = ed.accept_drop(ov, info, item, index)
            eq_(result, c.result)
    c = TestConfig(result=True, item_is_none=False)
    yield test, c(accepted_type=const.DOC_ID_LIST_PBOARD_TYPE)
    yield test, c(accepted_type=ak.NSFilenamesPboardType)
    yield test, c(accepted_type=ak.NSFilenamesPboardType, item_is_none=True)
    yield test, c(accepted_type=None, result=False)

def test_iter_dropped_id_list():
    def test(c):
        m = Mocker()
        ed = Editor(editxt.app, None)
        app = m.replace(ed, 'app')
        pb = m.mock(ak.NSPasteboard)
        result_items = []
        pb.types().containsObject_(const.DOC_ID_LIST_PBOARD_TYPE) >> c.has_ids
        if c.has_ids:
            ids = []
            pb.propertyListForType_(const.DOC_ID_LIST_PBOARD_TYPE) >> ids
            for it in c.ids:
                ids.append(it.id)
                item = m.mock()
                app.find_item_with_id(it.id) >> (item if it.found else None)
                if it.found:
                    result_items.append(item)
        with m:
            result = list(ed.iter_dropped_id_list(pb))
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
    import editxt.document
    def test(c):
        m = Mocker()
        ed = Editor(editxt.app, None)
        ed.find_project_with_path = m.method(ed.find_project_with_path)
        app = m.replace(ed, 'app')
        doc_class = m.replace('editxt.document.TextDocument')
        create_with_path = m.method(Project.create_with_path)
        pb = m.mock(ak.NSPasteboard)
        dc = m.mock(DocumentController)
        result_items = []
        #item = None if c.item_is_none else m.mock()
        pb.types().containsObject_(ak.NSFilenamesPboardType) >> c.has_paths
        if c.has_paths:
            #parent = None if c.item_is_none else m.mock(Project)
            #if not c.item_is_none:
            #    representedObject(item) >> parent
            paths = []
            pb.propertyListForType_(ak.NSFilenamesPboardType) >> paths
            for it in c.paths:
                paths.append(it.path)
                if Project.is_project_path(it.path):
                    proj = m.mock(Project) if it.found else None
                    app.find_project_with_path(it.path) >> proj
                    if not it.found:
                        proj = create_with_path(it.path) >> m.mock(Project)
                    result_items.append(proj)
                else:
                    doc = doc_class.get_with_path(it.path) >> m.mock(TextDocument)
                    result_items.append(doc)
        with m:
            result = list(ed.iter_dropped_paths(pb))
            eq_(result, result_items)
    c = TestConfig(item_is_none=False, has_paths=True)
    doc = "/path/to/doc%s.txt"
    proj = "/path/to/proj%s." + const.PROJECT_EXT
    def path(tmp, num, found=False, **kw):
        return TestConfig(found=found, path=tmp % num, **kw)
    yield test, c(has_paths=False)
    #yield test, c(paths=[], item_is_none=True)
    yield test, c(paths=[])
    #yield test, c(paths=[path(doc, 1)], item_is_none=True)
    yield test, c(paths=[path(doc, 1)])
    yield test, c(paths=[path(doc, 1), path(doc, 2), path(doc, 3)])
    #yield test, c(paths=[path(proj, 1, is_open=False)], item_is_none=True)
    yield test, c(paths=[path(proj, 1)])
    yield test, c(paths=[path(proj, 1, True)])
    yield test, c(paths=[path(proj, 1, True), path(doc, 1), path(proj, 2)])

def test_insert_items():
    class MatchingName(object):
        def __init__(self, name, rmap):
            self.name = name
            self.rmap = rmap
        def __repr__(self):
            return '<MatchingName %s>' % self.name
        def __eq__(self, other):
            return other.name == self.name or (
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

        m = Mocker()
        ed = Editor(editxt.app, None)
        current_view = m.property(ed, 'current_view')
        map = {}
        rmap = {}
        drop = {}
        pindex = dindex = -1
        project = None
        for i, char in enumerate(c.init + ' '):
            if char == ' ':
                if i == c.drop[1]:
                    parent, index = get_parent_index(c.drop, 1)
                dindex = -1
                continue
            if char in '0123456789':
                item = project = Project.create()
                item.name = char
                ed.projects.append(item)
                pindex += 1
            else:
                doc = TextDocument.alloc().init()
                doc.setFileURL_(fn.NSURL.fileURLWithPath_(char))
                item = TextDocumentView(project, document=doc)
                project.append_document_view(item)
                dindex += 1
            map[item] = char
            rmap[char] = item
            if i == c.drop[1]:
                parent, index = get_parent_index(c.drop)
            if char in c.drop[0]:
                drop[char] = item
        for char in c.drop[0]:
            if char not in rmap and char not in '0123456789':
                drop[char] = rmap[char] = TextDocument.alloc().init()
                drop[char].setFileURL_(fn.NSURL.fileURLWithPath_(char))
        items = [drop[char] for char in c.drop[0]]

        act = None if len(c.drop) == 2 else \
            ({'move': const.MOVE, 'copy':const.COPY}[c.drop[2]])

        if c.result and c.focus:
            current_view.value = MatchingName(c.focus, rmap)

        print(('drop(%s) %s at %s of %s' % (act, c.drop[0], index, parent)))
        with m:
            result = ed.insert_items(items, parent, index, act)

        eq_(result, c.result)
        final = []
        next_project = str(int(max(v for v in c.init if v in '0123456789')) + 1)
        for project in ed.projects:
            final.append(' ' + map.get(project, next_project))
            for view in project.documents:
                final.append(map.get(view, view.displayName().upper()))
        eq_(str(''.join(final)), c.final)

    # number = project
    # letter = document
    # capital letter = new view of document
    # space before project allows drop on project (insert at end)
    # so ' 0abc 1 2de' is...
    #   project 0
    #       document a
    #       document b
    #       document c
    #   project 1
    #   project 2
    #       document d
    #       document e

    c = TestConfig(init=' 0abc 1 2de', result=True, focus='')

    yield test, c(drop=('', 0), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 1), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 2), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 3), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 4), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 5), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 6), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 7), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 8), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 9), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 10), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 11), final=' 0abc 1 2de', result=False)

    yield test, c(drop=('a', 0), final=' 3a 0bc 1 2de', focus='a')
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

    yield test, c(drop=('f', 0), final=' 3F 0abc 1 2de', focus='F')
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

    yield test, c(drop=('2', 0), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 1), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 2), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 3), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 4), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 5), final=' 2de 0abc 1', focus='2')
    yield test, c(drop=('2', 6), final=' 0abc 2de 1', focus='2')
    yield test, c(drop=('2', 7), final=' 0abc 2de 1', focus='2')
    yield test, c(drop=('2', 8), final=' 0abc 1 2de', focus='')
    yield test, c(drop=('2', 9), final=' 0abc 1 2de', focus='')
    yield test, c(drop=('2', 10), final=' 0abc 1 2de', focus='')
    yield test, c(drop=('2', 11), final=' 0abc 1 2de', focus='')

    yield test, c(drop=('', 0, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 1, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 2, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 3, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 4, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 5, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 6, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 7, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 8, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 9, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 10, 'copy'), final=' 0abc 1 2de', result=False)
    yield test, c(drop=('', 11, 'copy'), final=' 0abc 1 2de', result=False)

    yield test, c(drop=('a', 0, 'copy'), final=' 3A 0abc 1 2de', focus='A')
    yield test, c(drop=('a', 1, 'copy'), final=' 0abcA 1 2de', focus='A')
    yield test, c(drop=('a', 2, 'copy'), final=' 0Aabc 1 2de', focus='A')
    yield test, c(drop=('a', 3, 'copy'), final=' 0aAbc 1 2de', focus='A')
    yield test, c(drop=('a', 4, 'copy'), final=' 0abAc 1 2de', focus='A')
    yield test, c(drop=('a', 5, 'copy'), final=' 0abcA 1 2de', focus='A')
    yield test, c(drop=('a', 6, 'copy'), final=' 0abc 1A 2de', focus='A')
    yield test, c(drop=('a', 7, 'copy'), final=' 0abc 1A 2de', focus='A')
    yield test, c(drop=('a', 8, 'copy'), final=' 0abc 1 2deA', focus='A')
    yield test, c(drop=('a', 9, 'copy'), final=' 0abc 1 2Ade', focus='A')
    yield test, c(drop=('a', 10, 'copy'), final=' 0abc 1 2dAe', focus='A')
    yield test, c(drop=('a', 11, 'copy'), final=' 0abc 1 2deA', focus='A')

def test_undo_manager():
    def test(c):
        m = Mocker()
        wc = m.mock(EditorWindowController)
        ed = Editor(editxt.app, wc)
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# EditorWindowController tests

# log.debug("""TODO implement
# """)

def test_EditorWindowController_passthrough_to_Editor():
    WC = "WC"
    def test(*args):
        wc = EditorWindowController.alloc().init()
        wc.editor = None
        do_method_pass_through("editor", Editor, wc, WC, *args)
    yield test, ("hoverButton_rowClicked_", "close_button_clicked"), (None, "<row>"), ("<row>",)
    yield test, ("windowWillClose_", "window_will_close"), ("<window>",), ()
    yield test, ("outlineView_writeItems_toPasteboard_", "write_items_to_pasteboard"), \
        ("<ov>", "<items>", "<pasteboard>"), ("<ov>", "<items>", "<pasteboard>"), \
        "<result>"
    yield test, ("outlineView_acceptDrop_item_childIndex_", "accept_drop"), \
        ("<ov>", "<drop>", "<item>", "<index>"), ("<ov>", "<drop>", "<item>", "<index>"), \
        "<drag result>"
    yield test, ("outlineView_validateDrop_proposedItem_proposedChildIndex_", "validate_drop"), \
        ("<ov>", "<drop>", "<item>", "<index>"), ("<ov>", "<drop>", "<item>", "<index>"), \
        "<drag operation>"
    yield test, ("outlineView_shouldEditTableColumn_item_", "should_edit_item"), \
        ("<ov>", "<col>", "<item>"), ("<col>", "<item>"), "<should ediit>"
    yield test, ("newProject_", "new_project"), ("<sender>",), ()
    yield test, ("togglePropertiesPane_", "toggle_properties_pane"), ("sender",), ()

def test_windowDidLoad():
    wc = EditorWindowController.alloc().init()
    m = Mocker()
    wc.editor = m.mock(Editor)
    wc.editor.window_did_load()
    with m:
        wc.windowDidLoad()

def test_syntaxDefNames():
    m = Mocker()
    wc = EditorWindowController.alloc().init()
    wc.editor = editor = m.mock(Editor)
    app = m.mock(Application)
    (editor.app << app).count(2)
    defs = [type("FakeDef", (object,), {"name": "Fake Syntax"})()]
    (app.syntaxdefs << defs).count(2)
    names = [d.name for d in defs]
    with m:
        eq_(wc.syntaxDefNames(), names)
        wc.setSyntaxDefNames_(None) # should be no-op
        eq_(wc.syntaxDefNames(), names)

def test_characterEncodings():
    wc = EditorWindowController.alloc().init()
    names = fn.NSValueTransformer.valueTransformerForName_("CharacterEncodingTransformer").names
    eq_(wc.characterEncodings(), names)
    wc.setCharacterEncodings_(None) # should be no-op
    eq_(wc.characterEncodings(), names)

def test_outlineViewSelectionDidChange_():
    ewc = EditorWindowController.alloc().init()
    m = Mocker()
    ewc.editor = m.mock(Editor)
    ewc.editor.selected_view_changed()
    with m:
        ewc.outlineViewSelectionDidChange_(None)

def test_outlineViewItemDidExpandCollapse():
    def test(c):
        m = Mocker()
        ewc = EditorWindowController.alloc().init()
        ed = ewc.editor = m.mock(Editor)
        n = m.mock() # ak.NSOutlineViewItemDid___Notification
        node = m.mock(ak.NSTreeControllerTreeNode); n.userInfo() >> {"NSObject": node}
        it = representedObject(node) >> m.mock(Project)
        it.expanded = c.exp
        with m:
            getattr(ewc, c.method)(n)
    c = TestConfig()
    yield c(method="outlineViewItemDidCollapse_", exp=False)
    yield c(method="outlineViewItemDidExpand_", exp=True)

# def test_setDocument_():
#     wc = EditorWindowController.alloc().init()
#     proj = wc.new_project()
#     doc = proj.documents[0].document
#     m = Mocker()
#     EditorWindowController.window = m.replace(EditorWindowController.window)
#     win = m.mock(NSWindow)
#     wc.window = lambda:win
#     wc.controller = m.replace(wc.controller, type=Editor)
#     wc.controller.set_document_main_view_of_window(doc, wc.mainView, wc.window())
#     with m:
#         wc.setDocument_(doc)

# def test_active_document_on_window_loaded():
#     ewc = EditorWindowController.alloc().init()
#     ewc.window() # load window
#     assert len(ewc.docsController.selectedObjects()) == 1
#     doc = ewc.projects()[0].documents[0]
#     assert doc in ewc.docsController.selectedObjects()

# def test_EditorWindowController_activate_document():
#     ewc = EditorWindowController.alloc().init()
#     ewc.window() # HACK load the window controller, create a project, etc.
#     assert len(ewc.projects()[0].documents) == 1
#     doc = TextDocument.alloc().init()
#     assert doc not in ewc.docsController.selectedObjects()
#     ewc.activate_document(doc)
#     assert len(ewc.docsController.selectedObjects()) == 1
#     assert doc in ewc.docsController.selectedObjects()

def test_outlineView_shouldSelectItem_():
    ewc = EditorWindowController.alloc().init()
    m = Mocker()
    ov = m.mock(ak.NSOutlineView)
    ewc.editor = m.mock(Editor)
    ewc.editor.should_select_item(ov, None)
    with m:
        ewc.outlineView_shouldSelectItem_(ov, None)

# def test_outlineView_shouldExpandItem_():
#     ewc = EditorWindowController.alloc().init()
#     m = Mocker()
#     ov = m.mock(NSOutlineView)
#     it = m.mock()
#     obj = m.mock(TextDocument)
#     representedObject(it) >> obj
#     obj.isLeaf() >> False
#     with m:
#         ewc.outlineView_shouldExpandItem_(ov, it)

def test_outlineView_willDisplayCell_forTableColumn_item_():
    from editxt.controls.cells import ImageAndTextCell
    ewc = EditorWindowController.alloc().init()
    m = Mocker()
    view = m.mock(ak.NSOutlineView)
    cell = m.mock(ImageAndTextCell)
    col, item, icon = m.mock(), m.mock(), m.mock()
    col.identifier() >> "name"
    representedObject(item).icon() >> icon
    cell.setImage_(icon)
    with m:
        ewc.outlineView_willDisplayCell_forTableColumn_item_(view, cell, col, item)

def test_outlineView_toolTipForCell_rect_tableColumn_item_mouseLocation_():
    ewc = EditorWindowController.alloc().init()
    m = Mocker()
    ewc.editor = ed = m.mock(Editor)
    ov = m.mock(ak.NSOutlineView)
    rect, item = m.mock(), m.mock()
    ed.tooltip_for_item(ov, item) >> "test tip"
    with m:
        result = ewc.outlineView_toolTipForCell_rect_tableColumn_item_mouseLocation_(
            ov, None, rect, None, item, None)
        assert len(result) == 2
        assert result[0] == "test tip"
        assert result[1] is rect

def test_EditorWindowController_undo_manager():
    wc = EditorWindowController.alloc().init()
    m = Mocker()
    win = m.mock(ak.NSWindow)
    wc.editor = m.mock(Editor)
    wc.editor.undo_manager() >> "<undo_manager>"
    with m:
        result = wc.undo_manager()
        eq_(result, "<undo_manager>")

def test_windowDidBecomeKey_():
    wc = EditorWindowController.alloc().init()
    m = Mocker()
    notif = m.mock()
    ed = wc.editor = m.mock(Editor)
    ed.window_did_become_key(notif.object() >> m.mock(ak.NSWindow))
    with m:
        wc.windowDidBecomeKey_(notif)

def test_windowShouldClose_():
    wc = EditorWindowController.alloc().init()
    m = Mocker()
    win = m.mock(ak.NSWindow)
    wc.editor = m.mock(Editor)
    wc.editor.window_should_close(win) >> "<should_close>"
    with m:
        result = wc.windowShouldClose_(win)
        eq_(result, "<should_close>")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#     def tableViewSelectionDidChange_(self, notification):
#         docs = self.docsController.selectedObjects()
#         doc = docs[0] if len(docs) == 1 else None
#         if doc is None:
#             if self.project is not None:
#                 self.project.newDocument()
#             else:
#                 sdc = NSDocumentController.sharedDocumentController()
#                 sdc.newDocument_(self)
#         else:
#             doc.addWindowController_(self)
