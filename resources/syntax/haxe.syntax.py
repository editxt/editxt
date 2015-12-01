# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: haxe.js
name = 'Haxe'
file_patterns = ['*.haxe', '*.hx']

keyword = [
    'break',
    'callback',
    'case',
    'cast',
    'catch',
    'class',
    'continue',
    'default',
    'do',
    'dynamic',
    'else',
    'enum',
    'extends',
    'extern',
    'for',
    'function',
    'here',
    'if',
    'implements',
    'import',
    'in',
    'inline',
    'interface',
    'never',
    'new',
    'override',
    'package',
    'private',
    'public',
    'return',
    'static',
    'super',
    'switch',
    'this',
    'throw',
    'trace',
    'try',
    'typedef',
    'untyped',
    'using',
    'var',
    'while',
]

literal = ['true', 'false', 'null']

class string:
    default_text = DELIMITER
    rules = [
        # {'relevance': 0, 'begin': '\\\\[\\s\\S]'},
    ]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

class comment0:
    default_text = DELIMITER
    rules = [
        # {'begin': {'type': 'RegExp', 'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b"}},
        ('doctag', doctag),
    ]
comment0.__name__ = 'comment'

number = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

keyword0 = ['class', 'interface']

title = [RE(r"[a-zA-Z]\w*")]

class class0:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('_group1', RE(r"\b(extends|implements)"), [RE(r"\B|\b")]),
        ('title', title),
    ]
class0.__name__ = 'class'

meta_keyword = ['if', 'else', 'elseif', 'end', 'error']

class meta:
    default_text = DELIMITER
    rules = [('meta-keyword', meta_keyword)]

keyword1 = ['function']

class params:
    default_text = DELIMITER
    rules = [
        None,  # rules[2],
        None,  # rules[3],
        None,  # rules[4],
        None,  # rules[5],
    ]

class function:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword1),
        None,  # ('title', title),
        ('params', RE(r"\("), [RE(r"\)")], params),
    ]

rules = [
    ('keyword', keyword),
    ('literal', literal),
    ('string', RE(r"'"), [RE(r"'")]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
    ('number', number),
    ('class', RE(r"\b(class|interface)"), [RE(r"(?={)")], class0),
    ('meta', RE(r"#"), [RE(r"$")], meta),
    ('function', RE(r"\b(function)"), [RE(r"(?=[{;])")], function),
]

function.rules[1] = ('title', title)
params.rules[0] = rules[2]
params.rules[1] = rules[3]
params.rules[2] = rules[4]
params.rules[3] = rules[5]

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
