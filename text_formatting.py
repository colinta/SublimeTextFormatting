import os.path
import re
import json
from functools import cmp_to_key

import sublime
import sublime_plugin


class TextFormattingTree(sublime_plugin.TextCommand):
    TREE = [' ', '├', '└', '─', '│', '\t', '*', '-']

    def run(self, edit, **kwargs):
        error = None
        for region in self.view.sel():
            try:
                self.run_each(edit, region, **kwargs)
            except Exception as exception:
                self.view.show_popup(str(exception))
                raise exception

    def run_each(self, edit, region):
        def create_node(name):
            return {"name": name, "children": []}

        def custom_trim(line):
            trimmed = ''
            for c in line.strip():
                if trimmed == '' and c in self.TREE:
                    continue
                trimmed += c
            return trimmed

        def render_tree(node, front=''):
            if not node['children']:
                return node['name']

            if node['name']:
                lines = [node['name']]
            else:
                lines = ['.']

            # lines = [node['name'] or '']
            for (index, child) in enumerate(node['children']):
                if index == len(node['children']) - 1:
                    first = '└── '
                    next_front = front + '    '
                else:
                    first = '├── '
                    next_front = front + '│   '

                lines.append(front + first + render_tree(child, next_front))
            return '\n'.join(lines) + ('\n' if front == '' else '')

        # convert bulleted list into an tree
        # using ├ └ ─ ╼ characters
        lines = self.view.substr(region).splitlines()
        if lines[0] == '.':
            lines = lines[1:]

        stack = []
        current_node = create_node(None)
        current_indent = None
        prev_node = None
        required_indent = None

        def flush(current_node, current_indent, indent, stack):
            last_indent = current_indent
            while indent < last_indent:
                if not stack:
                    break
                [last_node, last_indent] = stack.pop()
                # last_node['children'].append(current_node)
                if not last_node:
                    break
                current_node = last_node
                current_indent = last_indent
            return (current_node, current_indent)

        for line in lines:
            if not line.strip():
                continue

            node = create_node(custom_trim(line))
            indent = len(line) - len(custom_trim(line))
            if current_indent is None:
                current_indent = indent
                required_indent = indent

            if prev_node is None:
                min_indent = indent
            elif indent < min_indent or min_indent != required_indent:
                raise Exception('Indentation level is not consistent for item "' + line.strip() + '" (expected indentation ' + repr(required_indent) + ')')

            line = line.strip()[min_indent:]

            if indent > current_indent:
                stack.append([current_node, current_indent])
                current_node = prev_node
                current_indent = indent
            elif indent < current_indent:
                current_node, current_indent = flush(current_node, current_indent, indent, stack)

            current_node['children'].append(node)
            prev_node = node

        current_node, current_indent = flush(current_node, current_indent, 0, stack)
        self.view.replace(edit, region, render_tree(current_node))


class TextFormattingPrettifyJson(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        for region in self.view.sel():
            try:
                self.run_each(edit, region, **kwargs)
            except Exception as exception:
                error = str(exception)

            if error:
                self.view.show_popup(error)

    def run_each(self, edit, region, maxlength=80):
        if region.empty():
            return

        replace_str = json.dumps(json.loads(self.view.substr(region)), sort_keys=True, indent=4)
        self.view.replace(edit, region, replace_str)


class TextFormattingMaxlengthCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        for region in self.view.sel():
            try:
                self.run_each(edit, region, **kwargs)
            except Exception as exception:
                error = str(exception)
                self.view.show_popup(error)

    def is_lang(self, region, *langs):
        for lang in langs:
            if bool(self.view.score_selector(region.a, lang)):
                return True
        return False

    def run_each(self, edit, region, maxlength=80):
        if region.empty():
            region = self.view.line(region)

        is_php = self.is_lang(region, 'source.php')
        is_haskell = self.is_lang(region, 'source.haskell')
        is_python = self.is_lang(region, 'source.python')
        is_java = self.is_lang(region, 'source.python', 'source.Kotlin')
        is_javascript = self.is_lang(region, 'source.ts', 'source.tsx', 'source.js')

        if is_php:
            indent_regex = re.compile(r'^\s*(#|//| \* )?\s*')
        elif is_python:
            indent_regex = re.compile(r'^\s*(#)?\s*')
        elif is_java:
            indent_regex = re.compile(r'^\s*(\*)?\s*')
        elif is_javascript:
            indent_regex = re.compile(r'^\s*(\*)?\s*')
        elif is_haskell:
            indent_regex = re.compile(r'^\s*(--)?\s*')
        else:
            indent_regex = re.compile(r'^\s*(#|//)?\s*')
        markdown_indent_regex = re.compile(r'^\s*([-*+]|[0-9]+\.)[ ]*')
        selection = self.view.substr(region)

        lines = selection.splitlines()
        if selection[-1] == "\n":
            lines.append('')

        # remove initial indent from all lines
        initial_indent = None
        for line in lines:
            if not line:
                continue
            # markdown correction - if the first line is [-*+]|[0-9]\.?[ ]*,
            # and every subsequent line has whitespace in the place of those
            # characters, skip that line
            if initial_indent is None and markdown_indent_regex.match(line):
                pass
            indent = indent_regex.match(line).group(0)
            # if the line is matching a line that is only a blank comment,
            # we should disregard it.
            if initial_indent is None or \
                    (len(indent) < len(initial_indent) and line != indent):
                initial_indent = indent
            # don't bother continuing if we've eaten up the entire indentation
            if len(initial_indent) == 0:
                break

        if initial_indent:
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


class TextFormattingLineNumbers(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            line_no = self.view.rowcol(region.a)[0] + 1
            self.view.replace(edit, region, str(line_no))



def first_digits(line):
    numeric_regex = re.compile(r'\A([^\d]*)(\d+)([^\d]*)\Z', re.DOTALL)
    match = numeric_regex.match(line)
    if not match:
        return '0'
    return match.group(2)

class TextFormattingSort(sublime_plugin.TextCommand):
    def run(self, edit, case_sensitive=False, numeric=False):
        if len(self.view.sel()) == 1:
            lines = self.view.lines(self.view.sel()[0])
            self.view.sel().clear()
            for sel in lines:
                self.view.sel().add(sel)
            self.sort(edit, lines, case_sensitive=case_sensitive, numeric=numeric, did_select=True)

        elif self.view.sel():
            self.sort(edit, [sel for sel in self.view.sel()], case_sensitive, numeric=numeric, did_select=False)

    def sort(self, edit, selections, case_sensitive, numeric, did_select):
        max_digits = 0
        if numeric:
            for sel in selections:
                line = self.view.substr(sel)
                digits = first_digits(line)
                max_digits = max(max_digits, len(digits))

        def transform(region):
            line = self.view.substr(region)
            sort_text = line.strip()
            if not case_sensitive:
                sort_text = sort_text.lower()
            if numeric:
                digits = first_digits(line)
                sort_text = '0' * (max_digits - len(digits)) + digits
            return {
                'region': region,
                'line': line,
                'sort_text': sort_text,
            }
        sort_model = [transform(region) for region in selections]

        sorted_list = sorted(sort_model, key=lambda trim: trim['sort_text'])

        if not did_select and sorted_list == sort_model:
            sorted_list = sorted(sort_model, key=lambda trim: trim['sort_text'], reverse=True)
        region_list = sorted([trim['region'] for trim in sort_model], key=lambda region: region.begin())

        for region, trim in list(zip(region_list, sorted_list))[::-1]:
            self.view.replace(edit, region, trim['line'])
