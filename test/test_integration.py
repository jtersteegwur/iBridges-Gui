
import os

from pytest import raises,mark
from irodsConnector.manager import IrodsConnector
from pathlib import Path
from utils.sync_result import FileSyncMethod,SyncResult

ENVIRONMENT_PATH_FILE = 'irods_environment_new.json'
ENVIRONMENT = os.path.join(os.path.expanduser('~'), '.irods', ENVIRONMENT_PATH_FILE)
PASSWORD = os.environ.get('irods_password')

@mark.skipif(PASSWORD is None, reason="you're running this test somewhere where password is not set")
class TestIntegration:

    def test_diff_upload_single_file_error_file_not_exists(self, tmp_path):
        with raises(ValueError):
            connector = IrodsConnector(ENVIRONMENT, PASSWORD, 'mooienaam')
            empty_collection = self._ensure_empty_test_collection(connector, "test_single_file_diff_error")
            file_name = "file1.abc"
            remote_file = f"{empty_collection.path}/{file_name}"
            test_file_path = tmp_path.joinpath("testuploaddir").joinpath(file_name)
            actual = connector.get_diff_upload(str(test_file_path),remote_file)

    def test_diff_upload_single_file_differing_remote(self,tmp_path):
        connector = IrodsConnector(ENVIRONMENT, PASSWORD, 'mooienaam')
        empty_collection = self._ensure_empty_test_collection(connector, "test_single_file_diff")
        remote_file = f"{empty_collection.path}/file1.abc"
        test_local_dir = tmp_path.joinpath("testuploaddir")
        test_file_path = test_local_dir.joinpath("file1.abc")
        self._create_dummy_file(file_path=test_local_dir,file_name="file1.abc", size=10)
        connector.irods_put(str(test_file_path),remote_file)
        assert connector._data_op._ses_man.session.data_objects.exists(remote_file)
        with open(test_file_path, mode="a", encoding="utf-8") as file_obj:
            file_obj.write('changed')
        actual = connector.get_diff_upload(str(test_file_path),remote_file)
        assert len(actual) == 1
        assert actual[0].file_sync_method == FileSyncMethod.UPDATE
        connector._data_op._ses_man.session.data_objects.unlink(remote_file)

    def test_diff_upload_single_file_same_remote(self,tmp_path):
        connector = IrodsConnector(ENVIRONMENT, PASSWORD, 'mooienaam')
        empty_collection = self._ensure_empty_test_collection(connector, "test_single_file_diff")
        remote_file = f"{empty_collection.path}/file1.abc"
        test_local_dir = tmp_path.joinpath("testuploaddir")
        test_file_path = test_local_dir.joinpath("file1.abc")
        self._create_dummy_file(file_path=test_local_dir,file_name="file1.abc", size=10)
        connector.irods_put(str(test_file_path),remote_file)
        assert connector._data_op._ses_man.session.data_objects.exists(remote_file)
        actual = connector.get_diff_upload(str(test_file_path),remote_file)
        assert len(actual) == 0
        connector._data_op._ses_man.session.data_objects.unlink(remote_file)


    def test_diff_upload_single_file_not_exists_remote(self,tmp_path):
        connector = IrodsConnector(ENVIRONMENT, PASSWORD, 'mooienaam')
        empty_collection = self._ensure_empty_test_collection(connector, "test_diff_upload_single_file_not_exists_remote")
        remote_file = f"{empty_collection.path}/file1.abc"
        test_local_dir = tmp_path.joinpath("testuploaddir")
        test_file_path = test_local_dir.joinpath("file1.abc")
        self._create_dummy_file(file_path=test_local_dir,file_name="file1.abc", size=10)
        actual = connector.get_diff_upload(str(test_file_path),remote_file)
        assert len(actual) == 1
        assert actual[0].file_sync_method == FileSyncMethod.CREATE

    def test_diff_upload_multiple_files_not_exists_remote(self,tmp_path):
        connector = IrodsConnector(ENVIRONMENT, PASSWORD, 'mooienaam')
        empty_collection = self._ensure_empty_test_collection(connector, "test_diff_upload_multiple_files_not_exists_remote")
        remote_collection = f"{empty_collection.path}"
        test_local_dir = tmp_path.joinpath("testuploaddir")
        self._create_dummy_file(file_path=test_local_dir,file_name="file1.abc", size=10)
        self._create_dummy_file(file_path=test_local_dir,file_name="file2.abc", size=10)
        actual = connector.get_diff_upload(str(test_local_dir),remote_collection)
        expected = [SyncResult(source=f"{test_local_dir}/file1.abc", target=f"{remote_collection}/file1.abc",
                               filesize=10, f_sync_method=FileSyncMethod.CREATE),
                    SyncResult(source=f"{test_local_dir}/file2.abc", target=f"{remote_collection}/file2.abc",
                               filesize=10, f_sync_method=FileSyncMethod.CREATE)]
        assert all(exp in expected for exp in actual)

    def test_diff_upload_multiple_files_some_exists_remote(self, tmp_path):
        connector = IrodsConnector(ENVIRONMENT, PASSWORD, 'mooienaam')
        empty_collection = self._ensure_empty_test_collection(connector,
                                                              "test_diff_upload_multiple_files_some_exists_remote")
        remote_collection = f"{empty_collection.path}"
        test_local_dir = tmp_path.joinpath("testuploaddir")
        self._create_dummy_file(file_path=test_local_dir, file_name="file1.abc", size=10)
        self._create_dummy_file(file_path=test_local_dir, file_name="file2.abc", size=10)
        connector.irods_put(f"{test_local_dir}/file1.abc", f"{remote_collection}/file1.abc")

        actual = connector.get_diff_upload(str(test_local_dir), remote_collection)
        expected = [ SyncResult(source=f"{test_local_dir}/file2.abc", target=f"{remote_collection}/file2.abc",
                               filesize=10, f_sync_method=FileSyncMethod.CREATE)]
        connector._data_op._ses_man.session.data_objects.unlink(f"{remote_collection}/file1.abc")
        for exp in expected:
            assert exp in actual

    def test_diff_upload_multiple_files_some_exists_remote_differently(self, tmp_path):
        connector = IrodsConnector(ENVIRONMENT, PASSWORD, 'mooienaam')
        empty_collection = self._ensure_empty_test_collection(connector,
                                                              "test_diff_upload_multiple_files_some_exists_remote")
        remote_collection = f"{empty_collection.path}"
        test_local_dir = tmp_path.joinpath("testuploaddir")
        self._create_dummy_file(file_path=test_local_dir, file_name="file1.abc", size=10)
        self._create_dummy_file(file_path=test_local_dir, file_name="file2.abc", size=10)
        connector.irods_put(f"{test_local_dir}/file1.abc", f"{remote_collection}/file1.abc")
        with open(f"{test_local_dir}/file1.abc", mode="a", encoding="utf-8") as file_obj:
            file_obj.write('B'*10)
        actual = connector.get_diff_upload(str(test_local_dir), remote_collection)
        expected = [SyncResult(source=f"{test_local_dir}/file1.abc", target=f"{remote_collection}/file1.abc",
                               filesize=20, f_sync_method=FileSyncMethod.UPDATE),
                    SyncResult(source=f"{test_local_dir}/file2.abc", target=f"{remote_collection}/file2.abc",
                               filesize=10, f_sync_method=FileSyncMethod.CREATE)]
        connector._data_op._ses_man.session.data_objects.unlink(f"{remote_collection}/file1.abc")
        for exp in expected:
            assert exp in actual

    def _create_dummy_file(self, file_path:Path, file_name: str, size: int):
        os.makedirs(file_path, exist_ok=True)
        complete_path = file_path.joinpath(file_name)
        with open(complete_path, mode="x", encoding="utf-8") as file_obj:
            file_obj.write('A' * size)

    def _ensure_empty_test_collection(self, connector : IrodsConnector, coll_name: str):
        collection_path = f"{self.get_test_base_path(connector)}/{coll_name}"
        coll = connector.ensure_coll(collection_path)
        assert len(coll.data_objects) == 0
        return coll

    def get_test_base_path(self, connector):
        return f"/{connector.zone}/home/{connector.username}/integration_tests"