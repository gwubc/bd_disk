import requests
import json
from tqdm.auto import tqdm
import concurrent.futures
import os

class BaiduDiskDownloader:
    fileNames: list[str]
    downloadPaths: list[str]
    access_tokens: str
    max_concurrent: int

    def __init__(self, access_token: str, max_concurrent: int = 3):
        self.access_token = access_token
        self.max_concurrent = max_concurrent
        self.fileNames = []
        self.downloadPaths = []

    def add_download_task(self, fileName: str, downloadPath: str):
        self.fileNames.append(fileName)
        self.downloadPaths.append(downloadPath)

    def getFileId(self, fileName):
        if os.path.isabs(fileName):
            dir = os.path.dirname(fileName)
            fileName = os.path.basename(fileName)
        else:
            dir = "/"
        url = f"http://pan.baidu.com/rest/2.0/xpan/file?dir={dir}&access_token={self.access_token}&web=1&recursion=1&page=1&num=2&method=search&key={fileName}"
        headers = {'User-Agent': 'pan.baidu.com'}
        response = requests.get(url, headers=headers)
        responseData = json.loads(response.text.encode('utf8'))
        if len(responseData["list"]) != 1:
            if len(responseData["list"]) == 0:
                print("File not found")
            else:
                print("File not unique")
            raise Exception("File not found or not unique")
        fid = responseData["list"][0]["fs_id"]
        server_filename = responseData["list"][0]["server_filename"]
        return fid, server_filename

    def getDlink(self, fid):
        url = f"http://pan.baidu.com/rest/2.0/xpan/multimedia?method=filemetas&access_token={self.access_token}&fsids=[{fid}]&thumb=1&dlink=1&extra=1"
        headers = {'User-Agent': 'pan.baidu.com'}
        response = requests.get(url, headers=headers)
        responseData = json.loads(response.text.encode('utf8'))
        dlink = responseData["list"][0]["dlink"]
        return f"{dlink}&access_token={self.access_token}"


    def download_file(self, url, downloadPath):
        headers = {'User-Agent': 'pan.baidu.com'}
        response = requests.get(url, stream=True, headers=headers)
        file_size = int(response.headers.get('content-length', 0))
        with (open(downloadPath, 'wb') as f,
              tqdm(desc=f'Downloading {downloadPath}', total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as progress):
            for data in response.iter_content(1024):
                f.write(data)
                progress.update(len(data))
        return

    def run(self, fileName: str=None, downloadPath: str=None):
        if fileName is not None and downloadPath is not None:
            self.add_download_task(fileName, downloadPath)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = []
            for fileName, downloadPath in zip(self.fileNames, self.downloadPaths):
                fid, _ = self.getFileId(fileName)
                dlink = self.getDlink(fid)
                futures.append(executor.submit(self.download_file, dlink, downloadPath))
