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
from functools import wraps

def disable_font_smoothing(draw):
    @wraps(draw)
    def wrapper(self, *args, **kw):
        ak.NSGraphicsContext.saveGraphicsState()
        context = ak.NSGraphicsContext.currentContext()
        context.setShouldAntialias_(getattr(self, 'font_smoothing', False))
        try:
            return draw(self, *args, **kw)
        finally:
            ak.NSGraphicsContext.restoreGraphicsState()
    return wrapper
