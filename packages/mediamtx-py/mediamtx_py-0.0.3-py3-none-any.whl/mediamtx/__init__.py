import requests
import urllib.request
import platform as pf
import tarfile
import yaml
import subprocess
import os
import zipfile
import logging

logger = logging.getLogger(__name__)

MEDIAMTX_URL = "https://github.com/bluenviron/mediamtx/releases/"
LATEST_API_URL = "https://api.github.com/repos/bluenviron/mediamtx/releases/latest"


class Singleton(object):
    def __new__(cls, *args, **kargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


class MediaMTX(Singleton):
    def __init__(
        self,
        arch: str,
        platform: str = pf.system().lower(),
        version: str = "latest",
        overwrite: bool = True,
    ):
        self.platform = platform
        self.is_running_flag = False
        if version == "latest":
            latest_info = requests.get(LATEST_API_URL).json()
            version = latest_info["tag_name"]
        self.download_mediamtx(arch, platform, version, overwrite)

    def download_mediamtx(
        self, arch: str, platform: str, version: str, overwrite: bool = True
    ):
        if arch not in ["amd64", "arm64"]:
            logger.info(f"Warning: architecture '{arch}' may not be supported.")
        if platform not in ["linux", "windows", "darwin"]:
            logger.info(f"Warning: platform '{platform}' may not be supported.")
        if not overwrite:
            if self.platform in ["linux", "darwin"] and os.path.exists(
                "mediamtx/mediamtx"
            ):
                # Binary already exists
                return
            if self.platform == "windows" and os.path.exists("mediamtx/mediamtx.exe"):
                # Binary already exists
                return

        # Download binary
        logger.info("Downloading MediaMTX...")
        os.makedirs("mediamtx/")
        url = (
            f"{MEDIAMTX_URL}download/{version}/mediamtx_{version}_{platform}_{arch}"
            + (".zip" if platform == "windows" else ".tar.gz")
        )
        try:
            tmp = urllib.request.urlopen(url)
            tmp.close()
        except urllib.request.HTTPError:
            raise Exception(f"URL {url} does not exist.")

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
        logger.info("Download Complete")

        with open("mediamtx/mediamtx.yml", encoding="utf-8") as f:
            self.yaml = yaml.safe_load(f)

    def start(self) -> None:
        logger.info("Starting MediaMTX...")
        if self.platform == "windows":
            self.proc = subprocess.Popen(
                ["mediamtx/mediamtx.exe", "mediamtx/mediamtx.yml"]
            )
        else:
            self.proc = subprocess.Popen(["mediamtx/mediamtx", "mediamtx/mediamtx.yml"])
        self.is_running_flag = True
        logger.info("Process Started")

    def stop(self) -> None:
        logger.info("Stopping MediaMTX...")
        self.proc.kill()
        self.is_running_flag = False
        logger.info("Stopped MediaMTX")

    def is_running(self) -> bool:
        return self.is_running_flag

    def get_yaml(self) -> dict:
        with open("mediamtx/mediamtx.yml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def set_yaml(self, data: dict):
        with open("mediamtx/mediamtx.yml", "w", encoding="utf-8") as f:
            return yaml.safe_dump(data, f)

    def add_path(self, name, url):
        self.yaml["paths"][name] = {"source": url}
        with open("mediamtx/mediamtx.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(self.yaml, f)
