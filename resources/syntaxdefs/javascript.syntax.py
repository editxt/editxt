# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
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

name = "JavaScript"
filepatterns = ["*.js"]
comment_token = "//"
word_groups = [
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
        if
        implements
        import
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
        return
        short
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
        var
        void
        volatile
        while
        with
        yield
    """.split(), "0000CC"),
    ("true false alert".split(), "000080"),
]
delimited_ranges = [
    (RE('[ru]?"'), ['"', RE(r"[^\\]\n")], "008080", None),
    (RE("[ru]?'"), ["'", RE(r"[^\\]\n")], "008080", None),
    ("//", [RE(r"(?=\n)")], "008000", None),
    ("/*", ["*/"], "505050", None),
    (RE("/[^/]"), [RE(r"[^\\]/[img]*"), RE(r"(?=\n)")], "59069b", None),
]
