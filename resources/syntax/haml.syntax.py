# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: haml.js
name = 'Haml'
file_patterns = ['*.haml']

flags = re.IGNORECASE | re.MULTILINE

meta = [
    RE(r"^!!!(?: (?:5|1\.1|Strict|Frameset|Basic|Mobile|RDFa|XML\b.*))?$"),
]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class _group0:
    default_text = DELIMITER
    rules = [('_group0', RE(r"^\s*(?:-|=|!=)(?!#)"), [RE(r"\B\b")])]

class _group1:
    default_text = DELIMITER
    rules = []

selector_tag = [RE(r"\w+")]

selector_id = [RE(r"#[\w-]+")]

selector_class = [RE(r"\.[\w-]+")]

attr = [RE(r":\w+")]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class _group3:
    default_text = DELIMITER
    rules = [
        ('attr', attr),
        ('string', RE(r"'"), [RE(r"'")], string),
        ('string', RE(r"\""), [RE(r"\"")], string),
        # {'begin': '\\w+', 'relevance': 0},
    ]

class _group2:
    default_text = DELIMITER
    rules = [('_group3', RE(r"(?=:\w+\s*=>)"), [RE(r",\s+")], _group3)]

class _group7:
    default_text = DELIMITER
    rules = [
        ('attr', selector_tag),
        _group3.rules[1],
        _group3.rules[2],
        # {'begin': '\\w+', 'relevance': 0},
    ]

class _group6:
    default_text = DELIMITER
    rules = [('_group7', RE(r"(?=\w+\s*=)"), [RE(r"\s+")], _group7)]

class tag:
    default_text = DELIMITER
    rules = [
        ('selector-tag', selector_tag),
        ('selector-id', selector_id),
        ('selector-class', selector_class),
        ('_group2', RE(r"{\s*"), [RE(r"\s*}")], _group2),
        ('_group6', RE(r"\(\s*"), [RE(r"\s*\)")], _group6),
    ]

class _group9:
    default_text = DELIMITER
    rules = [('_group9', RE(r"#{"), [RE(r"\B\b")])]

class _group10:
    default_text = DELIMITER
    rules = []

rules = [
    ('meta', meta),
    ('comment', RE(r"^\s*(?:!=#|=#|-#|/).*$"), [RE(r"\B\b")], comment),
    ('_group0', _group0, [RE(r"\n")], _group1),
    ('tag', RE(r"^\s*%"), [RE(r"\B\b")], tag),
    # {'begin': '^\\s*[=~]\\s*'},
    ('_group9', _group9, [RE(r"}")], _group10),
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
