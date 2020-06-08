"""
main.py threads url
"""

import os
import sys
from threading import Thread, active_count

import certifi
import urllib3
from tqdm import tqdm

http = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())


class Download(object):
    def __init__(self, url: str, poolsize: int = 4):
        self.url = url
        self.filename = url.split("/")[-1]
        self.poolsize = poolsize
        self.total_length = self.get_size()
        self.partsize, self.remainder = divmod(self.total_length, poolsize)
        print(f"Total: {self.total_length}")
        print(f"Partsize: {self.partsize}, Remainder: {self.remainder}")
        print(self.partsize * poolsize + self.remainder)

    def run(self):
        start = 0
        for each in range(self.poolsize):
            if each == self.poolsize - 1:
                end = self.total_length
            else:
                end = start + self.partsize
            process = Thread(target=self.doshit, args=(start, end, each))
            start += self.partsize + 1
            process.start()
            if end == self.remainder:
                print("Downloading..")
                process.join()
        # a really dumb way to block
        while active_count() > 1:
            pass
        self.combine()

    def doshit(self, start, end, num):
        chunk = self.get_chunk(start, end)
        self.write_part(chunk, num)

    def get_size(self) -> int:
        request = http.request("HEAD", self.url)
        size = int(request.headers["Content-Length"])
        print(f"Total length: {size}")
        return size

    def get_chunk(self, start: int, end: int) -> bytes:
        print(f"Getting chunk {start} to {end}")
        headers = {"Range": f"bytes={start}-{end}"}
        request = http.request(
            "GET", self.url, headers=headers, preload_content=False
        )
        current = b''
        ssize = round(self.total_length/100)
        with tqdm(total=self.partsize) as pbar:
            for chunk in request.stream(ssize):
                pbar.update(ssize)
                current += chunk
        return current

    def write_part(self, data: bytes, num: int):
        with open(f"{self.filename}.{num}", "wb+") as f:
            f.write(data)
        print(f"Wrote {len(data)} to {self.filename}.{num}")

    def combine(self):
        with open(self.filename, "ab+") as mainfile:
            for each in range(self.poolsize):
                partfile = f"{self.filename}.{each}"
                print(f"Appending {partfile} to {self.filename}")
                with open(partfile, "rb+") as tmp:
                    mainfile.write(tmp.read())
                os.remove(partfile)


if __name__ == "__main__":
    try:
        url = sys.argv[2]
        size = sys.argv[1]
    except:
        sys.exit(__doc__)
    else:
        if size.isdigit() is False:
            sys.exit(__doc__)
        else:
            dl = Download(url, int(size))
            dl.run()
