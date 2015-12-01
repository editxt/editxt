# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: nginx.js
name = 'Nginx'
file_patterns = ['*.nginx', '*.nginxconf']

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

section = [RE(r"[a-zA-Z_]\w*")]

class _group0:
    default_text = DELIMITER
    rules = [('section', section)]

class attribute:
    default_text = DELIMITER
    rules = [('attribute', RE(r"[a-zA-Z_]\w*"), [RE(r"\B|\b")])]

literal = [
    'on',
    'off',
    'yes',
    'no',
    'true',
    'false',
    'none',
    'blocked',
    'debug',
    'info',
    'notice',
    'warn',
    'error',
    'crit',
    'select',
    'break',
    'last',
    'permanent',
    'redirect',
    'kqueue',
    'rtsig',
    'epoll',
    'poll',
    '/dev/poll',
]

variable = [RE(r"\$\d+")]

variable0 = [RE(r"[\$\@][a-zA-Z_]\w*")]

class string:
    default_text = DELIMITER
    rules = [
        ('variable', variable),
        ('variable', RE(r"\$\{"), [RE(r"}")]),
        ('variable', variable0),
    ]

class _group5:
    default_text = DELIMITER
    rules = [
        None,  # ('variable', variable),
    ]

class regexp:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
        None,  # ('variable', variable),
    ]

number = [RE(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?\b")]

number0 = [RE(r"\b\d+[kKmMgGdshdwy]*\b")]

class _group2:
    default_text = DELIMITER
    rules = [
        ('literal', literal),
        None,  # rules[0],
        ('string', RE(r"\""), [RE(r"\"")], string),
        ('string', RE(r"'"), [RE(r"'")], string),
        ('_group5', RE(r"([a-z]+):/"), [RE(r"(?=\s)")], _group5),
        ('regexp', RE(r"\s\^"), [RE(r"(?=\s|{|;)")], regexp),
        ('regexp', RE(r"~\*?\s+"), [RE(r"(?=\s|{|;)")], regexp),
        ('regexp', RE(r"\*(\.[a-z\-]+)+"), [RE(r"\B|\b")], regexp),
        ('regexp', RE(r"([a-z\-]+\.)+\*"), [RE(r"\B|\b")], regexp),
        ('number', number),
        ('number', number0),
        None,  # ('variable', variable),
    ]

class _group1:
    default_text = DELIMITER
    rules = [('attribute', attribute, [RE(r"(?=;|{)")], _group2)]

rules = [
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('_group0', RE(r"(?=[a-zA-Z_]\w*\s+{)"), [RE(r"{")], _group0),
    ('_group1', RE(r"(?=[a-zA-Z_]\w*\s)"), [RE(r";|{")], _group1),
]

_group2.rules[1] = rules[0]
_group5.rules[0] = ('variable', variable0)
regexp.rules[0] = ('variable', variable0)
_group2.rules[11] = ('variable', variable0)

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
