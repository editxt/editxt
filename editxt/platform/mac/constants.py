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
import AppKit as ak


ESCAPE = "cancelOperation:"

class KEY:
    class Modifier:
        Alt = ak.NSAlternateKeyMask
        Command = ak.NSCommandKeyMask
        Control = ak.NSControlKeyMask
        Shift = ak.NSShiftKeyMask

    Left = ak.NSLeftArrowFunctionKey
    Right = ak.NSRightArrowFunctionKey
    Up = ak.NSUpArrowFunctionKey
    Down = ak.NSDownArrowFunctionKey
    UpArrow = ak.NSUpArrowFunctionKey
    DownArrow = ak.NSDownArrowFunctionKey
    LeftArrow = ak.NSLeftArrowFunctionKey
    RightArrow = ak.NSRightArrowFunctionKey
    F1 = ak.NSF1FunctionKey
    F2 = ak.NSF2FunctionKey
    F3 = ak.NSF3FunctionKey
    F4 = ak.NSF4FunctionKey
    F5 = ak.NSF5FunctionKey
    F6 = ak.NSF6FunctionKey
    F7 = ak.NSF7FunctionKey
    F8 = ak.NSF8FunctionKey
    F9 = ak.NSF9FunctionKey
    F10 = ak.NSF10FunctionKey
    F11 = ak.NSF11FunctionKey
    F12 = ak.NSF12FunctionKey
    F13 = ak.NSF13FunctionKey
    F14 = ak.NSF14FunctionKey
    F15 = ak.NSF15FunctionKey
    F16 = ak.NSF16FunctionKey
    F17 = ak.NSF17FunctionKey
    F18 = ak.NSF18FunctionKey
    F19 = ak.NSF19FunctionKey
    F20 = ak.NSF20FunctionKey
    F21 = ak.NSF21FunctionKey
    F22 = ak.NSF22FunctionKey
    F23 = ak.NSF23FunctionKey
    F24 = ak.NSF24FunctionKey
    F25 = ak.NSF25FunctionKey
    F26 = ak.NSF26FunctionKey
    F27 = ak.NSF27FunctionKey
    F28 = ak.NSF28FunctionKey
    F29 = ak.NSF29FunctionKey
    F30 = ak.NSF30FunctionKey
    F31 = ak.NSF31FunctionKey
    F32 = ak.NSF32FunctionKey
    F33 = ak.NSF33FunctionKey
    F34 = ak.NSF34FunctionKey
    F35 = ak.NSF35FunctionKey
    Insert = ak.NSInsertFunctionKey
    Delete = ak.NSDeleteFunctionKey
    Home = ak.NSHomeFunctionKey
    Begin = ak.NSBeginFunctionKey
    End = ak.NSEndFunctionKey
    PageUp = ak.NSPageUpFunctionKey
    PageDown = ak.NSPageDownFunctionKey
    PrintScreen = ak.NSPrintScreenFunctionKey
    ScrollLock = ak.NSScrollLockFunctionKey
    Pause = ak.NSPauseFunctionKey
    SysReq = ak.NSSysReqFunctionKey
    Break = ak.NSBreakFunctionKey
    Reset = ak.NSResetFunctionKey
    Stop = ak.NSStopFunctionKey
    Menu = ak.NSMenuFunctionKey
    User = ak.NSUserFunctionKey
    System = ak.NSSystemFunctionKey
    Print = ak.NSPrintFunctionKey
    ClearLine = ak.NSClearLineFunctionKey
    ClearDisplay = ak.NSClearDisplayFunctionKey
    InsertLine = ak.NSInsertLineFunctionKey
    DeleteLine = ak.NSDeleteLineFunctionKey
    InsertChar = ak.NSInsertCharFunctionKey
    DeleteChar = ak.NSDeleteCharFunctionKey
    Prev = ak.NSPrevFunctionKey
    Next = ak.NSNextFunctionKey
    Select = ak.NSSelectFunctionKey
    Execute = ak.NSExecuteFunctionKey
    Undo = ak.NSUndoFunctionKey
    Redo = ak.NSRedoFunctionKey
    Find = ak.NSFindFunctionKey
    Help = ak.NSHelpFunctionKey
    ModeSwitch = ak.NSModeSwitchFunctionKey

class COLOR:
    def _color(name):
        color = getattr(ak.NSColor, name)()
        return color.colorUsingColorSpace_(ak.NSColorSpace.deviceRGBColorSpace())
    text_color = _color("textColor")
    selection_color = _color("selectedTextBackgroundColor")
    background_color = _color("controlBackgroundColor")
