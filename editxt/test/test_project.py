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
from editxt.datatypes import WeakProperty
from editxt.document import Editor, TextDocument
from editxt.project import Project
from editxt.util import dump_yaml
from editxt.window import Window, WindowController

from editxt.test.util import TestConfig, check_app_state, test_app

log = logging.getLogger(__name__)
# log.debug("""TODO
#     Project.is_dirty - should be True after a document is dragged within the project
# """)

def test_editor_interface():
    from editxt.test.test_document import verify_editor_interface
    editor = Project(None)
    verify_editor_interface(editor)

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

def test__init__():
    proj = Project(Window)
    assert proj.path is None
    eq_(proj.window, Window)
    eq_(len(proj.editors), 0)
    eq_(proj.serial_cache, proj.serialize())

@check_app_state
def test__init__serial():
    m = Mocker()
    window = m.mock(Window)
    kvo_class = m.replace(mod, 'KVOList')
    deserialize = m.method(Project._deserialize)
    reset_cache = m.method(Project.reset_serial_cache)
    docs = kvo_class() >> []
    deserialize("<serial>")
    reset_cache()
    with m:
        proj = Project(window, serial="<serial>")
        eq_(proj.window, window)

class MockDoc(object):
    proxy = WeakProperty()
    _target = WeakProperty()
    def __init__(self, ident):
        self.ident = ident
        self.proxy = self
        self._target = self
    @property
    def edit_state(self):
        return {"path": "doc_%s" % self.ident}
    @property
    def document(self):
        return "<doc %s>" % self.ident

def test_serialize_project():
    def test(c):
        def check(flag, key, serial, value=None):
            if flag:
                assert key in serial, (key, serial)
                if value is not None:
                    eq_(serial[key], value)
            else:
                assert key not in serial, key
        proj = Project(None)
        if c.name:
            proj.name = ak.NSString.alloc().initWithString_("<name>")
            assert isinstance(proj.name, objc.pyobjc_unicode), type(proj.name)
        if c.docs:
            proj.editors = [MockDoc(1)]
        proj.expanded = c.expn
        serial = proj.serialize()
        check(False, "path", serial, proj.path)
        check(c.name, "name", serial, proj.name)
        check(c.docs, "documents", serial)
        check(True, "expanded", serial, c.expn)
        dump_yaml(serial) # verify that it does not crash
    c = TestConfig()
    for name in (True, False):
        for docs in (True, False):
            yield test, c(name=name, docs=docs, expn=True)
            yield test, c(name=name, docs=docs, expn=False)

def test_deserialize_project():
    from Foundation import NSData, NSPropertyListSerialization, NSPropertyListImmutable
    from editxt.project import KVOList
    def test(serial):
        m = Mocker()
        proj = Project(None)
        log = m.replace(mod, 'log')
        nsdat = m.replace(fn, 'NSData')
        nspls = m.replace(fn, 'NSPropertyListSerialization')
        create_editor_with_state = m.method(Project.create_editor_with_state)
        create_editor = m.method(Project.create_editor)
        proj.editors = docs = m.mock(KVOList)
        if "path" in serial:
            data = nsdat.dataWithContentsOfFile_(serial["path"]) >> m.mock()
            serial_, format, error = nspls. \
                propertyListFromData_mutabilityOption_format_errorDescription_( \
                    data, NSPropertyListImmutable, None, None) >> ({}, m.mock(), None)
        else:
            serial_ = serial
        docs_ = serial_.get("documents", [])
        for item in docs_:
            create_editor_with_state(item)
            if item == "doc_not_found":
                m.throw(Exception("document not found"))
                log.warn("cannot open document: %r" % item)
            #proj._is_dirty = True
        bool(docs); m.result(bool(docs_))
        if not docs_:
            create_editor()
            #proj._is_dirty = True
        with m:
            proj._deserialize(serial)
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
        window = m.mock(Window)
        proj = Project(window)
        save_with_path = m.method(proj.save_with_path)
        reset_cache = m.method(proj.reset_serial_cache)
        m.method(proj.serialize)() >> "<serial>"
        if proj_has_path:
            proj.path = "test/proj.tmp"
        if is_changed:
            app = window.app >> m.mock(Application)
            proj.serial_cache = "<invalid-cache>"
            if proj_has_path:
                save_with_path(proj.path)
            app.save_window_states()
            reset_cache()
        else:
            proj.serial_cache = "<serial>"
        with m:
            proj.save()
    for is_changed in (True, False):
        yield test, True, is_changed
        yield test, False, is_changed

def test_create_editor_with_state():
    with test_app() as app:
        window = TestConfig(app=app)
        project = Project(window)
        state = {"path": "Untitled"}
        result = project.create_editor_with_state(state)
        eq_(result.project, project)
        assert result in project.editors, project.editors

def test_create_editor():
    with test_app("project") as app:
        project = app.windows[0].projects[0]
        eq_(len(project.editors), 0)
        project.create_editor()
        eq_(len(project.editors), 1)
        eq_(test_app.config(app), "window project editor[Untitled 0]")

def test_insert_items():
    proj = Project(None)
    doc = Editor(proj, document="fake")
    doc.project = proj
    proj.insert_items([doc])
    assert doc in proj.editors

def test_dirty_editors():
    def do_test(template):
        proj = Project(None)
        temp_docs = proj.editors
        try:
            m = Mocker()
            all_docs = []
            dirty_docs = []
            for item in template:
                doc = m.mock(Editor)
                all_docs.append(doc)
                doc.is_dirty >> (item == "d")
                if item == "d":
                    dirty_docs.append(doc)
            proj.editors = all_docs
            with m:
                result = list(proj.dirty_editors())
                assert len(dirty_docs) == template.count("d")
                assert dirty_docs == result, "%r != %r" % (dirty_docs, result)
        finally:
            proj.editors = temp_docs
    yield do_test, ""
    yield do_test, "c"
    yield do_test, "d"
    yield do_test, "dd"
    yield do_test, "dcd"

def test_insert_items_already_in_project():
    class Fake(object):
        def displayName(self):
            return "fake"
    proj = Project(None)
    editor = Editor(proj, document=Fake())
    proj.insert_items([editor])
    proj.insert_items([editor], action=const.COPY)
    eq_(len(proj.editors), 2, proj.editors)

def test_remove_editor():
    class Fake(object):
        def displayName(self):
            return "fake"
    project = Project(None)
    editor = Editor(project, document=Fake())
    project.insert_items([editor])
    assert editor in project.editors
    eq_(editor.project, project)
    #project.is_dirty = False
    project.remove_editor(editor)
    #assert project.is_dirty
    assert editor not in project.editors
    eq_(editor.project, None)

def test_find_editor_with_document():
    DOC = "the document we're looking for"
    def test(config):
        theeditor = None
        proj = Project(None)
        proj.editors = docs = []
        m = Mocker()
        doc = m.mock(TextDocument)
        found = False
        for item in config:
            editor = m.mock(Editor)
            docs.append(editor)
            editor.name >> item
            if not found:
                adoc = m.mock(TextDocument)
                editor.document >> (doc if item is DOC else adoc)
                if item is DOC:
                    theeditor = editor
                    found = True
        with m:
            eq_(config, [editor.name for editor in docs])
            result = proj.find_editor_with_document(doc)
            eq_(result, theeditor)
    yield test, []
    yield test, [DOC]
    yield test, ["doc1", "doc2"]
    yield test, ["doc1", DOC, "doc3"]

def test_can_rename():
    proj = Project(None)
    eq_(proj.path, None)
    assert proj.can_rename()
    proj.path = "<path>"
    assert not proj.can_rename()

def test_name():
    proj = Project(None)
    eq_(proj.name, const.UNTITLED_PROJECT_NAME)
    proj.name = "name"
    eq_(proj.name, "name")

def test_set_name():
    proj = Project(None)
    assert proj.path is None
    eq_(proj.name, const.UNTITLED_PROJECT_NAME)
    proj.name = "name"
    eq_(proj.name, "name")

def test_set_main_view_of_window():
    proj = Project(None)
    m = Mocker()
    view = m.mock(ak.NSView)
    win = m.mock(ak.NSWindow)
    with m:
        proj.set_main_view_of_window(view, win) # for now this does nothing

def test_perform_close():
    import editxt.application as xtapp
    def test(c):
        m = Mocker()
        dsd_class = m.replace(xtapp, 'DocumentSavingDelegate')
        ed = m.mock(Window)
        proj = Project(ed)
        app = ed.app >> m.mock(Application)
        app.find_windows_with_project(proj) >> [ed for x in range(c.num_eds)]
        if c.num_eds == 1:
            docs = [m.mock(Editor)]
            doc = docs[0].document >> m.mock(TextDocument)
            app.iter_windows_with_editor_of_document(doc) >> \
                (ed for x in range(c.num_editors))
            dirty_editors = m.method(proj.dirty_editors)
            dirty_editors() >> docs
            def check_docs(_docs):
                d = docs if c.num_editors == 1 else []
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
            proj.perform_close()
    c = TestConfig(num_eds=1)
    for ndv in range(3):
        yield test, c(should_close=True, num_editors=ndv)
        yield test, c(should_close=False, num_editors=ndv)
    yield test, c(num_eds=0)
    yield test, c(num_eds=2)

def test_close():
    m = Mocker()
    window = m.mock(name="window")
    proj = Project(window)
    proj.editors = docs = []
    for i in range(2):
        dv = m.mock(Editor)
        docs.append(dv)
        dv.close()
    with m:
        proj.close()
    eq_(proj.proxy, None)
    eq_(proj.window, None)
    eq_(proj.editors, None)
