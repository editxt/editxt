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


class UndoManager(fn.NSUndoManager):
    """Undo manager that uese "savepoints" to facilitate undo beyond save"""

    def init(self):
        self.actions_since_save = 0
        self.allow_clear = True
        self.level_before_save = 0
        return super(UndoManager, self).init()

    def removeAllActions(self):
        if self.allow_clear:
            super(UndoManager, self).removeAllActions()

    def savepoint(self):
        """Record a savepoint

        This clears `has_unsaved_actions`.
        """
        assert not (self.isUndoing() or self.isRedoing()), \
            ("cannot undo/redo savepoint", self.isUndoing(), self.isRedoing())
        level = self.groupingLevel()
        assert level in (0, 1), level
        if level > 0:
            assert not self.level_before_save, self.level_before_save
            self.endUndoGrouping()
        elif self.level_before_save:
            level = self.level_before_save
        self.level_before_save = level
        self.actions_since_save = 0

    def before_act(self):
        if self.actions_since_save is not None:
            if self.isUndoing():
                self.actions_since_save -= 1
            elif self.actions_since_save >= 0 or self.isRedoing():
                self.actions_since_save += 1
            else:
                self.actions_since_save = None
        if self.groupingLevel() == 0 and self.level_before_save:
            self.level_before_save = 0
            self.beginUndoGrouping()

    def prepareWithInvocationTarget_(self, target):
        self.before_act()
        return super().prepareWithInvocationTarget_(target)

    def registerUndoWithTarget_selector_object_(self, target, selector, object):
        self.before_act()
        super().registerUndoWithTarget_selector_object_(target, selector, object)

    def beginUndoGrouping(self):
        if self.level_before_save and not (self.isUndoing() or self.isRedoing()):
            self.level_before_save = 0
            self.beginUndoGrouping()
        super().beginUndoGrouping()

    def endUndoGrouping(self):
        if self.level_before_save and not (self.isUndoing() or self.isRedoing()):
            assert self.groupingLevel() == 0, self.groupingLevel()
            self.level_before_save = 0
        else:
            super().endUndoGrouping()

    def has_unsaved_actions(self):
        return self.actions_since_save != 0
