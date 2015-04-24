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

name = "SQL"
file_patterns = ["*.sql"]
flags = re.IGNORECASE | re.MULTILINE
comment_token = "--"
word_groups = [
    ("keyword", """
        abort absolute access action add admin after aggregate all also alter
        always analyse analyze and any array as asc assertion assignment
        asymmetric at authorization backward before begin between bigint binary
        bit boolean both by cache called cascade cascaded case cast catalog
        chain char character characteristics check checkpoint class close
        cluster coalesce collate column comment comments commit committed
        concurrently configuration connection constraint constraints content
        continue conversion copy cost create createdb createrole createuser
        cross csv current current_catalog current_date current_role
        current_schema current_time current_timestamp current_user cursor cycle
        data date database day deallocate dec decimal declare default defaults
        deferrable deferred definer delete delimiter delimiters desc dictionary
        disable discard distinct do document domain double drop each else enable
        encoding encrypted end enum escape except exclude excluding exclusive
        execute exists explain external extract false family fetch first float
        following for force foreign forward freeze from full function functions
        global grant granted greatest group handler having header hold hour
        identity if ilike immediate immutable implicit in including increment
        index indexes inherit inherits initially inline inner inout input
        insensitive insert instead int integer intersect interval into invoker
        is isnull isolation join key language large last lc_collate lc_ctype
        leading least left level like limit listen load local localtime
        localtimestamp location lock login mapping match maxvalue minute
        minvalue mode month move name names national natural nchar next no
        nocreatedb nocreaterole nocreateuser noinherit nologin none nosuperuser
        not nothing notify notnull nowait null nullif nulls numeric object of
        off offset oids on only operator option options or order out outer over
        overlaps overlay owned owner parser partial partition password perform
        placing plans position preceding precision prepare prepared preserve
        primary prior privileges procedural procedure quote range read real
        reassign recheck recursive references reindex relative release rename
        repeatable replace replica reset restart restrict return returning
        returns revoke right role rollback row rows rule savepoint schema scroll
        search second security select sequence sequences serializable server
        session session_user set setof share show similar simple smallint some
        stable standalone start statement statistics stdin stdout storage strict
        strip substring superuser symmetric sysid system table tables tablespace
        temp template temporary text then time timestamp to trailing transaction
        treat trigger trim true truncate trusted type unbounded uncommitted
        unencrypted union unique unknown unlisten until update user using vacuum
        valid validator value values varchar variadic varying verbose version
        view volatile when where whitespace window with without work wrapper
        write xml xmlattributes xmlconcat xmlelement xmlforest xmlparse xmlpi
        xmlroot xmlserialize year yes zone
    """.split()),
]
delimited_ranges = [
    ("identifier.quoted", RE('"'), ['"']),
    ("string.single-quote", RE("'"), ["'"]),
    ("comment.multi-line", "/*", ["*/"]),
    ("comment", "--", [RE(r"(?=\n)")]),
]
