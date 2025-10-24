# -*- coding:utf-8 -*-

"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""
from libopensesame import metadata
from libopensesame.py3compat import *
from libqtopensesame.misc.base_subcomponent import BaseSubcomponent
import re
import os
from libopensesame.oslogging import oslogger
from qtpy.QtGui import QGuiApplication
from qtpy.QtCore import Qt
try:
    import markdown
    from markdown.extensions import attr_list, extra, toc
except ImportError:
    oslogger.error(u'Unable to import markdown, proceeding without markdown')
    markdown = None
try:
    from pygments import highlight
    from pygments.lexers import Python3TracebackLexer as TracebackLexer
    from pygments.lexers import Python3Lexer as PythonLexer
    from pygments.formatters import HtmlFormatter
except ImportError:
    highlight = None
from libqtopensesame.misc.translate import translation_context
_ = translation_context(u'markdown', category=u'core')


class MarkdownParser(BaseSubcomponent):
    """A Markdown parser with syntax highlighting."""
    
    def __init__(self, main_window):
        """Constructor.

        Parameters
        ----------
        main_window
            The main-window object.
        """
        self.setup(main_window)
        mode = 'light'
        try:
            if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark:
                mode = 'dark'
        except Exception as e:
            oslogger.error(f'failed to detect dark mode: {e}')
        oslogger.info(f'using {mode} mode')        
        
        self.css = u'<style type="text/css">'
        with safe_open(self.main_window.theme.resource(
            f'markdown-{mode}.css')) as fd:
            self.css += fd.read() % {u'background_image':
                                     os.path.abspath(self.main_window.theme.resource(
                                         u'background.png'))}
        if highlight is not None:
            self.traceback_lexer = TracebackLexer()
            self.python_lexer = PythonLexer()
            self.html_formatter = HtmlFormatter()
            self.css += self.html_formatter.get_style_defs(u'.highlight')
            self.re_script = re.compile(
                r'^~~~\s*.(?P<syntax>\w+)(?P<script>.*?)^~~~', re.S | re.M)
        self.css += u'</style><link href="https://fonts.googleapis.com/css?family=Roboto+Slab&display=swap" rel="stylesheet">'
        if markdown is not None:
            self.ext = [attr_list.AttrListExtension(), extra.ExtraExtension(),
                        toc.TocExtension(title=u'Overview'),
                        u'markdown.extensions.tables']
        self.footer = u'''
<p>
<a class="dismiss-button" href="opensesame://action.close_current_tab">%s</a>
</p>

<div class="footer">
%s
Copyright <a href="http://www.cogsci.nl/smathot">Sebastiaan Mathôt</a> 2010-2025
</div>
''' % (_(u'Dismiss this message'), metadata.identity)

    def highlight(self, md):
        r"""Replaces ~~~ blocks with syntax-highlighted HTML code.

        Parameters
        ----------
        md : str
            A Markdown  string.

        Returns
        -------
        str
            A Markdown  string.
        """
        if highlight is None:
            return md
        while True:
            m = re.search(self.re_script, md)
            if m is None:
                break
            orig = m.group()
            syntax = m.group(u'syntax')
            script = m.group(u'script')
            if syntax == u'traceback':
                lexer = self.traceback_lexer
            elif syntax == u'python':
                lexer = self.python_lexer
            else:
                md = md.replace(orig, u'<code>%s</code>\n' % script)
                continue
            new = highlight(script, lexer, self.html_formatter)
            md = md.replace(orig, new)
        return md

    def to_html(self, md):
        r"""Converts Markdown to HTML.

        Parameters
        ----------
        md : str
            A Markdown  string.

        Returns
        -------
        str
            A Markdown  string.
        """
        md = self.highlight(md)
        if markdown is None:
            return u'<pre>%s</pre>' % md
        html = markdown.markdown(md, extensions=self.ext, errors=u'ignore') \
            + self.css + self.footer
        if html.startswith(u'<p>title:'):
            title, body = tuple(html.split(u'\n', 1))
            html = u'<h1>%s</h1>\n\n%s' % (title[9:-4], body)
        return html


# Alias for backwards compatibility
markdown_parser = MarkdownParser
