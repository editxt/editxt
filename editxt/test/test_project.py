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
from editxt.document import TextDocument
from editxt.editor import Editor
from editxt.project import Project, Recent
from editxt.util import dump_yaml
from editxt.window import Window, WindowController

from editxt.test.util import gentest, make_dirty, TestConfig, check_app_state, test_app

log = logging.getLogger(__name__)
# log.debug("""TODO
#     Project.is_dirty - should be True after a document is dragged within the project
# """)

def test_editor_interface():
    from editxt.test.test_editor import verify_editor_interface
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
    docs = []
    (kvo_class() << docs).count(2)
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
        def objcstr(value):
            value = ak.NSString.alloc().initWithString_(value)
            isinstance(value, objc.pyobjc_unicode), (type(value), value)
            return value
        def check(flag, key, serial, value=None):
            if flag:
                assert key in serial, (key, serial)
                if value is not None:
                    eq_(serial[key], value)
            else:
                assert key not in serial, key
        proj = Project(None)
        recent = [objcstr("/file.txt"), objcstr("/doc.xml")]
        if c.recent:
            proj.recent.extend(Recent(p) for p in recent)
        if c.name:
            proj.name = objcstr("<name>")
        if c.docs:
            proj.editors = [MockDoc(1)]
        proj.expanded = c.expn
        serial = proj.serialize()
        check(False, "path", serial, proj.path)
        check(c.name, "name", serial, proj.name)
        check(c.docs, "documents", serial)
        check(True, "expanded", serial, c.expn)
        check(c.recent, "recent", serial, recent)
        dump_yaml(serial) # verify that it does not crash
    c = TestConfig()
    for name in (True, False):
        for docs in (True, False):
            for rec in (True, False):
                yield test, c(name=name, docs=docs, recent=rec, expn=True)
                yield test, c(name=name, docs=docs, recent=rec, expn=False)

def test_serialize_project_with_errlog():
    with test_app("project") as app:
        project = app.windows[0].projects[0]
        project.create_editor_with_state({"internal": "errlog"})
        serial = project.serialize()
    print(serial)
    with test_app("window") as app:
        window = app.windows[0]
        project = Project(window, serial=serial)
        eq_(project.editors[0].document, app.errlog.document)

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
                eq_([r.path for r in proj.recent], serial.get("recent", []))
            #assert not proj.is_dirty
    #yield test, {"path": "<path>"} # project with path not implemented
    yield test, {"documents": []}
    yield test, {"documents": ["doc1"]}
    yield test, {"documents": ["doc1"], "name": "custom name"}
    yield test, {"documents": ["doc_not_found"], "name": "custom name"}
    yield test, {"documents": [], "expanded": True}
    yield test, {"documents": [], "expanded": False}
    yield test, {"documents": [], "recent": ["/file.txt"], "expanded": False}

def test_save():
    def test(proj_has_path, is_changed):
        m = Mocker()
        window = m.mock(Window)
        proj = Project(window)
        #save_with_path = m.method(proj.save_with_path)
        reset_cache = m.method(proj.reset_serial_cache)
        m.method(proj.serialize)() >> "<serial>"
        if proj_has_path:
            proj.path = "test/proj.tmp"
        if is_changed:
            app = window.app >> m.mock(Application)
            proj.serial_cache = "<invalid-cache>"
            #if proj_has_path:
            #    save_with_path(proj.path)
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
        eq_(test_app(app).state, "window project editor[untitled 0]")

def test_create_editor_with_recent_path():
    @gentest
    @test_app("project")
    def test(app, recent_after, path="/file.txt"):
        tapp = test_app(app)
        project = app.windows[0].projects[0]
        project.recent.append(Recent(tapp.temp_path("/file.txt")))
        project.create_editor(tapp.temp_path(path))
        eq_([tapp.pretty_path(r) for r in project.recent], recent_after)
        eq_(test_app(app).state, "window project editor[%s 0]" % path)

    yield test([])
    yield test(["/file.txt"], path="/doc.xml")

@test_app
def test_insert_items(app):
    proj = Project(None)
    doc = Editor(proj, document=app.document_with_path(None))
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

@test_app
def test_insert_items_already_in_project(app):
    proj = Project(None)
    editor = Editor(proj, document=app.document_with_path(None))
    proj.insert_items([editor])
    proj.insert_items([editor], action=const.COPY)
    eq_(len(proj.editors), 2, proj.editors)

def test_iter_editors_of_document():
    DOC = "the document we're looking for"
    def test(config):
        found = []
        proj = Project(None)
        proj.editors = docs = []
        m = Mocker()
        doc = m.mock(TextDocument)
        for item in config:
            editor = m.mock(Editor)
            docs.append(editor)
            editor.name >> item
            adoc = m.mock(TextDocument)
            editor.document >> (doc if item is DOC else adoc)
            if item is DOC:
                found.append(editor)
        with m:
            eq_(config, [editor.name for editor in docs])
            result = list(proj.iter_editors_of_document(doc))
            eq_(result, found)
    yield test, []
    yield test, [DOC]
    yield test, ["doc1", "doc2"]
    yield test, ["doc1", DOC, "doc3"]
    yield test, ["doc1", DOC, "doc3", DOC]

def test_remove():
    @gentest
    def test(recent_after, recent_before=(), path="/file.txt", config="project"):
        with test_app(config) as app:
            tapp = test_app(app)
            project = app.windows[0].projects[0]
            doc = tapp.document_with_path(path)
            project.recent.extend(
                Recent(tapp.temp_path(p)) for p in recent_before)
            editor = project.insert_items([doc], action=const.COPY)[1]
            project.remove(editor)
            print(test_app(app).state)
            eq_([tapp.pretty_path(r) for r in project.recent], recent_after)

    yield test([], path="file.txt")
    yield test(["/file.txt"])
    yield test(["/file.txt", "/doc.txt"], recent_before=["/doc.txt"])
    yield test(["/file.txt"], recent_before=["/file.txt"])
    yield test([], config="project editor(/file.txt)")

def test_can_rename():
    proj = Project(None)
    eq_(proj.path, None)
    assert proj.can_rename()
    proj.path = "<path>"
    assert proj.can_rename()

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
    project = Project(None)
    m = Mocker()
    view = m.mock()
    view.bounds() >> "<frame>"
    win = m.mock()
    with m:
        eq_(project.main_view, None)
        project.set_main_view_of_window(view, win)
        assert project.main_view is not None

def test_interactive_close():
    @gentest
    def test(config, prompt=[], close=True):
        calls = []
        def callback():
            calls.append(True)
        with test_app(config) as app:
            window = app.windows[0]
            project = window.projects[0]
            for editor in project.editors:
                if "dirty" in editor.document.file_path:
                    make_dirty(editor.document)
            project.interactive_close(callback)
            post_config = config.split()
            if prompt:
                post_config[0] += "*"
            eq_(test_app(app).state, "window project " + " ".join(post_config))
            eq_(window.wc.prompts, prompt)
            eq_(calls, [close] if close else [])

    yield test("editor")
    yield test("editor(dirty)", ["close dirty"], False)
    yield test("editor(dirty.save)", ["close dirty.save", "save dirty.save"], False) # save canceled
    yield test("editor(/dirty.save)", ["close dirty.save"])
    yield test("editor(dirty.dont_save)", ["close dirty.dont_save"])
    yield test("editor(dirty) project editor(dirty)")
    yield test("editor(/dirty.save) editor(/dirty.save)", ["close dirty.save"])

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
