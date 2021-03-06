# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: http.js
name = 'HTTP'
file_patterns = ['*.http', '*.https']

class _group0:
    default_text_color = DELIMITER
    rules = [('number', [RE(r"\b\d{3}\b")])]

class _string0:
    default_text_color = DELIMITER
    rules = [('_string', [RE(r" ")])]
_string0.__name__ = '_string'

class _group1:
    default_text_color = DELIMITER
    rules = [
        ('string', _string0, [_string0]),
        # ignore {'begin': 'HTTP/[0-9\\.]+'},
        ('keyword', [RE(r"[A-Z]+")]),
    ]

class _attribute0:
    default_text_color = DELIMITER
    rules = [('_attribute', [RE(r": ")])]
_attribute0.__name__ = '_attribute'

class attribute0:
    default_text_color = DELIMITER
    rules = [('attribute', RE(r"^\w"), [_attribute0])]
attribute0.__name__ = 'attribute'

class _group40:
    default_text_color = DELIMITER
    rules = [('_group4', RE(r"\n\n"), [RE(r"\B|\b")])]
_group40.__name__ = '_group4'

rules = [
    ('_group0', RE(r"^HTTP/[0-9\.]+"), [RE(r"$")], _group0),
    ('_group1', RE(r"(?=^[A-Z]+ (?:.*?) HTTP/[0-9\.]+$)"), [RE(r"$")], _group1),
    ('attribute', attribute0, [RE(r"$")]),
    ('_group4', _group40, [RE(r"\B|\b")]),
]
