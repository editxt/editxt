# EditXT
# Copyright 2007-2015 Daniel Miller <millerdev@gmail.com>
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

name = "Regular Expression"
file_patterns = []

word_groups = [
    ("keyword", list(r".^$*+?|") + [
        RE(r"\{\d+(,\d+)?\}"),
    ]),
    ("operator.class", [
        RE(r"\\[AbBdDsSwWZafnrtv]"),
    ]),
    ("operator.escape.char", [
        RE(r"\\x[0-9a-fA-F]{2}"),
        RE(r"\\u[0-9a-fA-F]{4}"),
        RE(r"\\U[0-9a-fA-F]{8}"),
        RE(r"\\([0-7]{3}|0\d{1,2})"),
    ]),
    ("group", [
        RE(r"\\[1-9]\d?"),
    ]),
    ("header", [
        RE(r"\(\?[aiLmsux]+\)")
    ]),
    ("operator.escape", [
        RE(r"\\."), # NOTE this pattern should be last (in word_groups)
    ]),
]

class name_:
    word_groups = [("name", [RE(r"[a-zA-Z_]\w+")])]

class named_group:
    delimited_ranges = [
        ("group.named", RE(r"\(\?P<(?=[a-zA-Z_]\w+>)"), [">"], name_),
        ("group.named", RE(r"\(\?P=(?=[a-zA-Z_]\w+\))"), [RE("(?=\))")], name_),
    ]

class charset:
    word_groups = [
        ("operator.range", [
            RE(r"(?<![\[^\\])-(?![\]])")
        ]),
        ("operator.class", [
            RE(r"\\[AbBdDsSwWZafnrtv]"),
        ]),
        ("operator.escape.char", [
            RE(r"\\x[0-9a-fA-F]{2}"),
            RE(r"\\u[0-9a-fA-F]{4}"),
            RE(r"\\U[0-9a-fA-F]{8}"),
            RE(r"\\([0-7]{3}|0\d{1,2})"),
        ]),
        ("operator.escape", [
            RE(r"\\."), # NOTE this pattern should be last (in word_groups)
        ]),
    ]

delimited_ranges = [
    ("group", RE(r"\((?!\?)"), [")"], "regular-expression"),
    ("keyword.set.inverse", "[^", ["]"], charset),
    ("keyword.set", "[", ["]"], charset),
    ("group.ahead", RE(r"\(\?="), [")"], "regular-expression"),
    ("group.not-ahead", RE(r"\(\?!"), [")"], "regular-expression"),
    ("group.behind", RE(r"\(\?<="), [")"], "regular-expression"),
    ("group.not-behind", RE(r"\(\?<!"), [")"], "regular-expression"),
    ("group.anon", RE(r"\(\?:"), [")"], "regular-expression"),
    ("group.named", named_group, [")"], "regular-expression"),
    ("group.conditional", RE(r"\(\?\((?:[1-9]\d?|[a-zA-Z_]\w*)\)"),
        [")"], "regular-expression"),
    ("comment", RE(r"\(\?#"), [")"]),
]