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
import glob
import logging
import os
from itertools import chain, repeat, count

import objc
import AppKit as ak
import Foundation as fn

import editxt
import editxt.constants as const
from editxt.commands import iterlines
from editxt.config import Config
from editxt.errorlog import errlog
from editxt.textcommand import CommandHistory, TextCommandController
from editxt.util import (ContextMap, perform_selector,
    atomicfile, dump_yaml, load_yaml, WeakProperty)

#from editxt.test.util import todo_remove # NOTE: this import causes error on start app:
# DistutilsPlatformError: invalid Python installation: unable to open ...
# .../Editxt.app/Contents/Resources/include/python2.5/pyconfig.h (No such file or directory)

log = logging.getLogger(__name__)


class Error(Exception): pass

doc_id_gen = count()

class Application(object):

    def __init__(self, profile=None):
        if profile is None:
            profile = self.default_profile()
        self.profile_path = os.path.expanduser(profile)
        assert os.path.isabs(self.profile_path), \
            'profile path cannot be relative (%s)' % self.profile_path
        self._setup_profile = set()
        self.windows = []
        self.path_opener = None
        self.config = Config(
            os.path.join(self.profile_path, const.CONFIG_FILENAME))
        self.context = ContextMap()
        self.syntax_factory = None
        state_dir = os.path.join(self.profile_path, const.STATE_DIR)
        command_history = CommandHistory(state_dir)
        self.text_commander = TextCommandController(command_history)

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
        paths = [(self.resource_path(), False), (self.profile_path, True)]
        for path, log_info in paths:
            path = os.path.join(path, const.SYNTAX_DEFS_DIR)
            sf.load_definitions(path, log_info)
        sf.index_definitions()

    @property
    def syntaxdefs(self):
        return self.syntax_factory.definitions

    def application_will_finish_launching(self, app, doc_ctrl):
        self.init_syntax_definitions()
        self.text_commander.load_commands(doc_ctrl.textMenu)
        states = list(self.iter_saved_window_states())
        if states:
            errors = []
            for state in reversed(states):
                if isinstance(state, StateLoadFailure):
                    errors.append(state)
                else:
                    self.create_window(state)
            if errors:
                self.open_error_log()
        else:
            self.create_window()

    def create_window(self, state=None):
        from editxt.window import WindowController, Window
        wc = WindowController.alloc().initWithWindowNibName_("EditorWindow")
        ed = Window(self, wc, state)
        wc.window_ = ed
        self.windows.append(ed)
        wc.showWindow_(self)
        return ed

    def open_path_dialog(self):
        if self.path_opener is None:
            opc = OpenPathController.create(self)
            opc.showWindow_(self)
            self.path_opener = opc
        else:
           self.path_opener.window().makeKeyAndOrderFront_(self)
        self.path_opener.populateWithClipboard()

    def new_project(self):
        window = self.current_window()
        if window is not None:
            return window.new_project()

    def document_with_path(self, path):
        """Get a document with the given path

        Documents returned by this method have been added to the document
        controllers list of documents.
        """
        from editxt.document import TextDocument
        dc = ak.NSDocumentController.sharedDocumentController()
        if path is None:
            doc = None
        else:
            if os.path.islink(path):
                path = os.path.realpath(path)
            url = fn.NSURL.fileURLWithPath_(path)
            doc = dc.documentForURL_(url)
        if doc is None:
            if path is not None and os.path.exists(path):
                doctype, err = dc.typeForContentsOfURL_error_(url, None)
                doc, err = dc.makeDocumentWithContentsOfURL_ofType_error_(
                    url, doctype, None)
                if err is not None:
                    raise Error(err.localizedFailureReason())
                if doc is None:
                    raise Error("could not open document: %s" % path)
                dc.addDocument_(doc)
            else:
                doc, err = dc.makeUntitledDocumentOfType_error_(
                    const.TEXT_DOCUMENT, None)
                if err is not None:
                    raise RuntimeError(err)
                if path is not None:
                    doc.setFileURL_(url)

        # TODO figure out how to move this into TextDocument.init
        doc.app = self
        doc.indent_mode = self.config["indent.mode"]
        doc.indent_size = self.config["indent.size"] # should come from syntax definition
        doc.newline_mode = self.config["newline_mode"]
        doc.highlight_selected_text = self.config["highlight_selected_text.enabled"]
        doc.reset_text_attributes(doc.indent_size)

        return doc

    def open_documents_with_paths(self, paths):
        window = self.current_window()
        if window is None:
            window = self.create_window()
        items = window.iter_dropped_paths(paths)
        return window.insert_items(items)

    def open_config_file(self):
        items = self.open_documents_with_paths([self.config.path])
        assert len(items) == 1, items
        document = items[0]
        assert document.file_path == self.config.path, \
            (document.file_path, self.config.path)
        if not (os.path.exists(document.file_path) or document.text):
            document.text = self.config.default_config

    def open_error_log(self, set_current=True):
        doc = errlog.document
        try:
            editor = next(self.iter_editors_of_document(doc))
        except StopIteration:
            window = self.current_window()
            if window is None:
                window = self.create_window()
            window.insert_items([doc])
        else:
            if set_current:
                self.set_current_editor(editor)

    def iter_dirty_editors(self):
        seen = set()
        for window in self.iter_windows():
            for proj in window.projects:
                dirty = False
                for editor in proj.dirty_editors():
                    if editor.document.id not in seen:
                        seen.add(editor.document.id)
                        yield editor
                        dirty = True
                if dirty:
                    yield proj

    def set_current_editor(self, editor):
        window = self.find_window_with_editor(editor)
        window.current_editor = editor

    def close_current_document(self):
        window = self.current_window()
        if window is not None:
            editor = window.current_editor
            if editor is not None:
                editor.perform_close()

    def iter_editors_of_document(self, doc):
        for window in self.iter_windows():
            for editor in window.iter_editors_of_document(doc):
                yield editor

    def iter_windows_with_editor_of_document(self, document):
        for window in self.iter_windows():
            try:
                next(window.iter_editors_of_document(document))
            except StopIteration:
                pass
            else:
                yield window

    def find_window_with_editor(self, editor):
        for window in self.iter_windows():
            for proj in window.projects:
                for ed in proj.editors:
                    if ed is editor:
                        return window
        return None

    def find_windows_with_project(self, project):
        return [ed for ed in self.windows if project in ed.projects]

    def find_project_with_path(self, path):
        for ed in self.windows:
            proj = ed.find_project_with_path(path)
            if proj is not None:
                return proj
        return None

    def find_item_with_id(self, ident):
        # HACK slow implementation, violates encapsulation
        for window in self.windows:
            for proj in window.projects:
                if proj.id == ident:
                    return proj
                for doc in proj.editors:
                    if doc.id == ident:
                        return doc
        return None

    def item_changed(self, item, change_type=None):
        for window in self.windows:
            window.item_changed(item, change_type)

    def iter_windows(self, app=None):
        """Iterate over windows in on-screen z-order starting with the
        front-most window"""
        from editxt.window import WindowController
        if app is None:
            app = ak.NSApp()
        z_ordered_eds = set()
        for win in app.orderedWindows():
            wc = win.windowController()
            if isinstance(wc, WindowController) and wc.window_ in self.windows:
                z_ordered_eds.add(wc.window_)
                yield wc.window_
        for ed in self.windows:
            if ed not in z_ordered_eds:
                yield ed

    def add_window(self, window):
        self.windows.append(window)

    def current_window(self):
        try:
            return next(self.iter_windows())
        except StopIteration:
            return None

    def discard_window(self, window):
        try:
            self.windows.remove(window)
        except ValueError:
            pass
        window.close()

    def setup_profile(self, windows=False):
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
        if windows and 'editors' not in self._setup_profile:
            state_path = os.path.join(self.profile_path, const.STATE_DIR)
            if not os.path.exists(state_path):
                try:
                    os.mkdir(state_path)
                except OSError:
                    log.error('cannot create %s', state_path, exc_info=True)
                    return False
            self._setup_profile.add('editors')
        return True

    def _legacy_window_states(self):
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

    def iter_saved_window_states(self):
        """Yield saved window states"""
        state_path = os.path.join(self.profile_path, const.STATE_DIR)
        if not os.path.exists(state_path):
            if self.profile_path == os.path.expanduser(self.default_profile()):
                # TODO remove once all users have upraded
                for state in self._legacy_window_states():
                    yield state
            return
        state_glob = os.path.join(state_path, const.EDITOR_STATE.format('*'))
        for path in sorted(glob.glob(state_glob)):
            try:
                with open(path) as f:
                    yield load_yaml(f)
            except Exception:
                log.error('cannot load %s', path, exc_info=True)
                yield StateLoadFailure(path)

    def save_window_state(self, window, ident=None):
        """Save a single window's state

        :param window: The window with state to be saved.
        :param ident: The identifier to use when saving window state. It
            is assumed that the profile has been setup when this
            argument is provided; ``window.id`` will be used when
            not provided.
        :returns: The name of the state file.
        """
        if ident is None:
            raise NotImplementedError
            ident = window.id
        self.setup_profile(windows=True)
        state_name = const.EDITOR_STATE.format(ident)
        state_file = os.path.join(
            self.profile_path, const.STATE_DIR, state_name)
        state = window.state
        try:
            with atomicfile(state_file, encoding="utf-8") as fh:
                dump_yaml(state, fh)
        except Exception:
            log.error('cannot write %s\n%s\n', state_file, state, exc_info=True)
        return state_name

    def save_window_states(self):
        """Save all windows' states"""
        state_path = os.path.join(self.profile_path, const.STATE_DIR)
        old_glob = os.path.join(state_path, const.EDITOR_STATE.format('*'))
        old = {os.path.basename(name) for name in glob.glob(old_glob)}
        for i, window in enumerate(self.iter_windows()):
            state_name = self.save_window_state(window, i)
            old.discard(state_name)
        for name in old:
            state_file = os.path.join(state_path, name)
            try:
                os.remove(state_file)
            except Exception:
                log.error('cannot remove %s', state_file, exc_info=True)

    def app_will_terminate(self, app):
        self.save_window_states()


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
        self.controller.create_window()

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
            self.controller.iter_dirty_editors(), callback)
        saver.save_next_document()

    def applicationWillTerminate_(self, notification):
        self.controller.app_will_terminate(notification.object())


class StateLoadFailure(object):

    def __init__(self, path):
        self.path = path

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.path == other.path

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<{} {}>".format(type(self).__name__, self.path)


# This may be removed if the app does not crash when the save panel is
# cancelled after quitting with unsaved documents.
# See also:
# [PyObjC-svn] r2350 - in trunk/pyobjc/pyobjc-framework-Cocoa: . Lib/AppKit PyObjCTest
#     http://permalink.gmane.org/gmane.comp.python.pyobjc.cvs/2763
# Re: Crash when closing all documents
#     http://permalink.gmane.org/gmane.comp.python.pyobjc.devel/5563
objc.registerMetaDataForSelector(b'NSDocumentController',
    b'_documentController:shouldTerminate:context:',
    {'arguments': {4: {'type': b'^v'}}})

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Document saving helper

class DocumentSavingDelegate(fn.NSObject):
    """Prompt to save each document by asking if it can be closed

    Any Projects will be saved by calling saveIfNecessary() rather than
    being asked to close.
    """

    registry = {}

    def init_callback_(self, editors, callback):
        self = super(DocumentSavingDelegate, self).init()
        self.registry[id(self)] = self # prevent garbage collection
        self.editors = editors
        self.callback = callback
        self.should_close = True
        return self

    def save_next_document(self):
        try:
            editor = next(self.editors)
        except StopIteration:
            self.editors = None # release references to editors (if there are any)
            self.callback(self.should_close)
            self.registry.pop(id(self))
            return

        from editxt.project import Project
        if isinstance(editor, Project):
            editor.save()
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
        editor.project.window.current_editor = editor # set current editor so we get a sheet
        window = editor.window()
        document = editor.document
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
            self.editors = iter([]) # cancel iteration
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
    app = WeakProperty()

    @classmethod
    def create(cls, app):
        opener = cls.alloc().initWithWindowNibName_("OpenPath")
        opener.app = app
        return opener

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
        paths = iterlines(self.paths.textStorage().string())
        self.app.open_documents_with_paths(
            p.strip() for p in paths if p.strip())
        self.window().orderOut_(self)

