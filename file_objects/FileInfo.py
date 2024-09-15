import datetime
from typing import Optional


class FileInfo(object):
    def __init__(self, path: str, filename: str, exists: bool, size: Optional[int],
                 last_modified: Optional[datetime.datetime]):
        self.last_modified = last_modified
        self.size = size
        self.exists = exists
        self.filename = filename
        self.path = path
