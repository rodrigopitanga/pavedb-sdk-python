# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Rodrigo Rodrigues da Silva. See ../LICENSE.

"""Chapter 9: the same Lattice search through a real PaveDB HTTP server."""

from __future__ import annotations

import os
import socket
import subprocess
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from pavesdk.client import connect
from shared.lattice import seed


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def wait_for_server(url: str, server: subprocess.Popen[bytes]) -> None:
    for _ in range(40):
        if server.poll() is not None:
            raise RuntimeError("pavesrv exited before becoming ready")
        try:
            with urlopen(f"{url}/health/live", timeout=1):
                return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("pavesrv did not become ready")


def main() -> None:
    with TemporaryDirectory(prefix="pavedb-lattice-") as data_dir:
        with connect(data_dir, tenant="lattice") as db:
            seed(db)
        port = free_port()
        url = f"http://127.0.0.1:{port}"
        environment = os.environ | {
            "PAVEDB_DEV": "1",
            "PAVEDB_AUTH__MODE": "none",
            "PAVEDB_SERVER__HOST": "127.0.0.1",
            "PAVEDB_SERVER__PORT": str(port),
        }
        server = subprocess.Popen(["pavesrv", "--data-dir", data_dir], env=environment)
        try:
            wait_for_server(url, server)
            with connect(url, tenant="lattice") as db:
                for hit in db.collection("standards").search(
                    "design and evaluate algorithms", k=3
                ):
                    print(f"{hit['score']:.3f} {hit['meta']['code']} {hit['text']}")
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    main()
