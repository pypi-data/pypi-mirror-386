import os
import platform
import subprocess
import time
from pathlib import Path
import urllib.request
import requests
import atexit
import signal
import socket
import uuid
from vector_cache.version import __version__

import grpc
from pb.vector_cache_pb2_grpc import VectorCacheServiceStub
from pb.vector_cache_pb2 import SetRequest, SetResponse, GetRequest, GetResponse
from google.protobuf.json_format import MessageToDict

from warnings import deprecated

class VectorCache:
    _servers = {}  # Singleton per port

    def __new__(cls, port=6379):
        if port in cls._servers:
            return cls._servers[port]
        instance = super().__new__(cls)
        cls._servers[port] = instance
        return instance

    def __init__(self, port=6379):
        if hasattr(self, "_initialized"):
            return  # Avoid reinitializing
        self._initialized = True

        self.port = port
        self.proc = None
        self.binary_path = self._get_binary_path()

        if self._is_server_running():
            print(f"ℹ️ VectorCache server already running on port {self.port}, reusing it.")
        else:
            self.start()

        atexit.register(self.stop)
        signal.signal(signal.SIGTERM, lambda *args: self.stop())

    def _is_server_running(self):
        """Check if a VectorCache server is already running on this port."""
        try:
            resp = requests.post(f"http://localhost:{self.port}/search", json={"emb": [], "topK": 1}, timeout=1)
            return resp.status_code == 200 or resp.status_code == 404
        except requests.RequestException:
            return False

    def _get_binary_path(self):
        system = platform.system().lower()
        arch = platform.machine().lower()

        if system == "linux":
            filename = "db_server_linux_amd64"
        elif system == "darwin":
            filename = "db_server_darwin_amd64"
        elif system == "windows":
            filename = "db_server_windows_amd64.exe"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

        bin_dir = Path(__file__).parent / "bin"
        bin_dir.mkdir(exist_ok=True)
        binary_path = bin_dir / filename

        if not binary_path.exists():
            version = f"v{__version__}"
            url = f"https://github.com/vector-cache/vector-cache/releases/download/{version}/{filename}"
            print(f"⬇️ Downloading {filename} from {url}")
            urllib.request.urlretrieve(url, binary_path)
            os.chmod(binary_path, 0o755)

        return str(binary_path)

    def start(self):
        if self.proc is None:
            self.proc = subprocess.Popen(
                [self.binary_path, f"-port={self.port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)
            print(f"✅ VectorCache server started at http://localhost:{self.port}")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            print(f"🛑 VectorCache server on port {self.port} stopped")
            self.proc = None

    @deprecated("use 'search' instead which uses gRPC calls")
    def search_http(self, emb, top_k=5):
        payload = {"emb": emb, "topK": top_k}
        resp = requests.post(f"http://localhost:{self.port}/search", json=payload)
        if resp.status_code != 200:
            print(f"⚠️ Search failed: {resp.text}")
            return None
        return resp.json()

    @deprecated("use 'set' instead which uses gRPC calls")
    def set_http(self, emb, data):
        uid = uuid.uuid4()
        payload = {"uid": uid, "emb": emb, "data": data}
        resp = requests.post(f"http://localhost:{self.port}/set", json=payload)
        if resp.status_code != 200:
            print(f"⚠️ Set failed: {resp.text}")
            return None
        return resp.json()

    def search(self, emb, top_k=5):
        try:
            with grpc.insecure_channel(f"localhost:{self.port}") as channel:
                stub = VectorCacheServiceStub(channel)
                response: GetResponse = stub.Get(GetRequest(emb=emb, topK=top_k))

                # TODO: Add dataclass for better typing
                return [MessageToDict(r) for r in response.results]
        except grpc.RpcError as e:
            print(f"⚠️ Search failed: {e.details()}")

    def set(self, emb, data={}):
        try:
            uid = str(uuid.uuid4())
            with grpc.insecure_channel(f"localhost:{self.port}") as channel:
                stub = VectorCacheServiceStub(channel)
                response: SetResponse = stub.Set(SetRequest(uid=uid, emb=emb, data=data))

                # TODO: Add dataclass for better typing
                return MessageToDict(response)
        except grpc.RpcError as e:
            print(f"⚠️ Set failed: {e.details()}")



def main():
    c = VectorCache()
    
    c.set([1, 2], {"foo": "bar0"})
    c.set([2, 3], {"foo": "bar1"})
    c.set([3, 4], {"foo": "bar2"})

    response = c.search([3, 4], 3)
    print(response)

if __name__ == "__main__":
    main()
