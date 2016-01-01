# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: matlab.js
name = 'Matlab'
file_patterns = ['*.matlab']

built_in = """
    sin sind sinh asin asind asinh cos cosd cosh acos acosd acosh tan
    tand tanh atan atand atan2 atanh sec secd sech asec asecd asech csc
    cscd csch acsc acscd acsch cot cotd coth acot acotd acoth hypot exp
    expm1 log log1p log10 log2 pow2 realpow reallog realsqrt sqrt
    nthroot nextpow2 abs angle complex conj imag real unwrap isreal
    cplxpair fix floor ceil round mod rem sign airy besselj bessely
    besselh besseli besselk beta betainc betaln ellipj ellipke erf erfc
    erfcx erfinv expint gamma gammainc gammaln psi legendre cross dot
    factor isprime primes gcd lcm rat rats perms nchoosek factorial
    cart2sph cart2pol pol2cart sph2cart hsv2rgb rgb2hsv zeros ones eye
    repmat rand randn linspace logspace freqspace meshgrid accumarray
    size length ndims numel disp isempty isequal isequalwithequalnans
    cat reshape diag blkdiag tril triu fliplr flipud flipdim rot90 find
    sub2ind ind2sub bsxfun ndgrid permute ipermute shiftdim circshift
    squeeze isscalar isvector ans eps realmax realmin pi i inf nan isnan
    isinf isfinite j why compan gallery hadamard hankel hilb invhilb
    magic pascal rosser toeplitz vander wilkinson
    """.split()

keyword = """
    break case catch classdef continue else elseif end enumerated events
    for function global if methods otherwise parfor persistent
    properties return spmd switch try while
    """.split()

keyword0 = ['function']

title = [RE(r"[a-zA-Z_]\w*")]

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('title', title),
        ('params', RE(r"\("), [RE(r"\)")]),
        ('params', RE(r"\["), [RE(r"\]")]),
    ]

class _group0:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': '[a-zA-Z_][a-zA-Z_0-9]*', 'type': 'RegExp'}, 'relevance': 0},
        # ignore {'begin': {'pattern': "'['\\.]*", 'type': 'RegExp'}},
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
        # ignore {'begin': "''"},
    ]

class _group1:
    default_text_color = DELIMITER
    rules = [('number', number), ('string', RE(r"'"), [RE(r"'")], string)]

class _group10:
    default_text_color = DELIMITER
    rules = [('_group1', RE(r"\["), [RE(r"\]")], _group1)]
_group10.__name__ = '_group1'

class _group4:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "'['\\.]*", 'type': 'RegExp'}},
    ]

class _group2:
    default_text_color = DELIMITER
    rules = []

class _group20:
    default_text_color = DELIMITER
    rules = [('_group2', RE(r"\{"), [RE(r"}")], _group2)]
_group20.__name__ = '_group2'

class _group5:
    default_text_color = DELIMITER
    rules = []

class _group3:
    default_text_color = DELIMITER
    rules = [('_group3', RE(r"\)"), [RE(r"\B|\b")])]

class _group6:
    default_text_color = DELIMITER
    rules = []

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('function', RE(r"\b(?:function)"), [RE(r"$")], function),
    ('_group0', RE(r"(?=[a-zA-Z_][a-zA-Z_0-9]*'['\.]*)"), [RE(r"\B\b")], _group0),
    ('_group1', _group10, [RE(r"\B\b")], _group4),
    ('_group2', _group20, [RE(r"\B\b")], _group5),
    ('_group3', _group3, [RE(r"\B\b")], _group6),
    ('comment', RE(r"^\s*\%\{\s*$"), [RE(r"^\s*\%\}\s*$")], comment),
    ('comment', RE(r"\%"), [RE(r"$")], comment),
    ('number', number),
    _group1.rules[1],
]
