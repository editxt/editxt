# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: dockerfile.js
name = 'Dockerfile'
file_patterns = ['*.dockerfile', '*.docker']

flags = re.IGNORECASE | re.MULTILINE

keyword = """
    from maintainer cmd expose add copy entrypoint volume user workdir
    onbuild run env label
    """.split()

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

keyword0 = """
    run cmd entrypoint volume add copy workdir onbuild label
    """.split()

class _group0:
    default_text = DELIMITER
    rules = [('keyword', keyword0)]

class _group00:
    default_text = DELIMITER
    rules = [
        ('_group0', RE(r"^ *(?:onbuild +)?(?:run|cmd|entrypoint|volume|add|copy|workdir|label) +"), [RE(r"\B\b")], _group0),
    ]
_group00.__name__ = '_group0'

class _group1:
    default_text = DELIMITER
    rules = []

keyword1 = ['from', 'maintainer', 'expose', 'env', 'user', 'onbuild']

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

number = [RE(r"\b\d+(?:\.\d+)?")]

class _group2:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword1),
        ('string', RE(r"'"), [RE(r"'")], string),
        ('string', RE(r"\""), [RE(r"\"")], string),
        ('number', number),
        None,  # rules[1],
    ]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('_group0', _group00, [RE(r"[^\\]\n")], _group1),
    ('_group2', RE(r"^ *(?:onbuild +)?(?:from|maintainer|expose|env|user|onbuild) +"), [RE(r"[^\\]\n")], _group2),
]

_group2.rules[4] = rules[1]

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
