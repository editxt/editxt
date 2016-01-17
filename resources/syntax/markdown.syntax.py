# -*- coding: UTF-8 -*-
# Adapted from highlight.js markdown syntax definition
# source: markdown.js
name = 'Markdown'
file_patterns = ['*.markdown', '*.md', '*.mkdown', '*.mkd']

class _string0:
    default_text_color = DELIMITER
    rules = [('_string', [RE(r"\[")])]
_string0.__name__ = '_string'

class _link0:
    default_text_color = DELIMITER
    rules = [('_link', [RE(r"\]\(")])]
_link0.__name__ = '_link'

class _link2:
    default_text_color = DELIMITER
    rules = [('_link', [RE(r"\)")])]
_link2.__name__ = '_link'

class _symbol0:
    default_text_color = DELIMITER
    rules = [('_symbol', [RE(r"\]\[")])]
_symbol0.__name__ = '_symbol'

class _symbol2:
    default_text_color = DELIMITER
    rules = [('_symbol', [RE(r"\]")])]
_symbol2.__name__ = '_symbol'

class _group2:
    default_text_color = DELIMITER
    rules = [
        ('string', _string0, [RE(r"(?=\])")]),
        ('link', _link0, [_link2]),
        ('symbol', _symbol0, [_symbol2]),
    ]

class _symbol4:
    default_text_color = DELIMITER
    rules = [('_symbol', [RE(r"\[")])]
_symbol4.__name__ = '_symbol'

class _symbol6:
    default_text_color = DELIMITER
    rules = [('_symbol', [RE(r"\]:")])]
_symbol6.__name__ = '_symbol'

class symbol1:
    default_text_color = DELIMITER
    rules = [('symbol', _symbol4, [_symbol6])]
symbol1.__name__ = 'symbol'

class _group3:
    default_text_color = DELIMITER
    rules = [('symbol', symbol1, [RE(r"$")])]

rules = [
    ('section', RE(r"^#{1,6}"), [RE(r"$")]),
    ('_group0', RE(r"<"), [RE(r">")], 'xml'),
    ('bullet', [RE(r"^(?:[*+-]|(?:\d+\.))\s+")]),
    ('strong', [RE(r"[*_]{2}.+?[*_]{2}")]),
    ('emphasis', [RE(r"\*.+?\*")]),
    ('emphasis', [RE(r"_.+?_")]),
    ('quote', RE(r"^>\s+"), [RE(r"$")]),
    ('code', "```", ["```"], DynamicRange(r"\S+\s*?$|", "tag")),
    ('code', [RE(r"``.+?``"), RE(r"`.+?`")]),
    ('code', RE(r"^(?: {4}|	)"), [RE(r"$")]),
    ('_group1', RE(r"^[-\*]{3,}"), [RE(r"$")]),
    ('_group2', RE(r"(?=\[.+?\][\(\[].*?[\)\]])"), [RE(r"\B|\b")], _group2),
    ('_group3', RE(r"(?=^\[.+\]:)"), [RE(r"\B|\b")], _group3),
    ('section', [RE(r"^.+?\n[=-]{2,}$")]),
]
