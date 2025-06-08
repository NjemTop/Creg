import requests
from urllib.parse import quote
import logging
from logger.log_config import setup_logger, get_abs_log_path

scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


class NextcloudManager:
    def __init__(self, base_url, username, password, timeout=30):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout

    def _build_url(self, path):
        return f"{self.base_url}/remote.php/dav/files/{self.username}/{quote(path)}"

    def create_folder(self, path):
        url = self._build_url(path)
        requests.request("MKCOL", url, auth=(self.username, self.password), timeout=self.timeout)

    def upload_file(self, local_path, remote_path):
        url = self._build_url(remote_path)
        with open(local_path, 'rb') as f:
            resp = requests.put(url, data=f, auth=(self.username, self.password), timeout=self.timeout)
        if resp.status_code not in (200, 201, 204):
            scripts_error_logger.error("Ошибка загрузки %s: %s", remote_path, resp.text)

    def folder_exists(self, path):
        url = self._build_url(path)
        resp = requests.request("PROPFIND", url, auth=(self.username, self.password), timeout=self.timeout)
        return resp.status_code in (207, 200)

    def list_folder(self, path):
        url = self._build_url(path)
        resp = requests.request("PROPFIND", url, auth=(self.username, self.password), timeout=self.timeout)
        return resp.text if resp.status_code in (207, 200) else ""

    def move_folder(self, src, dest):
        src_url = self._build_url(src)
        dest_url = self._build_url(dest)
        headers = {"Destination": dest_url}
        requests.request("MOVE", src_url, headers=headers, auth=(self.username, self.password), timeout=self.timeout)

    def move_internal_folders(self, src_dir, dest_dir):
        if self.folder_exists(src_dir):
            self.move_folder(src_dir, dest_dir)
