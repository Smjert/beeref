# This file is part of BeeRef.
#
# BeeRef is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BeeRef is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BeeRef.  If not, see <https://www.gnu.org/licenses/>.

from functools import partial
import logging

from PyQt6 import QtWidgets

from beeref import constants
from beeref.config import BeeSettings, settings_events


logger = logging.getLogger(__name__)


class RadioGroup(QtWidgets.QGroupBox):
    TITLE = None
    HELPTEXT = None
    KEY = None
    OPTIONS = None

    def __init__(self):
        super().__init__(self.TITLE)
        self.settings = BeeSettings()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        settings_events.restore_defaults.connect(self.on_restore_defaults)

        if self.HELPTEXT:
            helptxt = QtWidgets.QLabel(self.HELPTEXT)
            helptxt.setWordWrap(True)
            layout.addWidget(helptxt)

        self.ignore_values_changed = True
        self.buttons = {}
        for (value, label, helptext) in self.OPTIONS:
            btn = QtWidgets.QRadioButton(label)
            self.buttons[value] = btn
            btn.setToolTip(helptext)
            btn.toggled.connect(
                partial(self.on_values_changed, value=value, button=btn))
            if value == self.settings.valueOrDefault(self.KEY):
                btn.setChecked(True)
            layout.addWidget(btn)

        self.ignore_values_changed = False
        layout.addStretch(100)

    def on_values_changed(self, value, button):
        if self.ignore_values_changed:
            return

        if value != self.settings.valueOrDefault(self.KEY):
            logger.debug(f'Setting {self.KEY} changed to: {value}')
            self.settings.setValue(self.KEY, value)

    def on_restore_defaults(self):
        new_value = self.settings.valueOrDefault(self.KEY)
        self.ignore_values_changed = True
        for value, btn in self.buttons.items():
            btn.setChecked(value == new_value)
        self.ignore_values_changed = False


class IntegerGroup(QtWidgets.QGroupBox):
    TITLE = None
    HELPTEXT = None
    KEY = None
    MIN = None
    MAX = None

    def __init__(self):
        super().__init__(self.TITLE)
        self.settings = BeeSettings()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        settings_events.restore_defaults.connect(self.on_restore_defaults)

        if self.HELPTEXT:
            helptxt = QtWidgets.QLabel(self.HELPTEXT)
            helptxt.setWordWrap(True)
            layout.addWidget(helptxt)

        self.input = QtWidgets.QSpinBox()
        self.input.setValue(self.settings.valueOrDefault(self.KEY))
        self.input.setRange(self.MIN, self.MAX)
        self.input.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.input)
        layout.addStretch(100)
        self.ignore_values_changed = False

    def on_value_changed(self, value):
        if self.ignore_values_changed:
            return

        if value != self.settings.valueOrDefault(self.KEY):
            logger.debug(f'Setting {self.KEY} changed to: {value}')
            self.settings.setValue(self.KEY, value)

    def on_restore_defaults(self):
        new_value = self.settings.valueOrDefault(self.KEY)
        self.ignore_values_changed = True
        self.input.setValue(new_value)
        self.ignore_values_changed = False


class ImageStorageFormatWidget(RadioGroup):
    TITLE = 'Image Storage Format:'
    HELPTEXT = ('How images are stored inside bee files.'
                ' Changes will only take effect on newly saved images.')
    KEY = 'Items/image_storage_format'
    OPTIONS = (
        ('best', 'Best Guess',
         ('Small images and images with alpha channel are stored as png,'
          ' everything else as jpg')),
        ('png', 'Always PNG', 'Lossless, but large bee file'),
        ('jpg', 'Always JPG',
         'Small bee file, but lossy and no transparency support'))


class ArrangeGapWidget(IntegerGroup):
    TITLE = 'Arrange Gap:'
    HELPTEXT = ('The gap between images when using arrange actions.')
    KEY = 'Items/arrange_gap'
    MIN = 0
    MAX = 200


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(f'{constants.APPNAME} Settings')
        tabs = QtWidgets.QTabWidget()

        # Miscellaneous
        misc = QtWidgets.QWidget()
        misc_layout = QtWidgets.QGridLayout()
        misc.setLayout(misc_layout)
        misc_layout.addWidget(ImageStorageFormatWidget(), 0, 0)
        misc_layout.addWidget(ArrangeGapWidget(), 0, 1)
        tabs.addTab(misc, '&Miscellaneous')

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(tabs)

        # Bottom row of buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        reset_btn = QtWidgets.QPushButton('&Restore Defaults')
        reset_btn.setAutoDefault(False)
        reset_btn.clicked.connect(self.on_restore_defaults)
        buttons.addButton(reset_btn,
                          QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        layout.addWidget(buttons)
        self.show()

    def on_restore_defaults(self, *args, **kwargs):
        reply = QtWidgets.QMessageBox.question(
            self,
            'Restore defaults?',
            'Do you want to restore all settings to their default values?')

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            BeeSettings().restore_defaults()
