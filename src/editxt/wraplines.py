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
import objc
import os
import re
import time

from AppKit import *
from Foundation import *

import editxt.constants as const
from editxt.commandbase import SheetController
from editxt.textcommand import iterlines

log = logging.getLogger("editxt.wraplines")

WHITESPACE = re.compile("[ \t]*")

class WrapLinesController(SheetController):
    """Window controller for sort lines text command"""

    NIB_NAME = u"WrapLines"
    OPTIONS_DEFAULTS = dict(
        wrap_at_col=80,
        indent_like_first=True,
    )

    def wrap_(self, sender):
        wrap_selected_lines(self.textview, self.opts)
        self.save_options()
        self.cancel_(sender)

def wrap_selected_lines(textview, options):
    text = textview.string()
    sel = text.lineRangeForRange_(textview.selectedRange())
    lines = iterlines(text, sel)
    output = "\n".join(wraplines(lines, options))
    if textview.shouldChangeTextInRange_replacementString_(sel, output):
        textview.textStorage().replaceCharactersInRange_withString_(sel, output)
        textview.didChangeText()
        textview.setSelectedRange_((sel[0], len(output)))

def wraplines(lines, options):
    lines = iter(lines)
    width = options.wrap_column
    frag = lines.next().rstrip()
    leading = WHITESPACE.match(frag).group()
    if leading:
        frag = frag.lstrip()
        firstlen = width - len(leading)
        if firstlen > 0:
            line, frag = get_line(frag, lines, firstlen)
            yield leading + line
            if not options.indent:
                leading = u""
    while frag is not None:
        line, frag = get_line(frag, lines, width)
        yield leading + line if line else line
    if line:
        yield u""

def get_line(frag, lines, width, ws=u" \t"):
    while True:
        while len(frag) < width:
            try:
                nextline = lines.next()
            except StopIteration:
                return frag, None
            if nextline:
                frag = frag + u" " + nextline.strip()
        if len(frag) == width:
            return frag, u""
        for i in xrange(width, 0, -1):
            if frag[i] in ws:
                break
        else:
            fraglen = len(frag)
            i = width + 1
            while i < fraglen and frag[i] not in ws:
                i += 1
        line, frag = frag[:i].rstrip(), frag[i:].lstrip()
        if len(line) + len(WHITESPACE.split(frag, 1)[0]) < width:
            frag = line + u" " + frag
            continue
        return line, frag
