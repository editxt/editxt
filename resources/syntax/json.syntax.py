# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: json.js
name = 'JSON'
file_patterns = ['*.json']

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

class _attr0:
    default_text_color = DELIMITER
    rules = [('_attr', [RE(r"\s*\"")])]
_attr0.__name__ = '_attr'

class _attr2:
    default_text_color = DELIMITER
    rules = [('_attr', [RE(r"\"\s*:\s*")])]
_attr2.__name__ = '_attr'

class attr:
    default_text_color = DELIMITER
    rules = [operator_escape]

class attr1:
    default_text_color = DELIMITER
    rules = [('attr', _attr0, [_attr2], attr)]
attr1.__name__ = 'attr'

class _group1:
    default_text_color = DELIMITER
    ends_with_parent = True
    rules = [('literal', ['true', 'false', 'null'])]

class _group0:
    default_text_color = DELIMITER
    rules = [('attr', attr1, [RE(r",")], _group1)]

class _group3:
    default_text_color = DELIMITER
    ends_with_parent = True
    rules = [('literal', ['true', 'false', 'null'])]

class _group2:
    default_text_color = DELIMITER
    rules = [('_group3', RE(r"\B|\b"), [RE(r",")], _group3)]

rules = [
    ('literal', ['true', 'false', 'null']),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    ('_group0', RE(r"{"), [RE(r"}")], _group0),
    ('_group2', RE(r"\["), [RE(r"\]")], _group2),
]

_group1.rules.extend(rules)
_group3.rules.extend(rules)
