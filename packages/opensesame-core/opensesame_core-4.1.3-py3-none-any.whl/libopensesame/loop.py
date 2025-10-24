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
import os
from libopensesame.oslogging import oslogger
from libopensesame.exceptions import InvalidOpenSesameScript, OSException, \
    ItemDoesNotExist, LoopSourceFileDoesNotExist, UnsupportedLoopSourceFile, \
    InvalidConditionalExpression, PythonError, InvalidValue, \
    ConditionalExpressionError
from libopensesame.item import Item
from datamatrix import operations, DataMatrix, functional
from pseudorandom import Enforce, MaxRep, MinDist
from openexp.keyboard import Keyboard


class Loop(Item):
    """A loop item runs a single other item multiple times"""
    
    description = u'Repeatedly runs another item'
    valid_orders = u'sequential', u'random'
    commands = [
        u'fullfactorial',
        u'shuffle',
        u'shuffle_horiz',
        u'slice',
        u'sort',
        u'sortby',
        u'reverse',
        u'roll',
        u'weight',
    ]

    def reset(self):
        """See item."""
        self.ef = None
        self.dm = DataMatrix(length=0)
        self.dm.sorted = False
        self.live_dm = None
        self.live_row = None
        self._operations = []
        self._constraints = []
        self._item = u''

        self.var.repeat = 1
        self.var.continuous = u'no'
        self.var.order = u'random'
        self.var.break_if = u'never'
        self.var.break_if_on_first = u'yes'
        self.var.source = u'table'  # file or table
        self.var.source_file = u''

    def from_string(self, string):
        """See item."""
        self.var.clear()
        self.comments = []
        self.reset()
        if string is None:
            return
        for i in string.split(u'\n'):
            self.parse_variable(i)
            cmd, arglist, kwdict = self.syntax.parse_cmd(i)
            if cmd == u'run':
                if len(arglist) != 1 or kwdict:
                    raise InvalidOpenSesameScript('Invalid run command', 
                                                  line=i)
                self._item = arglist[0]
                continue
            if cmd == u'setcycle':
                if self.ef is not None or self._operations:
                    raise InvalidOpenSesameScript(
                        'setcycle must come before constraints and operations',
                        line=i)
                if len(arglist) != 3 or kwdict:
                    raise InvalidOpenSesameScript(
                        'Invalid setcycle command', line=i)
                row, var, val = tuple(arglist)
                if row >= len(self.dm):
                    self.dm.length = row + 1
                if var not in self.dm:
                    self.dm[var] = u''
                self.dm[row][var] = val
                continue
            if cmd == u'constrain':
                if self._operations:
                    raise InvalidOpenSesameScript(
                        'constraints must come before operations', line=i)
                if len(arglist) != 1:
                    raise InvalidOpenSesameScript(
                        'Invalid constrain command', line=i)
                colname = arglist[0]
                for constraint, value in kwdict.items():
                    if constraint == u'maxrep':
                        constraint_cls = MaxRep
                        kwargs = {u'maxrep': value}
                    elif constraint == u'mindist':
                        constraint_cls = MinDist
                        kwargs = {u'mindist': value}
                    else:
                        raise InvalidOpenSesameScript(
                            'Unknown constraint', line=i)
                    self._constraints.append((
                        constraint_cls,
                        colname,
                        kwargs
                    ))
                continue
            if cmd in self.commands:
                self._operations.append((cmd, arglist))
        if len(self.dm) == 0:
            self.dm.length = 1
        if len(self.dm.columns) == 0:
            self.dm.empty_column = u''
        # Backwards compatibility: Older version of OpenSesame can specify the
        # number of cycles through the cycles variable. If the specified number
        # of cycles doesn't match the length of the datamatrix, we change the
        # length of the datamatrix.
        if u'cycles' in self.var and isinstance(self.var.cycles, int) \
                and self.var.cycles != len(self.dm):
            self.dm.length = self.var.cycles

    def to_string(self):
        """See item."""
        # Older versions of OpenSesame use an explicit cycles variable, so we
        # set this here for backwards compatibility.
        self.var.cycles = len(self.dm)
        s = super().to_string()
        for i, row in enumerate(self.dm):
            for name, val in row:
                s += u'\t%s\n' % \
                    self.syntax.create_cmd(u'setcycle', [i, name, val])
        for constraint_cls, colname, kwargs in self._constraints:
            s += u'\t%s\n' % self.syntax.create_cmd(
                u'constrain', [colname], kwargs
            )
        for cmd, arglist in self._operations:
            s += u'\t%s\n' % self.syntax.create_cmd(cmd, arglist)
        s += u'\t%s\n' % self.syntax.create_cmd(u'run', [self._item])
        return s

    def _require_arglist(self, cmd, arglist, minlen=1):
        r"""Checks whether a non-empty argument list has been specified, and
        raises an Exception otherwise.

        Parameters
        ----------
        cmd : str
            The command to check for.
        arglist : list
            The argument list to check.
        """
        if len(arglist) < minlen:
            raise InvalidOpenSesameScript(
                f'Invalid argument list for {cmd}')

    def _create_live_datamatrix(self):
        r"""Builds a live DataMatrix. That is, it takes the original DataMatrix
        and applies all the operations as specified.

        Returns
        -------
        DataMatrix
            A live DataMatrix.
        """
        src_dm = self.dm if self.var.source == u'table' else self._read_file()
        for column_name in src_dm.column_names:
            if not self.syntax.valid_var_name(column_name):
                raise InvalidOpenSesameScript(
                    f'The loop table contains an invalid column name: '
                    f'"{column_name}"')
        # The number of repeats should be numeric. If not, then give an error.
        # This can also occur when generating a preview of a loop table if
        # repeat is variable.
        if not isinstance(self.var.repeat, (int, float)):
            raise InvalidValue(
                f'repeat should be numeric, not {self.var.repeat}')
        length = int(len(src_dm) * self.var.repeat)
        dm = DataMatrix(length=0)
        while len(dm) < length:
            i = min(length-len(dm), len(src_dm))
            if self.var.order == u'random':
                dm <<= operations.shuffle(src_dm)[:i]
            else:
                dm <<= src_dm[:i]
        # An empty loop table is not an error, but we should return an empty
        # DataMatrix and warn the user because it may indicate a mistake.
        if len(dm) == 0:
            oslogger.warning('loop table is empty')
            return dm
        if self.var.order == u'random':
            dm = operations.shuffle(dm)
        # Constraints come before loop operations
        if self._constraints:
            self.ef = Enforce(dm)
            for constraint_cls, colname, kwargs in self._constraints:
                colname = self.syntax.auto_type(self.syntax.eval_text(colname))
                kwargs = {
                    key: self.syntax.auto_type(self.syntax.eval_text(val))
                    for key, val in kwargs.items()
                }
                try:
                    cols = dm[colname]
                except AttributeError:
                    raise InvalidOpenSesameScript(
                        f'Column {colname} does not exist')
                self.ef.add_constraint(
                    constraint_cls, cols=cols, **kwargs
                )
            dm = self.ef.enforce()
        # Operations come last
        for cmd, arglist in self._operations:
            arglist = [
                self.syntax.auto_type(self.syntax.eval_text(arg))
                for arg in arglist
            ]
            # The column name is always specified last, or not at all
            if arglist:
                try:
                    colname = arglist[-1]
                    if not isinstance(colname, int):
                        col = dm[colname]
                except (IndexError, AttributeError):
                    raise InvalidOpenSesameScript(
                        f'Column {arglist[-1]} does not exist')
            if cmd == u'fullfactorial':
                try:
                    dm = operations.fullfactorial(dm)
                except MemoryError:
                    raise OSException(u'DataMatrix too large for fullfact')
            elif cmd == u'shuffle':
                if not arglist:
                    dm = operations.shuffle(dm)
                else:
                    dm[colname] = operations.shuffle(col)
            elif cmd == u'shuffle_horiz':
                if not arglist:
                    dm = operations.shuffle_horiz(dm)
                else:
                    # There can be multiple column names, so we need to check
                    # if all of them exist, rather than only the last one as
                    # we did above.
                    for _colname in arglist:
                        try:
                            dm[_colname]
                        except AttributeError:
                            raise InvalidOpenSesameScript(
                                f'Column {_colname} does not exist')
                    dm = operations.shuffle_horiz(
                        *[dm[_colname] for _colname in arglist]
                    )
            elif cmd == u'slice':
                self._require_arglist(cmd, arglist, minlen=2)
                dm = dm[arglist[0]: arglist[1]]
            elif cmd == u'sort':
                self._require_arglist(cmd, arglist)
                dm[colname] = operations.sort(col)
            elif cmd == u'sortby':
                self._require_arglist(cmd, arglist)
                dm = operations.sort(dm, by=col)
            elif cmd == u'reverse':
                if not arglist:
                    dm = dm[::-1]
                else:
                    dm[colname] = col[::-1]
            elif cmd == u'roll':
                self._require_arglist(cmd, arglist)
                steps = arglist[0]
                if not isinstance(steps, int):
                    raise InvalidValue('roll steps should be numeric')
                if len(arglist) == 1:
                    dm = dm[-steps:] << dm[:-steps]
                else:
                    dm[colname] = list(col[-steps:]) + list(col[:-steps])
            elif cmd == u'weight':
                self._require_arglist(cmd, arglist)
                # Evaluate the weights before passing them to the weight
                # function, so that weights can be defined in terms of
                # variables.
                ecol = functional.map_(
                    lambda w: self.syntax.auto_type(self.syntax.eval_text(w)),
                    col
                )
                try:
                    dm = operations.weight(ecol)
                except TypeError:
                    raise InvalidValue(
                        'weight values should be non-negative numeric values')
        return dm

    def prepare(self):
        """See item."""
        super().prepare()
        # Compile break-if statement
        break_if = self.var.get(u'break_if', _eval=False)
        if break_if not in (u'never', u''):
            self._break_if = self.syntax.compile_cond(break_if)
        else:
            self._break_if = None
        # Create a keyboard to flush responses between cycles
        self._keyboard = Keyboard(self.experiment)
        # Make sure the item to run exists
        if self._item not in self.experiment.items:
            raise ItemDoesNotExist(self._item)

    def run(self):
        self.set_item_onset()
        if self.live_dm is None or self.var.continuous == u'no':
            self.live_dm = self._create_live_datamatrix()
            self.live_row = 0
        first = True
        while self.live_row < len(self.live_dm):
            self.experiment.var.repeat_cycle = 0
            self.experiment.var.live_row = self.live_row
            self.experiment.var.set('live_row_%s' % self.name, self.live_row)
            for name, val in self.live_dm[self.live_row]:
                # For backwards compatibility, values prefixed by '=' are
                # interpreted as Python code. We rewrite this to f-string
                # notation
                if isinstance(val, str) and val.startswith('='):
                    val = f'{val[1:]}'
                try:
                    val = self.syntax.auto_type(val,
                                                allow_bool=True,
                                                allow_none=True)
                except Exception as e:
                    oslogger.warning(f'loop variable {name} has unusual type')
                self.experiment.var.set(name, self.syntax.eval_text(val))
            # Evaluate the run if statement
            if (
                    self._break_if is not None and
                    (not first or self.var.break_if_on_first == u'yes')
            ):
                self.python_workspace[u'self'] = self
                try:
                    if self.python_workspace._eval(self._break_if):
                        break
                except Exception as e:
                    raise ConditionalExpressionError(
                        'Error evaluating break-if expression')
            # Run the item!
            self.experiment.items.execute(self._item)
            # If the repeat_cycle flag was set, run the item again later
            if self.experiment.var.repeat_cycle:
                self.live_dm <<= self.live_dm[self.live_row:self.live_row+1]
                if self.var.order == u'random':
                    self.live_dm = self.live_dm[:self.live_row+1] \
                        << operations.shuffle(self.live_dm[self.live_row+1:])
            self.live_row += 1
            first = False
        else:
            # If the loop finished without breaking, it needs to be reset on
            # the next run of the loop item
            self.live_row = None
            self.live_dm = None

    def _read_file(self):
        r"""Reads a source file and raises an exception if this fails.

        Returns
        -------
        DataMatrix
        """
        from datamatrix import io
        src = self.experiment.pool[self.var.source_file]
        if not os.path.exists(src):
            raise LoopSourceFileDoesNotExist(self.var.source_file)
        if src.endswith(u'.xlsx'):
            try:
                return io.readxlsx(src)
            except Exception as e:
                raise UnsupportedLoopSourceFile(
                    f'Failed to read .xlsx file: {src}')
        try:
            return io.readtxt(src)
        except Exception as e:
            raise UnsupportedLoopSourceFile(
                f'Failed to read text file: {src}. Perhaps it has the wrong '
                f'format or it is not utf-8 encoded')

    def _var_info_table(self):
        """
        returns:
                A list of (var, value) tuples that have been defined in the loop
                table.
        """
        return [(colname, safe_decode(col)) for colname, col in self.dm.columns]

    def _var_info_file(self):
        """
        returns:
                A list of (var, value) tuples that have been defined in a source
                file.
        """
        try:
            dm = self._read_file()
        except Exception:
            return []
        return [(colname, safe_decode(col)) for colname, col in dm.columns]

    def var_info(self):
        """See item."""
        return super().var_info() + (
            self._var_info_table()
            if self.var.source == u'table'
            else self._var_info_file()
        )


# Alias for backwards compatibility
loop = Loop
