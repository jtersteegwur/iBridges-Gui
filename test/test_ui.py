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
import logging
import time
import irodsConnector.dataOperations
import irodsConnector.resource
import irodsConnector.session

ENVIRONMENT_PATH = 'irods_environment_new.json'
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
        envSelect = widget.currentWidget().envbox
        for i in range(0, len(envSelect)):
            if envSelect.itemData(i,0) == ENVIRONMENT_PATH:
                envSelect.setCurrentIndex(i)
        widget.currentWidget().passwordField.clear()
        widget.currentWidget().passwordField.setText(password)
        qtbot.mouseClick(widget.currentWidget().connectButton, PyQt6.QtCore.Qt.MouseButton.LeftButton)

    def test_diff_upload_performance(self):
        session = irodsConnector.session.Session(ENVIRONMENT_PATH,PASSWORD)
        resource = irodsConnector.resource.Resource(session)
        data_op = irodsConnector.dataOperations.DataOperation(resource,session)
        session.connect("test")
        start_time = time.perf_counter()
        data_op.get_diff_upload("C:\\iRods\\irods-main","/RDMacc/home/terst007/upload_here/irods_main")
        end_time = time.perf_counter()
        logging.info("%s",end_time - start_time)


    def bootstrap_ibridges(self, qtbot):
        widget = iBridges.widget
        setproctitle.setproctitle('iBridges')
        widget.addWidget(iBridges.IrodsLoginWindow())
        widget.show()
        qtbot.addWidget(widget)
        assert type(widget.currentWidget()) is iBridges.IrodsLoginWindow
        return widget
