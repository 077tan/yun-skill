#!/usr/bin/env python3
"""
微信投研日报 — 首次配置向导
================================
自动扫描本地微信群列表，引导用户设置过滤规则，保存到 ~/.wechat-digest/user_config.json

用法:
    python3 setup_wizard.py          # 首次配置
    python3 setup_wizard.py --reset  # 重置配置
"""
import json
import os
import sys
import sqlite3
import hashlib
import re

sys.stdout.reconfigure(encoding='utf-8')

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_DIR)

from crypto.config import (
    load_config, STATE_DIR, CONFIG_FILE, KEYS_FILE,
    auto_detect_db_dir
)
from crypto.keys import extract_keys
from crypto.decrypt import full_decrypt, decrypt_wal

USER_CONFIG_FILE = os.path.join(STATE_DIR, "user_config.json")

DEFAULT_CONFIG = {
    "exclude_groups": [],
    "invest_keywords": [],
    "invest_contact_keywords": [],
    "themes": {}
}

PRESET_THEMES = {
    "AI/科技": ["AI", "人工智能", "大模型", "算力", "英伟达", "半导体"],
    "宏观/策略": ["PMI", "宏观", "利率", "社融", "CPI", "PPI"],
    "医药/创新药": ["创新药", "医药", "生物", "临床", "FDA"],
    "新能源/电池": ["新能源", "电池", "锂电", "光伏", "风电", "比亚迪"],
    "消费/零售": ["消费", "零售", "白酒", "食品", "茅台"],
    "机器人": ["机器人", "人形", "特斯拉", "Figure"],
    "先进制造": ["封装", "台积电", "CoWoS", "MLCC", "碳化硅"],
}


def _input(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def ensure_keys():
    if os.path.exists(KEYS_FILE):
        print(f"[✓] 密钥已存在")
        return True

    print("[*] 未检测到密钥，开始自动提取...")
    print("[*] 请确保微信已登录并正在运行")

    os.makedirs(STATE_DIR, exist_ok=True)

    db_dir = auto_detect_db_dir()
    if db_dir is None:
        print("[!] 无法自动检测微信数据目录，请确认微信已登录", file=sys.stderr)
        return False

    print(f"[+] 检测到微信数据目录: {db_dir}")
    try:
        key_map = extract_keys(db_dir, KEYS_FILE)
    except RuntimeError as e:
        print(f"[!] 密钥提取失败: {e}", file=sys.stderr)
        return False

    cfg = {"db_dir": db_dir}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    print(f"[+] 密钥提取完成: {len(key_map)} 个数据库密钥\n")
    return True


def scan_chatrooms():
    """解密 contact.db，返回所有群聊列表 [(chat_id, display_name)]"""
    try:
        cfg, keys_path = load_config()
    except FileNotFoundError:
        return []

    with open(keys_path) as f:
        keys_db = json.load(f)
    keys = {k.replace('\\', '/'): v for k, v in keys_db.items()}

    db_dir = cfg['db_dir']
    tmp = os.path.join(db_dir, '..', '_cache')
    os.makedirs(tmp, exist_ok=True)

    contact_key = keys.get('contact/contact.db')
    if not contact_key:
        return []

    contact_path = os.path.join(db_dir, 'contact', 'contact.db')
    if not os.path.exists(contact_path):
        return []

    out_path = os.path.join(tmp, '_setup_contact.db')
    full_decrypt(contact_path, out_path, bytes.fromhex(contact_key['enc_key']))

    chatrooms = []
    try:
        conn = sqlite3.connect(out_path)
        rows = conn.execute(
            "SELECT username, nick_name, remark FROM contact WHERE username LIKE '%@chatroom'"
        ).fetchall()
        for uid, nick, remark in rows:
            name = remark or nick or uid
            chatrooms.append((uid, name))
        conn.close()
    except Exception as e:
        print(f"[!] 读取联系人失败: {e}")

    try:
        os.remove(out_path)
    except Exception:
        pass

    chatrooms.sort(key=lambda x: x[1])
    return chatrooms


def show_chatrooms_page(chatrooms, page, page_size=30):
    start = page * page_size
    end = min(start + page_size, len(chatrooms))
    print(f"\n  群列表（{start+1}-{end} / 共{len(chatrooms)}个）:")
    for i, (uid, name) in enumerate(chatrooms[start:end], start + 1):
        print(f"    {i:3d}. {name}")
    return start, end


def interactive_select_groups(chatrooms):
    """交互式让用户从群列表中标记投研群"""
    if not chatrooms:
        print("[!] 未找到任何群聊，请确认微信有群聊记录")
        return [], []

    print("\n" + "="*60)
    print("  第一步：告诉我你的投研群")
    print("="*60)
    print("""
两种方式选择（可混用）：
  A) 输入关键词 — 群名包含关键词的自动归为投研群
  B) 扫描群列表 — 逐页浏览，手动挑选

建议先用 A，再用 B 补充。
""")

    invest_keywords = []
    exclude_keywords = []
    selected_ids = set()

    # A: 关键词方式
    print("【A】输入投研群关键词（多个用逗号分隔，直接回车跳过）")
    print("  示例: 投研,证券,基金,策略,晨会")
    raw = _input("  关键词> ")
    if raw:
        invest_keywords = [k.strip() for k in raw.split(',') if k.strip()]

    print("\n【可选】输入要排除的关键词（购物/实习群等，逗号分隔，回车跳过）")
    raw = _input("  排除关键词> ")
    if raw:
        exclude_keywords = [k.strip() for k in raw.split(',') if k.strip()]

    # 预览关键词匹配结果
    if invest_keywords:
        matched = []
        for uid, name in chatrooms:
            excluded = any(kw in name for kw in exclude_keywords)
            included = any(kw in name for kw in invest_keywords)
            if included and not excluded:
                matched.append((uid, name))
        print(f"\n  关键词匹配到 {len(matched)} 个投研群：")
        for uid, name in matched[:20]:
            print(f"    · {name}")
        if len(matched) > 20:
            print(f"    ... 还有 {len(matched)-20} 个")
        selected_ids = {uid for uid, _ in matched}

    # B: 手动浏览补充
    print("\n【B】是否浏览全部群列表手动补充/调整？(y/N)")
    if _input("  > ").lower() == 'y':
        page = 0
        page_size = 30
        while True:
            start, end = show_chatrooms_page(chatrooms, page, page_size)
            print(f"\n  命令: [数字] 切换选中 | n 下一页 | p 上一页 | q 完成")
            cmd = _input("  > ")
            if cmd == 'q':
                break
            elif cmd == 'n':
                if end < len(chatrooms):
                    page += 1
            elif cmd == 'p':
                if page > 0:
                    page -= 1
            elif cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(chatrooms):
                    uid, name = chatrooms[idx]
                    if uid in selected_ids:
                        selected_ids.discard(uid)
                        print(f"  [-] 取消: {name}")
                    else:
                        selected_ids.add(uid)
                        print(f"  [+] 选中: {name}")

    return invest_keywords, exclude_keywords


def setup_contact_keywords():
    print("\n" + "="*60)
    print("  第二步：机构联系人关键词（单聊）")
    print("="*60)
    print("  单聊对象名称含这些词时，视为投研信息来源")
    print("  示例: 基金,证券,分析师,研究员,资管")
    print("  直接回车使用默认值")
    raw = _input("  关键词> ")
    if raw:
        return [k.strip() for k in raw.split(',') if k.strip()]
    return ["基金", "证券", "投资", "研究员", "分析师", "资管", "资产"]


def setup_themes():
    print("\n" + "="*60)
    print("  第三步：主题分类（日报按主题归类消息）")
    print("="*60)
    print("  预设主题（输入编号选择，多选用逗号分隔，全选输入 all）：\n")
    preset_list = list(PRESET_THEMES.items())
    for i, (name, kws) in enumerate(preset_list, 1):
        print(f"    {i}. {name}  [{', '.join(kws[:4])}...]")

    print("\n  直接回车跳过（不按主题分类）")
    raw = _input("  选择> ").strip()

    themes = {}
    if raw.lower() == 'all':
        themes = dict(PRESET_THEMES)
    elif raw:
        for part in raw.split(','):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(preset_list):
                    name, kws = preset_list[idx]
                    themes[name] = kws

    # 自定义主题
    print("\n  是否添加自定义主题？(y/N)")
    if _input("  > ").lower() == 'y':
        while True:
            print("  主题名称（回车结束）:")
            tname = _input("  > ")
            if not tname:
                break
            print(f"  {tname} 的关键词（逗号分隔）:")
            tkws = _input("  > ")
            if tkws:
                themes[tname] = [k.strip() for k in tkws.split(',') if k.strip()]

    return themes


def save_config(invest_keywords, exclude_keywords, contact_keywords, themes):
    os.makedirs(STATE_DIR, exist_ok=True)
    config = {
        "invest_keywords": invest_keywords,
        "exclude_groups": exclude_keywords,
        "invest_contact_keywords": contact_keywords,
        "themes": themes
    }
    with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n[✓] 配置已保存到 {USER_CONFIG_FILE}")
    return config


def load_user_config():
    if os.path.exists(USER_CONFIG_FILE):
        with open(USER_CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None


def run_wizard(force_reset=False):
    print("\n" + "="*60)
    print("  微信投研日报 — 初始化向导")
    print("="*60)

    if not force_reset and os.path.exists(USER_CONFIG_FILE):
        print(f"\n[!] 检测到已有配置: {USER_CONFIG_FILE}")
        print("  输入 y 重新配置，其他键跳过")
        if _input("  > ").lower() != 'y':
            print("  使用现有配置，跳过向导")
            return load_user_config()

    # 步骤0: 提取密钥
    if not ensure_keys():
        print("\n[!] 密钥提取失败，无法继续配置")
        sys.exit(1)

    # 步骤1: 扫描群列表
    print("\n[*] 正在读取群列表...")
    chatrooms = scan_chatrooms()
    print(f"[+] 共找到 {len(chatrooms)} 个群聊")

    invest_keywords, exclude_keywords = interactive_select_groups(chatrooms)
    contact_keywords = setup_contact_keywords()
    themes = setup_themes()

    config = save_config(invest_keywords, exclude_keywords, contact_keywords, themes)

    print("\n" + "="*60)
    print("  配置完成！现在可以运行日报了：")
    print("  在 Claude Code 中说「生成日报」")
    print("  或: python3 invest_daily.py")
    print("="*60 + "\n")

    return config


if __name__ == '__main__':
    force_reset = '--reset' in sys.argv
    run_wizard(force_reset=force_reset)
