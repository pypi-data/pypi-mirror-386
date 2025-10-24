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
from libopensesame.item_store import ItemStore
from libqtopensesame.misc.translate import translation_context
from libopensesame.oslogging import oslogger
from libopensesame.exceptions import ItemTypeDoesNotExist
_ = translation_context(u'qtitem_store', category=u'core')


class QtItemStore(ItemStore):
    """The GUI counterpart of the item store, which also distributes item
    changes etc.
    """
    @property
    def main_window(self):
        return self.experiment.main_window

    @property
    def itemtree(self):
        return self.experiment.main_window.itemtree

    @property
    def extension_manager(self):
        return self.main_window.extension_manager
    
    @property
    def plugin_manager(self):
        return self.experiment._plugin_manager

    @property
    def tabwidget(self):
        return self.main_window.tabwidget

    def __delitem__(self, name):
        """Deletes an item, and notifies other items of the deletion.

        Parameters
        ----------
        name : str, unicode
            The name of the item to be deleted.
        """
        self.extension_manager.fire(u'prepare_delete_item', name=name)
        # Temporarily disable build_item_tree to avoid recursively calling it,
        # which can take a long time when experiments are big. This is an ugly
        # hack that doesn't fix the recursion issue as such.
        fnc = self.experiment.build_item_tree
        self.experiment.build_item_tree = lambda: None
        del self.__items__[name]
        for _name in self:
            self[_name].remove_child_item(name, index=-1)
        self.experiment.build_item_tree = fnc
        self.experiment.build_item_tree()
        self.extension_manager.fire(u'delete_item', name=name)

    def new(self, _type, name=None, script=None, allow_rename=True):
        try:
            item = super(qtitem_store, self).new(
                _type=_type,
                name=name,
                script=script,
                allow_rename=allow_rename)
        except ModuleNotFoundError:
            item = super(qtitem_store, self).new(
                _type='missing_item',
                name=name,
                script=script,
                allow_rename=allow_rename)
        self.main_window.set_unsaved(True)
        return item

    def rename(self, from_name, to_name):
        """Renames an item and updates the interface. This function may show a
        notification dialog.

        Parameters
        ----------
        from_name : unicode
            The old item name.
        to_name : unicode
            The desired new item name.

        Returns
        -------
        NoneType, unicode
            The new name of the item, if renaming was successful, None
            otherwise.
        """
        if from_name not in self:
            self.notify(_(u'Item "%s" doesn\'t exist' % from_name))
            return None
        if from_name == to_name:
            return None
        to_name = self.valid_name(
            self[from_name].item_type, suggestion=to_name)
        if to_name in self:
            self.notify(
                _(u'An item with that name already exists.'))
            return None
        if to_name == u'':
            self.notify(_(u'An item name cannot be empty.'))
            return None
        self.extension_manager.fire(u'prepare_rename_item',
                                    from_name=from_name, to_name=to_name)
        # Copy the item in the __items__dictionary
        self.__items__[to_name] = self.__items__[from_name]
        del self.__items__[from_name]
        # Give all items a chance to update
        for item in self.values():
            item.rename(from_name, to_name)
        self.experiment.rename(from_name, to_name)
        self.itemtree.rename(from_name, to_name)
        self.main_window.set_unsaved(True)
        self.extension_manager.fire(u'rename_item', from_name=from_name,
                                    to_name=to_name)
        return to_name

    def set_icon(self, name, icon):
        """Changes an item's icon.

        Parameters
        ----------
        name : unicode
            The item name.
        icon : unicode
            The icon name.
        """
        self.itemtree.set_icon(name, icon)

    def used(self):
        """
        returns:
            desc: A list of used item names.
            type: list
        """
        if self.experiment.var.start not in self:
            return []
        return [self.experiment.var.start] + \
                self[self.experiment.var.start].children()

    def unused(self):
        """
        returns:
            desc: A list of unused item names.
            type: list
        """
        _used = self.used()
        return list(filter(lambda item: item not in _used,
                           self.__items__.keys()))

    def valid_type(self, _type):
        """
        arguments:
            _type:
                desc: The item type to check.
                type: str

        returns:
            desc: True if _type is a valid type, False otherwise.
            type: bool
        """
        return _type in self.built_in_types or _type in self.plugin_manager

    def clear_cache(self):
        """Clears the cache, currently only the cache with children for each
        item.
        """
        for item in self.values():
            item._children = None

    def is_supported(self, _type):
        supported = self.extension_manager.provide(
            'item_supported', experiment=self.experiment, item_type=_type)
        if supported is not None:
            return supported
        if _type in self.plugin_manager:
            return self.plugin_manager[_type].supports(self.experiment)
        return True

# Alias for backwards compatibility
qtitem_store = QtItemStore
