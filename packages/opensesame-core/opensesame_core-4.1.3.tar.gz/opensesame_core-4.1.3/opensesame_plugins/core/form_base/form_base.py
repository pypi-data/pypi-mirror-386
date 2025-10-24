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
from libopensesame.exceptions import InvalidFormScript, OSException, \
    InvalidValue
from libopensesame.item import Item
from libopensesame import widgets


class FormBase(Item):

    initial_view = 'script'

    def reset(self):
        self.var.cols = '2;2'
        self.var.rows = '2;2'
        self.var.spacing = 10
        self.var._theme = 'gray'
        self.var.only_render = 'no'
        self.var.timeout = 'infinite'
        self.var.margins = '50;50;50;50'
        self._widgets = []
        self._variables = []

    def set_validator(self):
        self.validator = FormBase

    def parse_line(self, line):
        cmd, arglist, kwdict = self.syntax.parse_cmd(line)
        if cmd != 'widget':
            return
        if len(arglist) != 5:
            raise InvalidFormScript(f'Invalid widget specification: {line}')
        self._widgets.append((arglist, kwdict))
        if 'var' in kwdict:
            self._variables.append(kwdict['var'])

    def to_string(self):
        s = super().to_string(self.item_type)
        for arglist, kwdict in self._widgets:
            s += '\t%s\n' % self.syntax.create_cmd('widget', arglist, kwdict)
        s += '\n'
        return s

    def run(self):
        self.set_item_onset()
        if self.var.only_render == 'yes':
            self._form.render()
        else:
            self._form._exec(focus_widget=self.focus_widget)

    def prepare(self):
        super().prepare()
        # Prepare the form
        try:
            cols = [float(i) for i in str(self.var.cols).split(';')]
            rows = [float(i) for i in str(self.var.rows).split(';')]
            margins = [float(i) for i in str(self.var.margins).split(';')]
        except Exception as e:
            raise InvalidValue('cols, rows, and margins should be numeric '
                               'values separated by a semi-colon')
        if self.var.timeout == 'infinite':
            timeout = None
        else:
            timeout = self.var.timeout
        self._form = widgets.Form(self.experiment, cols=cols, rows=rows,
                                  margins=margins, spacing=self.var.spacing,
                                  theme=self.var._theme,
                                  item=self, timeout=timeout,
                                  clicks=self.var.form_clicks == 'yes')

        self.focus_widget = None
        for arglist, orig_kwdict in self._widgets:
            kwdict = orig_kwdict.copy()
            # Evaluate all values
            arglist = [self.syntax.eval_text(arg, include_local=True)
                       for arg in arglist]
            for key, val in kwdict.items():
                kwdict[key] = self.syntax.eval_text(val, include_local=True)
            # Translate paths into full file names
            if 'path' in kwdict:
                kwdict['path'] = self.experiment.pool[kwdict['path']]
            # Process focus keyword
            focus = False
            if 'focus' in kwdict:
                if kwdict['focus'] == 'yes':
                    focus = True
                del kwdict['focus']
            # Parse arguments
            _type = arglist[4]
            try:
                col = int(arglist[0])
                row = int(arglist[1])
                colspan = int(arglist[2])
                rowspan = int(arglist[3])
            except (ValueError, TypeError):
                raise InvalidValue('In a form widget col, row, colspan, and '
                                   'rowspan should be integer')
            # Create the widget and add it to the form
            try:
                cls = getattr(widgets, _type)
            except AttributeError:
                raise InvalidFormScript(f'{_type} is not a valid form widget')
            _w = cls(self._form, **kwdict)
            self._form.set_widget(_w, (col, row), colspan=colspan,
                                  rowspan=rowspan)
            # Add as focus widget
            if focus:
                if self.focus_widget is not None:
                    raise InvalidFormScript(
                        'You can only specify one focus widget')
                self.focus_widget = _w

    def var_info(self):
        return super().var_info() + \
            [(var, '[Response variable]') for var in self._variables]
