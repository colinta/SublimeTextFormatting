import re

import sublime
import sublime_plugin


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

        # there is an off-by-one error in the "look for a space" code.
        maxlength += 1
        # fixed!

        indent_regex = '^\s*(#|//)? *'
        selection = self.view.substr(region)
        lines = selection.splitlines()
        if selection[-1] == "\n":
            lines.append('')

        # remove initial indent from all lines
        initial_indent = None
        for line in lines:
            if not line:
                continue
            indent = re.match(indent_regex, line).group(0)
            if initial_indent is None or len(indent) < len(initial_indent):
                initial_indent = indent
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
            if re.match('^\s*$', line):
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
                indent = re.match(indent_regex, current).group(0)
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

            if not line or re.match('^\s*$', line):
                if current:
                    ret.append(current)
                    current = None
                if line is not None:
                    ret.append('')
            else:
                indent = re.match(indent_regex, line).group(0)
                line = line[len(indent):].strip()
                if current:
                    current += u' '
                else:
                    current = indent
                current += line

        if initial_indent:
            ret = map(lambda line: line and initial_indent + line or line, ret)

        self.view.replace(edit, region, "\n".join(ret))
