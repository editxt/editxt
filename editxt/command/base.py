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

from AppKit import *
from Foundation import *

from editxt.commandparser import CommandParser, Options, VarArgs
from editxt.controls.alert import Caller
from editxt.util import KVOProxy

log = logging.getLogger(__name__)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Text command system interface
"""
The primary interface for loading text commands into EditXT is a module-level
function that returns a list of command functions provided by the module:

def load_commands():
    return [decorated_text_command, ...]
"""


def command(func=None, name=None, title=None, hotkey=None,
            is_enabled=None, arg_parser=None, lookup_with_arg_parser=False):
    """Text command decorator

    Text command signature: `text_command(textview, sender, args)`
    Both `sender` and `args` will be `None` in some contexts.

    :param name: A name that can be typed in the command bar to invoke the
        command. Defaults to the decorated callable's `__name__`.
    :param title: The command title displayed in Text menu. Not in menu if None.
    :param hotkey: Preferred command hotkey tuple: `(<key char>, <key mask>)`.
        Ignored if title is None.
    :param is_enabled: A callable that returns a boolean value indicating if
        the command is enabled in the Text menu. Always enabled if None.
        Signature: `is_enabled(textview, sender)`.
    :param arg_parser: An object inplementing the `CommandParser` interface.
        Defaults to `CommandParser(VarArgs("args"))`.
    :param lookup_with_arg_parser: If True, use the `arg_parser.parse` to
        lookup the command. The parser should return None if it receives
        a text string that cannot be parsed.
    """
    if isinstance(name, basestring):
        name = name.split()
    def command_decorator(func):
        func.is_text_command = True
        func.name = name[0] if name else func.__name__
        func.names = name or [func.__name__]
        func.title = title
        func.hotkey = hotkey
        func.is_enabled = is_enabled or (lambda textview, sender: True)
        func.arg_parser = arg_parser or CommandParser(VarArgs("args"))
        func.lookup_with_arg_parser = lookup_with_arg_parser
        return func
    if func is None:
        return command_decorator
    return command_decorator(func)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Base classes for GUI command controllers


class BaseCommandController(NSWindowController):
    """abstract window controller for text commands"""

    OPTIONS_FACTORY = Options       # A callable that creates default options.
                                    # If this is a function, it should accept
                                    # one arguemnt (`self`).
    #NIB_NAME = "NibFilename"       # Abstract attribute.
    #OPTIONS_key = "named_options"  # Optional abstract attribute.

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
        self.opts = KVOProxy(self.OPTIONS_FACTORY())
        self.default_option_keys = [k for k, v in self.opts]
        return self

    def load_options(self):
        defaults = NSUserDefaults.standardUserDefaults()
        data = defaults.dictionaryForKey_(self.OPTIONS_KEY)
        if data is None:
            data = {}
        opts = self.opts
        for key, value in opts:
            setattr(opts, key, data.get(key, value))

    def save_options(self):
        data = {k: getattr(self.opts, k) for k in self.default_option_keys}
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
