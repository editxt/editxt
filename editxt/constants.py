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
import Foundation

UNTITLED_PROJECT_NAME = "untitled project"
# DEFAULT_PROJECT_NAME = u"default.edxt"
PROJECT_EXT = u"edxt"
# PROJECT_TYPE = u"EditXT Project"
TEXT_DOCUMENT = u"public.plain-text"
SYNTAX_DEFS_DIR = "syntax"
SYNTAX_DEF_EXTENSION = ".syntax.py"
STATE_DIR = 'state'
EDITOR_STATE = 'editor-{}.yaml'
LOG_NAME = "EditXT Log"

DOC_ID_LIST_PBOARD_TYPE = "EditXT document id list"
MOVE = "move"
COPY = "copy"

FIND_PANEL_OPTIONS_KEY = "find_panel_options"
WINDOW_SETTINGS_DEFAULTS_KEY = "window_settings"
WINDOW_CONTROLLERS_DEFAULTS_KEY = "window_controllers"

LARGE_NUMBER_FOR_TEXT = 1e7

DEFAULT_RIGHT_MARGIN = 80

LINE_WRAP_NONE = "none"
LINE_WRAP_WORD = "word"
LINE_WRAP_CHAR = "char"

INDENT_MODE_TAB = "tab"
INDENT_MODE_SPACE = "space"

NEWLINE_MODE_UNIX = "LF"
NEWLINE_MODE_MAC = "CR"
NEWLINE_MODE_WINDOWS = "CRLF"
NEWLINE_MODE_UNICODE = "UNICODE"

EOLS = {
    NEWLINE_MODE_UNIX: u"\n",
    NEWLINE_MODE_MAC: u"\r",
    NEWLINE_MODE_WINDOWS: u"\r\n",
    NEWLINE_MODE_UNICODE: u"\u2028",
}

CHARACTER_ENCODINGS = [
    Foundation.NSUTF8StringEncoding,
    Foundation.NSUnicodeStringEncoding,

    Foundation.NSNonLossyASCIIStringEncoding,

    Foundation.NSASCIIStringEncoding,
    Foundation.NSISOLatin1StringEncoding,
    Foundation.NSMacOSRomanStringEncoding,
    Foundation.NSNEXTSTEPStringEncoding,
    Foundation.NSWindowsCP1252StringEncoding,

    Foundation.NSWindowsCP1250StringEncoding,
    Foundation.NSWindowsCP1251StringEncoding,
    Foundation.NSWindowsCP1253StringEncoding,
    Foundation.NSWindowsCP1254StringEncoding,
    Foundation.NSSymbolStringEncoding,
    Foundation.NSJapaneseEUCStringEncoding,
    Foundation.NSShiftJISStringEncoding,
    Foundation.NSISO2022JPStringEncoding,

    Foundation.NSISOLatin2StringEncoding,
#   Foundation.NSProprietaryStringEncoding,
]

PLUS_BUTTON_IMAGE = u"docsbar-plus.png"
PROPS_DOWN_BUTTON_IMAGE = u"docsbar-props-down.png"
PROPS_UP_BUTTON_IMAGE = u"docsbar-props-up.png"

# Images for HoverButtonCell
CLOSE_CLEAN_HOVER = u"close-hover.png"
CLOSE_CLEAN_NORMAL = u"close-normal.png"
CLOSE_CLEAN_PRESSED = u"close-pressed.png"
CLOSE_CLEAN_SELECTED = u"close-selected.png"
CLOSE_DIRTY_HOVER = u"close-dirty-hover.png"
CLOSE_DIRTY_NORMAL = u"close-dirty-normal.png"
CLOSE_DIRTY_PRESSED = u"close-dirty-pressed.png"
CLOSE_DIRTY_SELECTED = u"close-dirty-selected.png"

REGEX_HELP_URL = u"http://docs.python.org/library/re.html#regular-expression-syntax"

