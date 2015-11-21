# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: julia.js
name = 'Julia'
file_patterns = ['*.julia']

literal = [
    'true',
    'false',
    'ARGS',
    'CPU_CORES',
    'C_NULL',
    'DL_LOAD_PATH',
    'DevNull',
    'ENDIAN_BOM',
    'ENV',
    'I',
    'Inf',
    'Inf16',
    'Inf32',
    'InsertionSort',
    'JULIA_HOME',
    'LOAD_PATH',
    'MS_ASYNC',
    'MS_INVALIDATE',
    'MS_SYNC',
    'MergeSort',
    'NaN',
    'NaN16',
    'NaN32',
    'OS_NAME',
    'QuickSort',
    'RTLD_DEEPBIND',
    'RTLD_FIRST',
    'RTLD_GLOBAL',
    'RTLD_LAZY',
    'RTLD_LOCAL',
    'RTLD_NODELETE',
    'RTLD_NOLOAD',
    'RTLD_NOW',
    'RoundDown',
    'RoundFromZero',
    'RoundNearest',
    'RoundToZero',
    'RoundUp',
    'STDERR',
    'STDIN',
    'STDOUT',
    'VERSION',
    'WORD_SIZE',
    'catalan',
    'cglobal',
    'e',
    'eu',
    'eulergamma',
    'golden',
    'im',
    'nothing',
    'pi',
    'γ',
    'π',
    'φ',
    'Inf64',
    'NaN64',
    'RoundNearestTiesAway',
    'RoundNearestTiesUp',
]

keyword = [
    'in',
    'abstract',
    'baremodule',
    'begin',
    'bitstype',
    'break',
    'catch',
    'ccall',
    'const',
    'continue',
    'do',
    'else',
    'elseif',
    'end',
    'export',
    'finally',
    'for',
    'function',
    'global',
    'if',
    'immutable',
    'import',
    'importall',
    'let',
    'local',
    'macro',
    'module',
    'quote',
    'return',
    'try',
    'type',
    'typealias',
    'using',
    'while',
]

built_in = [
    'ANY',
    'ASCIIString',
    'AbstractArray',
    'AbstractRNG',
    'AbstractSparseArray',
    'Any',
    'ArgumentError',
    'Array',
    'Associative',
    'Base64Pipe',
    'Bidiagonal',
    'BigFloat',
    'BigInt',
    'BitArray',
    'BitMatrix',
    'BitVector',
    'Bool',
    'BoundsError',
    'Box',
    'CFILE',
    'Cchar',
    'Cdouble',
    'Cfloat',
    'Char',
    'CharString',
    'Cint',
    'Clong',
    'Clonglong',
    'ClusterManager',
    'Cmd',
    'Coff_t',
    'Colon',
    'Complex',
    'Complex128',
    'Complex32',
    'Complex64',
    'Condition',
    'Cptrdiff_t',
    'Cshort',
    'Csize_t',
    'Cssize_t',
    'Cuchar',
    'Cuint',
    'Culong',
    'Culonglong',
    'Cushort',
    'Cwchar_t',
    'DArray',
    'DataType',
    'DenseArray',
    'Diagonal',
    'Dict',
    'DimensionMismatch',
    'DirectIndexString',
    'Display',
    'DivideError',
    'DomainError',
    'EOFError',
    'EachLine',
    'Enumerate',
    'ErrorException',
    'Exception',
    'Expr',
    'Factorization',
    'FileMonitor',
    'FileOffset',
    'Filter',
    'Float16',
    'Float32',
    'Float64',
    'FloatRange',
    'FloatingPoint',
    'Function',
    'GetfieldNode',
    'GotoNode',
    'Hermitian',
    'IO',
    'IOBuffer',
    'IOStream',
    'IPv4',
    'IPv6',
    'InexactError',
    'Int',
    'Int128',
    'Int16',
    'Int32',
    'Int64',
    'Int8',
    'IntSet',
    'Integer',
    'InterruptException',
    'IntrinsicFunction',
    'KeyError',
    'LabelNode',
    'LambdaStaticData',
    'LineNumberNode',
    'LoadError',
    'LocalProcess',
    'MIME',
    'MathConst',
    'MemoryError',
    'MersenneTwister',
    'Method',
    'MethodError',
    'MethodTable',
    'Module',
    'NTuple',
    'NewvarNode',
    'Nothing',
    'Number',
    'ObjectIdDict',
    'OrdinalRange',
    'OverflowError',
    'ParseError',
    'PollingFileWatcher',
    'ProcessExitedException',
    'ProcessGroup',
    'Ptr',
    'QuoteNode',
    'Range',
    'Range1',
    'Ranges',
    'Rational',
    'RawFD',
    'Real',
    'Regex',
    'RegexMatch',
    'RemoteRef',
    'RepString',
    'RevString',
    'RopeString',
    'RoundingMode',
    'Set',
    'SharedArray',
    'Signed',
    'SparseMatrixCSC',
    'StackOverflowError',
    'Stat',
    'StatStruct',
    'StepRange',
    'String',
    'SubArray',
    'SubString',
    'SymTridiagonal',
    'Symbol',
    'SymbolNode',
    'Symmetric',
    'SystemError',
    'Task',
    'TextDisplay',
    'Timer',
    'TmStruct',
    'TopNode',
    'Triangular',
    'Tridiagonal',
    'Type',
    'TypeConstructor',
    'TypeError',
    'TypeName',
    'TypeVar',
    'UTF16String',
    'UTF32String',
    'UTF8String',
    'UdpSocket',
    'Uint',
    'Uint128',
    'Uint16',
    'Uint32',
    'Uint64',
    'Uint8',
    'UndefRefError',
    'UndefVarError',
    'UniformScaling',
    'UnionType',
    'UnitRange',
    'Unsigned',
    'Vararg',
    'VersionNumber',
    'WString',
    'WeakKeyDict',
    'WeakRef',
    'Woodbury',
    'Zip',
    'AbstractChannel',
    'AbstractFloat',
    'AbstractString',
    'AssertionError',
    'Base64DecodePipe',
    'Base64EncodePipe',
    'BufferStream',
    'CapturedException',
    'CartesianIndex',
    'CartesianRange',
    'Channel',
    'Cintmax_t',
    'CompositeException',
    'Cstring',
    'Cuintmax_t',
    'Cwstring',
    'Date',
    'DateTime',
    'Dims',
    'Enum',
    'GenSym',
    'GlobalRef',
    'HTML',
    'InitError',
    'InvalidStateException',
    'Irrational',
    'LinSpace',
    'LowerTriangular',
    'NullException',
    'Nullable',
    'OutOfMemoryError',
    'Pair',
    'PartialQuickSort',
    'Pipe',
    'RandomDevice',
    'ReadOnlyMemoryError',
    'ReentrantLock',
    'Ref',
    'RemoteException',
    'SegmentationFault',
    'SerializationState',
    'SimpleVector',
    'TCPSocket',
    'Text',
    'Tuple',
    'UDPSocket',
    'UInt',
    'UInt128',
    'UInt16',
    'UInt32',
    'UInt64',
    'UInt8',
    'UnicodeError',
    'Union',
    'UpperTriangular',
    'Val',
    'Void',
    'WorkerConfig',
    'AbstractMatrix',
    'AbstractSparseMatrix',
    'AbstractSparseVector',
    'AbstractVecOrMat',
    'AbstractVector',
    'DenseMatrix',
    'DenseVecOrMat',
    'DenseVector',
    'Matrix',
    'SharedMatrix',
    'SharedVector',
    'StridedArray',
    'StridedMatrix',
    'StridedVecOrMat',
    'StridedVector',
    'VecOrMat',
    'Vector',
]

number = [
    RE(r"(\b0x[\d_]*(\.[\d_]*)?|0x\.\d[\d_]*)p[-+]?\d+|\b0[box][a-fA-F0-9][a-fA-F0-9_]*|(\b\d[\d_]*(\.[\d_]*)?|\.\d[\d_]*)([eEfF][-+]?\d+)?"),
]

string = [RE(r"'(.|\\[xXuU][a-zA-Z0-9]+)'")]

type = [RE(r"::")]

type0 = [RE(r"<:")]

class subst:
    default_text = DELIMITER
    word_groups = [
        ('literal', literal),
        ('keyword', keyword),
        ('built_in', built_in),
    ]

variable = [RE(r"\$[A-Za-z_\u00A1-\uFFFF][A-Za-z_0-9\u00A1-\uFFFF]*")]

class string0:
    default_text = DELIMITER
    word_groups = [('variable', variable)]
    delimited_ranges = [('subst', RE(r"\$\("), [RE(r"\)")], subst)]
string0.__name__ = 'string'

meta = [RE(r"@[A-Za-z_\u00A1-\uFFFF][A-Za-z_0-9\u00A1-\uFFFF]*")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    word_groups = [('doctag', doctag)]

class subst0:
    default_text = DELIMITER
    word_groups = [
        ('literal', literal),
        ('keyword', keyword),
        ('built_in', built_in),
        ('number', number),
        ('string', string),
        ('type', type),
        ('type', type0),
        ('meta', meta),
    ]
    delimited_ranges = [
        ('string', RE(r"\w*\""), [RE(r"\"\w*")]),
        ('string', RE(r"\w*\"\"\""), [RE(r"\"\"\"\w*")]),
        ('string', RE(r"`"), [RE(r"`")], string0),
        ('comment', RE(r"#="), [RE(r"=#")]),
        ('comment', RE(r"#"), [RE(r"$")]),
        ('comment', RE(r"#"), [RE(r"$")], comment),
    ]
subst0.__name__ = 'subst'

class string1:
    default_text = DELIMITER
    word_groups = [('variable', variable)]
    delimited_ranges = [('subst', RE(r"\$\("), [RE(r"\)")], subst0)]
string1.__name__ = 'string'

class subst1:
    default_text = DELIMITER
    word_groups = [
        ('literal', literal),
        ('keyword', keyword),
        ('built_in', built_in),
        ('number', number),
        ('string', string),
        ('type', type),
        ('type', type0),
        ('meta', meta),
    ]
    delimited_ranges = [
        ('string', RE(r"\w*\""), [RE(r"\"\w*")], string0),
        ('string', RE(r"\w*\"\"\""), [RE(r"\"\"\"\w*")], string0),
        ('string', RE(r"`"), [RE(r"`")]),
        ('comment', RE(r"#="), [RE(r"=#")]),
        ('comment', RE(r"#"), [RE(r"$")]),
        ('comment', RE(r"#"), [RE(r"$")], comment),
    ]
subst1.__name__ = 'subst'

class string2:
    default_text = DELIMITER
    word_groups = [('variable', variable)]
    delimited_ranges = [('subst', RE(r"\$\("), [RE(r"\)")], subst1)]
string2.__name__ = 'string'

word_groups = [
    ('literal', literal),
    ('keyword', keyword),
    ('built_in', built_in),
    ('number', number),
    ('string', string),
    ('type', type),
    ('type', type0),
    ('meta', meta),
]

delimited_ranges = [
    ('string', RE(r"\w*\""), [RE(r"\"\w*")], string1),
    ('string', RE(r"\w*\"\"\""), [RE(r"\"\"\"\w*")], string1),
    ('string', RE(r"`"), [RE(r"`")], string2),
    ('comment', RE(r"#="), [RE(r"=#")]),
    ('comment', RE(r"#"), [RE(r"$")]),
    ('comment', RE(r"#"), [RE(r"$")], comment),
]
