"""配置加载 — 从 ~/.wechat-digest/ 读取配置"""

import glob as glob_mod
import json
import os
import platform
import sys

_SYSTEM = platform.system().lower()

STATE_DIR = os.path.expanduser("~/.wechat-digest")
CONFIG_FILE = os.path.join(STATE_DIR, "config.json")
KEYS_FILE = os.path.join(STATE_DIR, "all_keys.json")


def _choose_candidate(candidates):
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        if not sys.stdin.isatty():
            return candidates[0]
        print("[!] 检测到多个微信数据目录:")
        for i, c in enumerate(candidates, 1):
            print(f"    {i}. {c}")
        print("    0. 跳过")
        try:
            while True:
                choice = input(f"请选择 [0-{len(candidates)}]: ").strip()
                if choice == "0":
                    return None
                if choice.isdigit() and 1 <= int(choice) <= len(candidates):
                    return candidates[int(choice) - 1]
                print("    无效输入")
        except (EOFError, KeyboardInterrupt):
            print()
            return None
    return None


def _auto_detect_db_dir_windows():
    appdata = os.environ.get("APPDATA", "")
    config_dir = os.path.join(appdata, "Tencent", "xwechat", "config")
    if not os.path.isdir(config_dir):
        return None
    data_roots = []
    for ini_file in glob_mod.glob(os.path.join(config_dir, "*.ini")):
        try:
            content = None
            for enc in ("utf-8", "gbk"):
                try:
                    with open(ini_file, "r", encoding=enc) as f:
                        content = f.read(1024).strip()
                    break
                except UnicodeDecodeError:
                    continue
            if not content or any(c in content for c in "\n\r\x00"):
                continue
            if os.path.isdir(content):
                data_roots.append(content)
        except OSError:
            continue
    seen = set()
    candidates = []
    for root in data_roots:
        pattern = os.path.join(root, "xwechat_files", "*", "db_storage")
        for match in glob_mod.glob(pattern):
            normalized = os.path.normcase(os.path.normpath(match))
            if os.path.isdir(match) and normalized not in seen:
                seen.add(normalized)
                candidates.append(match)
    return _choose_candidate(candidates)


def _auto_detect_db_dir_linux():
    seen = set()
    candidates = []
    search_roots = [os.path.expanduser("~/Documents/xwechat_files")]
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        import pwd
        try:
            sudo_home = pwd.getpwnam(sudo_user).pw_dir
        except KeyError:
            sudo_home = None
        if sudo_home:
            fallback = os.path.join(sudo_home, "Documents", "xwechat_files")
            if fallback not in search_roots:
                search_roots.append(fallback)
    for root in search_roots:
        if not os.path.isdir(root):
            continue
        pattern = os.path.join(root, "*", "db_storage")
        for match in glob_mod.glob(pattern):
            normalized = os.path.normcase(os.path.normpath(match))
            if os.path.isdir(match) and normalized not in seen:
                seen.add(normalized)
                candidates.append(match)
    old_path = os.path.expanduser("~/.local/share/weixin/data/db_storage")
    if os.path.isdir(old_path):
        normalized = os.path.normcase(os.path.normpath(old_path))
        if normalized not in seen:
            candidates.append(old_path)

    def _mtime(path):
        msg_dir = os.path.join(path, "message")
        target = msg_dir if os.path.isdir(msg_dir) else path
        try:
            return os.path.getmtime(target)
        except OSError:
            return 0
    candidates.sort(key=_mtime, reverse=True)
    return _choose_candidate(candidates)


def _auto_detect_db_dir_macos():
    base = os.path.expanduser("~/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files")
    if not os.path.isdir(base):
        return None
    seen = set()
    candidates = []
    pattern = os.path.join(base, "*", "db_storage")
    for match in glob_mod.glob(pattern):
        normalized = os.path.normcase(os.path.normpath(match))
        if os.path.isdir(match) and normalized not in seen:
            seen.add(normalized)
            candidates.append(match)
    return _choose_candidate(candidates)


def auto_detect_db_dir():
    if _SYSTEM == "windows":
        return _auto_detect_db_dir_windows()
    if _SYSTEM == "linux":
        return _auto_detect_db_dir_linux()
    if _SYSTEM == "darwin":
        return _auto_detect_db_dir_macos()
    return None


def load_config():
    if os.path.exists(CONFIG_FILE) and os.path.exists(KEYS_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg, KEYS_FILE
    wechat_cli_config = os.path.expanduser("~/.wechat-cli/config.json")
    wechat_cli_keys = os.path.expanduser("~/.wechat-cli/all_keys.json")
    if os.path.exists(wechat_cli_config) and os.path.exists(wechat_cli_keys):
        with open(wechat_cli_config, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg, wechat_cli_keys
    raise FileNotFoundError(
        "未找到配置文件。请先运行 init-keys.py 提取密钥"
    )
