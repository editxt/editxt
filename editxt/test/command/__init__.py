# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2014 Daniel Miller <millerdev@gmail.com>
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
import Foundation as fn
from editxt.datatypes import AbstractNamedProperty, WeakProperty


class FakeTextView(object):

    def __init__(self, text="", sel=fn.NSMakeRange(0, 0), editor=None):
        self.text = text
        self.sel = sel
        self.editor = editor

    def selectedRange(self):
        return self.sel

    def setSelectedRange_(self, sel):
        self.sel = sel

    def string(self):
        return fn.NSString.alloc().initWithString_(self.text)

    def shouldChangeTextInRange_replacementString_(self, rng, str):
        return True

    def textStorage(self):
        return self

    def replaceCharactersInRange_withString_(self, rng, string):
        end = rng[0] + rng[1]
        self.text = self.text[:rng[0]] + string + self.text[end:]

    def didChangeText(self):
        pass
