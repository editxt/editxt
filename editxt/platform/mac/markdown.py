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
import re

import AppKit as ak
import Foundation as fn
import CommonMark as commonmark

AttributedString = ak.NSAttributedString

SPACE_RE = re.compile("  +")
NON_HARD_BREAK = re.compile(r"(?<!.\\|  )\n")

def markdown(value, pre=False, css=""):
    if pre:
        value = NON_HARD_BREAK.sub("\\\n", value.rstrip("\n"))
    parser = commonmark.DocParser()
    renderer = commonmark.HTMLRenderer()
    html = renderer.render(parser.parse(value))
    if pre:
        css = PRE_CSS + css
        # unfortunately we have to roll our own preformatted text
        # because `white-space: pre` renders double-spaced lines.
        def nbsp(match):
            num = len(match.group(0))
            if num % 2 == 0:
                return " \u00A0" * (num // 2)
            return " \u00A0" * (num // 2) + " "
        html = SPACE_RE.sub(nbsp, html)
    else:
        # TODO make the default font/size configurable
        css = DEFAULT_CSS + css
    html = HTML_TEMPLATE.format(css=css, body=html)
    data = fn.NSString.stringWithString_(html) \
             .dataUsingEncoding_(fn.NSUnicodeStringEncoding)
    options = {
        "NSDocumentTypeDocumentAttribute": ak.NSHTMLTextDocumentType,
        "NSCharacterEncodingDocumentAttribute": fn.NSUnicodeStringEncoding,
    }
    return ak.NSAttributedString.alloc() \
        .initWithHTML_options_documentAttributes_(data, options, None)[0]


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <style>{css}</style>
</head>
<body>{body}</body>
</html>
"""

PRE_CSS = """
body {
    font-family: "Lucida Console", Monaco, monospace;
}
a {
    text-decoration: none;
}
p:last-of-type {
    margin-bottom: 0;
    padding-bottom: 0;
}
"""

DEFAULT_CSS = """
body {
    font: 12pt sans-serif;
}
p:last-of-type {
    margin-bottom: 0;
    padding-bottom: 0;
}
"""