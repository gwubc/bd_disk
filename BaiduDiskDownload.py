import requests
import json
from tqdm.auto import tqdm

class BaiduDiskDownloader:
    fileName: str
    downloadPath: str
    access_token: str

    def __init__(self, fileName: str, downloadPath: str, access_token: str):
        self.fileName = fileName
        self.downloadPath = downloadPath
        self.access_token = access_token

    def getFileId(self):
        url = f"http://pan.baidu.com/rest/2.0/xpan/file?dir=/&access_token={self.access_token}&web=1&recursion=1&page=1&num=2&method=search&key={self.fileName}"
        headers = {'User-Agent': 'pan.baidu.com'}
        response = requests.get(url, headers=headers)
        responseData = json.loads(response.text.encode('utf8'))
        if len(responseData["list"]) != 1:
            print("File not unique")
            return
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


    def download_file(self, url, filename):
        headers = {'User-Agent': 'pan.baidu.com'}
        response = requests.get(url, stream=True, headers=headers)
        file_size = int(response.headers.get('content-length', 0))

        # Initialize progress bar with file size
        progress = tqdm(response.iter_content(1024), f'Downloading {filename}', total=file_size, unit='B',
                        unit_scale=True,
                        unit_divisor=1024)

        # Open the file for writing
        with open(filename, 'wb') as f:
            for data in progress:
                # Write data read from the URL to the file
                f.write(data)
                # Update the progress bar
                progress.update(len(data))
        progress.close()
        return

    def run(self):
        fid, _ = self.getFileId()
        dlink = self.getDlink(fid)
        self.download_file(dlink, self.downloadPath)
