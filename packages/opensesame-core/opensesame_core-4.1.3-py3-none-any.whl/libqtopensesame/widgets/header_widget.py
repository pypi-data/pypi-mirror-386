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
from qtpy import QtCore, QtWidgets
from libqtopensesame.widgets.base_widget import BaseWidget
from libqtopensesame.misc.item_name_delegate import ItemNameEditor
from libqtopensesame.misc.translate import translation_context
_ = translation_context('header_widget', category='core')


MAX_NAME_LENGTH = 30


class HeaderWidget(BaseWidget):
    """Editable labels for an item's name and description.
    
    Parameters
    ----------
    item
        QtItem
    """
    def __init__(self, item):
        super().__init__(item.main_window)
        self.setCursor(QtCore.Qt.IBeamCursor)
        self.setToolTip(_("Click to edit"))
        self.item = item
        self.label_name = QtWidgets.QLabel()
        self.label_name.setObjectName('item_name')
        self.label_name.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                      QtWidgets.QSizePolicy.Fixed)
        self.label_type = QtWidgets.QLabel()
        self.label_type.setObjectName('item_type')
        self.edit_name = ItemNameEditor()
        self.edit_name.editingFinished.connect(self.apply_name)
        self.edit_name.hide()
        self.label_desc = QtWidgets.QLabel()
        self.label_desc.setObjectName('item_desc')
        self.label_desc.setWordWrap(True)
        self.edit_desc = QtWidgets.QLineEdit()
        self.edit_desc.editingFinished.connect(self.apply_desc)
        self.edit_desc.hide()

        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)
        hbox.addWidget(self.label_name)
        hbox.addWidget(self.label_type)
        name_type = QtWidgets.QWidget()
        name_type.setLayout(hbox)
        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(name_type)
        vbox.addWidget(self.edit_name)
        vbox.addWidget(self.label_desc)
        vbox.addWidget(self.edit_desc)
        self.refresh()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Fixed)
        self.setLayout(vbox)

    def refresh(self):
        """Updates the header so that it's content match the item."""
        self.set_name(self.item.name)
        self.set_desc(self.item.var.description)

    def set_name(self, name, label_type=None):
        """Sets the name.

        Parameters
        ----------
        name: str
        label_type: str or None, optional
        """
        self.label_name.setText(
            name if len(name) < MAX_NAME_LENGTH
            else name[:MAX_NAME_LENGTH - 1] + '…')
        self.label_type.setText(
            ' — ' + label_type if label_type is not None
            else ' — ' + self.item.item_type.replace("_", " "))
        self.edit_name.setText(name)

    def set_desc(self, desc):
        """Sets the description.

        Parameters
        ----------
        name
            A description.
        type
            unicode
        """
        self.edit_desc.setText(safe_decode(desc))
        self.label_desc.setText(safe_decode(desc))

    def apply_name(self):
        """Applies the name change and revert the edit control back to the
        static label.
        """
        if self.label_name.isVisible():
            return
        self.label_name.show()
        self.label_type.show()
        self.edit_name.hide()
        self.item_store.rename(self.item.name, self.edit_name.text())

    def apply_desc(self):
        """Applies the description change and revert the edit back to the
        label.
        """
        if self.label_desc.isVisible():
            return
        description = self.edit_desc.text()
        description = self.item.syntax.sanitize(description)
        self.item.var.description = description
        self.label_desc.setText(description)
        self.label_desc.show()
        self.edit_desc.hide()
        self.item.apply_edit_changes()

    def mousePressEvent(self, event):
        """
        Change the label into an edit for the name or
        the description, depending on where has been
        clicked

        Arguments:
        event -- the mouseClickEvent
        """
        target = self.childAt(event.pos())
        if target == self.label_name:
            self.apply_desc()
            self.label_name.hide()
            self.label_type.hide()
            self.edit_name.show()
            self.edit_name.selectAll()
            self.edit_name.setFocus()
        elif target == self.label_desc:
            self.apply_name()
            self.label_desc.hide()
            self.edit_desc.show()
            self.edit_desc.selectAll()
            self.edit_desc.setFocus()


# Alias for backwards compatibility
header_widget = HeaderWidget
