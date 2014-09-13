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

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import *

import editxt
import editxt.constants as const
import editxt.application as mod
from editxt.application import Application, DocumentController, DocumentSavingDelegate
from editxt.commands import iterlines
from editxt.window import WindowController, Window
from editxt.document import TextDocument
from editxt.editor import Editor
from editxt.project import Project
from editxt.util import load_yaml

from editxt.test.util import (do_method_pass_through, gentest, TestConfig,
    replattr, test_app, tempdir)

log = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# test editxt.app global

def test_editxt_app():
    import editxt
    assert not hasattr(editxt, 'app'), editxt.app

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Application tests

# log.debug("""TODO implement
# """)

def test_application_init():
    from editxt.util import ContextMap
    app = Application()
    eq_(app.windows, [])
    assert isinstance(app.context, ContextMap)
    assert app.syntax_factory is None

def test_Application_logger():
    root = logging.getLogger()
    app = Application()
    handler = app.errlog_handler
    assert hasattr(app, "errlog"), app.errlog
    assert handler not in root.handlers, root.handlers
    with app.logger() as errlog:
        handler = app.errlog_handler
        assert handler in root.handlers, root.handlers
    assert handler not in root.handlers, root.handlers

def test_profile_path():
    def test(profile, profile_path):
        app = Application(profile)
        eq_(app.profile_path, profile_path)
    appname = Application.name().lower()
    yield test, None, os.path.expanduser('~/.' + appname)
    yield test, '~/.editxt', os.path.expanduser('~/.editxt')
    yield test, '/xt-profile', '/xt-profile'

def test_Application_config():
    app = Application("~/.editxt")
    eq_(app.config.path, os.path.expanduser("~/.editxt/config.yaml"))

def test_init_syntax_definitions():
    import editxt.syntax as syntax
    m = Mocker()
    app = Application(profile='/editxtdev')
    rsrc_path = m.method(app.resource_path)() >> "/tmp/resources"
    SyntaxFactory = m.replace(syntax, 'SyntaxFactory', spec=False)
    sf = SyntaxFactory() >> m.mock(syntax.SyntaxFactory)
    app_log = m.replace("editxt.application.log")
    for path, info in [(rsrc_path, False), ('/editxtdev', True)]:
        sf.load_definitions(os.path.join(path, const.SYNTAX_DEFS_DIR), info)
    sf.index_definitions()
    with m:
        app.init_syntax_definitions()

def test_syntaxdefs():
    from editxt.syntax import SyntaxFactory
    m = Mocker()
    app = Application()
    sf = app.syntax_factory = m.mock(SyntaxFactory)
    sf.definitions >> "<definitions>"
    with m:
        eq_(app.syntaxdefs, "<definitions>")

def test_application_will_finish_launching():
    from editxt.textcommand import TextCommandController
    def test(eds_config):
        app = Application()
        m = Mocker()
        create_window = m.method(app.create_window)
        open_error_log = m.method(app.open_error_log)
        nsapp = m.mock(ak.NSApplication)
        ud_class = m.replace(fn, 'NSUserDefaults')
        m.method(app.iter_saved_window_states)() >> iter(eds_config)
        tc = m.replace(app, 'text_commander', spec=TextCommandController)
        dc = m.mock(DocumentController)
        menu = dc.textMenu >> m.mock(ak.NSMenu)
        tc.load_commands(menu)
        if eds_config:
            error = False
            for ed_config in eds_config:
                if isinstance(ed_config, mod.StateLoadFailure):
                    error = True
                else:
                    create_window(ed_config)
            if error:
                open_error_log()
        else:
            create_window()
        with m:
            app.application_will_finish_launching(nsapp, dc)
            eq_(app.text_commander, tc)
    yield test, []
    yield test, [mod.StateLoadFailure("<path>")]
    yield test, ["project"]
    yield test, ["project 1", "project 2"]
    yield test, ["project 1", mod.StateLoadFailure("<path>"), "project 2"]

def test_create_window():
    import editxt.window as window #import Window
    def test(args):
        ac = Application()
        m = Mocker()
        ed_class = m.replace(window, 'Window')
        ed = ed_class(ac, args[0] if args else None) >> m.mock(window.Window)
        with m.order():
            ac.windows.append(ed)
            ed.show(ac)
        with m:
            result = ac.create_window(*args)
            eq_(result, ed)
    yield test, ("<serial data>",)
    yield test, ()

def test_open_path_dialog():
    def test(c):
        app = Application()
        m = Mocker()
        opc_class = m.replace(mod, 'OpenPathController')
        opc = m.mock(mod.OpenPathController)
        m.property(app, "path_opener").value >> (opc if c.exists else None)
        if c.exists:
            app.path_opener.window().makeKeyAndOrderFront_(app)
        else:
            opc_class(app) >> opc
            app.path_opener = opc
            opc.showWindow_(app)
        app.path_opener.populateWithClipboard()
        with m:
            app.open_path_dialog()
    c = TestConfig(exists=False)
    yield test, c
    yield test, c(exists=True)

def test_new_project():
    def test(has_current):
        m = Mocker()
        ac = Application()
        ac.current_window = m.method(ac.current_window)
        if has_current:
            ed = m.mock(Window)
            proj = (ac.current_window() >> ed).new_project() >> m.mock(Project)
        else:
            ac.current_window() >> None
            proj = None
        with m:
            result = ac.new_project()
            eq_(result, proj)
    yield test, True
    yield test, False

def test_document_with_path():
    def test(setup):
        with tempdir() as tmp, test_app() as app:
            docs = app.documents
            eq_(len(docs), 0)
            path = setup(tmp, app, docs)
            doc = app.document_with_path(path)
            try:
                assert isinstance(doc, TextDocument)
                if os.path.exists(path):
                    assert os.path.samefile(path, doc.file_path)
                else:
                    eq_(path, doc.file_path)
                eq_(doc.app, app)
            finally:
                doc.close()
            eq_(len(docs), 0)

    def plain_file(tmp, app, docs):
        path = os.path.join(tmp, "file.txt")
        with open(path, "w") as fh:
            fh.write("text")
        return path

    def symlink(tmp, app, docs):
        plain = plain_file(tmp, app, docs)
        path = os.path.join(tmp, "file.sym")
        assert plain != path, path
        os.symlink(os.path.basename(plain), path)
        return path

    def document_controller(tmp, app, docs):
        path = plain_file(tmp, app, docs)
        url = fn.NSURL.fileURLWithPath_(path)
        doc1 = docs.get_document(path)
        doc2 = app.document_with_path(path)
        assert doc1 is doc2, "%r is not %r" % (doc1, doc2)
        return path

    def nonexistent_file(tmp, app, docs):
        path = os.path.join(tmp, "file.txt")
        doc = app.document_with_path(path)
        assert not os.path.exists(path), "%s exists (but should not)" % path
        return path

    yield test, plain_file
    yield test, symlink
    yield test, document_controller
    yield test, nonexistent_file

def test_open_documents_with_paths():
    import editxt.document as edoc
    def test(c):
        m = Mocker()
        app = Application()
        create_window = m.method(app.create_window)
        window = m.mock(Window)
        m.method(app.current_window)() >> (window if c.has_window else None)
        if not c.has_window:
            create_window() >> window
        items = window.iter_dropped_paths("<paths>") >> m.mock()
        window.insert_items(items)
        with m:
            app.open_documents_with_paths("<paths>")
    c = TestConfig()
    yield test, c(has_window=False)
    yield test, c(has_window=True)

def test_open_config_file():
    def test(c):
        m = Mocker()
        app = Application()
        doc = m.mock(TextDocument)
        m.method(app.open_documents_with_paths)([app.config.path]) >> [doc]
        (doc.file_path << app.config.path).count(1, None)
        default_config = m.property(app.config, "default_config")
        m.replace("os.path.exists")(app.config.path) >> c.exists
        if not c.exists:
            doc.text >> c.text
            if not c.text:
                doc.text = default_config.value >> "# config"
        with m:
            app.open_config_file()
    c = TestConfig(exists=False)
    yield test, c(exists=True)
    yield test, c(text=True)
    yield test, c(text=False)

def test_open_error_log():
    def test(c):
        m = Mocker()
        ed = m.mock(Window)
        editor = m.mock(Editor)
        app = Application()
        with app.logger() as errlog:
            err = m.property(app.errlog, "document").value >> m.mock(TextDocument)
            if c.is_open:
                idocs = iter([editor])
                m.method(app.set_current_editor)(editor)
            else:
                idocs = iter([])
                m.method(app.current_window)() >> (ed if c.has_window else None)
                if not c.has_window:
                    m.method(app.create_window)() >> ed
                ed.insert_items([err])
            m.method(app.iter_editors_of_document)(err) >> idocs
            with m:
                app.open_error_log()
    c = TestConfig(is_open=False)
    yield test, c(is_open=True)
    yield test, c(has_window=True)
    yield test, c(has_window=False)

def test_iter_dirty_editors():
    def do_test(windows_template):
        app = Application()
        m = Mocker()
        seen = set()
        dirty_docs = []
        eds = []
        for ecfg in windows_template:
            projects = []
            for pcfg in ecfg:
                proj = m.mock(Project)
                projects.append(proj)
                editors = []
                has_dirty = False
                for doc_id in pcfg:
                    editor = m.mock(Editor)
                    editors.append(editor)
                    (editor.document.id << doc_id).count(1, 2)
                    if doc_id not in seen:
                        seen.add(doc_id)
                        dirty_docs.append(editor)
                        has_dirty = True
                proj.dirty_editors() >> editors
                if has_dirty:
                    dirty_docs.append(proj)
            ed = m.mock(Window)
            ed.projects >> projects
            eds.append(ed)
        m.method(app.iter_windows)() >> eds
        with m:
            result = list(app.iter_dirty_editors())
            eq_(result, dirty_docs)
    yield do_test, []
    yield do_test, [""]
    yield do_test, ["0"]
    yield do_test, ["01"]
    yield do_test, ["0", "1"]
    yield do_test, ["0", "0"]
    yield do_test, ["0", "10"]

def test_set_current_editor():
    ac = Application()
    m = Mocker()
    editor = m.mock(Editor)
    ac.find_window_with_editor = m.method(ac.find_window_with_editor)
    ed = ac.find_window_with_editor(editor) >> m.mock(Window)
    ed.current_editor = editor
    with m:
        ac.set_current_editor(editor)

def test_Application_close_current_document():
    def test(c):
        app = Application()
        m = Mocker()
        ed = m.mock(Window) if c.has_window else None
        m.method(app.current_window)() >> ed
        if c.has_window:
            editor = m.mock(Editor) if c.has_editor else None
            ed.current_editor >> editor
            if c.has_editor:
                editor.perform_close()
        with m:
            app.close_current_document()
    c = TestConfig(has_window=True, has_editor=True)
    yield test, c(has_window=False)
    yield test, c(has_editor=False)
    yield test, c

def test_Application_iter_editors_of_document():
    def test(config):
        ac = Application()
        m = Mocker()
        doc = m.mock(TextDocument)
        editors = []
        total_editors = 0
        windows = []
        for editor_count in config:
            window = m.mock(Window)
            windows.append(window)
            total_editors += editor_count
            eds = [m.mock(Editor) for i in range(editor_count)]
            window.iter_editors_of_document(doc) >> eds
            editors.extend(eds)
        m.method(ac.iter_windows)() >> windows
        with m:
            result = list(ac.iter_editors_of_document(doc))
            eq_(result, editors)
            eq_(len(result), total_editors)
    yield test, [0]
    yield test, [1]
    yield test, [2, 3, 4]

# def test_find_editor_with_document():
#   def test(c):
#       ac = Application()
#       m = Mocker()
#       editor = m.mock(Editor) if c.has_editor else None
#       doc = m.mock(TextDocument)
#       editors = m.method(ac.iter_editors_of_document)(doc) >> m.mock()
#       if c.has_editor:
#           next(editors) >> editor
#       else:
#           expect(next(editors)).throw(StopIteration)
#       with m:
#           result = ac.find_editor_with_document(doc)
#           eq_(result, editor)
#   c = TestConfig()
#   yield test, c(has_editor=True)
#   yield test, c(has_editor=False)

def test_iter_windows_with_editor_of_document():
    def test(c):
        result = None
        ac = Application()
        m = Mocker()
        doc = m.mock(TextDocument)
        found = []
        eds = m.method(ac.iter_windows)() >> []
        for e in c.eds:
            ed = m.mock(Window)
            eds.append(ed)
            if e.has_editor:
                editors = [m.mock(Editor)]
                found.append(ed)
            else:
                editors = []
            ed.iter_editors_of_document(doc) >> iter(editors)
        with m:
            result = list(ac.iter_windows_with_editor_of_document(doc))
            eq_(result, found)
            eq_(len(result), c.count)
    ed = lambda has_editor=True: TestConfig(has_editor=has_editor)
    c = TestConfig(eds=[], id=1, count=0)
    yield test, c
    yield test, c(eds=[ed(False)])
    yield test, c(eds=[ed()], count=1)
    yield test, c(eds=[ed(), ed(False)], count=1)
    yield test, c(eds=[ed(), ed(False), ed()], count=2)

def test_find_window_with_editor():
    DOC = "the editor we're looking for"
    def test(config):
        """Test argument structure:
        [ # collection of window controllers
            [ # window controller / collection of projects
                ["doc1", "doc2", "doc3", ...], # project / collection of editors
                ...
            ]
            ...
        ]
        """
        result = None
        ac = Application()
        m = Mocker()
        editor = m.mock(Editor) # this is the editor we're looking for
        document = m.mock(TextDocument)
        (editor.document << document).count(0, None)
        ac.iter_windows = m.method(ac.iter_windows)
        eds = ac.iter_windows() >> []
        for ed_projects in config:
            ed = m.mock(Window)
            eds.append(ed)
            projects = []
            ed.projects >> projects
            found = False
            for project_editors in ed_projects:
                project = m.mock(Project)
                projects.append(project)
                editors = []
                if not found:
                    project.editors >> editors
                for doc_name in project_editors:
                    if doc_name == DOC:
                        editors.append(editor)
                        result = ed
                        found = True
                    else:
                        editors.append(m.mock(Editor))
        with m:
            ed = ac.find_window_with_editor(editor)
            eq_(ed, result)
    yield test, []
    yield test, [[]]
    yield test, [[[DOC]]]
    yield test, [[["doc"], [DOC]]]
    yield test, [[["doc", DOC, "doc"]]]
    yield test, [[["doc"]]]
    yield test, [[["doc"]], [[DOC]]]

def test_add_window():
    ac = Application()
    m = Mocker()
    ed = m.mock(Window)
    assert not ac.windows
    with m:
        ac.add_window(ed)
    assert ed in ac.windows

def test_iter_windows():
    def test(config, unordered=0):
        """
        config - represents a list of window controllers in on-screen z-order
            with the front-most window controller first. Key:
                None - generic NSWindowController (not WindowController)
                <int> - Window index in ac.windows
        unordered - (optional, default 0) number of windows in
            ac.windows that are not in the on-screen z-order window
            list.
        """
        ac = Application()
        m = Mocker()
        app_class = m.replace(ak, 'NSApp')
        app = app_class()
        eds = {}
        unordered_eds = []
        z_windows = []
        for item in config:
            if item is None:
                wc = m.mock(ak.NSWindowController)
            else:
                wc = m.mock(WindowController)
                ed = m.mock(Window)
                print(ed, item)
                if item != 7:
                    (wc.window_ << ed).count(3)
                    unordered_eds.append(ed)
                else:
                    wc.window_ >> ed
                eds[item] = ed
            win = m.mock(ak.NSWindow)
            win.windowController() >> wc
            z_windows.append(win)
        for x in range(unordered):
            unordered_eds.append(m.mock(Window))
        ac.windows = unordered_eds # + [v for k, v in sorted(eds.items())]
        app.orderedWindows() >> z_windows
        sorted_eds = [eds[i] for i in config if i not in (None, 7)]
        sorted_eds.extend(ed for ed in unordered_eds if ed not in sorted_eds)
        with m:
            result = list(ac.iter_windows())
        eq_(result, sorted_eds)
    yield test, []
    yield test, [0]
    yield test, [0, 1]
    yield test, [1, 0]
    yield test, [1, 0, 2]
    yield test, [1, 0, 2, 7]
    yield test, [None, 1, None, None, 0, 2]
    yield test, [None, 1, None, 7, None, 0, 2, 7]
    yield test, [], 1
    yield test, [1, 0], 1
    yield test, [1, 0], 2
    yield test, [7, 1, 0], 2

def test_current_window():
    def test(config):
        ac = Application()
        m = Mocker()
        ac.iter_windows = iwc = m.method(ac.iter_windows)
        iwc() >> iter(config)
        with m:
            result = ac.current_window()
            eq_(result, (config[0] if config else None))
    yield test, []
    yield test, [0]
    yield test, [1, 0]

def test_discard_window():
    def test(c):
        m = Mocker()
        app = Application()
        ed = m.mock(Window)
        if c.ed_in_eds:
            app.windows.append(ed)
        def verify():
            assert ed not in app.windows, "ed cannot be in app.windows at this point"
        expect(ed.close()).call(verify)
        with m:
            app.discard_window(ed)
    c = TestConfig(ed_in_eds=True)
    yield test, c(ed_in_eds=False)
    yield test, c

def test_find_windows_with_project():
    PROJ = "the project"
    def test(eds_config, num_eds):
        eds_found = []
        ac = Application()
        m = Mocker()
        proj = m.mock(Project)
        ac.windows = eds = []
        for i, ed_config in enumerate(eds_config):
            ed = m.mock(Window)
            eds.append(ed)
            projects = []
            ed.projects >> projects
            found = False
            for item in ed_config:
                if item is PROJ and not found:
                    eds_found.append(ed)
                    project = proj
                    found = True
                else:
                    project = m.mock(Project)
                projects.append(project)
        with m:
            eq_(len(eds_found), num_eds)
            result = ac.find_windows_with_project(proj)
            eq_(result, eds_found)
    yield test, [], 0
    yield test, [[PROJ]], 1
    yield test, [["project", PROJ]], 1
    yield test, [["project", "project"], [PROJ]], 1
    yield test, [["project", PROJ], [PROJ, "project"]], 2

def test_find_project_with_path():
    def test(c):
        m = Mocker()
        ac = Application()
        ac.windows = eds = []
        found_proj = None
        for it in c.eds:
            ed = m.mock(Window)
            eds.append(ed)
            if found_proj is None:
                proj = m.mock(Project) if it.has_path else None
                ed.find_project_with_path(c.path) >> proj
                if it.has_path:
                    found_proj = proj
        with m:
            result = ac.find_project_with_path(c.path)
            eq_(result, found_proj)
            if c.found:
                assert result is not None
            else:
                assert result is None
    c = TestConfig(path="<path>", eds=[], found=True)
    ed = TestConfig(has_path=False)
    yield test, c(found=False)
    yield test, c(eds=[ed], found=False)
    yield test, c(eds=[ed, ed(has_path=True)])
    yield test, c(eds=[ed(has_path=True), ed, ed(has_path=True)])

def test_find_item_with_id():
    def test(c):
        m = Mocker()
        ac = Application()
        ac.windows = eds = []
        found_item = None
        for w in c.eds:
            ed = m.mock(Window)
            eds.append(ed)
            projs = (ed.projects >> [])
            for p in w.projs:
                proj = m.mock(Project)
                docs = []
                projs.append(proj)
                if found_item is None:
                    proj.id >> p.id
                    if p.id == c.id:
                        found_item = proj
                    else:
                        proj.editors >> docs
                for d in p.docs:
                    doc = m.mock(Editor)
                    docs.append(doc)
                    if found_item is None:
                        doc.id >> d.id
                        if d.id == c.id:
                            found_item = doc
        with m:
            result = ac.find_item_with_id(c.id)
            eq_(result, found_item)
            if c.found:
                assert result is not None
            else:
                assert result is None
    c = TestConfig(id=0, eds=[], found=True)
    ed = lambda projs:TestConfig(projs=projs)
    pj = lambda ident, docs:TestConfig(id=ident, docs=docs)
    dc = lambda ident:TestConfig(id=ident)
    yield test, c(found=False)
    yield test, c(eds=[ed([])], found=False)
    yield test, c(eds=[ed([pj(1, [])])], found=False)
    yield test, c(eds=[ed([pj(1, [dc(2)])])], found=False)
    yield test, c(eds=[ed([pj(0, [])])])
    yield test, c(eds=[ed([pj(0, [dc(2)])])])
    yield test, c(eds=[ed([pj(1, [dc(2)])]), ed([pj(3, [dc(0)])])])

class MockUserDefaults(object):
    def __init__(self):
        self.synced = False
    def arrayForKey_(self, key):
        return getattr(self, key, None)
    def setObject_forKey_(self, obj, key):
        setattr(self, key, obj)
    def synchronize(self):
        self.synced = True

def test_setup_profile_exists():
    with tempdir() as tmp:
        app = Application(tmp)
        eq_(app.setup_profile(), True)

def test_setup_profile_parent_exists():
    with tempdir() as tmp:
        path = os.path.join(tmp, 'profile')
        app = Application(path)
        eq_(app.setup_profile(), True)
        assert os.path.exists(path), path

def test_setup_profile_parent_missing():
    with tempdir() as tmp:
        path = os.path.join(tmp, 'missing', 'profile')
        app = Application(path)
        eq_(app.setup_profile(), False)
        assert not os.path.exists(path), path

def test_setup_profile_at_file():
    with tempdir() as tmp:
        path = os.path.join(tmp, 'profile')
        with open(path, 'w') as fh: pass
        app = Application(path)
        eq_(app.setup_profile(), False)
        assert os.path.isfile(path), path

def test_iter_saved_window_states():
    def test(states, error=None):
        with tempdir() as tmp:
            state_path = os.path.join(tmp, const.STATE_DIR)
            if states:
                # setup previous state
                m = Mocker()
                app = Application(tmp)
                def iter_windows():
                    for ident in states:
                        yield TestConfig(state=[ident])
                m.method(app.iter_windows)() >> iter_windows()
                with m:
                    app.save_window_states()
                assert os.listdir(state_path), state_path
                if error is not None:
                    fail_path = os.path.join(
                        state_path, const.EDITOR_STATE.format(error))
                    with open(fail_path, "w") as fh:
                        fh.write('!!invalid "yaml"')
            app = Application(tmp)
            result = list(app.iter_saved_window_states())
            eq_(result, [[id] if error != i else mod.StateLoadFailure(fail_path)
                         for i, id in enumerate(states)])
    yield test, []
    yield test, [3, 1, 2, 0]
    yield test, [666], 0

def test_save_window_state():
    def test(with_id=True, fail=False):
        with tempdir() as tmp:
            state_path = os.path.join(tmp, const.STATE_DIR)
            window = TestConfig(state=[42], id=9)
            args = (window.id,) if with_id else ()
            app = Application(tmp)
            state_name = app.save_window_state(window, *args)
            if fail:
                window = window(state="should not be written")
                def dump_fail(state, fh=None):
                    if fh is not None:
                        fh.write("should not be seen")
                    raise Exception("dump fail!")
                with replattr(mod, "dump_yaml", dump_fail, sigcheck=False):
                    state_name = app.save_window_state(window, *args)
            assert os.path.isdir(state_path), state_path
            with open(os.path.join(state_path, state_name)) as f:
                eq_(load_yaml(f), [42])
    yield test, True
    yield test, True, True
    #yield test, False not implemented

def test_save_window_states():
    def mock_windows(mock_iter_windows, windows):
        def iter_windows():
            for ident in windows:
                yield TestConfig(state=[ident])
        mock_iter_windows() >> iter_windows()
    def test(c):
        with tempdir() as tmp:
            state_path = os.path.join(tmp, const.STATE_DIR)
            if c.previous:
                # setup previous state
                m = Mocker()
                app = Application(tmp)
                mock_windows(m.method(app.iter_windows), c.previous)
                with m:
                    app.save_window_states()
                assert os.listdir(state_path), state_path

            m = Mocker()
            app = Application(tmp)
            mock_windows(m.method(app.iter_windows), c.windows)
            with m:
                app.save_window_states()
            assert os.path.isdir(state_path), state_path
            states = sorted(os.listdir(state_path))
            eq_(len(states), len(c.windows), states)
            for ident, state in zip(c.windows, states):
                with open(os.path.join(state_path, state)) as f:
                    eq_(load_yaml(f), [ident])
    c = TestConfig(windows=[], previous=[10, 20, 30])
    yield test, c
    yield test, c(windows=[1, 2])
    yield test, c(windows=[1, 2, 3, 4])

def test_should_terminate():
    @gentest
    def test(config, expected_calls=[]):
        with test_app(config) as app:
            m = Mocker()
            for item in config.split():
                if "(" in item:
                    editor = test_app.get(item, app)
                    is_dirty = m.replace(editor.document, "is_dirty")
                    (is_dirty() << True).count(0, 3)
            calls = []
            def callback(ok):
                calls.append(ok)
            with m:
                answer = app.should_terminate(callback)
                eq_(answer, (callback if calls else True))
                eq_(calls, expected_calls)
    # convention: editor(...) means that editor has unsaved changes
    yield test("")
    yield test("project")
    yield test("project editor editor project editor")
    yield test("editor(doc.save)", [False]) # no directory -> cancel save
    yield test("editor(/doc.save)", [True])
    yield test("editor(doc.dont_save)", [True])
    yield test("editor(cancel)", [False])
    yield test("editor(doc.dont_save) editor(cancel) editor(/doc.save)", [False])
    yield test("editor editor(doc.dont_save) project editor(/doc.save)", [True])

def test_will_terminate():
    app = Application()
    m = Mocker()
    m.method(app.save_window_states)() >> None
    with m:
        app.will_terminate()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DocumentSavingDelegate tests

#def test_DocumentSavingDelegate_init():
#    docs = object()
#    ctrl = object()
#    cbck = object()
#    saver = DocumentSavingDelegate.alloc().init_callback_(docs, cbck)
#    assert saver is DocumentSavingDelegate.registry[id(saver)]
#    assert saver.editors is docs
#    assert saver.callback is cbck
#    assert saver.should_close
#
#def test_save_next_document():
#    def do_test(doctype, doc_window_is_front=True):
#        m = Mocker()
#        docs = []
#        dc = m.mock(DocumentController)
#        note_ctr = m.replace(fn, 'NSNotificationCenter')
#        controller = m.mock()
#        callback = m.mock()
#        context = 0
#        saver = DocumentSavingDelegate.alloc().init_callback_(iter(docs), callback)
#        def do_stop_routine():
#            callback(saver.should_close)
#        if doctype is None:
#            do_stop_routine()
#        else:
#            doc = m.mock(doctype)
#            docs.append(doc)
#            if doctype is Project:
#                doc.save()
#                do_stop_routine()
#            elif doctype is Editor:
#                doc.project.window.current_editor = doc
#                win = m.mock()
#                doc.window() >> win
#                note_ctr.defaultCenter().addObserver_selector_name_object_(
#                    saver, "windowDidEndSheet:", ak.NSWindowDidEndSheetNotification, win)
#                document = doc.document >> m.mock(TextDocument)
#                wcs = m.mock(list)
#                (document.windowControllers() << wcs).count(1, 2)
#                wcs[0].window() >> (win if doc_window_is_front else m.mock())
#                if not doc_window_is_front:
#                    wcs.sort(key=ANY)
#                document.canCloseDocumentWithDelegate_shouldCloseSelector_contextInfo_(
#                    saver, "document:shouldClose:contextInfo:", context)
#        with m:
#            saver.save_next_document()
#        if doctype is Editor:
#            assert not saver.document_called_back
#            assert not saver.sheet_did_end
#        else:
#            eq_(saver.editors, None)
#            assert id(saver) not in saver.registry
#    yield do_test, Editor
#    yield do_test, Editor, False
#    yield do_test, Project
#    yield do_test, None
#
#def test_document_shouldClose_contextInfo_():
#    assert DocumentSavingDelegate.document_shouldClose_contextInfo_.signature == b'v@:@ci'
#    def do_test(should_close, sheet_did_end):
#        context = 0
#        m = Mocker()
#        saver = DocumentSavingDelegate.alloc().init_callback_(m.mock(), m.mock())
#        save_next_document = m.method(saver.save_next_document)
#        saver.sheet_did_end = sheet_did_end
#        if sheet_did_end:
#            save_next_document()
#        doc = m.mock(TextDocument)
#        with m:
#            saver.document_shouldClose_contextInfo_(doc, should_close, context)
#        assert saver.document_called_back
#        if not should_close:
#            assert not saver.should_close
#            try:
#                next(saver.editors)
#                raise AssertionError("next(saver.editors) should raise StopIteration")
#            except StopIteration:
#                pass
#        else:
#            assert saver.should_close
#    yield do_test, True, True
#    yield do_test, True, False
#    yield do_test, False, True
#    yield do_test, False, False
#
#def test_windowDidEndSheet_signature():
#    assert DocumentSavingDelegate.windowDidEndSheet_.signature == b'v@:@'
#
#def test_windowDidEndSheet_():
#    def do_test(called_back):
#        m = Mocker()
#        saver = DocumentSavingDelegate.alloc().init_callback_(m.mock(), m.mock())
#        saver.document_called_back = called_back
#        notif = m.mock(fn.NSNotification)
#        win = m.mock(ak.NSWindow)
#        notif.object() >> win
#        note_ctr = m.replace(fn, 'NSNotificationCenter')
#        note_ctr.defaultCenter().removeObserver_name_object_(
#            saver, ak.NSWindowDidEndSheetNotification, win)
#        save_next_document = m.method(saver.save_next_document)
#        if called_back:
#            save_next_document()
#        with m:
#            saver.windowDidEndSheet_(notif)
#            assert saver.sheet_did_end
#    yield do_test, True
#    yield do_test, False

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# OpenPathController tests
from editxt.application import OpenPathController

def test_OpenPathController_init():
    opc = OpenPathController(None)

def test_OpenPathController_windowDidLoad():
    m = Mocker()
    app = m.mock()
    opc = OpenPathController(app)
    tv = m.property(opc, "paths").value >> m.mock(ak.NSTextView)
    tc = tv.textContainer() >> m.mock(ak.NSTextContainer)
    tc.setContainerSize_(fn.NSMakeSize(const.LARGE_NUMBER_FOR_TEXT, const.LARGE_NUMBER_FOR_TEXT))
    tc.setWidthTracksTextView_(False)
    tv.setHorizontallyResizable_(True)
    tv.setAutoresizingMask_(ak.NSViewNotSizable)
    tv.setFieldEditor_(True)
    tv.setFont_(ANY)
    with m:
        opc.windowDidLoad()
        eq_(opc.app, app)

def test_OpenPathController_populateWithClipboard():
    # initialize main text field with clipboard content (if its text)
    def test(c):
        m = Mocker()
        opc = OpenPathController(None)
        paths = m.property(opc, "paths").value >> m.mock(ak.NSTextView)
        with m.order():
            ts = paths.textStorage() >> m.mock(ak.NSTextStorage)
            #ts.deleteCharactersInRange_((0, ts.string().length() >> c.len0))
            paths.setSelectedRange_((0, ts.string().length() >> c.len0))
            paths.pasteAsPlainText_(opc)
            paths.setSelectedRange_((0, ts.string().length() >> c.len1))
        with m:
            opc.populateWithClipboard()
    c = TestConfig
    yield test, c(len0=0, len1=3)
    yield test, c(len0=5, len1=8)

def test_OpenPathController_textView_doCommandBySelector_():
    def test(c):
        m = Mocker()
        nsapp = m.replace(ak, 'NSApp', spec=False)
        opc = OpenPathController(None)
        tv = m.mock(ak.NSTextView)
        if c.sel == "insertNewline:":
            nsapp().currentEvent().modifierFlags() >> c.mod
            if c.mod & ak.NSCommandKeyMask or c.mod & ak.NSShiftKeyMask:
                tv.insertNewlineIgnoringFieldEditor_(opc)
            else:
                m.method(opc.open_)(opc)
            # check for shift or command (tv.insertTabIgnoringFieldEditor_(self))
            # otherwise open file
        with m:
            eq_(opc.textView_doCommandBySelector_(tv, c.sel), c.res)
    c = TestConfig(sel="insertNewline:", mod=0, res=False)
    yield test, c
    yield test, c(mod=ak.NSCommandKeyMask, res=True)
    yield test, c(mod=ak.NSShiftKeyMask, res=True)
    yield test, c(mod=ak.NSAlternateKeyMask, res=False)
    yield test, c(sel="<otherSelector>")

def test_OpenPathController_open_():
    # TODO accept wildcards in filenames?
    def test(c):
        m = Mocker()
        app = m.mock(Application)
        opc = OpenPathController(app)
        paths = m.property(opc, "paths").value >> m.mock(ak.NSTextView)
        paths.textStorage().string() >> c.text
        def check_paths(paths):
            eq_(c.paths, list(paths))
        expect(app.open_documents_with_paths(ANY)).call(check_paths)
        (m.method(opc.window)() >> m.mock(ak.NSWindow)).orderOut_(opc)
        with m:
            opc.open_(None)
    c = TestConfig()
    yield test, c(text="", paths=[])
    yield test, c(text="abc", paths=["abc"])
    yield test, c(text="abc\ndef", paths=["abc", "def"])
    yield test, c(text="abc \n \n\tdef", paths=["abc", "def"])
