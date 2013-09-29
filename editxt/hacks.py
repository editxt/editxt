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

def _patch_traceback_module():
    """Patch traceback module to better support unicode
    
    HACK this patch assumes that the output device (e.g. Terminal.app)
    supports UTF-8
    """
    import traceback
    def _some_str(value):
        try:
            return str(value).encode("utf-8")
        except:
            return '<unprintable %s object>' % type(value).__name__
    traceback._some_str = _some_str
_patch_traceback_module()
