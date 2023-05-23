"""Created by: PyQt6 UI code generator from the corresponding UI file

WARNING: Any manual changes made to this file will be lost when pyuic6 is
run again.  Do not edit this file unless you know what you are doing.
"""


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_tabAmberData(object):
    def setupUi(self, tabAmberData):
        tabAmberData.setObjectName("tabAmberData")
        tabAmberData.resize(640, 532)
        tabAmberData.setStyleSheet("QWidget\n"
"{\n"
"    color: rgb(86, 184, 139);\n"
"    background-color: rgb(54, 54, 54);\n"
"    selection-background-color: rgb(58, 152, 112);\n"
"}\n"
"\n"
"QTreeView\n"
"{\n"
"background-color: rgb(85, 87, 83);\n"
"}\n"
"\n"
"QLabel#jobSubmitLabel\n"
"{\n"
"color: rgb(217, 174, 23);\n"
"}\n"
"\n"
"QLabel#importLabel\n"
"{\n"
"color: rgb(217, 174, 23);\n"
"}\n"
"")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(tabAmberData)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_2 = QtWidgets.QLabel(tabAmberData)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_3.addWidget(self.label_2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.amberToken = QtWidgets.QLineEdit(tabAmberData)
        self.amberToken.setObjectName("amberToken")
        self.verticalLayout_3.addWidget(self.amberToken)
        self.irodsZoneLabel1 = QtWidgets.QLabel(tabAmberData)
        self.irodsZoneLabel1.setText("")
        self.irodsZoneLabel1.setObjectName("irodsZoneLabel1")
        self.verticalLayout_3.addWidget(self.irodsZoneLabel1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.irodsUploadTree = QtWidgets.QTreeView(tabAmberData)
        self.irodsUploadTree.setMinimumSize(QtCore.QSize(0, 150))
        self.irodsUploadTree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.irodsUploadTree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.irodsUploadTree.setObjectName("irodsUploadTree")
        self.horizontalLayout.addWidget(self.irodsUploadTree)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(tabAmberData)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.glossaryBox = QtWidgets.QComboBox(tabAmberData)
        self.glossaryBox.setObjectName("glossaryBox")
        self.horizontalLayout_2.addWidget(self.glossaryBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.submitButton = QtWidgets.QPushButton(tabAmberData)
        font = QtGui.QFont()
        font.setBold(True)
        self.submitButton.setFont(font)
        self.submitButton.setObjectName("submitButton")
        self.verticalLayout.addWidget(self.submitButton)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem3)
        self.jobSubmitLabel = QtWidgets.QLabel(tabAmberData)
        self.jobSubmitLabel.setStyleSheet("")
        self.jobSubmitLabel.setText("")
        self.jobSubmitLabel.setObjectName("jobSubmitLabel")
        self.verticalLayout_3.addWidget(self.jobSubmitLabel)
        spacerItem4 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem4)
        self.label_3 = QtWidgets.QLabel(tabAmberData)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_3.addWidget(self.label_3)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem5)
        self.irodsZoneLabel2 = QtWidgets.QLabel(tabAmberData)
        self.irodsZoneLabel2.setText("")
        self.irodsZoneLabel2.setObjectName("irodsZoneLabel2")
        self.verticalLayout_3.addWidget(self.irodsZoneLabel2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.irodsDownloadTree = QtWidgets.QTreeView(tabAmberData)
        self.irodsDownloadTree.setMinimumSize(QtCore.QSize(0, 150))
        self.irodsDownloadTree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.irodsDownloadTree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.irodsDownloadTree.setObjectName("irodsDownloadTree")
        self.horizontalLayout_3.addWidget(self.irodsDownloadTree)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(tabAmberData)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.jobBox = QtWidgets.QComboBox(tabAmberData)
        self.jobBox.setObjectName("jobBox")
        self.horizontalLayout_4.addWidget(self.jobBox)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.refreshJobsButton = QtWidgets.QPushButton(tabAmberData)
        self.refreshJobsButton.setObjectName("refreshJobsButton")
        self.verticalLayout_2.addWidget(self.refreshJobsButton)
        spacerItem6 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_2.addItem(spacerItem6)
        self.previewButton = QtWidgets.QPushButton(tabAmberData)
        self.previewButton.setObjectName("previewButton")
        self.verticalLayout_2.addWidget(self.previewButton)
        self.importDataButton = QtWidgets.QPushButton(tabAmberData)
        font = QtGui.QFont()
        font.setBold(True)
        self.importDataButton.setFont(font)
        self.importDataButton.setObjectName("importDataButton")
        self.verticalLayout_2.addWidget(self.importDataButton)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.previewBrowser = QtWidgets.QTextBrowser(tabAmberData)
        self.previewBrowser.setObjectName("previewBrowser")
        self.verticalLayout_3.addWidget(self.previewBrowser)
        self.importLabel = QtWidgets.QLabel(tabAmberData)
        self.importLabel.setText("")
        self.importLabel.setObjectName("importLabel")
        self.verticalLayout_3.addWidget(self.importLabel)
        spacerItem7 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem7)

        self.retranslateUi(tabAmberData)
        QtCore.QMetaObject.connectSlotsByName(tabAmberData)

    def retranslateUi(self, tabAmberData):
        _translate = QtCore.QCoreApplication.translate
        tabAmberData.setWindowTitle(_translate("tabAmberData", "Form"))
        self.label_2.setText(_translate("tabAmberData", "Choose data to send to Amberscript:"))
        self.amberToken.setText(_translate("tabAmberData", "Replace with token"))
        self.label.setText(_translate("tabAmberData", "Use Glossary"))
        self.submitButton.setText(_translate("tabAmberData", "Submit to Amber"))
        self.label_3.setText(_translate("tabAmberData", "Download results from Amberscript"))
        self.label_4.setText(_translate("tabAmberData", "Choose job"))
        self.refreshJobsButton.setText(_translate("tabAmberData", "Refresh Jobs"))
        self.previewButton.setText(_translate("tabAmberData", "Preview"))
        self.importDataButton.setText(_translate("tabAmberData", "Import"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    tabAmberData = QtWidgets.QWidget()
    ui = Ui_tabAmberData()
    ui.setupUi(tabAmberData)
    tabAmberData.show()
    sys.exit(app.exec())
