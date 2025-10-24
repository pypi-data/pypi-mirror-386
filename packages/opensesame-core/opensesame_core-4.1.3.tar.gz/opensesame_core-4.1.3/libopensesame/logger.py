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
import fnmatch
from libopensesame.oslogging import oslogger
from libopensesame.exceptions import InvalidOpenSesameScript


class Logger(Item):
    """The logger item logs experimental data (i.e. variables)."""
    
    description = 'Logs experimental data'
    is_oneshot_coroutine = True

    def reset(self):
        self.logvars = []
        self._logvars = None
        self.var.auto_log = 'yes'
        self.exclude_patterns = []
        self._exclude_vars = []
        
    def _is_excluded(self, var):
        if var in self._logvars:
            return False
        if var in self._exclude_vars:
            return True
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(var, pattern):
                self._exclude_vars.append(var)
                return True
        return False

    def run(self):
        self.set_item_onset()
        if self._logvars is None:
            if self.var.auto_log == 'yes':
                self._logvars = self.experiment.log.all_vars()
            else:
                self._logvars = []
            for var in self.logvars:
                if var not in self._logvars and not self._is_excluded(var):
                    self._logvars.append(var)
            self._logvars.sort()
        # If we are automatically logging all variables, emit a warning when
        # a new variable was created after the first logger call, because it
        # will not be logged in that case.
        elif self.var.auto_log == 'yes':
            for var in self.experiment.log.all_vars():
                if var not in self._logvars and not self._is_excluded(var):
                    oslogger.warning(
                        f'the variable {var} was created after the first '
                        f'logger call and will therefore not be logged.')
        self.experiment.log.write_vars(self._logvars)

    def coroutine(self, coroutines):
        yield
        self.run()

    def from_string(self, string):
        self.var.clear()
        self.comments = []
        self.reset()
        if string is None:
            return
        for line in string.split('\n'):
            self.parse_variable(line)
            cmd, arglist, kwdict = self.experiment.syntax.parse_cmd(line)
            if cmd in ('log', 'exclude') and len(arglist) > 0:
                if cmd == 'log':
                    for var in arglist:
                        if not self.experiment.syntax.valid_var_name(
                                safe_decode(var)):
                            oslogger.error(
                                f'{var} is not a valid variable name')
                    self.logvars += arglist
                else:
                    self.exclude_patterns += arglist

    def to_string(self):
        s = super().to_string('logger')
        for var in self.logvars:
            s += '\t' + self.experiment.syntax.create_cmd(
                'log', [var]) + '\n'
        for var in self.exclude_patterns:
            s += '\t' + self.experiment.syntax.create_cmd(
                'exclude', [var]) + '\n'
        return s


# Alias for backwards compatibility
logger = Logger
