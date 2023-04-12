""" collections and data objects
"""
import base64
import hashlib
import logging
import os
from shutil import disk_usage
from concurrent.futures import ThreadPoolExecutor, wait
import irods.collection
import irods.data_object
import irods.exception
import irodsConnector.keywords as kw
from irodsConnector.resource import NotEnoughFreeSpace, Resource
from irodsConnector.session import Session
from utils import utils

NO_WRITE_ACCESS = 'No rights to write to destination.'

NOT_DIRECTORY = 'destination path does not exist or is not directory'

NOT_A_VALID_SOURCE_PATH = 'not a valid source path'


class DataOperation(object):
    """ Irods collections and data objects operations"""
    _res_man = None
    _ses_man = None

    def __init__(self, res_man: Resource, ses_man: Session):
        """ iRODS data operations initialization

            Parameters
            ----------
            res_man : irods resource
                Instance of the Reource class
            ses_man : irods session
                instance of the Session class

        """
        self._res_man = res_man
        self._ses_man = ses_man

    @staticmethod
    def is_dataobject_or_collection(obj: None):
        """Check if `obj` is an iRODS data object or collection.

        Parameters
        ----------
        obj : iRODS object instance
            iRODS instance to check.

        Returns
        -------
        bool
            If `obj` is an iRODS data object or collection.

        """
        return isinstance(obj, (
            irods.data_object.iRODSDataObject,
            irods.collection.iRODSCollection))

    def dataobject_exists(self, path: str) -> bool:
        """Check if an iRODS data object exists.

        Parameters
        ----------
        path : str
            Name of an iRODS data object.

        Returns
        -------
        bool
            Existence of the data object with `path`.

        """
        return self._ses_man.session.data_objects.exists(path)

    def collection_exists(self, path: str) -> bool:
        """Check if an iRODS collection exists.

        Parameters
        ----------
        path : str
            Name of an iRODS collection.

        Returns
        -------
        bool
            Existance of the collection with `path`.

        """
        return self._ses_man.session.collections.exists(path)

    @staticmethod
    def is_dataobject(obj) -> bool:
        """Check if `obj` is an iRODS data object.

        Parameters
        ----------
        obj : iRODS object instance
            iRODS instance to check.

        Returns
        -------
        bool
            If `obj` is an iRODS data object.

        """
        return isinstance(obj, irods.data_object.iRODSDataObject)

    @staticmethod
    def is_collection(obj) -> bool:
        """Check if `obj` is an iRODS collection.

        Parameters
        ----------
        obj : iRODS object instance
            iRODS instance to check.

        Returns
        -------
        bool
            If `obj` is an iRODS collection.

        """
        return isinstance(obj, irods.collection.iRODSCollection)

    @staticmethod
    def irods_dirname(path: str) -> str:
        """Find path less the final element for an iRODS path.

        Parameters
        ----------
        path : str
            An iRODS path, relative or absolute.

        Returns
        -------
        str
            iRODS path less the element after the final '/'

        """
        return utils.IrodsPath(path).parent

    def ensure_data_object(self, data_object_name: str) -> irods.data_object.DataObject:
        """Optimally create a data object with `data_object_name` if one does
        not exist.

        Parameters
        ----------
        data_object_name : str
            Name of the data object to check/create.

        Returns
        -------
        iRODS Data object
            Existing or new iRODS data object.

        Raises:
            irods.exception.CAT_NO_ACCESS_PERMISSION

        """
        try:
            if self._ses_man.session.data_objects.exists(data_object_name):
                return self._ses_man.session.data_objects.get(data_object_name)
            return self._ses_man.session.data_objects.create(data_object_name)
        except irods.exception.CAT_NO_ACCESS_PERMISSION as cnap:
            logging.info('ENSURE DATA OBJECT', exc_info=True)
            raise cnap

    def ensure_coll(self, coll_name: str) -> irods.collection.Collection:
        """Optimally create a collection with `coll_name` if one does
        not exist.

        Parameters
        ----------
        coll_name : str
            Name of the collection to check/create.

        Returns
        -------
        iRODSCollection
            Existing or new iRODS collection.

        Raises:
            irods.exception.CAT_NO_ACCESS_PERMISSION

        """
        try:
            if self._ses_man.session.collections.exists(coll_name):
                return self._ses_man.session.collections.get(coll_name)
            return self._ses_man.session.collections.create(coll_name)
        except irods.exception.CAT_NO_ACCESS_PERMISSION as cnap:
            logging.info('ENSURE COLLECTION', exc_info=True)
            raise cnap

    def get_dataobject(self, path: str) -> irods.data_object.DataObject:
        """Instantiate an iRODS data object.

        Parameters
        ----------
        path : str
            Name of an iRODS data object.

        Returns
        -------
        iRODSDataObject
            Instance of the data object with `path`.

        """
        if self.dataobject_exists(path):
            return self._ses_man.session.data_objects.get(path)
        raise irods.exception.DataObjectDoesNotExist(path)

    def get_collection(self, path: str) -> irods.collection.Collection:
        """Instantiate an iRODS collection.

        Parameters
        ----------
        path : str
            Name of an iRODS collection.

        Returns
        -------
        iRODSCollection
            Instance of the collection with `path`.

        """
        if self.collection_exists(path):
            return self._ses_man.session.collections.get(path)
        raise irods.exception.CollectionDoesNotExist(path)

    def irods_put(self, local_path: str, irods_path: str, resc_name: str = ''):
        """Upload `local_path` to `irods_path` following iRODS `options`.

        Parameters
        ----------
        local_path : str
            Path of local file or directory/folder.
        irods_path : str
            Path of iRODS data object or collection.
        resc_name : str
            Optional resource name.

        """
        options = {
            kw.ALL_KW: '',
            kw.NUM_THREADS_KW: kw.NUM_THREADS,
            kw.REG_CHKSUM_KW: '',
            kw.VERIFY_CHKSUM_KW: ''
        }
        if resc_name not in ['', None]:
            options[kw.RESC_NAME_KW] = resc_name
        self._ses_man.session.data_objects.put(local_path, irods_path, **options)

    def irods_get(self, irods_path: str, local_path: str, options: dict = None):
        """Download `irods_path` to `local_path` following iRODS `options`.

        Parameters
        ----------
        irods_path : str
            Path of iRODS data object or collection.
        local_path : str
            Path of local file or directory/folder.
        options : dict
            iRODS transfer options.

        """
        if options is None:
            options = {}
        options.update({
            kw.NUM_THREADS_KW: kw.NUM_THREADS,
            kw.VERIFY_CHKSUM_KW: '',
        })
        self._ses_man.session.data_objects.get(irods_path, local_path, **options)

    def upload_data(self, source: str, destination: irods.collection.Collection,
                    res_name: str, size: int, buff: int = kw.BUFF_SIZE, force: bool = False, diffs: tuple = None):
        """Upload data from the local `source` to the iRODS
        `destination`.

        When `source` is a folder/directory, upload its contents
        recursively to the iRODS collection `destination`.  If `source`
        is the path to a file, upload the file.

        Parameters
        ----------
        source : str
            Absolute path to local file or folder.
        destination : iRODSCollection
            The iRODS collection to where the data will be uploaded.
        res_name : str
            Name of the top-level iRODS resource.
        size : int
            Size of data to be uploaded in bytes.
        buff : int
            Buffer size on resource that should remain after upload in
            bytes.
        force : bool
            Ignore storage capacity on resource associated with
            `resc_name`.
        diffs : list
            Output of diff functions.

        """
        logging.info(
            'iRODS UPLOAD: %s-->%s %s', source, destination.path,
            res_name or '')
        source = utils.LocalPath(source)
        if source.is_file() or source.is_dir():
            if self.is_collection(destination):
                cmp_path = utils.IrodsPath(destination.path, source.name)
            else:
                raise irods.exception.CollectionDoesNotExist(destination)
        else:
            raise FileNotFoundError(
                'ERROR iRODS upload: not a valid source path')
        if res_name in [None, '']:
            res_name = self._ses_man.default_resc
        if diffs is None:
            if source.is_file():
                diff, only_fs, _= self.diff_obj_file(cmp_path, source, scope='checksum')
            else:
                cmp_coll = self.ensure_coll(cmp_path)
                diff, only_fs, _ = self.diff_irods_localfs(cmp_coll, source)
        else:
            diff, only_fs, _ = diffs
        if not force:
            space = self._res_man.resource_space(res_name)
            if size > (space - buff):
                logging.info(
                    'ERROR iRODS upload: Not enough free space on resource.',
                    exc_info=True)
                raise NotEnoughFreeSpace(
                    'ERROR iRODS upload: Not enough free space on resource.')
        try:
            # Data object
            if source.is_file() and len(diff + only_fs) > 0:
                logging.info(
                    'IRODS UPLOADING file %s to %s', source, cmp_path)
                self.irods_put(source, cmp_path, res_name)
            # Collection
            else:
                logging.info('IRODS UPLOAD started:')
                for irods_path, local_path in diff:
                    # Upload files to distinct data objects.
                    _ = self.ensure_coll(self.irods_dirname(irods_path))
                    logging.info(
                        'REPLACE: %s with %s', irods_path, local_path)
                    self.irods_put(local_path, irods_path, res_name)
                # Variable `only_fs` can contain files and folders.
                for rel_path in only_fs:
                    # Create subcollections and upload.
                    rel_path = utils.PurePath(rel_path)
                    local_path = source.joinpath(rel_path)
                    if len(rel_path.parts) > 1:
                        new_path = cmp_path.joinpath(rel_path.parent)
                    else:
                        new_path = cmp_path
                    _ = self.ensure_coll(new_path)
                    logging.info('UPLOAD: %s to %s', local_path, new_path)
                    irods_path = new_path.joinpath(rel_path.name)
                    logging.info('CREATE %s', irods_path)
                    self.irods_put(local_path, irods_path, res_name)
        except Exception as error:
            logging.info('UPLOAD ERROR', exc_info=True)
            raise error

    def download_data(self, source: None, destination: str, size: int,
                      buff: int = kw.BUFF_SIZE, force: bool = False, diffs: tuple = None):
        """Dowload data from an iRODS `source` to the local `destination`.

        When `source` is a collection, download its contents
        recursively to the local folder/directory `destination`.  If
        `source` is a data object, download it to a file in the local
        folder/director.

        Parameters
        ----------
        source : iRODSCollection, iRODSDataObject
            The iRODS collection or data object from where the data will
            be downloaded.
        destination : str
            Absolute path to local folder/directory.
        size : int
            Size of data to be uploaded in bytes.
        buff : int
            Buffer size on local storage that should remain after
            download in bytes.
        force : bool
            Ignore storage capacity on the storage system of `destination`.
        diffs : tuple
            Output of diff functions.

        """
        logging.info('iRODS DOWNLOAD: %s-->%s', source.path, destination)
        if self.is_dataobject_or_collection(source):
            source_path = utils.IrodsPath(source.path)
        else:
            raise FileNotFoundError('ERROR iRODS download: ' + NOT_A_VALID_SOURCE_PATH)
        destination = utils.LocalPath(destination)
        if not destination.is_dir():
            logging.info('DOWNLOAD ERROR: ' + NOT_DIRECTORY, exc_info=True)
            raise FileNotFoundError('ERROR iRODS download: ' + NOT_DIRECTORY)
        if not os.access(destination, os.W_OK):
            logging.info('DOWNLOAD ERROR: ' + NO_WRITE_ACCESS, exc_info=True)
            raise PermissionError('ERROR iRODS download: ' + NO_WRITE_ACCESS)
        cmp_path = destination.joinpath(source_path.name)
        # TODO perhaps treat this path as part of the diff
        if self.is_collection(source) and not cmp_path.is_dir():
            os.mkdir(cmp_path)
        # Only download if not present or difference in files.
        if diffs is None:
            if self.is_dataobject(source):
                diff, _, only_irods, _ = self.diff_obj_file(source_path, cmp_path, scope="checksum")
            else:
                diff, _, only_irods = self.diff_irods_localfs(source, cmp_path, scope="checksum")
        else:
            diff, _, only_irods, _ = diffs
        # Check space on destination.
        if not force:
            space = disk_usage(destination).free
            if size > (space - buff):
                logging.info(
                    'ERROR iRODS download: '+'Not enough space on local disk.',
                    exc_info=True)
                raise NotEnoughFreeSpace(
                    'ERROR iRODS download: '+'Not enough space on local disk.')
        # NOT the same force flag.  This overwrites the local file by default.
        # TODO should there be an option/switch for this 'clobber'ing?
        options = {kw.FORCE_FLAG_KW: ''}
        try:
            # Data object
            if self.is_dataobject(source) and len(diff + only_irods) > 0:
                logging.info(
                    'IRODS DOWNLOADING object: %s to %s',
                    source_path, cmp_path)
                self.irods_get(
                    source_path, cmp_path, options=options)
            # Collection
            # TODO add support for "downloading" empty collections?
            else:
                logging.info("IRODS DOWNLOAD started:")
                for irods_path, local_path in diff:
                    # Download data objects to distinct files.
                    logging.info(
                        'REPLACE: %s with %s', local_path, irods_path)
                    self.irods_get(irods_path, local_path, options=options)
                # Variable `only_irods` can contain data objects and
                # collections.
                for rel_path in only_irods:
                    # Create subdirectories and download.
                    rel_path = utils.PurePath(rel_path)
                    irods_path = source_path.joinpath(rel_path)
                    local_path = cmp_path.joinpath(rel_path)
                    if not local_path.parent.is_dir():
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                    logging.info(
                        'INFO: Downloading %s to %s', irods_path,
                        local_path)
                    self.irods_get(irods_path, local_path, options=options)
        except Exception as error:
            logging.info('DOWNLOAD ERROR', exc_info=True)
            raise error

    def walk_irods(self, path):
        root_subs = self._ses_man.session.collections.get(path).subcollections
        root_data_objects = self._ses_man.session.collections.get(path).data_objects
        collections, data_objects = [sub.path for sub in root_subs], \
                                    [data_object.path for data_object in root_data_objects]
        for col in collections:
            new_path = col
            for x in self.walk_irods(new_path):
                yield x
        yield path, collections, data_objects


    def recursive_upload(self, source: str, target: str) -> irods.collection.Collection:
        normalized_source_directories = []
        result = self.ensure_coll(target)
        files_in_folder = dict()
        for src_root, src_dirs, src_files in os.walk(source):
            src_dirs.sort()
            target_in_irods = (target + src_root[len(source):] + os.sep).replace(os.sep, '/')
            normalized_src_dirs_as_in_irods = [target_in_irods + source_dir for source_dir in src_dirs]
            files_ = [src_root + os.path.sep +  file for file in src_files]
            files_in_folder[target_in_irods] = files_
            normalized_source_directories.extend(normalized_src_dirs_as_in_irods)

        with ThreadPoolExecutor(20) as executor:
            [executor.submit(self.ensure_coll, target_col) for target_col in normalized_source_directories]
        with ThreadPoolExecutor(42) as file_executor:
            for file_destination in files_in_folder:
                [file_executor.submit(self.irods_put, independent_file, file_destination) 
                 for independent_file in files_in_folder[file_destination]]
        return result
    def diff_obj_file(self, objpath: str, fspath: str, scope: str = "size") -> tuple:
        """
        Compares and iRODS object to a file system file.

        Parameters
        ----------
        objpath: str
            irods collection or dataobject
        dirpath: str
            Local file or directory
        scope: str
            Syncing scope can be 'size' or 'checksum'
        Returns
        ----------
        tuple
            ([diff], [only_fs], [only_irods])
        '''

        """
        if os.path.isdir(fspath) and not os.path.isfile(fspath):
            raise IsADirectoryError("IRODS FS DIFF: file is a directory.")
        if self._ses_man.session.collections.exists(objpath):
            raise IsADirectoryError("IRODS FS DIFF: object exists already as collection. " + objpath)
        if not os.path.isfile(fspath) and self._ses_man.session.data_objects.exists(objpath):
            return ([], [], [objpath])
        if not self._ses_man.session.data_objects.exists(objpath) and os.path.isfile(fspath):
            return ([], [fspath], [])

        # both, file and object exist
        obj = self._ses_man.session.data_objects.get(objpath)
        if scope == "size":
            objsize = obj.size
            fsize = os.path.getsize(fspath)
            if objsize != fsize:
                return ([(objpath, fspath)], [])
            else:
                return ([], [], [])
        elif scope == "checksum":
            objcheck = obj.checksum
            if objcheck is None:
                try:
                    obj.chksum()
                    objcheck = obj.checksum
                except Exception:
                    logging.info('No checksum for %s', obj.path)
                    return ([(objpath, fspath)], [], [])
            if objcheck.startswith("sha2"):
                sha2obj = base64.b64decode(objcheck.split('sha2:')[1])
                with open(fspath, "rb") as f:
                    stream = f.read()
                    sha2 = hashlib.sha256(stream).digest()
                if sha2obj != sha2:
                    return ([(objpath, fspath)], [])
                else:
                    return ([], [], [])
            elif objcheck:
                # md5
                with open(fspath, "rb") as f:
                    stream = f.read()
                    md5 = hashlib.md5(stream).hexdigest()
                if objcheck != md5:
                    return ([(objpath, fspath)], [])
                else:
                    return ([], [], [])

    def diff_irods_localfs(self, coll: irods.collection.Collection,
                           dirpath: str, scope: str = "size") -> tuple:
        '''
        Compares and iRODS tree to a directory and lists files that are not in sync.

        Parameters
        ----------
        coll: irods collection
        dirpath: str
            Local directory
        scope: str
            Syncing scope can be 'size' or 'checksum'
        Returns
        ----------

        '''


        if dirpath is not None:
            if not os.access(dirpath, os.R_OK):
                raise PermissionError("IRODS FS DIFF: No rights to write to destination.")
            if not os.path.isdir(dirpath):
                raise IsADirectoryError("IRODS FS DIFF: directory is a file.")

        list_dir = self._get_files_relative_to_folder(dirpath)
        list_coll = self._get_dataobjects_relative_to_collection(coll)

        diff = []
        for locpartialpath in set(list_dir).intersection(list_coll):
            ipartialpath = locpartialpath.replace(os.sep, "/")
            irods_path = coll.path + '/' + ipartialpath
            data_object = self._ses_man.session.data_objects.get(irods_path)
            local_path = os.path.join(dirpath, locpartialpath)
            irods_and_local_path = (irods_path, local_path)
            if scope == "size":
                if data_object.size != os.path.getsize(local_path):
                    diff.append(irods_and_local_path)
            elif scope == "checksum":
                objcheck = data_object.checksum
                extracted_checksum = None
                used_objcheck = None
                force_add = False
                if objcheck is None:
                    try:
                        data_object.chksum()
                        objcheck = data_object.checksum
                    except irods.manager.data_object_manager.Server_Checksum_Warning:
                        logging.info('No checksum for %s/%s', coll.path, ipartialpath)
                        force_add = True
                if objcheck.startswith("sha2"):
                    used_objcheck = base64.b64decode(objcheck.split('sha2:')[1])
                    extracted_checksum = self.extract_checksum(local_path, lambda opened_stream: hashlib.sha256(opened_stream).digest())
                elif objcheck:
                    used_objcheck = objcheck
                    extracted_checksum = self.extract_checksum(local_path, lambda opened_stream: hashlib.md5(opened_stream).hexdigest())
                checksums_are_different = (extracted_checksum != used_objcheck)
                if force_add or checksums_are_different:
                    diff.append(irods_and_local_path)
            else:  # same paths, no scope
                diff.append(irods_and_local_path)

        # adding files that are not on iRODS, only present on local FS
        # adding files that are not on local FS, only present in iRODS
        # adding files that are stored on both devices with the same checksum/size
        irodsonly = list(set(list_coll).difference(list_dir))
        for i, _ in enumerate(irodsonly):
            irodsonly[i] = irodsonly[i].replace(os.sep, "/")
        return (diff, list(set(list_dir).difference(list_coll)), irodsonly)

    def extract_checksum(self, local_path, used_digest):
        with open(local_path, "rb") as f:
            stream = f.read()
            extracted_checksum = used_digest(stream)
        return extracted_checksum

    def _get_dataobjects_relative_to_collection(self, coll: irods.collection.Collection):
        if coll is None:
            return []
        listcoll = []
        if coll is not None:
            for root, _, objects in coll.walk():
                for obj in objects:
                    listcoll.append(os.path.join(root.path.split(coll.path)[1], obj.name).strip('/'))
        return listcoll

    def _get_files_relative_to_folder(self, dirpath: str):
        if dirpath is None:
            return []
        list_dir = []
        for root, _, files in os.walk(dirpath, topdown=False):
            for name in files:
                list_dir.append(os.path.join(root.split(dirpath)[1], name).strip(os.sep))
        return list_dir

    def delete_data(self, item: irods.collection.iRODSCollection):
        """
        Delete a data object or a collection recursively.
        Parameters
        ----------
        item: iRODS data object or collection
            item to delete
        """

        if self._ses_man.session.collections.exists(item.path):
            logging.info("IRODS DELETE: %s", item.path)
            try:
                item.remove(recurse=True, force=True)
            except irods.exception.CAT_NO_ACCESS_PERMISSION as cnap:
                print("ERROR IRODS DELETE: no permissions")
                raise cnap
        elif self._ses_man.session.data_objects.exists(item.path):
            logging.info("IRODS DELETE: %s", item.path)
            try:
                item.unlink(force=True)
            except irods.exception.CAT_NO_ACCESS_PERMISSION as cnap:
                print("ERROR IRODS DELETE: no permissions " + item.path)
                raise cnap

    def get_irods_size(self, path_names: list) -> int:
        """Collect the sizes of a set of iRODS data objects and/or
        collections and determine the total size.

        Parameters
        ----------
        path_names : list
            Names of logical iRODS paths.

        Returns
        -------
        int
            Total size [bytes] of all iRODS objects found from the
            logical paths in `path_names`.

        """
        irods_sizes = []
        for path_name in path_names:
            irods_name = utils.IrodsPath(path_name)
            if self.collection_exists(irods_name):
                irods_sizes.append(
                    utils.get_coll_size(
                        self.get_collection(irods_name)))
            elif self.dataobject_exists(irods_name):
                irods_sizes.append(
                    utils.get_data_size(
                        self.get_dataobject(irods_name)))
        return sum(irods_sizes)
