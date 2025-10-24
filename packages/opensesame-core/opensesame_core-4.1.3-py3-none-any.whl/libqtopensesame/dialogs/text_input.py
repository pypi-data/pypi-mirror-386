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
from libqtopensesame.dialogs.base_dialog import BaseDialog


class TextInput(BaseDialog):

    r"""A simple text-input dialog."""
    def __init__(self, main_window, msg=None, content=u'', validator=None):
        r"""Constructor.

        Parameters
        ----------
        main_window
            The main window object.
        msg
            A text message.
        content, optional
            The starting content.
        validator, optional
            A function to validate the input. This function should take a
            single str as argument, and return a bool.
        """
        super().__init__(main_window, ui=u'dialogs.text_input_dialog')
        if msg is not None:
            self.ui.label_message.setText(msg)
        self._validator = validator
        self.ui.textedit_input.setPlainText(content)
        self.adjustSize()

    def get_input(self):
        r"""Gets text input.

        Returns
        -------
        A string with text input or None of the dialog was not accepted.
        """
        while True:
            if self.exec_() != QtWidgets.QDialog.Accepted:
                break
            s = self.ui.textedit_input.toPlainText()
            if self._validator is None or self._validator(s):
                return s
        return None


# Alias for backwards compatibility
text_input = TextInput
