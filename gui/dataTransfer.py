"""Data transfer dialog.

"""
import datetime
import logging
import os
import sys

from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6 import QtCore
from PyQt6.QtGui import QMovie
from PyQt6.uic import loadUi

from gui.ui_files.dataTransferState import Ui_dataTransferState
import utils

from irodsConnector.manager import IrodsConnector

class dataTransfer(QDialog, Ui_dataTransferState):
    """

    """
    finished = pyqtSignal(bool, object)

    def __init__(self, ic: IrodsConnector, upload, localFsPath, irodsColl, irodsTreeIdx=None, resource=None):
        """

        Parameters
        ----------
        ic
        upload
        localFsPath
        irodsColl
        irodsTreeIdx
        resource
        """
        super().__init__()
        if getattr(sys, 'frozen', False):
            super().setupUi(self)
        else:
            loadUi("gui/ui_files/dataTransferState.ui", self)
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.ic = ic
        self.localFsPath = localFsPath
        self.coll = irodsColl
        self.TreeInd = irodsTreeIdx
        self.upload = upload
        self.resource = resource
        self.addFiles = []
        self.addSize = 0
        self.diff = []
        self.sync_list : list[utils.sync_result.SyncResult]= []
        self.updateFiles = []
        self.updateSize = 0
        self.force = ic.ienv.get('force_unknown_free_space', False)
        self.statusLbl.setText("Loading")
        self.cancelBtn.clicked.connect(self.cancel)
        self.confirmBtn.clicked.connect(self.confirm)
        # Upload
        if self.upload:
            self.confirmBtn.setText("Upload")
        else:
            self.confirmBtn.setText("Download")        
        self.confirmBtn.setEnabled(False)

        self.loading_movie = QMovie("gui/icons/loading_circle.gif")
        self.loadingLbl.setMovie(self.loading_movie)
        self.loading_movie.start()

        # Get information in separate thread
        self.thread = QThread()
        self.worker = getDataState(self.ic, localFsPath, irodsColl, upload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.updLabels.connect(self.updLabels)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.updateUiWithDataState)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.show()

    def cancel(self):
        print("Thread stopped")
        self.finished.emit(False, None)
        # if thread is still running
        try:
            self.thread.exit(1)
        except:
            pass
        self.close()

    def closeAfterUpDownl(self):
        self.finished.emit(True, self.TreeInd)
        self.close() 

    def confirm(self):
        total_size = self.updateSize + self.addSize
        self.loading_movie.start()
        self.loadingLbl.setHidden(False)
        self.confirmBtn.setEnabled(False)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        if self.upload:
            self.statusLbl.setText(
                f'Uploading... this might take a while. \nStarted {now}')
        else:
            self.statusLbl.setText(
                f'Downloading... this might take a while. \nStarted {now}')
        self.thread = QThread()
        if len(self.sync_list) == 0:
            self.statusLbl.setText("Nothing to update.")
            self.loading_movie.stop()
            self.loadingLbl.setHidden(True)
        else:
            self.worker = UpDownload(
                self.ic, self.upload, self.localFsPath, self.coll,
                total_size, self.resource, self.diff, self.addFiles,
                self.force, self.sync_list)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.upDownLoadFinished)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()

    def updLabels(self, numAdd, numDiff):
        """Callback for the getDataSize worker

        Parameters
        ----------
        numAdd
        numDiff

        """
        self.numDiffLabel.setText(f"{numDiff}")
        self.numAddLabel.setText(f"{numAdd}")

    def updateUiWithDataState(self, addFiles, diff, addSize, updateSize, sync_list: list[utils.sync_result.SyncResult]):
        """Callback for the getDataSize worker

        Parameters
        ----------
        addFiles
        diff
        addSize
        updateSize
        sync_list

        Returns
        -------

        """
        # TODO fix handling of updateSize and addSize as ints
        self.updateSize = updateSize
        print(int(addSize), int(updateSize))
        # checksumSizeStr = self.bytesToStr(updateSize)
        self.ChecksumSizeLbl.setText(utils.utils.bytes_to_str(int(updateSize)))
        self.diff = diff
        self.sync_list = sync_list

        self.addSize = addSize
        # newSizeStr = self.bytesToStr(addSize)
        self.newFSizeLbl.setText(utils.utils.bytes_to_str(int(addSize)))
        self.addFiles = addFiles

        self.loading_movie.stop()
        self.loadingLbl.setHidden(True)
        self.statusLbl.setText("")
        self.confirmBtn.setEnabled(True)

    def upDownLoadFinished(self, status, statusmessage):
        """

        Parameters
        ----------
        status
        statusmessage

        Returns
        -------

        """
        self.loading_movie.stop()
        self.loadingLbl.setHidden(True)
        if status:
            # remove callback
            self.confirmBtn.disconnect()
            self.confirmBtn.setText("Close")
            self.confirmBtn.setEnabled(True)
            self.confirmBtn.clicked.connect(self.closeAfterUpDownl)
            self.statusLbl.setText("Update complete.")
        else:
            self.statusLbl.setText(statusmessage)
            print(statusmessage)
            self.confirmBtn.setText("Retry")
            self.confirmBtn.setEnabled(True)
            if "No size set on iRODS resource" in statusmessage:
                self.force = True
                self.confirmBtn.setText("Retry and force upload?")


class getDataState(QObject):
    """Background worker to load the menu.

    """
    # Number of files
    updLabels = pyqtSignal(int, int)
    # Lists with size in bytes
    finished = pyqtSignal(list, list, str, str, list)

    def __init__(self, ic: IrodsConnector, localFsPath, coll, upload):
        """

        Parameters
        ----------
        ic
        localFsPath
        coll
        upload
        """
        super().__init__()
        self.ic = ic
        self.localFsPath = localFsPath
        self.coll = coll
        self.upload = upload

    def run(self):
        # Diff
        diff, only_fs, only_irods = [], [], []
        upload_diff = []
        try:
            if self.upload:
                # Data is placed inside of coll, check if dir or file is inside
                new_path = self.coll.path + "/" + os.path.basename(self.localFsPath)
                total_new_files = 0
                total_different_files = 0
                if os.path.isdir(self.localFsPath):
                    if self.ic.collection_exists(new_path):
                        #TODO figure out if this ever different from new_path
                        sub_coll_path = self.ic.get_collection(new_path).path
                    else:
                        sub_coll_path = new_path
                    upload_diff: list[utils.sync_result.SyncResult] = self.ic.get_diff_upload(self.localFsPath, sub_coll_path)
                    total_new_files = sum(1 for u_diff in upload_diff if
                               u_diff.file_sync_method == utils.sync_result.FileSyncMethod.CREATE)
                    total_different_files = len(upload_diff) - total_new_files
                elif os.path.isfile(self.localFsPath):
                    upload_diff = self.ic.get_diff_upload(self.localFsPath, new_path)
                    total_new_files = sum(1 for u_diff in upload_diff if
                                          u_diff.file_sync_method == utils.sync_result.FileSyncMethod.CREATE)
                    total_different_files = len(upload_diff) - total_new_files
                self.updLabels.emit(total_new_files, total_different_files)
            else:
                # Data is placed inside fsDir, check if obj or coll is inside
                new_path = os.path.join(self.localFsPath, self.coll.name)
                fs_path = new_path
                if self.ic.collection_exists(self.coll.path):
                    if not os.path.isdir(new_path):
                        fs_path = None
                    (diff, only_fs, only_irods) = self.ic.diff_irods_localfs( self.coll, fs_path, scope="checksum")
                    download_diff = self.ic.get_diff_download(new_path, self.coll.path)
                    pass
                else:
                    (diff, only_fs, only_irods) = self.ic.diff_obj_file(self.coll.path, new_path, scope="checksum")
                    download_diff = self.ic.get_diff_download(fs_path, self.coll.path)
                    pass
                total_new_files = sum(1 for d_diff in download_diff if
                                      d_diff.file_sync_method == utils.sync_result.FileSyncMethod.CREATE)
                total_different_files = len(download_diff) - total_new_files
                self.updLabels.emit(total_new_files, total_different_files)
        except Exception as exc:
            logging.exception("dataTransfer.py: Error in getDataState")

        # Get size 
        if self.upload:
            update_size = 0
            add_size = 0
            for item in upload_diff:
                if item.file_sync_method == utils.sync_result.FileSyncMethod.CREATE:
                    add_size += item.source_file_size
                elif item.file_sync_method == utils.sync_result.FileSyncMethod.UPDATE:
                    update_size += item.source_file_size
            self.finished.emit(only_fs, diff, str(add_size), str(update_size), upload_diff)
        else:
            irodsDiffFiles = [d[0] for d in diff]
            update_size = self.ic.get_irods_size(irodsDiffFiles)
            onlyIrodsFullPath = only_irods.copy()
            for i in range(len(onlyIrodsFullPath)):
                if not only_irods[i].startswith(self.coll.path):
                    onlyIrodsFullPath[i] = f'{self.coll.path}/{only_irods[i]}'
            add_size = self.ic.get_irods_size(onlyIrodsFullPath)
            self.finished.emit(only_irods, diff, str(add_size), str(update_size),download_diff)


class UpDownload(QObject):
    """Background worker for the up/download

    """
    finished = pyqtSignal(bool, str)

    def __init__(self, ic : IrodsConnector, upload, localFS, Coll, totalSize, resource, diff, addFiles, force, sync_list):
        """

        Parameters
        ----------
        ic
        upload
        localFS
        Coll
        totalSize
        resource
        diff
        addFiles
        force
        """
        super().__init__()
        self.ic : IrodsConnector= ic
        self.upload = upload
        self.localFS = localFS
        self.Coll = Coll
        self.totalSize = totalSize
        self.resource = resource
        self.diff = diff
        self.addFiles = addFiles
        # TODO prefer setting here?
        self.sync_list = sync_list
        self.force = ic.ienv.get('force_unknown_free_space', force)

    def run(self):    
        try:
            if self.upload:
                self.ic.upload_data_using_sync_result(self.sync_list, self.resource, int(self.totalSize), not self.force)
                self.finished.emit(True, "Upload finished")
            else:
                self.ic.download_data_using_sync_result(self.sync_list,1024**3, True)
                self.finished.emit(True, "Download finished")
        except Exception as error:
            logging.info(repr(error))
            self.finished.emit(False, str(error))
