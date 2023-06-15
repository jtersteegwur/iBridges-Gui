import utils.utils
import os
import json
import uuid
import datetime
from synchronisation.reporting import SynchronisationStatusEvent, SynchronisationStatusReport

DEFAULT_EMPTY_SYNCHRONISATION_REPORTING_CONFIG = {
                    'comment': "this file is programmatically controlled by ibridges, modification by hand might "
                               "result in undefined behavior",
                    'reports': []}


class ReportingRepository:
    def __init__(self, events_path: str = None):
        if events_path is None:
            ibridges_path: utils.utils.LocalPath = utils.utils.LocalPath(os.path.join('~', '.ibridges')).expanduser()
            events_path = ibridges_path.joinpath("synchronisation_events.json")

        self.events_path = events_path
        self._data: list[SynchronisationStatusReport] = []
        if os.path.isfile(events_path):
            with open(self.events_path, "r") as file_obj:
                try:
                    load = json.load(file_obj)
                    self._data = [self.json_dict_to_report(report)for report in load.get("reports")]
                except (json.JSONDecodeError, KeyError) as err:
                    raise ValueError(f"Error loading {self.events_path}, please fix or remove it.", err)
        else:
            with open(self.events_path, "x") as file_obj:
                json.dump(DEFAULT_EMPTY_SYNCHRONISATION_REPORTING_CONFIG, file_obj, indent=6)

        self.observers = []

    def attach_obverver(self, observer):
        self.observers.append(observer)

    def detach_obverver(self, observer):
        self.observers.remove(observer)

    def notify_reporting_changed(self, config_uuid: str, report_uuid :str, events: set[str]):
        self.write_current_reporting_to_file(config_uuid, report_uuid, events)
        for obs in self.observers:
            obs(config_uuid, report_uuid, events)

    def json_dict_to_event(self, json_dict:dict):
        return SynchronisationStatusEvent(
            start_date=datetime.datetime.fromisoformat(json_dict.get('start_date')),
            end_date=datetime.datetime.fromisoformat(json_dict.get('end_date'))if json_dict.get('end_date') is not None else None,
            source=json_dict.get('source'),
            destination=json_dict.get('destination'),
            status=json_dict.get('status'),
            bytes=json_dict.get('bytes')
        )

    def json_dict_to_report(self, json_dict:dict):
        return SynchronisationStatusReport(
            uuid=json_dict.get('uuid'),
            config_id=json_dict.get('config_id'),
            events=[self.json_dict_to_event(event) for event in json_dict.get('events')],
            start_date=datetime.datetime.fromisoformat(json_dict.get('start_date')),
            end_date=datetime.datetime.fromisoformat(json_dict.get('end_date')) if json_dict.get('end_date') is not None else None,
            total_bytes_processed=json_dict.get('total_bytes_processed'),
            total_files_processed=json_dict.get('total_files_processed'),
            total_files_processed_succesfully=json_dict.get('total_files_processed_succesfully')
        )

    def event_to_json_dict(self, event: SynchronisationStatusEvent):
        result : dict = {
            'source': event.source,
            'destination': event.destination,
            'bytes': event.bytes,
            'status': event.status,
            'start_date': event.start_date.isoformat(),
            'end_date': event.end_date.isoformat() if event.end_date is not None else None
        }
        return result

    def report_to_json_dict(self, report: SynchronisationStatusReport):
        result : dict = {
            'uuid': report.uuid,
            'config_id': report.config_id,
            'events': [self.event_to_json_dict(event) for event in report.events],
            'start_date': report.start_date.isoformat(),
            'end_date': report.end_date.isoformat() if report.end_date is not None else None,
            'total_bytes_processed': report.total_bytes_processed,
            'total_files_processed': report.total_files_processed,
            'total_files_processed_succesfully': report.total_files_processed_succesfully
        }
        return result

    def write_current_reporting_to_file(self, bla,bla2,bla3):
        with open(self.events_path, "r") as file_obj:
            data = json.load(file_obj)
        data['reports'] = [self.report_to_json_dict(blah) for blah in self._data]
        with open(self.events_path, "w") as file_obj:
            json.dump(data, file_obj, indent=6)


    def create_report(self, config_uuid: str):
        generated_uuid = str(uuid.uuid4())
        now = datetime.datetime.now()
        report = SynchronisationStatusReport(uuid=generated_uuid,
                                             config_id=config_uuid,
                                             events=[],
                                             start_date=now,
                                             end_date=None,
                                             total_files_processed=0,
                                             total_bytes_processed=0,
                                             total_files_processed_succesfully=0)
        self._data.append(report)
        self.notify_reporting_changed(config_uuid, report.uuid, events={})
        return report.uuid

    def find_reports_by_config_id(self,  config_id: str):
        result = []
        if config_id is None:
            return result
        for config_report in self._data:
            if config_report.config_id == config_id:
                result.append(config_report)
        return result
       # return [reports for reports in self._data if reports.config_id is config_id]

    def find_report_by_uuid(self, report_uuid: str):
        for index, report_data in enumerate(self._data):
            if report_data.uuid == report_uuid:
                return self._data[index]
        return []

    def add_events_to_report(self, report_uuid: str, events: list[SynchronisationStatusEvent]):
        report: SynchronisationStatusReport = self.find_report_by_uuid(report_uuid)
        report.events.extend(events)
        self.recalculate_report_metadata(report)
        self.notify_reporting_changed(report.config_id, report_uuid, {event.source for event in events})

    def add_event_to_report(self, report_uuid: str, event: SynchronisationStatusEvent):
        report: SynchronisationStatusReport = self.find_report_by_uuid(report_uuid)
        report.events.append(event)
        self.recalculate_report_metadata(report)
        self.notify_reporting_changed(report.config_id, report_uuid, {event.source})

    def recalculate_report_metadata(self, report: SynchronisationStatusReport,fill_end_date_when_no_event = False):
        report.total_files_processed = len(report.events)
        ok_counter = 0
        byte_counter= 0
        for event in report.events:
            if event.start_date < report.start_date:
                report.start_date =event.start_date
            if (event.end_date is not None) and ((report.end_date is None) or (event.end_date > report.end_date)):
                report.end_date = event.end_date
            if event.status == 'OK':
                ok_counter += 1
            byte_counter += event.bytes
        if fill_end_date_when_no_event:
            report.end_date = datetime.datetime.now()
        report.total_files_processed_succesfully = ok_counter
        report.total_bytes_processed = byte_counter

    def update_event(self, report_uuid:str, source:str, end_date = None, status = None, bytes = None):
        report = self.find_report_by_uuid(report_uuid)
        for index,event in enumerate(report.events):
            if event.source == source:
                if end_date is not None:
                    event.end_date = end_date
                if status is not None:
                    event.status = status
                if bytes is not None:
                    event.bytes = bytes
                self.recalculate_report_metadata(report)
                self.notify_reporting_changed(report.config_id, report_uuid, {source})
