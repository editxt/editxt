# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: java.js
name = 'Java'
file_patterns = ['*.java', '*.jsp']

keyword = [
    'false',
    'synchronized',
    'int',
    'abstract',
    'float',
    'private',
    'char',
    'boolean',
    'static',
    'null',
    'if',
    'const',
    'for',
    'true',
    'while',
    'long',
    'strictfp',
    'finally',
    'protected',
    'import',
    'native',
    'final',
    'void',
    'enum',
    'else',
    'break',
    'transient',
    'catch',
    'instanceof',
    'byte',
    'super',
    'volatile',
    'case',
    'assert',
    'short',
    'package',
    'default',
    'double',
    'public',
    'try',
    'this',
    'switch',
    'continue',
    'throws',
    'protected',
    'public',
    'private',
]

doctag = [RE(r"@[A-Za-z]+")]

doctag0 = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag), ('doctag', doctag0)]

class comment0:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag0),
    ]
comment0.__name__ = 'comment'

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

keyword0 = ['class', 'interface']

title = [RE(r"[a-zA-Z_]\w*")]

class class0:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('_group2', RE(r"\b(extends|implements)"), [RE(r"\B|\b")]),
        ('title', title),
    ]
class0.__name__ = 'class'

class _group4:
    default_text = DELIMITER
    rules = [
        None,  # ('title', title),
    ]

number = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

class params:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword),
        None,  # rules[4],
        None,  # rules[5],
        ('number', number),
        None,  # rules[3],
    ]

class function:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword),
        ('_group4', RE(r"(?=[a-zA-Z_]\w*\s*\()"), [RE(r"\B|\b")], _group4),
        ('params', RE(r"\("), [RE(r"\)")], params),
        None,  # rules[2],
        None,  # rules[3],
    ]

number0 = [
    RE(r"\b(0[bB]([01]+[01_]+[01]+|[01]+)|0[xX]([a-fA-F0-9]+[a-fA-F0-9_]+[a-fA-F0-9]+|[a-fA-F0-9]+)|(([\d]+[\d_]+[\d]+|[\d]+)(\.([\d]+[\d_]+[\d]+|[\d]+))?|\.([\d]+[\d_]+[\d]+|[\d]+))([eE][-+]?\d+)?)[lLfF]?"),
]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"/\*\*"), [RE(r"\*/")], comment),
    ('comment', RE(r"//"), [RE(r"$")], comment0),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
    ('string', RE(r"'"), [RE(r"'")]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('class', RE(r"\b(class|interface)"), [RE(r"(?=[{;=])")], class0),
    ('_group3', RE(r"\b(new|throw|return|else)"), [RE(r"\B|\b")]),
    ('function', RE(r"(?=([a-zA-Z_]\w*(<[a-zA-Z_]\w*>)?\s+)+[a-zA-Z_]\w*\s*\()"), [RE(r"(?=[{;=])")], function),
    ('number', number0),
    ('meta', doctag),
]

_group4.rules[0] = ('title', title)
params.rules[1] = rules[4]
params.rules[2] = rules[5]
params.rules[4] = rules[3]
function.rules[3] = rules[2]
function.rules[4] = rules[3]

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
