# -*- coding: utf-8 -*-
# EditXT
# Copyright (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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

from objc import Category
from AppKit import *
from Foundation import *

log = logging.getLogger("editxt.controls.outlineview")

ICON_PADDING = -23.0

class ImageAndTextCell(NSTextFieldCell):
    """Image/text cell

    Adapted from DragNDropOutlineView example code
    """

    def _init(self):
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
        return NSZeroRect

    def drawWithFrame_inView_(self, frame, view):
        if self._image is not None:
            isize = self._image.size()
            iframe, frame = NSDivideRect(
                frame, None, None, isize.width + ICON_PADDING, NSMinXEdge)
            if self.drawsBackground():
                self.backgroundColor().set()
                NSRectFill(iframe)
            iframe.origin.x += ICON_PADDING
            iframe.size = isize
            if view.isFlipped():
                iframe.origin.y += ceil((frame.size.height + iframe.size.height) / 2)
            else:
                iframe.origin.y += ceil((frame.size.height - iframe.size.height) / 2)
            self._image.compositeToPoint_operation_(iframe.origin, NSCompositeSourceOver)
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# HoverButtonCell implementation

BUTTON_STATE_HOVER = "HOVER"
BUTTON_STATE_NORMAL = "NORMAL"
BUTTON_STATE_PRESSED = "PRESSED"

class HoverButtonCell(NSButtonCell):

    delegate = objc.ivar("delegate")

    def _init(self):
        self.setBordered_(False)
        self.setButtonType_(NSMomentaryChangeButton)
        self.setImagePosition_(NSImageOnly)
        self._state = BUTTON_STATE_NORMAL
        self.maxImageWidth = 128
        self.mouseLocation = NSMakePoint(0.0, 0.0)

    def init(self):
        self = super(HoverButtonCell, self).init()
        self._init()
        return self

    def initWithCoder_(self, coder):
        self = super(HoverButtonCell, self).initWithCoder_(coder)
        self._init()
        return self

    def buttonImageForFrame_inView_(self, frame, view):
        row = view.rowAtPoint_(frame.origin)
        return self.delegate.hoverButtonCell_imageForState_row_(view, self._state, row)

    def mouseEnteredInvalidatesForFrame_(self, frame):
        return False

    def mouseExitedInvalidatesForFrame_(self, frame):
        if self._state != BUTTON_STATE_NORMAL:
            self._state = BUTTON_STATE_NORMAL
        return True

    def mouseMoveToPoint_invalidatesForFrame_(self, point, frame):
        origState = self._state
        if NSPointInRect(point, frame):
            self._state = BUTTON_STATE_HOVER
        else:
            self._state = BUTTON_STATE_NORMAL
        self.mouseLocation = point
        return self._state != origState

    def mouseUpAtPoint_invalidatesForFrame_(self, point, frame):
        if NSPointInRect(point, frame):
            self._state = BUTTON_STATE_HOVER
            # if point inside, call the action
            #self.target().performSelector_withObject_(self.action(), self)
            row = self.controlView().rowAtPoint_(frame.origin)
            self.delegate.hoverButton_rowClicked_(self, row)
        else:
            self._state = BUTTON_STATE_NORMAL
        self.mouseLocation = point
        return True

    def trackMouseAtPoint_invalidatesForFrame_redraw_(self, point, frame, redraw):
        # if point inside, track
        if NSPointInRect(point, frame):
            self._state = BUTTON_STATE_PRESSED
            self.mouseLocation = point
            return True, True
        return False, redraw

    def continueTrackingMouseAtPoint_invalidatesForFrame_redraw_(self, point, frame, redraw):
        origState = self._state
        if NSPointInRect(point, frame):
            self._state = BUTTON_STATE_PRESSED
        else:
            self._state = BUTTON_STATE_NORMAL
        self.mouseLocation = point
        return False, (self._state != origState)

    def buttonRectForFrame_imageSize_(self, frame, size):
        dest = NSMakeRect(frame.origin.x, frame.origin.y, size.width, size.height)

        # scale image to frame
        #if dest.size.height > frame.size.height:
        #    change = frame.size.height / size.height
        #    dest.size.height = frame.size.height
        #    dest.size.width = size.width * change

        # constrain image width
        if dest.size.width > self.maxImageWidth:
            change = self.maxImageWidth / dest.size.width
            dest.size.width = maxImageWidth
            dest.size.height = dest.size.height * change

        # center vertically
        if dest.size.height < frame.size.height:
            dest.origin.y += (frame.size.height - dest.size.height) / 2.0

        # adjust rects
        #dest.origin.y += 1
        #dest.origin.x += frame.size.width
        #dest.origin.x -= size.width
        return dest

    def drawInteriorWithFrame_inView_(self, frame, view):
        """Draw the button image as specified by the current button state

        Note: this is necessary (as opposed to self.setImage_(...) and the
        default drawing logic) because it takes a final chance to check if the
        mouse is actually hovering over the frame before drawing the button
        image. If this is not done, and the mouse is being moved quickly from
        one hover button to the next then the previous button may remain in the
        hovered state even though the mouse has moved out of its frame.
        """
        # update just in case some change was made in the view that wasn't reflected by events
        if not NSPointInRect(self.mouseLocation, frame):
            self._state = BUTTON_STATE_NORMAL

        image = self.buttonImageForFrame_inView_(frame, view)
        if image is not None:
            dest = self.buttonRectForFrame_imageSize_(frame, image.size())

            # Decrease the cell width by the width of the image we drew and its left padding
            frame.size.width -= dest.size.width

            NSGraphicsContext.currentContext().saveGraphicsState()
            NSGraphicsContext.currentContext().setImageInterpolation_(NSImageInterpolationHigh)
            image.drawInRect_fromRect_operation_fraction_(
                NSMakeRect(dest.origin.x, dest.origin.y, dest.size.width, dest.size.height),
                NSMakeRect(0.0, 0.0, image.size().width, image.size().height),
                NSCompositeSourceOver,
                1.0,
            )
            NSGraphicsContext.currentContext().restoreGraphicsState()

        # draw the rest of the cell
        super(HoverButtonCell, self).drawInteriorWithFrame_inView_(frame, view)

