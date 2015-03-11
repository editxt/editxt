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

#colors:
#    505050 (gray)
#    1BBA03 (green text)
#    BA0004 (red text)
#    D6FFD5 (green background)
#    FEE9E9 (red background)
#    19BABA (bright cyan)
#    008080 (other cyan)
#    008000 (comment green)
#    0002BB (blue)
#    59069B (purple)

name = "Git Diff"
file_patterns = ["*.diff", "*.patch"]
delimited_ranges = [
    ("string.diff.header", RE('^diff '), [RE(r"$")]), # 505050
    ("string.diff.index", RE('^index '), [RE(r"$")]), # 505050
    # Uncomment these if you want something different for the ---/+++ lines
    ("diff.removed.file", RE(r'^--- '),  [RE(r"$")]), # 59069B (purple)
    ("diff.added.file", RE(r'^\+\+\+ '),  [RE(r"$")]), # 59069B (purple)
    ("diff.removed", RE(r'^-(?!-- )'),  [RE(r"$")]), # BA0004 (red)
    ("diff.added", RE(r'^\+(?!\+\+ )'),  [RE(r"$")]), # 1BBA03 (green)
    ("diff.what?", RE(r'^@@ '),  [RE(r" @@ |$")]), # 19BABA (bright cyan)
]
