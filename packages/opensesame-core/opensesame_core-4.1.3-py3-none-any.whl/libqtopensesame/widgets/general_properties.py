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
from libopensesame.oslogging import oslogger
from qtpy import QtWidgets
from libqtopensesame.widgets.general_header_widget import GeneralHeaderWidget
from libqtopensesame.widgets.base_widget import BaseWidget
from libopensesame.exceptions import InvalidColor, MissingDependency
from openexp._color.color import Color
from openexp import backend
from libqtopensesame.misc.translate import translation_context
_ = translation_context(u'general_properties', category=u'core')


class GeneralProperties(BaseWidget):
    """The QWidget for the general properties tab.

    Parameters
    ----------
    main_window
        A qtopensesame object.
    """

    def __init__(self, main_window):
        super().__init__(main_window, ui=u'widgets.general_properties')
        self.lock = False
        # Set the header, with the icon, label and script button
        self.header_widget = GeneralHeaderWidget(self, self.main_window)
        header_hbox = QtWidgets.QHBoxLayout()
        header_hbox.addWidget(self.theme.qlabel(u"experiment"))
        header_hbox.addWidget(self.header_widget)
        header_hbox.addStretch()
        header_hbox.setContentsMargins(0, 0, 0, 0)
        header_hbox.setSpacing(12)
        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(header_hbox)
        self.ui.container_layout.insertWidget(0, header_widget)
        # Initialize the color and font widgets
        self.ui.edit_foreground.initialize(self.experiment)
        self.ui.edit_background.initialize(self.experiment)
        self.ui.widget_font.initialize(self.experiment)
        self.ui.button_reset_backend.clicked.connect(self._reset_backend)
        # Set the backend combobox
        self._backend_button_group = QtWidgets.QButtonGroup()
        for id_, (name, info) in enumerate(backend.backend_info().items()):
            radio_button = QtWidgets.QRadioButton(
                f'{info["description"]} ({name})')
            self._backend_button_group.addButton(radio_button)
            self._backend_button_group.setId(radio_button, id_)
            self.ui.layout_backend_list.addWidget(radio_button)
        self.quick_connect(
            slot=self.main_window.ui.tabwidget.open_general_script,
            signals=[self.ui.button_script_editor.clicked],
        )
        self.quick_connect(
            slot=self.main_window.ui.tabwidget.open_backend_settings,
            signals=[self.ui.button_backend_settings.clicked]
        )
        self.quick_connect(
            slot=self.apply_changes,
            signals=[
                self.ui.spinbox_width.editingFinished,
                self.ui.spinbox_height.editingFinished,
                self.ui.checkbox_disable_garbage_collection.stateChanged,
                self.ui.edit_foreground.textEdited,
                self.ui.edit_background.textEdited,
                self.ui.widget_font.font_changed,
                self._backend_button_group.idClicked,
            ])
        self.tab_name = u'__general_properties__'
        self.on_activate = self.refresh

    def set_header_label(self):
        """Sets the general header based on the experiment title and
        description.
        """
        self.header_widget.set_name(self.experiment.var.title)
        self.header_widget.set_desc(self.experiment.var.description)

    def apply_changes(self):
        """Applies changes to the general tab."""
        # Skip if the general tab is locked and lock it otherwise
        if self.lock:
            return
        self.lock = True

        self.main_window.set_busy(True)
        self.main_window.extension_manager.fire(u'prepare_change_experiment')
        # Set the title and the description
        title = self.experiment.syntax.sanitize(
            self.header_widget.edit_name.text())
        if title != self.experiment.var.title:
            self.experiment.var.title = title
            self.experiment.build_item_tree()
        desc = self.experiment.syntax.sanitize(
            self.header_widget.edit_desc.text())
        self.experiment.var.description = desc
        # Set the backend
        if self.ui.widget_backend_list.isEnabled():
            i = self._backend_button_group.checkedId()
            name, info = list(backend.backend_info().items())[i]
            oslogger.info(f'setting backend to {name}')
            self.experiment.var.canvas_backend = info["canvas"]
            self.experiment.var.keyboard_backend = info["keyboard"]
            self.experiment.var.mouse_backend = info["mouse"]
            self.experiment.var.sampler_backend = info["sampler"]
            self.experiment.var.clock_backend = info["clock"]
            self.experiment.var.color_backend = info["color"]
            self.ui.button_backend_settings.setEnabled(info['settings'])
        else:
            oslogger.debug(
                u'not setting back-end, because a custom backend is selected')
            self.ui.button_backend_settings.setEnabled(False)
        # Set the display width
        width = self.ui.spinbox_width.value()
        height = self.ui.spinbox_height.value()
        if self.experiment.var.width != width or \
                self.experiment.var.height != height:
            self.main_window.update_resolution(width, height)
        # Set the foreground color. If there are no variables in the color
        # definition, then we check whether it is a valid color specification.
        # If not, then we revert the change and notify the user.
        foreground = self.experiment.syntax.sanitize(
            self.ui.edit_foreground.text())
        if not self.experiment.syntax.contains_variables(foreground):
            try:
                Color.to_hex(foreground)
            except (InvalidColor, MissingDependency) as e:
                self.notify(f'Invalid color: {e}')
                foreground = self.experiment.var.foreground
        self.ui.edit_foreground.setText(foreground)
        self.experiment.var.foreground = foreground
        # Set the background color
        background = self.experiment.syntax.sanitize(
            self.ui.edit_background.text())
        if not self.experiment.syntax.contains_variables(background):
            try:
                Color.to_hex(background)
            except (InvalidColor, MissingDependency) as e:
                self.notify(f'Invalid color: {e}')
                background = self.experiment.var.background
        self.ui.edit_background.setText(background)
        self.experiment.var.background = background
        # Set the font
        self.experiment.var.font_family = self.ui.widget_font.family
        self.experiment.var.font_size = self.ui.widget_font.size
        self.experiment.var.font_italic = self.ui.widget_font.italic
        self.experiment.var.font_bold = self.ui.widget_font.bold
        # Other checkboxes
        self.experiment.var.disable_garbage_collection = \
            self.ui.checkbox_disable_garbage_collection.isChecked()
        # Refresh the interface and unlock the general tab
        self.lock = False
        self.main_window.extension_manager.fire(u'change_experiment')
        self.main_window.set_busy(False)
        self.main_window.set_unsaved()
        
    def _reset_backend(self):
        """Resets the backend to the default backend settings"""
        self.experiment.var.canvas_backend = 'psycho'
        del self.experiment.var.keyboard_backend
        del self.experiment.var.mouse_backend
        del self.experiment.var.sampler_backend
        del self.experiment.var.synth_backend
        del self.experiment.var.color_backend
        del self.experiment.var.clock_backend
        del self.experiment.var.log_backend
        self.refresh()

    def refresh(self):
        """Updates the controls of the general tab."""
        # Lock the general tab to prevent a recursive loop
        self.lock = True
        # Set the header containing the title etc
        self.set_header_label()
        # Select the backend
        backend_name = backend.backend_match(self.experiment)
        if backend_name == u"custom":
            self.ui.widget_reset_backend.setVisible(True)
            self.ui.widget_backend_list.setDisabled(True)
            self.ui.button_backend_settings.setDisabled(True)
        else:
            self.ui.widget_reset_backend.setVisible(False)
            backend_info = backend.backend_info()[backend_name]
            backend_desc = backend_info['description']
            backend_settings = backend_info['settings']
            self.ui.button_backend_settings.setEnabled(backend_settings)
            self.ui.widget_backend_list.setDisabled(False)
            for radio_button in self._backend_button_group.buttons():
                if radio_button.text().startswith(backend_desc):
                    radio_button.setChecked(True)
        # Set the resolution
        try:
            self.ui.spinbox_width.setValue(int(self.experiment.var.width))
            self.ui.spinbox_height.setValue(int(self.experiment.var.height))
        except ValueError:
            self.experiment.notify(
                _(u"Failed to parse the resolution. Expecting positive numeric values.")
            )
        # Set the colors
        self.ui.edit_foreground.setText(safe_decode(
            self.experiment.var.foreground))
        self.ui.edit_background.setText(safe_decode(
            self.experiment.var.background))
        self.ui.widget_font.initialize(self.experiment)
        self.ui.checkbox_disable_garbage_collection.setChecked(
            self.experiment.var.disable_garbage_collection == u'yes')
        # Release the general tab
        self.lock = False


# Alias for backwards compatibility
general_properties = GeneralProperties
