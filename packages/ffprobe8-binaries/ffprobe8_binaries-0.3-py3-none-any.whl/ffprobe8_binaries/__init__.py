import pathlib
import sys
import platform
import os

def add_to_path() -> None:
    """
    Add ffprobe binaries to path
    """
    executable_path = str(_get_binaries())
    if executable_path not in os.environ["PATH"]:
        os.environ["PATH"] = f"{executable_path}{os.pathsep}{os.environ['PATH']}"

def _get_binaries() -> pathlib.Path:
    package_folder = pathlib.Path(__file__).parent
    binaries_folder = package_folder.joinpath("binaries")
    os_name = sys.platform # 操作系统（如 'win32', 'linux', 'darwin'）
    arch = platform.machine().lower()  # 架构
    arch_dir = arch
    if arch in ("x86_64", "amd64"):
        arch_dir = "x86_64"

    executable_path = binaries_folder.joinpath(os_name).joinpath(arch_dir)
    if not executable_path.exists():
        raise RuntimeError(f"Binaries for platform {os_name} arch {arch} not supported")
    return executable_path
