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

name = "Python"
filepatterns = ["*.py", "*.pyw"]
comment_token = "#"
word_groups = [
    ("""
        and       del       from      not       while    
        as        elif      global    or        with     
        assert    else      if        pass      yield    
        break     except    import    class     in       
        raise     continue  finally   is        return   
        def       for       lambda    try       nonlocal
    """.split(), "0000CC"),
    ("self True False None".split(), "000080"),
    #("== != < > <= >=".split(), "FF0000"),
]
delimited_ranges = [
    (RE('[rub]?"""'), ['"""'], "008080", None),
    (RE("[rub]?'''"), ["'''"], "505050", None),
    (RE('[rub]?"'), ['"', RE(r"[^\\]\n")], "008080", None),
    (RE("[rub]?'"), ["'", RE(r"[^\\]\n")], "008080", None),
    ("#", [RE(r"(?=\n)")], "008000", None),
]
''' abc '''
# FIX type """ and then <ENTER> (following lines are not highlighted)
