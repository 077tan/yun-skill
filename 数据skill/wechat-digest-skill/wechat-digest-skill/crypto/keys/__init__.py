"""密钥提取模块 — 根据平台调用对应的 scanner"""

import platform


def extract_keys(db_dir, output_path, pid=None):
    system = platform.system().lower()
    if system == "darwin":
        from .scanner_macos import extract_keys as _extract
        return _extract(db_dir, output_path, pid=pid)
    elif system == "windows":
        from .scanner_windows import extract_keys as _extract
        return _extract(db_dir, output_path, pid=pid)
    elif system == "linux":
        from .scanner_linux import extract_keys as _extract
        return _extract(db_dir, output_path, pid=pid)
    else:
        raise RuntimeError(f"不支持的平台: {platform.system()}")
