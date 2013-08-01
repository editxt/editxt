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
import objc
import os
import re
import time

from AppKit import *
from Foundation import *

import editxt.constants as const
from editxt.commandbase import SheetController, Options
from editxt.commands import iterlines

log = logging.getLogger(__name__)


class SortOptions(Options):

    DEFAULTS = dict(
        selection=False,
        reverse=False,
        ignore_leading_whitespace=False,
        numeric_match=False,
        regex_sort=False,
        search_pattern="",
        match_pattern="",
    )

    @property
    def sort_regex(self):
        if self.regex_sort:
            return (self.search_pattern, self.match_pattern)
        return (None, None)


class SortLinesController(SheetController):
    """Window controller for sort lines text command"""

    NIB_NAME = u"SortLines"
    OPTIONS_FACTORY = SortOptions

    def sort_(self, sender):
        sortlines(self.textview, self.opts)
        self.save_options()
        self.cancel_(sender)

def sortlines(textview, opts):
    text = textview.string()
    if opts.sort_regex[0]:
        regex = re.compile(opts.sort_regex[0])
        if opts.sort_regex[1]:
            groups = [int(g.strip()) for g in opts.sort_regex[1].split("\\") if g.strip()]
        else:
            groups = None
    else:
        regex = None
    def key(line):
        if opts.ignore_leading_whitespace:
            line = line.lstrip()
        if regex is not None:
            match = regex.search(line)
            if match is None:
                line = (1,)
            elif not match.groups():
                line = (0, match.group(0))
            else:
                matched = match.groups("")
                if groups:
                    matched = dict(enumerate(matched))
                    matched = tuple(matched.get(g - 1, "") for g in groups)
                line = (0,) + matched
        return line
    if opts.selection:
        range = text.lineRangeForRange_(textview.selectedRange())
    else:
        range = (0, len(text))
    output = "".join(sorted(iterlines(text, range), key=key, reverse=opts.reverse))
    if textview.shouldChangeTextInRange_replacementString_(range, output):
        textview.textStorage().replaceCharactersInRange_withString_(range, output)
        textview.didChangeText()
        if opts.selection:
            textview.setSelectedRange_(range)
