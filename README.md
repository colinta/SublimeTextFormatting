Text Formatting
===============

Adds text-formatting tricks to Sublime Text.  Mostly for PEP8 formatting.

Installation
------------

1. Using Package Control, install "TextFormatting"

Or:

1. Open the Sublime Text 3 Packages folder

    - OS X: ~/Library/Application Support/Sublime Text 3/Packages/
    - Windows: %APPDATA%/Sublime Text 3/Packages/
    - Linux: ~/.Sublime Text 3/Packages/

2. clone this repo
3. Install keymaps for the commands (see Example.sublime-keymap for my preferred keys)

Commands
--------

`text_formatting_maxlength`: Wraps text to `maxlength` (default: 80) characters.
Select a bunch of docstrings or README content and it will not just *warp* lines,
but it will also combine lines that are *too short*, so you can with aplomb
and reformat when you're done.

Also works with comments.  Lines that have `#` or `//` are considered part of the
"indent", and so they'll be removed and re-added.

`text_formatting_prettify_json`: Select some gnarly JSON and this command will make it well formatted.

`text_formatting_line_numbers`: Just prints the current line number under the cursor.
