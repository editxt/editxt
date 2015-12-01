# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: erlang-repl.js
name = 'Erlang REPL'
file_patterns = ['*.erlang-repl']

built_in = ['spawn', 'spawn_link', 'self']

keyword = [
    'after',
    'and',
    'andalso',
    'band',
    'begin',
    'bnot',
    'bor',
    'bsl',
    'bsr',
    'bxor',
    'case',
    'catch',
    'cond',
    'div',
    'end',
    'fun',
    'if',
    'let',
    'not',
    'of',
    'or',
    'orelse',
    'query',
    'receive',
    'rem',
    'try',
    'when',
    'xor',
]

meta = [RE(r"^[0-9]+> ")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

number = [RE(r"\b(\d+#[a-fA-F0-9]+|\d+(\.\d+)?([eE][-+]?\d+)?)")]

class string:
    default_text = DELIMITER
    rules = [
        # {'relevance': 0, 'begin': '\\\\[\\s\\S]'},
    ]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('meta', meta),
    ('comment', RE(r"%"), [RE(r"$")], comment),
    ('number', number),
    ('string', RE(r"'"), [RE(r"'")]),
    ('string', RE(r"\""), [RE(r"\"")], string),
]

# TODO merge "word_groups" and "delimited_ranges" into "rules" in editxt.syntax
assert "__obj" not in globals()
assert "__fixup" not in globals()
def __fixup(obj):
    groups = []
    ranges = []
    rules = getattr(obj, "rules", [])
    for i, rng in reversed(list(enumerate(rules))):
        if len(rng) == 2:
            groups.append(rng)
        else:
            assert len(rng) > 2, rng
            ranges.append(rng)
    return groups, ranges

class __obj:
    rules = globals().get("rules", [])
word_groups, delimited_ranges = __fixup(__obj)

for __obj in globals().values():
    if hasattr(__obj, "rules"):
        __obj.word_groups, __obj.delimited_ranges = __fixup(__obj)

del __obj, __fixup
