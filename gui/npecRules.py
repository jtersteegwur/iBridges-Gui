"""NPEC Rules tab.

"""
import logging
import sys

import PyQt6.QtWidgets

import gui


class npecRules(PyQt6.QtWidgets.QWidget, gui.ui_files.tabNPECRules.Ui_tabNPECRules):
    """GUI around the custom rules for NPEC.

    """
    def __init__(self, ic):
        """Initialize an iRODS browser view.

        Parameters
        ----------
        ic

        """
        self.ic = ic
        super().__init__()
        if getattr(sys, 'frozen', False):
            super().setupUi(self)
        else:
            PyQt6.uic.loadUi("gui/ui_files/tabNPECRules.ui", self)
        