 Text Formatting for Sublime Text 2
====================================

Adds text-formatting tricks to Sublime Text.  Mostly for PEP8 formatting.

 Installation
--------------

1. Using Package Control, install "Text Formatting"

Or:

1. Open the Sublime Text 2 Packages folder

    - OS X: ~/Library/Application Support/Sublime Text 2/Packages/
    - Windows: %APPDATA%/Sublime Text 2/Packages/
    - Linux: ~/.Sublime Text 2/Packages/

2. clone this repo
3. Install keymaps for the commands (see Example.sublime-keymap for my preferred keys)

 Commands
----------

`text_formatting_maxlength`: Wraps text to `maxlength` (default: 80) characters.
Select a bunch of docstrings or README content and it will not just *warp* lines,
but it will also combine lines that are *too short*, so you can with aplomb
and reformat when you're done.

Also works with comments.  Lines that have `#` or `//` are considered part of the
"indent", and so they'll be removed and re-added.

`text_formatting_debug_python`: Select multiple variables, then put an empty
cursor somewhere and run this command (default: `ctrl+p` twice or `ctrl+p,p`).  You'll get
some good debug output that looks like this:

```python
print("""=============== at line 38 ===============
looks: {looks!r}
like: {like!r}
this: {this!r}
""".format(**locals()))
```

`text_formatting_debug_ruby`: Similar to `text_formatting_debug_python`
(default: `ctrl+p, ctrl+r` or `ctrl+p,r`).  Output looks like this:

```ruby
puts(<<debug)
=============== at line 49 ===============
looks: #{looks.inspect}
like: #{like.inspect}
this: #{this.inspect}
debug
```

For [rubymotion][] development, you can use `NSLog` instead of `puts`:

    { "keys": ["ctrl+p", "ctrl+p"], "command": "text_formatting_debug_python", "args": { "puts": "NSLog" } },

[rubymotion]: http://rubymotion.com/
