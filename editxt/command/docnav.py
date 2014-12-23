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
from editxt.command.parser import CommandParser, Choice, Int
from editxt.command.util import has_editor
from editxt.platform.app import beep
from editxt.platform.constants import KEY

log = logging.getLogger(__name__)


@command(arg_parser=CommandParser(
    Choice(
        ("previous", const.PREVIOUS),
        ("next", const.NEXT),
        ("up", const.UP),
        ("down", const.DOWN),
        name="direction"
    ),
    Int("offset", default=1),
), title="Navigate Document Tree", is_enabled=has_editor)
def doc(editor, sender, args):
    """Navigate the document tree"""
    if args is None:
        from editxt.commands import show_command_bar
        show_command_bar(editor, sender, doc.name + " ")
        return
    if not editor.project.window.focus(args.direction, args.offset):
        beep()
