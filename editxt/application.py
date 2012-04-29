# -*- coding: utf-8 -*-
# EditXT
# Copyright (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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
import objc
import os
from itertools import chain, repeat, izip, count

import objc
from AppKit import *
from Foundation import *
from PyObjCTools import AppHelper

import editxt
import editxt.constants as const
from editxt.errorlog import errlog
from editxt.util import ContextMap, perform_selector, untested
from editxt.valuetrans import register_value_transformers

#from editxt.test.util import todo_remove # NOTE: this import causes error on start app:
# DistutilsPlatformError: invalid Python installation: unable to open ...
# .../Editxt.app/Contents/Resources/include/python2.5/pyconfig.h (No such file or directory)

log = logging.getLogger("editxt.application")


doc_id_gen = count()

class Application(object):

    def __init__(self):
        self.editors = []
        self.path_opener = None
        self.context = ContextMap()
        register_value_transformers()

    @classmethod
    def app_support_path(cls):
        paths = NSSearchPathForDirectoriesInDomains(
            NSApplicationSupportDirectory, NSUserDomainMask, True)
        path = paths[0] if paths else NSTemporaryDirectory()
        appname = NSBundle.mainBundle().objectForInfoDictionaryKey_(u"CFBundleExecutable")
        path = unicode(path.stringByAppendingPathComponent_(appname))
        return path

    def init_syntax_definitions(self):
        from editxt.syntax import SyntaxFactory
        self.syntax_factory = sf = SyntaxFactory()
        paths = [NSBundle.mainBundle().resourcePath(), self.app_support_path()]
        for path in paths:
            path = os.path.join(path, const.SYNTAX_DEFS_DIR)
            sf.load_definitions(path)
        sf.index_definitions()

    @property
    def syntaxdefs(self):
        return self.syntax_factory.definitions

    def application_will_finish_launching(self, app, doc_ctrl):
        from editxt.textcommand import TextCommandController
        self.init_syntax_definitions()
        self.text_commander = tc = TextCommandController(doc_ctrl.textMenu)
        tc.load_commands()
        defaults = NSUserDefaults.standardUserDefaults()
        settings = defaults.arrayForKey_(const.WINDOW_CONTROLLERS_DEFAULTS_KEY)
        if settings:
            for serials in reversed(settings):
                self.create_editor(serials)
        else:
            self.create_editor()

    def create_editor(self, data=None):
        from editxt.editor import EditorWindowController, Editor
        wc = EditorWindowController.alloc().initWithWindowNibName_("EditorWindow")
        ed = Editor(wc, data)
        wc.editor = ed
        self.editors.append(ed)
        wc.showWindow_(self)
        return ed

    def open_path(self):
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
        for path in paths:
            if os.path.isfile(path):
                view = TextDocumentView.create_with_path(path)
                focus = editor.add_document_view(view)
            else:
                log.info("cannot open path: %s", path)
        if focus is not None:
            editor.current_view = focus

    def open_error_log(self, set_current=True):
        from editxt.document import TextDocumentView
        doc = errlog.document
        try:
            view = self.iter_views_of_document(doc).next()
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
#           return self.iter_views_of_document(doc).next()
#       except StopIteration:
#           return None

    def count_views_of_document(self, doc):
        return len(list(self.iter_views_of_document(doc)))

    def iter_editors_with_view_of_document(self, document):
        for editor in self.iter_editors():
            try:
                editor.iter_views_of_document(document).next()
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
            app = NSApp()
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
            return self.iter_editors().next()
        except StopIteration:
            return None

    def discard_editor(self, editor):
        try:
            self.editors.remove(editor)
        except ValueError:
            pass
        editor.close()

    def save_open_projects(self, defaults=None):
        if defaults is None:
            defaults = NSUserDefaults.standardUserDefaults()
        data = []
        for editor in self.iter_editors():
            serial = editor.serialize()
            if serial: data.append(serial)
        defaults.setObject_forKey_(data, const.WINDOW_CONTROLLERS_DEFAULTS_KEY)

    def load_window_settings(self, editor):
        try:
            index = self.editors.index(editor)
        except ValueError:
            pass
        else:
            defaults = NSUserDefaults.standardUserDefaults()
            settings = defaults.arrayForKey_(const.WINDOW_SETTINGS_DEFAULTS_KEY)
            if settings is not None and len(settings) > index:
                return settings[index]
        return {}

    def _save_window_settings(self, new_settings, defaults):
        END = object()
        new_settings = chain(new_settings, repeat(END))
        old_settings = defaults.arrayForKey_(const.WINDOW_SETTINGS_DEFAULTS_KEY)
        if old_settings is None:
            old_settings = []
        settings = NSMutableArray.alloc().init()
        for old in old_settings:
            new = new_settings.next()
            if new is None or new is END:
                settings.append(old)
            else:
                settings.append(new)
        for item in new_settings:
            if item is END:
                break
            if item is None:
                settings.append({})
            else:
                settings.append(item)
        defaults.setObject_forKey_(settings, const.WINDOW_SETTINGS_DEFAULTS_KEY)

    def save_window_settings(self, editor):
        if editor not in self.editors:
            return #raise Error("unknown window controller")
        index = len(self.editors) - 1
        if index > 4:
            return # do not save settings for more than five windows
        settings = [None for i in xrange(index)]
        settings.append(editor.window_settings)
        defaults = NSUserDefaults.standardUserDefaults()
        self._save_window_settings(settings, defaults)

    def app_will_terminate(self, app):
        settings = (
            editor.window_settings
            for editor in reversed(list(self.iter_editors(app)))
            if editor.window_settings_loaded
        )
        defaults = NSUserDefaults.standardUserDefaults()
        self._save_window_settings(settings, defaults)
        self.save_open_projects(defaults)
        defaults.synchronize()


class DocumentController(NSDocumentController):

    textMenu = objc.ivar("textMenu")

    @property
    def controller(self):
        return editxt.app

    def openPath_(self, sender):
        self.controller.open_path()

    def closeCurrentDocument_(self, sender):
        raise NotImplementedError()

    def closeCurrentProject_(self, sender):
        raise NotImplementedError()

    def saveProjectAs_(self, sender):
        raise NotImplementedError()

    def newProject_(self, sender):
        self.controller.new_project()

    def newWindow_(self, sender):
        self.controller.create_editor()

    def openErrorLog_(self, sender):
        self.controller.open_error_log()

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

class DocumentSavingDelegate(NSObject):
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
            doc_view = self.documents.next()
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
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "windowDidEndSheet:", NSWindowDidEndSheetNotification, window)
        document.canCloseDocumentWithDelegate_shouldCloseSelector_contextInfo_(
            self, "document:shouldClose:contextInfo:", 0)

    @objc.typedSelector('v@:@ci')
    def document_shouldClose_contextInfo_(self, doc, should_close, context):
        self.document_called_back = True
        if not should_close:
            self.should_close = False
            self.documents = iter([]) # cancel iteration
        if self.sheet_did_end:
            self.save_next_document()

    @objc.typedSelector('v@:@')
    def windowDidEndSheet_(self, notification):
        self.sheet_did_end = True
        NSNotificationCenter.defaultCenter().removeObserver_name_object_(
            self, NSWindowDidEndSheetNotification, notification.object())
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

class OpenPathController(NSWindowController):

    # not sure if this is correct
    # hastily added after changing baseclass from NibClassBuilder
    paths = objc.ivar("paths")

    def windowDidLoad(self):
        LNFT = const.LARGE_NUMBER_FOR_TEXT
        tv = self.paths
        tc = tv.textContainer()
        tc.setContainerSize_(NSMakeSize(LNFT, LNFT))
        tc.setWidthTracksTextView_(False)
        tv.setHorizontallyResizable_(True)
        tv.setAutoresizingMask_(NSViewNotSizable)
        tv.setFieldEditor_(True)
        tv.setFont_(NSFont.fontWithName_size_("Monaco", 10.0))

    def populateWithClipboard(self):
        paths = self.paths
        ts = paths.textStorage()
        #ts.deleteCharactersInRange_((0, ts.string().length()))
        paths.setSelectedRange_((0, ts.string().length()))
        paths.pasteAsPlainText_(self)
        paths.setSelectedRange_((0, ts.string().length()))

    def textView_doCommandBySelector_(self, view, selector):
        if selector == "insertNewline:":
            mod = NSApp().currentEvent().modifierFlags()
            if mod & NSCommandKeyMask or mod & NSShiftKeyMask:
                view.insertNewlineIgnoringFieldEditor_(self)
                return True
            else:
                self.open_(self)
        return False

    def open_(self, sender):
        from editxt import app
        from editxt.textcommand import iterlines
        paths = iterlines(self.paths.textStorage().string())
        app.open_documents_with_paths([p.strip() for p in paths if p.strip()])
        self.window().orderOut_(self)

