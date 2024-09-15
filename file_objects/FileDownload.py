import datetime


class FileDownload(object):
    def __init__(self, url: str, dest_path: str, filename: str, size: int, download: bool,
                 remote_timestamp: datetime.datetime):
        self.download = download
        self.size = size
        self.filename = filename
        self.dest_path = dest_path
        self.url = url
        self.remote_timestamp = remote_timestamp