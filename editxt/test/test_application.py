# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
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

from tempfile import gettempdir
from AppKit import *
from Foundation import *

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import *

import editxt.constants as const
from editxt.application import Application, DocumentController, DocumentSavingDelegate
from editxt.editor import EditorWindowController, Editor
from editxt.document import TextDocumentView, TextDocument
from editxt.project import Project

from editxt.test.util import do_method_pass_through, TestConfig

log = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# test editxt.app global

def test_editxt_app():
    import editxt
    dc = DocumentController.sharedDocumentController()
    assert editxt.app is dc.controller

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Application tests

# log.debug("""TODO implement
# """)

def test_application_init():
    from editxt.util import ContextMap
    from editxt.errorlog import ErrorLog
    m = Mocker()
    m.replace("editxt.valuetrans.register_value_transformers", passthrough=False)()
    with m:
        app = Application()
        eq_(app.editors, [])
        assert isinstance(app.context, ContextMap)

def test_app_support_path():
    def test(c):
        m = Mocker()
        search_path = m.replace(NSSearchPathForDirectoriesInDomains, passthrough=False)
        nstemp = m.replace(NSTemporaryDirectory, passthrough=False)
        nsb = m.replace(NSBundle)
        paths = [m.mock(NSString)] if c.has_paths else []
        appname = "App Name"
        search_path(NSApplicationSupportDirectory, NSUserDomainMask, True) >> paths
        nsb.mainBundle().objectForInfoDictionaryKey_(u"CFBundleExecutable") >> appname
        if c.has_paths:
            path = paths[0]
        else:
            path = nstemp() >> m.mock(NSString)
        asup_path = unicode(os.path.join("/path/to/app_support", appname))
        path.stringByAppendingPathComponent_(appname) >> asup_path
        with m:
            result = Application.app_support_path()
    c = TestConfig(has_paths=False)
    yield test, c
    yield test, c(has_paths=True)

def test_init_syntax_definitions():
    from editxt.syntax import SyntaxFactory
    m = Mocker()
    app = Application()
    sf_class = m.replace(SyntaxFactory, spec=False, passthrough=False)
    app_log = m.replace("editxt.application.log", passthrough=False)
    nsb = m.replace(NSBundle)
    app_support_path = m.method(Application.app_support_path)
    sf = sf_class() >> m.mock(SyntaxFactory)
    rsrc_path = nsb.mainBundle().resourcePath() >> "/resources/syntax"
    asup_path = app_support_path() >> "/app_support/syntax"
    for path in [rsrc_path, asup_path]:
        sf.load_definitions(os.path.join(path, const.SYNTAX_DEFS_DIR))
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
        create_editor = m.method(app.create_editor)
        nsapp = m.mock(NSApplication)
        ud_class = m.replace("editxt.application.NSUserDefaults")
        ud = ud_class.standardUserDefaults() >> m.mock(NSUserDefaults)
        ud.arrayForKey_(const.WINDOW_CONTROLLERS_DEFAULTS_KEY) >> eds_config
        cmd_class = m.replace("editxt.textcommand.TextCommandController")
        dc = m.mock(DocumentController)
        menu = dc.textMenu >> m.mock(NSMenu)
        m.method(app.init_syntax_definitions)()
        tc = cmd_class(menu) >> m.mock(TextCommandController)
        tc.load_commands()
        if eds_config:
            for ed_config in eds_config:
                create_editor(ed_config)
        else:
            create_editor()
        with m:
            app.application_will_finish_launching(nsapp, dc)
            eq_(app.text_commander, tc)
    yield test, []
    yield test, ["project"]
    yield test, ["project 1", "project 2"]

def test_create_editor():
    from editxt.editor import Editor
    def test(args):
        ac = Application()
        m = Mocker()
        ed_class = m.replace("editxt.editor.Editor", passthrough=False)
        wc_class = m.replace("editxt.editor.EditorWindowController", passthrough=False)
        wc = wc_class.alloc() >> m.mock(EditorWindowController)
        wc.initWithWindowNibName_("EditorWindow") >> wc
        ed = ed_class(wc, args[0] if args else None) >> m.mock(Editor)
        wc.editor = ed
        #ed = wc.controller >> m.mock(Editor)
        #wc_class.create_with_serial_data(args[0] if args else None) >> wc
        with m.order():
            ac.editors.append(ed)
            wc.showWindow_(ac)
        with m:
            result = ac.create_editor(*args)
            eq_(result, ed)
    yield test, ("<serial data>",)
    yield test, ()

def test_open_path_dialog():
    from editxt.application import OpenPathController
    def test(c):
        app = Application()
        m = Mocker()
        opc_class = m.replace(OpenPathController, passthrough=False)
        opc = m.mock(OpenPathController)
        m.property(app, "path_opener").value >> (opc if c.exists else None)
        if c.exists:
            app.path_opener.window().makeKeyAndOrderFront_(app)
        else:
            (opc_class.alloc() >> opc).initWithWindowNibName_("OpenPath") >> opc
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
        ac.current_editor = m.method(ac.current_editor)
        if has_current:
            ed = m.mock(Editor)
            proj = (ac.current_editor() >> ed).new_project() >> m.mock(Project)
        else:
            ac.current_editor() >> None
            proj = None
        with m:
            result = ac.new_project()
            eq_(result, proj)
    yield test, True
    yield test, False

def test_open_documents_with_paths():
    def test(c):
        m = Mocker()
        app = Application()
        exists = m.replace("os.path.isfile")
        alog = m.replace("editxt.application.log", passthrough=False)
        ed = m.mock(Editor)
        dv_class = m.replace(TextDocumentView, passthrough=False)
        m.method(app.current_editor)() >> (ed if c.has_editor else None)
        if not c.has_editor:
            m.method(app.create_editor)() >> ed
        focus = None
        for p in c.paths:
            exists(p.path) >> p.exists
            dv = dv_class.create_with_path(p.path) >> m.mock(TextDocumentView)
            focus = ed.add_document_view(dv) >> dv
        if focus is not None:
            ed.current_view = dv
        with m:
            app.open_documents_with_paths([p.path for p in c.paths])
    c = TestConfig(has_editor=True)
    p = lambda p, e: TestConfig(path=p, exists=e)
    yield test, c(has_editor=False, paths=[])
    yield test, c(paths=[])
    yield test, c(paths=[p("abc", True)])
    yield test, c(paths=[p("abc", True), p("def", False)])
    yield test, c(paths=[p("abc", True), p("def", False), p("ghi", True)])


def test_open_error_log():
    import editxt.application as mod
    from editxt.errorlog import ErrorLog
    def test(c):
        m = Mocker()
        ed = m.mock(Editor)
        dv = m.mock(TextDocumentView)
        dv_class = m.replace(TextDocumentView)
        app = Application()
        err = m.property(mod.errlog, "document").value >> m.mock(TextDocument)
        idocs = m.method(app.iter_views_of_document)(err) >> m.mock()
        if c.is_open:
            idocs.next() >> dv
            m.method(app.set_current_document_view)(dv)
        else:
            expect(idocs.next()).throw(StopIteration)
            m.method(app.current_editor)() >> (ed if c.has_editor else None)
            if not c.has_editor:
                m.method(app.create_editor)() >> ed
            dv_class.create_with_document(err) >> dv
            ed.add_document_view(dv)
            ed.current_view = dv
        with m:
            app.open_error_log()
    c = TestConfig(is_open=False)
    yield test, c(is_open=True)
    yield test, c(has_editor=True)
    yield test, c(has_editor=False)

def test_iter_dirty_documents():
    def do_test(editors_template):
        app = Application()
        m = Mocker()
        seen = set()
        dirty_docs = []
        eds = []
        for ecfg in editors_template:
            projects = []
            for pcfg in ecfg:
                proj = m.mock(Project)
                projects.append(proj)
                documents = []
                has_dirty = False
                for doc_id in pcfg:
                    dv = m.mock(TextDocumentView)
                    documents.append(dv)
                    (dv.document.id << doc_id).count(1, 2)
                    if doc_id not in seen:
                        seen.add(doc_id)
                        dirty_docs.append(dv)
                        has_dirty = True
                proj.dirty_documents() >> documents
                if has_dirty:
                    dirty_docs.append(proj)
            ed = m.mock(Editor)
            ed.projects >> projects
            eds.append(ed)
        m.method(app.iter_editors)() >> eds
        with m:
            result = list(app.iter_dirty_documents())
            eq_(result, dirty_docs)
    yield do_test, []
    yield do_test, [""]
    yield do_test, ["0"]
    yield do_test, ["01"]
    yield do_test, ["0", "1"]
    yield do_test, ["0", "0"]
    yield do_test, ["0", "10"]

def test_set_current_document_view():
    ac = Application()
    m = Mocker()
    dv = m.mock(TextDocumentView)
    ac.find_editor_with_document_view = m.method(ac.find_editor_with_document_view)
    ed = ac.find_editor_with_document_view(dv) >> m.mock(Editor)
    ed.current_view = dv
    with m:
        ac.set_current_document_view(dv)

def test_Application_iter_views_of_document():
    def test(config):
        ac = Application()
        m = Mocker()
        doc = m.mock(TextDocument)
        views = []
        total_views = 0
        #ac.editors = eds = []
        eds = []
        for view_count in config:
            ed = m.mock(Editor)
            eds.append(ed)
            total_views += view_count
            vws = [m.mock(TextDocumentView) for i in xrange(view_count)]
            ed.iter_views_of_document(doc) >> vws
            views.extend(vws)
        m.method(ac.iter_editors)() >> eds
        with m:
            result = list(ac.iter_views_of_document(doc))
            eq_(result, views)
            eq_(len(result), total_views)
    yield test, [0]
    yield test, [1]
    yield test, [2, 3, 4]

# def test_find_view_with_document():
#   def test(c):
#       ac = Application()
#       m = Mocker()
#       vw = m.mock(TextDocumentView) if c.has_view else None
#       doc = m.mock(TextDocument)
#       vws = m.method(ac.iter_views_of_document)(doc) >> m.mock()
#       if c.has_view:
#           vws.next() >> vw
#       else:
#           expect(vws.next()).throw(StopIteration)
#       with m:
#           result = ac.find_view_with_document(doc)
#           eq_(result, vw)
#   c = TestConfig()
#   yield test, c(has_view=True)
#   yield test, c(has_view=False)

def test_iter_editors_with_view_of_document():
    def test(c):
        result = None
        ac = Application()
        m = Mocker()
        doc = m.mock(TextDocument)
        found = []
        eds = m.method(ac.iter_editors)() >> []
        for e in c.eds:
            ed = m.mock(Editor)
            eds.append(ed)
            if e.has_view:
                views = [m.mock(TextDocumentView)]
                found.append(ed)
            else:
                views = []
            ed.iter_views_of_document(doc) >> iter(views)
        with m:
            result = list(ac.iter_editors_with_view_of_document(doc))
            eq_(result, found)
            eq_(len(result), c.count)
    ed = lambda has_view=True: TestConfig(has_view=has_view)
    c = TestConfig(eds=[], id=1, count=0)
    yield test, c
    yield test, c(eds=[ed(False)])
    yield test, c(eds=[ed()], count=1)
    yield test, c(eds=[ed(), ed(False)], count=1)
    yield test, c(eds=[ed(), ed(False), ed()], count=2)

def test_find_editor_with_document_view():
    DOC = "the document view we're looking for"
    def test(config):
        """Test argument structure:
        [ # collection of window controllers
            [ # window controller / collection of projects
                ["doc1", "doc2", "doc3", ...], # project / collection of documents
                ...
            ]
            ...
        ]
        """
        result = None
        ac = Application()
        m = Mocker()
        dv = m.mock(TextDocumentView) # this is the view we're looking for
        document = m.mock(TextDocument)
        (dv.document << document).count(0, None)
        ac.iter_editors = m.method(ac.iter_editors)
        eds = ac.iter_editors() >> []
        for ed_projects in config:
            ed = m.mock(Editor)
            eds.append(ed)
            projects = []
            ed.projects >> projects
            found = False
            for project_documents in ed_projects:
                project = m.mock(Project)
                projects.append(project)
                documents = []
                if not found:
                    project.documents() >> documents
                for doc_name in project_documents:
                    if doc_name == DOC:
                        documents.append(dv)
                        result = ed
                        found = True
                    else:
                        documents.append(m.mock(TextDocumentView))
        with m:
            ed = ac.find_editor_with_document_view(dv)
            eq_(ed, result)
    yield test, []
    yield test, [[]]
    yield test, [[[DOC]]]
    yield test, [[["doc"], [DOC]]]
    yield test, [[["doc", DOC, "doc"]]]
    yield test, [[["doc"]]]
    yield test, [[["doc"]], [[DOC]]]

def test_add_editor():
    ac = Application()
    m = Mocker()
    ed = m.mock(Editor)
    assert not ac.editors
    with m:
        ac.add_editor(ed)
    assert ed in ac.editors

def test_iter_editors():
    def test(config, unordered=0):
        """
        config - represents a list of window controllers in on-screen z-order
            with the front-most window controller first. Key:
                None - generic NSWindowController (not EditorWindowController)
                <int> - Editor index in ac.editors
        unordered - (optional, default 0) number of editors in
            ac.editors that are not in the on-screen z-order window
            list.
        """
        ac = Application()
        m = Mocker()
        app_class = m.replace("editxt.application.NSApp")
        app = app_class()
        eds = {}
        unordered_eds = []
        z_windows = []
        for item in config:
            if item is None:
                wc = m.mock(NSWindowController)
            else:
                wc = m.mock(EditorWindowController)
                ed = m.mock(Editor)
                print ed, item
                if item != 7:
                    (wc.editor << ed).count(3)
                    unordered_eds.append(ed)
                else:
                    wc.editor >> ed
                eds[item] = ed
            win = m.mock(NSWindow)
            win.windowController() >> wc
            z_windows.append(win)
        for x in xrange(unordered):
            unordered_eds.append(m.mock(Editor))
        ac.editors = unordered_eds # + [v for k, v in sorted(eds.iteritems())]
        app.orderedWindows() >> z_windows
        sorted_eds = [eds[i] for i in config if i not in (None, 7)]
        sorted_eds.extend(ed for ed in unordered_eds if ed not in sorted_eds)
        with m:
            result = list(ac.iter_editors())
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

def test_current_editor():
    def test(config):
        ac = Application()
        m = Mocker()
        ac.iter_editors = iwc = m.method(ac.iter_editors)
        iwc() >> iter(config)
        with m:
            result = ac.current_editor()
            eq_(result, (config[0] if config else None))
    yield test, []
    yield test, [0]
    yield test, [1, 0]

def test_discard_editor():
    def test(c):
        m = Mocker()
        app = Application()
        ed = m.mock(Editor)
        if c.ed_in_eds:
            app.editors.append(ed)
        def verify():
            assert ed not in app.editors, "ed cannot be in app.editors at this point"
        expect(ed.close()).call(verify)
        with m:
            app.discard_editor(ed)
    c = TestConfig(ed_in_eds=True)
    yield test, c(ed_in_eds=False)
    yield test, c

def test_find_editors_with_project():
    PROJ = "the project"
    def test(eds_config, num_eds):
        eds_found = []
        ac = Application()
        m = Mocker()
        proj = m.mock(Project)
        ac.editors = eds = []
        for i, ed_config in enumerate(eds_config):
            ed = m.mock(Editor)
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
            result = ac.find_editors_with_project(proj)
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
        ac.editors = eds = []
        found_proj = None
        for it in c.eds:
            ed = m.mock(Editor)
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
        ac.editors = eds = []
        found_item = None
        for w in c.eds:
            ed = m.mock(Editor)
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
                        proj.documents() >> docs
                for d in p.docs:
                    doc = m.mock(TextDocumentView)
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

def test_item_changed():
    def test(c):
        m = Mocker()
        app = Application()
        ctype = 0
        item = m.mock(TextDocument if c.item_type == "d" else Project)
        for e in xrange(c.eds):
            ed = m.mock(Editor)
            ed.item_changed(item, ctype)
            app.add_editor(ed)
        with m:
            app.item_changed(item, ctype)
    c = TestConfig(eds=0, item_type="d")
    yield test, c
    yield test, c(eds=1)
    yield test, c(eds=3)
    yield test, c(eds=1, item_type="p")

def test_save_open_projects():
    def test(eds_config, ud_is_none=False):
        ac = Application()
        m = Mocker()
        df_class = m.replace("editxt.application.NSUserDefaults")
        eds = []
        mac = m.patch(ac)
        mac.iter_editors() >> eds
        settings = []
        for i, ed_config in enumerate(eds_config):
            ed = m.mock(Editor)
            eds.append(ed)
            serial = ed.serialize() >> (("<serial %s>" % i)
                if ed_config else None)
            if serial:
                settings.append(serial)
        ud = m.mock(NSUserDefaults)
        if ud_is_none:
            df_class.standardUserDefaults() >> ud
            args = ()
        else:
            args = (ud,)
        ud.setObject_forKey_(settings, const.WINDOW_CONTROLLERS_DEFAULTS_KEY)
        with m:
            ac.save_open_projects(*args)
    yield test, []
    yield test, [1]
    yield test, [0]
    yield test, [1, 1]
    yield test, [1, 0]

def test_load_window_settings():
    def test(ed_count, all_settings, result, add_eds=True):
        ac = Application()
        m = Mocker()
        defaults = m.mock(NSUserDefaults)
        df_class = m.replace("editxt.application.NSUserDefaults")
        eds = [m.mock(Editor) for x in xrange(ed_count)]
        if add_eds:
            df_class.standardUserDefaults() >> defaults
            defaults.arrayForKey_(const.WINDOW_SETTINGS_DEFAULTS_KEY) >> all_settings
            ac.editors = eds
        with m:
            window_settings = ac.load_window_settings(eds[-1])
        eq_(window_settings, result)
    ws = "settings"
    yield test, 1, [ws], {}, False
    yield test, 1, None, {}
    yield test, 1, [], {}
    yield test, 1, [ws], ws
    yield test, 2, [ws], {}
    yield test, 2, [None, ws, None], ws

class MockUserDefaults(object):
    def __init__(self):
        self.synced = False
    def arrayForKey_(self, key):
        return getattr(self, key, None)
    def setObject_forKey_(self, obj, key):
        setattr(self, key, obj)
    def synchronize(self):
        self.synced = True

def test_save_window_settings():
    def do_save_window_settings(ed_count, close_ed, wsets, default_settings, all_settings):
        m = Mocker()
        ac = Application()
        df_class = m.replace("editxt.application.NSUserDefaults")
        defaults = MockUserDefaults()
        defaults.setObject_forKey_(default_settings, const.WINDOW_SETTINGS_DEFAULTS_KEY)
        ac.editors = eds = [m.mock(Editor) for x in xrange(ed_count)]
        if close_ed < 6:
            df_class.standardUserDefaults() >> defaults
            eds[close_ed-1].window_settings >> wsets
        with m:
            ac.save_window_settings(eds[close_ed-1])
            saved = defaults.arrayForKey_(const.WINDOW_SETTINGS_DEFAULTS_KEY)
            eq_(saved, all_settings)
    ws = "settings"
    yield do_save_window_settings, 1, 1, ws, None, [ws]
    yield do_save_window_settings, 2, 2, ws, None, [{}, ws]
    yield do_save_window_settings, 2, 1, ws, None, [{}, ws]
    yield do_save_window_settings, 1, 1, ws, [{}], [ws]
    yield do_save_window_settings, 2, 2, ws, [{}, {}], [{}, ws]
    yield do_save_window_settings, 2, 2, ws, [{}, {}, {}], [{}, ws, {}]
    yield do_save_window_settings, 3, 1, ws, [{}, {}, {}, {}], [{}, {}, ws, {}]
    yield do_save_window_settings, 5, 5, ws, [{}, {}, {}, {}, {}], [{}, {}, {}, {}, ws]
    yield do_save_window_settings, 6, 6, ws, [{}, {}, {}, {}, {}], [{}, {}, {}, {}, {}]

def test_save_window_settings_with_unknown_editor():
    ac = Application()
    m = Mocker()
    df_class = m.replace("editxt.application.NSUserDefaults")
    ed = m.mock(Editor)
    with m:
        ac.save_window_settings(ed)

def test_app_will_terminate():
    def test(ed_config):
        ac = Application()
        m = Mocker()
        df_class = m.replace("editxt.application.NSUserDefaults")
        iter_editors = m.method(ac.iter_editors)
        save_open_projects = m.method(ac.save_open_projects)
        discard_editor = m.method(ac.discard_editor)
        nsapp = m.mock()
        ac.editors = eds = []
        all_settings = []
        for i in ed_config:
            ed = m.mock(Editor)
            eds.append(ed)
            ed.window_settings_loaded >> (i != 2)
            if i != 2:
                settings = "<settings %s>" % i
                all_settings.append(settings)
                ed.window_settings >> settings
        iter_editors(nsapp) >> reversed(eds)
        defaults = df_class.standardUserDefaults() >> MockUserDefaults()
        save_open_projects(defaults)
        with m:
            ac.app_will_terminate(nsapp)
        result = defaults.arrayForKey_(const.WINDOW_SETTINGS_DEFAULTS_KEY)
        eq_(result, all_settings)
        assert defaults.synced
    yield test, []
    yield test, [0]
    yield test, [1, 2, 0]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DocumentController tests

def test_get_document_controller():
    dc = DocumentController.sharedDocumentController()
    assert isinstance(dc, DocumentController)

def test_document_controller_has_app_controller():
    dc = NSDocumentController.sharedDocumentController()
    assert dc.controller is not None

def test_applicationShouldOpenUntitledFile_():
    dc = DocumentController.sharedDocumentController()
    assert not dc.applicationShouldOpenUntitledFile_(None)

def test_applicationWillFinishLaunching_():
    dc = DocumentController.sharedDocumentController()
    m = Mocker()
    app = m.replace("editxt.app", type=Application)
    nsapp = m.mock(NSApplication)
    app.application_will_finish_launching(nsapp, dc)
    with m:
        dc.applicationWillFinishLaunching_(nsapp)

def test_openPath_():
    dc = DocumentController.sharedDocumentController()
    m = Mocker()
    app = m.replace("editxt.app", type=Application)
    app.open_path_dialog()
    with m:
        dc.openPath_(None)

def test_closeCurrentDocument_():
    dc = DocumentController.sharedDocumentController()
    dc.closeCurrentDocument_ #(None) # TODO implement this method

def test_closeCurrentProject_():
    dc = DocumentController.sharedDocumentController()
    dc.closeCurrentProject_ #(None) # TODO implement this method

def test_saveProjectAs_():
    dc = DocumentController.sharedDocumentController()
    dc.saveProjectAs_ #(None) # TODO implement this method

def test_newProject_():
    dc = DocumentController.sharedDocumentController()
    dc.newProject_ #(None) # TODO implement this method

# def test_togglePropertiesPane_():
#     dc = DocumentController.sharedDocumentController()
#     dc.togglePropertiesPane_ #(None) # TODO implement this method

def test_newWindow_():
    dc = DocumentController.sharedDocumentController()
    m = Mocker()
    app = m.replace("editxt.app", type=Application)
    app.create_editor()
    with m:
        dc.newWindow_(None)

def test_openErrorLog_():
    dc = DocumentController.sharedDocumentController()
    m = Mocker()
    app = m.replace("editxt.app", type=Application)
    app.open_error_log()
    with m:
        dc.openErrorLog_(None)

def test_applicationWillTerminate():
    dc = NSDocumentController.sharedDocumentController()
    m = Mocker()
    app = m.replace("editxt.app", type=Application)
    notif = m.mock() # NSApplicationWillTerminateNotification
    nsapp = m.mock(NSApplication)
    app.app_will_terminate(notif.object() >> nsapp)
    with m:
        dc.applicationWillTerminate_(notif)

def test_closeAllDocumentsWithDelegate_didCloseAllSelector_contextInfo_():
    context = 42
    dc = NSDocumentController.sharedDocumentController()
    m = Mocker()
    app = m.replace("editxt.app", type=Application)
    perf_sel = m.replace("editxt.util.perform_selector", passthrough=False)
    dsd_class = m.replace("editxt.application.DocumentSavingDelegate",
        spec=False, passthrough=False)
    docs = m.mock()
    app.iter_dirty_documents() >> docs
    selector = "_docController:shouldTerminate:context:"
    delegate = m.mock()
    def test_callback(callback):
        callback("<result>")
        return True
    should_term = delegate._docController_shouldTerminate_context_
    expect(perf_sel(delegate, selector, dc, "<result>", context)).call(
        lambda *a:should_term(dc, "<result>", context))
    should_term(dc, "<result>", context)
    saver = m.mock(DocumentSavingDelegate)
    dsd_class.alloc() >> saver
    saver.init_callback_(docs, MATCH(test_callback)) >> saver
    saver.save_next_document()
    with m:
        dc.closeAllDocumentsWithDelegate_didCloseAllSelector_contextInfo_(
            delegate, selector, context)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DocumentSavingDelegate tests

def test_DocumentSavingDelegate_init():
    docs = object()
    ctrl = object()
    cbck = object()
    saver = DocumentSavingDelegate.alloc().init_callback_(docs, cbck)
    assert saver is DocumentSavingDelegate.registry[id(saver)]
    assert saver.documents is docs
    assert saver.callback is cbck
    assert saver.should_close

def test_save_next_document():
    def do_test(doctype, doc_window_is_front=True):
        m = Mocker()
        app = m.replace("editxt.app", type=Application)
        docs = m.mock()
        dc = m.mock(DocumentController)
        controller = m.mock()
        callback = m.mock()
        context = 0
        saver = DocumentSavingDelegate.alloc().init_callback_(docs, callback)
        def do_stop_routine():
            expect(docs.next()).throw(StopIteration)
            callback(saver.should_close)
        if doctype is None:
            do_stop_routine()
        else:
            doc = m.mock(doctype)
            docs.next() >> doc
            if doctype is Project:
                doc.save()
                do_stop_routine()
            elif doctype is TextDocumentView:
                app.set_current_document_view(doc)
                win = m.mock()
                doc.window() >> win
                note_ctr = m.replace("editxt.application.NSNotificationCenter")
                note_ctr.defaultCenter().addObserver_selector_name_object_(
                    saver, "windowDidEndSheet:", NSWindowDidEndSheetNotification, win)
                document = doc.document >> m.mock(TextDocument)
                wcs = m.mock(list)
                (document.windowControllers() << wcs).count(1, 2)
                wcs[0].window() >> (win if doc_window_is_front else m.mock())
                if not doc_window_is_front:
                    wcs.sort(key=ANY)
                document.canCloseDocumentWithDelegate_shouldCloseSelector_contextInfo_(
                    saver, "document:shouldClose:contextInfo:", context)
        with m:
            saver.save_next_document()
        if doctype is TextDocumentView:
            assert not saver.document_called_back
            assert not saver.sheet_did_end
        else:
            eq_(saver.documents, None)
            assert id(saver) not in saver.registry
    yield do_test, TextDocumentView
    yield do_test, TextDocumentView, False
    yield do_test, Project
    yield do_test, None

def test_document_shouldClose_contextInfo_():
    assert DocumentSavingDelegate.document_shouldClose_contextInfo_.signature == 'v@:@ci'
    def do_test(should_close, sheet_did_end):
        context = 0
        m = Mocker()
        saver = DocumentSavingDelegate.alloc().init_callback_(m.mock(), m.mock())
        save_next_document = m.method(saver.save_next_document)
        saver.sheet_did_end = sheet_did_end
        if sheet_did_end:
            save_next_document()
        doc = m.mock(TextDocument)
        with m:
            saver.document_shouldClose_contextInfo_(doc, should_close, context)
        assert saver.document_called_back
        if not should_close:
            assert not saver.should_close
            try:
                saver.documents.next()
                raise AssertionError("saver.documents.next() should raise StopIteration")
            except StopIteration:
                pass
        else:
            assert saver.should_close
    yield do_test, True, True
    yield do_test, True, False
    yield do_test, False, True
    yield do_test, False, False

def test_windowDidEndSheet_signature():
    assert DocumentSavingDelegate.windowDidEndSheet_.signature == 'v@:@'

def test_windowDidEndSheet_():
    def do_test(called_back):
        m = Mocker()
        saver = DocumentSavingDelegate.alloc().init_callback_(m.mock(), m.mock())
        saver.document_called_back = called_back
        notif = m.mock(NSNotification)
        win = m.mock(NSWindow)
        notif.object() >> win
        note_ctr = m.replace("editxt.application.NSNotificationCenter")
        note_ctr.defaultCenter().removeObserver_name_object_(
            saver, NSWindowDidEndSheetNotification, win)
        save_next_document = m.method(saver.save_next_document)
        if called_back:
            save_next_document()
        with m:
            saver.windowDidEndSheet_(notif)
            assert saver.sheet_did_end
    yield do_test, True
    yield do_test, False

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# OpenPathController tests
from editxt.application import OpenPathController

def test_OpenPathController_init():
    opc = OpenPathController.alloc().init()

def test_OpenPathController_windowDidLoad():
    m = Mocker()
    opc = OpenPathController.alloc().init()
    tv = m.property(opc, "paths").value >> m.mock(NSTextView)
    tc = tv.textContainer() >> m.mock(NSTextContainer)
    tc.setContainerSize_(NSMakeSize(const.LARGE_NUMBER_FOR_TEXT, const.LARGE_NUMBER_FOR_TEXT))
    tc.setWidthTracksTextView_(False)
    tv.setHorizontallyResizable_(True)
    tv.setAutoresizingMask_(NSViewNotSizable)
    tv.setFieldEditor_(True)
    tv.setFont_(ANY)
    with m:
        opc.windowDidLoad()

def test_OpenPathController_populateWithClipboard():
    # initialize main text field with clipboard content (if its text)
    def test(c):
        m = Mocker()
        opc = OpenPathController.alloc().init()
        paths = m.property(opc, "paths").value >> m.mock(NSTextView)
        with m.order():
            ts = paths.textStorage() >> m.mock(NSTextStorage)
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
        nsapp = m.replace(NSApp, spec=False, passthrough=False)
        opc = OpenPathController.alloc().init()
        tv = m.mock(NSTextView)
        if c.sel == "insertNewline:":
            nsapp().currentEvent().modifierFlags() >> c.mod
            if c.mod & NSCommandKeyMask or c.mod & NSShiftKeyMask:
                tv.insertNewlineIgnoringFieldEditor_(opc)
            else:
                m.method(opc.open_)(opc)
            # check for shift or command (tv.insertTabIgnoringFieldEditor_(self))
            # otherwise open file
        with m:
            eq_(opc.textView_doCommandBySelector_(tv, c.sel), c.res)
    c = TestConfig(sel="insertNewline:", mod=0, res=False)
    yield test, c
    yield test, c(mod=NSCommandKeyMask, res=True)
    yield test, c(mod=NSShiftKeyMask, res=True)
    yield test, c(mod=NSAlternateKeyMask, res=False)
    yield test, c(sel="<otherSelector>")

def test_OpenPathController_open_():
    # TODO accept wildcards in filenames?
    from editxt.textcommand import iterlines
    def test(c):
        m = Mocker()
        app = m.replace("editxt.app", passthrough=False)
        opc = OpenPathController.alloc().init()
        paths = m.property(opc, "paths").value >> m.mock(NSTextView)
        paths.textStorage().string() >> c.text
        app.open_documents_with_paths(c.paths)
        (m.method(opc.window)() >> m.mock(NSWindow)).orderOut_(opc)
        with m:
            opc.open_(None)
    c = TestConfig()
    yield test, c(text="", paths=[])
    yield test, c(text="abc", paths=["abc"])
    yield test, c(text="abc\ndef", paths=["abc", "def"])
    yield test, c(text="abc \n \n\tdef", paths=["abc", "def"])
