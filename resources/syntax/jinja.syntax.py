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

name = "Jinja Template"
file_patterns = ["*.jn2"]
comment_token = "{#" # ("{#", "#}")
rules = [
    # xml tags
    ("comment", "<!--", ["-->"]),
    ("tag", RE("<(/)?[a-zA-Z]"), [">", RE(r"(?=\{\{ )")]),
    # both (hackish and nasty)
    ("tag.jinja", RE(r"(?<= \}\}).+?(?=(>|\{\{ |$))"), [">", RE(r"(?=\{\{ |$)")]),
    # jinja2 syntax
    ("value.statement", RE(r"\{\%(-)? "), ["}", RE(r"$")], "python"), # 800000
    ("value.expression", "{{ ", [" }}", RE(r"$")], "python"), # 800000
    ("comment.multi-line", "{#", ["#}"]), # 666666
]
