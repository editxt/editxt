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

def setup_main_view(*args):
    pass

def teardown_main_view(*args):
    pass

def add_command_view(view, frame, editor):
    class command_view:
        command = editor.project.window.command
    command_view.editor = editor
    class main_view:
        top = view
        bottom = command_view
        def frame(self):
            return frame
        def become_subview_of(self, view, focus=None):
            self.parent_view = view
    return main_view()
