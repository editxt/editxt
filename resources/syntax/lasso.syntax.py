# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: lasso.js
name = 'Lasso'
file_patterns = ['*.lasso', '*.ls', '*.lassoscript']

flags = re.IGNORECASE | re.MULTILINE

built_in = [
    'array',
    'date',
    'decimal',
    'duration',
    'integer',
    'map',
    'pair',
    'string',
    'tag',
    'xml',
    'null',
    'boolean',
    'bytes',
    'keyword',
    'list',
    'locale',
    'queue',
    'set',
    'stack',
    'staticarray',
    'local',
    'var',
    'variable',
    'global',
    'data',
    'self',
    'inherited',
    'currentcapture',
    'givenblock',
]

keyword = [
    'error_code',
    'error_msg',
    'error_pop',
    'error_push',
    'error_reset',
    'cache',
    'database_names',
    'database_schemanames',
    'database_tablenames',
    'define_tag',
    'define_type',
    'email_batch',
    'encode_set',
    'html_comment',
    'handle',
    'handle_error',
    'header',
    'if',
    'inline',
    'iterate',
    'ljax_target',
    'link',
    'link_currentaction',
    'link_currentgroup',
    'link_currentrecord',
    'link_detail',
    'link_firstgroup',
    'link_firstrecord',
    'link_lastgroup',
    'link_lastrecord',
    'link_nextgroup',
    'link_nextrecord',
    'link_prevgroup',
    'link_prevrecord',
    'log',
    'loop',
    'namespace_using',
    'output_none',
    'portal',
    'private',
    'protect',
    'records',
    'referer',
    'referrer',
    'repeating',
    'resultset',
    'rows',
    'search_args',
    'search_arguments',
    'select',
    'sort_args',
    'sort_arguments',
    'thread_atomic',
    'value_list',
    'while',
    'abort',
    'case',
    'else',
    'if_empty',
    'if_false',
    'if_null',
    'if_true',
    'loop_abort',
    'loop_continue',
    'loop_count',
    'params',
    'params_up',
    'return',
    'return_value',
    'run_children',
    'soap_definetag',
    'soap_lastrequest',
    'soap_lastresponse',
    'tag_name',
    'ascending',
    'average',
    'by',
    'define',
    'descending',
    'do',
    'equals',
    'frozen',
    'group',
    'handle_failure',
    'import',
    'in',
    'into',
    'join',
    'let',
    'match',
    'max',
    'min',
    'on',
    'order',
    'parent',
    'protected',
    'provide',
    'public',
    'require',
    'returnhome',
    'skip',
    'split_thread',
    'sum',
    'take',
    'thread',
    'to',
    'trait',
    'type',
    'where',
    'with',
    'yield',
    'yieldhome',
    'and',
    'or',
    'not',
]

literal = [
    'true',
    'false',
    'none',
    'minimal',
    'full',
    'all',
    'void',
    'bw',
    'nbw',
    'ew',
    'new',
    'cn',
    'ncn',
    'lt',
    'lte',
    'gt',
    'gte',
    'eq',
    'neq',
    'rx',
    'nrx',
    'ft',
]

class meta:
    default_text = DELIMITER
    rules = [('meta', RE(r"\]|\?>"), [RE(r"\B|\b")])]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

class _group0:
    default_text = DELIMITER
    rules = [('comment', RE(r"<!--"), [RE(r"-->")], comment)]

class meta0:
    default_text = DELIMITER
    rules = [('meta', RE(r"\[noprocess\]"), [RE(r"\B|\b")])]
meta0.__name__ = 'meta'

class _group1:
    default_text = DELIMITER
    rules = [
        None,  # _group0.rules[0],
    ]

meta1 = [RE(r"\[/noprocess|<\?(lasso(script)?|=)")]

class meta2:
    default_text = DELIMITER
    rules = [('meta', RE(r"\[no_square_brackets"), [RE(r"\B|\b")])]
meta2.__name__ = 'meta'

class _group3:
    default_text = DELIMITER
    rules = [
        None,  # _group0.rules[0],
    ]

class comment0:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]
comment0.__name__ = 'comment'

number = [
    RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)|(infinity|nan)\b"),
]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

attr = [RE(r"-(?!infinity)[a-zA-Z_]\w*")]

attr0 = [RE(r"(\.\.\.)")]

symbol = [RE(r"'[a-zA-Z_][a-zA-Z0-9_.]*'")]

class _group7:
    default_text = DELIMITER
    rules = [('symbol', symbol)]

keyword0 = ['define']

title = [RE(r"[a-zA-Z_]\w*(=(?!>))?")]

class class0:
    default_text = DELIMITER
    rules = [('keyword', keyword0), ('title', title)]
class0.__name__ = 'class'

class _group2:
    default_text = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', literal),
        ('meta', meta, [RE(r"(?=\[noprocess\]|<\?(lasso(script)?|=))")], _group3),
        None,  # rules[4],
        None,  # ('meta', meta1),
        ('comment', RE(r"/\*\*!"), [RE(r"\*/")], comment0),
        ('comment', RE(r"//"), [RE(r"$")], comment0),
        ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
        ('number', number),
        ('string', RE(r"'"), [RE(r"'")]),
        ('string', RE(r"\""), [RE(r"\"")], string),
        ('string', RE(r"`"), [RE(r"`")]),
        ('_group6', RE(r"#"), [RE(r"\d+")]),
        ('type', RE(r"::\s*"), [RE(r"[a-zA-Z_][a-zA-Z0-9_.]*")]),
        ('attr', attr),
        ('attr', attr0),
        ('_group7', RE(r"(->|\.\.?)\s*"), [RE(r"\B|\b")], _group7),
        ('class', RE(r"\b(define)"), [RE(r"(?=\(|=>)")], class0),
    ]

meta3 = [RE(r"\[")]

meta4 = [RE(r"^#!.+lasso9\b")]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('meta', meta, [RE(r"(?=\[|<\?(lasso(script)?|=))")], _group0),
    ('meta', meta0, [RE(r"(?=\[/noprocess\])")], _group1),
    ('meta', meta1),
    ('meta', meta2, [RE(r"\[/no_square_brackets\]")], _group2),
    ('meta', meta3),
    ('meta', meta4),
    None,  # _group2.rules[6],
    None,  # _group2.rules[7],
    None,  # _group2.rules[8],
    None,  # ('number', number),
    None,  # _group2.rules[10],
    None,  # _group2.rules[11],
    None,  # _group2.rules[12],
    None,  # _group2.rules[13],
    None,  # _group2.rules[14],
    None,  # ('attr', attr0),
    None,  # _group2.rules[17],
    None,  # _group2.rules[18],
]

_group1.rules[0] = _group0.rules[0]
_group3.rules[0] = _group0.rules[0]
_group2.rules[4] = rules[4]
_group2.rules[5] = ('meta', meta1)
rules[9] = _group2.rules[6]
rules[10] = _group2.rules[7]
rules[11] = _group2.rules[8]
rules[12] = ('number', number)
rules[13] = _group2.rules[10]
rules[14] = _group2.rules[11]
rules[15] = _group2.rules[12]
rules[16] = _group2.rules[13]
rules[17] = _group2.rules[14]
rules[18] = ('attr', attr0)
rules[19] = _group2.rules[17]
rules[20] = _group2.rules[18]

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
