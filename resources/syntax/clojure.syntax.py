# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: clojure.js
name = 'Clojure'
file_patterns = ['*.clojure', '*.clj']

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    word_groups = [('doctag', doctag)]

built_in = [
    'def',
    'defonce',
    'cond',
    'apply',
    'if-not',
    'if-let',
    'if',
    'not',
    'not=',
    '=',
    '<',
    '>',
    '<=',
    '>=',
    '==',
    '+',
    '/',
    '*',
    '-',
    'rem',
    'quot',
    'neg?',
    'pos?',
    'delay?',
    'symbol?',
    'keyword?',
    'true?',
    'false?',
    'integer?',
    'empty?',
    'coll?',
    'list?',
    'set?',
    'ifn?',
    'fn?',
    'associative?',
    'sequential?',
    'sorted?',
    'counted?',
    'reversible?',
    'number?',
    'decimal?',
    'class?',
    'distinct?',
    'isa?',
    'float?',
    'rational?',
    'reduced?',
    'ratio?',
    'odd?',
    'even?',
    'char?',
    'seq?',
    'vector?',
    'string?',
    'map?',
    'nil?',
    'contains?',
    'zero?',
    'instance?',
    'not-every?',
    'not-any?',
    'libspec?',
    '->',
    '->>',
    '..',
    '.',
    'inc',
    'compare',
    'do',
    'dotimes',
    'mapcat',
    'take',
    'remove',
    'take-while',
    'drop',
    'letfn',
    'drop-last',
    'take-last',
    'drop-while',
    'while',
    'intern',
    'condp',
    'case',
    'reduced',
    'cycle',
    'split-at',
    'split-with',
    'repeat',
    'replicate',
    'iterate',
    'range',
    'merge',
    'zipmap',
    'declare',
    'line-seq',
    'sort',
    'comparator',
    'sort-by',
    'dorun',
    'doall',
    'nthnext',
    'nthrest',
    'partition',
    'eval',
    'doseq',
    'await',
    'await-for',
    'let',
    'agent',
    'atom',
    'send',
    'send-off',
    'release-pending-sends',
    'add-watch',
    'mapv',
    'filterv',
    'remove-watch',
    'agent-error',
    'restart-agent',
    'set-error-handler',
    'error-handler',
    'set-error-mode!',
    'error-mode',
    'shutdown-agents',
    'quote',
    'var',
    'fn',
    'loop',
    'recur',
    'throw',
    'try',
    'monitor-enter',
    'monitor-exit',
    'defmacro',
    'defn',
    'defn-',
    'macroexpand',
    'macroexpand-1',
    'for',
    'dosync',
    'and',
    'or',
    'when',
    'when-not',
    'when-let',
    'comp',
    'juxt',
    'partial',
    'sequence',
    'memoize',
    'constantly',
    'complement',
    'identity',
    'assert',
    'peek',
    'pop',
    'doto',
    'proxy',
    'defstruct',
    'first',
    'rest',
    'cons',
    'defprotocol',
    'cast',
    'coll',
    'deftype',
    'defrecord',
    'last',
    'butlast',
    'sigs',
    'reify',
    'second',
    'ffirst',
    'fnext',
    'nfirst',
    'nnext',
    'defmulti',
    'defmethod',
    'meta',
    'with-meta',
    'ns',
    'in-ns',
    'create-ns',
    'import',
    'refer',
    'keys',
    'select-keys',
    'vals',
    'key',
    'val',
    'rseq',
    'name',
    'namespace',
    'promise',
    'into',
    'transient',
    'persistent!',
    'conj!',
    'assoc!',
    'dissoc!',
    'pop!',
    'disj!',
    'use',
    'class',
    'type',
    'num',
    'float',
    'double',
    'short',
    'byte',
    'boolean',
    'bigint',
    'biginteger',
    'bigdec',
    'print-method',
    'print-dup',
    'throw-if',
    'printf',
    'format',
    'load',
    'compile',
    'get-in',
    'update-in',
    'pr',
    'pr-on',
    'newline',
    'flush',
    'read',
    'slurp',
    'read-line',
    'subvec',
    'with-open',
    'memfn',
    'time',
    're-find',
    're-groups',
    'rand-int',
    'rand',
    'mod',
    'locking',
    'assert-valid-fdecl',
    'alias',
    'resolve',
    'ref',
    'deref',
    'refset',
    'swap!',
    'reset!',
    'set-validator!',
    'compare-and-set!',
    'alter-meta!',
    'reset-meta!',
    'commute',
    'get-validator',
    'alter',
    'ref-set',
    'ref-history-count',
    'ref-min-history',
    'ref-max-history',
    'ensure',
    'sync',
    'io!',
    'new',
    'next',
    'conj',
    'set!',
    'to-array',
    'future',
    'future-call',
    'into-array',
    'aset',
    'gen-class',
    'reduce',
    'map',
    'filter',
    'find',
    'empty',
    'hash-map',
    'hash-set',
    'sorted-map',
    'sorted-map-by',
    'sorted-set',
    'sorted-set-by',
    'vec',
    'vector',
    'seq',
    'flatten',
    'reverse',
    'assoc',
    'dissoc',
    'list',
    'disj',
    'get',
    'union',
    'difference',
    'intersection',
    'extend',
    'extend-type',
    'extend-protocol',
    'int',
    'nth',
    'delay',
    'count',
    'concat',
    'chunk',
    'chunk-buffer',
    'chunk-append',
    'chunk-first',
    'chunk-rest',
    'max',
    'min',
    'dec',
    'unchecked-inc-int',
    'unchecked-inc',
    'unchecked-dec-inc',
    'unchecked-dec',
    'unchecked-negate',
    'unchecked-add-int',
    'unchecked-add',
    'unchecked-subtract-int',
    'unchecked-subtract',
    'chunk-next',
    'chunk-cons',
    'chunked-seq?',
    'prn',
    'vary-meta',
    'lazy-seq',
    'spread',
    'list*',
    'str',
    'find-keyword',
    'keyword',
    'symbol',
    'gensym',
    'force',
    'rationalize',
]

class name0:
    default_text = DELIMITER
    word_groups = [('built_in', built_in)]
name0.__name__ = 'name'

class name1:
    default_text = DELIMITER
    delimited_ranges = [
        ('name', RE(r"[a-zA-Z_\-!.?+*=<>&#'][a-zA-Z_\-!.?+*=<>&#'0-9/;:]*"), [RE(r"\B|\b")], name0),
    ]
name1.__name__ = 'name'

comment0 = [RE(r"\^[a-zA-Z_\-!.?+*=<>&#'][a-zA-Z_\-!.?+*=<>&#'0-9/;:]*")]

symbol = [RE(r"[:][a-zA-Z_\-!.?+*=<>&#'][a-zA-Z_\-!.?+*=<>&#'0-9/;:]*")]

number = [RE(r"[-+]?\d+(\.\d+)?")]

literal = [RE(r"\b(true|false|nil)\b")]

class _group7:
    default_text = DELIMITER
    word_groups = [
        ('comment', comment0),
        ('symbol', symbol),
        ('number', number),
        ('literal', literal),
    ]
    delimited_ranges = [
        ('_group8', RE(r"\("), [RE(r"\)")]),
        ('string', RE(r"\""), [RE(r"\"")]),
        ('comment', RE(r"\^\{"), [RE(r"\}")], comment),
        ('comment', RE(r";"), [RE(r"$")], comment),
        ('_group12', RE(r"[\[\{]"), [RE(r"[\]\}]")]),
    ]

class _group2:
    default_text = DELIMITER
    word_groups = [
        ('comment', comment0),
        ('symbol', symbol),
        ('number', number),
        ('literal', literal),
    ]
    delimited_ranges = [
        ('_group3', RE(r"\("), [RE(r"\)")]),
        ('string', RE(r"\""), [RE(r"\"")]),
        ('comment', RE(r"\^\{"), [RE(r"\}")], comment),
        ('comment', RE(r";"), [RE(r"$")], comment),
        ('_group7', RE(r"[\[\{]"), [RE(r"[\]\}]")], _group7),
    ]

class _group20:
    default_text = DELIMITER
    word_groups = [
        ('comment', comment0),
        ('symbol', symbol),
        ('number', number),
        ('literal', literal),
    ]
    delimited_ranges = [
        ('_group21', RE(r"\("), [RE(r"\)")]),
        ('string', RE(r"\""), [RE(r"\"")]),
        ('comment', RE(r"\^\{"), [RE(r"\}")], comment),
        ('comment', RE(r";"), [RE(r"$")], comment),
        ('_group25', RE(r"[\[\{]"), [RE(r"[\]\}]")]),
    ]

class _group15:
    default_text = DELIMITER
    word_groups = [
        ('comment', comment0),
        ('symbol', symbol),
        ('number', number),
        ('literal', literal),
    ]
    delimited_ranges = [
        ('_group16', RE(r"\("), [RE(r"\)")]),
        ('string', RE(r"\""), [RE(r"\"")]),
        ('comment', RE(r"\^\{"), [RE(r"\}")], comment),
        ('comment', RE(r";"), [RE(r"$")], comment),
        ('_group20', RE(r"[\[\{]"), [RE(r"[\]\}]")], _group20),
    ]

class _group0:
    default_text = DELIMITER
    delimited_ranges = [
        ('comment', RE(r"comment"), [RE(r"\B|\b")], comment),
        ('name', name1, [RE(r"(?=\))")], _group2),
        ('_group15', RE(r"\B|\b"), [RE(r"")], _group15),
    ]

class _group34:
    default_text = DELIMITER
    word_groups = [
        ('comment', comment0),
        ('symbol', symbol),
        ('number', number),
        ('literal', literal),
    ]
    delimited_ranges = [
        ('_group35', RE(r"\("), [RE(r"\)")]),
        ('string', RE(r"\""), [RE(r"\"")]),
        ('comment', RE(r"\^\{"), [RE(r"\}")], comment),
        ('comment', RE(r";"), [RE(r"$")], comment),
        ('_group39', RE(r"[\[\{]"), [RE(r"[\]\}]")]),
    ]

class _group41:
    default_text = DELIMITER
    word_groups = [
        ('comment', comment0),
        ('symbol', symbol),
        ('number', number),
        ('literal', literal),
    ]
    delimited_ranges = [
        ('_group42', RE(r"\("), [RE(r"\)")]),
        ('string', RE(r"\""), [RE(r"\"")]),
        ('comment', RE(r"\^\{"), [RE(r"\}")], comment),
        ('comment', RE(r";"), [RE(r"$")], comment),
        ('_group46', RE(r"[\[\{]"), [RE(r"[\]\}]")]),
    ]

class _group32:
    default_text = DELIMITER
    delimited_ranges = [
        ('comment', RE(r"comment"), [RE(r"\B|\b")], comment),
        ('name', name1, [RE(r"(?=\))")], _group34),
        ('_group41', RE(r"\B|\b"), [RE(r"")], _group41),
    ]

class _group31:
    default_text = DELIMITER
    word_groups = [
        ('comment', comment0),
        ('symbol', symbol),
        ('number', number),
        ('literal', literal),
    ]
    delimited_ranges = [
        ('_group32', RE(r"\("), [RE(r"\)")], _group32),
        ('string', RE(r"\""), [RE(r"\"")]),
        ('comment', RE(r"\^\{"), [RE(r"\}")], comment),
        ('comment', RE(r";"), [RE(r"$")], comment),
        ('_group51', RE(r"[\[\{]"), [RE(r"[\]\}]")]),
    ]

word_groups = [
    ('comment', comment0),
    ('symbol', symbol),
    ('number', number),
    ('literal', literal),
]

delimited_ranges = [
    ('_group0', RE(r"\("), [RE(r"\)")], _group0),
    ('string', RE(r"\""), [RE(r"\"")]),
    ('comment', RE(r"\^\{"), [RE(r"\}")], comment),
    ('comment', RE(r";"), [RE(r"$")], comment),
    ('_group31', RE(r"[\[\{]"), [RE(r"[\]\}]")], _group31),
]
