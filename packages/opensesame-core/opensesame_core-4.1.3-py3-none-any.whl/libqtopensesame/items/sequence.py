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
from qtpy import QtWidgets
from libopensesame.sequence import Sequence as SequenceRuntime
from libqtopensesame.widgets.tree_item_item import TreeItemItem
from libqtopensesame.widgets.tree_overview import TreeOverview
from libqtopensesame.items.qtitem import requires_init
from libqtopensesame.items.qtplugin import QtPlugin
from libqtopensesame.items.qtstructure_item import QtStructureItem
from libqtopensesame.misc.translate import translation_context
_ = translation_context(u'sequence', category=u'item')


class Sequence(QtStructureItem, QtPlugin, SequenceRuntime):
    """GUI controls for the sequence item.
    
    Parameters
    ----------
    name
        The item name.
    experiment
        The experiment object.
    string, optional
        A definition string.
    """
    
    description = _(u'Runs a number of items in sequence')
    help_url = u'manual/structure/sequence'
    lazy_init = True

    def __init__(self, name, experiment, string=None):
        SequenceRuntime.__init__(self, name, experiment, string)
        QtStructureItem.__init__(self)
        QtPlugin.__init__(self)
        self.last_removed_child = None, None

    def init_edit_widget(self):
        super().init_edit_widget(False)
        self.checkbox_flush_keyboard = QtWidgets.QCheckBox(
            _(u'Flush pending key presses at sequence start'))
        self.checkbox_flush_keyboard.setToolTip(
            _(u'Flush pending key presses at sequence start'))
        self.auto_add_widget(self.checkbox_flush_keyboard,
                             var=u'flush_keyboard')
        self.edit_vbox.addWidget(self.checkbox_flush_keyboard)
        self.treewidget = TreeOverview(self.main_window, overview_mode=False)
        self.treewidget.setup(self.main_window)
        self.treewidget.structure_change.connect(self.update)
        self.treewidget.text_change.connect(self.update_script)
        self.set_focus_widget(self.treewidget)
        self.edit_vbox.addWidget(self.treewidget)
        self.add_text(
            _(u'<b>Important</b>: A sequence has <a href="http://osdoc.cogsci.nl/usage/prepare-run">a variable preparation time</a>.'))

    def edit_widget(self):
        super().edit_widget()
        if self.treewidget.locked:
            return
        for item, cond, enabled in self.items:
            if item not in self.experiment.items:
                self.extension_manager.fire(
                    u'notify',
                    message=_(u'Sequence contains non-existing item: %s') % item,
                    category=u'warning')
        self.treewidget.clear()
        self.toplevel_treeitem = self.build_item_tree(max_depth=2)
        self.treewidget.addTopLevelItem(self.toplevel_treeitem)
        self.toplevel_treeitem.setExpanded(True)
        self.treewidget.resizeColumnToContents(0)
        self.treewidget.append_button.set_position()

    @requires_init
    @QtStructureItem.clears_children_cache
    def rename(self, from_name, to_name):
        QtPlugin.rename(self, from_name, to_name)
        new_items = []
        for item, cond, enabled in self.items:
            if item == from_name:
                new_items.append((to_name, cond, enabled))
            else:
                new_items.append((item, cond, enabled))
        self.items = new_items
        self.treewidget.rename(from_name, to_name)

    @QtStructureItem.clears_children_cache
    def delete(self, item_name, item_parent=None, index=None):
        if item_parent is None or (item_parent == self.name and index is None):
            while True:
                for i, (child_item_name, child_run_if) in enumerate(self.items):
                    if child_item_name == item_name:
                        self.items = self.items[:i]+self.items[i+1:]
                        break
                else:
                    # Break the while loop if no break occurred in the for loop
                    break
        elif item_parent == self.name and index is not None:
            if self.items[index][0] == item_name:
                self.items = self.items[:index]+self.items[index+1:]

    def build_item_tree(self, toplevel=None, items=[], max_depth=-1,
                        extra_info=None):
        widget = TreeItemItem(self, extra_info=extra_info)
        items.append(self.name)
        if max_depth < 0 or max_depth > 1:
            for item, cond, enabled in self.items:
                if item in self.experiment.items:
                    tree_widget = self.experiment.items[item].build_item_tree(
                        widget, items, max_depth=max_depth-1, extra_info=cond)
                    if not enabled:
                        tree_widget.setDisabled(True)
                        tree_widget.set_extra_info(None)
                    
        if toplevel is not None:
            toplevel.addChild(widget)
        else:
            widget.set_draggable(False)
        return widget

    def set_run_if(self, index, cond=u'always'):
        r"""Sets the run-if statement for an item at a specific index.

        Parameters
        ----------
        index : int
            The index of the item to change the run-if statement of.
        cond : unicode, optional
            The run-if statement.
        """
        self.items[index] = self.items[index][0], cond, self.items[index][2]

    @QtStructureItem.cached_children
    def children(self):
        """See qtitem."""
        self._children = []
        for item, _, _ in self.items:
            if item not in self.experiment.items:
                continue
            self._children += [item] + self.experiment.items[item].children()
        return self._children

    def direct_children(self):
        return [item for item, _, _ in self.items
                if item in self.experiment.items]

    def is_child_item(self, item):
        return item in self.children()

    @QtStructureItem.clears_children_cache
    def insert_child_item(self, item_name, index=0):
        if item_name == self.last_removed_child[0]:
            # If this item was just removed, re-add it and preserve its run-if
            # statement.
            self.items.insert(index, self.last_removed_child)
        else:
            self.items.insert(index, (item_name, 'True', True))
        self.update()
        self.main_window.set_unsaved(True)

    @QtStructureItem.clears_children_cache
    def remove_child_item(self, item_name, index=0):
        if index < 0:
            items = []
            for item, cond, enabled in self.items:
                if item != item_name:
                    items.append((item, cond, enabled))
            self.items = items
        elif len(self.items) > index and self.items[index][0] == item_name:
            # We remember the last removed child item, because we will reuse
            # it's run-if statement if it is re-added.
            self.last_removed_child = self.items[index]
            del self.items[index]
        if not self.update():
            self.extension_manager.fire(u'change_item', name=self.name)
        self.main_window.set_unsaved(True)

    def enable_child_item(self, item_name, index=0, enabled=True):
        # If no index is specified, we set the disabled status of all children
        if index < 0:
            items = []
            for item, cond, _enabled in self.items:
                if item == item_name:
                    _enabled = enabled
                items.append((item, cond, _enabled))
            self.items = items
        elif len(self.items) > index and self.items[index][0] == item_name:
            self.items[index] = item_name, self.items[index][1], enabled
        if not self.update():
            self.extension_manager.fire(u'change_item', name=self.name)
        self.main_window.set_unsaved(True)


# Alias for backwards compatibility
sequence = Sequence
