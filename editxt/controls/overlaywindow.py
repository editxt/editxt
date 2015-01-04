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
import Foundation as fn
import objc
from objc import super

from editxt.platform.mac.views import screen_rect


class OverlayWindow(ak.NSWindow):
    """Overlay window for floating controls over NSScrollView

    Based on LKOverlayWindow
    http://cocoadev.com/LKOverlayWindow
    https://github.com/bushd/rex/blob/master/reX/BBOverlayWindow.h
    https://github.com/bushd/rex/blob/master/reX/BBOverlayWindow.m
    """

    def initWithView_(self, parent):
        rect = fn.NSMakeRect(0, 0, *parent.frame().size)
        super(OverlayWindow, self).initWithContentRect_styleMask_backing_defer_(
            rect, ak.NSBorderlessWindowMask, ak.NSBackingStoreBuffered, False)
        self.setBackgroundColor_(fn.NSColor.clearColor())
        self.setLevel_(ak.NSPopUpMenuWindowLevel)
        self.setAlphaValue_(1.0)
        self.setOpaque_(False)
        self.setHasShadow_(False)
        self.parent = None
        self.attachToView_(parent)
        return self

    def attachToView_(self, parent):
        if self not in (parent.window().childWindows() or []):
            if self.parentWindow() is not None:
                self.parentWindow().removeChildWindow_(self)
            # Attach the overlay window to the parent's window
            parent.window().addChildWindow_ordered_(self, ak.NSWindowAbove)
        if self.parent is not None:
            ak.NSNotificationCenter.defaultCenter().removeObserver_name_object_(
                self, ak.NSViewFrameDidChangeNotification, self.parent)
        ak.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, 'updateSize', ak.NSViewFrameDidChangeNotification, parent)
        self.parent = parent
        self.updateSize()

    def detach(self):
        ak.NSNotificationCenter.defaultCenter().removeObserver_(self)
        self.parentWindow().removeChildWindow_(self)
        self.parent = None
        self.close()

    def updateSize(self):
        if self.parent.window() is None:
            return
        rect = screen_rect(self.parent, self.parent.overlay_bounds)
        if self.frame() != rect:
            self.setFrame_display_(rect, True)

    def acceptsFirstResponder(self):
        return True

    def isKeyWindow(self):
        return False

    def canBecomeMainWindow(self):
        return False

    def cleanAndRelease(self):
        self.detach()
        self.release()
