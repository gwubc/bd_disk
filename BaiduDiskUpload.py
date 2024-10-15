import os
import io
import json
import typing

from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import requests


def generate_md5(data):
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()


def split_file_and_generate_md5(file_path, block_size=16 * 1024 * 1024):  # n * MB block size
    hashes = []
    with open(file_path, 'rb') as f:
        while True:
            block_data = f.read(block_size)
            if not block_data:
                break  # End of file
            block_md5 = generate_md5(block_data)
            hashes.append(block_md5)
    return hashes


class BaiduDiskUploader:
    filePath: str
    access_token: str
    blockSize: int

    fileName: str
    targetPath: str
    fileSize: str
    block_list: typing.List[str]
    waitingUpload: typing.List[int]  # for index i, if uploaded i = 1, else i = 0
    block_list_str: str

    def __init__(self, filePath: str, access_token: str, blockSize: int = 0):
        self.filePath = filePath
        self.access_token = access_token
        self.blockSize = blockSize
        self.fileName = Path(filePath).name
        self.targetPath = os.path.join("/apps/download_anywhere", self.fileName)
        self.fileSize = os.path.getsize(filePath)

        if blockSize == 0:
            self.blockSize = self.chooseBlockSize(self.fileSize)

    def chooseBlockSize(self, fileSize) -> int:
        if fileSize < 4 * 1024 * 1024 * 1024:
            return 4 * 1024 * 1024
        if fileSize < 8 * 1024 * 1024 * 1024:
            return 8 * 1024 * 1024
        if fileSize < 16 * 1024 * 1024 * 1024:
            return 16 * 1024 * 1024
        return 32 * 1024 * 1024

    def getBlockList(self) -> typing.List[str]:
        return split_file_and_generate_md5(self.filePath, self.blockSize)

    def setup(self):
        self.block_list = self.getBlockList()
        self.block_list_str = f"{self.block_list}".replace("'", '"')
        self.waitingUpload = []
        for i in self.block_list:
            self.waitingUpload.append(0)
        print(f"block count: {len(self.block_list)}")

    def run(self):
        self.setup()
        precreateResponse = self.precreate()
        self.uploadid = precreateResponse["uploadid"]
        self.upload()
        self.create()

    def precreate(self):
        url = f"http://pan.baidu.com/rest/2.0/xpan/file?method=precreate&access_token={self.access_token}"
        payload = {
            'path': self.targetPath,
            'size': self.fileSize,
            'rtype': '1',
            'isdir': '0',
            'autoinit': '1',
            'block_list': self.block_list_str
        }
        response = requests.post(url, headers={}, data=payload)
        response = json.loads(response.text.encode('utf8'))
        print(response)
        return response

    def getPartOfDataFromFile(self, path, offset, size):
        try:
            with open(path, 'rb') as f:  # 'rb' for reading in binary mode
                f.seek(offset)  # Move to the starting index
                data = f.read(size)  # Read 'length' bytes from the current position
                return io.BytesIO(data)
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def uploadPart(self, index):
        params = {
            "access_token": self.access_token,
            "method": "upload",
            "type": "tmpfile",
            "path": self.targetPath,
            "uploadid": self.uploadid,
            "partseq": index
        }
        file = [("file", self.getPartOfDataFromFile(self.filePath, index * self.blockSize, self.blockSize))]
        response = requests.post("https://d.pcs.baidu.com/rest/2.0/pcs/superfile2?method=upload", params=params,
                                 files=file)
        return json.loads(response.text.encode('utf8'))

    def getProgessStr(self, progess, total):
        progessOutOfTen = int(progess / total * 10)
        s = "[" + "=" * progessOutOfTen + "_" * (10 - progessOutOfTen) + f"] {progess}/{total}"
        return s
    def threaded_upload(self, i):
        if self.waitingUpload[i] == 0:
            uploadResponse = self.uploadPart(i)
            md5Uploaded = uploadResponse["md5"]
            if md5Uploaded == self.block_list[i]:
                self.waitingUpload[i] = 1
                print(f"\r{self.getProgessStr(self.waitingUpload.count(1), len(self.waitingUpload))}", end='', flush=True)


    def upload(self):
        if all(x == 1 for x in self.waitingUpload):
            return
        with ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(self.threaded_upload, range(len(self.waitingUpload)), timeout=10)
            executor.shutdown(wait=True)
        return self.upload()

    def create(self):
        url = f"https://pan.baidu.com/rest/2.0/xpan/file?method=create&access_token={self.access_token}"

        payload = {
            'path': self.targetPath,
            'size': self.fileSize,
            'rtype': '1',
            'isdir': '0',
            'uploadid': self.uploadid,
            'block_list': self.block_list_str
        }

        response = requests.post(url, headers={}, data=payload)

        response = json.loads(response.text.encode('utf8'))
        print("\n", response)
        return response

