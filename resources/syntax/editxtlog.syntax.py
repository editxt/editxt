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

name = "EditXT Log"
file_patterns = ["EditXT Log"]
comment_token = "x"
rules = [
    ("navy.log.debug", [RE("DEBUG [a-zA-Z.]+ - ")]),
    ("green.log.info", [RE("INFO [a-zA-Z.]+ - ")]),
    ("orange.log.warning", [RE("WARNING [a-zA-Z.]+ - ")]),
    ("red.log.error", [RE("ERROR [a-zA-Z.]+ - ")]),
    ("red.log.critical", [RE("CRITICAL [a-zA-Z.]+ - ")]),
]
