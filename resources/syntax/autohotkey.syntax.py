# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: autohotkey.js
name = 'AutoHotkey'
file_patterns = ['*.autohotkey']

flags = re.IGNORECASE | re.MULTILINE

keyword = ['Break', 'Continue', 'Else', 'Gosub', 'If', 'Loop', 'Return', 'While']

literal = ['A', 'true', 'false', 'NOT', 'AND', 'OR']

built_in = [RE(r"A_[a-zA-Z0-9]+")]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': '`[\\s\\S]', 'type': 'RegExp'}},
    ]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

number = [RE(r"\b\d+(?:\.\d+)?")]

class variable:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': '`[\\s\\S]', 'type': 'RegExp'}},
    ]

class symbol:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': '`[\\s\\S]', 'type': 'RegExp'}},
    ]

rules = [
    ('keyword', keyword),
    ('literal', literal),
    ('built_in', built_in),
    ('built_in', RE(r"\b(?:ComSpec|Clipboard|ClipboardAll|ErrorLevel)"), [RE(r"\B\b")]),
    # {'begin': {'pattern': '`[\\s\\S]', 'type': 'RegExp'}},
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('comment', RE(r";"), [RE(r"$")], comment),
    ('number', number),
    ('variable', RE(r"%"), [RE(r"%")], variable),
    ('symbol', RE(r"^[^\n\";]+::(?!=)"), [RE(r"\B\b")], symbol),
    ('symbol', RE(r"^[^\n\";]+:(?!=)"), [RE(r"\B\b")], symbol),
    # {'begin': ',\\s*,'},
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
