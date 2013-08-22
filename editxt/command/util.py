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
import re

import editxt.constants as const

log = logging.getLogger(__name__)


def has_selection(textview, sender):
    return textview.selectedRange().length > 0


_line_splitter = re.compile(u"([^\n\r\u2028]*(?:%s)?)" % "|".join(
    eol for eol in sorted(const.EOLS.values(), key=len, reverse=True)))

def iterlines(text, range=(0,)):
    """iterate over lines of text

    By default this function iterates over all lines in the give text. If the
    'range' parameter (NSRange or tuple) is given, lines within that range will
    be yielded.
    """
    if not text:
        yield text
    else:
        if range != (0,):
            range = (range[0], sum(range))
        for line in _line_splitter.finditer(text, *range):
            if line.group():
                yield line.group()
