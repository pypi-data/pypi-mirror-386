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
import time
import functools
import traceback
from qtpy import QtWidgets, QtCore
from openexp import resources
from libopensesame.misc import snake_case, camel_case
from libopensesame.oslogging import oslogger
from libqtopensesame.misc.config import cfg
from libqtopensesame.misc.base_subcomponent import BaseSubcomponent
from libqtopensesame.misc.translate import translation_context


class BaseExtension(BaseSubcomponent):

    r"""A base class for GUI extensions."""
    extension_filter = None
    preferences_ui = None

    def __init__(self, main_window, info=None):
        r"""Constructor.

        Parameters
        ----------
        main_window
            The main-window object.
        info, optional
            deprecated
        """
        oslogger.debug(u'creating %s' % self.name())
        if info is not None:
            oslogger.warning('the info keyword is deprecated')
        if main_window.options.profile:
            # Use a special fire() function that keeps track of durations
            self._event_durations = {}
            self.fire = self._fire_and_time
        self._ = translation_context(snake_case(self.name()),
                                     category='extension')
        self.setup(main_window)
        if self.name() in self.unloaded_extension_manager:
            self._unloaded_extension = \
                self.unloaded_extension_manager[self.name()]
        else:
            self._unloaded_extension = \
                self.unloaded_extension_manager[snake_case(self.name())]
        self.register_ui_files()
        self.register_config()
        # Store of aliases so that we can still call the extension by its old
        # name if it has been renamed, e.g. OpenSesameIDE (old) for
        # opensesame_ide (new).
        name = self.name()
        self.aliases = [name]
        self.aliases += self.extension_attribute('aliases', [])
        if name.islower():
            self.aliases.append(camel_case(name))
        else:
            self.aliases.append(snake_case(name))
        try:
            qm_path = self.ext_resource('locale/' + main_window.locale + '.qm')
        except Exception as e:
            pass
        else:
            if main_window.translators:
                from qtpy.QtCore import QCoreApplication
                oslogger.info('installing translator {}'.format(qm_path))
                self._translator = main_window.translators.pop()
                self._translator.load(qm_path)
                QCoreApplication.installTranslator(self._translator)
            else:
                oslogger.warning('no translators objects available')
        self.create_action()

    @staticmethod
    def as_thread(wait):
        r"""A decorator to execute events in a separate thread, optionally
        after a delay.
        """
        def inner(fnc):
            def innermost(self, *args, **kwargs):
                QtCore.QTimer.singleShot(wait,
                    functools.partial(fnc, self, *args, **kwargs))
            return innermost
        return inner

    @property
    def menubar(self):
        return self.main_window.menuBar()

    @property
    def toolbar(self):
        return self.main_window.ui.toolbar_main

    @property
    def tabwidget(self):
        return self.main_window.ui.tabwidget

    @property
    def statusbar(self):
        return self.main_window.statusBar()

    @property
    def set_busy(self):
        return self.main_window.set_busy
    
    @property
    def extension_attribute(self):
        return self._unloaded_extension.attribute
    
    @property
    def extension_folder(self):
        return self._unloaded_extension.folder
    
    def folder(self):
        oslogger.warning('BaseExtension.folder() is deprecated, use '
                         'BaseExtension.extension_folder instead')
        return self._unloaded_extension.folder

    def label(self):
        r"""Gives the label that is used for the menu and toolbar entry.
        Normally, this is specified in info.json, but you can override this
        function to implement custom logic.

        Returns
        -------
        unicode, NoneType
            A label text or None.
        """
        if not hasattr(self, '_label'):
            label = self.extension_attribute('label', None)
            self._label = None if label is None else self._(label)
        return self._label

    def tooltip(self):
        r"""Gives the tooltip that is used for the menu and toolbar entry.
        Normally, this is specified in info.json, but you can override this
        function to implement custom logic.

        Returns
        -------
        unicode, NoneType
            A tooltip text.
        """
        if not hasattr(self, '_tooltip'):
            tooltip = self._(self.extension_attribute(u'tooltip', None))
            if not tooltip:
                self._tooltip = None
            else:
                shortcut = self.shortcut()
                if not shortcut:
                    self._tooltip = tooltip
                else:
                    self._tooltip = '{} ({})'.format(tooltip, shortcut)
        return self._tooltip

    def checkable(self):
        r"""Indicates whether the extension action is checkable or not.
        Normally, this is specified in info.json, but you can override this
        function to implement custom logic.

        Returns
        -------
        bool
        """
        return self.extension_attribute(u'checkable', False)

    def set_checked(self, checked):
        r"""Sets the checked status of the action. If there is no action, or if
        the action is not checkable, this is silently ignored.

        Parameters
        ----------
        checked : bool
            The checked status.
        """
        if self.action is None or not self.checkable():
            return
        self.action.setChecked(checked)

    def set_enabled(self, enabled=True):
        r"""Enables/ disables the action. If there is no action, this is
        silently ignored.

        Parameters
        ----------
        enabled : bool
            The enabled status.
        """
        if self.action is None:
            return
        self.action.setEnabled(enabled)

    def icon(self):
        r"""Gives the name of the icon that is used for the menu and toolbar
        entry. Normally, this is specified in info.json, but you can override
        this function to implement custom logic.

        Returns
        -------
        unicode
            The name of an icon.
        """
        return self.extension_attribute(u'icon', u'applications-utilities')

    def shortcut(self):
        r"""Gives the keyboard shortcut that activates the extension. Normally,
        this is specified in info.json, but you can override this function to
        implement custom logic. A shortcut only works if the extension has
        either a toolbar or menu entry.

        Returns
        -------
        unicode
            The keyboard shortcut.
        """
        return self.extension_attribute(u'shortcut', None)

    def menu_pos(self):
        r"""Describes the position of the extension in the menu. Normally, this
        is specified in info.json, but you can override this function to
        implement custom logic.

        Returns
        -------
        tuple, NoneType
            A (submenu, menuindex, separator_before, separator_after) tuple, or
            None if the extension has no menu entry.
        """
        menu_pos = self.extension_attribute(u'menu', None)
        if menu_pos is None:
            return None
        return (menu_pos.get(u'submenu', None),
                menu_pos.get(u'index', -1),
                menu_pos.get(u'separator_before', False),
                menu_pos.get(u'separator_after', False))

    def toolbar_pos(self):
        r"""Describes the position of the extension in the toolbar. Normally,
        this is specified in info.json, but you can override this function to
        implement custom logic.

        Returns
        -------
        tuple, NoneType
            An (index, separator_before, separator_after) tuple, or None if the
            extension has no toolbar entry.
        """
        toolbar_pos = self.extension_attribute(u'toolbar', None)
        if toolbar_pos is None:
            return None
        return (toolbar_pos.get(u'index', -1),
                toolbar_pos.get(u'separator_before', False),
                toolbar_pos.get(u'separator_after', False))

    def activate(self):
        r"""Is called when the extension is activated through a keyboard
        shortcut, or a menu/ toolbar click. Override this function to implement
        your extension's behavior.
        """
        pass

    def _activate(self):
        r"""A wrapper around [activate] to catch Exceptions."""
        try:
            self.activate()
        except Exception as e:
            self.notify(
                f'Extension {self.name()} misbehaved on activate '
                f'(see debug window for stack trace)',
                category='warning')
            traceback.print_exc()
            oslogger.error(
                f'Extension {self.name()} misbehaved on activate: {e}')

    def add_action(self, widget, action, index, separator_before,
                   separator_after):
        r"""Adds an action to a widget that supports actions (i.e. a QMenu or a
        QToolBar).

        Parameters
        ----------
        widget
            The widget to add the action to.
        action
            The action to add.
        index
            The index of the action.
        separator_before
            Indicates whether a separator should be added before the action.
        separator_action
            Indicates whether a separator should be added before the action.
        """
        if index >= len(widget.actions()) or index < -len(widget.actions()) \
                or index == -1:
            before = None
            widget.addAction(action)
        else:
            if index < 0:
                index += 1
            before = widget.actions()[index]
        if separator_after:
            if before is None:
                before = widget.addSeparator()
            else:
                before = widget.insertSeparator(before)
        if before is None:
            widget.addAction(action)
        else:
            widget.insertAction(before, action)
        if separator_before:
            widget.insertSeparator(action)

    def get_submenu(self, menu_text):
        r"""Gets the submenu that matches the menu text. If no match is found a
        new submenu is created.

        Parameters
        ----------
        menu_text
            The menu text. This should match an object in
            main_window.ui.menu_[menu_text].

        Returns
        -------
        QMenu
        """
        menu_name = u'menu_%s' % menu_text.lower()
        if not hasattr(self.main_window.ui, menu_name):
            menu_name = u'menu_custom_{}'.format(len(self.menubar.actions()))
            menu = QtWidgets.QMenu(menu_text)
            self.menubar.addMenu(menu)
            setattr(self.main_window.ui, menu_name, menu)
        return getattr(self.main_window.ui, menu_name)

    def register_ui_files(self):
        r"""Registers all .ui files in the extension folder so that they can be
        retrieved as extensions.[extension name].[ui name].
        """
        for path in os.listdir(self.extension_folder):
            if path.endswith(u'.ui'):
                basename = os.path.splitext(path)[0]
                resource_path = os.path.join(self.extension_folder, path)
                name = self.name()
                resources[f'extensions.{name}.{basename}'] = resource_path
                if not name.islower():
                    resources[f'extensions.{snake_case(name)}.{basename}'] = \
                        resource_path

    def qaction(self, icon, label, target, checkable=False, tooltip=None,
                shortcut=None):
        """Creates a QAction for an extension."""
        action = QtWidgets.QAction(
            self.theme.qicon(icon), label, self.main_window)
        action.triggered.connect(target)
        action.setCheckable(checkable)
        if tooltip is not None:
            action.setToolTip(tooltip)
        if shortcut is not None:
            action.setShortcuts([shortcut])
        return action

    def create_action(self):
        r"""Creates a QAction for the extension, and adds it to the menubar
        and/ or the toolbar.
        """
        label = self.label()
        shortcut = self.shortcut()
        if label is None and shortcut is None:
            self.action = None
            return
        self.action = self.qaction(self.icon(), label,
                                   self._activate, checkable=self.checkable(),
                                   tooltip=self.tooltip(), shortcut=shortcut)
        # Insert the action into the menu
        if self.menu_pos() is not None:
            submenu_text, index, separator_before, separator_after = \
                self.menu_pos()
            submenu = self.get_submenu(submenu_text)
            self.add_action(submenu, self.action, index, separator_before,
                            separator_after)
        # Insert the action into the toolbar
        if self.toolbar_pos() is not None:
            index, separator_before, separator_after = self.toolbar_pos()
            self.add_action(self.toolbar, self.action, index,
                            separator_before, separator_after)

    def register_config(self):
        r"""Registers the extension settings in the config object."""
        for setting, default in self.extension_attribute(u'settings', {}).items():
            if isinstance(default, dict):
                default = default.get(self.main_window.mode, u'')
            cfg.register(setting, default=default)

    def _settings_widget_from_ui(self, ui):
        r"""Generates a standard preferences widget based on a ui file.

        Parameters
        ----------
        ui
            A ui file.
        """
        from libqtopensesame.widgets.base_preferences_widget import (
            BasePreferencesWidget
        )
        return BasePreferencesWidget(self.main_window, ui)

    def settings_widget(self):
        r"""Creates a settings QWidget for the extension, or returns None if no
        settings have been defined. Override this function to implement a more
        fancy non-default settings menu.

        Returns
        -------
        A settings QWidget or None.
        """
        if self.preferences_ui is not None:
            return self._settings_widget_from_ui(self.preferences_ui)
        r = 10000000  # Maximumum range for spinbox widgets
        settings = self.extension_attribute('settings', None)
        if settings is None:
            return
        group = QtWidgets.QGroupBox(
            self._(u'Extension: %s') % self.name(),
            self.main_window
        )
        group.__advanced__ = True
        layout = QtWidgets.QFormLayout(group)
        self.settings_controls = {}
        for setting, default in settings.items():
            value = cfg[setting]
            label = QtWidgets.QLabel(self._(setting))
            if isinstance(default, bool):
                control = QtWidgets.QCheckBox(self.main_window)
                control.setChecked(bool(value))
                control.clicked.connect(self.apply_settings_widget)
            elif isinstance(default, int):
                try:
                    value = int(value)
                except:
                    value = default
                control = QtWidgets.QSpinBox(self.main_window)
                control.setRange(-r, r)
                control.setValue(value)
                control.editingFinished.connect(self.apply_settings_widget)
            elif isinstance(default, float):
                try:
                    value = float(value)
                except:
                    value = default
                control = QtWidgets.QDoubleSpinBox(self.main_window)
                control.setRange(-r, r)
                control.setValue(value)
                control.editingFinished.connect(self.apply_settings_widget)
            else:
                control = QtWidgets.QLineEdit(safe_decode(value))
                control.editingFinished.connect(self.apply_settings_widget)
            self.settings_controls[setting] = control
            layout.addRow(label, control)
        group.setLayout(layout)
        return group

    def apply_settings_widget(self):
        r"""Applies the settings widget. This function is called automatically
        when a default settings widget is created by [settings_widget].
        """
        
        for setting, default in self.extension_attribute(u'settings', {}).items():
            control = self.settings_controls[setting]
            if isinstance(default, bool):
                cfg[setting] = control.isChecked()
            elif isinstance(default, int) or isinstance(default, float):
                cfg[setting] = control.value()
            else:
                cfg[setting] = str(control.text())

    def ext_resource(self, resource):
        r"""Finds an extension resource, i.e. a file in the extension folder,
        and returns the full path to the resource. An FileNotFoundError is 
        raised if the resource does not exist.

        Parameters
        ----------
        resource : str, unicode
            The name of a resource.

        Returns
        -------
        unicode
            The full path to the resource.
        """
        path = os.path.join(self.extension_folder, u'locale', self.locale,
                            resource)
        if os.path.exists(path):
            return path
        path = os.path.join(self.extension_folder, resource)
        if not os.path.exists(path):
            raise FileNotFoundError(f'Extension resource not found: {path}')
        return path
