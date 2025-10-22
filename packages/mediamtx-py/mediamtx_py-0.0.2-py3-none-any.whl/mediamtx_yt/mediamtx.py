import urllib.request, platform, tarfile, yaml, subprocess
import os
import zipfile


MEDIAMTX_URLS = {
    "Linux": "https://github.com/bluenviron/mediamtx/releases/download/v1.14.0/mediamtx_v1.14.0_linux_amd64.tar.gz",
    "Windows": "https://github.com/bluenviron/mediamtx/releases/download/v1.14.0/mediamtx_v1.14.0_windows_amd64.zip",
}


class Singleton(object):
    def __new__(cls, *args, **kargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


class MediaMTX(Singleton):
    def __init__(self):
        self.system = platform.system()
        if self.system not in MEDIAMTX_URLS:
            raise Exception("Unsupported OS")
        url = MEDIAMTX_URLS[self.system]
        os.makedirs("mediamtx/", exist_ok=True)
        if url.endswith(".tar.gz"):
            urllib.request.urlretrieve(url, "mediamtx.tar.gz")
            with tarfile.open("mediamtx.tar.gz", mode="r:gz") as tar:
                tar.extractall("mediamtx/")
            os.remove("mediamtx.tar.gz")
        elif url.endswith(".zip"):
            urllib.request.urlretrieve(url, "mediamtx.zip")
            with zipfile.ZipFile("mediamtx.zip", "r") as zip_ref:
                zip_ref.extractall("mediamtx/")
            os.remove("mediamtx.zip")
        with open("mediamtx/mediamtx.yml", encoding="utf-8") as f:
            self.yaml = yaml.safe_load(f)

    def start(self):
        if self.system == "Linux":
            self.proc = subprocess.Popen(
                ["mediamtx/mediamtx", "/mediamtx/mediamtx.yml"]
            )
        elif self.system == "Windows":
            self.proc = subprocess.Popen(
                ["mediamtx/mediamtx.exe", "/mediamtx/mediamtx.yml"]
            )

    def stop(self):
        self.proc.kill()

    def getYaml(self):
        with open("mediamtx/mediamtx.yml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def setYaml(self, data):
        with open("mediamtx/mediamtx.yml", "w", encoding="utf-8") as f:
            return yaml.safe_dump(data, f)

    def addPath(self, name, url):
        self.yaml["paths"][name] = {"source": url}
        with open("mediamtx/mediamtx.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(self.yaml, f)


mtx = MediaMTX()
mtx.start()
mtx.stop()
