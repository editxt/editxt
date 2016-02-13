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
import logging
from math import ceil

from objc import Category, IBOutlet
import AppKit as ak
import Foundation as fn
from objc import super

log = logging.getLogger(__name__)

ICON_PADDING = -23.0

class ImageAndTextCell(ak.NSTextFieldCell):
    """Image/text cell

    Adapted from DragNDropOutlineView example code
    """

    def _init(self):
        self.editor = None
        self._image = None

    def init(self):
        self._init()
        return super(ImageAndTextCell, self).init()

    def initWithCoder_(self, coder):
        self._init()
        return super(ImageAndTextCell, self).initWithCoder_(coder)

    def dealloc(self):
        self._image = None
        super(ImageAndTextCell, self).dealloc()

    def copyWithZone_(self, zone):
        cell = super(ImageAndTextCell, self).copyWithZone_(zone)
        cell._image = self._image
        return cell

    def setImage_(self, value):
        if self._image != value:
            self._image = value

    def image(self):
        return self._image

    def expansionFrameWithFrame_inView_(self, frame, view):
        """prevent tooltip (expansion frame) for elided text"""
        return fn.NSZeroRect

    def drawWithFrame_inView_(self, frame, view):
        if self._image is not None:
            if self._image.isFlipped() != view.isFlipped():
                self._image.setFlipped_(view.isFlipped())
            isize = self._image.size()
            iframe, frame = fn.NSDivideRect(
                frame, None, None, isize.width + ICON_PADDING, fn.NSMinXEdge)
            if self.drawsBackground():
                self.backgroundColor().set()
                ak.NSRectFill(iframe)
            iframe.origin.x += ICON_PADDING
            iframe.size = isize
            draw_icon(self._image, iframe.origin, self.editor.is_dirty)
        frame.origin.x += 3
        frame.size.width -= 3
        super(ImageAndTextCell, self).drawWithFrame_inView_(frame, view)

    def cellSize(self):
        size = super(ImageAndTextCell, self).cellSize()
        size.width += (0 if self._image is None else self._image.size().width) + ICON_PADDING
        if size.width < 0:
            size.width = 0
        return size

#     def imageFrameForCellFrame_(self, frame):
#         if self._image is not None:
#             iframe = NSMakeRect(0, 0, 0, 0)
#             iframe.size = self._image.size()
#             iframe.origin = frame.origin
#             iframe.origin.x += ICON_PADDING
#             iframe.origin.y += ceil((frame.size.height - iframe.size.height) / 2)
#         else:
#             iframe = NSZeroRect()
#         return iframe


def draw_icon(image, point, dirty):
    if dirty:
        red = ak.NSColor.redColor()
        shadow = ak.NSShadow.alloc().init()
        shadow.setShadowOffset_(fn.NSMakeSize(0, 0))
        shadow.setShadowBlurRadius_(4.0)
        shadow.setShadowColor_(red)
        shadow.set()
        ak.NSColor.colorWithCalibratedWhite_alpha_(0.9, 1.0).set()
    image.drawAtPoint_fromRect_operation_fraction_(
        point, ak.NSZeroRect, ak.NSCompositeSourceOver, 1.0)
    if dirty:
        ak.NSShadow.alloc().init().set()  # clear shadow
        # draw badge
        red.setFill()
        badge_rect = fn.NSMakeRect(point.x - 7, point.y + 6, 5, 5)
        path = ak.NSBezierPath.bezierPath()
        path.appendBezierPathWithOvalInRect_(badge_rect)
        path.fill()
