# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: roboconf.js
name = 'Roboconf'
file_patterns = ['*.roboconf', '*.graph', '*.instances']

flags = re.IGNORECASE | re.MULTILINE

class _attribute0:
    default_text_color = DELIMITER
    rules = [('_attribute', [RE(r"\s*:")])]
_attribute0.__name__ = '_attribute'

class attribute0:
    default_text_color = DELIMITER
    rules = [('attribute', RE(r"[a-zA-Z-_]+"), [_attribute0])]
attribute0.__name__ = 'attribute'

class _group1:
    default_text_color = DELIMITER
    rules = [
        ('variable', [RE(r"\.[a-zA-Z-_]+")]),
        ('keyword', [RE(r"\(optional\)")]),
    ]

attribute1 = ('attribute', attribute0, [RE(r";")], _group1)

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

comment0 = ('comment', RE(r"#"), [RE(r"$")], comment)

class _group0:
    default_text_color = DELIMITER
    rules = [('keyword', ['facet']), attribute1, comment0]

keyword2 = """
    name count channels instance-data instance-state instance of
    """.split()

class _group3:
    default_text_color = DELIMITER
    rules = [('keyword', keyword2), attribute1, comment0]

class _group4:
    default_text_color = DELIMITER
    rules = [attribute1, comment0]

rules = [
    ('keyword', ['import']),
    ('_group0', RE(r"^facet [a-zA-Z-_][^\n{]+\{"), [RE(r"}")], _group0),
    ('_group3', RE(r"^\s*instance of [a-zA-Z-_][^\n{]+\{"), [RE(r"}")], _group3),
    ('_group4', RE(r"^[a-zA-Z-_][^\n{]+\{"), [RE(r"}")], _group4),
    comment0,
]