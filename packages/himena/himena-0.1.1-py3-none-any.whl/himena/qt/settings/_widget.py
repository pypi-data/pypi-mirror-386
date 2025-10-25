from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtWidgets as QtW, QtGui, QT6, QtCore
from qtpy.QtCore import Qt

from himena.consts import DefaultFontFamily
from himena.qt.settings._theme import QThemePanel
from himena.qt.settings._plugins import QPluginListEditor
from himena.qt.settings._startup_commands import QStartupCommandsPanel
from himena.qt.settings._configs import QPluginConfigs
from himena.qt.settings._keybind_edit import QKeybindEdit

if TYPE_CHECKING:
    from himena.widgets import MainWindow


class QSettingsDialog(QtW.QDialog):
    """The dialog used for settings."""

    def __init__(self, ui: MainWindow) -> None:
        super().__init__(ui._backend_main_window)
        self._ui = ui
        self.setWindowTitle("Settings")
        self.resize(600, 400)
        layout = QtW.QHBoxLayout(self)

        layout_left = QtW.QVBoxLayout()
        layout_left.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(layout_left)

        self._list = QtW.QListWidget(self)
        self._list.setFixedWidth(150)
        self._list.setFont(QtGui.QFont(DefaultFontFamily, 13))
        self._open_json_btn = QtW.QPushButton("Open JSON")
        self._open_json_btn.clicked.connect(self._open_json)
        self._stack = QtW.QStackedWidget(self)

        self._list.currentRowChanged.connect(
            lambda: self._stack.setCurrentIndex(self._list.currentRow())
        )

        layout_left.addWidget(self._list)
        layout_left.addWidget(self._open_json_btn)
        layout.addWidget(self._stack)

        self._setup_panels()
        self._list.setCurrentRow(0)

    def addPanel(self, name: str, title: str, panel: QtW.QWidget) -> None:
        """Add a panel to the settings dialog, with the corresponding list item."""
        self._list.addItem(name)
        widget = QtW.QWidget(self._stack)
        layout = QtW.QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._stack.addWidget(widget)
        layout.addWidget(QTitleLabel(title, 18))
        layout.addWidget(panel)

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if (
            a0.key() in (Qt.Key.Key_W, Qt.Key.Key_Q)
            and a0.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.close()
        return super().keyPressEvent(a0)

    def _setup_panels(self):
        self.addPanel("Apperance", "Color Theme", QThemePanel(self._ui))
        self.addPanel("Plugins", "Plugins", QPluginListEditor(self._ui))
        self.addPanel("Startup", "Startup Commands", QStartupCommandsPanel(self._ui))
        self.addPanel("Keybindings", "Keybindings", QKeybindEdit(self._ui))
        self.addPanel(
            "Configurations", "Plugin Configurations", QPluginConfigs(self._ui)
        )

    def _open_json(self):
        self._ui.read_file(self._ui.app_profile.profile_path())
        self.close()


class QTitleLabel(QtW.QLabel):
    """Label used for titles in the preference dialog."""

    def __init__(self, text: str, size: int) -> None:
        super().__init__()
        self.setText(text)
        self.setFont(QtGui.QFont(DefaultFontFamily, size))

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        color = foreground_color_role(self.palette())
        painter.setPen(QtGui.QPen(color, 1))
        bottom_left = self.rect().bottomLeft()
        bottom_right = QtCore.QPoint(bottom_left.x() + 300, bottom_left.y())
        painter.drawLine(bottom_left, bottom_right)
        return super().paintEvent(a0)


def foreground_color_role(qpalette: QtGui.QPalette) -> QtGui.QColor:
    if QT6:
        return qpalette.color(
            QtGui.QPalette.ColorGroup.Normal, QtGui.QPalette.ColorRole.Text
        )
    else:
        return qpalette.color(QtGui.QPalette.ColorRole.Foreground)
