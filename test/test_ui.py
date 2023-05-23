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

PASSWORD = "I should remove this but better safe than sorry"
with open('C:\\Users\\terst\\.irods\\passwd.txt', 'r') as file:
    PASSWORD = file.read().rstrip()


class TestUI:

    def test_login(self, qtbot):
        widget = self.bootstrap_ibridges(qtbot)
        self.log_into_ibridges(qtbot, widget, PASSWORD)
        def check_widget():
            assert type(widget.currentWidget()) is not iBridges.IrodsLoginWindow
        qtbot.waitUntil(check_widget)

    def test_synchronisation(self, qtbot):
        widget = self.bootstrap_ibridges(qtbot)
        self.log_into_ibridges(qtbot, widget, PASSWORD)
        def logged_in_successfully():
            assert type(widget.currentWidget()) is not iBridges.IrodsLoginWindow
        qtbot.waitUntil(logged_in_successfully)
        asdf : PyQt6.QtWidgets.QTabWidget = widget.currentWidget().tabWidget
        self._navigate_to_tab(asdf, "Synchronisation")
        qtbot.stop()
        pass

    def _navigate_to_tab(self, asdf, tab_name):
        for i in range(asdf.count()):
            if asdf.tabText(i) == tab_name:
                asdf.setCurrentIndex(i)
                return
            else:
                pass
        raise ValueError('tab not found')

    def log_into_ibridges(self, qtbot, widget, password):
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
