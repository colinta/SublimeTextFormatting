import os.path
import re
import json

import sublime
import sublime_plugin


class NonBreakingBreak:
    pass
NonBreakingBreak = NonBreakingBreak()


class TextFormattingPrettifyJson(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        e = self.view.begin_edit('text_formatting')
        regions = [region for region in self.view.sel()]

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        regions.sort(key=get_end, reverse=True)

        for region in regions:
            try:
                error = self.run_each(edit, region, **kwargs)
            except Exception as exception:
                print repr(exception)
                error = exception.message

            if error:
                sublime.status_message(error)
        self.view.end_edit(e)

    def run_each(self, edit, region, maxlength=80):
        if region.empty():
            return

        replace_str = json.dumps(json.loads(self.view.substr(region)), sort_keys=True, indent=4)
        self.view.replace(edit, region, replace_str)


class TextFormattingMaxlengthCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        e = self.view.begin_edit('text_formatting')
        regions = [region for region in self.view.sel()]

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        regions.sort(key=get_end, reverse=True)

        for region in regions:
            try:
                error = self.run_each(edit, region, **kwargs)
            except Exception as exception:
                print repr(exception)
                error = exception.message

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
        elif self.view.score_selector(location, 'source.js'):
            self.view.run_command('text_formatting_debug_js', kwargs)
        elif self.view.score_selector(location, 'source.php'):
            self.view.run_command('text_formatting_debug_php', kwargs)
        else:
            sublime.status_message('No support for the current language grammar.')


class TextFormattingDebugPython(sublime_plugin.TextCommand):
    def run(self, edit, puts="print"):
        e = self.view.begin_edit('text_formatting')
        regions = [region for region in self.view.sel()]

        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
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

        for empty in empty_regions:
            line_no = self.view.rowcol(empty.a)[0] + 1
            if debug:
                p = puts + '("""=============== {name} at line {{0}} ==============='.format(name=name, line_no=line_no)
                p += "\n" + debug + "\n"
                p += '""".format(__import__(\'sys\')._getframe().f_lineno - {lines}, '.format(lines=1 + len(debug_vars))
                for var in debug_vars:
                    p += var.strip() + ', '
                p += '))'
            else:
                p = puts + '("=============== {name} at line {{0}} ===============".format(__import__(\'sys\')._getframe().f_lineno))'.format(name=name, line_no=line_no)
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
                if ' ' in s:
                    var = "({0})".format(s)
                else:
                    var = s
                debug += "{s}: #{{{var}.inspect}}".format(s=s, var=var)
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            for empty in empty_regions:
                # line_no = self.view.rowcol(empty.a)[0] + 1
                if self.view.file_name():
                    name = os.path.basename(self.view.file_name())
                elif self.view.name():
                    name = self.view.name()
                else:
                    name = 'Untitled'
                p = puts + '("=============== {name} line #{{__LINE__}} ==============='.format(name=name)
                if debug:
                    p += '\n=============== #{self.class == Class ? self.name + \'##\' : self.class.name + \'#\'}#{__method__} ===============\n'
                    p += debug
                p += '")'
                self.view.insert(edit, empty.a, p)

        if error:
            sublime.status_message(error)
        self.view.end_edit(e)


class TextFormattingDebugObjc(sublime_plugin.TextCommand):
    def run(self, edit, puts="NSLog"):
        e = self.view.begin_edit('text_formatting')
        regions = [region for region in self.view.sel()]

        error = None
        empty_regions = []
        debug = ''
        debug_vars = ''
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                if not debug_vars:
                    debug_vars = ', __PRETTY_FUNCTION__, __LINE__+1'
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
            for empty in empty_regions:
                # line_no = self.view.rowcol(empty.a)[0] + 1
                if self.view.file_name():
                    name = os.path.basename(self.view.file_name())
                elif self.view.name():
                    name = self.view.name()
                else:
                    name = 'Untitled'
                p = puts + '(@"=============== {name}:%s at line %i ==============='.format(name=name)
                p += debug
                p += '"'
                p += debug_vars
                p += ");"
                self.view.insert(edit, empty.a, p)

        if error:
            sublime.status_message(error)
        self.view.end_edit(e)


class TextFormattingDebugJs(sublime_plugin.TextCommand):
    def run(self, edit, puts="console.log"):
        e = self.view.begin_edit('text_formatting')
        regions = [region for region in self.view.sel()]

        error = None
        empty_regions = []
        debugs = []
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
            for empty in empty_regions:
                line_start = self.view.line(empty).begin()
                line_indent = self.view.rowcol(empty.a)[1]
                indent = self.view.substr(sublime.Region(line_start, line_start + line_indent))
                line_no = self.view.rowcol(empty.a)[0] + 1
                if self.view.file_name():
                    name = os.path.basename(self.view.file_name())
                elif self.view.name():
                    name = self.view.name()
                else:
                    name = 'Untitled'
                output = puts + '("=============== {name} at line {line_no} ===============");\n'.format(name=name, line_no=line_no)
                for debug in debugs:
                    output += indent + puts + "({debug});\n".format(debug=debug)
                output = output[:-1]
                self.view.insert(edit, empty.a, output)

        if error:
            sublime.status_message(error)
        self.view.end_edit(e)


class TextFormattingDebugPhp(sublime_plugin.TextCommand):
    def run(self, edit):
        e = self.view.begin_edit('text_formatting')
        regions = [region for region in self.view.sel()]

        error = None
        empty_regions = []
        debugs = ''
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
            for empty in empty_regions:
                line_start = self.view.line(empty).begin()
                line_indent = self.view.rowcol(empty.a)[1]
                indent = self.view.substr(sublime.Region(line_start, line_start + line_indent))
                line_no = self.view.rowcol(empty.a)[0] + 1
                if self.view.file_name():
                    name = os.path.basename(self.view.file_name())
                elif self.view.name():
                    name = self.view.name()
                else:
                    name = 'Untitled'

                p = '''$__LINE__ = __LINE__;error_log("=============== {name} at line $__LINE__ ===============");'''.format(name=name, line_no=line_no)
                if debugs:
                    p += '''
{indent}ob_start();
{indent}var_dump(array({debugs}));
{indent}array_map('error_log', explode("\\n", ob_get_clean()));
'''[:-1].format(indent=indent, debugs=debugs)

                self.view.insert(edit, empty.a, p)

        if error:
            sublime.status_message(error)
        self.view.end_edit(e)


class TextFormattingDebugRubyMotion(TextFormattingDebugRuby):
    def run(self, edit, puts="NSLog"):
        return super(TextFormattingDebugRubyMotion, self).run(edit, puts)
