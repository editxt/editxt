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
import objc
import os
from collections import defaultdict

import objc
import AppKit as ak
import Foundation as fn
from PyObjCTools import AppHelper

import editxt.constants as const
from editxt.document import Editor, TextDocument
from editxt.platform.kvo import KVOList
from editxt.platform.views import BUTTON_STATE_HOVER, BUTTON_STATE_NORMAL, BUTTON_STATE_PRESSED
from editxt.project import Project
from editxt.textcommand import CommandBar
from editxt.util import (RecentItemStack, load_image, perform_selector,
    untested, message, representedObject, user_path, WeakProperty)

log = logging.getLogger(__name__)

class Error(Exception): pass

BUTTON_STATE_SELECTED = object()


class Window(object):

    supported_drag_types = [const.DOC_ID_LIST_PBOARD_TYPE, ak.NSFilenamesPboardType]
    app = WeakProperty()

    def __init__(self, app, window_controller, state=None):
        self.app = app
        self._current_editor = None
        self.wc = window_controller
        self.state = state
        self.command = CommandBar(self, app.text_commander)
        self.projects = KVOList()
        self.recent = self._suspended_recent = RecentItemStack(20)
        self.window_settings_loaded = False

    def window_did_load(self):
        wc = self.wc
        wc.setShouldCloseDocument_(False)
        wc.docsView.setRefusesFirstResponder_(True)
        wc.plusButton.setRefusesFirstResponder_(True)
        wc.plusButton.setImage_(load_image(const.PLUS_BUTTON_IMAGE))
        wc.propsViewButton.setRefusesFirstResponder_(True)
        wc.propsViewButton.setImage_(load_image(const.PROPS_DOWN_BUTTON_IMAGE))
        wc.propsViewButton.setAlternateImage_(load_image(const.PROPS_UP_BUTTON_IMAGE))

        fn.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            wc, "windowDidBecomeKey:", ak.NSWindowDidBecomeKeyNotification, wc.window())
        assert hasattr(WindowController, "windowDidBecomeKey_")

        wc.cleanImages = {
            BUTTON_STATE_HOVER: load_image(const.CLOSE_CLEAN_HOVER),
            BUTTON_STATE_NORMAL: load_image(const.CLOSE_CLEAN_NORMAL),
            BUTTON_STATE_PRESSED: load_image(const.CLOSE_CLEAN_PRESSED),
            BUTTON_STATE_SELECTED: load_image(const.CLOSE_CLEAN_SELECTED),
        }
        wc.dirtyImages = {
            BUTTON_STATE_HOVER: load_image(const.CLOSE_DIRTY_HOVER),
            BUTTON_STATE_NORMAL: load_image(const.CLOSE_DIRTY_NORMAL),
            BUTTON_STATE_PRESSED: load_image(const.CLOSE_DIRTY_PRESSED),
            BUTTON_STATE_SELECTED: load_image(const.CLOSE_DIRTY_SELECTED),
        }

        wc.docsView.registerForDraggedTypes_(self.supported_drag_types)

        self._setstate(self._state)
        self._state = None

        if not self.projects:
            self.new_project()

    def _setstate(self, state):
        if state:
            for serial in state.get("project_serials", []):
                proj = Project(self, serial=serial)
                self.projects.append(proj)
            for proj_index, doc_index in state.get("recent_items", []):
                if proj_index < len(self.projects):
                    proj = self.projects[proj_index]
                    if doc_index == "<project>":
                        self.recent.push(proj.id)
                    elif doc_index < len(proj.editors):
                        doc = proj.editors[doc_index]
                        self.recent.push(doc.id)
            if 'window_settings' in state:
                self.window_settings = state['window_settings']
            self.discard_and_focus_recent(None)

    def __getstate__(self):
        if self._state is not None:
            return self._state
        def iter_settings():
            indexes = {}
            serials = []
            for i, project in enumerate(self.projects):
                serial = project.serialize()
                if serial:
                    serials.append(serial)
                indexes[project.id] = [i, "<project>"]
                offset = 0
                for j, doc in enumerate(project.editors):
                    if doc.file_path and os.path.exists(doc.file_path):
                        indexes[doc.id] = [i, j - offset]
                    else:
                        offset += 1
            yield "project_serials", serials
            rits = []
            for ident in self.recent:
                pair = indexes.get(ident)
                if pair is not None:
                    rits.append(pair)
            yield "recent_items", rits
            yield "window_settings", self.window_settings
        return {key: val for key, val in iter_settings() if val}

    def __setstate__(self, state):
        assert not hasattr(self, '_state'), 'can only be called once'
        self._state = state

    state = property(__getstate__, __setstate__)

    def discard_and_focus_recent(self, item):
        ident = None if item is None else item.id
        lookup = {}
        recent = self.recent
        self.suspend_recent_updates()
        try:
            for project in list(self.projects):
                pid = project.id
                for editor in list(project.editors):
                    did = editor.id
                    if ident in (pid, did):
                        recent.discard(did)
                        assert editor.project is project, (editor.project, project)
                        editor.close()
                    else:
                        lookup[did] = editor
                if ident == pid:
                    recent.discard(pid)
                    self.projects.remove(project)
                    project.close()
                else:
                    lookup[pid] = project
        finally:
            self.resume_recent_updates()
        while True:
            ident = recent.pop()
            if ident is None:
                break
            item = lookup.get(ident)
            if item is not None:
                self.current_editor = item
                break
        if not recent and self.current_editor is not None:
            recent.push(self.current_editor.id)

    def suspend_recent_updates(self):
        self.recent = RecentItemStack(20)

    def resume_recent_updates(self):
        self.recent = self._suspended_recent

    def _get_current_editor(self):
        return self._current_editor

    def _set_current_editor(self, editor):
        if editor is self._current_editor:
            return
        self._current_editor = editor
        main_view = self.wc.mainView
        if editor is not None:
            sel = self.wc.docsController.selected_objects
            if not sel or sel[0] is not editor:
                self.wc.docsController.selected_objects = [editor]
            self.recent.push(editor.id)
            if isinstance(editor, Editor): # TODO eliminate isinstance call
                if editor.main_view not in main_view.subviews():
                    for subview in main_view.subviews():
                        subview.removeFromSuperview()
                    editor.document.addWindowController_(self.wc)
                    editor.set_main_view_of_window(main_view, self.wc.window())
                    #self.wc.setDocument_(editor.document)
                    if self.find_project_with_editor(editor) is None:
                        self.insert_items([editor])
                return
            #else:
            #    self.wc.window().setTitle_(editor.name)
            #    log.debug("self.wc.window().setTitle_(%r)", editor.name)
        for subview in main_view.subviews():
            subview.removeFromSuperview()
        self.wc.setDocument_(None)

    current_editor = property(_get_current_editor, _set_current_editor)

    def selected_editor_changed(self):
        selected = self.wc.docsController.selected_objects
        if selected and selected[0] is not self.current_editor:
            self.current_editor = selected[0]

    def iter_editors_of_document(self, doc):
        for project in self.projects:
            editor = project.find_editor_with_document(doc)
            if editor is not None:
                yield editor

    def should_select_item(self, outlineview, item):
        return True

    def new_project(self):
        project = Project(self)
        editor = project.create_editor()
        self.projects.append(project)
        self.current_editor = editor
        return project

    def toggle_properties_pane(self):
        tree_rect = self.wc.docsScrollview.frame()
        prop_rect = self.wc.propsView.frame()
        if self.wc.propsViewButton.state() == ak.NSOnState:
            # hide properties view
            tree_rect.size.height += prop_rect.size.height - 1.0
            tree_rect.origin.y = prop_rect.origin.y
            prop_rect.size.height = 0.0
        else:
            # show properties view
            tree_rect.size.height -= 115.0
            if prop_rect.size.height > 0:
                tree_rect.size.height += (prop_rect.size.height - 1.0)
            tree_rect.origin.y = prop_rect.origin.y + 115.0
            prop_rect.size.height = 116.0
            self.wc.propsView.setHidden_(False)
        resize_tree = fn.NSDictionary.dictionaryWithObjectsAndKeys_(
            self.wc.docsScrollview, ak.NSViewAnimationTargetKey,
            fn.NSValue.valueWithRect_(tree_rect), ak.NSViewAnimationEndFrameKey,
            None,
        )
        resize_props = fn.NSDictionary.dictionaryWithObjectsAndKeys_(
            self.wc.propsView, ak.NSViewAnimationTargetKey,
            fn.NSValue.valueWithRect_(prop_rect), ak.NSViewAnimationEndFrameKey,
            None,
        )
        anims = fn.NSArray.arrayWithObjects_(resize_tree, resize_props, None)
        animation = ak.NSViewAnimation.alloc().initWithViewAnimations_(anims)
        #animation.setAnimationBlockingMode_(NSAnimationBlocking)
        animation.setDuration_(0.25)
        animation.startAnimation()

    def find_project_with_editor(self, editor):
        for proj in self.projects:
            for e in proj.editors:
                if editor is e:
                    return proj
        return None

    def find_project_with_path(self, path):
        for proj in self.projects:
            p = proj.file_path
            if p and os.path.exists(p) and os.path.samefile(p, path):
                return proj
        return None

    def get_current_project(self, create=False):
        docs_controller = self.wc.docsController
        if docs_controller is not None:
            path = docs_controller.selectionIndexPath()
            if path is not None:
                index = path.indexAtPosition_(0)
                path2 = fn.NSIndexPath.indexPathWithIndex_(index)
                return docs_controller.objectAtArrangedIndexPath_(path2)
        if create:
            proj = Project(self)
            self.projects.append(proj)
            return proj
        return None

    def tooltip_for_item(self, view, item):
        it = view.realItemForOpaqueItem_(item)
        null = it is None or it.file_path is None
        return None if null else user_path(it.file_path)

    def should_edit_item(self, col, item):
        if col.isEditable():
            obj = representedObject(item)
            return isinstance(obj, Project) and obj.can_rename()
        return False

    def close_button_clicked(self, row):
        docs_view = self.wc.docsView
        if row < docs_view.numberOfRows():
            item = docs_view.itemAtRow_(row)
            item = docs_view.realItemForOpaqueItem_(item)
            item.perform_close()

    def window_did_become_key(self, window):
        editor = self.current_editor
        if isinstance(editor, Editor):
            # TODO refactor Editor to support check_for_external_changes()
            editor.document.check_for_external_changes(window)

    def window_should_close(self, window):
        from editxt.application import DocumentSavingDelegate
        # this method is called after the window controller has prompted the
        # user to save the current document (if it is dirty). This causes some
        # wierdness with the window and subsequent sheets. Technically we
        # do not need to prompt to save the current document a second time.
        # However, we will because it is easier... THIS IS UGLY! but there
        # doesn't seem to be a way to prevent the window controller from
        # prompting to save the current document when the window's close button
        # is clicked. UPDATE: the window controller seems to only prompt to save
        # the current document if the document is new (untitled).
        def iter_dirty_editors():
            app = self.app
            for proj in self.projects:
                wins = app.find_windows_with_project(proj)
                if wins == [self]:
                    for editor in proj.dirty_editors():
                        doc = editor.document
                        windows = app.iter_windows_with_editor_of_document(doc)
                        if list(windows) == [self]:
                            yield editor
                    yield proj
        def callback(should_close):
            if should_close:
                window.close()
        saver = DocumentSavingDelegate.alloc(). \
            init_callback_(iter_dirty_editors(), callback)
        saver.save_next_document()
        return False

    def window_will_close(self):
        self.app.discard_window(self)

    def _get_window_settings(self):
        return dict(
            frame_string=str(self.wc.window().stringWithSavedFrame()),
            splitter_pos=self.wc.splitView.fixedSideThickness(),
            properties_hidden=(self.wc.propsViewButton.state() == ak.NSOnState),
        )
    def _set_window_settings(self, settings):
        fs = settings.get("frame_string")
        if fs is not None:
            self.wc.window().setFrameFromString_(fs)
            self.wc.setShouldCascadeWindows_(False)
        sp = settings.get("splitter_pos")
        if sp is not None:
            self.wc.splitView.setFixedSideThickness_(sp)
        if settings.get("properties_hidden", False):
            # REFACTOR eliminate boilerplate here (similar to toggle_properties_pane)
            self.wc.propsViewButton.setState_(ak.NSOnState)
            tree_view = self.wc.docsScrollview
            prop_view = self.wc.propsView
            tree_rect = tree_view.frame()
            prop_rect = prop_view.frame()
            tree_rect.size.height += prop_rect.size.height - 1.0
            tree_rect.origin.y = prop_rect.origin.y
            tree_view.setFrame_(tree_rect)
            prop_rect.size.height = 0.0
            prop_view.setFrame_(prop_rect)
        self.window_settings_loaded = True
    window_settings = property(_get_window_settings, _set_window_settings)

    def close(self):
        wc = self.wc
        if wc is not None:
            self.window_settings_loaded = False
            while self.projects:
                self.projects.pop().close()
            #wc.docsController.setContent_(None)
            #wc.setDocument_(None)
            #self.wc = None

    # drag/drop logic ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def is_project_drag(self, info):
        """Return True if only projects are being dropped else False"""
        pb = info.draggingPasteboard()
        t = pb.availableTypeFromArray_(self.supported_drag_types)
        if t == const.DOC_ID_LIST_PBOARD_TYPE:
            id_list = pb.propertyListForType_(const.DOC_ID_LIST_PBOARD_TYPE)
            items = self.iter_dropped_id_list(id_list)
            return all(isinstance(item, Project) for item in items)
        elif t == ak.NSFilenamesPboardType:
            paths = pb.propertyListForType_(ak.NSFilenamesPboardType)
            return all(Project.is_project_path(path) for path in paths)
        return False

    def write_items_to_pasteboard(self, outline_view, items, pboard):
        """Write dragged items to pasteboard

        :param outline_view: The OutlineView containing the items.
        :param items: A list of opaque outline view item objects.
        :param pboard: ak.NSPasteboard object.
        :returns: True if items were written else False.
        """
        data = defaultdict(list)
        for item in items:
            item = outline_view.realItemForOpaqueItem_(item)
            data[const.DOC_ID_LIST_PBOARD_TYPE].append(item.id)
            path = item.file_path
            if path is not None and os.path.exists(path):
                data[ak.NSFilenamesPboardType].append(path)
        if data:
            types = [t for t in self.supported_drag_types if t in data]
            pboard.declareTypes_owner_(types, None)
            for t in types:
                pboard.setPropertyList_forType_(data[t], t)
        return bool(data)

    def validate_drop(self, outline_view, info, item, index):
        if self.is_project_drag(info):
            if item is not None:
                obj = representedObject(item)
                path = self.wc.docsController.indexPathForObject_(obj)
                if path is not None:
                    index = path.indexAtPosition_(0)
                    outline_view.setDropItem_dropChildIndex_(None, index)
                else:
                    return ak.NSDragOperationNone
            elif index < 0:
                outline_view.setDropItem_dropChildIndex_(None, len(self.projects))
        else:
            # text document drag
            if item is not None:
                obj = representedObject(item)
                if isinstance(obj, Project):
                    if index < 0:
                        #outline_view.setDropItem_dropChildIndex_(item, 0)
                        # the following might be more correct, but is too confusing
                        outline_view.setDropItem_dropChildIndex_(item, len(obj.editors))
                else:
                    return ak.NSDragOperationNone # document view cannot have children
            else:
                if index < 0:
                    # drop on listview background
                    last_proj_index = len(self.projects) - 1
                    if last_proj_index > -1:
                        # we have at least one project
                        path = fn.NSIndexPath.indexPathWithIndex_(last_proj_index)
                        node = self.wc.docsController.nodeAtArrangedIndexPath_(path)
                        proj = representedObject(node)
                        outline_view.setDropItem_dropChildIndex_(node, len(proj.editors))
                    else:
                        outline_view.setDropItem_dropChildIndex_(None, -1)
                elif index == 0:
                    return ak.NSDragOperationNone # prevent drop above top project
        # src = info.draggingSource()
        # if src is not None:
        #   # internal drag
        #   if src is not outline_view:
        #       delegate = getattr(src, "delegate", lambda:None)()
        #       if isinstance(delegate, WindowController) and \
        #           delegate is not self.wc:
        #           # drag from some other window controller
        #           # allow copy (may need to override outline_view.ignoreModifierKeysWhileDragging)
        return ak.NSDragOperationGeneric

    def accept_drop(self, view, pasteboard, parent=const.CURRENT, index=-1):
        """Accept drop operation

        :param view: The view on which the drop occurred.
        :param pasteboard: NSPasteboard object.
        :param parent: The parent item in the outline view.
        :param index: The index in the outline view or parent item at which the
            drop occurred.
        :returns: True if the drop was accepted, otherwise False.
        """
        pb = pasteboard
        t = pb.availableTypeFromArray_(self.supported_drag_types)
        action = None
        if t == const.DOC_ID_LIST_PBOARD_TYPE:
            id_list = pb.propertyListForType_(const.DOC_ID_LIST_PBOARD_TYPE)
            items = self.iter_dropped_id_list(id_list)
            action = const.MOVE
        elif t == ak.NSFilenamesPboardType:
            paths = pb.propertyListForType_(ak.NSFilenamesPboardType)
            items = self.iter_dropped_paths(paths)
        else:
            assert t is None, t
            return False
        return bool(self.insert_items(items, parent, index, action))

    def iter_dropped_id_list(self, id_list):
        """Iterate TextDocument objects referenced by pasteboard (if any)"""
        if not id_list:
            return
        for ident in id_list:
            item = self.app.find_item_with_id(ident)
            if item is not None:
                yield item

    def iter_dropped_paths(self, paths):
        if not paths:
            return
        for path in paths:
            if os.path.isfile(path) or not os.path.exists(path):
                yield self.app.document_with_path(path)
#            elif os.path.isdir(path):
#                yield Project(self, name=os.path.dirname(path))
            else:
                log.info("cannot open path: %s", path)

    def insert_items(self, items, project=const.CURRENT, index=-1, action=None):
        """Insert projects or documents into the document tree

        :param items: A sequence of projects and/or documents.
        :param project: The parent project into which items are being inserted.
            Documents will be inserted in the current project if unspecified.
        :param index: The index in the outline view or parent project at which
            the item(s) should be inserted.
        :param action: What to do with items that are already open in
            this window:

            - None : insert new item(s), but do not change existing item(s).
            - MOVE : move existing item(s) to index.
            - COPY : copy item(s) to index.

            A file is considered to be "existing" if there is a editor
            with the same path in the project where it is being
            inserted. A project is considered to be "existing" if there
            is a project with the same path in the window where it is
            being inserted.
        :returns: A list of items that were inserted.
        """
        proj_index = len(self.projects) # insert projects at end of list
        if project is const.CURRENT:
            assert index == -1, index
            project = self.get_current_project()
        if project is None:
            # a new project will be inserted at index if/when needed
            if index >= 0 and index <= proj_index:
                proj_index = index
            index = 0
        elif index < 0:
            index = len(project.editors)
        inserted = []
        focus = None
        is_move = action == const.MOVE
        is_copy = action == const.COPY
        self.suspend_recent_updates()
        try:
            for item in items:
                inserted.append(item)
                if isinstance(item, Project):
                    set_focus, proj_index = \
                        self._insert_project(item, proj_index, action)
                    if set_focus:
                        focus = item
                    continue

                if project is None:
                    project = Project(self)
                    if isinstance(item, Editor):
                        if is_move:
                            editor = item
                            item.project.remove_editor(editor)
                        else:
                            editor = Editor(project, document=item.document)
                    else:
                        assert isinstance(item, TextDocument), item
                        editor = Editor(project, document=item)
                    self.projects.insert(proj_index, project)
                    proj_index += 1
                    index = 0
                else:
                    if isinstance(item, Editor):
                        editor, item = item, item.document
                    else:
                        assert isinstance(item, TextDocument), item
                        editor = project.find_editor_with_document(item)
                    if is_move and editor is not None:
                        if editor.project is project:
                            vindex = project.editors.index(editor)
                            if vindex in [index - 1, index]:
                                continue
                            if vindex - index <= 0:
                                index -= 1
                        editor.project.remove_editor(editor)
                    elif is_copy or editor is None or project is not editor.project:
                        editor = Editor(project, document=item)
                    else:
                        focus = editor
                        continue
                project.insert_editor(index, editor)
                focus = editor
                index += 1
        finally:
            self.resume_recent_updates()
        if focus is not None:
            self.current_editor = focus
        return inserted

    def _insert_project(self, item, index, action):
        if action != const.MOVE:
            raise NotImplementedError('cannot copy project yet')
        if item.window is self:
            window = self
            pindex = self.projects.index(item)
            if pindex == index:
                return False, index
            if pindex - index <= 0:
                index -= 1
        else:
            window = item.window

        # BEGIN HACK crash on remove project with editors
        editors = item.editors
        tmp, editors[:] = list(editors), []
        window.projects.remove(item) # this line should be all that's necessary
        editors.extend(tmp)
        # END HACK

        self.projects.insert(index, item)
        return True, index + 1

    def undo_manager(self):
        doc = self.wc.document()
        if doc is None:
            return fn.NSUndoManager.alloc().init()
        return doc.undoManager()


class WindowController(ak.NSWindowController):

    # 2013-11-23 08:56:28.994 EditXTDev[47194:707] An instance 0x10675fc30 of
    # class _KVOList was deallocated while key value observers were still
    # registered with it. Observation info was leaked, and may even become
    # mistakenly attached to some other object. Set a breakpoint on
    # NSKVODeallocateBreak to stop here in the debugger.
    #window_ = WeakProperty()

    docsController = objc.IBOutlet()
    docsScrollview = objc.IBOutlet()
    docsView = objc.IBOutlet()
    mainView = objc.IBOutlet()
    splitView = objc.IBOutlet()
    plusButton = objc.IBOutlet()
    propsView = objc.IBOutlet()
    propsViewButton = objc.IBOutlet()
    #propCharacterEncoding = objc.IBOutlet()
    #propLanguageSelector = objc.IBOutlet()
    #propLineEndingType = objc.IBOutlet()
    #propTabSpacesInput = objc.IBOutlet()
    #propTabSpacesSelector = objc.IBOutlet()
    #propWrapLines = objc.IBOutlet()

    def windowDidLoad(self):
        self.window_.window_did_load()

    def characterEncodings(self):
        return fn.NSValueTransformer.valueTransformerForName_("CharacterEncodingTransformer").names
        #return const.CHARACTER_ENCODINGS

    def setCharacterEncodings_(self, value):
        pass

    def syntaxDefNames(self):
        return [d.name for d in self.window_.app.syntaxdefs]

    def setSyntaxDefNames_(self, value):
        pass

    def projects(self):
        return self.window_.projects

    def newProject_(self, sender):
        self.window_.new_project()

    def togglePropertiesPane_(self, sender):
        self.window_.toggle_properties_pane()

    def outlineViewSelectionDidChange_(self, notification):
        self.window_.selected_editor_changed()

    def outlineViewItemDidCollapse_(self, notification):
        representedObject(notification.userInfo()["NSObject"]).expanded = False

    def outlineViewItemDidExpand_(self, notification):
        representedObject(notification.userInfo()["NSObject"]).expanded = True

    def outlineView_shouldSelectItem_(self, outlineview, item):
        return self.window_.should_select_item(outlineview, item)

    def outlineView_willDisplayCell_forTableColumn_item_(self, view, cell, col, item):
        if col.identifier() == "name":
            cell.setImage_(representedObject(item).icon())

    def outlineView_shouldEditTableColumn_item_(self, view, col, item):
        return self.window_.should_edit_item(col, item)

    def outlineView_toolTipForCell_rect_tableColumn_item_mouseLocation_(
        self, view, cell, rect, col, item, mouseloc):
        return self.window_.tooltip_for_item(view, item), rect

    def hoverButton_rowClicked_(self, cell, row):
        self.window_.close_button_clicked(row)

    @untested
    def hoverButtonCell_imageForState_row_(self, cell, state, row):
        if state is BUTTON_STATE_NORMAL and self.docsView.isRowSelected_(row):
            state = BUTTON_STATE_SELECTED
        if row >= 0 and row < self.docsView.numberOfRows():
            item = self.docsView.itemAtRow_(row)
            doc = self.docsView.realItemForOpaqueItem_(item)
            if doc is not None and doc.is_dirty:
                return self.dirtyImages[state]
        return self.cleanImages[state]

    def undo_manager(self):
        return self.window_.undo_manager()

    def windowTitleForDocumentDisplayName_(self, name):
        editor = self.window_.current_editor
        if editor is not None and editor.file_path is not None:
            return user_path(editor.file_path)
        return name

    def windowDidBecomeKey_(self, notification):
        self.window_.window_did_become_key(notification.object())

    def windowShouldClose_(self, window):
        return self.window_.window_should_close(window)

    def windowWillClose_(self, notification):
        self.window_.window_will_close()

    # outlineview datasource methods ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def outlineView_writeItems_toPasteboard_(self, view, items, pboard):
        return self.window_.write_items_to_pasteboard(view, items, pboard)

    def outlineView_acceptDrop_item_childIndex_(self, view, info, item, index):
        parent = None if item is None else representedObject(item)
        return self.window_.accept_drop(
            view, info.draggingPasteboard(), parent, index)

    def outlineView_validateDrop_proposedItem_proposedChildIndex_(self, view, info, item, index):
        return self.window_.validate_drop(view, info, item, index)

    # def outlineView_namesOfPromisedFilesDroppedAtDestination_forDraggedItems_(
    #   self, view, names, items):
    #   item = representedObject(item)
    #   raise NotImplementedError

    # the following are dummy implementations since we are using bindings (they
    # are required since we are using NSOutlineView's drag/drop datasource methods)
    # see: http://theocacao.com/document.page/130

    def outlineView_child_ofItem_(self, view, index, item):
        return None

    def outlineView_isItemExpandable_(self, view, item):
        return False

    def outlineView_numberOfChildrenOfItem_(self, view, item):
        return 0

    def outlineView_objectValueForTableColumn_byItem_(self, view, col, item):
        return None
