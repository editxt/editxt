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
import re

name = "Markup"
file_patterns = ["*.html", "*.htm", "*.plist", "*.xml"]
comment_token = "" #("<!--", "-->")
flags = re.IGNORECASE | re.MULTILINE

class attributes:
    rules = [
        ("attribute", [RE(r"[\w.:-]+")]),
        ("tag.punctuation", "="),
        ("value", [RE(r"(?<==)\s*'[^']*'")]),
        ("value", [RE(r'(?<==)\s*"[^"]*"')]),
        ("value", [RE(r"(?<==)\s*[^\s/>]+")]),
    ]

class cdata:
    rules = []

def tag(name):
    class tag:
        rules = [
            ("tag", RE(r"<{}\b".format(name)), [">"], attributes)
        ]
    tag.__name__ = name
    return tag

rules = [
    ("tag", [RE(r"</[\w.:-]+\s*>")]),

    ("tag.doctype", RE(r"<!DOCTYPE\b"), [">"], attributes),
    ("comment", RE("<!--"), ["-->"]),
    ("tag.cdata", RE(r"<!\[CDATA\["), [RE(r"\]\]>")], cdata),
    ("tag", tag("style"), ["</style>"], "css"),
    ("tag", tag("script"), ["</script>"], "javascript"),
    ("tag", RE(r"<[\w.:-]+(?=\s|/?>|$)"), [
        RE(r"/?>"),
        RE(r"(?=<[\w.:!-])"),
    ], attributes),
    #("tag.pi", RE(r"<\?\w+"), ["\?>"], attributes),
]
