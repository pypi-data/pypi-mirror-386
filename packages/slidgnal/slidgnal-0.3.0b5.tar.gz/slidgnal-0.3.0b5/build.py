# build script for slidgnal extension module

import os
import platform
import shutil
import subprocess
from pathlib import Path
from urllib.request import urlretrieve

LIBSIGNAL_FFI_URL = (
    "https://mau.dev/tulir/gomuks-build-docker/-/jobs/{}/artifacts/raw/libsignal_ffi.a"
)


def main():
    if not shutil.which("go"):
        raise RuntimeError(
            "Cannot find the go executable in $PATH. "
            "Make you sure install golang, via your package manager or https://go.dev/dl/"
        )
    fetch_libsignal()
    os.environ["PATH"] = os.path.expanduser("~/go/bin") + ":" + os.environ["PATH"]
    subprocess.run(["go", "install", "github.com/go-python/gopy@master"], check=True)
    subprocess.run(
        ["go", "install", "golang.org/x/tools/cmd/goimports@latest"], check=True
    )
    src_path = Path(".") / "slidgnal"
    subprocess.run(
        [
            "gopy",
            "build",
            "-output=generated",
            "-no-make=true",
            ".",
        ],
        cwd=src_path,
        check=True,
    )


def fetch_libsignal():
    # IMPORTANT: Update job version when updating Go libraries.
    # Find latest pipeline under https://mau.dev/tulir/gomuks-build-docker/-/pipelines and copy job numbers
    # for `libsignal` jobs.
    if platform.machine() == "x86_64":
        job_id = "79937"
    elif platform.machine() == "aarch64":
        job_id = "79938"
    else:
        raise RuntimeError("Slidgnal is only supported for amd64 and arm64")
    urlretrieve(LIBSIGNAL_FFI_URL.format(job_id), "./libsignal_ffi.a")
    os.environ["LIBRARY_PATH"] = os.getcwd() + ":" + os.getenv("LIBRARY_PATH", "")


if __name__ == "__main__":
    main()
