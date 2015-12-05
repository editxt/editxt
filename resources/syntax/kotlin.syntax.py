# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: kotlin.js
name = 'Kotlin'
file_patterns = ['*.kotlin']

keyword = """
    val var get set class trait object open private protected public
    final enum if else do while for when break continue throw try catch
    finally import package is as in return fun override default
    companion reified inline volatile transient native Byte Short Char
    Int Long Boolean Float Double Void Unit Nothing
    """.split()

literal = ['true', 'false', 'null']

doctag = [RE(r"@[A-Za-z]+")]

doctag0 = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        ('doctag', doctag),
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag0),
    ]

class comment0:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag0),
    ]
comment0.__name__ = 'comment'

class _function:
    default_text = DELIMITER
    rules = [('_function', RE(r"[(?:]|$"), [RE(r'\b|\B')])]

title = [RE(r"[a-zA-Z_]\w*")]

class _group0:
    default_text = DELIMITER
    rules = [('title', title)]

keyword0 = ['reified']

class type:
    default_text = DELIMITER
    rules = [('keyword', keyword0)]

class _type:
    default_text = DELIMITER
    rules = [('_type', RE(r":\s*"))]

class params:
    default_text = DELIMITER
    rules = [('keyword', keyword), ('type', _type, [RE(r"(?=\s*[=\)])")])]

class function:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword),
        ('_group0', RE(r"(?=[a-zA-Z_]\w*\s*\()"), [RE(r"\B\b")], _group0),
        ('type', RE(r"<"), [RE(r">")], type),
        ('params', RE(r"\("), [RE(r"\)")], params),
        None,  # rules[3],
        None,  # rules[4],
    ]

class _class:
    default_text = DELIMITER
    rules = [('_class', RE(r"[:\{(?:]|$"), [RE(r'\b|\B')])]

keyword1 = ['class', 'trait']

class _type0:
    default_text = DELIMITER
    rules = [('_type', RE(r"[,:]\s*"))]
_type0.__name__ = '_type'

class class0:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword1),
        ('title', title),
        ('_type', RE(r"<"), [RE(r">")]),
        ('type', _type0, [RE(r"(?=[<\(,]|$)")]),
    ]
class0.__name__ = 'class'

class _variable:
    default_text = DELIMITER
    rules = [('_variable', RE(r"\s*[=:$]"), [RE(r'\b|\B')])]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

rules = [
    ('keyword', keyword),
    ('literal', literal),
    ('comment', RE(r"/\*\*"), [RE(r"\*/")], comment),
    ('comment', RE(r"//"), [RE(r"$")], comment0),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
    ('type', RE(r"(?=<)"), [RE(r">")]),
    ('function', RE(r"(?=\b(?:fun))"), [_function], function),
    ('class', RE(r"\b(?:class|trait)"), [_class], class0),
    ('variable', RE(r"\b(?:var|val)"), [_variable]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('meta', RE(r"^#!/usr/bin/env"), [RE(r"$")]),
    ('number', number),
]

function.rules[4] = rules[3]
function.rules[5] = rules[4]

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
