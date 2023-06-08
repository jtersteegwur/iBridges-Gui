"""NPEC Rules tab.

"""
import logging
import sys
import os
import PyQt6.QtCore
import PyQt6.QtWidgets
import PyQt6.QtGui

from json import loads

import gui

# for an overview of the available rules and how to call them see:
#https://git.wur.nl/rdm-infrastructure/azure-instance/-/tree/main/playbooks/files/rules/core

# rdm_npec_create_experiment(){*experiment_path,*experiment_name);
# rdm_npec_finish_experiment(){*experiment_path,*experiment_name);

# ??rdm_npec_create_experiment_group(){*group_name);
# ??rdm_npec_get_users_list_from_experiment(){*group_name);

# rdm_npec_add_users_to_experiment(){*user_name,*group_name);
# rdm_npec_remove_users_from_experiment(){*user_name,*group_name);
# rdm_npec_remove_experiment_group(){*group_name);
# rdm_npec_set_permissions_to_experiment(){*experiment_name,*experiment_path,*permission_type);
# rdm_npec_set_user_permissions_to_experiment(){*experiment_name,*experiment_path,*permission_type,*experiment_user);
# rdm_npec_add_metadata_to_experiment(){*experiment_path,*experiment_name,*experiment_meta_attr,*experiment_meta_value,*experiment_meta_unit);

NPEC_modules = ['daale010', 'Field', 'Greenhouse', 'Cells']


class NPECRules(PyQt6.QtWidgets.QWidget, gui.ui_files.tabNPECRules.Ui_tabNPECRules):
    """GUI around the custom rules for NPEC.

    """

    def __init__(self, ic):
        """Initialize an iRODS browser view.

        Parameters
        ----------
        ic

        """
        self.ic = ic
        # Buffer to avoid exsesive calls to the server
        self.all_experiments = []
        self.selected_modules = NPEC_modules
        super().__init__()
        if getattr(sys, 'frozen', False):
            super().setupUi(self)
        else:
            PyQt6.uic.loadUi("gui/ui_files/tabNPECRules.ui", self)
        self.createExpButton.clicked.connect(self.create_experiment)
        self.finishExpButton.clicked.connect(self.finish_experiment)
        self.addUserButton.clicked.connect(self.add_user)

        # Set row and column size
        self.ExperimentTable.setColumnWidth(0, 60)
        self.ExperimentTable.setColumnWidth(1, 100)
        self.ExperimentTable.setColumnWidth(2, 100)
        # Last column expanding
        table_header= self.ExperimentTable.horizontalHeader()
        table_header.setSectionResizeMode(3, PyQt6.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.ExperimentTable.setIconSize(PyQt6.QtCore.QSize(50, 50))

        self.ModulesList.addItems(NPEC_modules)
        for index in range(self.ModulesList.count()):
            self.ModulesList.item(index).setFlags(self.ModulesList.item(index).flags() | PyQt6.QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            self.ModulesList.item(index).setCheckState(PyQt6.QtCore.Qt.CheckState.Checked)
        self.ModulesList.itemChanged.connect(self.module_list_callback)

        # Load icons
        self.running_icon = PyQt6.QtGui.QIcon()
        self.done_icon = PyQt6.QtGui.QIcon()
        running_iconpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'icons','running.png')
        done_iconpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'icons','finished.png')
        self.running_icon.addPixmap(PyQt6.QtGui.QPixmap(running_iconpath))
        self.done_icon.addPixmap(PyQt6.QtGui.QPixmap(done_iconpath))
        #self.running_icon = PyQt6.QtGui.QPixmap.fromImage("D:/aa_code/a_js_ibridges/gui/icons/running.png")
        #self.done_icons = PyQt6.QtGui.QPixmap.fromImage("D:/aa_code/a_js_ibridges/gui/icons/running.png")
        self.list_experiments()

    def module_list_callback(self, item):
        # A few simple loops to implement the All functionality
        self.ModulesList.blockSignals(True)
        state = item.checkState()
        if item.text() == 'All':
            for index in range(self.ModulesList.count()):
                module = self.ModulesList.item(index)
                if state == PyQt6.QtCore.Qt.CheckState.Checked:
                    module.setCheckState(PyQt6.QtCore.Qt.CheckState.Checked)
                else:
                    module.setCheckState(PyQt6.QtCore.Qt.CheckState.Unchecked)
        elif state == PyQt6.QtCore.Qt.CheckState.Unchecked:
            # Uncheck all
            self.ModulesList.item(0).setCheckState(PyQt6.QtCore.Qt.CheckState.Unchecked)
        
        # Loop over modules, set all if others are checked
        all_checked = True
        self.selected_modules = []
        for index in range(self.ModulesList.count()):
            if self.ModulesList.item(index).text() == 'All':
                continue
            elif self.ModulesList.item(index).checkState() == PyQt6.QtCore.Qt.CheckState.Unchecked:
                all_checked = False
            else:
                self.selected_modules.append(self.ModulesList.item(index).text())
        if all_checked is True:
            self.ModulesList.item(0).setCheckState(PyQt6.QtCore.Qt.CheckState.Checked)
        self.ModulesList.blockSignals(False)
        self.update_experiment_ui()

    def create_exp_callback(self, module_name, exp_name):
        # TODO: implement module name
        print(module_name)
        print(exp_name)
        params = {'*experiment_path': f'/RDMtest/home/daale010/{exp_name}', '*experiment_name':exp_name}
        std_out, std_err = self.ic.execute_rule(body = 'irods_rdm_npec_create_experiment_2', params = params, rule_type = 'irods_rule_language')
        self.vizualise_rule_output(std_out, std_err)
        # stdout:
        # '/RDMtest/home/daale010/9\n9\nThe experiment 9 has been CREATED\nThe experiment NOW EXISTS with ID 24175\nMETADATA has been ADDED with the following content:\n  (1)(attr,value): collection_type is experiment\n  (2)(attr,value): experiment_status is started\n#----------------------------------------------------------------------------------------------------------------------------------------#'
        #rdm_npec_create_experiment_group


    def create_experiment(self):
        """ open pop up to ask for user input """
        create_exp_window = gui.popupWidgets.npecCreateExperiment(NPEC_modules)
        create_exp_window.finished.connect(self.create_exp_callback)
        create_exp_window.exec()


    def finish_experiment(self):
        " Set experiment status to finished, this automatically makes the experiment read only "
        #rows=[idx.row() for idx in self.selectionModel().selectedIndexes()]
        for index in self.ExperimentTable.selectionModel().selectedRows():
            module_name = self.ExperimentTable.item(index.row(), 1).text()
            exp_name = self.ExperimentTable.item(index.row(), 2).text()
            print(exp_name)
            params = {'*experiment_path': f'{module_name}', '*experiment_name':exp_name}
            std_out, std_err = self.ic.execute_rule(body = 'rdm_npec_finish_experiment', params = params, rule_type = 'irods_rule_language')
            self.vizualise_rule_output(std_out, std_err)
            self.list_experiments()


    def list_experiments(self):
        # List all the experiments on the server
        std_out, std_err = self.ic.execute_rule(body='rdm_npec_get_experiment_list', rule_type='irods_rule_language')
        self.vizualise_rule_output(std_out, std_err, False)  
        self.all_experiments = loads(std_out)
        self.update_experiment_ui()

    def add_user(self):
        # Add user to an existing experiment
        for index in self.ExperimentTable.selectionModel().selectedRows():
            module_name = self.ExperimentTable.item(index.row(), 1).text()
        # TODO: retreive groupname
        groupname = ""
        username, ok = PyQt6.QtWidgets.QInputDialog.getText(self, 'Add user', 'Username:')
        if ok:
            params = {'*user_name': username, '*group_name': groupname}
            std_out, std_err = self.ic.execute_rule(body = 'rdm_npec_add_users_to_experiment', params = params, rule_type = 'irods_rule_language')
            self.vizualise_rule_output(std_out, std_err, False)  


    def update_experiment_ui(self):
        # First filtering the experiment and updating the UI once is faster
        showing_experiments = []
        for experiment in self.all_experiments:
            if experiment['experiment_path'].split('/')[-2] in self.selected_modules:
                showing_experiments.append(experiment)
        self.ExperimentTable.setRowCount(len(showing_experiments))
        for row, experiment in enumerate(showing_experiments):
            status_item = PyQt6.QtWidgets.QTableWidgetItem()
            if experiment['experiment_status'] == 'started':
                status_item.setIcon(self.running_icon)
            else:
                status_item.setIcon(self.done_icon)
            self.ExperimentTable.setItem(row, 0, status_item)
            self.ExperimentTable.setItem(row, 1, PyQt6.QtWidgets.QTableWidgetItem(experiment['experiment_path']))
            self.ExperimentTable.setItem(row, 2, PyQt6.QtWidgets.QTableWidgetItem(experiment['experiment_name']))
            self.ExperimentTable.setItem(row, 3, PyQt6.QtWidgets.QTableWidgetItem(','.join(experiment['experiment_users'])))
            self.ExperimentTable.setRowHeight(row, 50)


    def vizualise_rule_output(self, std_out, std_err, show_std_out=True):
        "Helper function to vizualise the output of a rule"
        if std_err != '':
            PyQt6.QtWidgets.QMessageBox.critical(None,
                                "Error", std_err,
                                PyQt6.QtWidgets.QMessageBox.StandardButton.Close)
        elif show_std_out:
            PyQt6.QtWidgets.QMessageBox.critical(None,
                                "Info", std_out,
                                PyQt6.QtWidgets.QMessageBox.StandardButton.Close)