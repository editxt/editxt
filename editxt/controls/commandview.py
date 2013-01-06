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

from AppKit import NSFocusRingTypeNone, NSFont, NSTextField

log = logging.getLogger(__name__)

class CommandView(NSTextField):

    def initWithFrame(self, rect):
        super(CommandView, self).initWithFrame_(rect)
        self.setStringValue_("")
        self.setFont_(NSFont.fontWithName_size_("Monaco", 9.0))
        self.setFocusRingType_(NSFocusRingTypeNone)
        self.setTarget_(self)
        self.setAction_('doCommand:')
        self.setDelegate_(self)
        self.command = None
        return self

    def __nonzero__(self):
        return self.command is not None

    def activate(self, command, initial_text=""):
        self.command = command
        self.setStringValue_(initial_text)
        #self.performSelector_withObject_afterDelay_("selectText:", self, 0)
        # possibly use setSelectedRange
        # http://jeenaparadies.net/weblog/2009/apr/focus-a-nstextfield
        self.window().makeFirstResponder_(self)
        self._redraw()

    def deactivate(self):
        view = self.command.editor.current_view
        if view is not None:
            self.window().makeFirstResponder_(view.text_view)
        self.command = None
        self._redraw()

    def doCommand_(self, sender):
        self.command.execute(self.stringValue())

    def textDidEndEditing_(self, notification):
        super(CommandView, self).textDidEndEditing_(notification)
        self.deactivate()

    def control_textView_doCommandBySelector_(self, view, textview, selector):
        if selector == "cancelOperation:": # escape key
            self.deactivate()
            return True
        if selector == "insertTab:":
            # TODO invoke command completion
            return True
        if selector == "insertBacktab:":
            # ignore
            return True
        return False

    #def control_textView_completions_forPartialWordRange_indexOfSelectedItem_(

    def _redraw(self):
        self.superview().tile()
        self.superview().setNeedsDisplay_(True)
