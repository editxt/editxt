# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: lua.js
name = 'Lua'
file_patterns = ['*.lua']

built_in = [
    '_G',
    '_VERSION',
    'assert',
    'collectgarbage',
    'dofile',
    'error',
    'getfenv',
    'getmetatable',
    'ipairs',
    'load',
    'loadfile',
    'loadstring',
    'module',
    'next',
    'pairs',
    'pcall',
    'print',
    'rawequal',
    'rawget',
    'rawset',
    'require',
    'select',
    'setfenv',
    'setmetatable',
    'tonumber',
    'tostring',
    'type',
    'unpack',
    'xpcall',
    'coroutine',
    'debug',
    'io',
    'math',
    'os',
    'package',
    'string',
    'table',
]

keyword = [
    'and',
    'break',
    'do',
    'else',
    'elseif',
    'end',
    'false',
    'for',
    'if',
    'in',
    'local',
    'nil',
    'not',
    'or',
    'repeat',
    'return',
    'then',
    'true',
    'until',
    'while',
]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

class _group0:
    default_text = DELIMITER
    rules = []

class comment0:
    default_text = DELIMITER
    rules = [
        ('_group0', RE(r"\[=*\["), [RE(r"\]=*\]")], _group0),
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]
comment0.__name__ = 'comment'

keyword0 = ['function']

title = [RE(r"([_a-zA-Z]\w*\.)*([_a-zA-Z]\w*:)?[_a-zA-Z]\w*")]

class params:
    default_text = DELIMITER
    rules = [
        None,  # rules[2],
        None,  # rules[3],
    ]

class function:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('title', title),
        ('params', RE(r"\("), [RE(r"")], params),
        None,  # rules[2],
        None,  # rules[3],
    ]

number = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class string0:
    default_text = DELIMITER
    rules = [
        None,  # comment0.rules[0],
    ]
string0.__name__ = 'string'

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('comment', RE(r"--(?!\[=*\[)"), [RE(r"$")], comment),
    ('comment', RE(r"--\[=*\["), [RE(r"\]=*\]")], comment0),
    ('function', RE(r"\b(function)"), [RE(r"\)")], function),
    ('number', number),
    ('string', RE(r"'"), [RE(r"'")]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', RE(r"\[=*\["), [RE(r"\]=*\]")], string0),
]

params.rules[0] = rules[2]
params.rules[1] = rules[3]
function.rules[3] = rules[2]
function.rules[4] = rules[3]
string0.rules[0] = comment0.rules[0]

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
