""" Basic UI tests """
import os
import sys
import setproctitle
sys.path.append('..')
from pytest import mark
from typing import Type
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QTabWidget
from iBridges import IrodsLoginWindow, widget
from gui.IrodsSynchronisation import IrodsSynchronisation

ENVIRONMENT_PATH_FILE = 'irods_environment_new.json'
ENVIRONMENT = os.path.join(os.path.expanduser('~'), '.irods', ENVIRONMENT_PATH_FILE)
PASSWORD = os.environ.get('irods_password')


@mark.skipif(PASSWORD is None, reason="you're running this test somewhere where password is not set")
class TestUI:
    """
    Tests for the iBridges UI
    """
    def test_login(self, qtbot):
        test_widget = self.bootstrap_ibridges(qtbot)
        self.log_into_ibridges(qtbot, widget, PASSWORD)

        def check_widget():
            assert not isinstance(widget.currentWidget(), IrodsLoginWindow)
        qtbot.waitUntil(check_widget)

    @mark.skip(reason="Just a stub, also need to ensure that the order tests are running in does not matter")
    def test_synchronisation(self, qtbot):
        _ = self.bootstrap_ibridges(qtbot)
        self.log_into_ibridges(qtbot, widget, PASSWORD)
        tab: IrodsSynchronisation = self._navigate_to_tab(widget, "Synchronisation")
        assert isinstance(tab, IrodsSynchronisation)

    def _navigate_to_tab(self, test_widget, tab_name) -> Type[QWidget]:
        tab_widget: QTabWidget = test_widget.currentWidget().tabWidget
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i) == tab_name:
                tab_widget.setCurrentIndex(i)
                return tab_widget.currentWidget()
            else:
                pass
        raise ValueError('tab not found')

    def log_into_ibridges(self, qtbot, test_widget, password):
        env_select = test_widget.currentWidget().envbox
        for i in range(0, len(env_select)):
            if env_select.itemData(i, 0) == ENVIRONMENT_PATH_FILE:
                env_select.setCurrentIndex(i)
        test_widget.currentWidget().passwordField.clear()
        test_widget.currentWidget().passwordField.setText(password)
        qtbot.mouseClick(test_widget.currentWidget().connectButton, Qt.MouseButton.LeftButton)

        def logged_in_successfully():
            assert not isinstance(widget.currentWidget(),IrodsLoginWindow)
        qtbot.waitUntil(logged_in_successfully)

    def bootstrap_ibridges(self, qtbot):
        setproctitle.setproctitle('iBridges')
        widget.addWidget(IrodsLoginWindow())
        widget.show()
        qtbot.addWidget(widget)
        assert isinstance(widget.currentWidget(), IrodsLoginWindow)
        return widget
