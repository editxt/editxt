# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: rust.js
name = 'Rust'
file_patterns = ['*.rust', '*.rs']

built_in = """
    Copy Send Sized Sync Drop Fn FnMut FnOnce drop Box ToOwned Clone
    PartialEq PartialOrd Eq Ord AsRef AsMut Into From Default Iterator
    Extend IntoIterator DoubleEndedIterator ExactSizeIterator Option
    Some None Result Ok Err SliceConcatExt String ToString Vec assert!
    assert_eq! bitflags! bytes! cfg! col! concat! concat_idents!
    debug_assert! debug_assert_eq! env! panic! file! format!
    format_args! include_bin! include_str! line! local_data_key!
    module_path! option_env! print! println! select! stringify! try!
    unimplemented! unreachable! vec! write! writeln!
    """.split()

keyword = """
    alignof as be box break const continue crate do else enum extern
    false fn for if impl in let loop match mod mut offsetof once priv
    proc pub pure ref return self Self sizeof static struct super trait
    true type typeof unsafe unsized use virtual while where yield int i8
    i16 i32 i64 uint u8 u32 u64 float f32 f64 str char bool
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class string:
    default_text_color = DELIMITER
    rules = [('operator.escape', [RE(r"\\[\s\S]")])]

number2 = [
    RE(r"\b(?:\d[\d_]*(?:\.[0-9_]+)?(?:[eE][+-]?[0-9_]+)?)(?:[uif](?:8|16|32|64|size))?"),
]

class _function0:
    default_text_color = DELIMITER
    rules = [('_function', [RE(r"(?:\(|<)")])]
_function0.__name__ = '_function'

title = ('title', [RE(r"[a-zA-Z_]\w*")])

class function:
    default_text_color = DELIMITER
    rules = [('keyword', ['fn']), title]

class class0:
    default_text_color = DELIMITER
    rules = [('keyword', ['type']), title]
class0.__name__ = 'class'

class class2:
    default_text_color = DELIMITER
    rules = [('keyword', ['trait', 'enum']), title]
class2.__name__ = 'class'

class _group1:
    default_text_color = DELIMITER
    rules = [('built_in', built_in)]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', [RE(r"r(?:#*)\".*?\"\1(?!#)")]),
    ('string', [RE(r"'\\?(?:x\w{2}|u\w{4}|U\w{8}|.)'")]),
    ('symbol', [RE(r"'[a-zA-Z_][a-zA-Z0-9_]*")]),
    ('number', [RE(r"\b0b(?:[01_]+)(?:[uif](?:8|16|32|64|size))?")]),
    ('number', [RE(r"\b0o(?:[0-7_]+)(?:[uif](?:8|16|32|64|size))?")]),
    ('number', [RE(r"\b0x(?:[A-Fa-f0-9_]+)(?:[uif](?:8|16|32|64|size))?")]),
    ('number', number2),
    ('function', RE(r"\b(?:fn)"), [_function0], function),
    ('meta', RE(r"#\!?\["), [RE(r"\]")]),
    ('class', RE(r"\b(?:type)"), [RE(r"(?:=|<)")], class0),
    ('class', RE(r"\b(?:trait|enum)"), [RE(r"{")], class2),
    ('_group1', RE(r"[a-zA-Z]\w*::"), [RE(r"\B\b")], _group1),
    # ignore {'begin': '->'},
]
