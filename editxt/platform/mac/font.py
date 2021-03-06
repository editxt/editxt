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

from editxt.datatypes import Font


def make_font(cocoa_font, smooth):
    _font = cocoa_font
    return Font(_font.displayName(), _font.pointSize(), smooth, _font)


_font = ak.NSFont.userFixedPitchFontOfSize_(-1.0)
DEFAULT_FONT = make_font(_font, True)


def get_font(face, size, smooth, ignore=None):
    font = ak.NSFont.fontWithName_size_(face, size)
    if font is None:
        font = ak.NSFont.fontWithName_size_(DEFAULT_FONT.face, size)
    return Font(font.displayName(), font.pointSize(), smooth, font)


def get_font_from_view(view, app):
    if view is not None:
        return make_font(view.font(), getattr(view, "font_smoothing", True))
    return app.default_font


def get_system_font_names():
    names = ak.NSFontManager.sharedFontManager().availableFontFamilies()
    return [str(name) for name in names]
