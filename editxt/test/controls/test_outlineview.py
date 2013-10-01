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
import os

import AppKit as ak

from mocker import Mocker, expect, ANY

from editxt.controls.outlineview import OutlineView

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# NSTreeController extension tests

def test_nstc_setSelectedObject_():
    tc = ak.NSTreeController.alloc().init()
    tc.setSelectedObject_ # test for existence of method (TODO better testing)

def test_nstc_setSelectedObjects_():
    tc = ak.NSTreeController.alloc().init()
    tc.setSelectedObjects_ # test for existence of method (TODO better testing)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# NSOutlineView extension tests

def test_nsov_realItemForOpaqueItem_():
    tc = ak.NSOutlineView.alloc().init()
    tc.realItemForOpaqueItem_ # test for existence of method (TODO better testing)
