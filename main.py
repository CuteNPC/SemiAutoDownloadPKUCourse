import os
import requests
from typing import Dict, List
import json
import sys
from tqdm import tqdm
import subprocess
import shutil
import time


class Task():

    def __init__(self, url: str, cache: str, output: str, headers: Dict[str, str]) -> None:
        self.url = url
        url_, arg = self.url.split("?")
        split_url = url_.split('/')
        self.title, self.sub_title = [
            pair.split("=")[-1] for pair in arg.split("&")]
        self.output_filename = self.title + self.sub_title + '.mp4'
        self.m3u8_file = split_url[-1]
        self.task_id = split_url[-3]
        self.url_prefix = '/'.join(split_url[:-1]) + '/'
        self.cache_path = os.path.join(cache, self.task_id)
        self.output_path = os.path.join(output, self.output_filename)
        self.headers = headers.copy()
        self.failed = False

    def auto_retry_get(self, url: str, retry_times: int = 5, cold_time: float = 0.05):
        for i in range(retry_times):
            try:
                response = requests.get(url=url, headers=self.headers)
                if response.ok:
                    return response
            except:
                pass
            time.sleep(cold_time)
        raise ConnectionError

    def get_m3u8_and_key(self):
        if self.failed:
            return
        try:
            response = self.auto_retry_get(self.url_prefix + self.m3u8_file)
        except:
            self.failed = True
            print("Can't download m3u8")
            return
        self.m3u8: str = response.text
        self.m3u8_lines = self.m3u8.split("\n")
        self.segments = [
            line for line in self.m3u8_lines if (not line.startswith("#")) and len(line) > 0]
        self.key_url = self.m3u8_lines[5][31:-1]
        try:
            response = self.auto_retry_get(self.key_url)
        except:
            self.failed = True
            print("Can't download key, may be error token?")
            return
        self.key: str = response.text
        self.m3u8_lines[5] = '#EXT-X-KEY:METHOD=AES-128,URI=\"keyfile.key\"'
        self.m3u8 = '\n'.join(self.m3u8_lines)

    def get_segment(self):
        if self.failed:
            return
        try:
            os.makedirs(self.cache_path, exist_ok=True)
            with open(os.path.join(self.cache_path, "index.m3u8"), 'w') as fp:
                fp.write(self.m3u8)
            with open(os.path.join(self.cache_path, "keyfile.key"), 'w') as fp:
                fp.write(self.key)
            print(f"Downloading {self.output_filename}")
            for id, segment in enumerate(tqdm(self.segments)):
                response = self.auto_retry_get(url=self.url_prefix + segment)
                with open(os.path.join(self.cache_path, segment), 'wb') as fp:
                    fp.write(response.content)
            print(f"Downloading Success")
            print(f"Merging {self.output_filename}")
            command = f'ffmpeg -allowed_extensions ALL -protocol_whitelist "file,http,https,tls,crypto" -i index.m3u8 -c copy {os.path.abspath(self.output_path)}'
            result = subprocess.run(command, shell=True, cwd=os.path.abspath(
                self.cache_path), capture_output=True)
            if result.returncode != 0:
                print(result.stderr)
                raise SystemError
            print(f"Merging Success")
        except Exception as e:
            self.failed = True
            print(f"Error: {e}")
        try:
            shutil.rmtree(self.cache_path)
        except:
            pass


class Main():

    def __init__(self) -> None:
        print("Initializing")
        json_data = self.get_args()
        self.cache: str = json_data["cache"]
        self.output: str = json_data["output"]
        os.makedirs(self.cache, exist_ok=True)
        os.makedirs(self.output, exist_ok=True)
        self.headers: Dict[str, str] = self.load_headers(json_data["headers"])
        self.headers["cookie"] = "_token=" + \
            self.load_token(json_data["token"])
        self.url_list = self.load_url_list(json_data["course"])
        self.tasks: List[Task] = []
        for url in self.url_list:
            self.tasks.append(
                Task(url, self.cache, self.output, self.headers.copy()))
        print("Initializing Success")

    def __call__(self) -> None:
        print("Downloading m3u8 and key")
        for task in self.tasks:
            task.get_m3u8_and_key()
        print("Downloading m3u8 and key Success")
        for task in self.tasks:
            task.get_segment()

    def load_headers(self, file_path) -> Dict[str, str]:
        with open(file_path, "r", encoding="UTF-8") as fp:
            lines = fp.readlines()
        lines = [line.split(":") for line in lines]
        dicts = {key.strip(): value.strip() for key, value in lines}
        return dicts

    def load_token(self, file_path) -> str:
        with open(file_path, "r", encoding="UTF-8") as fp:
            lines = fp.readlines()
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if len(line) > 0]
        assert len(lines) > 0, "Empty token file\n"
        return lines[0]

    def load_url_list(self, file_path) -> str:
        with open(file_path, "r", encoding="UTF-8") as fp:
            lines = fp.readlines()
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if len(line) > 0]
        return lines

    def get_args(self):
        file_path = "config.json" if len(sys.argv) < 2 else sys.argv[1]
        with open(file_path, "r", encoding="UTF-8") as fp:
            json_data = json.load(fp)
        return json_data


if __name__ == "__main__":
    Main()()
