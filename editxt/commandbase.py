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
import objc
import os
import re
import time
import weakref

from AppKit import *
from Foundation import *

import editxt.constants as const
from editxt import app
from editxt.commandparser import Options
from editxt.controls.alert import Caller
from editxt.util import KVOProxy, KVOLink

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


class BaseCommandController(NSWindowController):
    """abstract window controller for text commands"""

    OPTIONS_CLASS = Options
    #NIB_NAME = "NibFilename"       # abstract attribute
    #OPTIONS_DEFAULTS = {}          # abstract attribute
    #OPTIONS_key = "named_options"  # optional abstract attribute

    @classmethod
    def create(cls):
        obj = cls.alloc().initWithWindowNibName_(cls.NIB_NAME)
        obj.load_options()
        return obj

    @classmethod
    def shared_controller(cls):
        try:
            return cls.__dict__["_shared_controller"]
        except KeyError:
            cls._shared_controller = ctl = cls.create()
        return ctl

    def initWithWindowNibName_(self, name):
        self = super(BaseCommandController, self).initWithWindowNibName_(name)
        self.setWindowFrameAutosaveName_(name)
        if not hasattr(self, "OPTIONS_KEY"):
            self.OPTIONS_KEY = self.NIB_NAME + "_options"
        self.opts = KVOProxy(self.OPTIONS_CLASS())
        return self

    def load_options(self):
        defaults = NSUserDefaults.standardUserDefaults()
        data = defaults.dictionaryForKey_(self.OPTIONS_KEY)
        if data is None:
            data = {}
        opts = self.opts
        for key, value in self.OPTIONS_DEFAULTS.iteritems():
            setattr(opts, key, data.get(key, value))

    def save_options(self):
        opts = self.opts
        data = dict((key, getattr(opts, key))
            for key, value in self.OPTIONS_DEFAULTS.iteritems())
        defaults = NSUserDefaults.standardUserDefaults()
        defaults.setObject_forKey_(data, self.OPTIONS_KEY)

    def options(self):
        return self.opts

    def setOptions_(self, value):
        self.opts = value


class SheetController(BaseCommandController):
    """abstract window controller for sheet-based text command"""

    @classmethod
    def create_with_textview(cls, textview):
        obj = cls.alloc().initWithWindowNibName_(cls.NIB_NAME)
        obj.textview = textview
        obj.load_options()
        return obj

    def begin_sheet(self, sender):
        self.caller = Caller.alloc().init(self.sheet_did_end)
        NSApp.beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(
            self.window(), self.textview.window(), self.caller,
            "alertDidEnd:returnCode:contextInfo:", 0)

    def sheet_did_end(self, code):
        self.window().orderOut_(None)

    def cancel_(self, sender):
        NSApp.endSheet_returnCode_(self.window(), 0)


class PanelController(BaseCommandController):
    """abstract window controller for panel-based text command"""
