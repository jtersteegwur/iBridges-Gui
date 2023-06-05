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




ENVIRONMENT_PATH_FILE = 'irods_environment_new.json'
ENVIRONMENT = os.path.join(os.path.expanduser('~'), '.irods', ENVIRONMENT_PATH_FILE)
PASSWORD = "I should remove this but better safe than sorry"
with open('C:\\Users\\terst\\.irods\\passwd.txt', 'r') as file:
    PASSWORD = file.read().rstrip()



class TestUI:




    def test_diff_upload_performance(self,caplog):
        caplog.set_level(logging.INFO)
        connector = IrodsConnector(ENVIRONMENT, PASSWORD, 'mooienaam')
        start_time = time.perf_counter()
        logging.getLogger().info("test")
       #connector._data_op.fetch_all_files_and_checksums_in_collection("/RDMacc/home/terst007/upload_here/irods_main")
        connector.get_diff_upload("C:\\iRods\\irods-main","/RDMacc/home/terst007/upload_here/irods_main")
        end_time = time.perf_counter()
        logging.info("%s", end_time - start_time)
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
            if envSelect.itemData(i,0) == ENVIRONMENT_PATH_FILE:
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



