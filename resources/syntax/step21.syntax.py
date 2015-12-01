# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: step21.js
name = 'STEP Part 21 (ISO 10303-21)'
file_patterns = ['*.step21', '*.p21', '*.step', '*.stp']

flags = re.IGNORECASE | re.MULTILINE

keyword = ['HEADER', 'ENDSEC', 'DATA']

meta = [RE(r"ISO-10303-21;")]

meta0 = [RE(r"END-ISO-10303-21;")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

class comment0:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]
comment0.__name__ = 'comment'

number = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

rules = [
    ('keyword', keyword),
    ('meta', meta),
    ('meta', meta0),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
    ('comment', RE(r"/\*\*!"), [RE(r"\*/")], comment0),
    ('number', number),
    ('string', RE(r"'"), [RE(r"'")]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', RE(r"'"), [RE(r"'")]),
    ('symbol', RE(r"#"), [RE(r"\d+")]),
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
