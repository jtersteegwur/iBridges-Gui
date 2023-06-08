""" Irods connection factory
"""
import irods.collection
import irods.data_object
import irods.resource
import irods.session
import irodsConnector
import irodsConnector.keywords as kw
import utils.sync_result


class IrodsConnector(object):
    """Create python or icommands class instance
    """

    def __init__(self, irods_env_file='', password='', application_name=None):
        """iRODS authentication with Python client.

        Parameters
        ----------
        irods_env_file : str
            JSON document with iRODS connection parameters.
        password : str
            Plain text password.
        application_name : str
            Name of the application using this connector.

        """
        self.__name__ = 'IrodsConnector'
        self._session = irodsConnector.session.Session(irods_env_file, password)
        self._resource = irodsConnector.resource.Resource(self._session)
        self._data_op = irodsConnector.dataOperations.DataOperation(self._resource, self._session)
        self._icommands = irodsConnector.Icommands.IrodsConnectorIcommands(self._resource, self._session)
        self._meta = irodsConnector.meta.Meta()
        self._permission = irodsConnector.permission.Permission(self._data_op, self._session)
        self._query = irodsConnector.query.Query(self._session)
        self._rules = irodsConnector.rules.Rules(self._session)
        self._tickets = irodsConnector.tickets.Tickets(self._session)
        self._users = irodsConnector.users.Users(self._session)

        if irods_env_file != '' and password != '': 
            self._session.connect(application_name)

    @property
    def davrods(self) -> str:
        return self._session.davrods

    @property
    def default_resc(self) -> str:
        return self._session.default_resc

    @property
    def ienv(self) -> dict:
        return self._session.ienv

    @property
    def irods_env_file(self) -> str:
        return self._session.irods_env_file

    @property
    def host(self) -> str:
        return self._session.host

    @property
    def port(self) -> str:
        return self._session.port

    @property
    def server_version(self) -> str:
        return self._session.server_version

    @property
    def username(self) -> str:
        return self._session.username

    @property
    def zone(self) -> str:
        return self._session.zone

    @property
    def password(self) -> str:
        return self._session.password

    @property
    def permissions(self) -> dict:
        return self._permission.permissions

    @property
    def resources(self) -> dict:
        return self._resource.resources

    @property
    def session(self) -> irods.session.iRODSSession:
        return self._session.session

    def add_metadata(self, items: list, key: str, value: str, units: str = None):
        return self._meta.add(items, key, value, units)

    def add_multiple_metadata(self, items, avus):
        return self._meta.add_multiple(items, avus)

    def cleanup(self):
        return self._session.cleanup()

    def collection_exists(self, path: str) -> bool:
        return self._data_op.collection_exists(path)

    def create_ticket(self, obj_path: str, expiry_string: str = '') -> tuple:
        return self._tickets.create_ticket(obj_path, expiry_string)

    def dataobject_exists(self, path: str) -> bool:
        return self._data_op.dataobject_exists(path)

    def delete_data(self, item: None):
        return self._data_op.delete_data(item)

    def delete_metadata(self, items: list, key: str, value: str, units: str = None):
        return self._meta.delete(items, key, value, units)

    def diff_obj_file(self, objpath: str, fspath: str, scope: str = "size") -> tuple:
        return self._data_op.diff_obj_file(objpath, fspath, scope)

    def diff_irods_localfs(self, coll: irods.collection.Collection,
                           dirpath: str, scope: str = "size") -> tuple:
        return self._data_op.diff_irods_localfs(coll, dirpath, scope)

    def get_diff_download(self, source:str, target:str) -> list[utils.sync_result.SyncResult]:
        return self._data_op.get_diff_download(source, target)

    def get_diff_upload(self, source: str, target: str) -> list[utils.sync_result.SyncResult]:
        return self._data_op.get_diff_upload(source, target)

    def download_data_using_sync_result(self, sync_result_list: list[utils.sync_result.SyncResult],
                                        minimal_free_space_on_disk: int, check_free_space: bool):
        return self._data_op.download_data_using_sync_result(sync_result_list,minimal_free_space_on_disk,check_free_space)

    def upload_data_using_sync_result(self, sync_result_list: list[utils.sync_result.SyncResult], resource_name: str,
                                      minimal_free_space_on_server: int, check_free_space: bool):
        return list(self._data_op.upload_data_with_sync_result_generator(sync_result_list, resource_name, minimal_free_space_on_server, check_free_space))
    def download_data(self, source: None, destination: str,
                      size: int, buff: int = kw.BUFF_SIZE, force: bool = False, diffs: tuple = None):
        if self._icommands.icommands():
            return self._icommands.download_data(source, destination, size, buff, force)
        else:
            return self._data_op.download_data(source, destination, size, buff, force, diffs)

    def ensure_coll(self, coll_name: str) -> irods.collection.Collection:
        return self._data_op.ensure_coll(coll_name)

    def ensure_data_object(self, data_object_name: str) -> irods.data_object.DataObject:
        return self._data_op.ensure_data_object(data_object_name)

    def execute_rule(self, rule_file: str, params: dict, output: str = 'ruleExecOut') -> tuple:
        return self._rules.execute_rule(rule_file, params, output)

    def get_collection(self, path: str) -> irods.collection.Collection:
        return self._data_op.get_collection(path)

    def get_dataobject(self, path: str) -> irods.data_object.DataObject:
        return self._data_op.get_dataobject(path)

    def get_free_space(self, resc_name: str, multiplier: int = 1) -> int:
        return self._resource.get_free_space(resc_name, multiplier)

    def get_irods_size(self, path_names: list) -> int:
        return self._data_op.get_irods_size(path_names)

    def get_permissions(self, path: str = '', obj: irods.collection = None) -> list:
        return self._permission.get_permissions(path, obj)

    def get_resource(self, resc_name: str) -> irods.resource.Resource:
        return self._resource.get_resource(resc_name)

    def get_resource_children(self, resc: irods.resource.Resource) -> list:
        return self._resource.get_resource_children(resc)

    def get_user_info(self) -> tuple:
        return self._users.get_user_info()

    def icommands(self) -> bool:
        return self._icommands.icommands()
    
    def irods_put(self, local_path: str, irods_path: str, res_name: str = ''):
        if self._icommands.icommands():
            return self._icommands.irods_put(local_path, irods_path, res_name)
        else:
            return self._data_op.irods_put(local_path, irods_path, res_name)

    def irods_get(self, irods_path: str, local_path: str, options: dict = None):
        if self._icommands.icommands():
            return self._icommands.irods_get(irods_path, local_path)
        else:
            return self._data_op.irods_get(irods_path, local_path, options)

    def is_collection(self, obj) -> bool:
        return self._data_op.is_collection(obj)

    def is_dataobject(self, obj) -> bool:
        return self._data_op.is_dataobject(obj)

    def list_resources(self, attr_names: list = None) -> tuple:
        return self._resource.list_resources(attr_names)

    def resource_space(self, resc_name: str) -> int:
        return self._resource.resource_space(resc_name)

    def search(self, key_vals: dict = None) -> list:
        return self._query.search(key_vals)

    def set_permissions(self, perm: str, path: str, user: str = '', zone: str = '',
                        recursive: bool = False, admin: bool = False):
        return self._permission.set_permissions(perm, path, user, zone, recursive, admin)

    def update_metadata(self, items: list, key: str, value: str, units: str = None):
        return self._meta.update(items, key, value, units)

    def upload_data(self, source: str, destination: irods.collection.Collection,
                    res_name: str, size: int, buff: int = kw.BUFF_SIZE, force: bool = False, diffs: tuple = None):
        if self._icommands.icommands():
            return self._icommands.upload_data(source, destination,
                                               res_name, size, buff, force)
        else:
            return self._data_op.upload_data(source, destination, res_name, size, buff, force, diffs)
