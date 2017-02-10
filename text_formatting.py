import os.path
import re
import json
from functools import cmp_to_key

import sublime
import sublime_plugin


def indent_at(view, region):
    line_start = view.line(region).begin()
    line_indent = view.rowcol(region.a)[1]
    return view.substr(sublime.Region(line_start, line_start + line_indent))


class TextFormattingPrettifyJson(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        for region in self.view.sel():
            try:
                error = self.run_each(edit, region, **kwargs)
            except Exception as exception:
                error = exception.message

            if error:
                sublime.status_message(error)

    def run_each(self, edit, region, maxlength=80):
        if region.empty():
            return

        replace_str = json.dumps(json.loads(self.view.substr(region)), sort_keys=True, indent=4)
        self.view.replace(edit, region, replace_str)


class TextFormattingMaxlengthCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        for region in self.view.sel():
            try:
                error = self.run_each(edit, region, **kwargs)
            except Exception as exception:
                error = exception.message

            if error:
                sublime.status_message(error)

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


class TextFormattingLineNumbers(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            line_no = self.view.rowcol(region.a)[0] + 1
            self.view.replace(edit, region, str(line_no))


class TextFormattingDebug(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        if not len(self.view.sel()):
            return

        location = self.view.sel()[0].begin()
        if self.view.score_selector(location, 'source.python'):
            self.view.run_command('text_formatting_debug_python', kwargs)
        elif self.view.score_selector(location, 'source.ruby.mac') or self.view.score_selector(location, 'source.rubymotion'):
            self.view.run_command('text_formatting_debug_ruby_motion', kwargs)
        elif self.view.score_selector(location, 'source.ruby'):
            self.view.run_command('text_formatting_debug_ruby', kwargs)
        elif self.view.score_selector(location, 'source.objc'):
            self.view.run_command('text_formatting_debug_objc', kwargs)
        elif self.view.score_selector(location, 'source.swift'):
            self.view.run_command('text_formatting_debug_swift', kwargs)
        elif self.view.score_selector(location, 'source.js'):
            self.view.run_command('text_formatting_debug_js', kwargs)
        elif self.view.score_selector(location, 'source.php'):
            self.view.run_command('text_formatting_debug_php', kwargs)
        elif self.view.score_selector(location, 'source.java'):
            self.view.run_command('text_formatting_debug_java', kwargs)
        elif self.view.score_selector(location, 'source.elixir'):
            self.view.run_command('text_formatting_debug_elixir', kwargs)
        else:
            sublime.status_message('No support for the current language grammar.')


class TextFormattingDebugPython(sublime_plugin.TextCommand):
    def run(self, edit, puts="print"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if debug:
                    debug += "\n"
                debug += "{s}: {{{count}!r}}".format(s=s, count=1 + len(debug_vars))
                debug_vars.append(s)
                self.view.sel().subtract(region)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
            return

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if self.view.file_name():
            name = os.path.basename(self.view.file_name())
        elif self.view.name():
            name = self.view.name()
        else:
            name = 'Untitled'

        if debug:
            output = puts + '("""=============== {name} at line {{0}} ==============='.format(name=name)
            output += "\n" + debug + "\n"
            output += '""".format(__import__(\'sys\')._getframe().f_lineno - {lines}, '.format(lines=1 + len(debug_vars))
            for var in debug_vars:
                output += var.strip() + ', '
            output += '))'
        else:
            output = puts + '("=============== {name} at line {{0}} ===============".format(__import__(\'sys\')._getframe().f_lineno))'.format(name=name)

        for empty in empty_regions:
            self.view.insert(edit, empty.a, output)

        if error:
            sublime.status_message(error)


class TextFormattingDebugRuby(sublime_plugin.TextCommand):
    def run(self, edit, puts="puts"):
        error = None
        empty_regions = []
        debug = ''
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if debug:
                    debug += "\n"
                if ' ' in s:
                    var = "({0})".format(s)
                else:
                    var = s
                debug += "{s}: #{{{var}.inspect}}".format(s=s.replace("\"", r'\"'), var=var)
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '("=============== {name} line #{{__LINE__}} ==============='.format(name=name)
            if debug:
                output += '\n=============== #{self.class == Class ? self.name + \'##\' : self.class.name + \'#\'}#{__method__} ===============\n'
                output += debug
            output += '")'

            for empty in empty_regions:
                self.view.insert(edit, empty.a, output)

        if error:
            sublime.status_message(error)


class TextFormattingDebugSwift(sublime_plugin.TextCommand):
    def run(self, edit, puts="print"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())

        if self.view.settings().get('translate_tabs_to_spaces'):
            tab = ' ' * self.view.settings().get('tab_size')
        else:
            tab = "\t"

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if ' ' in s:
                    var = "({0})".format(s)
                else:
                    var = s
                debug_vars.append((s, var))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            for (s, var) in debug_vars:
                if debug:
                    debug += "\n"
                debug += puts + "(\"{s}: \({var})\")".format(s=s.replace("\"", r'\"'), var=var)

            output = puts + '("=============== \(#file) line \(#line) ===============")'
            if debug:
                output += "\n" + debug

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)



class TextFormattingDebugElixir(sublime_plugin.TextCommand):
    def run(self, edit, puts="IO.puts"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())

        if self.view.settings().get('translate_tabs_to_spaces'):
            tab = ' ' * self.view.settings().get('tab_size')
        else:
            tab = "\t"

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if ' ' in s:
                    var = "({0})".format(s)
                else:
                    var = s
                debug_vars.append((s, var))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            for (s, var) in debug_vars:
                if debug:
                    debug += "\n"
                debug += puts + "(\"{s}: #{{inspect({var})}}\")".format(s=s.replace("\"", r'\"'), var=var)

            output = puts + '("=============== #{__ENV__.file} line #{__ENV__.line} ===============")'
            if debug:
                output += "\n" + debug

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextFormattingDebugObjc(sublime_plugin.TextCommand):
    def run(self, edit, puts="NSLog"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = ''
        regions = list(self.view.sel())
        not_empty_regions = 0
        for region in regions:
            if region:
                not_empty_regions += 1

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                if not debug_vars:
                    debug_vars = ', __PRETTY_FUNCTION__, __LINE__ - {0}'.format(not_empty_regions)
                s = self.view.substr(region)
                debug += "\\n\\\n"
                debug_vars += ", "
                debug += "{s}: %@".format(s=s.replace("\"", r'\"'))
                debug_vars += s
                self.view.sel().subtract(region)
        if not debug_vars:
            debug_vars = ', __PRETTY_FUNCTION__, __LINE__'

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '(@"=============== {name}:%s at line %i ==============='.format(name=name)
            output += debug
            output += '"'
            output += debug_vars
            output += ");"

            for empty in empty_regions:
                self.view.insert(edit, empty.a, output)

        if error:
            sublime.status_message(error)


class TextFormattingDebugJs(sublime_plugin.TextCommand):
    def run(self, edit, puts="console.log"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                debugs += ["'{s_escaped}:', {s}".format(s=s, s_escaped=s.replace("'", "\\'"))]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '(\'=============== {name} at line line_no ===============\');\n'.format(name=name)
            for debug in debugs:
                output += puts + "({debug});\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextFormattingDebugPhp(sublime_plugin.TextCommand):
    def run(self, edit):
        error = None
        empty_regions = []
        debugs = ''
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if debugs:
                    debugs += ", "
                debugs += "'{0}' => {1}".format(s.replace('\'', '\\\''), s)
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = '''$__LINE__ = __LINE__;error_log("=============== {name} at line $__LINE__ ===============");'''.format(name=name)
            if debugs:
                output += '''
ob_start();
var_dump(array({debugs}));
array_map('error_log', explode("\\n", ob_get_clean()));
'''[:-1].format(debugs=debugs)

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextFormattingDebugRubyMotion(TextFormattingDebugRuby):
    def run(self, edit, puts="NSLog"):
        return super(TextFormattingDebugRubyMotion, self).run(edit, puts)


class TextFormattingDebugJava(sublime_plugin.TextCommand):
    def run(self, edit, puts="System.out.println"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                debugs += ['"{s_escaped}:", {s}'.format(s=s, s_escaped=s.replace('"', '\\"'))]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '("=============== {name} at line line_no ===============");\n'.format(name=name)
            for debug in debugs:
                output += puts + "({debug});\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


