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
import sys
from collections import defaultdict
from contextlib import contextmanager
from itertools import groupby
from os.path import basename, dirname, isabs, isdir, sep, split
from urllib.parse import parse_qs, unquote, urlparse
from weakref import WeakSet

import AppKit as ak
import Foundation as fn

import editxt.constants as const
from editxt.document import TextDocument
from editxt.editor import Editor
from editxt.platform.kvo import KVOList
from editxt.platform.pasteboard import Pasteboard
from editxt.platform.views import Menu, MenuItem
from editxt.platform.window import WindowController
from editxt.project import Project
from editxt.textcommand import CommandBar
from editxt.undo import UndoManager
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
        self._recent_history = None
        self.window_settings_loaded = False
        self.no_document_undo_manager = UndoManager()
        self.menu = self.make_context_menu()
        self.dirty_editors = WeakSet()

    def window_did_load(self):
        wc = self.wc
        wc.docsView.default_menu = self.menu
        wc.docsView.setRefusesFirstResponder_(True)
        wc.docsView.registerForDraggedTypes_(self.supported_drag_types)
        wc.plusButton.setRefusesFirstResponder_(True)
        wc.plusButton.setImage_(load_image(const.PLUS_BUTTON_IMAGE))
        wc.propsViewButton.setRefusesFirstResponder_(True)
        wc.propsViewButton.setImage_(load_image(const.PROPS_DOWN_BUTTON_IMAGE))
        wc.propsViewButton.setAlternateImage_(load_image(const.PROPS_UP_BUTTON_IMAGE))

        self._setstate(self._state)
        self._state = None

        if not self.projects:
            self.new_project()

    def make_context_menu(self):
        def has_path(item):
            return item and item.file_path
        return Menu([
            MenuItem("Copy Path", self.copy_path, is_enabled=has_path),
            MenuItem("Close", self.close_item, "Command+w"),
        ])

    def _setstate(self, state):
        if state:
            projects = state.get("projects")
            if projects is None:
                projects = state.get("project_serials", []) # legacy
            for serial in projects:
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
            with self.suspend_recent_updates():
                pass # focus recent

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
                for j, doc in enumerate(project.editors):
                    indexes[doc.id] = [i, j]
            yield "projects", serials
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

    def discard(self, item):
        ident = None if item is None else item.id
        recent = self.recent
        update_current = item in self.selected_items or not self.selected_items
        with self.suspend_recent_updates(update_current):
            for project in list(self.projects):
                pid = project.id
                for editor in list(project.editors):
                    did = editor.id
                    if ident in (pid, did):
                        recent.discard(did)
                        assert editor.project is project, (editor.project, project)
                        editor.close()
                if ident == pid:
                    recent.discard(pid)
                    self.projects.remove(project)
                    project.close()

    def focus(self, value, offset=1):
        """Change the current document by navigating the tree or recent documents

        :param value: One of the direction constants in
        `editxt.constants` or an editor's file path. `NEXT` and
        `PREVIOUS` select items in the recent editors stack. `UP` and
        `DOWN` move up or down in the tree.
        :param offset: The number of positions to move in direction.
        :returns: True if a new editor was focused, otherwise false.
        """
        def focus(ident):
            for project in self.projects:
                if project.id == ident:
                    self.current_editor = project
                    return True
                else:
                    for editor in project.editors:
                        if editor.id == ident:
                            self.current_editor = editor
                            return True
            return False
        def get_item_in_tree(current, offset):
            if current is not None:
                items = []
                index = 0
                stop = sys.maxsize
                for project in self.projects:
                    items.append(project)
                    if current.id == project.id:
                        stop = index + offset
                        if stop <= index:
                            break
                    index += 1
                    if project.expanded:
                        for editor in project.editors:
                            items.append(editor)
                            if current.id == editor.id:
                                stop = index + offset
                                if stop <= index:
                                    break
                            index += 1
                if 0 <= stop < len(items):
                    return items[stop]
            return None
        if isinstance(value, const.Constant):
            if value == const.PREVIOUS or value == const.NEXT:
                history = ((list(reversed(self.recent)) + [0])
                           if self._recent_history is None
                           else self._recent_history)
                if value == const.PREVIOUS:
                    offset = offset + history[-1]
                else:
                    offset = history[-1] - offset
                if 0 <= offset < len(history) - 1:
                    ok = focus(history[offset])
                    if ok:
                        history[-1] = offset
                        self._recent_history = history
                    return ok
                return False
            if value == const.UP:
                offset = -offset
            editor = get_item_in_tree(self.current_editor, offset)
            if editor is not None:
                self.current_editor = editor
                return True
        if isinstance(value, (Editor, Project)):
            return focus(value.id)
        return False

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

    def do_menu_command(self, sender):
        self.app.text_commander.do_menu_command(self.current_editor, sender)

    def validate_menu_command(self, item):
        return self.app.text_commander.is_menu_command_enabled(self.current_editor, item)

    @property
    def current_editor(self):
        return self._current_editor
    @current_editor.setter
    def current_editor(self, editor):
        self._current_editor = editor
        self._recent_history = None
        if editor is None:
            self.wc.setup_current_editor(None)
            self.selected_items = []
            return
        if self.wc.is_current_view(editor.main_view):
            editor.focus()
        else:
            self.recent.push(editor.id)
            if self.wc.setup_current_editor(editor):
                if isinstance(editor, Editor) \
                        and self.find_project_with_editor(editor) is None:
                    self.insert_items([editor])
        if not self.selected_items or editor is not self.selected_items[0]:
            self.selected_items = [editor]

    @property
    def selected_items(self):
        return self.wc.selected_items
    @selected_items.setter
    def selected_items(self, value):
        self.wc.selected_items = value

    def selected_editor_changed(self):
        selected = self.selected_items
        if selected and selected[0] is not self.current_editor:
            self.current_editor = selected[0]

    def on_dirty_status_changed(self, editor, dirty):
        if dirty:
            self.dirty_editors.add(editor)
        else:
            self.dirty_editors.discard(editor)
        self.wc.on_dirty_status_changed(editor, self.is_dirty)

    @property
    def is_dirty(self):
        return bool(self.dirty_editors)

    def iter_editors_of_document(self, doc):
        for project in self.projects:
            for editor in project.iter_editors_of_document(doc):
                yield editor

    def should_select_item(self, outlineview, item):
        return True

    def open_documents(self):
        editor = self.current_editor
        if editor is not None and editor.dirname():
            directory = editor.dirname()
        else:
            directory = os.path.expanduser("~")
        self.wc.open_documents(directory, None, self.open_paths)

    def save_as(self):
        self.save(prompt=True)

    def save(self, prompt=False):
        editor = self.current_editor
        if isinstance(editor, Editor):
            editor.save(prompt=prompt)

    def reload_current_document(self):
        editor = self.current_editor
        if isinstance(editor, Editor):
            editor.document.reload_document()

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
        if editor is None:
            diff_with_original = None
        else:
            def diff_with_original():
                from editxt.command.diff import diff
                from editxt.command.parser import Options
                diff(editor, Options(file=editor.file_path))
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

    def copy_path(self, item):
        """Copy item path to pasteboard

        Put newline-delimited paths on pasteboard if there are multiple
        items selected and the given item is one of them.
        """
        selected = self.selected_items
        if item not in selected:
            selected = [item]
        Pasteboard().text = "\n".join(item.file_path for item in selected)

    def close_item(self, item):
        """Close editor or project

        Close all selected items if there are multiple items selected
        and the given item is one of them.
        """
        def do_close(should_close):
            if should_close:
                for item in selected:
                    self.discard(item)
        selected = self.selected_items
        if item not in selected:
            selected = [item]
        self.app.async_interactive_close(selected, do_close)

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

    def get_id_path_pairs(self, items):
        """Get a list of (<item id>, <item path>) pairs for given items

        :param items: A list of editors and/or projects.
        :returns: A list of two-tuples (<item id>, <item path>). <item id> is
        an opaque internal identifier for the document, and <item path> is
        the file system path of the item or ``None`` if the item does not have
        a path.
        """
        def pair(item):
            path = item.file_path
            return (item.id, path if path and os.path.exists(path) else None)
        return [pair(item) for item in items]

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
            return ak.NSDragOperationMove
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
        op = info.draggingSourceOperationMask()
        if op not in [ak.NSDragOperationCopy, ak.NSDragOperationGeneric]:
            op = ak.NSDragOperationMove
        return op

    def accept_drop(self, view, pasteboard, parent=const.CURRENT, index=-1, action=const.MOVE):
        """Accept drop operation

        :param view: The view on which the drop occurred.
        :param pasteboard: NSPasteboard object.
        :param parent: The parent item in the outline view.
        :param index: The index in the outline view or parent item at which the
            drop occurred.
        :param action: The action to perform when dragging (see
        ``insert_items(..., action)``). Ignored if the items being dropped are
        paths.
        :returns: True if the drop was accepted, otherwise False.
        """
        pb = pasteboard
        t = pb.availableTypeFromArray_(self.supported_drag_types)
        if t == const.DOC_ID_LIST_PBOARD_TYPE:
            id_list = pb.propertyListForType_(const.DOC_ID_LIST_PBOARD_TYPE)
            items = self.iter_dropped_id_list(id_list)
        elif t == ak.NSFilenamesPboardType:
            paths = pb.propertyListForType_(ak.NSFilenamesPboardType)
            items = self.iter_dropped_paths(paths)
            action = None
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

    def open_url(self, url, link, focus=True):
        """Open file specified by URL

        The URL must have two attributes:
        - path : The path to the file. The first leading slash is
          stripped, so absolute paths must have an extra slash.
        - query : A query string from which an optional "goto" parameter
          may be parsed. The goto parameter specifies a line or line +
          selection (`line.sel_start.sel_length`) to goto/select after
          opening the file.

        :param url: Parsed URL. See `urllib.parse.urlparse` for structure.
        :param link: The original URL string.
        :param focus: Focus newly opened editor.
        """
        path = unquote(url.path)
        if path.startswith("/"):
            path = path[1:]
        editors = self.open_paths([path], focus=focus)
        if editors:
            assert len(editors) == 1, (link, editors)
            query = parse_qs(url.query)
            if "goto" in query:
                goto = query["goto"][0]
                editors[0].handle_goto(goto, link)

    def open_paths(self, paths, focus=True):
        return self.insert_items(self.iter_dropped_paths(paths), focus=focus)

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

    def insert_items(self, items, project=const.CURRENT, index=-1, action=None,
                     focus=True):
        """Insert items into the document tree

        :param items: An iterable of projects, editors, and/or documents.
        :param project: The parent project into which items are being inserted.
            Documents will be inserted in the current project if unspecified.
        :param index: The index in the outline view or parent project at which
            the item(s) should be inserted. Add after current if < 0 (default).
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
        :param focus: Focus most recent newly opened editor if true (the
            default).
        :returns: A list of editors and projects that were inserted.
        """
        if (project is not None and
            project != const.CURRENT and
            project.window is not self):
            raise ValueError("project does not belong to this window")
        inserted = []
        focus_editor = None
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
                            focus_editor = project
                    # Reset index since the project into which non-project
                    # items will be inserted has changed.
                    index = -1
                else:
                    if project == const.CURRENT or project is None:
                        if index >= 0:
                            raise NotImplementedError
                        project = self.get_current_project(create=True)
                    inserts, focus_editor = project.insert_items(group, index, action)
                    inserted.extend(inserts)
        if focus and focus_editor is not None:
            self.current_editor = focus_editor
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
            return self.no_document_undo_manager
        return editor.undo_manager
