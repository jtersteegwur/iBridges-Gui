import logging
from datetime import datetime

import PyQt6.QtCore

import irodsConnector
import synchronisation.configuration_item
import synchronisation.reporting_repository
from synchronisation.reporting import SynchronisationStatusEvent


class FileUploader(PyQt6.QtCore.QObject):
    finished = PyQt6.QtCore.pyqtSignal()

    def __init__(self, ic: irodsConnector.manager.IrodsConnector,
                 config: synchronisation.configuration_item.SynchronisationConfigItem,
                 report_repo: synchronisation.reporting_repository.ReportingRepository):
        super(FileUploader, self).__init__()
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
            SynchronisationStatusEvent(start_date=datetime.now(), end_date=None, source=upload.source_path,
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
            self.report_repo.update_event(report_uuid, sync_result.source_path, datetime.now(), result,
                                          sync_result.source_file_size)
        logging.info("done uploading")
        report = self.report_repo.find_report_by_uuid(report_uuid)
        self.report_repo.recalculate_report_metadata(report, fill_end_date_when_no_event=True)
        self.finished.emit()
