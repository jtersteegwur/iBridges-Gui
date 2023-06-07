import sys

import PyQt6.uic

from PyQt6.QtWidgets import QDialog,QToolTip
from PyQt6.QtCore import QPoint
from gui.ui_files.dialogCreateUpdateSynchronisation import Ui_Dialog
from synchronisation.configuration_item import SynchronisationConfigItem
from irods.exception import CollectionDoesNotExist, DataObjectDoesNotExist
from os import path
from irodsConnector.manager import IrodsConnector
from croniter import croniter


class CreateUpdateSynchronisationConfigDialog(Ui_Dialog):
    def __init__(self, irods_connector: IrodsConnector, parent: QDialog):
        super().__init__()
        if getattr(sys, 'frozen', False):
            super().setupUi(self)
        else:
            PyQt6.uic.loadUi("gui/ui_files/dialogCreateUpdateSynchronisation.ui")
        self.setupUi(parent)
        self.ic = irods_connector
        self.parent = parent
        self.comboBox.currentIndexChanged.connect(lambda: self.dialogSyncComboAndInput('combobox'))
        self.cronInput.textChanged.connect(lambda: self.dialogSyncComboAndInput('text'))
        self.browseButton.clicked.connect(lambda: self.dialogOpenfileDialog(self.localInput))
        self.buttonBox.accepted.connect(lambda: self.dialogValidateAndAcceptNewConfig())

    def build_synchronisationconfigitem(self, uuid = None):
        result = SynchronisationConfigItem(type=self.dialogGetType(),
                                           local=self.localInput.toPlainText(),
                                           remote=self.remoteInput.toPlainText(),
                                           cron=self.cronInput.toPlainText(),
                                           uuid=uuid)
        return result


    @classmethod
    def create_or_update(cls,ic : IrodsConnector, sci: SynchronisationConfigItem, parent):
        this_dialog = cls(irods_connector=ic,parent=parent)
        this_dialog.localInput.setPlainText(sci.local)
        this_dialog.remoteInput.setPlainText(sci.remote)
        this_dialog.cronInput.setPlainText(sci.cron)
        parent_exec = parent.exec()
        if parent_exec == QDialog.DialogCode.Accepted:
            return this_dialog.build_synchronisationconfigitem(sci.uuid)
        else:
            return None


    def dialogGetType(self):
        return "Scheduled upload"

    def dialogOpenfileDialog(self, target):
        dialog = PyQt6.QtWidgets.QFileDialog()
        # option = PyQt6.QtWidgets.QFileDialog.Option.ShowDirsOnly
        file_select = PyQt6.QtWidgets.QFileDialog.getExistingDirectory(dialog, "Select folder")
        if file_select and '' != file_select:
            target.setPlainText(path.normpath(file_select))

    def dialogValidateAndAcceptNewConfig(self):
        resulting_config = self.build_synchronisationconfigitem()
        config_valid = self.validate_config(resulting_config)
        if config_valid:
            self.parent.accept()

    def validate_config(self, resulting_config):
        remote_valid = False
        try:
            remote_permission = self.ic.get_permissions(resulting_config.remote)
            own_and_write_perms = list(filter(lambda perm: perm.user_name == self.ic.session.username
                                                           and (perm.access_name in {'own', 'write'}),
                                              remote_permission))
            remote_valid = len(own_and_write_perms) >= 1
        except CollectionDoesNotExist:
            remote_valid = False
        except DataObjectDoesNotExist:
            remote_valid = False

        local_valid = path.exists(resulting_config.local)
        cron_valid = croniter.is_valid(resulting_config.cron)

        if not remote_valid:
            self._display_text_on_widget(self.remoteInput, "This path is not accessible by this user", 5000)
        if not local_valid:
            self._display_text_on_widget(self.localInput, "This path does not exist", 5000)
        if not cron_valid:
            self._display_text_on_widget(self.cronInput, "Invalid Cron notation", 5000)
        config_valid = local_valid and cron_valid and remote_valid
        return config_valid

    def _display_text_on_widget(self, widget, message, msec_show_time):
        q_point = QPoint(0, 0)
        QToolTip.showText(widget.mapToGlobal(q_point), message, msecShowTime=msec_show_time)

    def _change_input_blocking_signals(self, value: str):
        self.cronInput.blockSignals(True)
        self.cronInput.setText(value)
        self.cronInput.blockSignals(False)

    def _change_combobox_blocking_signals(self, index: int):
        self.comboBox.blockSignals(True)
        self.comboBox.setCurrentIndex(index)
        self.comboBox.blockSignals(False)

    def dialogSyncComboAndInput(self, initiator):
        index = self.comboBox.currentIndex()

        text = self.cronInput.toPlainText()
        if 'text' == initiator:
            match text:
                case '0 0 * * *':
                    self._change_combobox_blocking_signals(0)
                case '0 13 * * *':
                    self._change_combobox_blocking_signals(1)
                case _:
                    self._change_combobox_blocking_signals(2)
        elif 'combobox' == initiator:
            match index:
                case 0:
                    self._change_input_blocking_signals('0 0 * * *')
                case 1:
                    self._change_input_blocking_signals('0 13 * * *')
