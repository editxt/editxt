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
import os

import AppKit as ak
import Foundation as fn
from mocker import Mocker, MockerTestCase, expect, ANY
from nose.tools import *
from editxt.test.util import TestConfig, untested

import editxt.constants as const
import editxt.controls.splitview as mod

log = logging.getLogger(__name__)

# log.debug("""TODO
#     implement TextDocumentView.pasteboard_data()
# """)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def test_is_view_visibile():
    def test(c):
        m = Mocker()
        sv = mod.ThinSplitView.alloc().init()
        view = m.method(sv.subviews)()[c.index] >> m.mock(ak.NSView)
        if m.method(sv.isVertical)() >> c.vertical:
            view.bounds().size.width >> c.thick
        else:
            view.bounds().size.height >> c.thick
        with m:
            result = sv.is_view_visible(c.index, c.minthick)
        eq_(result, c.thick > c.minthick)
        eq_(result, c.vis)
    c = TestConfig(index=0, vis=False)
    for v in (True, False):
        for i in range(3):
            yield test, c(index=i, vertical=v, minthick=0.0, thick=0.0)
        yield test, c(vertical=v, minthick=5.0, thick=0.0)
        yield test, c(vertical=v, minthick=5.0, thick=5.0)
        yield test, c(vertical=v, minthick=0.0, thick=5.0, vis=True)


def test_show_view():
    def test(c):
        m = Mocker()
        sv = mod.ThinSplitView.alloc().init()
        view = m.method(sv.subviews)()[c.index] >> m.mock(ak.NSView)
        rect = view.frame() >> m.mock(fn.NSRect)
        if m.method(sv.isVertical)() >> c.vertical:
            dim, org = "width", "x"
        else:
            dim, org = "height", "y"
        getattr(rect.size, dim) >> c.vwthick
        if c.vwthick < c.thick:
            if c.index == 1:
                getattr(rect.origin, org) >> 0
                setattr(rect.origin, org, -c.thick)
            setattr(rect.size, dim, c.thick)
            ad = sv.animation_delegate = m.mock()
            m.method(sv._animate_view)(view, rect, ad)
        with m:
            sv.show_view(c.index, c.thick)
    c = TestConfig(index=0, vwthick=50.0, thick=50.0)
    for v in (True, False):
        for i in (0, 1):
            yield test, c(index=i, vertical=v)
            yield test, c(index=i, vertical=v, vwthick=0.0)
            yield test, c(index=i, vertical=v, thick=20.0)


def test_hide_view():
    def test(c):
        m = Mocker()
        sv = mod.ThinSplitView.alloc().init()
        view = m.method(sv.subviews)()[c.index] >> m.mock(ak.NSView)
        rect = view.frame() >> m.mock(fn.NSRect)
        if m.method(sv.isVertical)() >> c.vertical:
            dim, org = "width", "x"
        else:
            dim, org = "height", "y"
        getattr(rect.size, dim) >> c.vwthick
        if c.vwthick > 0:
            if c.index == 1:
                getattr(rect.origin, org) >> 0
                setattr(rect.origin, org, c.vwthick)
            setattr(rect.size, dim, 0.0)
            m.method(sv._animate_view)(view, rect)
        with m:
            sv.hide_view(c.index)
    c = TestConfig(index=0, vwthick=0.0)
    for v in (True, False):
        for i in (0, 1):
            yield test, c(index=i, vertical=v)
            yield test, c(index=i, vertical=v, vwthick=20.0)

def test_animate_view():
    def test(c):
        m = Mocker()
        sv = mod.ThinSplitView.alloc().init()
        nsanim = m.replace(mod, 'NSViewAnimation')
        view = m.mock(ak.NSView)
        rect = fn.NSMakeRect(0, 0, 1, 1)
        anim = nsanim.alloc() >> m.mock(ak.NSViewAnimation)
        anim.initWithViewAnimations_(ANY) >> anim
        anim.setDuration_(0.5)
        if c.delegate:
            delegate = m.mock(mod.RedrawOnAnimationEndedDelegate)
            anim.setDelegate_(delegate)
        else:
            delegate = None
        anim.startAnimation()
        with m:
            sv._animate_view(view, rect, delegate)
    c = TestConfig()
    yield test, c(delegate=True)
    yield test, c(delegate=False)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SplitView-related tests

def test_SliderImageView_splitView():
    vw = mod.SliderImageView.alloc().init()
    assert hasattr(vw, "splitView")
