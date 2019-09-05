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
    and       as        assert    async     await     break     class
    continue  def       del       elif      else      except    finally
    for       from      global    if        import    in        is
    lambda    nonlocal  not       or        pass      raise     return
    try       while     with      yield
""".split())

_builtin_constants = (
    "builtin", "self True False None NotImplemented Ellipsis".split()
)

_builtin_functions = ("name", """
    __import__    abs           all           any           ascii
    bin           bool          breakpoint    bytearray     bytes
    callable      chr           classmethod   compile       complex
    delattr       dict          dir           divmod        enumerate
    eval          exec          filter        float         format
    frozenset     getattr       globals       hasattr       hash
    help          hex           id            input         int
    isinstance    issubclass    iter          len           list
    locals        map           max           memoryview    min
    next          object        oct           open          ord
    pow           print         property      range         repr
    reversed      round         set           setattr       slice
    sorted        staticmethod  str           sum           super
    tuple         type          vars          zip
""".split())

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
        _builtin_constants,
        _builtin_functions,
    ] + _strings

Expression.rules.extend(
    ("text_color", rhs, [lhs], Expression) for rhs, lhs in ["()", "{}"]
)

FString.rules.append(
    ("group.expression", "{", [format_spec], Expression)
)

rules = [
    _keywords,
    _builtin_constants,
    _builtin_functions,
    ("comment.single-line", [RE("#.*")]),
    #("operator", "== != < > <= >=".split()),
] + _strings


'''
def columnize(words):
    words = sorted(words)
    width = max(len(w) for w in words) + 2
    n_cols = int((79 - 4) / width)
    n_rows = int(len(words) / n_cols) + 1
    print("\n".join(
        "".join(
            f"{words[row * n_cols + col]:<{width}}"
            for col in range(n_cols)
            if row * n_cols + col < len(words)
        ).strip()
        for row in range(n_rows)
    ))
    print()

columnize("""
abs delattr hash memoryview set all dict help min setattr any dir hex next
slice ascii divmod id object sorted bin enumerate input oct staticmethod bool
eval int open str breakpoint exec isinstance ord sum bytearray filter
issubclass pow super bytes float iter print tuple callable format len property
type chr frozenset list range vars classmethod getattr locals repr zip compile
globals map reversed __import__ complex hasattr max round
""".split())

import keyword
columnize(k for k in keyword.kwlist if not k.istitle())
'''
