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
import json
import logging
import weakref
from collections import defaultdict
from itertools import count
from os.path import exists, join

from AppKit import *
from Foundation import *

from editxt import app
from editxt.commandparser import ArgumentError
from editxt.commands import load_commands

log = logging.getLogger(__name__)


class CommandBar(object):

    def __init__(self, editor):
        self._editor = weakref.ref(editor)

    @property
    def editor(self):
        return self._editor()

    def activate(self):
        # abstract to a PyObjC-specific subclass when implementing other frontend
        view = self.editor.current_view
        if view is None:
            NSBeep()
            return
        view.scroll_view.commandView.activate(self)

    def execute(self, text):
        args = text.split()
        if not args:
            return
        doc_view = self.editor.current_view
        if doc_view is None:
            NSBeep()
            return
        command = app.text_commander.lookup(args[0])
        if command is not None:
            argstr = text[len(args[0]) + 1:]
            try:
                args = command.arg_parser.parse(argstr)
            except Exception:
                msg = 'argument parse error: {}'.format(argstr)
                self.message(msg, exc_info=True)
                return
        else:
            argstr = text
            command, args = app.text_commander.lookup_full_command(argstr)
            if command is None:
                self.message('unknown command: {}'.format(argstr))
                return
        if args is None:
            self.message('invalid command arguments: {}'.format(argstr))
            return
        try:
            command(doc_view.text_view, self, args)
        except Exception:
            self.message('error in command: {}'.format(command), exc_info=True)

    def _find_command(self, text):
        """Get a tuple (command, argument_string)

        :returns: A tuple ``(command, argument_string)``. ``command`` will be
        ``None`` if no matching command is found.
        """
        args = text.split()
        if not args:
            return None, text
        command = app.text_commander.lookup(args[0])
        if command is not None:
            argstr = text[len(args[0]) + 1:]
        else:
            argstr = text
            command, args = app.text_commander.lookup_full_command(argstr)
        return command, argstr

    def get_placeholder(self, text):
        """Get arguments placeholder text"""
        command, argstr = self._find_command(text)
        if command is not None:
            placeholder = command.arg_parser.get_placeholder(argstr)
            prefix = " " if placeholder and not text.endswith(" ") else ""
            return prefix + placeholder
        return ""

    def get_completions(self, text):
        """Get completions for the word at the end of the given command string

        :param text: Command string.
        :returns: A tuple consisting of a list of potential completions
        and/or replacements for the word at the end of the command text,
        and the index of the item that should be selected (-1 for no
        selection).
        """
        if len(text.split()) < 2 and not text.endswith(" "):
            words = sorted(name
                for name in app.text_commander.commands
                if isinstance(name, basestring) and name.startswith(text))
            index = 0 if words else -1
        else:
            command, argstr = self._find_command(text)
            if command is not None:
                words = command.arg_parser.get_completions(argstr)
                index = (0 if words else -1)
            else:
                words, index = [], -1
        return words, index

    def message(self, text, exc_info=None):
        log.info(text, exc_info=exc_info)
        NSBeep()



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


class CommandHistory(object):

    INDEX_FILENAME = "history-index.json"
    FILENAME_PATTERN = "history-{}.txt"

    def __init__(self, store_dir, page_size=100, max_pages=10):
        self.store_dir = store_dir
        self.page_size = page_size
        self.max_pages = max_pages
        self.pages = None
        self.zeropage = None
        self.zerofile = None

    def _initialize(self):
        self.pages = []
        index_file = join(self.store_dir, self.INDEX_FILENAME)
        if exists(index_file):
            try:
                with open(index_file) as fh:
                    self.pages = pages = json.load(fh)
                assert all(isinstance(p, unicode) for p in pages), \
                    repr(pages)
            except Exception:
                log.warn("cannot load %s", index_file, exc_info=True)
        if len(self.pages) < self.max_pages:
            for n in xrange(self.max_pages):
                filename = self.FILENAME_PATTERN.format(n)
                if filename not in self.pages:
                    self.pages.append(filename)
                if len(self.pages) == self.max_pages:
                    break
        elif len(self.pages) > self.max_pages:
            del self.pages[self.max_pages:]
        assert len(self.pages) == self.max_pages, repr(self.pages)
        self.zerofile = self.pages[0]
        self.zeropage = next(self.iter_pages(0))
        zeropath = join(self.store_dir, self.zerofile)
        if exists(zeropath) and not self.zeropage:
            with open(zeropath, "wb") as fh:
                pass # truncate corrupt page file

    def iter_pages(self, start=1):
        def is_command_list(page):
            return isinstance(page, list) and all(
                isinstance(it, basestring) for it in page)
        assert start > -1, start
        for pagefile in self.pages[start:]:
            pagepath = join(self.store_dir, pagefile)
            if exists(pagepath):
                try:
                    with open(pagepath) as fh:
                        page = [json.loads(line.rstrip("\n")) for line in fh]
                except Exception:
                    log.warn("cannot load %s", pagepath, exc_info=True)
                yield (page if is_command_list(page) else [])
            else:
                yield []

    def __iter__(self):
        if self.zeropage is None:
            self._initialize()
        for item in reversed(self.zeropage):
            yield item
        for page in self.iter_pages():
            for item in reversed(page):
                yield item

    def append(self, command):
        """Append a command to history

        This causes the history to be saved to disk. If command already
        exists in history it will be moved to the the most recent item,
        and the older item will be removed.

        :param command: Command text.
        """
        if self.zeropage is None:
            self._initialize()
        zero = self.zeropage
        removed = False
        while command in zero:
            zero.remove(command)
            removed = True
        if removed:
            # rewrite entire file because a command was moved
            zero.append(command)
            zeropath = join(self.store_dir, self.zerofile)
            try:
                with open(zeropath, "wb") as fh:
                    for command in zero:
                        json.dump(command, fh)
                        fh.write("\n")
            except Exception:
                log.warn("cannot write to history: %s", zeropath, exc_info=True)
            assert len(zero) <= self.page_size, repr(zero)
            return
        if len(zero) < self.page_size:
            zero.append(command)
            mode = "ab"
        else:
            self.zeropage = zero = [command]
            self.zerofile = self.pages.pop()
            self.pages.insert(0, self.zerofile)
            index_file = join(self.store_dir, self.INDEX_FILENAME)
            try:
                with open(index_file, "wb") as fh:
                    json.dump(self.pages, fh)
            except Exception:
                log.warn("cannot write %s", index_file, exc_info=True)
            mode = "wb"
        zeropath = join(self.store_dir, self.zerofile)
        try:
            with open(zeropath, mode) as fh:
                json.dump(command, fh)
                fh.write("\n")
        except Exception:
            log.warn("cannot write to history: %s", zeropath, exc_info=True)

    def __getitem__(self, index):
        """Get command by index

        :param index: Integer index of command in history.
        :returns: Command text or ``None`` if index does not reference a
        valid item in history.
        """
        if self.zeropage is None:
            self._initialize()
        zero = self.zeropage
        if index < len(zero):
            return zero[len(zero) - index - 1]
        index -= len(zero)
        for page in self.iter_pages():
            if index >= len(page):
                index -= len(page)
                continue
            return page[len(page) - index - 1]
        return None

    def __delitem__(self, index):
        """Remove command from history by index

        :param index: Integer index of command in history.
        """
