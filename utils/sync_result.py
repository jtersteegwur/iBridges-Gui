""" Utilities for synchronising files

"""

# def get_diff_download(source, target)
## Should result in a list[SyncResult] comprising of:
#### Files that are different
#### Files that are present on target, but not on source
# def get_diff_upload(source, target)
#### Files that are different
#### Files that are different on source, but not on target
# def get_diff_both(source, target)

class SyncResult:
    """
     Return value object for determining diffs
     """
    source_path: str = None  # can be both a irods or (local) filesystem
    target_path: str = None  # can be both a irods or (local) filesystem
    source_file_size: int = None  # bytes

    def __init__(self, source, target, filesize):
        self.source_path = source
        self.target_path = target
        self.source_file_size = filesize
