#!/usr/bin/env python3
"""
微信投研日报 — 自包含版本
================================
解密微信数据库 → 过滤投研内容 → 跨群去重 → 按主题聚类 → 输出日报

用法:
    python3 invest_daily.py                # 分析今天
    python3 invest_daily.py 2026-06-01     # 分析指定日期
    python3 invest_daily.py --setup        # 重新配置

首次运行自动启动配置向导，后续直接出报告。
"""
import json, os, sys, sqlite3, hashlib, re, datetime
import zstandard

sys.stdout.reconfigure(encoding='utf-8')

# 确保能导入同目录下的 crypto 模块
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_DIR)

from crypto.config import load_config, STATE_DIR, CONFIG_FILE, KEYS_FILE, auto_detect_db_dir
from crypto.keys import extract_keys
from crypto.decrypt import full_decrypt, decrypt_wal

USER_CONFIG_FILE = os.path.join(STATE_DIR, "user_config.json")


def load_user_config():
    """加载用户配置，不存在则触发配置向导。"""
    if os.path.exists(USER_CONFIG_FILE):
        with open(USER_CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)

    print("[!] 未找到用户配置，启动初始化向导...\n")
    from setup_wizard import run_wizard
    return run_wizard()


def ensure_keys():
    """检查密钥是否存在，不存在则自动提取。"""
    if os.path.exists(KEYS_FILE):
        print(f"[✓] 密钥已存在: {KEYS_FILE}")
        return

    print("[*] 未检测到密钥，开始自动提取...")
    print("[*] 请确保微信已登录并正在运行")

    os.makedirs(STATE_DIR, exist_ok=True)

    db_dir = auto_detect_db_dir()
    if db_dir is None:
        print("[!] 无法自动检测微信数据目录", file=sys.stderr)
        print("请确认微信已登录", file=sys.stderr)
        sys.exit(1)
    print(f"[+] 检测到微信数据目录: {db_dir}")

    try:
        key_map = extract_keys(db_dir, KEYS_FILE)
    except RuntimeError as e:
        print(f"\n[!] 密钥提取失败: {e}", file=sys.stderr)
        sys.exit(1)

    cfg = {"db_dir": db_dir}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    print(f"[+] 密钥提取完成: {len(key_map)} 个数据库密钥\n")


def is_investment_chat(chat_id, display, exclude_groups, invest_keywords, contact_keywords):
    if chat_id.endswith('@chatroom'):
        for kw in exclude_groups:
            if kw in display:
                return False
        for kw in invest_keywords:
            if kw in display:
                return True
        return False
    if chat_id.startswith('gh_') or chat_id == 'filehelper':
        return False
    for kw in contact_keywords:
        if kw in display:
            return True
    return False


# 账号分享 / 提示词注入 等垃圾内容，整条丢弃（隐私 + 去噪）
_EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.\w+')
_CRED_RE = re.compile(r'账号|密码|验证码|卡密|收码|claude\.ai', re.I)
_INJECT_RE = re.compile(r'DO NOT SHARE|WARNING_BANNER|SHARING THIS INFO|grant access to your account', re.I)


def is_junk_content(text):
    """账号/凭证分享、提示词注入等内容，不应进入投研报告。"""
    if _INJECT_RE.search(text):
        return True
    # 凭证关键词 + 邮箱/验证码/官网登录 = 账号分享
    if _CRED_RE.search(text) and (_EMAIL_RE.search(text) or '验证码' in text or 'claude.ai' in text.lower()):
        return True
    return False


def main():
    if '--setup' in sys.argv:
        from setup_wizard import run_wizard
        run_wizard(force_reset=True)
        return

    user_cfg = load_user_config()
    EXCLUDE_GROUPS = user_cfg.get("exclude_groups", [])
    INVEST_KEYWORDS = user_cfg.get("invest_keywords", [])
    INVEST_CONTACT_KEYWORDS = user_cfg.get("invest_contact_keywords", [])
    THEMES = user_cfg.get("themes", {})

    ensure_keys()

    cfg, keys_path = load_config()
    with open(keys_path) as f:
        keys_db = json.load(f)
    keys = {}
    for k, v in keys_db.items():
        keys[k.replace('\\', '/')] = v

    db_dir = cfg['db_dir']
    tmp = os.path.join(db_dir, '..', '_cache')
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        try:
            os.remove(os.path.join(tmp, f))
        except:
            pass

    dctx = zstandard.ZstdDecompressor()

    target_date = datetime.date.today()
    if len(sys.argv) > 1:
        target_date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
    ts_start = int(datetime.datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0).timestamp())
    ts_end = ts_start + 86400

    def decrypt_db(rel_path, out_name):
        norm = rel_path.replace('\\', '/')
        if norm not in keys:
            return None
        in_path = os.path.join(db_dir, rel_path)
        out_path = os.path.join(tmp, out_name)
        if not os.path.exists(in_path):
            return None
        full_decrypt(in_path, out_path, bytes.fromhex(keys[norm]['enc_key']))
        wal_path = in_path + '-wal'
        if os.path.exists(wal_path):
            decrypt_wal(wal_path, out_path, bytes.fromhex(keys[norm]['enc_key']))
        return out_path

    # 1. 联系人名称映射
    name_map = {}
    contact_dec = decrypt_db('contact/contact.db', 'inv_contact.db')
    if contact_dec:
        conn = sqlite3.connect(contact_dec)
        cur = conn.cursor()
        cur.execute("SELECT username, nick_name, remark FROM contact WHERE nick_name IS NOT NULL OR remark IS NOT NULL")
        for u, nick, remark in cur.fetchall():
            name_map[u] = remark or nick or u
        conn.close()

    # 2. 获取所有聊天 ID
    all_chat_ids = set()
    for di in range(10):
        dn = decrypt_db(f'message/message_{di}.db', f'inv_n2i_{di}.db')
        if dn:
            try:
                conn = sqlite3.connect(dn)
                for r in conn.execute("SELECT user_name FROM Name2Id").fetchall():
                    all_chat_ids.add(r[0])
                conn.close()
            except:
                pass

    # 3. 提取消息
    chat_msgs = {}
    msg_dbs = []
    for key_name in keys:
        m = re.match(r'^message/message_(\d+)\.db$', key_name)
        if m and 'enc_key' in keys[key_name]:
            p = os.path.join(db_dir, key_name)
            if os.path.exists(p):
                msg_dbs.append((int(m.group(1)), p, bytes.fromhex(keys[key_name]['enc_key'])))
    msg_dbs.sort()

    for db_idx, db_path, enc_key in msg_dbs:
        out_path = os.path.join(tmp, f'inv_msg_{db_idx}.db')
        full_decrypt(db_path, out_path, enc_key)
        wal_path = db_path + '-wal'
        if os.path.exists(wal_path):
            decrypt_wal(wal_path, out_path, enc_key)

        conn = sqlite3.connect(out_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'")
        for tbl in cur.fetchall():
            tbl = tbl[0]
            try:
                rows = cur.execute(f"""SELECT create_time, message_content, WCDB_CT_message_content, local_type
                    FROM "{tbl}" WHERE create_time >= ? AND create_time < ? ORDER BY create_time""",
                    (ts_start, ts_end)).fetchall()
            except:
                continue
            if not rows:
                continue
            md5_part = tbl[4:]
            chat_id = None
            for cid in all_chat_ids:
                if hashlib.md5(cid.encode()).hexdigest() == md5_part:
                    chat_id = cid
                    break
            if not chat_id:
                continue
            display = name_map.get(chat_id, chat_id)
            if not is_investment_chat(chat_id, display, EXCLUDE_GROUPS, INVEST_KEYWORDS, INVEST_CONTACT_KEYWORDS):
                continue
            if chat_id not in chat_msgs:
                chat_msgs[chat_id] = []
            for ts, content, ct, lt in rows:
                real_type = lt & 0xFFFFFFFF
                if real_type not in (1, 3, 47, 49):
                    continue
                if not content:
                    continue
                try:
                    text = dctx.decompress(content).decode('utf-8', errors='replace') if ct == 4 else (
                        content if isinstance(content, str) else content.decode('utf-8', errors='replace'))
                except:
                    continue
                if is_junk_content(text):   # 丢弃账号分享/注入等垃圾
                    continue
                dt_str = datetime.datetime.fromtimestamp(ts).strftime('%H:%M')
                if real_type == 1:
                    parts = text.split(':\n', 1)
                    sender = parts[0].strip() if len(parts) == 2 else ''
                    msg_text = parts[1].strip() if len(parts) == 2 else text.strip()
                    chat_msgs[chat_id].append((dt_str, sender, msg_text, 'text'))
                elif real_type == 49:
                    title_m = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', text, re.DOTALL)
                    title = title_m.group(1).strip() if title_m else ''
                    if title:
                        chat_msgs[chat_id].append((dt_str, '', title, 'link'))
        conn.close()

    # 4. 跨群去重
    all_texts = {}
    for chat_id, msgs in chat_msgs.items():
        display = name_map.get(chat_id, chat_id)
        for m in msgs:
            if m[3] == 'text':
                content_hash = hashlib.md5(m[2][:100].encode()).hexdigest()
                if content_hash not in all_texts:
                    all_texts[content_hash] = []
                all_texts[content_hash].append((display, m[0], m[1], m[2]))

    duplicate_hashes = set()
    for h, entries in all_texts.items():
        if len(entries) > 1:
            duplicate_hashes.add(h)

    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

    # 5. 输出报告
    print(f"\n{'='*65}")
    print(f"  投研日报  {target_date}（{weekday_names[target_date.weekday()]}）")
    print(f"{'='*65}")

    # 5a. 跨群热点
    print(f"\n>> 跨群热点（同内容推送 >=3群）")
    dupes_3plus = {h: es for h, es in all_texts.items() if len(es) >= 3}
    if dupes_3plus:
        for h, entries in sorted(dupes_3plus.items(), key=lambda x: len(x[1]), reverse=True):
            groups = [e[0] for e in entries]
            preview = entries[0][3][:120]
            print(f"\n  [{len(groups)}个群推送]")
            print(f"  {preview}")
            print(f"  群: {', '.join(groups[:8])}{'...' if len(groups) > 8 else ''}")
    else:
        print("  （无跨群热点）")

    # 5b. 主题分类
    print(f"\n{'='*65}")
    print(f">> 投研主题分析")
    print(f"{'='*65}")

    theme_content = {t: [] for t in THEMES}
    for chat_id, msgs in chat_msgs.items():
        display = name_map.get(chat_id, chat_id)
        for m in msgs:
            if m[3] != 'text':
                continue
            ch = hashlib.md5(m[2][:100].encode()).hexdigest()
            if ch in dupes_3plus:
                continue
            for theme, kws in THEMES.items():
                for kw in kws:
                    if kw.lower() in m[2].lower():
                        sender_info = f"({m[0]}) " if m[1] else ""
                        theme_content[theme].append(f"  [{m[0]}] {sender_info}{m[2][:200]}")
                        break

    for theme, items in theme_content.items():
        if not items:
            continue
        print(f"\n【{theme}】")
        seen = set()
        unique_items = []
        for item in items:
            h = hashlib.md5(item[:80].encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                unique_items.append(item)
        for item in unique_items[:8]:
            print(item)
        if len(unique_items) > 8:
            print(f"  ... 还有 {len(unique_items) - 8} 条相关")

    # 5c. 事件日历
    print(f"\n{'='*65}")
    print(f">> 关键事件")
    print(f"{'='*65}")
    seen_events = set()
    for chat_id, msgs in sorted(chat_msgs.items(), key=lambda x: len(x[1]), reverse=True):
        display = name_map.get(chat_id, chat_id)
        for m in msgs:
            if m[3] != 'text':
                continue
            txt = m[2]
            if any(kw in txt for kw in ['时间', '会议', '调研', '路演', '电话会', '日程']):
                if len(txt) > 30:
                    h = hashlib.md5(txt[:100].encode()).hexdigest()
                    if h not in seen_events:
                        seen_events.add(h)
                        lines = txt.split('\n')[:3]
                        preview = '\n'.join([l[:120] for l in lines])
                        print(f"\n{preview[:200]}")
                        print(f"  来源: {display}")

    # 5d. 统计
    total_msgs = sum(len(msgs) for msgs in chat_msgs.values())
    dedup_count = len(duplicate_hashes)
    print(f"\n{'='*65}")
    print(f">> 数据统计")
    print(f"{'='*65}")
    print(f"  投研聊天数: {len(chat_msgs)}")
    print(f"  投研消息数: {total_msgs}")
    print(f"  跨群去重: {dedup_count} 条")
    print()


if __name__ == '__main__':
    main()
