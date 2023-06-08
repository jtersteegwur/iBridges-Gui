import sys
sys.path.append('..')
import datetime

import os

from gui.synchronisationConfigurationTableModel import SynchronisationConfigurationTableModel
from synchronisation.reporting_repository import ReportingRepository
from synchronisation.reporting import SynchronisationStatusEvent
from synchronisation.configuration_repository import ConfigRepository
from synchronisation.configuration_item import SynchronisationConfigItem


class TestModelImplementations:
    def test_SynchronisationConfigurationTableModel(self, tmp_path, qtmodeltester):
        joinpath = tmp_path.joinpath("synchronisation.json")
        repository = ConfigRepository(str(joinpath))
        model = SynchronisationConfigurationTableModel(repository)
        repository.add_config(SynchronisationConfigItem(type="Scheduled upload",
                                                        local="C:\\iRods\\jtersteegwur\\iBridges-Gui\\docker",
                                                        remote="/RDMacc/home/terst007",
                                                        cron="0 0 * * *"))
        qtmodeltester.check(model)

    def test_configuration_reporting_repositories_defaults(self, tmp_path):
        test_local_dir = self._setup_dummy_dir(tmp_path)
        test_remote_dir = "/some/dummy/path/"
        reporting_path = tmp_path.joinpath("synchronisation_events.json")
        config_path = tmp_path.joinpath("synchronisation.json")

        config_repository = ConfigRepository(str(config_path))
        config_repository.add_config(SynchronisationConfigItem(type="Scheduled upload",
                                                               local=str(test_local_dir),
                                                               remote=test_remote_dir,
                                                               cron="0 0 * * *"))
        written_config = config_repository.get_by_index(0)
        assert written_config.type == "Scheduled upload"
        assert written_config.cron == "0 0 * * *"
        assert written_config.local == str(test_local_dir)
        assert written_config.remote == test_remote_dir
        assert written_config.uuid is not None
        assert len(written_config.uuid) > 0

        reporting_repository = ReportingRepository(str(reporting_path))
        report_uuid = reporting_repository.create_report(written_config.uuid)
        report = reporting_repository.find_report_by_uuid(report_uuid)
        assert report.uuid is not None
        assert len(report.uuid) > 0
        assert report.events == []
        assert report.config_id == written_config.uuid
        assert report.total_bytes_processed == 0
        assert report.total_files_processed == 0
        assert report.total_files_processed_succesfully == 0
        assert report.start_date is not None
        assert report.end_date is None

    def test_report_meta_info_is_updated(self, tmp_path):
        test_local_dir = self._setup_dummy_dir(tmp_path)
        test_remote_dir = "/some/dummy/path/"
        reporting_path = tmp_path.joinpath("synchronisation_events.json")
        config_path = tmp_path.joinpath("synchronisation.json")

        config_repository = ConfigRepository(str(config_path))
        config_repository.add_config(SynchronisationConfigItem(type="Scheduled upload",
                                                               local=str(test_local_dir),
                                                               remote=test_remote_dir,
                                                               cron="0 0 * * *"))
        written_config = config_repository.get_by_index(0)
        reporting_repository = ReportingRepository(str(reporting_path))
        report_uuid = reporting_repository.create_report(written_config.uuid)
        date_2022 = datetime.datetime(2022, 1, 1)
        date_2023 = datetime.datetime(2023, 1, 1)
        date_2024 = datetime.datetime(2024, 1, 1)
        event = SynchronisationStatusEvent(date_2023, date_2023, 'dummy_src', 'dummy_dst', "OK", 100)
        event2 = SynchronisationStatusEvent(date_2022, date_2023, 'dummy_src', 'dummy_dst', "OK", 100)
        event3 = SynchronisationStatusEvent(date_2023, date_2024, 'dummy_src', 'dummy_dst', "OK", 100)
        event4 = SynchronisationStatusEvent(date_2023, date_2024, 'dummy_src', 'dummy_dst', "ERROR", 0)
        event5 = SynchronisationStatusEvent(date_2023, date_2024, 'dummy_src', 'dummy_dst', "ERROR", 100)
        reporting_repository.add_event_to_report(report_uuid, event)
        report = reporting_repository.find_report_by_uuid(report_uuid)
        self._assert_report(report, date_2023, date_2023, 1, 1, 1, 100)
        reporting_repository.add_event_to_report(report_uuid, event2)
        self._assert_report(report, date_2022, date_2023, 2, 2, 2, 200)
        reporting_repository.add_event_to_report(report_uuid, event3)
        self._assert_report(report, date_2022, date_2024, 3, 3, 3, 300)
        reporting_repository.add_event_to_report(report_uuid, event4)
        self._assert_report(report, date_2022, date_2024, 4, 4, 3, 300)
        reporting_repository.add_event_to_report(report_uuid, event5)
        self._assert_report(report, date_2022, date_2024, 5, 5, 3, 400)


    def _assert_report(self, report, expected_start_date, expected_end_date, expected_event_length,
                       expected_total_files_processed, expected_total_files_processed_successfully,
                       expected_total_bytes_processed):
        assert len(report.events) == expected_event_length
        assert report.start_date == expected_start_date
        assert report.end_date == expected_end_date
        assert report.total_files_processed == expected_total_files_processed
        assert report.total_files_processed_succesfully == expected_total_files_processed_successfully
        assert report.total_bytes_processed == expected_total_bytes_processed

    def _create_dummy_file(self, path, size):
        with open(path, "x") as file_obj:
            file_obj.write('A' * size)

    def _setup_dummy_dir(self, tmp_path):
        test_local_dir = tmp_path.joinpath("testuploaddir")
        os.mkdir(test_local_dir)
        self._create_dummy_file(test_local_dir.joinpath("file1.abc"), 10)
        self._create_dummy_file(test_local_dir.joinpath("file2.abc"), 10)
        self._create_dummy_file(test_local_dir.joinpath("file3.abc"), 10)
        return test_local_dir



