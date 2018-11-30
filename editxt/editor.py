# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2014 Daniel Miller <millerdev@gmail.com>
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
from urllib.parse import urlparse

import AppKit as ak
import Foundation as fn
# from NDAlias import NDAlias

import editxt.constants as const
import editxt.platform.constants as platform_const

from editxt.command.find import Finder, FindOptions
from editxt.command.util import change_indentation, replace_newlines
from editxt.document import DocumentController, Error as DocumentError
from editxt.linenumbers import LineNumbers
from editxt.platform.alert import Alert
from editxt.platform.document import setup_main_view, teardown_main_view
from editxt.platform.events import debounce
from editxt.platform.kvo import KVOList, KVOProxy, KVOLink
from editxt.platform.window import OutputPanel
from editxt.util import noraise, register_undo_callback, user_path, WeakProperty

log = logging.getLogger(__name__)


def document_property(do):
    name = do.__name__
    def fget(self):
        if self.document is None:
            return None
        return getattr(self.document, name)
    def fset(self, value):
        old = getattr(self.document, name)
        if value != old:
            do(self, value, old)
    return property(fget, fset)


class CommandSubject:

    id = None  # will be overwritten (here for type api for testing)
    command_view = None
    command_output = None

    def message(self, *args, **kw):
        """Display a message in the command view output pane"""
        self.command_view.message(*args, **kw)

    def get_output_view(self):
        self.stop_output()
        self.message("")
        self.command_output = CommandOutput(self.command_view, self)
        return self.command_output

    def create_output_panel(self, text_data, rect):
        """Create a command output panel

        This also redirects output of the currently running command (if
        any) to the new output panel.

        :param text_data: text data to be displayed in the panel (see
        `ContentSizedTextView.text_data`).
        :param rect: The initial size and location in screen coordinates of
        the output panel.
        :returns: The output panel object.
        """
        panel = OutputPanel(self, text_data, rect)
        if self.command_output is not None:
            panel.on.close(self.command_output.kill_process)
            self.command_output.output_view = panel
            self.command_output = None
        self.command_view.dismiss()
        panel.show(self.window)
        return panel

    def stop_output(self):
        if self.command_output is not None:
            self.command_output.kill_process()
            self.command_output = None

    def do_command(self, selector):
        if selector == platform_const.ESCAPE and self.command_view is not None:
            if self.command_view:
                self.command_view.dismiss()
            else:
                self.command_view.show_last_message()
            return True
        return self.app.text_commander.do_command(self, selector)

    def handle_link(self, link, meta=False):
        """Handle clicked hyperlink

        :param link: Link URL string.
        :param meta: Command key was pressed if true. Default false.
        """
        try:
            url = urlparse(link)
        except Exception:
            log.warn("cannot parse: %r", link, exc_info=True)
            return False
        # TODO allow extensions to hook URL handling?
        if url.scheme != "xt":
            return False
        if url.netloc == "open":
            self.window.open_url(url, link, not meta)
            return True
        if url.netloc == "preferences":
            self.window.app.open_config_file()
            return True
        log.warn("unhandled URL: %s", link)
        return False


class CommandOutput:

    editor = WeakProperty()

    def __init__(self, output_view, editor):
        self._output_view = output_view
        self.editor = editor
        self._process = None

    @property
    def process(self):
        return self._process
    @process.setter
    def process(self, value):
        self._process = value
        if self.output_view is not None:
            self.output_view.is_waiting(value is not None)

    @property
    def output_view(self):
        return self._output_view
    @output_view.setter
    def output_view(self, value):
        self._output_view = value
        if value is not None:
            value.is_waiting(self.process is not None)

    def append_message(self, *args, **kw):
        self.output_view.append_message(*args, **kw)

    def kill_process(self):
        if self.process is not None:
            self.process.terminate()
            self.process_completed()

    def process_completed(self):
        self.process = None
        self.output_view = None
        self.editor.stop_output()


class Editor(CommandSubject):
    """Editor

    Reference graph:
        strong:
            app -> window -> KVOProxy(project) -> KVOProxy(self)
        weak:
            self -> project -> window -> app
    """

    _project = WeakProperty()
    is_leaf = True

    def __init__(self, project, *, document=None, path=None, state=None):
        if state is not None:
            if "internal" in state:
                app = project.window.app
                document = app.get_internal_document(state["internal"])
            else:
                assert document is None, (state, document)
                assert path is None, (state, path)
                path = state["path"]
        if path is not None:
            assert document is None, (path, document)
        if document is None:
            document = project.window.app.document_with_path(path)
            assert document is not None, (project, path, state)
        self.editors = KVOList.alloc().init()
        self.id = next(DocumentController.id_gen)
        self._project = project
        self.document = document
        self.proxy = KVOProxy(self)
        self.main_view = None
        self.text_view = None
        self.scroll_view = None
        self._goto_line = None
        self.line_numbers = LineNumbers(self.text)
        props = document.props
        self.kvolink = KVOLink([
            (props, "is_dirty", self.proxy, "is_dirty"),
            (props, "indent_mode", self.proxy, "indent_mode"),
            (props, "indent_size", self.proxy, "indent_size"),
            (props, "newline_mode", self.proxy, "newline_mode"),
            (props, "syntaxdef", self.proxy, "syntaxdef"),
            (props, "character_encoding", self.proxy, "character_encoding"),
            (props, "highlight_selected_text", self.proxy, "highlight_selected_text"),
        ])
        if state is not None:
            self.edit_state = state

        self.undo_manager.on(self.on_dirty_status_changed)

    def icon(self):
        return self.document.icon()

    @property
    def app(self):
        return self.project.window.app

    @property
    def project(self):
        """Get/set this editor's project

        The setter will remove this editor from it's previous project's
        editors if it is found there.
        """
        return self._project
    @project.setter
    def project(self, new):
        old = getattr(self, "_project", None)
        if old is not None:
            old.remove(self)
        self._project = new

    @property
    def window(self):
        return self.project.window

    @property
    def name(self):
        return self.document.name

    @property
    def text(self):
        return self.document.text_storage

    @property
    def undo_manager(self):
        return self.document.undo_manager

    @property
    def file_path(self):
        return self.document.file_path
    @file_path.setter
    def file_path(self, value):
        self.document.file_path = value

    @property
    def selection(self):
        if self.text_view is None:
            return None
        return self.text_view.selectedRange()
    @selection.setter
    def selection(self, rng):
        self.text_view.select(rng)

    @property
    def is_dirty(self):
        return self.document.is_dirty()

    def on_dirty_status_changed(self, dirty):
        self.window.on_dirty_status_changed(self, dirty)

    def short_path(self, name=True):
        path = self.file_path
        if not name:
            path = os.path.dirname(path)
        if self.project.path and path.startswith(self.project.path + os.path.sep):
            path = path[len(self.project.path) + 1:]
        return user_path(path)

    def dirname(self):
        if self.file_path and os.path.isabs(self.file_path):
            return os.path.dirname(self.file_path)
        return self.project.dirname()

    def save(self, prompt=False, callback=(lambda saved:None)):
        """Save the document to disk

        Possible UI interactions:
        - get file path if the file has not been saved.
        - ask to overwrite existing file if file has not been opened from or
          saved to its current file_path before.
        - ask to overwrite if the file has changed on disk and there has been
          no subsequent prompt to reload.

        :param prompt: Optional boolean argument, defaults to False.
        Unconditionally prompt for new save location if True.
        :param callback: Optional callback to be called with the save result
        of the save operation (True if successful else False).
        """
        document = self.document
        window = self.window
        def save_with_path(path):
            saved = False
            try:
                if path is not None:
                    if document.file_path != path:
                        document.file_path = path
                    document.save()
                    saved = True
                    if self.text_view is not None:
                        self.text_view.breakUndoCoalescing()
            except DocumentError as err:
                log.error(err)
            except Exception:
                log.exception("cannot save %s", path)
            finally:
                callback(saved)
        if prompt or not document.file_exists():
            window.save_document_as(self, save_with_path)
        elif document.file_changed_since_save():
            window.prompt_to_overwrite(self, save_with_path)
        else:
            save_with_path(document.file_path)

    def should_close(self, callback):
        """Check if the document can be closed

        Prompt for save, discard, or cancel if the document is dirty and call
        ``callback(<should close>)`` once the appropriate action has been
        performed. Otherwise call ``callback(True)``. The callback may raise an
        exception; if it does it must be allowed to propagate to continue the
        termination sequence.
        """
        if not self.is_dirty:
            callback(True)
            return
        def save_discard_or_cancel(save):
            """Save, discard, or cancel the current operation

            :param save: True => save, False => discard, None => cancel
            """
            if save:
                self.save(callback=callback)
            else:
                callback(save is not None)
        document = self.document
        save_as = not document.has_real_path()
        self.window.prompt_to_close(self, save_discard_or_cancel, save_as)

    def set_main_view_of_window(self, view, window):
        frame = view.bounds()
        if self.scroll_view is None:
            self.main_view = setup_main_view(self, frame)
            self.scroll_view = self.main_view.top
            self.command_view = self.main_view.bottom
            self.text_view = self.scroll_view.documentView() # HACK deep reach
            self.set_text_attributes()
            self.reset_edit_state()
            self.on_selection_changed(self.text_view)
            if self._goto_line is not None:
                self.text_view.goto_line(self._goto_line)
        else:
            self.main_view.setFrame_(frame)
        view.addSubview_(self.main_view)
        window.makeFirstResponder_(self.text_view)
        self.document.update_syntaxer()
        self.document.check_for_external_changes(window)

    def focus(self):
        if self is not self.window.current_editor:
            self.window.current_editor = self
        elif self.text_view is not None:
            self.text_view.focus()

    def set_text_attributes(self, attrs=None):
        view = self.text_view
        if view is None:
            return
        if attrs is None:
            attrs = self.document.default_text_attributes()
        ruler = self.scroll_view.verticalRulerView() # HACK deep reach
        view.font_smoothing = ruler.font_smoothing = self.document.font.smooth
        view.setTypingAttributes_(attrs)
        view.setDefaultParagraphStyle_(attrs[ak.NSParagraphStyleAttributeName])
        self.scroll_view.setBackgroundColor_(self.app.theme.background_color)
        del view.margin_params
        font = attrs[ak.NSFontAttributeName]
        half_char = font.advancementForGlyph_(ord("8")).width / 2
        ruler.invalidateRuleThickness()
        view.setTextContainerInset_(fn.NSMakeSize(half_char, half_char)) # width/height
        view.setNeedsDisplay_(True)
        if self.window.current_editor is self:
            self.document.update_syntaxer()

    def put(self, text, rng, select=False):
        """Put text in range

        :param text: text to replace range.
        :param rng: range of text to replace.
        :param select: select the edited text if true.
        :returns: true if the change was applied, otherwise false.
        """
        should_change = (
            self.text_view is None or
            self.text_view.shouldChangeTextInRange_replacementString_(rng, text)
        )
        if should_change:
            self.text[rng] = text
            if self.text_view is not None:
                if select:
                    self.selection = (rng[0], len(text))
                self.text_view.didChangeText()
            return True
        log.warn("cannot change text in range %s", rng)
        return False

    @property
    def soft_wrap(self):
        if self.text_view is None:
            return self.edit_state["soft_wrap"]
        return self.text_view.soft_wrap()
    @soft_wrap.setter
    def soft_wrap(self, value):
        if self.text_view is None:
            state = getattr(self, "_state", {})
            state["soft_wrap"] = value
            self._state = state
            return
        self.text_view.soft_wrap(value)

    @document_property
    def indent_size(self, new, old):
        mode = self.document.indent_mode
        if mode == const.INDENT_MODE_TAB:
            self.change_indentation(mode, old, mode, new, True)
        elif new != old:
            self.document.props.indent_size = new

    @document_property
    def indent_mode(self, new, old):
        if new != old:
            self.document.props.indent_mode = new

    @document_property
    def newline_mode(self, new, old):
        undoman = self.undo_manager
        if not (undoman.isUndoing() or undoman.isRedoing()):
            replace_newlines(self, const.EOLS[new])
        self.document.props.newline_mode = new

        def undo():
            self.proxy.newline_mode = old
        register_undo_callback(undoman, undo)

    @document_property
    def syntaxdef(self, new, old):
        self.document.syntaxdef = new

    @document_property
    def character_encoding(self, new, old):
        self.document.character_encoding = new

    @document_property
    def font(self, new, old):
        self.document.font = new

    @document_property
    def highlight_selected_text(self, new, old):
        if not new:
            self.finder.mark_occurrences("")
        self.document.highlight_selected_text = new

    @document_property
    def updates_path_on_file_move(self, new, old):
        self.document.updates_path_on_file_move = new

    def change_indentation(self, old_mode, old_size, new_mode, new_size, convert_text):
        if convert_text:
            old_indent = "\t" if old_mode == const.INDENT_MODE_TAB else (" " * old_size)
            new_indent = "\t" if new_mode == const.INDENT_MODE_TAB else (" " * new_size)
            change_indentation(self.text_view, old_indent, new_indent, new_size)
        if old_mode != new_mode:
            self.document.props.indent_mode = new_mode
        if old_size != new_size:
            self.document.props.indent_size = new_size
        if convert_text or convert_text is None:
            def undo():
                self.change_indentation(new_mode, new_size, old_mode, old_size, None)
            register_undo_callback(self.undo_manager, undo)

    @property
    def edit_state(self):
        if self.text_view is not None:
            sel = self.selection
            sp = self.scroll_view.documentVisibleRect().origin
            state = dict(
                selection=[sel.location, sel.length],
                scrollpoint=[sp.x, sp.y],
                soft_wrap=self.soft_wrap,
            )
        else:
            state = dict(getattr(self, "_state", {}))
            state.setdefault("soft_wrap", self.app.config["soft_wrap"])
        upfm_default = bool(self.app.config["updates_path_on_file_move"])
        if bool(self.updates_path_on_file_move) != upfm_default:
            state["updates_path_on_file_move"] = False
        if self.document is self.app.errlog.document \
                and not self.document.has_real_path():
            state["internal"] = "errlog"
        else:
            assert self.file_path is not None, repr(self)
            state["path"] = str(self.file_path)
            state.pop("internal", None)
        return state
    @edit_state.setter
    def edit_state(self, state):
        if self.text_view is not None:
            point = state.get("scrollpoint", [0, 0])
            self.point = point
            sel = state.get("selection", [0, 0])
            self.soft_wrap = state.get("soft_wrap", self.app.config["soft_wrap"])
            # HACK text_view.scrollPoint_ does not work without this
            char_index, ignore = self.text_view.layoutManager() \
                .characterIndexForPoint_inTextContainer_fractionOfDistanceBetweenInsertionPoints_(
                    (0.0, point[1] + self.text_view.bounds().size.height),
                    self.text_view.textContainer(), None)
            length = self.document.text_storage.length()
            char_index = min(char_index, length - 1)
            self.line_numbers[char_index] # count lines for ruler view
            self.scroll_view.verticalRulerView().invalidateRuleThickness()
            self.text_view.scrollPoint_(point)
            if sel[0] > length:
                sel = (length, 0)
            elif sel[0] + sel[1] > length:
                sel = (sel[0], length - sel[0])
            self.text_view.setSelectedRange_(sel)
        else:
            self._state = state
        if "updates_path_on_file_move" in state:
            self.proxy.updates_path_on_file_move = bool(state["updates_path_on_file_move"])

    def reset_edit_state(self):
        state = getattr(self, "_state", None)
        if state is not None:
            self.edit_state = state
            del self._state
        else:
            self.soft_wrap = self.app.config["soft_wrap"]

    def goto_line(self, line):
        if self.text_view is None:
            self._goto_line = line
        else:
            self.text_view.goto_line(line)

    def interactive_close(self, do_close):
        """Close this editor if the user agrees to do so

        :param do_close: A function to be called to close the document.
        """
        def last_editor_of_document():
            return all(editor is self
                for editor in self.app.iter_editors_of_document(self.document))
        if self.is_dirty and last_editor_of_document():
            def callback(should_close):
                if should_close:
                    do_close()
            self.should_close(callback)
        else:
            do_close()

    def close(self):
        project = self.project
        doc = self.document
        self.undo_manager.off(self.on_dirty_status_changed)
        # remove from window.dirty_editors if present
        project.window.on_dirty_status_changed(self, False)
        self.stop_output()
        self.project = None # removes editor from project.editors
        if self.text_view is not None and doc.text_storage is not None:
            doc.text_storage.removeLayoutManager_(self.text_view.layoutManager())
        if all(e is self for e in doc.app.iter_editors_of_document(doc)):
            doc.close()
        self.document = None
        if self.main_view is not None:
            teardown_main_view(self.main_view)
            self.main_view = None
        self.text_view = None
        self.scroll_view = None
        self.command_view = None
        self.proxy = None
        self.line_numbers.close()

    def __repr__(self):
        name = 'N/A' if self.document is None else self.name
        return '<%s 0x%x name=%s>' % (type(self).__name__, id(self), name)

    # TextView delegate ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @property
    def finder(self):
        try:
            finder = self._finder
        except Exception:
            finder = self._finder = Finder(
                (lambda:self),
                FindOptions(ignore_case=False, wrap_around=False),
                self.app,
            )
        return finder

    @noraise
    def on_selection_changed(self, textview):
        from editxt.platform.text import composed_length
        lines = self.line_numbers
        text = lines.text
        length = len(text)
        range = textview.selectedRange()
        index = min(range.location, length) if length else 0
        try:
            line = lines[index]
        except IndexError:
            if index != length or not lines.end:
                log.warn("expected index (%s) to equal length (%s) or "
                         "newline (%s lines)", 
                        index, length, lines.end,
                        lines.newline_at_end, len(lines))
            line = len(lines)
        line_index = self.line_numbers.index_of(line)
        if line_index < index:
            col = composed_length(text[line_index:index])
        else:
            col = 0
        sel = composed_length(text[range])
        self.scroll_view.status_view.updateLine_column_selection_(line, col, sel)

        if self.document.highlight_selected_text:
            self.highlight_selection(text, range)

    @debounce
    def highlight_selection(self, text, range):
        if self.project is None:
            return
        ftext = text[range]
        if len(ftext.strip()) < 3 or " " in ftext:
            ftext = ""
        self.finder.mark_occurrences(ftext)
