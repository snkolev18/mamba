import cgi
import datetime
import email.utils
import multiprocessing
import os
import queue
import re
import threading
from typing import Callable, Optional
from urllib.parse import urlparse, unquote


import requests
import tqdm

from file_objects import FileDownload, FileInfo


def set_mtime(path: str, mtime: datetime.datetime):
    t = mtime.timestamp()
    os.utime(path, (t, t))


def get_remote_file_info(url: str, client, file_size: Optional[int] = None) -> FileInfo:
    filename = urlparse(url).path.split("/")[-1]

    resp = client.head(url, allow_redirects=True)
    if resp.status_code == 405:
        resp = client.get(url, allow_redirects=True, stream=True)
    if not (200 <= resp.status_code <= 299):
        return FileInfo(url, filename, False, None, None)

    size = resp.headers["Content-Length"] or None
    if size:
        size = int(size)
    elif file_size is not None:
        size = file_size

    last_modified = resp.headers["Last-Modified"] or None
    if last_modified:
        if re.match(r"^\d+$", last_modified):
            last_modified = datetime.datetime.fromtimestamp(int(last_modified) / 1000, datetime.timezone.utc)
        else:
            last_modified = email.utils.parsedate_to_datetime(last_modified)

    content_disposition = resp.headers["Content-Disposition"] if "Content-Disposition" in resp.headers.keys() else None
    if content_disposition:
        value, params = cgi.parse_header(content_disposition)
        if value == "attachment":
            if 'filename*' in params:
                encoding, filename = re.match("(.+?)'.*?'\"(.*)\"", params['filename*']).groups()
                filename = unquote(filename, encoding)
            elif "filename" in params:
                filename = params['filename'].strip('"')

    resp.close()

    fi = FileInfo(url, filename, True, size, last_modified)
    return fi


def get_local_file_info(path: str) -> FileInfo:
    size = None
    last_modified = None
    exists = False
    if os.path.isfile(path):
        exists = True
        stat = os.stat(path)
        last_modified = datetime.datetime.fromtimestamp(stat.st_mtime, datetime.datetime.now().astimezone().tzinfo)
        size = stat.st_size

    filename = None
    if not (path.endswith("/") or os.path.isdir(path)):
        filename = os.path.basename(path)

    fi = FileInfo(path, filename, exists, size, last_modified)
    return fi


def prepare_download(url: str, dest_path: str, client, file_size: Optional[int] = None) -> FileDownload:
    remote_file_info = get_remote_file_info(url, client, file_size)
    if dest_path.endswith("/") or os.path.isdir(dest_path):
        dest_path = os.path.join(dest_path, remote_file_info.filename)
    local_file_info = get_local_file_info(dest_path)

    if not remote_file_info.exists:
        return None

    sizes_equal = None
    remote_is_not_newer = None
    if local_file_info.exists:
        if remote_file_info.size is not None:
            sizes_equal = remote_file_info.size == local_file_info.size
        if remote_file_info.last_modified is not None:
            remote_is_not_newer = remote_file_info.last_modified <= local_file_info.last_modified

    download = None
    if (remote_is_not_newer is None and sizes_equal is None) or remote_is_not_newer is False or sizes_equal is False:
        download = True
    if (remote_is_not_newer is None and sizes_equal) or (sizes_equal is None and remote_is_not_newer):
        download = False

    # assert download is not None

    if download:
        os.makedirs(os.path.dirname(local_file_info.path), exist_ok=True)

    fd = FileDownload(url,
                      local_file_info.path, os.path.basename(local_file_info.path),
                      remote_file_info.size, download, remote_file_info.last_modified)

    return fd


def file_download(url: str,
                  dest_path: str,
                  client=None,
                  chunk_size: int = 8192,
                  threads: Optional[int] = None,
                  progress_factory_fn: Callable[[str, int], Callable[[int], None]] = None,
                  file_size: Optional[int] = None,
                  force_download=False) -> str:
    if client is None:
        client = requests
    if threads is None:
        threads = multiprocessing.cpu_count()

    download_info = prepare_download(url, dest_path, client, file_size)
    file_size = download_info.size
    dest_path = download_info.dest_path
    url = download_info.url
    if not (download_info.download or force_download):
        print(f"Skipping {url} because it already exists and is up to date")
        return dest_path

    if progress_factory_fn:
        disk_write_progress_fn = progress_factory_fn(f"Writing {download_info.filename} to disk", download_info.size)

    global writer_queue
    writer_queue = queue.Queue()

    def _download_partition(start: int, size: int) -> None:
        response = client.get(url, stream=True, headers={"Range": f"bytes={start}-{start + size - 1}"})
        for chunk in response.iter_content(chunk_size):
            writer_queue.put((start, chunk))
            start += len(chunk)

    def _write_chunks():
        total_bytes_written = 0
        with open(dest_path, "wb") as fp:
            while total_bytes_written < file_size:
                start, chunk = writer_queue.get()
                fp.seek(start)
                bytes_written = fp.write(chunk)
                total_bytes_written += bytes_written
                if disk_write_progress_fn is not None:
                    disk_write_progress_fn(bytes_written)

    partition_size = file_size // threads
    partitions = [
        (partition_start, min(partition_size, file_size - partition_start))
        for partition_start in
        range(0, file_size, partition_size)]
    # TODO: Switch to TPE
    download_threads = [
        threading.Thread(target=_download_partition, args=(start, size), name=f"ThreadForStartByte-{start}")
        for start, size in
        partitions
    ]

    for dt in download_threads:
        dt.start()
    writer_thread = threading.Thread(target=_write_chunks)
    writer_thread.start()
    for dt in download_threads:
        dt.join()
    writer_thread.join()
    set_mtime(dest_path, download_info.remote_timestamp)
    return dest_path


def tqdm_progress_factory(desc, size):
    pb = tqdm.tqdm(desc=desc, total=size, unit="B", unit_scale=True, unit_divisor=1024)

    return pb.update


def file_download_tqdm(url, dest_path, client=None, *args, **kwargs):
    return file_download(url, dest_path, client, *args, **kwargs, progress_factory_fn=tqdm_progress_factory)
