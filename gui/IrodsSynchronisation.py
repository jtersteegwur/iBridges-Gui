import os
import sys
from datetime import datetime
from typing import Optional

import PyQt6.QtCore
import PyQt6.QtGui
import PyQt6.QtWidgets
import PyQt6.uic

import gui
import synchronisation.configuration_repository
import synchronisation.configuration_item
import synchronisation.reporting_repository
import irods
import datetime
import croniter
import time
import logging

from synchronisation.reporting import SynchronisationStatusEvent, SynchronisationStatusReport


class AnimationTicker(PyQt6.QtCore.QObject):
    text_animation_tick = PyQt6.QtCore.pyqtSignal(int)

    def __init__(self):
        super(AnimationTicker, self).__init__()
        self.running = False
        self.tickcounter = 0


    @PyQt6.QtCore.pyqtSlot()
    def run(self):
        self.running = True
        self.tickcounter = 0

        while self.running:
            self.text_animation_tick.emit(self.tickcounter)
            logging.info("Beep")
            self.thread().msleep(100)
            self.tickcounter += 1

    @PyQt6.QtCore.pyqtSlot()
    def stop(self):
        self.running = False


class IrodsSynchronisation(PyQt6.QtWidgets.QWidget, gui.ui_files.tabSynchronisation.Ui_tabSynchronisation):
    def __init__(self, ic):
        super().__init__()
        if getattr(sys, 'frozen', False):
            super().setupUi(self)
        else:
            PyQt6.uic.loadUi("gui/ui_files/tabSynchronisation.ui", self)
        self.configuration_repository = synchronisation.configuration_repository.ConfigRepository()
        self.reporting_repository = synchronisation.reporting_repository.ReportingRepository()
        self._setup_configuration_view()
        self._setup_sync_event_view()
        self.create_configuration_button.clicked.connect(lambda: self.create_configuration_dialog())
        self.update_configuration_button.clicked.connect(lambda: self.create_update_config_dialog())
        self.delete_configuration_button.clicked.connect(lambda: self.delete_selected_configuration())
        self.configuration_view.model().layoutChanged.connect(lambda: self.on_configuration_changed())
        self.configuration_view.selectionModel().selectionChanged.connect(lambda: self.enable_disable_buttons())
        self.on_configuration_changed()
        self._setup_animation_ticker()
        self.force_trigger_button.clicked.connect(self.toggle1)
        self.ui = None
        self.ic = ic

    def _setup_animation_ticker(self):
        self.ticker_thread = PyQt6.QtCore.QThread()
        self.ticker = AnimationTicker()
        self.ticker.moveToThread(self.ticker_thread)
        self.ticker_thread.started.connect(self.ticker.run)
        self.ticker_thread.start()

    def toggle1(self):
        self.force_trigger_button.clicked.disconnect()
        self.ticker.text_animation_tick.connect(self.timerding)
        self.force_trigger_button.clicked.connect(self.toggle2)

    def toggle2(self):
        self.force_trigger_button.clicked.disconnect()
        self.force_trigger_button.clicked.connect(self.toggle1)

    def timerding(self, tickcounter):
        bla = [
            'loading',
            'loading.',
            'loading..',
            'loading...',
            'loading..',
            'loading.'
        ]
        current_frame = tickcounter % len(bla)
        self.force_trigger_button.setText(bla[current_frame])


    def _setup_configuration_view(self):
        self.configuration_view.setSelectionBehavior(PyQt6.QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.configuration_view.setSelectionMode(PyQt6.QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.configuration_view.setModel(SynchronisationConfigurationTableModel(self.configuration_repository))
        self.configuration_view.setSizeAdjustPolicy(
            PyQt6.QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.configuration_view.horizontalHeader().setSizeAdjustPolicy(
            PyQt6.QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

    def _setup_sync_event_view(self):
        self.event_view.setSelectionBehavior(PyQt6.QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.event_view.setSelectionMode(PyQt6.QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.event_view.setModel(SynchronisationStatusTableModel(self.reporting_repository))
        self.event_view.setSizeAdjustPolicy(PyQt6.QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.event_view.horizontalHeader().setSizeAdjustPolicy(
            PyQt6.QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.event_view.model().layoutChanged.connect(lambda: self.event_view.resizeColumnsToContents())
        self.event_view.doubleClicked.connect(self.event_view.model().on_double_click)

    def on_configuration_changed(self):
        self.configuration_view.resizeColumnsToContents()
        self.enable_disable_buttons()

    def enable_disable_buttons(self):
        row_index = self.configuration_view.currentIndex().row()
        has_selected_items = row_index >= 0
        update_delete_force_enabled = has_selected_items
        self.update_configuration_button.setEnabled(update_delete_force_enabled)
        self.delete_configuration_button.setEnabled(update_delete_force_enabled)
        self.force_trigger_button.setEnabled(update_delete_force_enabled)
        self.update_configuration_button.setStyleSheet(self.update_configuration_button.styleSheet())
        self.delete_configuration_button.setStyleSheet(self.delete_configuration_button.styleSheet())
        self.force_trigger_button.setStyleSheet(self.force_trigger_button.styleSheet())
        if has_selected_items:
            config = self.configuration_repository.get_by_index(row_index)
            self.event_view.model().change_selected_config_uuid(config.uuid)
            self.event_view.resizeColumnsToContents()
        else:
            self.event_view.model().change_selected_config_uuid(None)

    def delete_selected_configuration(self):
        index = self.configuration_view.currentIndex().row()
        by_index = self.configuration_repository.get_by_index(index)
        self.configuration_repository.delete_config(by_index)
        self.configuration_view.clearSelection()

    def create_update_config_dialog(self):
        row = self.configuration_view.currentIndex().row()
        config_item = self.configuration_repository.get_by_index(row)
        self.create_configuration_dialog(config_item)

    def create_configuration_dialog(self,
                                    configuration_item: synchronisation.configuration_item.SynchronisationConfigItem = None):
        if configuration_item is None:
            configuration_item = synchronisation.configuration_item.SynchronisationConfigItem(
                type='',
                local='C:\\iRods\\jtersteegwur\\iBridges-Gui\\docker',
                remote='/RDMacc/home/terst007',
                cron='0 0 * * *'
            )
        dialog = PyQt6.QtWidgets.QDialog()
        self.ui = gui.ui_files.dialogCreateUpdateSynchronisation.Ui_Dialog()
        self.ui.setupUi(dialog)

        def put_data_in_object(obj: synchronisation.configuration_item.SynchronisationConfigItem,
                               ui: gui.ui_files.dialogCreateUpdateSynchronisation.Ui_Dialog):
            obj.type = self.dialogGetType(self.ui)
            obj.local = ui.localInput.toPlainText()
            obj.remote = ui.remoteInput.toPlainText()
            obj.cron = ui.cronInput.toPlainText()
            return obj

        try:
            self.ui.localInput.setPlainText(configuration_item.local)
            self.ui.remoteInput.setPlainText(configuration_item.remote)
            self.ui.cronInput.setPlainText(configuration_item.cron)
            self.ui.browseButton.clicked.connect(lambda: self.dialogOpenfileDialog(self.ui.localInput))
            self.ui.copyFromBrowserButton.clicked.connect(lambda: self.dialogCopyFromiRodsBrowser(self.ui.remoteInput))
            self.ui.comboBox.currentIndexChanged.connect(
                lambda: self.dialogSyncComboAndInput('combobox', self.ui.cronInput, self.ui.comboBox))
            self.ui.cronInput.textChanged.connect(
                lambda: self.dialogSyncComboAndInput('text', self.ui.cronInput, self.ui.comboBox))
            self.ui.buttonBox.accepted.connect(
                lambda: self.dialogValidateNewConfig(dialog, self.ic, put_data_in_object(configuration_item, self.ui)))
            if configuration_item.uuid is None:
                dialog.accepted.connect(
                    lambda: self.createNewConfig(put_data_in_object(configuration_item, self.ui)))
            else:
                dialog.accepted.connect(
                    lambda: self.updateConfig(put_data_in_object(configuration_item, self.ui)))

            self.dialogSyncComboAndInput('text', self.ui.cronInput, self.ui.comboBox)

            dialog_exec = dialog.exec()
        except Exception as e:
            pass
            raise e

    def dialogSyncComboAndInput(self, initiator, input, combobox):
        index = combobox.currentIndex()
        text = input.toPlainText()
        if 'text' == initiator:
            match text:
                case '0 0 * * *':
                    combobox.blockSignals(True)
                    combobox.setCurrentIndex(0)
                    combobox.blockSignals(False)
                case '0 13 * * *':
                    combobox.blockSignals(True)
                    combobox.setCurrentIndex(1)
                    combobox.blockSignals(False)
                case _:
                    combobox.blockSignals(True)
                    combobox.setCurrentIndex(2)
                    combobox.blockSignals(False)
        elif 'combobox' == initiator:
            match index:
                case 0:
                    input.blockSignals(True)
                    input.setText('0 0 * * *')
                    input.blockSignals(False)
                case 1:
                    input.blockSignals(True)
                    input.setText('0 13 * * *')
                    input.blockSignals(False)

    def dialogValidateNewConfig(self, dialog, ic, item: synchronisation.configuration_item.SynchronisationConfigItem):
        try:
            remote_permission = ic.get_permissions(item.remote)
            l = list(filter(lambda perm: perm.user_name == ic.session.username and (
                    perm.access_name == 'own' or perm.access_name == 'write'),
                            remote_permission))
            remote_valid = len(l) >= 1
        except irods.exception.CollectionDoesNotExist:
            remote_valid = False

        config_valid = item.validate_cron_localpath() and remote_valid
        if config_valid:
            dialog.accept()

    def dialogOpenfileDialog(self, target):
        dialog = PyQt6.QtWidgets.QFileDialog()
        # option = PyQt6.QtWidgets.QFileDialog.Option.ShowDirsOnly
        file_select = PyQt6.QtWidgets.QFileDialog.getExistingDirectory(dialog, "Select folder")
        if file_select and '' != file_select:
            target.setPlainText(os.path.normpath(file_select))

    def createNewConfig(self, item: synchronisation.configuration_item.SynchronisationConfigItem):
        self.configuration_repository.add_config(item)

    def updateConfig(self, item: synchronisation.configuration_item.SynchronisationConfigItem):
        self.configuration_repository.update_config(item)

    def dialogGetType(self, ui):
        if ui.radioButton.isEnabled():
            return "Two-way replication"
        elif ui.radioButton_2.isEnabled():
            return "Scheduled upload"
        elif ui.radioButton_3.isEnabled():
            return "One-way replication"


class SynchronisationConfigurationTableModel(PyQt6.QtCore.QAbstractTableModel):
    def __init__(self, config_repository: synchronisation.configuration_repository.ConfigRepository, parent=None):
        super().__init__(parent)
        self.config_repository = config_repository
        config_repository.attach_obverver(self.on_data_changed)

    def on_data_changed(self):
        self.layoutChanged.emit()

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        repository_len = self.config_repository.len()
        return repository_len

    def columnCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        return 4

    def headerData(self, section: int, orientation: PyQt6.QtCore.Qt.Orientation, role: int = ...):
        if role == PyQt6.QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == orientation.Horizontal:
                return ["Type", "State", "Local", "Remote"][section]
            else:
                return str(section)
        return None

    def data(self, index, role=PyQt6.QtCore.Qt.ItemDataRole.DisplayRole):
        if role == PyQt6.QtCore.Qt.ItemDataRole.DisplayRole:
            row = index.row()
            sci = self.config_repository.get_by_index(row)
            match (index.column()):
                case 0:
                    return sci.type
                case 1:
                    return self.determineState(sci)
                case 2:
                    return sci.local
                case 3:
                    return sci.remote
        return PyQt6.QtCore.QVariant()

    def determineState(self, sci: synchronisation.configuration_item.SynchronisationConfigItem):
        if sci.validate_cron_localpath():
            now = datetime.datetime.now()
            next_moment = croniter.croniter(sci.cron, now).get_next(datetime.datetime)
            str_next_moment = next_moment.strftime("%m/%d/%Y, %H:%M:%S")
            return f'Scheduled for {str_next_moment}'
        else:
            return 'ERROR'


class SynchronisationStatusTableModel(PyQt6.QtCore.QAbstractTableModel):
    def __init__(self, repository: synchronisation.reporting_repository.ReportingRepository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self._selected_configuration_uuid: Optional[str] = None
        self._selected_report: Optional[synchronisation.reporting.SynchronisationStatusReport] = None
        self._selected_configuration_reports: list[synchronisation.reporting.SynchronisationStatusReport] = []
        self.report_headers = ["StartTime", "EndTime", "Status", "Size"]
        self.event_headers = ["StartTime", "EndTate", "Source", "Destination", "Status", "Bytes"]
        self.repository.attach_obverver(self.on_repository_data_changed)

    def on_repository_data_changed(self, config_uuid, report_uuid):
        if self._selected_configuration_uuid == config_uuid:
            self._selected_configuration_reports = self.repository.find_reports_by_config_id(config_uuid)
            self.layoutChanged.emit()

    def change_selected_config_uuid(self, new_uuid: str):
        self._selected_configuration_uuid = new_uuid
        self._selected_report = None
        self._selected_configuration_reports = self.repository.find_reports_by_config_id(new_uuid)
        self.layoutChanged.emit()

    def on_double_click(self, index: PyQt6.QtCore.QModelIndex):
        if self._selected_configuration_uuid is None:
            return
        row = index.row()
        if (self._selected_report is None) and (row >= 0) and (row < len(self._selected_configuration_reports)):
            self._selected_report = self._selected_configuration_reports[row]
            self.layoutChanged.emit()
        pass

    def createReport(self):
        if self._selected_configuration_uuid is not None:
            report_uuid = self.repository.create_report(self._selected_configuration_uuid)
        else:
            raise ValueError("Cannot create report that is not attached to a configuration")

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        if self._selected_configuration_uuid is None:
            return 0
        if self._selected_report is None:  # viewing reports associated with configuration
            return len(self._selected_configuration_reports)
        else:
            return len(self._selected_report.events)

    def columnCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        has_config_uuid = (self._selected_configuration_uuid is not None)
        has_report_uuid = (self._selected_report is not None)
        if has_config_uuid and not has_report_uuid:  # viewing report-list
            return len(self.report_headers)
        if has_config_uuid and has_report_uuid:  # viewing event-list
            return len(self.event_headers)
        return 0

    def headerData(self, section: int, orientation: PyQt6.QtCore.Qt.Orientation, role: int = ...):
        if role == PyQt6.QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == orientation.Horizontal:
                has_config_uuid = (self._selected_configuration_uuid is not None)
                has_report_id = (self._selected_report is not None)
                if has_config_uuid and not has_report_id:  # viewing report-list
                    return self.report_headers[section]
                if has_config_uuid and has_report_id:  # viewing event-list
                    return self.event_headers[section]
            else:
                return str(section)
        return None

    def data(self, index, role=PyQt6.QtCore.Qt.ItemDataRole.DisplayRole):
        if role == PyQt6.QtCore.Qt.ItemDataRole.DisplayRole:
            row = index.row()

            has_config_uuid = (self._selected_configuration_uuid is not None)
            has_report_id = (self._selected_report is not None)
            if has_config_uuid and not has_report_id:
                sci = self._selected_configuration_reports[row]
                match (index.column()):
                    case 0:
                        return str(sci.start_date)
                    case 1:
                        return str(sci.end_date)
                    case 2:
                        return f"{sci.total_files_processed_succesfully}/{sci.total_files_processed}"
                    case 3:
                        return f"{sci.total_bytes_processed}"
            if has_config_uuid and has_report_id:
                sci = self._selected_report.events[row]

                match (index.column()):
                    case 0:
                        return str(sci.start_date)
                    case 1:
                        return str(sci.end_date)
                    case 2:
                        return sci.source
                    case 3:
                        return sci.destination
                    case 4:
                        return sci.status
                    case 5:
                        return sci.bytes
        return PyQt6.QtCore.QVariant()
