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


class OverlayWindow(ak.NSWindow):
    """Overlay window for floating controls over NSScrollView

    Based on LKOverlayWindow
    http://cocoadev.com/LKOverlayWindow
    https://github.com/bushd/rex/blob/master/reX/BBOverlayWindow.h
    https://github.com/bushd/rex/blob/master/reX/BBOverlayWindow.m
    """

    def initWithView_(self, parent):
        rect = fn.NSMakeRect(0, 0, *parent.frame().size)
        self.initWithContentRect_styleMask_backing_defer_(
            rect, ak.NSBorderlessWindowMask, ak.NSBackingStoreBuffered, False)
        self.attachToView_(parent)
        return self

    def initWithContentRect_styleMask_backing_defer_(self, rect, mask, back, defer):
        super(OverlayWindow, self).initWithContentRect_styleMask_backing_defer_(
            rect, ak.NSBorderlessWindowMask, ak.NSBackingStoreBuffered, False)
        self.setBackgroundColor_(fn.NSColor.clearColor())
        self.setLevel_(ak.NSPopUpMenuWindowLevel)
        self.setAlphaValue_(1.0)
        self.setOpaque_(False)
        self.setHasShadow_(False)
        ak.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, 'updateSize', ak.NSWindowDidResizeNotification, None)
        return self

    def attachToView_(self, parent):
        self.parent = parent
        if self not in (parent.window().childWindows() or []):
            if self.parentWindow() is not None:
                self.parentWindow().removeChildWindow_(self)
            # Attach the overlay window to the parent's window
            parent.window().addChildWindow_ordered_(self, ak.NSWindowAbove)
        self.updateSize()

    def detach(self):
        self.parentWindow().removeChildWindow_(self)
        self.parent = None
        self.close()

    def updateSize(self):
        window_rect = self.parent.convertRect_toView_(self.parent.bounds(), None)
        screen_rect = self.parent.window().convertRectToScreen_(window_rect)
        self.setFrame_display_(screen_rect, True)

    def windowDidResize_(self, notification):
        self.updateSize()

    def acceptsFirstResponder(self):
        return True

    def isKeyWindow(self):
        return False

    def canBecomeMainWindow(self):
        return False

    def cleanAndRelease(self):
        ak.NSNotificationCenter.defaultCenter().removeObserver_(self)
        self.detach()
        self.release()
