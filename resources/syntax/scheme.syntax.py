# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: scheme.js
name = 'Scheme'
file_patterns = ['*.scheme']

number = [RE(r"(?:\-|\+)?\d+(?:[./]\d+)?")]

number0 = [RE(r"(?:\-|\+)?\d+(?:[./]\d+)?[+\-](?:\-|\+)?\d+(?:[./]\d+)?i")]

number1 = [RE(r"#b[0-1]+(?:/[0-1]+)?")]

number2 = [RE(r"#o[0-7]+(?:/[0-7]+)?")]

number3 = [RE(r"#x[0-9a-f]+(?:/[0-9a-f]+)?")]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

symbol = [RE(r"'[^\(\)\[\]\{\}\",'`;#|\\\s]+")]

builtin_name = """
    case-lambda call/cc class define-class exit-handler field import
    inherit init-field interface let*-values let-values let/ec mixin
    opt-lambda override protect provide public rename require
    require-for-syntax syntax syntax-case syntax-error unit/sig unless
    when with-syntax and begin call-with-current-continuation
    call-with-input-file call-with-output-file case cond define
    define-syntax delay do dynamic-wind else for-each if lambda let let*
    let-syntax letrec letrec-syntax map or syntax-rules ' * + , ,@ - ...
    / ; < <= = => > >= ` abs acos angle append apply asin assoc assq
    assv atan boolean? caar cadr call-with-input-file
    call-with-output-file call-with-values car cdddar cddddr cdr ceiling
    char->integer char-alphabetic? char-ci<=? char-ci<? char-ci=?
    char-ci>=? char-ci>? char-downcase char-lower-case? char-numeric?
    char-ready? char-upcase char-upper-case? char-whitespace? char<=?
    char<? char=? char>=? char>? char? close-input-port
    close-output-port complex? cons cos current-input-port
    current-output-port denominator display eof-object? eq? equal? eqv?
    eval even? exact->inexact exact? exp expt floor force gcd imag-part
    inexact->exact inexact? input-port? integer->char integer?
    interaction-environment lcm length list list->string list->vector
    list-ref list-tail list? load log magnitude make-polar
    make-rectangular make-string make-vector max member memq memv min
    modulo negative? newline not null-environment null? number->string
    number? numerator odd? open-input-file open-output-file output-port?
    pair? peek-char port? positive? procedure? quasiquote quote quotient
    rational? rationalize read read-char real-part real? remainder
    reverse round scheme-report-environment set! set-car! set-cdr! sin
    sqrt string string->list string->number string->symbol string-append
    string-ci<=? string-ci<? string-ci=? string-ci>=? string-ci>?
    string-copy string-fill! string-length string-ref string-set!
    string<=? string<? string=? string>=? string>? string? substring
    symbol->string symbol? tan transcript-off transcript-on truncate
    values vector vector->list vector-fill! vector-length vector-ref
    vector-set! with-input-from-file with-output-to-file write
    write-char zero?
    """.split()

class name0:
    default_text = DELIMITER
    rules = [('builtin-name', builtin_name)]
name0.__name__ = 'name'

literal = [RE(r"(?:#t|#f|#\\[^\(\)\[\]\{\}\",'`;#|\\\s]+|#\\.)")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class _group2:
    default_text = DELIMITER
    rules = [
        ('literal', literal),
        ('number', number3),
        None,  # rules[6],
        # {'begin': '[^\\(\\)\\[\\]\\{\\}",\'`;#|\\\\\\s]+', 'relevance': 0},
        ('symbol', symbol),
        # {},
        ('comment', RE(r";"), [RE(r"$")], comment),
        ('comment', RE(r"#\|"), [RE(r"\|#")], comment),
    ]

class _group1:
    default_text = DELIMITER
    rules = [
        ('name', RE(r"[^\(\)\[\]\{\}\",'`;#|\\\s]+"), [RE(r"\B\b")], name0),
        ('_group2', RE(r"\B|\b"), [RE(r"\B\b")], _group2),
    ]

class _group5:
    default_text = DELIMITER
    rules = [
        ('literal', literal),
        ('number', number3),
        None,  # rules[6],
        # {'begin': '[^\\(\\)\\[\\]\\{\\}",\'`;#|\\\\\\s]+', 'relevance': 0},
        ('symbol', symbol),
        None,  # rules[8],
        ('comment', RE(r";"), [RE(r"$")], comment),
        ('comment', RE(r"#\|"), [RE(r"\|#")], comment),
    ]

class _group4:
    default_text = DELIMITER
    rules = [
        ('name', RE(r"[^\(\)\[\]\{\}\",'`;#|\\\s]+"), [RE(r"\B\b")], name0),
        ('_group5', RE(r"\B|\b"), [RE(r"\B\b")], _group5),
    ]

rules = [
    ('meta', RE(r"^#!"), [RE(r"$")]),
    ('number', number),
    ('number', number0),
    ('number', number1),
    ('number', number2),
    ('number', number3),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('symbol', symbol),
    ('_group1', RE(r"\("), [RE(r"\)")], _group1),
    ('_group4', RE(r"\["), [RE(r"\]")], _group4),
    _group5.rules[5],
    _group5.rules[6],
]

_group2.rules[2] = rules[6]
_group5.rules[2] = rules[6]
_group5.rules[4] = rules[9]

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
