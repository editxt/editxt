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

# TODO rewrite this with nested definitions (or scrap it in favor of markup)
name = "Mako Template"
file_patterns = ["*.mako", "*.mak"]
comment_token = "##"
word_groups = [
    ("builtin", [
        RE("<%!?\s"), RE("\s%>"),
    ]), # 400080
]
delimited_ranges = [
    ("comment.doc", "<%doc>", ["</%doc>"]),
    ("tag", RE("<%[a-z]"), [">"]),
    ("tag", RE("</%"), [">"]),
    ("comment.multi-line", "<!--", ["-->"]),
    ("tag", RE("<[^/%]"), [">"]),
    ("tag", RE("</[^%]"), [">"]),
    ("comment.single-line", "##", [RE(r"(?=\n)")]),
]
