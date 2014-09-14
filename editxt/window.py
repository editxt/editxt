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
from collections import defaultdict
from contextlib import contextmanager
from itertools import groupby

import AppKit as ak
import Foundation as fn

import editxt.constants as const
from editxt.document import TextDocument
from editxt.editor import Editor
from editxt.platform.kvo import KVOList
from editxt.platform.views import BUTTON_STATE_HOVER, BUTTON_STATE_NORMAL, BUTTON_STATE_PRESSED
from editxt.platform.window import WindowController
from editxt.project import Project
from editxt.textcommand import CommandBar
from editxt.util import (RecentItemStack, load_image, representedObject,
    user_path, WeakProperty)

log = logging.getLogger(__name__)

class Error(Exception): pass

BUTTON_STATE_SELECTED = object()


class Window(object):

    supported_drag_types = [const.DOC_ID_LIST_PBOARD_TYPE, ak.NSFilenamesPboardType]
    app = WeakProperty()

    def __init__(self, app, state=None):
        self.app = app
        self._current_editor = None
        self.wc = WindowController(self)
        self.state = state
        self.command = CommandBar(self, app.text_commander)
        self.projects = KVOList()
        self.recent = self._suspended_recent = RecentItemStack(100)
        self.window_settings_loaded = False

    def window_did_load(self):
        wc = self.wc
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
        with self.suspend_recent_updates():
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

    @contextmanager
    def suspend_recent_updates(self, update_current=True):
        self.recent = RecentItemStack(1)
        try:
            yield
        finally:
            self.recent = recent = self._suspended_recent
        if not update_current:
            return
        lookup = {}
        for project in self.projects:
            lookup[project.id] = project
            lookup.update((e.id, e) for e in project.editors)
        current = self.current_editor
        current_id = None if current is None else current.id
        if current_id in lookup and recent and current_id == recent[-1]:
            return
        while True:
            ident = recent.pop()
            if ident is None:
                if self.projects:
                    for project in self.projects:
                        if project.expanded and project.editors:
                            self.current_editor = project.editors[0]
                            break
                    else:
                        self.current_editor = self.projects[0]
                break
            item = lookup.get(ident)
            if item is not None:
                self.current_editor = item
                break

    def _get_current_editor(self):
        return self._current_editor

    def _set_current_editor(self, editor):
        if editor is self._current_editor:
            return
        self._current_editor = editor
        if editor is not None:
            self.recent.push(editor.id)
        if self.wc.setup_current_editor(editor):
            assert isinstance(editor, Editor), editor
            if self.find_project_with_editor(editor) is None:
                self.insert_items([editor])

    current_editor = property(_get_current_editor, _set_current_editor)

    def selected_editor_changed(self):
        selected = self.wc.docsController.selected_objects
        if selected and selected[0] is not self.current_editor:
            self.current_editor = selected[0]

    def iter_editors_of_document(self, doc):
        for project in self.projects:
            for editor in project.iter_editors_of_document(doc):
                yield editor

    def should_select_item(self, outlineview, item):
        return True

    def save_as(self):
        self.save(prompt=True)

    def save(self, prompt=False):
        editor = self.current_editor
        if isinstance(editor, Editor):
            editor.save(prompt=prompt)

    def save_document_as(self, editor, save_with_path):
        """Prompt for path to save document

        :param editor: The editor of the document to be saved.
        :param save_with_path: A callback accepting a sinlge parameter (the
        chosen file path) that does the work of actually saving the file.
        Call with ``None`` to cancel the save operation.
        """
        directory, filename = self._directory_and_filename(editor.file_path)
        self.wc.save_document_as(directory, filename, save_with_path)

    def prompt_to_overwrite(self, editor, save_with_path):
        """Prompt to overwrite the given editor's document's file path

        :param editor: The editor of the document to be saved.
        :param save_with_path: A callback accepting a sinlge parameter (the
        chosen file path) that does the work of actually saving the file.
        Call with ``None`` to cancel the save operation.
        """
        def save_as():
            self.save_document_as(editor, save_with_path)
        if editor.text_view is None:
            diff_with_original = None
        else:
            def diff_with_original():
                from editxt.command.diff import diff
                save_with_path(None) # cancel save operation
                diff(editor.text_view, self, None)
        self.wc.prompt_to_overwrite(
            editor.file_path, save_with_path, save_as, diff_with_original)

    def prompt_to_close(self, editor, save_discard_or_cancel, save_as=True):
        """Prompt to see if the document can be closed

        :param editor: The editor of the document to be closed.
        :param save_discard_or_cancel: A callback to be called with the outcome
        of the prompt: save (True), discard (False), or cancel (None).
        :param save_as: Boolean, if true prompt to "save as" (with dialog),
        otherwise prompt to save (without dialog).
        """
        self.current_editor = editor
        self.wc.prompt_to_close(editor.file_path, save_discard_or_cancel, save_as)

    @staticmethod
    def _directory_and_filename(path):
        from os.path import basename, dirname, isabs, isdir, sep, split
        if isabs(path):
            directory, filename = split(path)
            while directory and directory != sep and not isdir(directory):
                directory = dirname(directory)
        else:
            directory = None
            filename = basename(path)
        assert filename, path
        if not directory:
            # TODO editor.project.path or path of most recent document
            # None -> directory used in the previous invocation of the panel
            directory = None
        return directory, filename

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
        item = self.current_editor
        if item is not None:
            return item if isinstance(item, Project) else item.project
        if self.projects:
            for project in self.projects:
                if project.expanded:
                    return project
            return self.projects[0]
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
            def do_close():
                self.discard_and_focus_recent(item)
            item = docs_view.itemAtRow_(row)
            item = docs_view.realItemForOpaqueItem_(item)
            item.interactive_close(do_close)

    def window_did_become_key(self, window):
        editor = self.current_editor
        if isinstance(editor, Editor):
            # TODO refactor Editor to support check_for_external_changes()
            editor.document.check_for_external_changes(window)

    def should_close(self, do_close):
        """Determine if the window should be closed

        If this returns false an interactive close loop will be started, which
        may eventually result in the window being closed.
        """
        def iter_dirty_editors():
            app = self.app
            for proj in self.projects:
                wins = app.find_windows_with_project(proj)
                if wins == [self]:
                    for editor in proj.dirty_editors():
                        doc_windows = app.iter_windows_with_editor_of_document(
                                            editor.document)
                        if all(win is self for win in doc_windows):
                            yield editor
        if next(iter_dirty_editors(), None) is None:
            return True
        def callback(should_close):
            if should_close:
                do_close()
        self.app.async_interactive_close(iter_dirty_editors(), callback)
        return False

    def window_will_close(self):
        self.app.discard_window(self)

    def _get_window_settings(self):
        return dict(
            frame_string=str(self.wc.frame_string),
            splitter_pos=self.wc.splitter_pos,
            properties_hidden=self.wc.properties_hidden,
        )
    def _set_window_settings(self, settings):
        fs = settings.get("frame_string")
        if fs is not None:
            self.wc.frame_string = fs
        sp = settings.get("splitter_pos")
        if sp is not None:
            self.wc.splitter_pos = sp
        self.wc.properties_hidden = settings.get("properties_hidden", False)
        self.window_settings_loaded = True
    window_settings = property(_get_window_settings, _set_window_settings)

    def close(self):
        wc = self.wc
        if wc is not None:
            self.window_settings_loaded = False
            while self.projects:
                self.projects.pop().close()
            #wc.docsController.setContent_(None)
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
            if path is None or os.path.isfile(path) or not os.path.exists(path):
                yield self.app.document_with_path(path)
#            elif os.path.isdir(path):
#                yield Project(self, name=os.path.dirname(path))
            else:
                log.info("cannot open path: %s", path)

    def insert_items(self, items, project=const.CURRENT, index=-1, action=None):
        """Insert items into the document tree

        :param items: An iterable of projects, editors, and/or documents.
        :param project: The parent project into which items are being inserted.
            Documents will be inserted in the current project if unspecified.
        :param index: The index in the outline view or parent project at which
            the item(s) should be inserted. Append if < 0 (the default).
        :param action: What to do with items that are already open in
            this window:

            - None : insert new item(s), but do not change existing item(s).
            - MOVE : move existing item(s) to index.
            - COPY : copy item(s) to index.

            A file is considered to be "existing" if there is an editor
            with the same path in the project where it is being
            inserted. A project is considered to be "existing" if there
            is a project with the same path in the window where it is
            being inserted.
        :returns: A list of items that were inserted.
        """
        if (project is not None and
            project != const.CURRENT and
            project.window is not self):
            raise ValueError("project does not belong to this window")
        inserted = []
        focus = None
        with self.suspend_recent_updates(update_current=False):
            pindex = index
            if pindex < 0:
                pindex = len(self.projects)
            for is_project_group, group in groupby(items, self.is_project):
                if is_project_group:
                    for item in group:
                        project, pindex = self._insert_project(item, pindex, action)
                        if project is not None:
                            inserted.append(project)
                            focus = project
                    # Reset index since the project into which non-project
                    # items will be inserted has changed.
                    index = -1
                else:
                    if project == const.CURRENT or project is None:
                        if index >= 0:
                            raise NotImplementedError
                        project = self.get_current_project(create=True)
                    inserts, focus = project.insert_items(group, index, action)
                    inserted.extend(inserts)
        if focus is not None:
            self.current_editor = focus
        return inserted

    def is_project(self, item):
        """Return true if item can be inserted as a project"""
        # TODO return true if item is a directory path
        return isinstance(item, Project)

    def _insert_project(self, item, index, action):
        if action != const.MOVE:
            raise NotImplementedError('cannot copy project yet')
        if item.window is self:
            window = self
            pindex = self.projects.index(item)
            if pindex == index:
                return None, index
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

        item.window = self
        self.projects.insert(index, item)
        return item, index + 1

    def show(self, sender):
        self.wc.showWindow_(sender)

    @property
    def undo_manager(self):
        editor = self.current_editor
        if editor is None:
            return None
        return editor.undo_manager
