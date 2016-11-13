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
import re
import sys
import traceback
from collections import defaultdict
from itertools import count

import AppKit as ak
import Foundation as fn

import editxt.constants as const
from editxt.command.base import CommandError
from editxt.command.parser import ArgumentError, CompleteWord, CompletionsList
from editxt.command.util import has_editor, markdoc
from editxt.commands import load_commands, help
from editxt.config import schema_to_dict
from editxt.events import eventize
from editxt.history import History
from editxt.platform.app import beep
from editxt.platform.events import call_later
from editxt.platform.kvo import KVOList, KVOProxy
from editxt.platform.markdown import AttributedString
from editxt.platform.views import CommandView
from editxt.util import parse_hotkey, WeakProperty

log = logging.getLogger(__name__)


class CommandBar(object):

    window = WeakProperty()
    text_commander = WeakProperty()

    def __init__(self, window, text_commander):
        self.window = window
        self.text_commander = text_commander
        self.history_view = None
        self.failed_command = None
        self.completing = Completing()
        self._cached_parser = (None, None, None)

    def activate(self, text="", select=False):
        editor = self.window.current_editor
        if editor is None:
            beep()
            return
        if not text and self.failed_command:
            text = self.failed_command
            select = True
        self._cached_parser = (None, None, None)
        editor.command_view.activate(self, text, select)
        editor.command_view.__last_completions = [None]

    def on_key_command(self, key, command_view, keys=CommandView.KEYS):
        """Handle key press in command view

        :param key: A command token corresponding to the key that was
        pressed. This is one of the command key contsants defined in
        `editxt.platform.views.CommandView.KEYS`.
        :param view: The CommandView object.
        :returns: True if the command was handled and should not be
        propagated to the text view, otherwise false.
        """
        if key == keys.SELECTION_CHANGED:
            if command_view.completions and not self.completing:
                call_later(0, self.complete, command_view, auto_one=False)
            command_view.completions.select_range = \
                command_view.command_text_selected_range
            return True

        if key == keys.TAB:
            word = command_view.completions.selected_item
            if command_view.completions and not word:
                words = command_view.completions.items
                word = self.common_prefix(words)
                if word:
                    self._auto_complete(command_view, word)
                if len(words) == 1:
                    command_view.completions.items = []
            else:
                self.complete(command_view)
            return True

        if key == keys.UP:
            if command_view.completions:
                command_view.completions.select_prev()
            else:
                self.navigate_history(command_view)
            return True

        if key == keys.DOWN:
            if command_view.completions:
                command_view.completions.select_next()
            else:
                self.navigate_history(command_view, forward=True)
            return True

        if key == keys.ENTER:
            text = command_view.command_text
            # TODO send cursor position instead of len(text)
            if not self.should_insert_newline(text, len(text)):
                command_view.deactivate()
                self.execute(text)
                return True

        if key == keys.ESC:
            if command_view.completions:
                select_range = command_view.completions.select_range
                command_view.completions.items = []
                if select_range is not None:
                    command_view.command_text_selected_range = select_range
            elif command_view.output_text:
                command_view.message("")
            else:
                command_view.deactivate()
            return True

        if key == keys.BACK_TAB:
            # ignore
            return True

        return False

    def complete(self, command_view, auto_one=True):
        text, words, default_index = self._get_completions(command_view)
        if len(words) == 1 and auto_one:
            # replace immediately with single suggestion
            self._auto_complete(command_view, words[0], (len(text), 0))
        else:
            # show auto-complete menu and auto-complete with common prefix
            completions = command_view.completions
            if isinstance(words, CompletionsList):
                completions.title = words.title
            else:
                completions.title = None
            if completions.items != words:
                completions.items = words
            completions.select(default_index)
            word = self.common_prefix(words)
            if word and auto_one:
                self._auto_complete(command_view, word, (len(text), 0))

    def _get_completions(self, command_view):
        range = command_view.command_text_selected_range
        index = range[0]
        text = command_view.command_text
        if index < len(text):
            text = text[:index]
        if command_view.__last_completions[0] == text:
            return command_view.__last_completions
        words, default_index = self.get_completions(text)
        command_view.__last_completions = text, words, default_index
        return text, words, default_index

    def _auto_complete(self, command_view, word, range=None):
        """Auto-complete word replacing range

        :param word: The word to complete.
        :param range: The range of characters to replace.
        :returns: The range of characters that were added.
        """
        if range is None:
            if command_view.completions.select_range is not None:
                range = command_view.completions.select_range
            else:
                range = command_view.command_text_selected_range
        text = command_view.command_text
        word, replace, select = self.auto_complete(text, word, range)
        with self.completing:
            command_view.replace_command_text_range(replace, word)
        command_view.completions.select_range = select

    def propose_completion(self, command_view, items):
        if not items:
            return
        word = items[0]
        with self.completing:
            self._auto_complete(command_view, word)

    def parser(self, command):
        editor = self.window.current_editor
        command_, editor_, parser = self._cached_parser
        if command is not command_ or editor is not editor_ or parser is None:
            parser = command.arg_parser.with_context(editor)
            self._cached_parser = (command, editor, parser)
        return parser

    def execute(self, text):
        self.reset()
        if not text.strip():
            return
        self.failed_command = text
        editor = self.window.current_editor
        if editor is None:
            beep()
            return
        command, index = self._find_command(text)
        if command is None:
            self.message('unknown command: {}'.format(text))
            return
        try:
            args = self.parser(command).parse(text, index)
        except Exception:
            msg = 'parse error: {}'.format(text)
            self.message(msg, exc_info=True)
            return
        finally:
            self._cached_parser = (None, None, None)
        assert args is not None, 'invalid command arguments: {}'.format(text)
        try:
            message = command(editor, args)
        except CommandError as err:
            self.message(err)
        except Exception:
            msg = 'error in command: {} in {}'.format(
                command.__name__,
                command.__module__,
            )
            self.message(msg, exc_info=True)
        else:
            self.failed_command = None
            if not text.startswith(" "):
                self.text_commander.history.append(text)
            if message is not None:
                self.message(message, msg_type=const.INFO)

    def _find_command(self, text):
        """Get a tuple (command, arg_index)

        :returns: A tuple ``(command, arg_index)``. ``command`` will be
        ``None`` if no matching command is found. ``arg_index`` is the index
        of the first argument in the string.
        """
        return self.text_commander.find_command(text)

    def get_placeholder(self, text):
        """Get arguments placeholder text"""
        command, index = self._find_command(text)
        if command is not None:
            try:
                placeholder = self.parser(command).get_placeholder(text, index)
            except Exception:
                log.debug("get_placeholder failed", exc_info=True)
                placeholder = None
            if placeholder:
                if text and index > len(text):
                    return " " + placeholder
                return placeholder
        return ""

    def get_completions(self, text):
        """Get completions for the word at the end of the given command string

        :param text: Command string.
        :returns: A tuple consisting of a list of potential completions
        and/or replacements for the word at the end of the command text,
        and the index of the item that should be selected (`None` for no
        selection).
        """
        if " " not in text:
            editor = self.window.current_editor
            def is_enabled(command, cache={}):
                try:
                    result = cache[command]
                except KeyError:
                    try:
                        result = cache[command] = command.is_enabled(editor)
                    except Exception:
                        log.debug("%s.is_enabled failed",
                                  type(command).__name__, exc_info=True)
                        result = False
                return result
            words = sorted(name
                for name, command in self.text_commander.commands.items()
                if isinstance(name, str)
                    and name.startswith(text)
                    and is_enabled(command))
        else:
            command, index = self._find_command(text)
            if command is not None:
                try:
                    words = self.parser(command).get_completions(text, index)
                except Exception:
                    log.debug("get_completions failed", exc_info=True)
                    words = []
            else:
                words = []
        return words, None

    def common_prefix(self, words):
        """Get the longest common prefix from the given list of words

        :returns: The longest common prefix string.
        """
        prefix = os.path.commonprefix(words)
        if not prefix:
            return ""
        match = (w for w in words if w.startswith(prefix))
        word = next(match)
        if next(match, False):
            # use empty delimiter if there are two or more matching words
            return CompleteWord(
                prefix,
                lambda:"",
                getattr(word, 'start', None),
                getattr(word, 'escape', None),
            )
        return word

    def auto_complete(self, text, word, replace_range):
        """Get auto-complete word and range to be replaced

        All range objects have the semantics of a two-tuple.

        :param text: Command bar text.
        :param word: The word to complete.
        :param replace_range: The range of characters to replace.
        :returns: (<replace text>, <replace range>, <select range>)
        """
        start, length = replace_range
        assert start + length <= len(text), (replace_range, text)
        if getattr(word, 'start', None) is not None:
            index = word.start
        else:
            index = start - len(word)
            if index < 0:
                index = 0
            while index < start:
                if word.startswith(text[index:start]):
                    break
                index += 1
        assert start >= index, (text, start, index, word)
        replace = (index, start - index + length)
        assert len(word) - (start - index) >= 0, (text, start, index, word)
        if len(text) == start + length and word:
            # append delimiter if completing at end of input
            if isinstance(word, CompleteWord):
                word = word.complete()
            else:
                word += " "
        return word, replace, (start, len(word) - (start - index))

    def should_insert_newline(self, text, index):
        """Return true if a newline can be inserted in text at index"""
        return False # TODO implement this

    def navigate_history(self, command_view, forward=False):
        # TODO test
        old_text = command_view.command_text
        text = self.get_history(old_text, forward)
        if text is None:
            beep()
            return
        command_view.command_text = text

    def get_history(self, current_text, forward=False):
        if self.history_view is None:
            self.history_view = self.text_commander.history.view()
        return self.history_view.get(current_text, forward)

    def show_help(self, text):
        """Show help for comment text"""
        command, index = self._find_command(text)
        if command is None:
            message = help.__doc__
        else:
            message = command.__doc__ or ""
            #if index <= len(text) or " " in text:
            #    msg = [message]
            #    # TODO handle exception
            #    msg.append(self.parser(command).get_help(text, index))
            #    message = "\n\n".join(m for m in msg if m.strip())
        if message:
            self.message(markdoc(message), msg_type=const.INFO)
        else:
            beep()

    def message(self, text, exc_info=None, msg_type=const.ERROR):
        if isinstance(text, AttributedString):
            assert not exc_info
            msg = text
        else:
            if exc_info:
                if isinstance(exc_info, (int, bool)):
                    exc_info = sys.exc_info()
                exc = "\n\n" + "".join(traceback.format_exception(*exc_info))
            else:
                exc = ""
            msg = "{}{}".format(text, exc)
        editor = self.window.current_editor
        if editor is None:
            log.info(text, exc_info=exc_info)
            if msg_type == const.ERROR:
                beep()
        else:
            editor.message(msg, msg_type=msg_type)

    def reset(self):
        view, self.history_view = self.history_view, None
        if view is not None:
            self.text_commander.history.discard_view(view)


class CommandManager(object):

    app = WeakProperty()

    def __init__(self, history, app=None):
        self.app = app
        self.history = history
        self.tagger = count()
        self.commands = commands = {}
        self.commands_by_path = bypath = defaultdict(list)
        self.lookup_full_commands = []
        self.input_handlers = {}
        self.editems = editems = {}
#         ntc = menu.itemAtIndex_(1) # New Text Command menu item
#         ntc.setTarget_(self)
#         ntc.setAction_("newTextCommand:")
#         etc = menu.itemAtIndex_(2).submenu() # Edit Text Command menu
        #self.load_commands()

    def lookup(self, alias):
        return self.commands.get(alias)

    def lookup_full_command(self, command_text, full_parse=True):
        # TODO parser.with_context
        for command in self.lookup_full_commands:
            if not full_parse:
                if command.arg_parser.match(command_text):
                    return command, None
                continue
            try:
                args = command.arg_parser.parse(command_text)
            except ArgumentError as err:
                continue
            except Exception:
                log.warn('cannot parse command: %s', command_text, exc_info=True)
                continue
            return command, args
        return None, None

    def find_command(self, text):
        """Find a command for the given command string

        :returns: `(command, index)` where `index` is the index in text
        to start parsing arguments.
        """
        if not text.strip():
            return None, None
        if text.startswith(" "):
            full = text
            text = text.lstrip(" ")
            index = len(full) - len(text)
        else:
            index = 0
        cmdstr = text.split(" ", 1)[0]
        command = self.lookup(cmdstr)
        if command is None:
            command, a = self.lookup_full_command(text, False)
        else:
            index += len(cmdstr) + 1
        return command, index

    def get_completions(self, text, index):
        # TODO implement this
        return []

    @classmethod
    def iter_command_modules(self):
        """Iterate text commands, yield (<command file path>, <command instance>)"""
        # load local (built-in) commands
        yield None, load_commands()

    def load_commands(self, menu):
        for path, reg in self.iter_command_modules():
            for command in reg.get("text_menu_commands", []):
                self.add_command(command, path, menu)
            self.input_handlers.update(reg.get("input_handlers", {}))

    def load_shortcuts(self, menu):
        shortcuts = schema_to_dict(self.app.config.schema["shortcuts"])
        shortcuts.update(self.app.config.lookup("shortcuts", as_dict=True))
        def make_command(text):
            from editxt.command.base import command
            cmd, ignore = self.find_command(text)
            if cmd is None:
                log.warn("unrecognized command: %r", text)
                return None
            @command(is_enabled=None if cmd is None else cmd.is_enabled)
            def exec(editor, args):
                editor.project.window.command.execute(text)
            exec.__name__ = text
            return exec
        def sortkey(item):
            cmd = item[1]
            if isinstance(cmd, str):
                return sys.maxsize, cmd.lstrip()
            name = cmd["name"] if "name" in cmd else cmd["command"].lstrip()
            return cmd.get("rank", sys.maxsize), name
        for hotkey, cmd in sorted(shortcuts.items(), key=sortkey):
            key, mask = parse_hotkey(hotkey)
            if isinstance(cmd, str):
                text = cmd
                name = cmd.lstrip()
            else:
                text = cmd["command"]
                name = cmd["name"] if "name" in cmd else text.lstrip()
            command = make_command(text)
            if key is not None and command is not None:
                tag = self.add_menu_item(menu, name, key, mask)
                self.commands[tag] = command
            elif key is None:
                log.warn("unrecognized hotkey: %s", hotkey)

    def add_command(self, command, path, menu):
        if command.title is not None:
            key, mask = self.validate_hotkey(command.hotkey)
            tag = command.__tag = self.add_menu_item(menu, command.title, key, mask)
            self.commands[tag] = command
        if command.lookup_with_arg_parser:
            self.lookup_full_commands.insert(0, command)
        if command.names:
            for alias in command.names:
                if not isinstance(alias, str) or ' ' in alias:
                    log.warn('invalid command alias (%r) for %s loaded from %s',
                        alias, command, path)
                else:
                    self.commands[alias] = command
        if command.config is not None:
            self.app.config.extend(command.name, command.config)

    def add_menu_item(self, menu, title, key, mask):
        tag = next(self.tagger)
        item = ak.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            title, "doMenuCommand:", key)
        item.setKeyEquivalentModifierMask_(mask)
        item.setTag_(tag)
        menu.addItem_(item)
        return tag

    def validate_hotkey(self, value):
        if value is not None:
            if isinstance(value, str):
                value = parse_hotkey(value)
            assert len(value) == 2, "invalid hotkey tuple: %r" % (value,)
            # TODO check if a hot key is already in use; ignore if it is
            return value
        return "", 0

    def is_menu_command_enabled(self, editor, sender):
        command = self.commands.get(sender.tag())
        if command is not None:
            try:
                return command.is_enabled(editor)
            except Exception:
                log.exception("%s.is_enabled failed", type(command).__name__)
        return False

    def do_menu_command(self, editor, sender):
        command = self.commands.get(sender.tag())
        if command is not None:
            try:
                command(editor, None)
            except Exception:
                log.exception("%s.execute failed", type(command).__name__)

    def do_command(self, editor, selector):
        #log.debug(selector)
        callback = self.input_handlers.get(selector)
        if callback is not None:
            try:
                callback(editor, None)
                return True
            except Exception:
                log.exception("%s failed", callback)
        return False


CommandHistory = History


class AutoCompleteMenu(object):

    class events:
        double_click = eventize.call("view.on.double_click", dispatch=False)
        items_changed = eventize.attr("fire_items_changed")
        selection_changed = eventize.call("setup_selection_changed")

    fire_items_changed = None

    def __init__(self):
        from editxt.platform.views import ListView
        eventize(self)
        self._items = KVOList()
        self.view = ListView(self._items, [{"name": "value", "title": None}])
        self.select_range = None

    def setup_selection_changed(self, callback):
        def adapt(items):
            callback([x.value for x in items])
        self.view.on.selection_changed(adapt)

    @property
    def scroller(self):
        return self.view.scroll

    @property
    def preferred_height(self):
        return self.view.preferred_height

    def __bool__(self):
        return bool(self._items)

    @property
    def title(self):
        return self.view.title

    @title.setter
    def title(self, value):
        self.view.title = value

    @property
    def items(self):
        return [i.value for i in self._items]

    @items.setter
    def items(self, items):
        self._items[:] = [KVOProxy(Completion(v)) for v in items]
        self.select_range = None
        if self.fire_items_changed is not None:
            self.fire_items_changed()

    def select(self, index):
        self.view.select(index)

    def select_next(self):
        index = self.view.selected_row
        if index > -1 and index < len(self._items) - 1:
            self.view.select(index + 1)
        else:
            self.view.select(0)

    def select_prev(self):
        index = self.view.selected_row
        if index > 0:
            self.view.select(index - 1)
        else:
            self.view.select(len(self._items) - 1)

    @property
    def selected_item(self):
        row = self.view.selected_row
        return self._items[row].value if row > -1 else None


class Completion(object):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "{}({!r})".format(type(self).__name__, self.value)


class Completing(object):

    def __init__(self):
        self.level = 0

    def __bool__(self):
        return bool(self.level)

    def __enter__(self):
        self.level += 1

    def __exit__(self, *a):
        self.level -= 1
