# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: r.js
name = 'R'
file_patterns = ['*.r']

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

keyword = """
    function if in break next repeat else for return switch while try
    tryCatch stop warning require library attach detach source setMethod
    setGeneric setGroupGeneric setClass ...
    """.split()

literal = """
    NULL NA TRUE FALSE T F Inf NaN NA_integer_ NA_real_ NA_character_
    NA_complex_
    """.split()

class _group0:
    default_text = DELIMITER
    rules = [('keyword', keyword), ('literal', literal)]

number = [RE(r"0[xX][0-9a-fA-F]+[Li]?\b")]

number0 = [RE(r"\d+(?:[eE][+\-]?\d*)?L\b")]

number1 = [RE(r"\d+\.(?!\d)(?:i\b)?")]

number2 = [RE(r"\d+(?:\.\d*)?(?:[eE][+\-]?\d*)?i?\b")]

number3 = [RE(r"\.\d+(?:[eE][+\-]?\d*)?i?\b")]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

rules = [
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('_group0', RE(r"(?:[a-zA-Z]|\.[a-zA-Z.])[a-zA-Z0-9._]*"), [RE(r"\B\b")], _group0),
    ('number', number),
    ('number', number0),
    ('number', number1),
    ('number', number2),
    ('number', number3),
    ('_group1', RE(r"`"), [RE(r"`")]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', RE(r"'"), [RE(r"'")], string),
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
