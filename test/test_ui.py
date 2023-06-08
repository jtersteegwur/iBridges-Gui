from PyQt6.QtWidgets import QWidget
from gui.IrodsSynchronisation import IrodsSynchronisation
from typing import Type

import sys

import irods.collection
import setproctitle

sys.path.append('..')
# sys.frozen = True

import PyQt6.QtCore
import PyQt6.QtGui
import PyQt6.QtWidgets
import PyQt6.uic

import iBridges
import gui
import logging
import time
import os
import irodsConnector.dataOperations
import irodsConnector.resource
import irodsConnector.session


from pytest import mark



ENVIRONMENT_PATH_FILE = 'irods_environment_new.json'
ENVIRONMENT = os.path.join(os.path.expanduser('~'), '.irods', ENVIRONMENT_PATH_FILE)
PASSWORD = os.environ.get('irods_password')

@mark.skipif(PASSWORD is None, reason="you're running this test somewhere where password is not set")
class TestUI:
    def test_login(self, qtbot):
        widget = self.bootstrap_ibridges(qtbot)
        self.log_into_ibridges(qtbot, widget, PASSWORD)
        def check_widget():
            assert not isinstance(widget.currentWidget(),iBridges.IrodsLoginWindow)
        qtbot.waitUntil(check_widget)

    @mark.skip(reason="Just a stub, also need to ensure that the order tests are running in does not matter")
    def test_synchronisation(self, qtbot):
        widget = self.bootstrap_ibridges(qtbot)
        self.log_into_ibridges(qtbot, widget, PASSWORD)
        tab: IrodsSynchronisation = self._navigate_to_tab(widget, "Synchronisation")
        assert isinstance(tab,IrodsSynchronisation)
    def _navigate_to_tab(self, widget, tab_name) -> Type[QWidget]:
        tab_widget: PyQt6.QtWidgets.QTabWidget = widget.currentWidget().tabWidget
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i) == tab_name:
                tab_widget.setCurrentIndex(i)
                return tab_widget.currentWidget()
            else:
                pass
        raise ValueError('tab not found')

    def log_into_ibridges(self, qtbot, widget, password):
        envSelect = widget.currentWidget().envbox
        for i in range(0, len(envSelect)):
            if envSelect.itemData(i,0) == ENVIRONMENT_PATH_FILE:
                envSelect.setCurrentIndex(i)
        widget.currentWidget().passwordField.clear()
        widget.currentWidget().passwordField.setText(password)
        qtbot.mouseClick(widget.currentWidget().connectButton, PyQt6.QtCore.Qt.MouseButton.LeftButton)
        def logged_in_successfully():
            assert not isinstance(widget.currentWidget(),iBridges.IrodsLoginWindow)
        qtbot.waitUntil(logged_in_successfully)

    def bootstrap_ibridges(self, qtbot):
        widget = iBridges.widget
        setproctitle.setproctitle('iBridges')
        widget.addWidget(iBridges.IrodsLoginWindow())
        widget.show()
        qtbot.addWidget(widget)
        assert type(widget.currentWidget()) is iBridges.IrodsLoginWindow
        return widget



