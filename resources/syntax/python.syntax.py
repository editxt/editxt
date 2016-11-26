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

name = "Python"
file_patterns = ["*.py", "*.pyw"]
comment_token = "#"

class PyString:
    default_text_color = DELIMITER
    rules = [
        ("operator.escape", [
            RE(r"""\\[\\'"abfnrtv]"""),
        ]),
        ("operator.escape.char", [
            RE(r"\\[0-7]{1,3}"),
            RE(r"\\x[0-9a-fA-F]{2}"),
            RE(r"\\u[0-9a-fA-F]{4}"),
            RE(r"\\U[0-9a-fA-F]{8}"),
        ]),
        ("operator.escape.continuation", [
            RE(r"\\(?:\n|\r\n|\r)"),
        ]),
    ]

rules = [
    ("keyword", """
        and       del       from      not       while    
        as        elif      global    or        with     
        assert    else      if        pass      yield    
        break     except    import    class     in       
        raise     continue  finally   is        return   
        def       for       lambda    try       nonlocal
    """.split()),
    ("builtin", "self True False None".split()),
    ("comment.single-line", [RE("#.*")]),
    #("operator", "== != < > <= >=".split()),

    ("string.multiline.double-quote", RE(r'(?<!r)[bu]?"""'), ['"""'], PyString),
    ("string.multiline.single-quote", RE(r"(?<!r)[bu]?'''"), ["'''"], PyString),
    ("string.double-quote", RE(r'(?<!r)[bu]?"'), [RE(r'"|$')], PyString),
    ("string.single-quote", RE(r"(?<!r)[bu]?'"), [RE(r"'|$")], PyString),
    ("string.multiline.double-quote", RE(r'(?:br|rb|ur|ru|r)"""'), ['"""'], "regular-expression"),
    ("string.multiline.single-quote", RE(r"(?:br|rb|ur|ru|r)'''"), ["'''"], "regular-expression"),
    ("string.double-quote", RE(r'(?:br|rb|ur|ru|r)"'), [RE(r'"|$')], "regular-expression"),
    ("string.single-quote", RE(r"(?:br|rb|ur|ru|r)'"), [RE(r"'|$")], "regular-expression"),
]
