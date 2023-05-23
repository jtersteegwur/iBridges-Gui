import os
import sys

import setproctitle

sys.path.append('..')
# sys.frozen = True

import PyQt6.QtCore
import PyQt6.QtGui
import PyQt6.QtWidgets
import PyQt6.uic

import iBridges
import gui

ENVIRONMENT_PATH = 'irods_environment_integration_test.json'
PASSWORD = os.environ.get('irods_password')

class TestUI:
    def test_login(self, qtbot):
        widget = self.bootstrap_ibridges(qtbot)
        self.log_into_ibridges(qtbot, widget, PASSWORD)
        def check_widget():
            assert type(widget.currentWidget()) is not iBridges.IrodsLoginWindow
        qtbot.waitUntil(check_widget)

    def log_into_ibridges(self, qtbot, widget, password):
        envSelect = widget.currentWidget().envbox
        for i in range(0, len(envSelect)):
            if envSelect.itemData(i,0) == ENVIRONMENT_PATH:
                envSelect.setCurrentIndex(i)
        widget.currentWidget().passwordField.clear()
        widget.currentWidget().passwordField.setText(password)
        qtbot.mouseClick(widget.currentWidget().connectButton, PyQt6.QtCore.Qt.MouseButton.LeftButton)

    def bootstrap_ibridges(self, qtbot):
        widget = iBridges.widget
        setproctitle.setproctitle('iBridges')
        widget.addWidget(iBridges.IrodsLoginWindow())
        widget.show()
        qtbot.addWidget(widget)
        assert type(widget.currentWidget()) is iBridges.IrodsLoginWindow
        return widget
