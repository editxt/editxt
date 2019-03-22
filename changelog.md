# EditXT Change Log

This file contains notable new features and other large changes. See
https://github.com/editxt/editxt for details of what actually happened.

## 2019-03-22 - 1.13.0

- Behavior change: make `ag` command search project directory by default rather
  than the directory of the current file. Use `ag PATTERN .` to search the
  current directory (old behavior). Fall back to directory of current editor's
  file if project directory is not set. Changed default project path to null
  rather than user's home directory because having `ag` recursively search the
  entire home directory by default could be pretty annoying.
- Add `isort` command for sorting Python import statements.
- Add `split` and `join` commands.
- Improve performance of `pathfind` command. It now searches source files only
  by default (using `ag` under the covers). It is no longer possible to
  automatically open the first match, but that was a bad feature anyway because
  it forced an exhaustive search before displaying any output. The new command
  searches in the background and shows matches as they are found.
- Improve `python` command executable resolution and display of default value
  on command line.
- Updates for macOS 10.13 High Sierra

## 2018-06-30 - 1.12.1 (unreleased)

- Strip trailing newline from `python` command output.
- Filter command bar history with command text (incomplete: slow if no match).
- Upgrade to Python 3.7.
- Fix bug in syntax highlighting that could cause edits to be invisible.

## 2017-10-28 - 1.12.0

- Auto-print last expression of `python` command input.
- Change color of visited links in command output.
- Command+i in find dialog to toggle ignore case.
- Change new document insertion position in document tree to be consistent:
  after current document.
- Fix off-by-one error in command bar path autocompletion.
- Fix freeze on highlight text in large file.
- Fix diff on save after file changed on disk.
- Fix diff on prompt to overwrite.
- Upgrade to Python 3.6.

## 2016-12-20 - 1.11.0

- Add `unique` command for removing duplicate lines.
- Add `preferences` command (also aliased as `config`).
- Add regular expression and Python syntax highlighting in find dialog.
- Syntax highlighting: add bash comment token `#` for commenting multiple lines
  when Shell syntax is enabled.
- Syntax highlighting: highlight escape sequences in Python strings.
- Only escape characters in find dialog that have special meaning in regular
  expressions. This means that characters like space and tab are not escaped.
- Show `blame` command error on non-zero exit.
- Fix undo after type, paste, then type some more.
- Fix bug in indentation mode/size detection: line with single leading space is
  not considered to be an indented line.
- Fix editing commands (insert newline, indent, find/replace) and syntax
  highlighting in documents with emoji.
- Fix insert newline removing characters when selected text had leading
  spaces.
- Fix closing document with no path.
- Fix command argument completion bugs.
- Fix scrollbars showing when not needed.

## 2016-10-14 - 1.10.0

- Remove close buttons from file tree. Right-click > Close or or Command+W
  instead.
- Switch from `ack` to `ag` for faster find-in-file. Unfortunately the `ag`
  program's options are not compatible with `ack`, so this means you must
  install `ag` (a.k.a. `the_silver_searcher`) to use the `ag` command. The old
  `ack` command is an alias for the new `ag` command. The `ag` command also now
  runs in a background thread.
- Allow multi-selection in file tree. Some commands work differently with
  multiple files selected. For example, if there are two files selected, the
  `diff` command will compare them. It is also possible to close multiple files
  at once by selecting them and then Right Click > Close.
- The `python` command's `executable` argument now accepts a virtualenv path
  (or any directory containing an executable at `bin/python`) from which it will
  automatically derive the Python executable path.
- Add `blame` command, which invokes `git gui blame` on the current file.
- Add `github-url` command, which creates a link to the github page for the
  current file.
- Exclude unwanted files and directories from the pathfind command. The default
  set of excluded files is:
  ```
  command:
    pathfind:
      exclude_patterns:
        - "*.pyc"
        - ".git"
        - ".hg"
        - ".svn"
  ```
  This can be customized in the config file.
- Maintain scroll position on soft wrap toggle.
- Fixed sluggish typing and line number redrawing bug.
- Fixed newlines in markdown output.
- Fixed Escape key in project main view.
- Fixed move to beginning of line (Home, Command+Left Arrow) with unicode.
- Fixed bugs in Home/End cursor movement and selection.

## 2016-02-21 - 1.9.5

- Add wildcard path matching to `open` command.
- Add `set comment_token` command, which changes the comment token for the
  document's language (in all editors) until the program is restarted.
- Add moved file detection (update path when file is moved).
- Add config setting (`updates_path_on_file_move: true`) and command to change
  document-level setting (`set updates_path_on_file_move yes`) to enable or
  disable file move detection for globally or individually for each document.
  The default config value is `true` (move detection is enabled by default).
- Activate window unsaved indocator when current document has unsaved changes.
- Do not escape spaces in command bar file auto-complete list.
- Fix tab path expansion in project view when project path has trailing slash.
- Fix default value for skipped regex args in command bar.
- Fix document paths with up-references resulting in unnecessary save prompt.
- Fix command completions view sometimes not drawing.
- Fix line numbers overlap content text after find next.
- Fix undo in command bar.
- Fix command bar auto-complete for directory with space in name.
- Improve responsiveness while highlighting syntax in large files.

## 2016-01-30 - 1.9.0

- Added many new syntax definitions derived from the
  [highlight.js](https://highlightjs.org/) library. Note: the built-in theme
  does not yet have colors defined for all token types, so tokens in some
  languages may not be colored as expected. Better theme support is planned for
  a future release.
- Syntax definitions now allow `word_groups` and `delimited_ranges` to be
  combined in a single `rules` list. Use of separate `word_groups` and
  `delimited_ranges` lists is deprecated, and cannot be used in combination
  with a consolidated `rules` list.
- Syntax definition attribute `default_text` (added in 1.8.0) was renamed to
  `default_text_color`.
- Add context menu for documents pane.
- Add `pathfind` command for finding files by regular expression matching paths
  (similar to `find /path | grep pattern`). One place where this is very handy
  is finding the file for an imported Python module. Select the imported module
  path (example: `editxt.command.find`) and enter the `pathfind` command or use
  it's hotkey (Command+Alt+P) to quickly find the file for that module. The file
  will be opened if there is a single match. Otherwise a list of clickable
  matches will be displayed in the command output area. The default search path
  is the current project path, and can be set with the `set project_path`
  command.
- Add `...` abbreviation for the project path. This is displayed in window
  titles and other places where abbreviated paths are displayed. It can also be
  typed in the command bar to reference file paths from the root of the current
  project. Example: `ack "def delimit" .../editxt`.
- Change: use selected text as default pattern for `ack` command.
- Change: use first matching choice instead of error on ambiguous argument
  typed in command bar.
- Change: prompt on save if file has path but does not exist on disk.
- Do not open error log in new window on launch.
- Convert newlines to match document on paste multi-line text.
- Fix no document selected in tree after drag/drop.
- Fix line numbers overlapping text on goto line > 100 in newly opened document.
- Fix bugs in file command argument parser.
- Fix sluggish line insertion on Mac OS 10.11.
- Remove unnecessary "Paste and Match Style" menu item.
- Hopefully fix `xt` script lag.
- Fix/reset text attributes on reload document.

## 2015-11-14 - 1.8.1

- Fix `python` command in packaged EditXT.app

## 2015-11-14 - 1.8.0

- [Pick a font](http://hivelogic.com/articles/top-10-programming-fonts/)!
  (install if necessary) then `set font YourFavoriteFont` to give it a spin.
  Finally, `open ~/.editxt/config.yaml` and set your preferred font.
  For example:
  ```
  font:
    face: Inconsolata
    size: 14
  ```
  Save and `reload_config`. If you really don't like change you can revert to
  the old font style:
  ```
  font:
    face: Monaco
    size: 10
    smooth: false
  ```
  The system default fixed width font and size will be used if no font is set
  in the config. To view the current font, type `set font` in the command bar
  and observe the default parameter values.
- Improve line numbers, including support for correct numbering on soft-wrapped
  documents. The line number view now uses the same background and border color
  as the right margin. These colors can be customized in the config:
  ```
  line_number_color: 707070
  right_margin:
    position: 80
    line_color: E6E6E6
    margin_color: F7F7F7
  ```
- Select line(s) on click/drag in line number view.
- Rescan selection on Replace (Command+=), and replace only if the find
  text/pattern is found in the selection.
- Add `python` command, which executes the current file content or selection
  as python code. It does the same thing as `python -c CODE` in a terminal.

## 2015-01-31 - 1.7.6

- Fix bugs in command parser.

## 2015-01-06 - 1.7.5

- Show message instead of beep on `ack` command with no match.
- Do not update command history on keyboard document navigation.
- Switch to a file in another project with `doc PROJECT FILE`.
- Add `nonlocal` keyword to Python syntax definition.
- Fix crasher bug related to command bar view.
- Fix missing command auto-complete title.
- Fix various bugs in `doc` command.

## 2015-01-01 - 1.7.4

- NOTE for users updating from versions before 1.7.1: you need to run a
  command in the terminal before clicking **Install and Relaunch** during the
  update process (adjust the `/Applications/EditXT.app` part of the path to
  where EditXT.app is located on your local machine):
  ```
  chmod +x /Applications/EditXT.app/Contents/Frameworks/Sparkle.framework/Versions/Current/Resources/Autoupdate.app/Contents/MacOS/Autoupdate
  ```
- Add/update syntax definitions: Bind zone, diff, Jinja, SQL
- Fix packaging issue that broke auto-updater.
- Fix parse error in commands with file arguments.

## 2014-12-31 - 1.7.3

- NOTE for users updating from versions before 1.7.1: you need to run a
  command in the terminal before clicking **Install and Relaunch** during the
  update process (adjust the `/Applications/EditXT.app` part of the path to
  where EditXT.app is located on your local machine):
  ```
  chmod +x /Applications/EditXT.app/Contents/Frameworks/Sparkle.framework/Versions/Current/Resources/Autoupdate.app/Contents/MacOS/Autoupdate
  ```
- Better fix for bug in sparkle framework that prevented check for updates.
- Disable font smoothing in views that use the default fixed width font, which
  is currently hard-coded at Monaco 10pt. It appears that the upgrade to
  py2app 0.9 somehow caused the main text view to draw anti-aliased text. User
  font preferences are on the todo list, so hopefully we won't need this hack
  for long.
- Add version history page for Sparkle updates on github.

## 2014-12-31 - 1.7.2

- NOTE for users updating from versions before 1.7.1: you need to run a
  command in the terminal before clicking **Install and Relaunch** during the
  update process (adjust the `/Applications/EditXT.app` part of the path to
  where EditXT.app is located on your local machine):
  ```
  chmod +x /Applications/EditXT.app/Contents/Frameworks/Sparkle.framework/Versions/Current/Resources/Autoupdate.app/Contents/MacOS/Autoupdate
  ```
- Fix bug in sparkle framework that prevented check for updates.
- Fix deprecated image drawing call.
- Add syntax definition for git diff format.

## 2014-12-30 - 1.7.1

- Fix a bug that prevented auto-update.
  NOTE: you need to run a command in the terminal before clicking
  **Install and Relaunch** during the update process (adjust the
  `/Applications/EditXT.app` part of the path to where EditXT.app
  is located on your local machine):
  ```
  chmod +x /Applications/EditXT.app/Contents/Frameworks/Sparkle.framework/Versions/Current/Resources/Autoupdate.app/Contents/MacOS/Autoupdate
  ```
  Bug details: https://github.com/sparkle-project/Sparkle/issues/309

## 2014-12-30 - 1.7.0

- Add customizable *Shortcuts* menu for quick command execution. The items in
  this menu can be customized by adding a `shortcuts` section to the config
  file (EditXT > Preferences). For example:
  ```
  shortcuts:
    Command+C: clear_highlighted_text
    Command+Alt+s: sort
  ```
  Note:
  - Menu is not yet updated with `reload_config` command. Restart for now.
  - The following key combinaations are equivalent:
    `Command+C` and `Command+Shift+c`
  - The *Shortcuts* menu is pre-loaded with shortcuts for document tree
    navigation. These default shortcuts are merged with the custom shortcuts
    specified in the config file.
  - Some shortcuts in other menus cannot be overridden with custom shortcuts.
- Add `doc` command for document tree navigation. This command can be used
  to focus editors by name, in the order they have been most recently visited
  (`previous` / `next`), or by relative position (`up` / `down`).
- Rename *Text* menu to *Command*
- Add command bar help, which is accessed with F1 key or with the
  *Help > Command Help* menu item when the command bar is active.
- Add button to show command output in panel so it can be preserved while
  other commands that produce output are executed.
- Fix `ack` command output formatting.
- Eliminate superfluous trailing backslash in ack command output.
- Fix `open` command creating duplicate editor.
- Fix command bar auto-complete bugs.
- Fix display flash on hide command view.
- Various other bug fixes.

## 2014-12-01 - 1.6.0

- Toggle last command output with Escape key.
- Add `ack` command integration for code search. Command output contains
  clickable links to open files. Command+click to open files in background.
  Ack ([http://beyondgrep.com/](http://beyondgrep.com/)) must be installed and
  the path to the ack executable may need to be specified in preferences. For
  example:
  ```
  command:
    ack:
      path: /usr/local/bin/ack
  ```
- Add `grab` command to collect lines matching a pattern.
- Add `open` command (also `xt`) for opening files from command bar.
- Add support for invoking commands from project view.
- Add `set project_path ...` command. The project path is used as a fallback
  default path for commands that touch the filesystem if the current editor
  does not have a path.
- Add Sparkle updater for automatic updates.
- Improve command bar auto-complete menu so it doesn't display off screen.
- Improve auto-complete algorithm to use longest common substring rather
  than currently selected item.

## 2014-10-24 - 1.5.3

- Fix bug that prevented text command sheets from closing.

## 2014-10-22 - 1.5.2

- Fix bad “Save as...” prompt on save after reload.

## 2014-10-21 - 1.5.1

- Fix bug in automatic file reload.

## 2014-10-17 - 1.5.0

- Internal refactoring and bug fixes: eliminate NSDocument framework.
  - Closing a project with modified documents now prompts to save changes.
- Add recently closed document list as main project view.
- Re-open error log (rather than new document named "EditXT Log") on launch.
- Allow drag/drop documents to other applications.
- Allow copy and move documents in file tree (hold Command key to copy).
- Fix bug in content analysis (indent mode and size, EOL mode).

## 2014-05-18 - 1.4.0

- Add `*.mm` to Objective-C syntax definition file patterns.
- Fix bug that preventing opening document via File > Open dialog.
- Add diff command to compare with file on disk.
- Improve error handling for find commands.
- Improve error logging.
- Suppress traceback on break xt script.
- Overlay scrollers on OS X 10.7+
- Runs on Python 3.
- Fix bug that prevented replace with nothing (empty string).
- Added Python Replace feature to find command. This feature evaluates a
  Python expression during the replace phase of a find/replace operation
  allowing text transformations such as case changes or conditional
  replacements, far beyond what is possible with a regular expression find/
  replace operation. Example replace expression:
  ```
  match[1].lower() + match[2]
  ```
- Dramatic performance boost when highlighting selected text.
- Add count-occurrences action to find command.
- Add right_margin config settings:
  ```
  right_margin:
    position: 80
    line_color: BBDDBB
    margin_color: DDBBDD
  ```
- Add syntax definitions for shell scripts and Objective C

## 2013-09-26 - 1.3.2

- Use SafeDump to dump editor config files (preparation for v1.4).

## 2013-09-26 - 1.3.1

- Fix bug that prevented replace with nothing (empty string).

## 2013-09-22 - 1.3.0

- Omit command from history if it has a leading space.
- Integrate GUI and hotkey commands with command bar history.
- Improve indent size calculation.
- Added status message output to command bar.
- Log config file path on load.
- Move document defaults to config file:
  ```
  indent:
    mode: (space|tab) # default is space
    size: 4
  newline_mode: (LF|CR|CRLF|UNICODE) # default is LF
  soft_wrap: (none|word)
  ```
- Added commands:
  - Clear highlighted text (`clear_highlighted_text`).
  - Reload config (`reload_config`)
  - `set <variable> ...` to set document variables:
    - `highlight_selected_text`
    - `indent`
    - `newline_mode`
    - `soft_wrap`
- Make Preferences... menu item open config file.
- Add config file (`~/.editxt/config.yaml`) with selection matching settings:
  ```
  highlight_selected_text:
    enabled: (yes|no) # default is yes
    color: FEFF6B
  ```
- Mark occurrences when counting with the find dialog.
- Mark (highlight) all occurrences of selected text (length > 3, containing
  no spaces), yellow for now.
- Allow close document from menu and with *Command+W* hotkey
- Many improvements on command bar
  - More commands: `wrap`, `sort`, `/find/replace/i`
  - Argument placeholders/hints
  - Tab completion
  - Command history
- Improve exception logging.
- Fix bugs related to app termination with unsaved documents.
- Fix log file syntax highlighting.
- Fix startup errors due to strange arguments passed by OS X.
- Fix long pause on quit with many documents open.

## 2013-01-05 - 1.2.0 (unreleased)

- Add command bar (needs more work, but it's minimally usable).
- Add "Goto Line" command: type line number in command bar.
- Store app config and state in `~/.editxt`.
- Add `xt` command line script to packaged app.
- Display full path in window title and document tooltips.
- Fix cursor column status view: left-most position is now 0 instead of 1.
- Create new (empty) document when opening non-existent path from command
  line.
- Always move (do not copy) document or project on internal drag.

## 2012-05-22 - 1.1.0

- Added non-padded (un)comment text command. This is now the default comment
  mode (*Shift+,*). Moved old command to *Command+Shift+,*.
- Improve button text in find/replace dialog.
- Fixed bug in backspace at end of line with trailing whitespace.
- Fixed bug in document auto-reload which caused a prompt to "Save As..."
  on next save.
- Fixed bug: crash on OS X Lion when collapsing project.
- Fixed bug: crash on OS X Lion due to no current project in settings file on
  launch. 'NSNull' object has no attribute 'indexAtPosition_' in editor.py
  line 290, in get_current_project.
- Internal: upgrade to PyObjC 2.3 and Python 2.7.3.
- Internal: improve logging configuration.
- Internal: major package reorganization.

## 2010-10-13 - 1.0.1

- Fixed undo and document pane hover bugs.

## 2010-08-16 - 1.0.0

- Added GPLv3 license and released on github.com

## 2007-12-29 - Initial development

During this period, as soon as it was functional enough for day-to-day use,
EditXT was used as the primary editor with which to further develop itself.
In addition to that, EditXT was also used on a daily basis for other
software development.
