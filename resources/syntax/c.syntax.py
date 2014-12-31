# EditXT
# Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
# 
# This file is part of EditXT, a programmer's text editor for Mac OS X,
# which can be found at http://editxt.org/.
# 
# EditXT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# EditXT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with EditXT.  If not, see <http://www.gnu.org/licenses/>.


name = "C"
filepatterns = [
    "*.c",      # C
    "*.h",      # [Obj-]C[++] / etc header files
    "*.cpp",    # C++
    "*.m",      # Obj-C
    "*.mm",     # Obj-C C++
    "*.ino",    # Arduino C++
]
comment_token = "//"
word_groups = [
    # --------------------------------------------------------------------------
    # copied from javascript
    ("""
        abstract
        boolean
        break
        byte
        case
        catch
        char
        class
        const
        continue
        debugger
        default
        delete
        dispatch_block_t
        do
        double
    	else
        enum
        export
        extends
        final
        finally
        float
        for
        function
        goto
        id
        if
        implements
        in
        instanceOf
        int
        interface
        long
        native
        new
        null
        package
        private
        protected
        public
        release
        return
        short
        signed
        static
        super
        switch
        synchronized
        this
        throw
        throws
        transient
        try
        typeof
        uint32_t
        uint64_t
        unsigned
        var
        volatile
        while
        with
        yield
    """.split(), "0000CC"),
    # --------------------------------------------------------------------------
    # added/changed for obj-c
    ("""
        autorelease
        extern
        retain
        self
        void
    """.split(), "0000CC"),
    ("""
        #define
        #import
        #include
        #undef
    """.split(), "78492A"),
    ("""
        @class
        @defs
        @protocol
        @required
        @optional
        @end
        @interface
        @public
        @package
        @protected
        @private
        @property
        @end
        @implementation
        @synthesize
        @dynamic
        @end
        @throw
        @try
        @catch
        @finally
        @synchronized
        @autoreleasepool
        @selector
        @encode
        @compatibility_alias
    """.split(), "BA2DA2"),
    ("YES NO NULL nil".split(), "000080"),
]
delimited_ranges = [
    (RE('[@]?"'), ['"', RE(r"[^\\]\n")], "D32E1B", None),
    (RE('\s\<'), [RE('\.h\>'), RE(r"[^\\]\n")], "D32E1B", None),
    (RE("[@]?'"), ["'", RE(r"[^\\]\n")], "008080", None),
    ("//", [RE(r"(?=\n)")], "008000", None),
    ("/*", ["*/"], "505050", None),
    #(RE("/[^/]"), [RE(r"[^\\]/[img]*"), RE(r"(?=\n)")], "59069b", None),
]
