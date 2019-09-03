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

class definition_rules:
    ag_filetype_options = ["--py"]
    delimiters = [
        (r"\bclass[ \t]+", r"[ \t]*[(:]"),
        (r"\bdef[ \t]+", r"[ \t]*\("),
        (r"\b", r"[ \t]*="),
    ]

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

_keywords = ("keyword", """
    and       del       from      not       while    
    as        elif      global    or        with     
    assert    else      if        pass      yield    
    break     except    import    class     in       
    raise     continue  finally   is        return   
    def       for       lambda    try       nonlocal
""".split())

_builtins = ("builtin", "self True False None".split())

class FString:
    # https://www.python.org/dev/peps/pep-0498/
    default_text_color = DELIMITER
    rules = PyString.rules + [
        ("operator.escape", ["{{", "}}"]),
    ]

_strings = [
    ("string.multiline.double-quote", RE(r'(?<!r)[bu]?"""'), ['"""'], PyString),
    ("string.multiline.single-quote", RE(r"(?<!r)[bu]?'''"), ["'''"], PyString),
    ("string.double-quote", RE(r'(?<!r)[bu]?"'), [RE(r'"|$')], PyString),
    ("string.single-quote", RE(r"(?<!r)[bu]?'"), [RE(r"'|$")], PyString),
    ("string.multiline.double-quote", RE(r'(?<!r)f"""'), ['"""'], FString),
    ("string.multiline.single-quote", RE(r"(?<!r)f'''"), ["'''"], FString),
    ("string.double-quote", RE(r'(?<!r)f"'), [RE(r'"|$')], FString),
    ("string.single-quote", RE(r"(?<!r)f'"), [RE(r"'|$")], FString),
    ("string.multiline.double-quote", RE(r'(?:br|rb|ur|ru|r)"""'), ['"""'], "regular-expression"),
    ("string.multiline.single-quote", RE(r"(?:br|rb|ur|ru|r)'''"), ["'''"], "regular-expression"),
    ("string.double-quote", RE(r'(?:br|rb|ur|ru|r)"'), [RE(r'"|$')], "regular-expression"),
    ("string.single-quote", RE(r"(?:br|rb|ur|ru|r)'"), [RE(r"'|$")], "regular-expression"),
]

# TODO regex f-strings
# TODO highlight format string delimiters?

# TODO convert to syntax definition with support for nested arguments
# https://docs.python.org/3/library/string.html#format-specification-mini-language
format_spec = RE(compact_regex(r"""
    (?:![rsa])?             # conversion
    (?::                    # format spec
        (?:
            [^}{]?          # fill
            [<>=^]          # align
        )?
        [+\- ]?             # sign
        \#?                 # alternate form
        0?
        (?:\d+)?            # width
        [_,]?
        (?:\.\d+)?          # precision
        [bcdeEfFgGnosxX%]?  # type
    )?
    (?:}|$)                 # end delimiter or EOL
"""))

class Expression:
    default_text_color = "text_color"
    rules = [
        _keywords,
        _builtins,
    ] + _strings

Expression.rules.extend(
    ("text_color", rhs, [lhs], Expression) for rhs, lhs in ["()", "{}"]
)

FString.rules.append(
    ("group.expression", "{", [format_spec], Expression)
)

rules = [
    _keywords,
    _builtins,
    ("comment.single-line", [RE("#.*")]),
    #("operator", "== != < > <= >=".split()),
] + _strings
