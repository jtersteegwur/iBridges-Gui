""" Tests pertaining to irodsConnector.dataOperations """
import shutil
from unittest.mock import MagicMock, Mock, patch, ANY, call
from pytest import raises
from irods.exception import CollectionDoesNotExist
import irodsConnector.dataOperations
from irodsConnector.resource import NotEnoughFreeSpace


def setup_data_operation(attrs_resource_mock=None, attrs_session_mock=None) -> (
        irodsConnector.dataOperations.DataOperation, MagicMock, MagicMock):
    """ Create a mocked version of th """

    if attrs_session_mock is None:
        attrs_session_mock = {}
    if attrs_resource_mock is None:
        attrs_resource_mock = {}
    mock_resource = MagicMock(name="Mocked Resource", **attrs_resource_mock)
    mock_session = MagicMock(name="Mocked Session", **attrs_session_mock)
    class_under_test = irodsConnector.dataOperations.DataOperation(mock_resource, mock_session)
    return class_under_test, mock_resource, mock_session


class TestDataOperations:
    """
    Tests the irodsconnector dataoperations
    """

    def test_dataobject_exists(self):
        """
        Tests the irodsconnector dataoperations
        """
        class_under_test, _, mock_session = setup_data_operation()
        test = "test"
        class_under_test.dataobject_exists(test)
        # Not sure what we're going to test with all these pass-through methods...
        # For now, I'll just add one (for copy-pasting purposes ;) ) and only test the more complicated methods
        mock_session.session.data_objects.exists.assert_called_with(test)

    def test_upload_data_invalid_source_path(self):
        """
        Tests the irodsconnector dataoperations
        """
        with raises(FileNotFoundError):
            with patch('utils.utils.LocalPath') as mock_localpath:
                class_under_test, _, _ = setup_data_operation()
                mock_localpath.return_value.is_file = MagicMock(return_value=False)
                mock_localpath.return_value.is_dir = MagicMock(return_value=False)
                class_under_test.upload_data(source="/mocked/path/to/file", destination=MagicMock(),
                                             res_name="res_name", size=100)

    def test_upload_data_destination_not_exist(self):
        with raises(CollectionDoesNotExist):
            with patch('utils.utils.LocalPath') as mock_localpath:
                class_under_test, _, _ = setup_data_operation()
                class_under_test.is_collection = MagicMock(return_value=False)
                mock_localpath.return_value.is_file = MagicMock(return_value=True)
                mock_localpath.return_value.is_dir = MagicMock(return_value=False)
                class_under_test.upload_data(source="/mocked/path/to/file", destination=MagicMock(),
                                             res_name="res_name", size=100)

    def test_upload_data_checks_for_free_space(self):
        with raises(NotEnoughFreeSpace):
            with patch('utils.utils.LocalPath') as mock_localpath:
                all_free_space = 100
                class_under_test, _, _ = setup_data_operation(
                    attrs_resource_mock={'resource_space.return_value': all_free_space}
                )
                class_under_test.is_collection = MagicMock(return_value=True)
                class_under_test.diff_obj_file = MagicMock(return_value=([], [], [], []))
                mock_localpath.return_value.is_file = MagicMock(return_value=True)
                mock_localpath.return_value.is_dir = MagicMock(return_value=False)
                class_under_test.upload_data(source="/mocked/path/to/file", destination=MagicMock(),
                                             res_name="res_name", size=10, buff=all_free_space)

    def test_upload_data_file_upload_successful(self):
        file = "/mocked/path/to/file"
        config = {"return_value.is_file.return_value": True,
                  "return_value.is_dir.return_value": False,
                  "return_value.__str__.return_value": file}
        with patch('utils.utils.LocalPath', **config):
            class_under_test, _, _ = setup_data_operation(
                attrs_resource_mock={'resource_space.return_value': 100}
            )
            class_under_test.is_collection = MagicMock(return_value=True)
            class_under_test.diff_obj_file = MagicMock(return_value=([], [file], [], []))
            class_under_test.irods_put = Mock()
            class_under_test.upload_data(source=file, destination=MagicMock(),
                                         res_name="res_name", size=10, buff=0)
            class_under_test.irods_put.assert_called_once()
            assert str(class_under_test.irods_put.call_args.args[0]) == file

    def test_download_data_invalid_source_path(self):
        with raises(FileNotFoundError):
            sourceMock = Mock()
            class_under_test, _, _ = setup_data_operation()
            class_under_test.is_dataobject_or_collection = Mock(return_value=False)
            class_under_test.download_data(source=sourceMock, destination="destination", size=100)

    def test_download_data_invalid_destination(self):
        file = "/mocked/path/to/file"
        destination_localpath_config = {"return_value.is_file.return_value": True,
                                        "return_value.is_dir.return_value": False,
                                        "return_value.__str__.return_value": file}

        irods_source_path = '/mocked/irods/path'
        source_irods_config = {"return_value.is_file.return_value": True,
                               "return_value.is_dir.return_value": False,
                               "return_value.__str__.return_value": irods_source_path}
        with patch('utils.utils.IrodsPath', **source_irods_config):
            with patch('utils.utils.LocalPath', **destination_localpath_config):
                with raises(FileNotFoundError):
                    sourceMock = Mock()
                    destMock = Mock()
                    class_under_test, _, _ = setup_data_operation()
                    class_under_test.is_dataobject_or_collection = Mock(return_value=True)
                    class_under_test.download_data(source=sourceMock, destination=destMock, size=100)

    def test_download_data_no_access(self):
        file = "/mocked/path/to/file"
        destination_localpath_config = {"return_value.is_file.return_value": False,
                                        "return_value.is_dir.return_value": True,
                                        "return_value.__str__.return_value": file}

        irods_source_path = '/mocked/irods/path'
        source_irods_config = {"return_value.is_file.return_value": True,
                               "return_value.is_dir.return_value": False,
                               "return_value.__str__.return_value": irods_source_path}
        with patch('os.access', return_value=False):
            with patch('utils.utils.IrodsPath', **source_irods_config):
                with patch('utils.utils.LocalPath', **destination_localpath_config):
                    with raises(PermissionError):
                        sourceMock = Mock()
                        destMock = Mock()
                        class_under_test, _, _ = setup_data_operation()
                        class_under_test.is_dataobject_or_collection = Mock(return_value=True)
                        class_under_test.download_data(source=sourceMock, destination=destMock, size=100)

    def test_download_data_no_free_space(self):
        file = "/mocked/path/to/dir/"
        destination_localpath_config = {"return_value.is_file.return_value": False,
                                        "return_value.is_dir.return_value": True,
                                        "return_value.__str__.return_value": file}

        irods_source_path = '/mocked/irods/path/to/file'
        source_irods_config = {"return_value.is_file.return_value": True,
                               "return_value.is_dir.return_value": False,
                               "return_value.__str__.return_value": irods_source_path}
        with patch('os.access', return_value=True):
            with patch('utils.utils.IrodsPath', **source_irods_config):
                with patch('utils.utils.LocalPath', **destination_localpath_config):
                    with patch('irodsConnector.dataOperations.disk_usage', **{'return_value.free': 0}):
                        with raises(NotEnoughFreeSpace):
                            sourceMock = Mock()
                            destMock = Mock()
                            class_under_test, _, _ = setup_data_operation()
                            class_under_test.is_dataobject_or_collection = Mock(return_value=True)
                            class_under_test.is_dataobject = Mock(return_value=True)
                            class_under_test.diff_obj_file = Mock(return_value=([], [], [], []))
                            class_under_test.download_data(source=sourceMock, destination=destMock, size=100)

    def test_download_data_file_no_free_space_force(self):
        localpath_dir = "/mocked/path/to/dir/"
        destination_localpath_config = {"return_value.is_file.return_value": False,
                                        "return_value.is_dir.return_value": True,
                                        "return_value.__str__.return_value": localpath_dir}

        irods_source_path = '/mocked/irods/path/to/file'
        source_irods_config = {"return_value.is_file.return_value": True,
                               "return_value.is_dir.return_value": False,
                               "return_value.__str__.return_value": irods_source_path}
        with patch('os.access', return_value=True):
            with patch('utils.utils.IrodsPath', **source_irods_config):
                with patch('utils.utils.LocalPath', **destination_localpath_config):
                    with patch('irodsConnector.dataOperations.disk_usage', **{'return_value.free': 0}):
                        source_mock = Mock()
                        dest_mock = Mock()
                        class_under_test, _, _ = setup_data_operation()
                        class_under_test.is_dataobject_or_collection = Mock(return_value=True)
                        class_under_test.is_dataobject = Mock(return_value=True)
                        class_under_test.diff_obj_file = Mock(return_value=([], [], [irods_source_path], []))
                        class_under_test.irods_get = Mock()
                        class_under_test.download_data(source=source_mock, destination=dest_mock, size=100, force=True)
                        class_under_test.irods_get.assert_called_once()
                        assert str(class_under_test.irods_get.call_args[0][0]) == irods_source_path

    def test_download_data_folder(self):
        localpath_dir = "/mocked/path/to/dir/"
        destination_localpath_config = {"return_value.is_file.return_value": False,
                                        "return_value.is_dir.return_value": True,
                                        "return_value.__str__.return_value": localpath_dir}

        irods_source_dir = '/mocked/irods/path/to/directory/'
        source_irods_config = {"return_value.is_file.return_value": False,
                               "return_value.is_dir.return_value": True,
                               "return_value.__str__.return_value": irods_source_dir}
        with patch('os.access', return_value=True):
            with patch('utils.utils.IrodsPath', **source_irods_config):
                with patch('utils.utils.LocalPath', **destination_localpath_config):
                    with patch('irodsConnector.dataOperations.disk_usage', **{'return_value.free': 0}):
                        source_mock = Mock()
                        dest_mock = Mock()
                        class_under_test, _, _ = setup_data_operation()
                        class_under_test.is_dataobject_or_collection = Mock(return_value=True)
                        class_under_test.is_dataobject = Mock(return_value=False)
                        class_under_test.diff_irods_localfs = Mock(return_value=([], [], ['file_1', 'file_2'], []))
                        class_under_test.irods_get = Mock()
                        class_under_test.download_data(source=source_mock, destination=dest_mock, size=100, force=True)
                        ## To much path manipulation going on to mock and check args
                        assert len(class_under_test.irods_get.call_args_list) == 2

    def test_obj_file_localdir(self):
        localpath_dir = "/mocked/path/to/dir/"
        obj_path = '/mocked/path/to/irods'
        class_under_test, _, _ = setup_data_operation()
        with patch('os.path.isfile', **{'return_value': False}):
            with patch('os.path.isdir', **{'return_value': True}):
                with raises(IsADirectoryError):
                    class_under_test.diff_obj_file(obj_path, localpath_dir, "checksum")

    def test_obj_file_objpath_is_collection(self):
        localpath_dir = "/mocked/path/to/file"
        obj_path = '/mocked/path/to/irods'
        class_under_test, _, mock_session = setup_data_operation(None,
                                                                 {'session.collections.exists.return_value': True})
        with patch('os.path.isfile', **{'return_value': True}):
            with patch('os.path.isdir', **{'return_value': False}):
                with raises(IsADirectoryError):
                    class_under_test.diff_obj_file(obj_path, localpath_dir, "checksum")
        mock_session.session.collections.exists.assert_called()

    def test_obj_file_objpath_not_exists_locally(self):
        localpath_dir = "/mocked/path/to/file"
        obj_path = '/mocked/path/to/irods'
        class_under_test, _, mock_session = setup_data_operation(None, {'session.collections.exists.return_value': False
            , 'session.data_objects.exists.return_value': True})
        with patch('os.path.isfile', **{'return_value': False}):
            with patch('os.path.isdir', **{'return_value': False}):
                diff, only_fs, only_irods, same = class_under_test.diff_obj_file(obj_path, localpath_dir, "checksum")
                assert only_irods == [obj_path]

    def test_obj_file_objpath_exists_locally_but_not_in_irods(self):
        localpath_dir = "/mocked/path/to/file"
        obj_path = '/mocked/path/to/irods'
        class_under_test, _, mock_session = setup_data_operation(None, {'session.collections.exists.return_value': False
            , 'session.data_objects.exists.return_value': False})
        with patch('os.path.isfile', **{'return_value': True}):
            with patch('os.path.isdir', **{'return_value': False}):
                diff, only_fs, only_irods, same = class_under_test.diff_obj_file(obj_path, localpath_dir, "checksum")
                assert only_fs == [localpath_dir]

    def test_obj_file_objpath_scope_size(self):
        localpath_dir = "/mocked/path/to/file"
        obj_path = '/mocked/path/to/irods'
        class_under_test, _, mock_session = setup_data_operation(None, {'session.collections.exists.return_value': False
            , 'session.data_objects.exists.return_value': False})
        with patch('os.path.isfile', **{'return_value': True}):
            with patch('os.path.isdir', **{'return_value': False}):
                diff, only_fs, only_irods, same = class_under_test.diff_obj_file(obj_path, localpath_dir, "checksum")
                assert only_fs == [localpath_dir]
