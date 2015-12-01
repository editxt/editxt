# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: twig.js
name = 'Twig'
file_patterns = ['*.twig', '*.craftcms']

flags = re.IGNORECASE | re.MULTILINE

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

keyword = [
    'autoescape',
    'block',
    'do',
    'embed',
    'extends',
    'filter',
    'flush',
    'for',
    'if',
    'import',
    'include',
    'macro',
    'sandbox',
    'set',
    'spaceless',
    'use',
    'verbatim',
    'endautoescape',
    'endblock',
    'enddo',
    'endembed',
    'endextends',
    'endfilter',
    'endflush',
    'endfor',
    'endif',
    'endimport',
    'endinclude',
    'endmacro',
    'endsandbox',
    'endset',
    'endspaceless',
    'enduse',
    'endverbatim',
]

class name0:
    default_text = DELIMITER
    rules = [('keyword', keyword)]
name0.__name__ = 'name'

class name1:
    default_text = DELIMITER
    rules = [('name', RE(r"\w+"), [RE(r"\B|\b")], name0)]
name1.__name__ = 'name'

keyword0 = [
    'abs',
    'batch',
    'capitalize',
    'convert_encoding',
    'date',
    'date_modify',
    'default',
    'escape',
    'first',
    'format',
    'join',
    'json_encode',
    'keys',
    'last',
    'length',
    'lower',
    'merge',
    'nl2br',
    'number_format',
    'raw',
    'replace',
    'reverse',
    'round',
    'slice',
    'sort',
    'split',
    'striptags',
    'title',
    'trim',
    'upper',
    'url_encode',
]

name2 = [
    'attribute',
    'block',
    'constant',
    'cycle',
    'date',
    'dump',
    'include',
    'max',
    'min',
    'parent',
    'random',
    'range',
    'source',
    'template_from_string',
]

class _group2:
    default_text = DELIMITER
    rules = [('name', name2), ('params', RE(r"\("), [RE(r"\)")])]

class _group1:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('_group2', RE(r"\b(attribute|block|constant|cycle|date|dump|include|max|min|parent|random|range|source|template_from_string)"), [RE(r"\B|\b")], _group2),
    ]

class _group0:
    default_text = DELIMITER
    rules = [
        ('_group1', RE(r"\|[A-Za-z_]+:?"), [RE(r"\B|\b")], _group1),
        None,  # _group1.rules[1],
    ]

class template_tag:
    default_text = DELIMITER
    rules = [('name', name1, [RE(r"(?=%})")], _group0)]
template_tag.__name__ = 'template-tag'

class template_variable:
    default_text = DELIMITER
    rules = [
        None,  # _group0.rules[0],
        None,  # _group1.rules[1],
    ]
template_variable.__name__ = 'template-variable'

rules = [
    ('comment', RE(r"\{#"), [RE(r"#}")], comment),
    ('template-tag', RE(r"\{%"), [RE(r"%}")], template_tag),
    ('template-variable', RE(r"\{\{"), [RE(r"}}")], template_variable),
]

_group0.rules[1] = _group1.rules[1]
template_variable.rules[0] = _group0.rules[0]
template_variable.rules[1] = _group1.rules[1]

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
