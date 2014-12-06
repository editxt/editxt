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
from contextlib import contextmanager
from itertools import chain, repeat

import objc
import AppKit as ak
import Foundation as fn

import editxt
import editxt.constants as const
from editxt.commands import iterlines
from editxt.config import Config
from editxt.document import DocumentController
from editxt.errorlog import ErrorLog, LogViewHandler
from editxt.textcommand import CommandHistory, CommandManager
from editxt.util import (ContextMap, perform_selector,
    atomicfile, dump_yaml, load_yaml, WeakProperty)

log = logging.getLogger(__name__)


class Error(Exception): pass

class Application(object):

    def __init__(self, profile=None):
        if profile is None:
            profile = self.default_profile()
        self.profile_path = os.path.expanduser(profile)
        assert os.path.isabs(self.profile_path), \
            'profile path cannot be relative (%s)' % self.profile_path
        self.documents = DocumentController(self)
        self.errlog = ErrorLog(self)
        self.errlog_handler = LogViewHandler(self)
        self.errlog_handler.setLevel(logging.INFO)
        self.errlog_handler.setFormatter(
            logging.Formatter("%(levelname).7s %(name)s - %(message)s"))
        self.panels = []
        with self.logger():
            self._setup_profile = set()
            self.windows = []
            self.path_opener = None
            self.config = Config(
                os.path.join(self.profile_path, const.CONFIG_FILENAME))
            self.context = ContextMap()
            self.syntax_factory = None
            state_dir = os.path.join(self.profile_path, const.STATE_DIR)
            command_history = CommandHistory(state_dir)
            self.text_commander = CommandManager(command_history, app=self)

    @classmethod
    def name(cls):
        return fn.NSBundle.mainBundle().objectForInfoDictionaryKey_("CFBundleName")

    @classmethod
    def resource_path(cls):
        return fn.NSBundle.mainBundle().resourcePath()

    @classmethod
    def default_profile(cls):
        return '~/.' + cls.name().lower()

    @contextmanager
    def logger(self):
        root = logging.getLogger()
        root.addHandler(self.errlog_handler)
        try:
            yield self.errlog
        finally:
            root.removeHandler(self.errlog_handler)

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

    def application_will_finish_launching(self, app, delegate):
        self.init_syntax_definitions()
        self.text_commander.load_commands(delegate.textMenu)
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
        from editxt.window import Window
        window = Window(self, state)
        self.windows.append(window)
        window.show(self)
        return window

    def open_path_dialog(self):
        if self.path_opener is None:
            opc = OpenPathController(self)
            opc.showWindow_(self)
            self.path_opener = opc
        else:
           self.path_opener.window().makeKeyAndOrderFront_(self)
        self.path_opener.populateWithClipboard()

    def new_document(self):
        self.open_documents_with_paths([None])

    def new_project(self):
        window = self.current_window()
        if window is not None:
            return window.new_project()

    def document_with_path(self, path):
        """Get a text document with the given path

        Documents returned by this method have been added to the document
        controllers list of documents.
        """
        from editxt.document import TextDocument
        docs = self.documents
        if path is None:
            # untitled document will get associated with DocumentController on save
            doc = TextDocument(self)
        else:
            if os.path.islink(path):
                path = os.path.realpath(path)
            doc = docs.get_document(path)
        return doc

    def open_documents_with_paths(self, paths):
        window = self.current_window()
        if window is None:
            window = self.create_window()
        return window.open_paths(paths)

    def open_config_file(self):
        items = self.open_documents_with_paths([self.config.path])
        assert len(items) == 1, items
        editor = items[0]
        assert editor.file_path == self.config.path, \
            (editor.file_path, self.config.path)
        if not (os.path.exists(editor.file_path) or editor.document.text):
            editor.document.text = self.config.default_config

    def open_error_log(self, set_current=True):
        """Open the error log document

        This method should only be called while this application's
        ``logger`` context manager is active.
        """
        doc = self.errlog.document
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

    def get_internal_document(self, name):
        if name == "errlog":
            return self.errlog.document
        raise Error("unknown internal document: {}".format(name))

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
                # TODO implement this
                def do_close():
                    editor.close()
                editor.interactive_close(do_close)

    def document_closed(self, document):
        """Remove document from the list of open documents"""
        self.documents.discard(document)

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
        serials = defaults.arrayForKey_(const.WINDOW_CONTROLLERS_DEFAULTS_KEY) or []
        settings = defaults.arrayForKey_(const.WINDOW_SETTINGS_DEFAULTS_KEY) or []
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

    def should_terminate(self, callback):
        """Check if application can terminate

        :param callback: A callback to be used as the return value to signal
        a delayed termination. If this object is returned it will be called with
        a single boolean argument at some point in the future when it is known
        if the application should terminate or not.
        :returns: ``True``, ``False`` or ``callback``. ``True`` means the
        application should terminate immediately. ``False`` means the
        application should not terminate, and ``callback`` means the application
        will perform an extended check to determine if it should terminate
        before calling ``callback`` with either ``True`` or ``False``.
        """
        if next(self.iter_dirty_editors(), None) is not None:
            self.async_interactive_close(self.iter_dirty_editors(), callback)
            return callback
        return True

    @staticmethod
    def async_interactive_close(dirty_editors, callback):
        """Visit each dirty document and prompt for close

        Calls ``callback(False)`` if any unsaved document cancels the
        close operation. Otherwise calls ``callback(True)``.
        """
        class RecursiveCall(Exception): pass

        def continue_closing():
            def _callback(ok_to_close):
                if not ok_to_close:
                    callback(False)
                    return
                if recursive_call:
                    raise RecursiveCall()
                continue_closing()
            recursive_call = True
            for editor in dirty_editors:
                try:
                    editor.should_close(_callback)
                except RecursiveCall:
                    continue
                except Exception:
                    log.exception("termination sequence failed")
                    callback(False)
                    return
                recursive_call = False
                return
            callback(True)

        continue_closing()

    def will_terminate(self):
        self.save_window_states()


class StateLoadFailure(object):

    def __init__(self, path):
        self.path = path

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.path == other.path

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<{} {}>".format(type(self).__name__, self.path)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Open path controller

class OpenPathController(ak.NSWindowController):

    paths = objc.IBOutlet()
    app = WeakProperty()

    def __new__(cls, app):
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

