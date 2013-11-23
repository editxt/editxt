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
from tempfile import gettempdir

import AppKit as ak
import Foundation as fn
import objc
from mocker import Mocker, expect, ANY, MATCH
from nose.tools import *

import editxt.constants as const
import editxt.project as mod
from editxt.application import Application, DocumentController
from editxt.editor import Editor, EditorWindowController
from editxt.document import TextDocumentView, TextDocument
from editxt.project import Project
from editxt.util import dump_yaml

from editxt.test.util import TestConfig, check_app_state

log = logging.getLogger(__name__)
# log.debug("""TODO
#     Project.is_dirty - should be True after a document is dragged within the project
# """)

def test_document_view_interface():
    from editxt.test.test_document import verify_document_view_interface
    view = Project.create()
    verify_document_view_interface(view)

def test_is_project_path():
    def test(path, expected):
        result = Project.is_project_path(path)
        eq_(result, expected, "Project.is_project_path(%r) returned wrong value: %s" % (path, result))
    for path, result in (
        ("/", False),
        ("/test", False),
        ("test." + const.PROJECT_EXT, True),
        ("/path/test." + const.PROJECT_EXT, True),
        ("/path/test.something." + const.PROJECT_EXT, True),
    ):
        yield test, path, result

def test_create_and_init():
    proj = Project.create()
    assert proj.path is None
    eq_(len(proj.documents()), 0)
    eq_(proj.serial_cache, proj.serialize())

@check_app_state
def test_create_with_path():
    path = "/temp/non-existent/project.edxt"
    assert not os.path.exists(path)
    result = Project.create_with_path(path)
    try:
        eq_(result.path, path)
    finally:
        result.close()

@check_app_state
def test_create_with_serial():
    m = Mocker()
    serial = {"path": "/temp/non-existent/project.edxt"}
    assert not os.path.exists(serial["path"])
    with m:
        result = Project.create_with_serial(serial)
        try:
            eq_(result.path, serial["path"])
        finally:
            result.close()

@check_app_state
def test_init_with_serial():
    m = Mocker()
    kvo_class = m.replace(mod, 'KVOList')
    deserialize = m.method(Project.deserialize)
    reset_cache = m.method(Project.reset_serial_cache)
    docs = kvo_class() >> []
    deserialize("<serial>")
    reset_cache(); m.count(2)
    with m:
        proj = Project.init_with_serial("<serial>")

class MockDoc(object):
    def __init__(self, ident):
        self.ident = ident
    @property
    def edit_state(self):
        return {"path": "doc_%s" % self.ident}
    @property
    def document(self):
        return "<doc %s>" % self.ident

def test_serialize_project():
    def test(path_is_none):
        proj = Project.create()
        m = Mocker()
        if path_is_none:
            assert proj.path is None
            doc_states = []
            for x in range(3):
                doc = MockDoc(x)
                doc_states.append(doc.edit_state)
                proj.append_document_view(doc)
            testkey = dict(documents=doc_states, expanded=True)
            if proj.name != const.UNTITLED_PROJECT_NAME:
                testkey["name"] = proj.name
        else:
            proj.path = "<path>"
            testkey = {"path": proj.path}
        with m:
            result = proj.serialize()
            eq_(result, testkey)
    yield test, True
    yield test, False

def test_serialize_full():
    def test(c):
        def check(flag, key, serial, value=None):
            if flag:
                assert key in serial, key
                if value is not None:
                    eq_(serial[key], value)
            else:
                assert key not in serial, key
        proj = Project.create()
        if c.path:
            proj.path = "<path>"
        if c.name:
            proj.name = ak.NSString.alloc().initWithString_("<name>")
            assert isinstance(proj.name, objc.pyobjc_unicode), type(proj.name)
        if c.docs:
            proj._documents = [MockDoc(1)]
        proj.expanded = c.expn
        serial = proj.serialize_full()
        check(c.path, "path", serial, proj.path)
        check(c.name, "name", serial, proj.name)
        check(c.docs, "documents", serial)
        check(True, "expanded", serial, c.expn)
        dump_yaml(serial) # verify that it does not crash
    c = TestConfig()
    for path in (True, False):
        for name in (True, False):
            for docs in (True, False):
                yield test, c(path=path, name=name, docs=docs, expn=True)
                yield test, c(path=path, name=name, docs=docs, expn=False)

def test_deserialize_project():
    from Foundation import NSData, NSPropertyListSerialization, NSPropertyListImmutable
    from editxt.project import KVOList
    def test(serial):
        m = Mocker()
        proj = Project.create()
        log = m.replace(mod, 'log')
        nsdat = m.replace(fn, 'NSData')
        nspls = m.replace(fn, 'NSPropertyListSerialization')
        create_document_view_with_state = m.method(Project.create_document_view_with_state)
        create_document_view = m.method(Project.create_document_view)
        proj._documents = docs = m.mock(KVOList)
        if "path" in serial:
            data = nsdat.dataWithContentsOfFile_(serial["path"]) >> m.mock()
            serial_, format, error = nspls. \
                propertyListFromData_mutabilityOption_format_errorDescription_( \
                    data, NSPropertyListImmutable, None, None) >> ({}, m.mock(), None)
        else:
            serial_ = serial
        docs_ = serial_.get("documents", [])
        for item in docs_:
            create_document_view_with_state(item)
            if item == "doc_not_found":
                m.throw(Exception("document not found"))
                log.warn("cannot open document: %r" % item)
            #proj._is_dirty = True
        bool(docs); m.result(bool(docs_))
        if not docs_:
            create_document_view()
            #proj._is_dirty = True
        with m:
            proj.deserialize(serial)
            if "path" in serial:
                eq_(proj.path, serial["path"])
                assert "name" not in serial
            else:
                eq_(proj.name, serial.get("name", const.UNTITLED_PROJECT_NAME))
                eq_(proj.expanded, serial.get("expanded", True))
            #assert not proj.is_dirty
    yield test, {"path": "<path>"}
    yield test, {"documents": []}
    yield test, {"documents": ["doc1"]}
    yield test, {"documents": ["doc1"], "name": "custom name"}
    yield test, {"documents": ["doc_not_found"], "name": "custom name"}
    yield test, {"documents": [], "expanded": True}
    yield test, {"documents": [], "expanded": False}

def test_save():
    def test(proj_has_path, is_changed):
        m = Mocker()
        proj = Project.create()
        app = m.replace(mod, 'app')
        save_with_path = m.method(proj.save_with_path)
        reset_cache = m.method(proj.reset_serial_cache)
        m.method(proj.serialize_full)() >> "<serial>"
        if proj_has_path:
            proj.path = "test/proj.tmp"
        if is_changed:
            proj.serial_cache = "<invalid-cache>"
            if proj_has_path:
                save_with_path(proj.path)
            app.save_editor_states()
            reset_cache()
        else:
            proj.serial_cache = "<serial>"
        with m:
            proj.save()
    for is_changed in (True, False):
        yield test, True, is_changed
        yield test, False, is_changed

def test_save_with_path_when_project_has_a_path():
    m = Mocker()
    path = "<path>"
    nsdict = m.replace(fn, 'NSMutableDictionary')
    proj = Project.create()
    proj.name = "<name>"
    serial = proj.serialize()
    assert serial, "serial should not be empty: %r" % (serial,)
    serial["path"] = path
    proj.path = path
    data = nsdict.alloc().init() >> m.mock(dict)
    data.update(serial)
    data.writeToFile_atomically_(path, True); m.nospec()
    with m:
        proj.save_with_path(path)

@check_app_state
def test_save_and_load_project_with_path():
    def do_save_project(path):
        proj = Project.create()
        m = Mocker()
        doc = m.mock(TextDocumentView)
        doc.edit_state >> {"path": "xyz"}
        doc.project = proj
        with m:
            proj.append_document_view(doc)
            proj.save_with_path(path)
            assert os.path.exists(path), "project not saved: %s" % path
    def do_load_project(path):
        import editxt.project as mod
        m = Mocker()
        create_document_view_with_state = m.method(Project.create_document_view_with_state)
        create_document_view_with_state(ANY)
        with m:
            proj = Project.create_with_path(path)
            try:
                assert proj.path == path
                assert len(proj.documents()) == 1
            finally:
                proj.close()
    path = os.path.join(gettempdir(), "test.edxt")
    if os.path.exists(path):
        log.warn("removing test project before running test: %s", path)
        os.remove(path)
    try:
        yield do_save_project, path
        yield do_load_project, path
    finally:
        if os.path.exists(path):
            os.remove(path)

# def test_save_if_dirty():
#     def do_test(is_dirty):
#         proj = Project.create()
#         proj.is_dirty = is_dirty
#         m = Mocker()
#         proj.save = m.method(proj.save)
#         if is_dirty:
#             proj.save()
#         with m:
#             proj.save_if_dirty()
#     yield do_test, False
#     yield do_test, True

def test_create_document_view_with_state():
    proj = Project.create()
    m = Mocker()
    state = m.mock()
    dv_class = m.replace(mod, 'TextDocumentView')
    dv = m.mock(TextDocumentView)
    dv_class.create_with_state(state, proj) >> dv
    dv.project = proj
    with m:
        result = proj.create_document_view_with_state(state)
        eq_(result, dv)
        assert dv in proj.documents()

def test_create_document_view():
    proj = Project.create()
    m = Mocker()
    nsdc = m.replace(ak, 'NSDocumentController')
    append_document_view = m.method(proj.append_document_view)
    dc = m.mock(ak.NSDocumentController)
    doc = m.mock(TextDocument)
    dv_class = m.replace(mod, 'TextDocumentView')
    dv = m.mock(TextDocumentView)
    nsdc.sharedDocumentController() >> dc
    dc.makeUntitledDocumentOfType_error_(const.TEXT_DOCUMENT, None) >> (doc, None)
    dc.addDocument_(doc)
    dv_class.create_with_document(doc, proj) >> dv
    append_document_view(dv) >> dv
    with m:
        result = proj.create_document_view()
        eq_(result, dv)

def test_append_document_view():
    proj = Project.create()
    #assert not proj.is_dirty
    m = Mocker()
    doc = m.mock(TextDocumentView)
    doc.project = proj
    with m:
        proj.append_document_view(doc)
    assert doc in proj.documents()
    #assert proj.is_dirty

def test_dirty_documents():
    def do_test(template):
        proj = Project.create()
        temp_docs = proj._documents
        try:
            m = Mocker()
            all_docs = []
            dirty_docs = []
            for item in template:
                doc = m.mock(TextDocumentView)
                all_docs.append(doc)
                doc.is_dirty >> (item == "d")
                if item == "d":
                    dirty_docs.append(doc)
            proj._documents = all_docs
            with m:
                result = list(proj.dirty_documents())
                assert len(dirty_docs) == template.count("d")
                assert dirty_docs == result, "%r != %r" % (dirty_docs, result)
        finally:
            proj._documents = temp_docs
    yield do_test, ""
    yield do_test, "c"
    yield do_test, "d"
    yield do_test, "dd"
    yield do_test, "dcd"

def test_append_document_view_already_in_project():
    class Fake(object): pass
    proj = Project.create()
    dv = Fake()
    proj.append_document_view(dv)
    proj.append_document_view(dv)
    assert len(proj.documents()) == 2, proj.documents()

def test_remove_document_view():
    class MockView(object):
        project = None
    project = Project.create()
    doc = MockView()
    project.insert_document_view(0, doc)
    assert doc in project.documents()
    eq_(doc.project, project)
    #project.is_dirty = False
    project.remove_document_view(doc)
    #assert project.is_dirty
    assert doc not in project.documents()
    eq_(doc.project, None)

def test_find_view_with_document():
    DOC = "the document we're looking for"
    def test(config):
        theview = None
        proj = Project.create()
        proj._documents = docs = []
        m = Mocker()
        doc = m.mock(TextDocument)
        found = False
        for item in config:
            view = m.mock(TextDocumentView)
            docs.append(view)
            view.name >> item
            if not found:
                adoc = m.mock(TextDocument)
                view.document >> (doc if item is DOC else adoc)
                if item is DOC:
                    theview = view
                    found = True
        with m:
            eq_(config, [view.name for view in docs])
            result = proj.find_view_with_document(doc)
            eq_(result, theview)
    yield test, []
    yield test, [DOC]
    yield test, ["doc1", "doc2"]
    yield test, ["doc1", DOC, "doc3"]

# def test_get_set_is_dirty():
#     from editxt import app
#     m = Mocker()
#     item_changed = m.method(app.item_changed)
#     proj = Project.create()
#     # first test that item_changed is not called
#     with m:
#         assert not proj.is_dirty
#         proj.is_dirty = False
#     # now test that item_changed is called when is_dirty changes
#     item_changed(proj)
#     with m:
#         assert not proj.is_dirty
#         proj.is_dirty = True
#         assert proj.is_dirty

def test_can_rename():
    proj = Project.create()
    eq_(proj.path, None)
    assert proj.can_rename()
    proj.path = "<path>"
    assert not proj.can_rename()

def test_displayName():
    proj = Project.create()
    eq_(proj.displayName(), const.UNTITLED_PROJECT_NAME)
    proj.setDisplayName_("name")
    eq_(proj.displayName(), "name")
    proj.path = path = "/tmp/test.edxt"
    eq_(proj.displayName(), "test")

def test_setDisplayName_():
    proj = Project.create()
    assert proj.path is None
    #assert not proj.is_dirty
    eq_(proj.displayName(), const.UNTITLED_PROJECT_NAME)
    proj.setDisplayName_("name")
    #assert proj.is_dirty
    eq_(proj.displayName(), "name")
    #proj.is_dirty = False
    proj.path = path = "/tmp/test.edxt"
    eq_(proj.displayName(), "test")
    #assert not proj.is_dirty
    proj.setDisplayName_("name")
    #assert not proj.is_dirty
    eq_(proj.displayName(), "test")

def test_set_main_view_of_window():
    proj = Project.create()
    m = Mocker()
    view = m.mock(ak.NSView)
    win = m.mock(ak.NSWindow)
    with m:
        proj.set_main_view_of_window(view, win) # for now this does nothing

def test_perform_close():
    import editxt.application as xtapp
    def test(c):
        proj = Project.create()
        m = Mocker()
        dsd_class = m.replace(xtapp, 'DocumentSavingDelegate')
        app = m.replace(mod, 'app')
        ed = m.mock(Editor)
        app.find_editors_with_project(proj) >> [ed for x in range(c.num_eds)]
        if c.num_eds == 1:
            docs = [m.mock(TextDocumentView)]
            doc = docs[0].document >> m.mock(TextDocument)
            app.iter_editors_with_view_of_document(doc) >> \
                (ed for x in range(c.num_doc_views))
            dirty_documents = m.method(proj.dirty_documents)
            dirty_documents() >> docs
            def check_docs(_docs):
                d = docs if c.num_doc_views == 1 else []
                eq_(list(_docs), d + [proj])
                return True
            callback = []
            def get_callback(func):
                callback.append(func)
                return True
            def do_callback():
                callback[0](c.should_close)
            saver = m.mock(xtapp.DocumentSavingDelegate)
            dsd_class.alloc() >> saver
            saver.init_callback_(MATCH(check_docs), MATCH(get_callback)) >> saver
            expect(saver.save_next_document()).call(do_callback)
            if c.should_close:
                ed.discard_and_focus_recent(proj)
        else:
            ed.discard_and_focus_recent(proj)
        with m:
            proj.perform_close(ed)
    c = TestConfig(num_eds=1)
    for ndv in range(3):
        yield test, c(should_close=True, num_doc_views=ndv)
        yield test, c(should_close=False, num_doc_views=ndv)
    yield test, c(num_eds=0)
    yield test, c(num_eds=2)


# def test_close_with_editor():
#     proj = Project.create()
#     m = Mocker()
#     ed = m.mock(Editor)
#     ed.discard_and_focus_recent(proj)
#     m.method(proj.close)()
#     with m:
#         proj.close_with_editor(ed)

def test_close():
    proj = Project.create()
    m = Mocker()
    proj._documents = docs = []
    for i in range(2):
        dv = m.mock(TextDocumentView)
        docs.append(dv)
        dv.close()
    with m:
        proj.close()



#         dc = NSDocumentController.sharedDocumentController()
#         controllers = dc.window_controllers_with_project(self)
#         if len(controllers) == 1 and self.path is not None:
#             # save project
#             pass
#         # close the project (remove it from the window_controller, etc.)
