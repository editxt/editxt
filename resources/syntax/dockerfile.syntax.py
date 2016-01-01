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
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

keyword0 = """
    run cmd entrypoint volume add copy workdir onbuild label
    """.split()

class _group0:
    default_text_color = DELIMITER
    rules = [('keyword', keyword0)]

class _group00:
    default_text_color = DELIMITER
    rules = [
        ('_group0', RE(r"^ *(?:onbuild +)?(?:run|cmd|entrypoint|volume|add|copy|workdir|label) +"), [RE(r"\B|\b")], _group0),
    ]
_group00.__name__ = '_group0'

keyword1 = ['from', 'maintainer', 'expose', 'env', 'user', 'onbuild']

number = [RE(r"\b\d+(?:\.\d+)?")]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class _group1:
    default_text_color = DELIMITER
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
    ('_group0', _group00, [RE(r"[^\\]\n")], 'bash'),
    ('_group1', RE(r"^ *(?:onbuild +)?(?:from|maintainer|expose|env|user|onbuild) +"), [RE(r"[^\\]\n")], _group1),
]

_group1.rules[4] = rules[1]
