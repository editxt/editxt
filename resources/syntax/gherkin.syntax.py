# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: gherkin.js
name = 'Gherkin'
file_patterns = ['*.gherkin', '*.feature']

keyword = [
    'Feature',
    'Background',
    'Ability',
    'Business',
    'Need',
    'Scenario',
    'Scenarios',
    'Scenario',
    'Outline',
    'Scenario',
    'Template',
    'Examples',
    'Given',
    'And',
    'Then',
    'But',
    'When',
]

keyword0 = [RE(r"\*")]

meta = [RE(r"@[^@\s]+")]

string = [RE(r"[^|]+")]

class _group0:
    default_text = DELIMITER
    rules = [('string', string)]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

rules = [
    ('keyword', keyword),
    ('keyword', keyword0),
    ('meta', meta),
    ('_group0', RE(r"\|"), [RE(r"\|\w*$")], _group0),
    ('variable', RE(r"<"), [RE(r">")]),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('string', RE(r"\"\"\""), [RE(r"\"\"\"")]),
    ('string', RE(r"\""), [RE(r"\"")]),
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
