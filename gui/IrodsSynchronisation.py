import os
import sys
from datetime import datetime

import PyQt6.QtCore
import PyQt6.QtGui
import PyQt6.QtWidgets
import PyQt6.uic
import irods
import datetime
import time
import logging


from .synchronisationConfigurationTableModel import SynchronisationConfigurationTableModel
from .synchronisationStatusTableModel import SynchronisationStatusTableModel
from .fileuploader import FileUploader
from .ui_files.tabSynchronisation import Ui_tabSynchronisation
from .CreateUpdateSynchronisation import CreateUpdateSynchronisationConfigDialog
from synchronisation.configuration_item import SynchronisationConfigItem
from synchronisation.configuration_repository import ConfigRepository
from synchronisation.reporting_repository import ReportingRepository



class IrodsSynchronisation(PyQt6.QtWidgets.QWidget, Ui_tabSynchronisation):
    def __init__(self, ic):
        super().__init__()
        if getattr(sys, 'frozen', False):
            super().setupUi(self)
        else:
            PyQt6.uic.loadUi("gui/ui_files/tabSynchronisation.ui", self)
        self.configuration_repository = ConfigRepository()
        self.reporting_repository = ReportingRepository()
        self._setup_configuration_view_and_buttons()
        self._setup_sync_event_view_and_buttons()

        self._upload_thread_dict = {}
        self._uploader_dict = {}
        self.timer_dict = {}
        self.reinitialise_scheduling_timers()
        # self.uploader_thread = PyQt6.QtCore.QThread()
        self.ic = ic
        self.configuration_view.resizeColumnsToContents()

    def reinitialise_scheduling_timers(self):
        for value in self.timer_dict.values():
            value.stop()
        self.timer_dict.clear()
        datetimes = self.configuration_repository.get_all_cron_datetimes()
        for next_moment in datetimes:
            next_interval_seconds = int(next_moment[1] - time.mktime(datetime.datetime.now().timetuple()))
            timer = PyQt6.QtCore.QTimer()
            config_id = next_moment[0]
            timer.timeout.connect(lambda config_uuid=config_id: self.start_uploader(config_uuid))
            timer.timeout.connect(lambda: self.reinitialise_scheduling_timers())
            timer.setSingleShot(True)
            self.timer_dict[next_moment[0]] = timer
            timer.start(next_interval_seconds * 1000)

    def _config_view_model(self) -> SynchronisationConfigurationTableModel:
        return self.configuration_view.model()

    def _event_view_model(self) -> SynchronisationStatusTableModel:
        return self.event_view.model()

    def start_uploader_for_selected_config(self):
        row = self.configuration_view.currentIndex().row()
        config = self.configuration_repository.get_by_index(row)
        self.start_uploader(config.uuid)
    def start_uploader(self, config_uuid: str):
        if config_uuid is None:
            logging.error("invalidly scheduled uploader!")
            return
        config = self.configuration_repository.get_by_id(config_uuid)
        if config is None:
            logging.error("invalidly scheduled uploader!")
            return
        if self._upload_thread_dict.get(config.uuid) is None:
            logging.info("starting upload %s", config.uuid)
            uploader = FileUploader(self.ic, config=config, report_repo=self.reporting_repository)
            uploader_thread = PyQt6.QtCore.QThread()
            self._uploader_dict[config.uuid] = uploader
            self._upload_thread_dict[config.uuid] = uploader_thread
            uploader_thread.started.connect(uploader.run)
            uploader_thread.started.connect(lambda: self._config_view_model().display_loading(config.uuid))
            uploader.finished.connect(lambda: self.clean_up_uploader(config.uuid))
            uploader.finished.connect(lambda: self._config_view_model().remove_display_loading(config.uuid))
            uploader.moveToThread(uploader_thread)
            uploader_thread.start()

    def clean_up_uploader(self, uuid: str):
        logging.info("cleaning up uploader %s", uuid)
        del self._uploader_dict[uuid]
        self._upload_thread_dict[uuid].quit()
        del self._upload_thread_dict[uuid]

    def _setup_configuration_view_and_buttons(self):
        self.configuration_view.setSelectionBehavior(PyQt6.QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.configuration_view.setSelectionMode(PyQt6.QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.configuration_view.setModel(SynchronisationConfigurationTableModel(self.configuration_repository))
        self.configuration_view.setSizeAdjustPolicy(
            PyQt6.QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.configuration_view.horizontalHeader().setSizeAdjustPolicy(
            PyQt6.QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.configuration_view.model().layoutChanged.connect(lambda: self.on_configuration_changed())
        self.configuration_view.selectionModel().selectionChanged.connect(self.enable_disable_buttons)
        self.configuration_view.selectionModel().selectionChanged.connect(lambda: self.on_config_selection_changed())
        self.create_configuration_button.clicked.connect(lambda: self.create_configuration_dialog())
        self.update_configuration_button.clicked.connect(lambda: self.create_update_config_dialog())
        self.delete_configuration_button.clicked.connect(lambda: self.delete_selected_configuration())

    def _setup_sync_event_view_and_buttons(self):
        self.event_view.setSelectionBehavior(PyQt6.QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.event_view.setSelectionMode(PyQt6.QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.event_view.setModel(SynchronisationStatusTableModel(self.reporting_repository))
        self.event_view.setSizeAdjustPolicy(PyQt6.QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.event_view.horizontalHeader().setSizeAdjustPolicy(
            PyQt6.QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.event_view.model().layoutChanged.connect(lambda: self.event_view.resizeColumnsToContents())
        self.event_view.doubleClicked.connect(self.event_view.model().on_double_click)
        self.force_trigger_button.clicked.connect(lambda: self.start_uploader_for_selected_config())

    def on_configuration_changed(self):
        logging.info("on_configuration_changed")
        self.configuration_view.resizeColumnsToContents()

        self.reinitialise_scheduling_timers()
        #self.enable_disable_buttons()

    def enable_disable_buttons(self, selected = None, deselected=None):
        selected_rows = self.configuration_view.selectionModel().selectedRows()
        row_selected = len(selected_rows) > 0
        selected_config_has_no_upload_running = False

        self.update_configuration_button.setEnabled(row_selected)
        self.delete_configuration_button.setEnabled(row_selected)

        if row_selected:
            row_index = selected_rows[0].row()
            config = self.configuration_repository.get_by_index(row_index)
            selected_config_has_no_upload_running = self._upload_thread_dict.get(config.uuid,None) is None
        self.force_trigger_button.setEnabled( selected_config_has_no_upload_running)
        self.update_configuration_button.setStyleSheet(self.update_configuration_button.styleSheet())
        self.delete_configuration_button.setStyleSheet(self.delete_configuration_button.styleSheet())
        self.force_trigger_button.setStyleSheet(self.force_trigger_button.styleSheet())

    def on_config_selection_changed(self):
        logging.info("on_config_selection_changed")
        selected_rows = self.configuration_view.selectionModel().selectedRows()
        row_selected = len(selected_rows) > 0
        if row_selected:
            row_index = selected_rows[0].row()
            config = self.configuration_repository.get_by_index(row_index)
            self.event_view.model().change_selected_config_uuid(config.uuid)
            self.event_view.resizeColumnsToContents()
        else:
            self.event_view.model().clear_selected_report()
    def delete_selected_configuration(self):
        index = self.configuration_view.currentIndex().row()
        self.configuration_view.clearSelection()
        by_index = self.configuration_repository.get_by_index(index)
        self.configuration_repository.delete_config(by_index)

    def create_update_config_dialog(self):
        row = self.configuration_view.currentIndex().row()
        config_item = self.configuration_repository.get_by_index(row)
        self.create_configuration_dialog(config_item)

    def create_configuration_dialog(self, configuration_item: SynchronisationConfigItem = None):
        if configuration_item is None:
            configuration_item = SynchronisationConfigItem(
                type='',
                local='C:\\iRods\\jtersteegwur\\iBridges-Gui\\docker',
                remote='/RDMacc/home/terst007',
                cron='0 0 * * *'
            )
        dialog = PyQt6.QtWidgets.QDialog()
        resulting_config = CreateUpdateSynchronisationConfigDialog.create_or_update(self.ic, configuration_item, dialog)
        if resulting_config is not None:
            if resulting_config.uuid is None:
                self.createNewConfig(resulting_config)
                pass
            else:
                self.updateConfig(resulting_config)
                pass

    def createNewConfig(self, item: SynchronisationConfigItem):
        self.configuration_repository.add_config(item)

    def updateConfig(self, item: SynchronisationConfigItem):
        self.configuration_repository.update_config(item)
