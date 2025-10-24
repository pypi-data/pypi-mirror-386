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
from libopensesame.py3compat import *
from libopensesame.item import Item
from libopensesame.exceptions import PythonError, PythonSyntaxError, \
    AbortCoroutines


class InlineScript(Item):
    """Allows users to use Python code in their experiments."""
    
    description = u'Executes Python code'

    def reset(self):
        """See item."""
        self.var._prepare = u''
        self.var._run = u''
        self._var_info = None

    @property
    def workspace(self):

        return self.experiment.python_workspace

    def prepare(self):
        r"""Executes the prepare script. The code that you enter in the
        'prepare' tab of an inline_script item in the GUI is used as a body for
        this function.
        """
        super().prepare()
        # 'self' must always be registered, otherwise we get confusions between
        # the various inline_script items.
        self.workspace[u'self'] = self
        # Compile prepare script
        try:
            self.cprepare = self.workspace._compile(
                self.var.get(u'_prepare', _eval=False))
        except SyntaxError as e:
            raise PythonSyntaxError(
                'Syntax error in inline script (prepare phase)',
                line_nr=e.lineno)
        # Compile run script
        try:
            self.crun = self.workspace._compile(
                self.var.get(u'_run', _eval=False))
        except SyntaxError as e:
            raise PythonSyntaxError(
                'Syntax error in inline script (run phase)',
                line_nr=e.lineno)
        # Run prepare script
        try:
            self.workspace._exec(self.cprepare)
        except Exception as e:
            raise PythonError(
                'Error while executing inline script (prepare phase)')

    def run(self):
        r"""Executes the run script. The code that you enter in the 'run' tab
        of an inline_script item in the GUI is used as a body for this
        function.
        """
        self.set_item_onset()
        # 'self' must always be registered, otherwise we get confusions between
        # the various inline_script items.
        self.workspace[u'self'] = self
        try:
            self.workspace._exec(self.crun)
        except Exception as e:
            raise PythonError(
                'Error while executing inline script (run phase)')

    def coroutine(self, coroutines):
        """See coroutines plug-in"""
        yield
        self.set_item_onset()
        while True:
            self.workspace[u'self'] = self
            try:
                self.workspace._exec(self.crun)
            except AbortCoroutines as e:
                # If the inline_script is part of a coroutines, this signals
                # that the coroutines should be aborted, so we don't wrap it
                # into a PythonError.
                raise
            except Exception as e:
                raise PythonError(
                    'Error while executing inline script (coroutines)')
            yield


# Alias for backwards compatibility
inline_script = InlineScript
