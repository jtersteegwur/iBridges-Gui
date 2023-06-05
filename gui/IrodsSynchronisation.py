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
import irodsConnector

from synchronisation.reporting import SynchronisationStatusEvent, SynchronisationStatusReport


class Uploader(PyQt6.QtCore.QObject):
    finished = PyQt6.QtCore.pyqtSignal()

    def __init__(self, ic: irodsConnector.manager.IrodsConnector,
                 config: synchronisation.configuration_item.SynchronisationConfigItem,
                 report_repo: synchronisation.reporting_repository.ReportingRepository):
        super(Uploader, self).__init__()
        self.cancelled = False
        self.irods_connector = ic
        self.configuration = config
        self.report_repo = report_repo

    @PyQt6.QtCore.pyqtSlot()
    def run(self):
        logging.debug("started diffing between %s and %s", self.configuration.local, self.configuration.remote)
        upload_diff = self.irods_connector._data_op.get_diff_upload(self.configuration.local, self.configuration.remote)
        logging.debug("done diffing between %s and %s", self.configuration.local, self.configuration.remote)
        logging.debug("create report for %s", self.configuration.uuid)
        report_uuid: str = self.report_repo.create_report(self.configuration.uuid)
        events = [
            SynchronisationStatusEvent(start_date=datetime.datetime.now(), end_date=None, source=upload.source_path,
                                       destination=upload.target_path, status='Pending', bytes=0) for upload in
            upload_diff]
        self.report_repo.add_events_to_report(report_uuid, events)
        resource_name = 'hot_1'
        minimal_free_space_on_server = 0
        check_free_space = True
        generator = self.irods_connector._data_op.upload_data_with_sync_result_generator(upload_diff, resource_name,
                                                                                         minimal_free_space_on_server,
                                                                                         check_free_space)
        logging.info("start uploading")
        for result, sync_result in generator:
            self.report_repo.update_event(report_uuid, sync_result.source_path, datetime.datetime.now(), result,
                                          sync_result.source_file_size)
        logging.info("done uploading")
        report = self.report_repo.find_report_by_uuid(report_uuid)
        self.report_repo.recalculate_report_metadata(report, fill_end_date_when_no_event=True)
        self.finished.emit()


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
        self._setup_configuration_view_and_buttons()
        self._setup_sync_event_view_and_buttons()

        self._setup_animation_ticker()
        self._upload_thread_dict = dict()
        self._uploader_dict = dict()
        self.timer_dict = dict()
        self.reinitialise_scheduling_timers()
        # self.uploader_thread = PyQt6.QtCore.QThread()
        self.ui = None
        self.ic = ic
        self.configuration_view.resizeColumnsToContents()
        self.enable_disable_buttons()

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
            pass

    def _setup_animation_ticker(self):
        self.ticker_thread = PyQt6.QtCore.QThread()
        self.ticker = AnimationTicker()
        self.ticker.moveToThread(self.ticker_thread)
        self.destroyed.connect(self.ticker.stop)
        self.ticker_thread.started.connect(self.ticker.run)
        # TODO: this could be optimised, only connect when needed to
        self.ticker.text_animation_tick.connect(self.configuration_view.model().animation_tick)
        self.ticker_thread.start()

    def start_uploader(self, config_uuid:str = None):
        if config_uuid is None:
            row = self.configuration_view.currentIndex().row()
            config = self.configuration_repository.get_by_index(row)
        else:
            config = self.configuration_repository.get_by_id(config_uuid)
        if self._upload_thread_dict.get(config.uuid) is None:
            logging.info("starting upload %s", config.uuid)
            uploader = Uploader(self.ic, config=config, report_repo=self.reporting_repository)
            uploader_thread = PyQt6.QtCore.QThread()
            self._uploader_dict[config.uuid] = uploader
            self._upload_thread_dict[config.uuid] = uploader_thread
            uploader_thread.started.connect(uploader.run)
            uploader_thread.started.connect(lambda: self.configuration_view.model().enable_text_animation(config.uuid))
            uploader.finished.connect(lambda: self.configuration_view.model().disable_text_animation(config.uuid))
            uploader.finished.connect(lambda: self.clean_up_uploader(config.uuid))
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
        self.configuration_view.selectionModel().selectionChanged.connect(lambda: self.enable_disable_buttons())
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
        self.force_trigger_button.clicked.connect(lambda: self.start_uploader(None))

    def on_configuration_changed(self):
        self.configuration_view.resizeColumnsToContents()
        self.enable_disable_buttons()

    def enable_disable_buttons(self):
        configuration_row_index = self.configuration_view.currentIndex().row()
        config_view_has_selected_items = configuration_row_index >= 0
        config = self.configuration_repository.get_by_index(
            configuration_row_index) if config_view_has_selected_items else None
        self.update_configuration_button.setEnabled(config_view_has_selected_items)
        self.delete_configuration_button.setEnabled(config_view_has_selected_items)
        self.force_trigger_button.setEnabled(
            config_view_has_selected_items and config.uuid not in self._upload_thread_dict.keys())
        self.update_configuration_button.setStyleSheet(self.update_configuration_button.styleSheet())
        self.delete_configuration_button.setStyleSheet(self.delete_configuration_button.styleSheet())
        self.force_trigger_button.setStyleSheet(self.force_trigger_button.styleSheet())

    def on_config_selection_changed(self):
        configuration_row_index = self.configuration_view.currentIndex().row()
        config_view_has_selected_items = configuration_row_index >= 0
        config = self.configuration_repository.get_by_index(
            configuration_row_index) if config_view_has_selected_items else None
        if config_view_has_selected_items:
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
        self.animation_tick_counter = 0
        self._animation_set = set()

    def enable_text_animation(self, config_id: str):
        logging.info("start textanimation")
        self._animation_set.add(config_id)

    def disable_text_animation(self, config_id: str):
        logging.info("stop textanimation")
        if config_id in self._animation_set:
            self._animation_set.remove(config_id)

    def animation_tick(self, tickcounter):
        self.animation_tick_counter = tickcounter
        self.layoutChanged.emit()

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
            if sci.uuid in self._animation_set:
                bla = [
                    'loading',
                    'loading.',
                    'loading..',
                    'loading...',
                    'loading..',
                    'loading.'
                ]
                current_frame_text = bla[self.animation_tick_counter % len(bla)]
                return current_frame_text
            else:
                now = datetime.datetime.now()
                next_moment = croniter.croniter(sci.cron, now).get_next(datetime.datetime)
                str_next_moment = next_moment.strftime("%m/%d/%Y, %H:%M:%S")
                return str_next_moment
            # return f'Scheduled for {str_next_moment}'
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
