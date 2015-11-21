# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: objectivec.js
name = 'Objective C'
file_patterns = ['*.objectivec', '*.mm', '*.objc', '*.obj-c']

literal = ['false', 'true', 'FALSE', 'TRUE', 'nil', 'YES', 'NO', 'NULL']

keyword = [
    'int',
    'float',
    'while',
    'char',
    'export',
    'sizeof',
    'typedef',
    'const',
    'struct',
    'for',
    'union',
    'unsigned',
    'long',
    'volatile',
    'static',
    'bool',
    'mutable',
    'if',
    'do',
    'return',
    'goto',
    'void',
    'enum',
    'else',
    'break',
    'extern',
    'asm',
    'case',
    'short',
    'default',
    'double',
    'register',
    'explicit',
    'signed',
    'typename',
    'this',
    'switch',
    'continue',
    'wchar_t',
    'inline',
    'readonly',
    'assign',
    'readwrite',
    'self',
    '@synchronized',
    'id',
    'typeof',
    'nonatomic',
    'super',
    'unichar',
    'IBOutlet',
    'IBAction',
    'strong',
    'weak',
    'copy',
    'in',
    'out',
    'inout',
    'bycopy',
    'byref',
    'oneway',
    '__strong',
    '__weak',
    '__block',
    '__autoreleasing',
    '@private',
    '@protected',
    '@public',
    '@try',
    '@property',
    '@end',
    '@throw',
    '@catch',
    '@finally',
    '@autoreleasepool',
    '@synthesize',
    '@dynamic',
    '@selector',
    '@optional',
    '@required',
]

built_in = [
    'BOOL',
    'dispatch_once_t',
    'dispatch_queue_t',
    'dispatch_sync',
    'dispatch_async',
    'dispatch_once',
]

built_in0 = [RE(r"(AV|CA|CF|CG|CI|MK|MP|NS|UI)\w+")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    word_groups = [('doctag', doctag)]

number = [RE(r"(\b0[xX][a-fA-F0-9]+|(\b\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)")]

class meta:
    default_text = DELIMITER
    delimited_ranges = [
        ('string', RE(r"\""), [RE(r"\"")]),
        ('string', RE(r"<"), [RE(r">")]),
    ]

keyword0 = ['@interface', '@class', '@protocol', '@implementation']

title = [RE(r"[a-zA-Z_]\w*")]

class class0:
    default_text = DELIMITER
    word_groups = [('keyword', keyword0), ('title', title)]
class0.__name__ = 'class'

word_groups = [
    ('literal', literal),
    ('keyword', keyword),
    ('built_in', built_in),
    ('built_in', built_in0),
    ('number', number),
]

delimited_ranges = [
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"\""), [RE(r"\"")]),
    ('string', RE(r"@\""), [RE(r"\"")]),
    ('string', RE(r"'"), [RE(r"[^\\]'")]),
    ('meta', RE(r"#"), [RE(r"$")], meta),
    ('class', RE(r"(@interface|@class|@protocol|@implementation)\b"), [RE(r"(?=({|$))")], class0),
]
