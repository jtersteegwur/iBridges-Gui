import logging
from datetime import datetime

import PyQt6.QtCore
import croniter

from synchronisation.configuration_item import SynchronisationConfigItem
from synchronisation.configuration_repository import ConfigRepository


class SynchronisationConfigurationTableModel(PyQt6.QtCore.QAbstractTableModel):
    def __init__(self, config_repository: ConfigRepository, parent=None):
        super().__init__(parent)
        self._display_loading = set()
        self.config_repository = config_repository
        config_repository.attach_obverver(self.on_data_changed)

    def display_loading(self, config_uuid):
        self._display_loading.add(config_uuid)

    def remove_display_loading(self, config_uuid):
        self._display_loading.remove(config_uuid)

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

    def determineState(self, sci: SynchronisationConfigItem):
        if sci.uuid in self._display_loading:
            return "Working"
        now = datetime.now()
        next_moment = croniter.croniter(sci.cron, now).get_next(datetime)
        str_next_moment = next_moment.strftime("%m/%d/%Y, %H:%M:%S")
        return str_next_moment
        # return f'Scheduled for {str_next_moment}'
