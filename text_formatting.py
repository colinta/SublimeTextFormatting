import re

import sublime
import sublime_plugin


class NonBreakingBreak:
    pass
NonBreakingBreak = NonBreakingBreak()


class TextFormattingMaxlengthCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        e = self.view.begin_edit('text_formatting')
        regions = [region for region in self.view.sel()]

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def compare(region_a, region_b):
            return cmp(region_b.end(), region_a.end())
        regions.sort(compare)

        for region in regions:
            error = self.run_each(edit, region, **kwargs)
            if error:
                sublime.status_message(error)
        self.view.end_edit(e)

    def run_each(self, edit, region, maxlength=80):
        if region.empty():
            region = self.view.line(region)

        is_php = self.view.score_selector(region.a, 'source.php')
        is_haskell = self.view.score_selector(region.a, 'source.haskell')
        is_python = self.view.score_selector(region.a, 'source.python')
        if is_php:
            indent_regex = re.compile(r'^\s*?(#|//| \* )?\s*')
        elif is_python:
            indent_regex = re.compile(r'^\s*?(#)?\s*')
        elif is_haskell:
            indent_regex = re.compile(r'^\s*?(--)?\s*')
        else:
            indent_regex = re.compile(r'^\s*(#|//)?\s*')
        markdown_indent_regex = re.compile(r'^\s*([-*+]|[0-9]\.)\s*')
        selection = self.view.substr(region)

        lines = selection.splitlines()
        if selection[-1] == "\n":
            lines.append('')

        # remove initial indent from all lines
        initial_indent = None
        for line in lines:
            if not line:
                continue
            # markdown correction - if the first line is [-*+0-9]\.? *,
            # and every subsequent line has whitespace in the place of those
            # characters,
            if initial_indent is None and markdown_indent_regex.match(line):
                pass
            indent = indent_regex.match(line).group(0)
            # if the line is matching a line that is only a blank comment,
            # we should disregard it.
            if initial_indent is None or \
                    (len(indent) < len(initial_indent) and line != indent):
                initial_indent = indent
            # don't bother contuing if we've eaten up the entire indentation
            if len(initial_indent) == 0:
                break

        if initial_indent:
            maxlength -= len(initial_indent)
            if maxlength <= 0:
                return
            lines = map(lambda line: line[len(initial_indent):], lines)

        # combine sequential lines
        combined = []
        current = u''
        for line in lines:
            if re.match(r'^\s*$', line):
                if current:
                    combined.append(current)
                combined.append('')
                current = ''
            else:
                if current:
                    current += u' '
                current += line

        if current:
            combined.append(current)

        lines = combined

        # one more line - this ensures that the last line is truncated
        lines.append(None)

        ret = []
        current = None
        for line in lines:
            while current and len(current) > maxlength:
                current, too_much = current[:maxlength], current[maxlength:]
                if too_much and too_much[0] == ' ':
                    current += ' '
                    too_much = too_much[1:]

                indent = indent_regex.match(current).group(0)
                if ' ' in current:
                    space = current.rindex(' ')
                else:
                    space = None

                if not space or space < len(indent):
                    if ' ' in too_much:
                        current += too_much[:too_much.index(' ')]
                        ret.append(current)
                        current = too_much[too_much.index(' ') + 1:]
                    else:
                        ret.append(current + too_much)
                        current = ''
                else:
                    ret.append(current[:space])
                    # remove the trailing space and continue working on current
                    current = indent + current[space + 1:] + too_much

            if not line or re.match(r'^\s*$', line):
                if current:
                    ret.append(current)
                    current = None
                if line is not None:
                    ret.append('')
            else:
                indent = indent_regex.match(line).group(0)
                line = line[len(indent):].strip()
                if current:
                    current += u' '
                else:
                    current = indent
                current += line

        if initial_indent:
            ret = map(lambda line: line and initial_indent + line or line, ret)

        self.view.replace(edit, region, "\n".join(ret))

    def parse(self, selection):
        # - blocks of whitespace, separated by two newlines
        # - blocks of comments, separated by two newlines
        # - blocks of markdown-style lists
        return [selection]


class TextFormattingDebugPython(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        e = self.view.begin_edit('text_formatting')
        regions = [region for region in self.view.sel()]

        error = None
        empty_regions = []
        debug = ''
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if debug:
                    debug += "\n"
                debug += "{s}: {{{s}!r}}".format(s=s.replace('"', '').replace("'", ''))
                self.view.sel().subtract(region)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            for empty in empty_regions:
                line_no = self.view.rowcol(empty.a)[0] + 1
                p = 'print("""=============== at line {line_no} ===============\n'.format(line_no=line_no)
                p += debug
                p += '\n""".format(**locals()))'
                self.view.insert(edit, empty.a, p)

        if error:
            sublime.status_message(error)
        self.view.end_edit(e)


class TextFormattingDebugRuby(sublime_plugin.TextCommand):
    def run(self, edit, puts="puts"):
        e = self.view.begin_edit('text_formatting')
        regions = [region for region in self.view.sel()]

        error = None
        empty_regions = []
        debug = ''
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if debug:
                    debug += "\n"
                debug += "{s}: #{{{s}.inspect}}".format(s=s)
                self.view.sel().subtract(region)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            for empty in empty_regions:
                line_no = self.view.rowcol(empty.a)[0] + 1
                p = puts + '("=============== at line {line_no} ===============\n'.format(line_no=line_no)
                p += debug
                p += '")'
                self.view.insert(edit, empty.a, p)

        if error:
            sublime.status_message(error)
        self.view.end_edit(e)
