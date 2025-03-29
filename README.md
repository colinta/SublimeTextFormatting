Text Formatting
===============

Adds text-formatting tricks to Sublime Text.  Mostly for PEP8 formatting.

Installation
------------

Using Package Control, install "TextFormatting" or clone this repo in your packages folder.

I recommended you add key bindings for the commands. I've included my preferred bindings below.
Copy them to your key bindings file (⌘⇧,).

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

Key Bindings
------------

Copy these to your user key bindings file.

<!-- keybindings start -->
    { "keys": ["super+shift+space"], "command": "text_formatting_maxlength" },
    { "keys": ["ctrl+l"], "command": "text_formatting_line_numbers" },
    { "keys": ["ctrl+alt+t"], "command": "text_formatting_tree" },
    { "keys": ["f5"], "command": "text_formatting_sort" },
    { "keys": ["ctrl+f5"], "command": "text_formatting_sort", "args": {"case_sensitive": true} },

    // not pertinant to this plugin, but useful for anyone who writes JSDoc/JavaDocs
    { "keys": ["/"], "command": "chain",
      "args": {
        "commands": [
          ["left_delete"],
          ["insert_snippet", {"contents": "/"}]
        ]
      },
      "context": [
        { "key": "selection_empty", "operator": "equal", "operand": true, "match_all": true },
        { "key": "preceding_text", "operator": "regex_match", "operand": "^ +\\* ", "match_all": true }
      ]
    },
<!-- keybindings stop -->
