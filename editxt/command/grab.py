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
import logging
import re

import editxt.constants as const
from editxt.command.base import command, CommandError
from editxt.command.parser import CommandParser, Choice, Regex
from editxt.command.util import iterlines
from editxt.platform.app import beep

log = logging.getLogger(__name__)


@command(arg_parser=CommandParser(
    Regex("pattern"),
    Choice(("match", False), ("invert", True), name="invert"),
    Choice("all", "selection", name="scope"),
    #Choice("output", "pboard", "new document"), # maybe allow pipe instead of these
), title="Grab lines")
def grab(editor, sender, args):
    """Collect lines matching a pattern"""
    if args is None:
        from editxt.commands import show_command_bar
        show_command_bar(editor, sender, "grab ")
        return
    elif args.pattern is None:
        raise CommandError("please specify a pattern to match")
    if args.invert:
        norm = lambda m: not m
    else:
        norm = lambda m: m
    scope = editor.selection if args.scope == "selection" else (0,)
    regex = re.compile(args.pattern, args.pattern.flags)
    lines = []
    for line in iterlines(editor.document.text, scope):
        if norm(regex.search(line)):
            lines.append(line)
    if lines:
        editor.message("".join(lines), msg_type=const.INFO)
    else:
        beep()
