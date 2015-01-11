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

_font = ak.NSFont.userFixedPitchFontOfSize_(-1.0)
DEFAULT_FONT = Font(_font.displayName(), _font.pointSize(), True, _font)


def get_font(face, size, smooth, ignore=None):
    font = ak.NSFont.fontWithName_size_(face, size)
    if font is None:
        font = ak.NSFont.fontWithName_size_(DEFAULT_FONT.face, size)
    return Font(font.displayName(), font.pointSize(), smooth, font)
