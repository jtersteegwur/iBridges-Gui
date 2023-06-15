from typing import Optional

import PyQt6.QtCore

from synchronisation.reporting import SynchronisationStatusEvent, SynchronisationStatusReport
from synchronisation.reporting_repository import ReportingRepository

class SynchronisationStatusTableModel(PyQt6.QtCore.QAbstractTableModel):
    def __init__(self, repository: ReportingRepository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self._selected_configuration_uuid: Optional[str] = None
        self._selected_report: Optional[SynchronisationStatusReport] = None
        self._selected_configuration_reports: list[SynchronisationStatusReport] = []
        self.report_headers = ["StartTime", "EndTime", "Status", "Size"]
        self.event_headers = ["StartTime", "EndTate", "Source", "Destination", "Status", "Bytes"]
        self.repository.attach_obverver(self.on_repository_data_changed)

    def clear_selected_report(self):
        self._selected_report = None
        self._selected_configuration_uuid = None
        self._selected_configuration_reports = []
        self.layoutChanged.emit()

    def _is_viewing_reports_for(self, config_uuid):
        return self._selected_configuration_uuid == config_uuid \
               and self._selected_report is None

    def _is_viewing_events_for(self, report_uuid):
        return self._selected_configuration_uuid is not None \
               and self._selected_report is not None \
               and self._selected_report.uuid == report_uuid


    def on_repository_data_changed(self, config_uuid, report_uuid, events):
        if self._is_viewing_reports_for(config_uuid):
            self._refetch_selected_configuration_reports()
        self.layoutChanged.emit()

    def _refetch_selected_configuration_reports(self):
        self._selected_configuration_reports = self.repository.find_reports_by_config_id(self._selected_configuration_uuid)

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
            index_column = index.column()
            if has_config_uuid and not has_report_id:
                sci = self._selected_configuration_reports[row]
                return self.display_report_data(index_column, sci)
            if has_config_uuid and has_report_id:
                sci = self._selected_report.events[row]
                return self.display_event_data(index_column, sci)

    def display_event_data(self, index_column, sci):
        match index_column:
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
            case _:
                return PyQt6.QtCore.QVariant()

    def display_report_data(self, column, sci):
        match column:
            case 0:
                return str(sci.start_date)
            case 1:
                return str(sci.end_date)
            case 2:
                return f"{sci.total_files_processed_succesfully}/{sci.total_files_processed}"
            case 3:
                return f"{sci.total_bytes_processed}"
            case _:
                return PyQt6.QtCore.QVariant()
