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
from editxt.command.base import command, objc_delegate, SheetController
from editxt.command.parser import Choice, Regex, CommandParser, Options
from editxt.commands import iterlines

log = logging.getLogger(__name__)


@command(name='sort', title=u"Sort Lines...",
    arg_parser=CommandParser(
        Choice(('selection', True), ('all', False)),
        Choice(('forward', False), ('reverse', True), name='reverse'),
        Choice(
            ('sort-leading-whitespace', False),
            ('ignore-leading-whitespace', True),
            name='ignore-leading-whitespace'),
        Choice(
            ('ignore-case', True),
            ('match-case', False)),
        Regex('sort-regex', True),
    ))
def sort_lines(textview, sender, args):
    if args is None:
        sorter = SortLinesController(textview)
        sorter.begin_sheet(sender)
    else:
        sortlines(textview, args)


class SortOptions(Options):

    DEFAULTS = dict(
        selection=True,
        reverse=False,
        ignore_leading_whitespace=False,
        ignore_case=True,
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

    COMMAND = sort_lines
    NIB_NAME = u"SortLines"
    OPTIONS_FACTORY = SortOptions

    @objc_delegate
    def sort_(self, sender):
        sortlines(self.textview, self.options)
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
        if opts.ignore_case:
            line = line.lower()
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
