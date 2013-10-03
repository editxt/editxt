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

from mocker import Mocker, expect, ANY
from nose.tools import eq_
from editxt.test.util import TestConfig

import editxt.controls.cells as mod

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ImageAndTextCell tests

def test_HoverButtonCell_init():
    HoverButtonCell.alloc().init()

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

def test_drawWithFrame_inView_():
    def test(c):
        m = Mocker()
        cell = mod.ImageAndTextCell.alloc().init()
        img = cell._image = m.mock(ak.NSImage) if c.image else None
        frame = fn.NSMakeRect(0, 0, 20, 100)
        view = m.mock(ak.NSView)
        draws = m.method(mod.ImageAndTextCell.drawsBackground)
        color = m.method(mod.ImageAndTextCell.backgroundColor)
        fill = m.replace(ak, 'NSRectFill')
        if c.image:
            img.size() >> fn.NSSize(20, 20)
            if draws() >> c.draws:
                color().set()
                fill(ANY)
            view.isFlipped() >> c.flipped
            img.compositeToPoint_operation_(ANY, ak.NSCompositeSourceOver)
        m.method(ak.NSTextFieldCell.drawWithFrame_inView_)(frame, view)
        with m:
            cell.drawWithFrame_inView_(frame, view)
    c = TestConfig(image=True)
    yield test, c(image=False)
    for draws in [True, False]:
        yield test, c(draws=draws, flipped=True)
        yield test, c(draws=draws, flipped=False)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# HoverButtonCell tests
from editxt.controls.cells import (HoverButtonCell, BUTTON_STATE_NORMAL,
    BUTTON_STATE_HOVER, BUTTON_STATE_PRESSED)


# TODO this cell should calculate the button state during redraw.
# The button state is derived from the mouse location and the redraw frame.
# 
# A single cell instance is used to draw an entire column in NSOutlineView.
# The cell instance caches the hover state (and updates that state on redraw),
# which causes problems when redrawing a cell that is not under the mouse.
# 
# The cell should cache the mouse location and pressed state passed to
# *invalidatesForFrame* methods. Then the redraw has a simple NSPointInRect call
# to calculate the hover state.
# 
# cell should have two dicts: 

# def test_HBC_state_for_row():
#   def test(c):
#       m = Mocker()
#       hbc = HoverButtonCell.alloc().init()
#       hbc.hover_info = 
#   raise NotImplementedError

#       hrow, pressed = self.hover_info
#       if row == hrow:
#           return BUTTON_STATE_PRESSED if pressed else BUTTON_STATE_HOVER
#       return BUTTON_STATE_NORMAL

def test_HBC_buttonImageForFrame_inView_():
    from editxt.editor import EditorWindowController
    def test(c):
        m = Mocker()
        hbc = HoverButtonCell.alloc().init()
        frame = m.mock(fn.NSRect)
        view = m.mock(ak.NSOutlineView)
        point, pressed = hbc.hover_info = c.info
        if point is not None:
            m.replace(fn, 'NSPointInRect')(point, frame) >> (point == "in")
        row = view.rowAtPoint_(frame.origin >> (1, 1)) >> 2
        dgt = m.property(hbc, "delegate").value >> m.mock(EditorWindowController)
        image = dgt.hoverButtonCell_imageForState_row_(hbc, c.state, row) >> "<img>"
        with m:
            eq_(hbc.buttonImageForFrame_inView_(frame, view), image)
    c = TestConfig(info=(None, False), state=BUTTON_STATE_NORMAL)
    yield test, c
    yield test, c(info=("in", False), state=BUTTON_STATE_HOVER)
    yield test, c(info=("in", True), state=BUTTON_STATE_PRESSED)
    yield test, c(info=("out", False))

class MockFrame(object):
    origin = None

def test_HBC_mouseEnteredInvalidatesForFrame_():
    hbc = HoverButtonCell.alloc().init()
    assert not hbc.mouseEnteredInvalidatesForFrame_(MockFrame)

def test_HBC_mouseMovePressHandlers():
    m = Mocker()
    hbc = HoverButtonCell.alloc().init()
    hbc.hover_info = ("point", False)
    with m:
        assert hbc.mouseExitedInvalidatesForFrame_(MockFrame)
        eq_(hbc.hover_info, (None, False))

def test_HBC_mouseMoveHandlers():
    from editxt.editor import EditorWindowController
    def test(c):
        m = Mocker()
        hbc = HoverButtonCell.alloc().init()
        hbc.hover_info = ("initial", None)
        frame = m.mock(fn.NSRect)
        point = c.info[0]
        pir = m.replace(fn, 'NSPointInRect')
        if c.method.startswith("mouseUp"):
            if c.inside is None:
                hbc.hover_info = (None, None)
            elif pir("initial", frame) >> c.inside[0] \
                and pir(point, frame) >> c.inside[1]:
                row = (m.method(hbc, "controlView")() >> m.mock(ak.NSOutlineView)) \
                    .rowAtPoint_(point) >> 2
                (m.property(hbc, "delegate").value >> m.mock(EditorWindowController)) \
                    .hoverButton_rowClicked_(hbc, row)
        with m:
            assert getattr(hbc, c.method)(point, frame)
            eq_(hbc.hover_info, c.info)
    c = TestConfig(info=(None, False))
    yield test, c(method='mouseMoveToPoint_invalidatesForFrame_', info=('point', False))
    yield test, c(method='mouseUpAtPoint_invalidatesForFrame_', info=('point', False), inside=None)
    yield test, c(method='mouseUpAtPoint_invalidatesForFrame_', info=('point', False), inside=(False, False))
    yield test, c(method='mouseUpAtPoint_invalidatesForFrame_', info=('point', False), inside=(True, False))
    yield test, c(method='mouseUpAtPoint_invalidatesForFrame_', info=('point', False), inside=(False, True))
    yield test, c(method='mouseUpAtPoint_invalidatesForFrame_', info=('point', False), inside=(True, True))

def test_HBC_mouseDragHandlers():
    def test(c):
        m = Mocker()
        hbc = HoverButtonCell.alloc().init()
        hbc.hover_info = "<initial value>"
        frame = m.mock(fn.NSRect)
        point = c.info[0]
        with m:
            result = getattr(hbc, c.method)(point, frame, None)
            if c.method.startswith("track"):
                eq_(result, (True, True))
                eq_(hbc.hover_info, c.info)
            else:
                eq_(result, (True, False))
                eq_(hbc.hover_info, "<initial value>")
    c = TestConfig(info=(None, False))
    yield test, c(method='trackMouseAtPoint_invalidatesForFrame_redraw_', info=('point', True))
    yield test, c(method='continueTrackingMouseAtPoint_invalidatesForFrame_redraw_', info=('point', True))

# NOTE this test will not work due to super call (it's not finished either)
# def test_HBC_drawInteriorWithFrame_inView_():
#   def test(c):
#       m = Mocker()
#       hbc = HoverButtonCell.alloc().init()
#       frame = m.mock(fn.NSRect)
#       view = m.mock(NSOutlineView)
#       img = m.method(hbc, "buttonImageForFrame_inView_")(frame, view) \
#           >> (None if not c.img else m.mock(NSImage))
#       ctx_class = m.replace(NSGraphicsContext)
#       ctx = m.mock(NSGraphicsContext)
#       if c.img is None:
#           (ctx_class.currentContext() << ctx).count(2)
#           ctx.saveGraphicsState()
#           ctx.setImageInterpolation_(NSImageInterpolationHigh)
#           img.
#       with m:
#           hbc.drawInteriorWithFrame_inView_(frame, view)
#   c = TestConfig(img=True)
#   yield test, c(img=False)

