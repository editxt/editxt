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
import sys
import traceback
from collections import defaultdict
from itertools import count

import AppKit as ak
import Foundation as fn

import editxt.constants as const
from editxt.command.base import CommandError
from editxt.command.parser import ArgumentError, CompleteWord
from editxt.commands import load_commands
from editxt.history import History
from editxt.util import WeakProperty

log = logging.getLogger(__name__)


class CommandBar(object):

    window = WeakProperty()
    text_commander = WeakProperty()

    def __init__(self, window, text_commander):
        self.window = window
        self.text_commander = text_commander
        self.history_view = None

    def activate(self, text=""):
        # abstract to a PyObjC-specific subclass when implementing other frontend
        editor = self.window.current_editor
        if editor is None:
            ak.NSBeep()
            return
        editor.command_view.activate(self, text)

    def parser(self, command):
        parser = command.arg_parser
        editor = self.window.current_editor
        return command.arg_parser.with_context(editor)

    def execute(self, text):
        self.reset()
        if not text.strip():
            return
        cmdstr, space, argstr = text.lstrip(" ").partition(" ")
        editor = self.window.current_editor
        if editor is None:
            ak.NSBeep()
            return
        command = self.text_commander.lookup(cmdstr)
        if command is not None:
            try:
                args = self.parser(command).parse(argstr)
            except Exception:
                msg = 'argument parse error: {}'.format(argstr)
                self.message(msg, exc_info=True)
                return
        else:
            argstr = text
            command, args = self.text_commander.lookup_full_command(argstr)
            if command is None:
                self.message('unknown command: {}'.format(argstr))
                return
        if args is None:
            self.message('invalid command arguments: {}'.format(argstr))
            return
        try:
            message = command(editor, self, args)
        except CommandError as err:
            self.message(err)
        except Exception:
            self.message('error in command: {}'.format(command), exc_info=True)
        else:
            if not text.startswith(" "):
                self.text_commander.history.append(text)
            if message is not None:
                self.message(message, msg_type=const.INFO)

    def _find_command(self, text):
        """Get a tuple (command, argument_string)

        :returns: A tuple ``(command, argument_string)``. ``command`` will be
        ``None`` if no matching command is found.
        """
        if not text:
            return None, text
        cmdstr, space, argstr = text.partition(" ")
        command = self.text_commander.lookup(cmdstr)
        if command is None:
            argstr = text
            command, a = self.text_commander.lookup_full_command(argstr, False)
        return command, argstr

    def get_placeholder(self, text):
        """Get arguments placeholder text"""
        command, argstr = self._find_command(text)
        if command is not None:
            try:
                placeholder = self.parser(command).get_placeholder(argstr)
            except Exception:
                log.debug("get_placeholder failed", exc_info=True)
                placeholder = None
            if placeholder:
                if text and not argstr and not text.endswith(" "):
                    return " " + placeholder
                return placeholder
        return ""

    def get_completions(self, text):
        """Get completions for the word at the end of the given command string

        :param text: Command string.
        :returns: A tuple consisting of a list of potential completions
        and/or replacements for the word at the end of the command text,
        and the index of the item that should be selected (-1 for no
        selection).
        """
        if " " not in text:
            editor = self.window.current_editor
            def is_enabled(command, cache={}):
                try:
                    result = cache[command]
                except KeyError:
                    try:
                        result = cache[command] = command.is_enabled(editor, self)
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
            index = 0 if words else -1
        else:
            command, argstr = self._find_command(text)
            if command is not None:
                try:
                    words = self.parser(command).get_completions(argstr)
                except Exception:
                    log.debug("get_completions failed", exc_info=True)
                    words = []
                index = (0 if words else -1)
            else:
                words, index = [], -1
        return words, index

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
        index = start - len(word)
        if index < 0:
            index = 0
        if isinstance(word, CompleteWord) and word.overlap is not None:
            index = start - word.overlap
        else:
            while index < start:
                if word.startswith(text[index:start]):
                    break
                index += 1
        assert start >= index, (text, start, index)
        replace = (index, start - index + length)
        assert len(word) - (start - index) >= 0, (word, start, index)
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

    def get_history(self, current_text, forward=False):
        if self.history_view is None:
            self.history_view = self.text_commander.history.view()
        return self.history_view.get(current_text, forward)

    def message(self, text, exc_info=None, msg_type=const.ERROR):
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
                ak.NSBeep()
        else:
            editor.message(msg, msg_type=msg_type)

    def reset(self):
        view, self.history_view = self.history_view, None
        if view is not None:
            self.text_commander.history.discard_view(view)


class TextCommandController(object):

    def __init__(self, history):
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

    def add_command(self, command, path, menu):
        if command.title is not None:
            command.__tag = tag = next(self.tagger)
            hotkey, keymask = self.validate_hotkey(command.hotkey)
            item = ak.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                command.title, "doCommand:", hotkey)
            item.setKeyEquivalentModifierMask_(keymask)
            item.setTag_(tag)
            # HACK tag will not be the correct index if an item is ever removed
            menu.insertItem_atIndex_(item, tag)
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

    def validate_hotkey(self, value):
        if value is not None:
            assert len(value) == 2, "invalid hotkey tuple: %r" % (value,)
            # TODO check if a hot key is already in use; ignore if it is
            return value
        return "", 0

    def is_command_enabled(self, editor, sender):
        command = self.commands.get(sender.tag())
        if command is not None:
            try:
                return command.is_enabled(editor, sender)
            except Exception:
                log.error("%s.is_enabled failed", type(command).__name__, exc_info=True)
        return False

    def do_command(self, editor, sender):
        command = self.commands.get(sender.tag())
        if command is not None:
            try:
                command(editor, sender, None)
            except Exception:
                log.error("%s.execute failed", type(command).__name__, exc_info=True)

    def do_command_by_selector(self, editor, selector):
        #log.debug(selector)
        callback = self.input_handlers.get(selector)
        if callback is not None:
            try:
                callback(editor, None, None)
                return True
            except Exception:
                log.error("%s failed", callback, exc_info=True)
        return False


CommandHistory = History
