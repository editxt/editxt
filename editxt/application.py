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
import glob
import logging
import objc
import os
from itertools import chain, repeat, count

import objc
import AppKit as ak
import Foundation as fn
from PyObjCTools import AppHelper

import editxt
import editxt.constants as const
from editxt.commands import iterlines
from editxt.config import Config
from editxt.errorlog import errlog
from editxt.textcommand import CommandHistory, TextCommandController
from editxt.util import ContextMap, perform_selector, dump_yaml, load_yaml
from editxt.valuetrans import register_value_transformers

#from editxt.test.util import todo_remove # NOTE: this import causes error on start app:
# DistutilsPlatformError: invalid Python installation: unable to open ...
# .../Editxt.app/Contents/Resources/include/python2.5/pyconfig.h (No such file or directory)

log = logging.getLogger(__name__)


doc_id_gen = count()

class Application(object):

    def __init__(self, profile=None):
        if profile is None:
            profile = self.default_profile()
        self.profile_path = os.path.expanduser(profile)
        assert os.path.isabs(self.profile_path), \
            'profile path cannot be relative (%s)' % self.profile_path
        self._setup_profile = set()
        self.editors = []
        self.path_opener = None
        self.config = Config(self.profile_path)
        self.context = ContextMap()
        self.syntax_factory = None
        state_dir = os.path.join(self.profile_path, const.STATE_DIR)
        command_history = CommandHistory(state_dir)
        self.text_commander = TextCommandController(command_history)
        register_value_transformers()

    @classmethod
    def name(cls):
        return fn.NSBundle.mainBundle().objectForInfoDictionaryKey_("CFBundleName")

    @classmethod
    def resource_path(cls):
        return fn.NSBundle.mainBundle().resourcePath()

    @classmethod
    def default_profile(cls):
        return '~/.' + cls.name().lower()

    def init_syntax_definitions(self):
        from editxt.syntax import SyntaxFactory
        self.syntax_factory = sf = SyntaxFactory()
        paths = [self.resource_path(), self.profile_path]
        for path in paths:
            path = os.path.join(path, const.SYNTAX_DEFS_DIR)
            sf.load_definitions(path)
        sf.index_definitions()

    @property
    def syntaxdefs(self):
        return self.syntax_factory.definitions

    def application_will_finish_launching(self, app, doc_ctrl):
        self.init_syntax_definitions()
        self.text_commander.load_commands(doc_ctrl.textMenu)
        states = list(self.iter_saved_editor_states())
        if states:
            for state in reversed(states):
                self.create_editor(state)
        else:
            self.create_editor()

    def create_editor(self, state=None):
        from editxt.editor import EditorWindowController, Editor
        wc = EditorWindowController.alloc().initWithWindowNibName_("EditorWindow")
        ed = Editor(self, wc, state)
        wc.editor = ed
        self.editors.append(ed)
        wc.showWindow_(self)
        return ed

    def open_path_dialog(self):
        if self.path_opener is None:
            opc = OpenPathController.alloc().initWithWindowNibName_("OpenPath")
            opc.showWindow_(self)
            self.path_opener = opc
        else:
           self.path_opener.window().makeKeyAndOrderFront_(self)
        self.path_opener.populateWithClipboard()

    def new_project(self):
        editor = self.current_editor()
        if editor is not None:
            return editor.new_project()

    def open_documents_with_paths(self, paths):
        from editxt.document import TextDocumentView
        editor = self.current_editor()
        if editor is None:
            editor = self.create_editor()
        focus = None
        views = []
        for path in paths:
            if os.path.isfile(path) or not os.path.exists(path):
                view = TextDocumentView.create_with_path(path)
                focus = editor.add_document_view(view)
                views.append(view)
            else:
                log.info("cannot open path: %s", path)
        if focus is not None:
            editor.current_view = focus
        return views

    def open_config_file(self):
        views = self.open_documents_with_paths([self.config.path])
        if not os.path.exists(self.config.path):
            assert len(views) == 1, views
            views[0].document.text = self.config.default_config

    def open_error_log(self, set_current=True):
        from editxt.document import TextDocumentView
        doc = errlog.document
        try:
            view = next(self.iter_views_of_document(doc))
        except StopIteration:
            editor = self.current_editor()
            if editor is None:
                editor = self.create_editor()
            view = TextDocumentView.create_with_document(doc)
            editor.add_document_view(view)
            if set_current:
                editor.current_view = view
        else:
            if set_current:
                self.set_current_document_view(view)

    def iter_dirty_documents(self):
        seen = set()
        for editor in self.iter_editors():
            for proj in editor.projects:
                dirty = False
                for view in proj.dirty_documents():
                    if view.document.id not in seen:
                        seen.add(view.document.id)
                        yield view
                        dirty = True
                if dirty:
                    yield proj

    def set_current_document_view(self, doc_view):
        ed = self.find_editor_with_document_view(doc_view)
        ed.current_view = doc_view

    def close_current_document(self):
        editor = self.current_editor()
        if editor is not None:
            view = editor.current_view
            if view is not None:
                view.perform_close(editor)

    def iter_views_of_document(self, doc):
        for editor in self.iter_editors():
            for view in editor.iter_views_of_document(doc):
                yield view

#   def find_view_with_document(self, doc):
#       """find a view of the given document
# 
#       Returns a view in the topmost window with the given document, or None
#       if there are no views of this document.
#       """
#       try:
#           return next(self.iter_views_of_document(doc))
#       except StopIteration:
#           return None

    def count_views_of_document(self, doc):
        return len(list(self.iter_views_of_document(doc)))

    def iter_editors_with_view_of_document(self, document):
        for editor in self.iter_editors():
            try:
                next(editor.iter_views_of_document(document))
            except StopIteration:
                pass
            else:
                yield editor

    def find_editor_with_document_view(self, doc_view):
        for editor in self.iter_editors():
            for proj in editor.projects:
                for dv in proj.documents():
                    if dv is doc_view:
                        return editor
        return None

    def find_editors_with_project(self, project):
        return [ed for ed in self.editors if project in ed.projects]

    def find_project_with_path(self, path):
        for ed in self.editors:
            proj = ed.find_project_with_path(path)
            if proj is not None:
                return proj
        return None

    def find_item_with_id(self, ident):
        # HACK slow implementation, violates encapsulation
        for editor in self.editors:
            for proj in editor.projects:
                if proj.id == ident:
                    return proj
                for doc in proj.documents():
                    if doc.id == ident:
                        return doc
        return None

    def item_changed(self, item, change_type=None):
        for editor in self.editors:
            editor.item_changed(item, change_type)

    def iter_editors(self, app=None):
        """Iterate over editors in on-screen z-order starting with the
        front-most editor window"""
        from editxt.editor import EditorWindowController
        if app is None:
            app = ak.NSApp()
        z_ordered_eds = set()
        for win in app.orderedWindows():
            wc = win.windowController()
            if isinstance(wc, EditorWindowController) and wc.editor in self.editors:
                z_ordered_eds.add(wc.editor)
                yield wc.editor
        for ed in self.editors:
            if ed not in z_ordered_eds:
                yield ed

    def add_editor(self, editor):
        self.editors.append(editor)

    def current_editor(self):
        try:
            return next(self.iter_editors())
        except StopIteration:
            return None

    def discard_editor(self, editor):
        try:
            self.editors.remove(editor)
        except ValueError:
            pass
        editor.close()

    def setup_profile(self, editors=False):
        """Ensure that profile dir exists

        This will create the profile directory if it does not exist.

        :returns: True on success, otherwise False.
        """
        if not ('.' in self._setup_profile or os.path.isdir(self.profile_path)):
            try:
                os.mkdir(self.profile_path)
            except OSError:
                log.error('cannot create %s', self.profile_path, exc_info=True)
                return False
            self._setup_profile.add('.')
        if editors and 'editors' not in self._setup_profile:
            state_path = os.path.join(self.profile_path, const.STATE_DIR)
            if not os.path.exists(state_path):
                try:
                    os.mkdir(state_path)
                except OSError:
                    log.error('cannot create %s', state_path, exc_info=True)
                    return False
            self._setup_profile.add('editors')
        return True

    def _legacy_editor_states(self):
        # TODO remove once all users have upraded to new state persistence
        def pythonify(value):
            if isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, (dict, fn.NSDictionary)):
                return {k: pythonify(v) for k, v in value.items()}
            if isinstance(value, (list, fn.NSArray)):
                return [pythonify(v) for v in value]
            raise ValueError('unknown value type: {} {}'
                .format(type(value), repr(value)))
        defaults = fn.NSUserDefaults.standardUserDefaults()
        serials = defaults.arrayForKey_(const.WINDOW_CONTROLLERS_DEFAULTS_KEY)
        settings = defaults.arrayForKey_(const.WINDOW_SETTINGS_DEFAULTS_KEY)
        serials = list(reversed(serials))
        for serial, setting in zip(serials, chain(settings, repeat(None))):
            try:
                state = dict(serial)
                if setting is not None:
                    state['window_settings'] = setting
                yield pythonify(state)
            except Exception:
                log.warn('cannot load legacy state: %r', serial, exc_info=True)

    def iter_saved_editor_states(self):
        """Yield saved editor states"""
        state_path = os.path.join(self.profile_path, const.STATE_DIR)
        if not os.path.exists(state_path):
            if self.profile_path == os.path.expanduser(self.default_profile()):
                # TODO remove once all users have upraded
                for state in self._legacy_editor_states():
                    yield state
            return
        state_glob = os.path.join(state_path, const.EDITOR_STATE.format('*'))
        for path in sorted(glob.glob(state_glob)):
            try:
                with open(path) as f:
                    yield load_yaml(f)
            except Exception:
                log.error('cannot load %s', path, exc_info=True)

    def save_editor_state(self, editor, ident=None):
        """Save a single editor's state

        :param editor: The editor with state to be saved.
        :param ident: The identifier to use when saving editor state. It
            is assumed that the profile has been setup when this
            argument is provided; ``editor.id`` will be used when
            not provided.
        :returns: The name of the state file.
        """
        if ident is None:
            raise NotImplementedError
            ident = editor.id
        self.setup_profile(editors=True)
        state_name = const.EDITOR_STATE.format(ident)
        state_file = os.path.join(
            self.profile_path, const.STATE_DIR, state_name)
        state = editor.state
        try:
            with open(state_file, 'w', encoding="utf-8") as fh:
                dump_yaml(state, fh)
        except Exception:
            log.error('cannot write %s\n%s\n',
                state_file, dump_yaml(state), exc_info=True)
        return state_name

    def save_editor_states(self):
        """Save all editors' states"""
        state_path = os.path.join(self.profile_path, const.STATE_DIR)
        old_glob = os.path.join(state_path, const.EDITOR_STATE.format('*'))
        old = {os.path.basename(name) for name in glob.glob(old_glob)}
        for i, editor in enumerate(self.iter_editors()):
            state_name = self.save_editor_state(editor, i)
            old.discard(state_name)
        for name in old:
            state_file = os.path.join(state_path, name)
            try:
                os.remove(state_file)
            except Exception:
                log.error('cannot remove %s', state_file, exc_info=True)

    def app_will_terminate(self, app):
        self.save_editor_states()


class DocumentController(ak.NSDocumentController):

    textMenu = objc.IBOutlet()
    textEditCommandsMenu = objc.IBOutlet()

    @property
    def controller(self):
        return editxt.app

    def openPath_(self, sender):
        self.controller.open_path_dialog()

    def closeCurrentDocument_(self, sender):
        self.controller.close_current_document()

    def closeCurrentProject_(self, sender):
        raise NotImplementedError()

    def saveProjectAs_(self, sender):
        #raise NotImplementedError()
        import gc
        from collections import defaultdict
        from datetime import datetime
        def rep(obj, count):
            return '%-30s %10s    %s' % (obj.__name__, count, obj)
        objs = defaultdict(lambda:0)
        for obj in gc.get_objects():
            objs[type(obj)] += 1
        ones = sum(1 for o in objs.items() if o[1] == 1)
        objs = (o for o in objs.items() if o[1] > 1)
        objs = sorted(objs, key=lambda v:(-v[1], v[0].__name__))
        names = (rep(*o) for o in objs)
        log.info('%s gc objects:\n%s\nsingletons                     %10s',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '\n'.join(names), ones)

    def newProject_(self, sender):
        self.controller.new_project()

    def newWindow_(self, sender):
        self.controller.create_editor()

    def openConfigFile_(self, sender):
        self.controller.open_config_file()

    def openErrorLog_(self, sender):
        self.controller.open_error_log()

    def application_openFiles_(self, app, filenames):
        self.controller.open_documents_with_paths(filenames)
        app.replyToOpenOrPrint_(0) # success

    def applicationShouldOpenUntitledFile_(self, app):
        return False

    def applicationWillFinishLaunching_(self, app):
        self.controller.application_will_finish_launching(app, self)

    def closeAllDocumentsWithDelegate_didCloseAllSelector_contextInfo_(
        self, delegate, selector, context):
        #perform_selector(delegate, selector, self, 1, context)
        def callback(result):
            #log.debug("%s.%s(%s, %s, %s)", delegate, selector, self, result, context)
            perform_selector(delegate, selector, self, result, context)
        saver = DocumentSavingDelegate.alloc().init_callback_(
            self.controller.iter_dirty_documents(), callback)
        saver.save_next_document()

    def applicationWillTerminate_(self, notification):
        self.controller.app_will_terminate(notification.object())

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Document saving helper

class DocumentSavingDelegate(fn.NSObject):
    """Prompt to save each document by asking if it can be closed

    Any Projects will be saved by calling saveIfNecessary() rather than
    being asked to close.
    """

    registry = {}

    def init_callback_(self, docs, callback):
        self = super(DocumentSavingDelegate, self).init()
        self.registry[id(self)] = self # prevent garbage collection
        self.documents = docs
        self.callback = callback
        self.should_close = True
        return self

    def save_next_document(self):
        try:
            doc_view = next(self.documents)
        except StopIteration:
            self.documents = None # release references to documents (if there are any)
            self.callback(self.should_close)
            self.registry.pop(id(self))
            return

        from editxt.project import Project
        if isinstance(doc_view, Project):
            doc_view.save()
            self.save_next_document()
            return

        # HACK ?? these flags control when save_next_document is called. If
        # the document is not saved then document_shouldClose_contextInfo_
        # is called before windowDidEndSheet_, in which case windowDidEndSheet_
        # must call save_next_document. But if the document is saved then
        # windowDidEndSheet_ gets called before document_shouldClose_contextInfo_,
        # in which case the latter must call save_next_document.
        self.document_called_back = False
        self.sheet_did_end = False
        editxt.app.set_current_document_view(doc_view) # set current view so we get a sheet
        window = doc_view.window()
        document = doc_view.document
        if document.windowControllers()[0].window() != window:
            # HACK rearrange document window controllers to make the sheet appear on our window
            document.windowControllers().sort(key=lambda wc: -abs(wc.window() is window))
        fn.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "windowDidEndSheet:", ak.NSWindowDidEndSheetNotification, window)
        document.canCloseDocumentWithDelegate_shouldCloseSelector_contextInfo_(
            self, "document:shouldClose:contextInfo:", 0)

    @objc.typedSelector(b'v@:@ci')
    def document_shouldClose_contextInfo_(self, doc, should_close, context):
        self.document_called_back = True
        if not should_close:
            self.should_close = False
            self.documents = iter([]) # cancel iteration
        if self.sheet_did_end:
            self.save_next_document()

    @objc.typedSelector(b'v@:@')
    def windowDidEndSheet_(self, notification):
        self.sheet_did_end = True
        fn.NSNotificationCenter.defaultCenter().removeObserver_name_object_(
            self, ak.NSWindowDidEndSheetNotification, notification.object())
        if self.document_called_back:
            self.save_next_document()


# class DocumentCloser(object):
#     """Helper class to be used with DocumentSavingDelegate to perform
#     document.close() after the document is saved.
#
#     Note: this only works when closing a single document.
#     """
#
#     def __init__(self, doc):
#         self.doc = doc
#
#     def controller_closedDocument_(self, controller, shouldClose):
#         if shouldClose:
#             self.doc.close()
#

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Open path controller

class OpenPathController(ak.NSWindowController):

    paths = objc.IBOutlet()

    def windowDidLoad(self):
        LNFT = const.LARGE_NUMBER_FOR_TEXT
        tv = self.paths
        tc = tv.textContainer()
        tc.setContainerSize_(fn.NSMakeSize(LNFT, LNFT))
        tc.setWidthTracksTextView_(False)
        tv.setHorizontallyResizable_(True)
        tv.setAutoresizingMask_(ak.NSViewNotSizable)
        tv.setFieldEditor_(True)
        tv.setFont_(ak.NSFont.fontWithName_size_("Monaco", 10.0))

    def populateWithClipboard(self):
        paths = self.paths
        ts = paths.textStorage()
        #ts.deleteCharactersInRange_((0, ts.string().length()))
        paths.setSelectedRange_((0, ts.string().length()))
        paths.pasteAsPlainText_(self)
        paths.setSelectedRange_((0, ts.string().length()))

    def textView_doCommandBySelector_(self, view, selector):
        if selector == "insertNewline:":
            mod = ak.NSApp().currentEvent().modifierFlags()
            if mod & ak.NSCommandKeyMask or mod & ak.NSShiftKeyMask:
                view.insertNewlineIgnoringFieldEditor_(self)
                return True
            else:
                self.open_(self)
        return False

    def open_(self, sender):
        from editxt import app
        paths = iterlines(self.paths.textStorage().string())
        app.open_documents_with_paths([p.strip() for p in paths if p.strip()])
        self.window().orderOut_(self)

