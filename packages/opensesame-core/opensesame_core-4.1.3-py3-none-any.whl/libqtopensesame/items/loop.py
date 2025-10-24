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
from qdatamatrix import QDataMatrix
from pseudorandom import EnforceFailed
from libopensesame.loop import Loop as LoopRuntime
from libopensesame.exceptions import OSException
from libqtopensesame.items.qtitem import QtItem
from libqtopensesame.items.qtstructure_item import QtStructureItem
from libqtopensesame.widgets.loop_widget import LoopWidget
from libqtopensesame.widgets.tree_item_item import TreeItemItem
from libqtopensesame.misc.translate import translation_context
import math
_ = translation_context(u'loop', category=u'item')


class Loop(QtStructureItem, QtItem, LoopRuntime):

    """The GUI for the loop item"""
    description = _(u'Repeatedly runs another item')
    help_url = u'manual/structure/loop'
    lazy_init = True

    def __init__(self, name, experiment, string=None):
        """See QtItem."""
        self.lock_cycles = False
        LoopRuntime.__init__(self, name, experiment, string)
        QtStructureItem.__init__(self)
        QtItem.__init__(self)

    def init_edit_widget(self):
        """Builds the loop controls."""
        super().init_edit_widget(stretch=False)
        self.loop_widget = LoopWidget(self.experiment.main_window)
        self.qdm = QDataMatrix(self.dm)
        self.qdm.changed.connect(self._apply_table)
        self.qdm.cellchanged.connect(self._on_cell_changed)
        self.edit_vbox.addWidget(self.loop_widget)
        self.edit_vbox.addWidget(self.qdm)
        self.set_focus_widget(self.qdm)
        self.auto_add_widget(self.loop_widget.ui.spinbox_repeat, u'repeat')
        self.auto_add_widget(self.loop_widget.ui.combobox_order, u'order')
        self.auto_add_widget(self.loop_widget.ui.combobox_source, u'source',
                             apply_func=self._apply_source)
        self.auto_add_widget(
            self.loop_widget.ui.edit_source_file, u'source_file')
        self.loop_widget.ui.edit_break_if.verb = 'break'
        self.auto_add_widget(self.loop_widget.ui.edit_break_if, u'break_if')
        self.auto_add_widget(self.loop_widget.ui.checkbox_break_if_on_first,
                             u'break_if_on_first')
        self.auto_add_widget(self.loop_widget.ui.checkbox_continuous,
                             u'continuous')
        self.loop_widget.ui.combobox_item.activated.connect(self._apply_item)
        self.loop_widget.ui.button_preview.clicked.connect(self._show_preview)
        self.loop_widget.ui.button_wizard.clicked.connect(self._show_wizard)

    def _show_wizard(self):
        r"""Shows the full-factorial-design wizard."""
        from libqtopensesame.dialogs.loop_wizard import loop_wizard
        d = loop_wizard(self.main_window)
        dm = d.exec_()
        if dm is None:
            return
        dm.sorted = False
        self.dm = dm
        self.update()

    def _show_preview(self):
        r"""Shows a preview tab for the loop table."""
        l = [_(u'# Preview of loop table'), u'\n\n']
        try:
            dm = self._create_live_datamatrix()
        except (OSException, EnforceFailed) as e:
            l.append(_(u'Failed to generate preview.'))
            l.append(u'\n~~~ .python\n%s\n~~~' % e)
        else:
            l.append(u'\n\n<table><thead><tr>')
            l.append(u''.join([u'<th>%s</th>' % column_name
                               for column_name in dm.column_names]))
            l.append(u'</tr></thead><tbody>')
            for row in dm:
                l.append(u'<tr>'
                         + u''.join([u'<th>%s</th>' %
                                    val for name, val in row])
                         + u'</tr>')
            l.append(u'</tbody></table>')
        md = u'\n'.join(l)
        self.tabwidget.open_markdown(
            md, title=u'Loop preview', icon=u'os-loop')

    @QtStructureItem.clears_children_cache
    def _apply_item(self, *args):
        r"""Applies changes to the item combobox.

        Parameters
        ----------
        *args : list
            Dummy arguments passed by the signal-slot system.
        """
        self._item = self.loop_widget.ui.combobox_item.selected_item
        self.experiment.build_item_tree()
        self.update_script()

    def _update_item(self):
        r"""Updates the item combobox."""
        self.loop_widget.ui.combobox_item.select(self._item)

    def _on_cell_changed(self, rownr, colnr):
        r"""Protects the table from having newlines in the cells."""
        if rownr == 0:
            return
        col = self.qdm.dm.columns[colnr][1]
        val = self.qdm.dm[col][rownr - 1]
        if not isinstance(val, str) or u'\n' not in val:
            return
        val = val.replace(u'\n', u'')
        self.qdm._spreadsheet._setcell(rownr, colnr, val)
        self.qdm.dm[col][rownr - 1] = val
        self._apply_table()

    def _apply_table(self):
        r"""Applies changes to the loop table."""
        # QDataMatrix can create a new datamatrix object, and that's the one we
        # have to use.
        self.dm = self.qdm.dm
        if not self.dm:
            self.dm.length = 1
            self.qdm.refresh()
        if not self.dm.columns:
            self.dm.empty_column = u''
            self.qdm.refresh()
        self.update_script()
        self._warn_empty_rows()

    def _apply_source(self):
        r"""Applies changes to the source selector, if a file source is
        selected.
        """
        self.var.source = self.loop_widget.ui.combobox_source.currentText()
        self._update_source()
        self.update_script()

    def _update_source(self):
        r"""Update the file-source selector, hiding it when the loop table is
        used as source.
        """
        file_mode = self.var.get(u'source', _eval=False) != u'table'
        self.loop_widget.ui.label_source_file.setVisible(file_mode)
        self.loop_widget.ui.edit_source_file.setVisible(file_mode)
        self.loop_widget.ui.spacer.setVisible(file_mode)
        self.qdm.setVisible(not file_mode)

    def _row_count_text(self, n):
        r"""A descriptive text for the number of rows.

        Parameters
        ----------
        n
            The number of rows.

        Returns
        -------
        A descriptive text.
        """
        if n == 1:
            return _(u'one row occurs')
        if n == 2:
            return _(u'two rows occur')
        return _(u'%s rows occur' % n)

    def _time_count_text(self, n):
        r"""A descriptive text for the number of times an item is executed.

        Parameters
        ----------
        n
            The number of times.

        Returns
        -------
        A descriptive text.
        """
        if n == 0:
            return _(u'never')
        if n == 1:
            return _(u'once')
        if n == 2:
            return _(u'twice')
        return _(u'%s times' % n)

    def _set_summary(self, msg):
        r"""Sets the summary label.

        Parameters
        ----------
        msg
            The summary message.
        """
        self.loop_widget.ui.label_summary.setText(msg)

    def _update_summary(self):
        r"""Generates a loop summary and sets the summary label."""
        if self._item not in self.experiment.items:
            self._set_summary(_(u'Warning: No item to run has been specified'))
            return
        repeat = self.var.get(u'repeat', _eval=False)
        order = self.var.get(u'order', _eval=False)
        if not isinstance(repeat, (float, int)) \
                or order not in self.valid_orders:
            self._set_summary(
                _(u'Note: Order or repeat is unknown or variably defined'))
            return
        if self.var.get(u'source', _eval=False) != u'table':
            self._set_summary(
                _(u'Note: Loop data will be read from file'))
            return

        f, i = math.modf(repeat)
        length = int(repeat*len(self.dm))
        numrows = len(self.dm)
        r_freq = int(i+1)
        n_freq = int(f * numrows)
        r_rare = int(i)
        n_rare = numrows - n_freq
        s = _(u'Summary: <b>%s</b> will be called <b>%s</b> in <b>%s</b> order.') \
            % (self._item, self._time_count_text(length), order)
        s += u' ' + _(u'The number of rows is %s.') % numrows
        if n_freq == 0:
            s += u' ' + \
                _(u'All rows occur %s.') % self._time_count_text(r_rare)
        elif n_rare == 0:
            s += u' ' + \
                _(u'All rows occur %s.') % self._time_count_text(r_freq)
        else:
            s += u' ' + _(u'This means that %s %s and %s %s.') \
                % (self._row_count_text(n_freq),
                   self._time_count_text(r_freq),
                   self._row_count_text(n_rare),
                   self._time_count_text(r_rare))
        self._set_summary(s)

    def _warn_empty_rows(self):
        r"""Gives a notification when the loop table has more than 1 rows and
        the last row is empty. This generally happens if the user has forgotten
        to truncate the loop table when clearing rows at the end.
        """
        if len(self.qdm.dm) > 1 and all(
                cell == u'' for name, cell in self.qdm.dm[-1]
        ):
            self.extension_manager.fire(
                u'notify',
                message=u'The loop table has empty rows at the end'
            )

    def edit_widget(self):
        """See QtItem."""
        super().edit_widget()
        self.loop_widget.ui.combobox_item.filter_fnc = (
            lambda item: item not in self.parents()
        )
        self.loop_widget.ui.combobox_item.refresh()
        self.loop_widget.ui.combobox_item.select(self._item)
        self.qdm.dm = self.dm
        self.qdm.refresh()
        self._update_summary()
        self._update_item()
        self._update_source()
        self._warn_empty_rows()

    def update_script(self, use_cache=True):
        """See QtItem."""
        super().update_script(use_cache=use_cache)
        self._update_summary()

    def build_item_tree(self, toplevel=None, items=[], max_depth=-1,
                        extra_info=None):
        """See QtItem."""
        items.append(self.name)
        widget = TreeItemItem(self, extra_info=extra_info)
        if toplevel is not None:
            toplevel.addChild(widget)
        if (max_depth < 0 or max_depth > 1) \
                and self._item in self.experiment.items:
            self.experiment.items[self._item].build_item_tree(widget, items,
                max_depth=max_depth-1)
        return widget

    @QtStructureItem.cached_children
    def children(self):
        """See QtItem."""
        if self._item not in self.experiment.items:
            return []
        return [self._item] + self.experiment.items[self._item].children()

    def direct_children(self):

        return [self._item] if self._item in self.experiment.items else []

    def is_child_item(self, item):
        """See QtItem."""
        return self._item == item or (self._item in self.experiment.items and
                                      self.experiment.items[self._item].is_child_item(item))

    @QtStructureItem.clears_children_cache
    def insert_child_item(self, item_name, index=0):
        """See QtItem."""
        self._item = item_name
        self.update()
        self.main_window.set_unsaved(True)

    @QtStructureItem.clears_children_cache
    def remove_child_item(self, item_name, index=0):
        """See QtItem."""
        if item_name == self._item:
            self._item = u''
        if not self.update():
            self.extension_manager.fire(u'change_item', name=self.name)
        self.main_window.set_unsaved(True)

    @QtStructureItem.clears_children_cache
    def rename(self, from_name, to_name):
        """See QtItem."""
        super().rename(from_name, to_name)
        if self._item == from_name:
            self._item = to_name

    @QtStructureItem.clears_children_cache
    def delete(self, item_name, item_parent=None, index=None):
        """See QtItem."""
        if self._item == item_name and item_parent == self.name:
            self._item = u''


# Alias for backwards compatibility
loop = Loop
