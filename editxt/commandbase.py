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

from AppKit import *
from Foundation import *

import editxt.constants as const
from editxt import app
from editxt.controls.alert import Caller
from editxt.util import KVOProxy, KVOLink

log = logging.getLogger(__name__)


class Options(object):
    """default options class"""


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
