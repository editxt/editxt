# EditXT

A programmer's text editor for Mac OS X

## Features:

- Syntax highlighting
- Advanced find/replace supporting
  - Regular expressions with group expansion in replacement string
  - *Python Replace*, which evaluates a Python expression to generate the
    replacement string.
- Command bar to execute commands without using the mouse.
- Smart indent/dedent with tabs or spaces.
- Comment/uncomment selection.
- Word wrap.
- Line numbers.
- Cursor position/selection length indicator.
- Unix/Mac/Windows line ending support.
- Document pane with drag/drop support.
- Undo beyond save and beyond auto-reload on external change.
- Inter-document navigation with keyboard
  - Command+Option+Arrow Keys
    - Up/Down moves up and down in the document tree.
    - Left/Right navigates most recently visited documents.
  - `doc FILENAME` command to switch to editor by name.
- `ag` (http://geoff.greer.fm/ag/) code search tool integration.
- `grab` command to grab (think grep) lines from the current document.
- Diff tool integration for viewing differences between the current (unsaved)
  document and the file on disk.
- Preliminary support for character encodings other than UTF-8.
- Sort lines tool.
- Licensed under GPLv3 (source code available at http://editxt.org/)
- Many more...

## Known issues:

- changing the tab width when in tab-indent mode does not automatically update
  the width of tabs. Recommendation: use spaces not tabs for indentation.

--

DISCLAIMER: EditXT is always in development and may have bugs that could
cause you to lose your work. However, the primary developer has been using it
for professional software development since 2008 and thinks it is quite
usable, if incomplete. You can download the source code and help with
development at http://editxt.org/

## License

Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
Website: http://editxt.org/

EditXT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

EditXT is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with EditXT.  If not, see <http://www.gnu.org/licenses/>.
