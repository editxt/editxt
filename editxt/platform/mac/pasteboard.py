# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2016 Daniel Miller <millerdev@gmail.com>
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

GENERAL = ak.NSGeneralPboard
FIND = ak.NSFindPboard


class Pasteboard:

    def __init__(self, name=GENERAL):
        self.pboard = ak.NSPasteboard.pasteboardWithName_(name)

    @property
    def text(self):
        """Get pasteboard text

        :returns: A string; `None` if the pasteboard did not contain text.
        """
        if self.pboard.availableTypeFromArray_([ak.NSStringPboardType]):
            return self.pboard.stringForType_(ak.NSStringPboardType)
        return None

    @text.setter
    def text(self, value):
        """Set pasteboard text"""
        self.pboard.declareTypes_owner_([ak.NSStringPboardType], None)
        self.pboard.setString_forType_(value, ak.NSStringPboardType)
