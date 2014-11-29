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
import AppKit as ak
import Foundation as fn
import CommonMark as commonmark

AttributedString = ak.NSAttributedString

def markdown(value, pre=False):
    parser = commonmark.DocParser()
    renderer = commonmark.HTMLRenderer()
    if pre:
        value = value.replace("\n", "\\\n")
    html = renderer.render(parser.parse(value))
    if pre:
        html = "<div style='font-family: Monaco; whitespace: pre;'>{}</div>".format(html)
    data = fn.NSString.stringWithString_(html) \
             .dataUsingEncoding_(fn.NSUTF8StringEncoding)
    options = {
        "NSDocumentTypeDocumentAttribute": ak.NSHTMLTextDocumentType,
        "NSCharacterEncodingDocumentAttribute": fn.NSUTF8StringEncoding,
    }
    return ak.NSAttributedString.alloc() \
        .initWithHTML_options_documentAttributes_(data, options, None)[0]
