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
import os

import AppKit as ak
import Foundation as fn

from mocker import Mocker, ANY
from nose.tools import eq_
from editxt.test.util import TestConfig

import editxt.platform.mac.cells as mod

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ImageAndTextCell tests

def test_iatc_init():
    cell = mod.ImageAndTextCell.alloc().init()
    assert cell._image is None

def test_iatc_image_property_():
    cell = mod.ImageAndTextCell.alloc().init()
    assert cell.image() is None
    cell.setImage_("test")
    assert cell.image() == "test"

def test_iatc_cellSize():
    cell = mod.ImageAndTextCell.alloc().init()
    assert cell.image() is None
    size = cell.cellSize()
    m = Mocker()
    image = m.mock(ak.NSImage)
    image.size().width >> 10
    m.replay()
    cell.setImage_(image)
    assert cell.image() is image
    print(size.width)
    size2 = cell.cellSize()
    assert size2.width == size.width + 10, "%s != %s" % (size2.width, size.width + 10)
    assert size2.height == size.height

def test_expansionFrameWithFrame_inView_():
    cell = mod.ImageAndTextCell.alloc().init()
    #frame = NSMakeRect(0, 0, 50, 16)
    eq_(cell.expansionFrameWithFrame_inView_(fn.NSZeroRect, None), fn.NSZeroRect)
