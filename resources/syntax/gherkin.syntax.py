# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: gherkin.js
name = 'Gherkin'
file_patterns = ['*.gherkin', '*.feature']

keyword = """
    Feature Background Ability Business Need Scenario Scenarios Scenario
    Outline Scenario Template Examples Given And Then But When
    """.split()

class _group0:
    default_text_color = DELIMITER
    rules = [('string', [RE(r"[^|]+")])]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class string1:
    default_text_color = DELIMITER
    rules = [('operator.escape', [RE(r"\\[\s\S]")])]
string1.__name__ = 'string'

rules = [
    ('keyword', keyword),
    ('keyword', [RE(r"\*")]),
    ('meta', [RE(r"@[^@\s]+")]),
    ('_group0', RE(r"\|"), [RE(r"\|\w*$")], _group0),
    ('variable', RE(r"<"), [RE(r">")]),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('string', RE(r"\"\"\""), [RE(r"\"\"\"")]),
    ('string', RE(r"\""), [RE(r"\"")], string1),
]
