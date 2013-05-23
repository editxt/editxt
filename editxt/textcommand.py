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
import logging
from collections import defaultdict
from itertools import count

from AppKit import *
from Foundation import *

from editxt.commandparser import ArgumentError

log = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextCommandController

class TextCommandController(object):

    def __init__(self, menu):
        self.tagger = count()
        self.menu = menu
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

    def lookup_full_command(self, command_text):
        for command in self.lookup_full_commands:
            try:
                args = command.arg_parser.parse(command_text)
            except ArgumentError:
                continue
            except Exception:
                log.warn('cannot parse command: %s', command_text, exc_info=True)
                continue
            if args is not None:
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

    def load_commands(self):
        for path, reg in self.iter_command_modules():
            for command in reg.get("text_menu_commands", []):
                self.add_command(command, path)
            self.input_handlers.update(reg.get("input_handlers", {}))

    def add_command(self, command, path):
        if command.title is not None:
            command.__tag = tag = self.tagger.next()
            hotkey, keymask = self.validate_hotkey(command.hotkey)
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                command.title, "performTextCommand:", hotkey)
            item.setKeyEquivalentModifierMask_(keymask)
            item.setTag_(tag)
            # HACK tag will not be the correct index if an item is ever removed
            self.menu.insertItem_atIndex_(item, tag)
            self.commands[tag] = command
        if command.lookup_with_arg_parser:
            self.lookup_full_commands.insert(0, command)
        if command.names:
            for alias in command.names:
                if not isinstance(alias, basestring) or ' ' in alias:
                    log.warn('invalid command alias (%r) for %s loaded from %s',
                        alias, command, path)
                else:
                    self.commands[alias] = command

    def validate_hotkey(self, value):
        if value is not None:
            assert len(value) == 2, "invalid hotkey tuple: %r" % (value,)
            # TODO check if a hot key is already in use; ignore if it is
            return value
        return u"", 0

    def is_textview_command_enabled(self, textview, sender):
        command = self.commands.get(sender.tag())
        if command is not None:
            try:
                return command.is_enabled(textview, sender)
            except Exception:
                log.error("%s.is_enabled failed", type(command).__name__, exc_info=True)
        return False

    def do_textview_command(self, textview, sender):
        command = self.commands.get(sender.tag())
        if command is not None:
            try:
                command(textview, sender, None)
            except Exception:
                log.error("%s.execute failed", type(command).__name__, exc_info=True)

    def do_textview_command_by_selector(self, textview, selector):
        #log.debug(selector)
        callback = self.input_handlers.get(selector)
        if callback is not None:
            try:
                callback(textview, None, None)
                return True
            except Exception:
                log.error("%s failed", callback, exc_info=True)
        return False
