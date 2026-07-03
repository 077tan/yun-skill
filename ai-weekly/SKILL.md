---
name: ai-weekly
description: AI应用周报自动撰写技能。搜索本周AI行业重要动态（覆盖芯片/存储/云/大模型/多模态/Agent/智驾/机器人等10大分类），按实际周报格式生成含行情更新、行业动态、下周事件预告的完整Word文档。当用户说"生成AI周报"、"AI应用周报"、"本周AI周报"、"写AI周报"、"更新AI周报"、"/ai-weekly"时触发。
metadata:
    version: 1.0
    migrated_from: commands/ai-weekly.md
---


# AI应用周报自动撰写

你是一名专业的AI行业分析师。按以下步骤搜索本周各大AI公司动态，撰写完整周报并保存为Word文档。

**核心原则（按优先级排序，越往上越是 deal-breaker）：**

1. **信源可靠性 ≥ 时效性 ≥ 完整性**——宁可少一条新闻，绝不放一条假新闻。**未经2+独立信源交叉验证的内容，一律不写入正文。**
2. **每条新闻必须是本周（周一至周日）7天内发生的**，过时新闻一律不收录。
3. **AI/SEO 农场内容必须识别并剔除**（详见"第三·四步：信源核实"）。
4. **【强制格式 deal-breaker】每条新闻正文的第一句必须以"X月X日，"开头**——这是格式硬约束，不是建议。具体规则：
   - 第一个字符必须是阿拉伯数字月份（如 `5月28日，`、`12月3日，`）
   - 单日事件用 `X月X日，`；跨日事件用 `X月X日至X月X日，` 或 `X月X日-X日，`
   - 财报/区间数据可用 `X月X日披露的Q1业绩显示，` 或 `X月X日盘后，` 等变体，但**必须包含完整月日**
   - **禁止写法**：`本周，` / `近日，` / `日前，` / `周中，` / `5月下旬，`（无具体日期）/ 直接 `公司发布……`（无日期前缀）
   - 标题（headline）可以不写日期，但正文（body_text）第一句必须有完整 X月X日

> ⚠️ **关键失败模式（2026-05-17 沉淀经验）**：在搜索 AI 行业 2026 内容时，WebSearch 召回结果中混杂大量 **AI 自动生成 / SEO 关键词页面**，特征是"未来日期 + 关键词堆砌 + 多家公司同日发布同类产品 + 无具体引述"。第一版周报曾因直接采信这类内容，出现"五月十三日七家大模型同日发布旗舰新版本"这类系统性错误。**这是顶层设计问题，不是参数调优能解决的——必须把信源核实作为强制门槛**。

---

## 第一步：确定本周日期

用 Bash 运行以下代码确定时间范围：

```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import date, timedelta
today = date.today()
monday = today - timedelta(days=today.weekday())
sunday = monday + timedelta(days=6)
print(f"本周：{monday.strftime('%Y/%m/%d')} - {sunday.strftime('%Y/%m/%d')}")
print(f"文件名日期：{sunday.strftime('%y%m%d')}")
print(f"搜索月份：{monday.strftime('%Y年%m月')}")
print(f"周一：{monday.strftime('%m月%d日')}  周日：{sunday.strftime('%m月%d日')}")
```

---

## 第二步：用数据接口自动拉取本周行情

**不用手动搜索**，直接用 Bash 运行以下脚本，自动从 yfinance（美股/港股）和 AKShare（A股ETF）拉取本周行情数据，并输出三段行情文字供直接使用。

```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import yfinance as yf
from datetime import date, timedelta

today = date.today()
monday = today - timedelta(days=today.weekday())
last_friday = monday - timedelta(days=3)   # 上周五 = 周初基准
fetch_end = (today + timedelta(days=1)).strftime('%Y-%m-%d')
fetch_start = last_friday.strftime('%Y-%m-%d')

m_start = f"{monday.month}/{monday.day}"
m_end   = f"{today.month}/{today.day}"
week_display = f"{m_start}-{m_end}"

print(f"【数据区间】上周五={last_friday}  本周一={monday}  今天={today}")
print("=" * 60)

def pull(label, sym):
    """返回 (base, last, chg%) 或 None"""
    try:
        df = yf.Ticker(sym).history(start=fetch_start, end=fetch_end)
        df = df.dropna(subset=['Close'])
        if len(df) >= 2:
            base = float(df['Close'].iloc[0])
            last = float(df['Close'].iloc[-1])
            return base, last, (last - base) / base * 100
        elif len(df) == 1:
            v = float(df['Close'].iloc[0])
            return v, v, 0.0
    except Exception as e:
        print(f"  {label} 异常: {e}")
    return None

# ── 美股 ──────────────────────────────────────────────────
print("▶ 美股")
us = {}
for label, sym in [('纳指', '^IXIC'), ('标普500', '^GSPC'), ('金龙指数', '^HXC')]:
    r = pull(label, sym)
    if r:
        us[label] = r
        print(f"  {label:12s} 上周五={r[0]:.2f} → 最新={r[1]:.2f}  周涨跌={r[2]:+.2f}%")
    else:
        print(f"  {label}: 无数据")

# ── 港股 ──────────────────────────────────────────────────
print("▶ 港股")
hk = {}
for label, sym in [('恒生指数', '^HSI'), ('恒生科技ETF', '3032.HK')]:
    r = pull(label, sym)
    if r:
        hk[label] = r
        print(f"  {label:12s} 上周五={r[0]:.2f} → 最新={r[1]:.2f}  周涨跌={r[2]:+.2f}%")
    else:
        print(f"  {label}: 无数据")

# ── A股 ETF（yfinance，后缀 .SS/.SZ）────────────────────
# 515980.SS 华夏中证AI ETF | 512480.SS 国联安半导体ETF | 588000.SS 科创50ETF
print("▶ A股 ETF")
a = {}
for label, sym in [
    ('AI人工智能ETF(515980)', '515980.SS'),
    ('半导体ETF(512480)',     '512480.SS'),
    ('科创50ETF(588000)',     '588000.SS'),
    ('算力ETF(516960)',       '516960.SS'),
]:
    r = pull(label, sym)
    if r:
        a[label] = r
        print(f"  {label:22s} 上周五={r[0]:.3f} → 最新={r[1]:.3f}  本周={r[2]:+.2f}%")
    else:
        print(f"  {label}: 无数据")

print()
print("=" * 60)

# ── 自动生成行情三段 ──────────────────────────────────────
def fmt(chg): return f"{'涨' if chg > 0 else '跌'}{abs(chg):.1f}%"
def pt(label, d, precision=0):
    if label not in d: return f"{label}（数据缺失）"
    b, l, c = d[label]
    return f"{label}{fmt(c)}至{l:.{precision}f}{'点' if precision==0 else ''}"

print("【行情段落（复制到第五步 _para() 中，可适当润色）】")
print()
nas = pt('纳指', us); sp = pt('标普500', us)
hxc = f"纳斯达克金龙指数{fmt(us['金龙指数'][2])}" if '金龙指数' in us else ""
print(f"§1  本周（{week_display}），美股科技股整体震荡，{nas}；{sp}；{hxc}。")
print()

if '恒生指数' in hk:
    hsi_c = hk['恒生指数'][2]; hsi_l = hk['恒生指数'][1]
    hst_c = hk.get('恒生科技ETF', (0,0,0))[2]
    print(f"§2  港股方面，恒生指数本周{fmt(hsi_c)}，报{hsi_l:.0f}点；恒生科技ETF本周{fmt(hst_c)}。")
else:
    print("§2  港股方面，（数据获取失败，请手动补充恒生指数涨跌）。")
print()

if a:
    parts = [f"{k.split('(')[0]}{fmt(v[2])}" for k, v in a.items()]
    print(f"§3  A股方面，AI芯片/算力/半导体板块本周分化：{'; '.join(parts)}。")
else:
    print("§3  A股方面，（数据获取失败，请手动补充板块涨跌）。")
```

> **注意**：自动段落是数据骨架，需要结合本周重要事件（如大公司财报、政策出台）手动润色后填入第五步的 `_para()` 调用中。

---

## 第三步：用 Alpha派 批量搜集本周行业新闻

**主力工具：Alpha派（alphapai）`qa --web-search --mode Think`**。Think模式会自动对一个问题发起多次联网搜索并汇总，输出带来源引用的完整分析，比逐公司WebSearch更全面、更准确、效率更高。

**Alpha派脚本路径（每次调用前确认）：**
```
ALPHAPAI=C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py
```

**调用模板：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "【在此填写分类问题】" \
  --web-search --mode Think \
  --start YYYY-MM-DD --end YYYY-MM-DD
```
其中 `--start` 填本周周一日期，`--end` 填今天日期（均来自第一步输出）。

**工作流程：**
1. 用 Alpha派 按分类发起宽搜（每个分类1个问题，覆盖该分类所有主要公司）
2. Alpha派返回结果后，**逐条核查日期**，只保留本周7天内的新闻
3. 对于 Alpha派 未能覆盖的空白点，用 WebSearch 补充搜索
4. 完成所有分类后，**额外做一次横向事件搜索**（见下方"横向兜底搜索"），捕捉跨公司的标志性事件

**每条新闻必须满足：①本周7天内发生 ②有明确日期 ③属于重要动态（模型/产品发布、重大融资、财报业绩、战略合作、技术突破、重要政策）**

---

### 横向兜底搜索（每次必做，在所有分类搜索完成后执行）

用 Alpha派 或 WebSearch 各搜一次，捕捉按公司维度逐条搜索时容易遗漏的**比较性、标志性、跨公司事件**：

```bash
# 兜底搜索1：本周AI公司估值/融资格局变化
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI科技公司估值、融资、IPO方面最重要的新闻，包括各大AI公司估值排名变化、新一轮融资、上市进程等" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD

# 兜底搜索2：本周最重要AI行业综合新闻 TOP10
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）全球AI行业最重要的10条新闻，涵盖芯片、云、大模型、机器人、自动驾驶各领域，请按重要性排列并注明每条新闻的具体日期" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

---

### 分类一：AI芯片

**Alpha派宽搜问题（一次覆盖所有芯片公司）：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI芯片和半导体领域最重要的新闻动态，覆盖NVIDIA、AMD、英特尔、台积电、高通、博通、Arm、Marvell、Cerebras、Lumentum、寒武纪、华为昇腾、壁仞、摩尔线程、中芯国际、地平线，以及Astera Labs（ALAB，PCIe/CXL）、Credo（CRDO，AEC线缆）、MACOM（MTSI）、AMD EPYC/Intel Xeon数据中心CPU、Ampere Computing等公司。重点关注：财报业绩、新品发布、战略合作、重大融资、产能变化。每条新闻请标注具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

**WebSearch补充（Alpha派遗漏时使用）：** `NVIDIA/AMD/台积电 AI芯片 YYYY年MM月`

关注公司：
- **AI GPU/加速卡**：NVIDIA · AMD（MI系列）· Cerebras · Groq · Tenstorrent
- **数据中心CPU（美股热度高）**：AMD EPYC · Intel Xeon · Ampere Computing · Arm（ARM）· 高通 Snapdragon Data Center
- **AI网络/互连芯片（美股热度高）**：博通（AVGO，定制ASIC+网络）· Marvell（MRVL）· Astera Labs（ALAB，PCIe/CXL Retimer）· Credo（CRDO，AEC线缆）· MACOM（MTSI）
- **代工/设备**：台积电 · 中芯国际 · ASML · 应用材料
- **国产算力**：寒武纪 · 华为昇腾 · 壁仞科技 · 摩尔线程 · 海光信息 · 沐曦 · 地平线

### 分类二：AI存储

**Alpha派宽搜问题：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI存储领域最重要的新闻，包括HBM（高带宽内存）供需、SK海力士/三星/美光/Sandisk的HBM4/HBM4E进展、DRAM/NAND/eSSD价格走势、长协（LTA）签订、长江存储/兆易创新动态、Western Digital/希捷HDD供需。请标注每条新闻的具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：
- **HBM/DRAM（美股+韩股热度极高）**：SK海力士（HBM4/HBM4E）· 三星（HBM）· **美光 MU**（万亿市值新贵）
- **NAND/eSSD/企业级存储（美股热度高）**：**Sandisk WDC**（NAND独立分拆后纯标的）· **Pure Storage PSTG**（企业SSD/AI数据湖）· **NetApp NTAP**
- **HDD（受AI数据存储拉动）**：**希捷 STX** · **Western Digital WDC**（HDD业务）
- **存储控制器/接口（美股热度高）**：**Astera Labs ALAB**（CXL内存扩展）· Marvell MRVL（DCI存储接口）
- **国内**：长江存储 · 长鑫存储 · 兆易创新 · 江波龙

### 分类二·五：AI光通信 / CPO / 光模块（美股+A股双线热度极高，独立列出）

**Alpha派宽搜问题：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI光通信、光模块、CPO（共封装光学）、硅光、相干光通信领域最重要的新闻，覆盖Coherent（COHR）、Lumentum（LITE）、Fabrinet（FN）、Ciena（CIEN）、Marvell光业务、Astera Labs光互连，以及国内中际旭创（300308）、新易盛（300502）、天孚通信（300394）、光迅科技、华工科技、太辰光、剑桥科技、源杰科技、长光华芯等。重点关注：1.6T/3.2T光模块订单、CPO量产进展、英伟达Rubin/Quantum-X光互连合作、博通/Astera CPO芯片、HBM周边光互连扩展、北美云厂商光模块采购展望。每条新闻请标注具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：
- **美股光通信核心（热度极高）**：**Coherent COHR**（光模块+光器件龙头）· **Lumentum LITE**（数据中心光+激光器）· **Fabrinet FN**（光模块代工+英伟达供应链）· **Ciena CIEN**（DCI相干光通信）· **MACOM MTSI**（射频+光器件）
- **CPO/硅光相关美股**：博通 AVGO（CPO芯片+TH5/Jericho）· Marvell MRVL（800G/1.6T PAM4 DSP）· Astera Labs ALAB（光互连IP）· NVIDIA（Quantum-X / Spectrum-X CPO）
- **A股光模块龙头（热度极高）**：**中际旭创 300308** · **新易盛 300502** · **天孚通信 300394** · 光迅科技 002281 · 华工科技 000988 · 太辰光 300570 · 剑桥科技 603083
- **光芯片/激光器**：源杰科技 688498 · 长光华芯 688048 · 仕佳光子 688313 · 联特科技 301205

### 分类三：AI云

**Alpha派宽搜问题：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI云计算领域最重要的新闻，覆盖AWS、Google Cloud、微软Azure、阿里云、腾讯云、华为云、百度智能云、火山引擎、CoreWeave等。重点关注：季度财报/营收数据、新服务发布、大客户合同、算力扩建计划。请标注每条新闻的具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：AWS · Google Cloud · 微软Azure · 阿里云 · 腾讯云 · 华为云 · 百度智能云 · 火山引擎 · CoreWeave

### 分类四：AI大模型

**Alpha派宽搜问题（分两次：海外+国内）：**
```bash
# 海外大模型
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）海外AI大模型领域最重要的新闻，覆盖OpenAI（GPT系列）、Anthropic（Claude）、Google（Gemini）、Meta（Llama）、xAI（Grok）、DeepSeek。重点关注：新模型发布/升级、定价调整、融资估值、战略合作、监管动态。每条请注明具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD

# 国内大模型
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）国内AI大模型领域最重要的新闻，覆盖月之暗面Kimi、阿里通义千问、百度文心、字节豆包、智谱AI、MiniMax、阶跃星辰、讯飞星火、商汤日日新。重点关注：新模型发布、商业落地、融资、合作。每条请注明具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：OpenAI · Anthropic · Google Gemini · Meta Llama · xAI Grok · DeepSeek · Kimi · 通义千问 · 文心 · 豆包 · 智谱AI · MiniMax · 阶跃星辰 · 讯飞星火 · 商汤日日新

### 分类五：AI多模态

**Alpha派宽搜问题：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI多模态和视频生成领域最重要的新闻，覆盖OpenAI视频/图像、Google Veo、Midjourney、Runway、快手可灵、字节即梦、HeyGen、腾讯混元、美图AI等。重点关注：新功能发布、商业合作、用户增长数据。每条请注明具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：OpenAI视频 · Google Veo · Midjourney · Runway · 快手可灵 · 字节即梦 · HeyGen · 腾讯混元 · 美图

### 分类六：AI Agent

**Alpha派宽搜问题：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI Agent和AI编程工具领域最重要的新闻，覆盖OpenAI Operator、Google Gemini Agent、Anthropic Computer Use、字节Coze、阿里百炼、腾讯元宝/WorkBuddy、Cursor、Perplexity、MiniMax等。重点关注：产品发布、用户增长数据、商业化进展。每条请注明具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：OpenAI Operator · Google Gemini Agent · Anthropic · Coze · 阿里百炼 · 腾讯元宝/WorkBuddy · Cursor · Perplexity · MiniMax Hermes

### 分类七：AI智驾

**Alpha派宽搜问题：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI自动驾驶和智能驾驶领域最重要的新闻，覆盖特斯拉FSD/Robotaxi、Waymo、百度萝卜快跑、小鹏智驾、华为ADS、理想智驾、文远知行、小马智行、比亚迪智驾、蔚来等。重点关注：商业化数据（里程/订单量）、新功能发布、监管政策、重大合作。请标注每条新闻的具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：特斯拉FSD · Waymo · 百度萝卜快跑 · 小鹏智驾 · 华为ADS · 理想智驾 · 文远知行 · 小马智行 · 地平线 · 比亚迪智驾 · 蔚来

### 分类八：AI端侧 / 机器人

**Alpha派宽搜问题：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI端侧和人形机器人领域最重要的新闻，覆盖特斯拉Optimus、宇树科技Unitree、智元机器人、优必选、Figure AI、Boston Dynamics、小米机器人、Apple Intelligence端侧AI、AGIBOT等。重点关注：产品发布/演示、量产进展、融资、重大合作、出货量数据。请标注每条新闻的具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：特斯拉Optimus · 宇树科技 · 智元机器人 · 优必选 · Figure AI · Boston Dynamics · 小米机器人 · Apple Intelligence · AGIBOT

### 分类九：AI教育（仅在有重要动态时写入）

**Alpha派宽搜问题：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI教育领域最重要的新闻，覆盖Duolingo、科大讯飞AI教育、作业帮、猿辅导等。仅报告有实质性进展（产品发布、重大融资、政策变化）的动态，无重要事件请明确说明。请标注每条新闻的具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：Duolingo · 科大讯飞AI教育 · 作业帮 · 猿辅导

### 分类十：AI硬件（仅在有重要动态时写入）

**Alpha派宽搜问题：**
```bash
python "C:\Users\于怡然\.claude\skills\alphapai-research\scripts\alphapai_client.py" qa \
  --question "本周（START至END）AI硬件领域最重要的新闻，覆盖Meta Ray-Ban AI眼镜、Apple Vision Pro、XREAL、华为AI手机、小米AI手机、AI PC（联想/华硕等）。仅报告有实质性进展（新品发布、销售数据、重大合作）的动态，无重要事件请明确说明。请标注每条新闻的具体日期。" \
  --web-search --mode Think --start YYYY-MM-DD --end YYYY-MM-DD
```

关注公司：Meta Ray-Ban · Apple Vision Pro · XREAL · 华为AI手机 · 小米AI手机 · AI PC（联想/华硕）

---

## 第三·四步：信源核实与 SEO 农场内容剔除（强制门槛，每条新闻必做）

**这一步是从"搜索结果"到"周报正文"之间的唯一闸门。任何未通过此核查的内容禁止写入。**

### A. SEO 农场 / AI 农场内容特征（出现 2+ 项即判定为不可信）

| 特征 | 说明 |
|---|---|
| **域名低质量** | aitoolsrecap、coaio、imfounder、tradingkey、个人 csdn.net、个人 .gitcode、个人博客（cnblogs.com 子站除外）、navigator/导航站、聚合站 |
| **标题含"全景/横评/汇总/盘点/趋势/Top10/速递"** | 这是二手综述/榜单，不是新闻 |
| **多家公司"同一天发布同类产品"** | 99% 是 SEO 关键词页面或榜单类文章更新日期，**不是真实事件**。常见诱饵："5月13日 GPT-5.1 / Gemini 3 / Claude X / Grok X / Kimi X / MiniMax X / Veo X 同日发布"——必须**逐家公司去官方 Newsroom 单独核** |
| **没有具体数字、官方引述、人物姓名** | 模型瞎编的可能性极高 |
| **同一条新闻只能在一个域名找到** | 单点失败，必须找第二源 |
| **文章末尾推荐"AI 课程/工具/会员/订阅"** | 软文 + SEO 套壳 |
| **WebFetch 拉取后内容是"无具体数字、模板化、未来时间"** | 几乎可以确定是 AI 自动生成的占位/草稿文 |

### B. 一手 / 权威信源白名单（优先采信）

- **公司官方**：newsroom.workday.com、openai.com/index、blogs.nvidia.com、investor.nvidia.com、anthropic.com/news、claude.com、investor.alibaba.com（IR 页面优先）
- **官方政府**：mfa.gov.cn（外交部）、sec.gov（SEC 文件）、bis.gov（美商务部）
- **一线财经媒体原创稿**：Bloomberg、Reuters、CNBC、华尔街见闻原创（wallstreetcn.com）、第一财经、财联社、彭博、路透、英国金融时报
- **行业一线媒体**：Tom's Hardware、TechCrunch、The Information、The New Stack、InfoWorld、VentureBeat、TrendForce、Counterpoint Research、IT之家、量子位、36氪原创
- **新华社、人民日报、央视、央广**（中国官媒，事件类报道权威）

### C. 信源核查 SOP（每条新闻必须跑完）

```
对每条候选新闻，按以下顺序执行：

1. 【一手源查找】先尝试找公司官网 Newsroom / IR / 官方公告原文
   ↓ 找到 → 取该来源为主信源，进入步骤3
   ↓ 找不到 → 进入步骤2

2. 【权威媒体核实】在白名单内找至少 1 篇原创报道
   ↓ 找到 → 取该来源为主信源，进入步骤3
   ↓ 找不到 → 用 WebSearch 加日期限定（如 "May 14 2026" 或 "5月14日 2026"）再搜
   ↓ 仍只能从低质量域名找到 → 整条新闻丢弃，不写入

3. 【交叉验证】至少再找 1 个独立信源（不同域名/不同媒体）确认
   ↓ 数字、日期、人物、事件细节一致 → 通过
   ↓ 信息冲突 → 以一手源为准，并在正文中标注差异

4. 【写入正文】每条新闻在正文中至少隐含两个可追溯锚点：
   - 明确日期（X月X日，...）
   - 具体数字 / 官方引述 / 公司名称
   - 来源类型（如"Bloomberg 援引知情人士"、"路透独家"、"公司公告"、"IR 页面披露"）

5. 【信源记录】完成后回复时，给出 Sources 区，每条新闻对应 1+ 链接
```

### D. 高风险话题特别处理

- **大模型发布**：必须查公司官方 Twitter/X、Newsroom、Hugging Face 模型卡，**禁止采信"榜单类知乎/CSDN 文章的更新日期"作为发布日**
- **季度财报**：必须查公司 IR 页面 / Bloomberg / 一线财经媒体首日原创稿，**禁止采信二手摘要中的"具体数字"**
- **政策/监管/外交**：必须查官方部委网站（mfa.gov.cn / bis.gov / 白宫）
- **IPO / 融资**：交叉验证 SEC 文件（stocktitan、SEC EDGAR）+ 一线财经媒体首日原创
- **市场行情**：用财联社、第一财经、新浪财经原创快讯，**禁止采信无具体点位的"涨跌幅"概述**

### E. 不确定时的处理原则

- **宁缺毋滥**：信源不足 → 不写。一周收录 5 条扎实的，比 15 条掺水的有价值。
- **明确标注存疑**：必要时可在该条末尾用括号注明 *(待官方确认)* 或 *(媒体报道，公司尚未确认)*。
- **回到用户**：如果某条用户特别关心的新闻确实只能找到 SEO 农场来源，直接说明"未找到可信信源"，**绝不为了"显得勤奋"而编造或包装可疑信息**。

---

## 第三·五步：自动更新 Excel 行情数据表

**在搜索新闻的同时，用 Bash 执行以下脚本**，自动从 yfinance 拉取市值、周涨跌幅、YTD 涨跌幅、PE-TTM、PS-TTM，并写入本周 Excel 文件（替换 Wind 公式列）。

```python
import sys, io, glob, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

import yfinance as yf
import openpyxl
from openpyxl.styles import numbers
from datetime import date, timedelta
from collections import defaultdict

# ── 日期 ──────────────────────────────────────────────────
today      = date.today()
monday     = today - timedelta(days=today.weekday())
sunday     = monday + timedelta(days=6)
last_fri   = monday - timedelta(days=3)
jan1       = date(today.year, 1, 1)
file_date  = sunday.strftime('%y%m%d')

OUT_DIR = r'D:\Work related\AI传媒互联网\A周报\AI应用周报 - skill'
# 以最近一期已有 xlsx 为模版，保存为本周新文件
existing = sorted([f for f in glob.glob(OUT_DIR + r'\*.xlsx') if '~$' not in f])
SRC = existing[-1]
DST = OUT_DIR + f'\\AI应用周报_{file_date}.xlsx'
print(f'模版: {SRC}\n输出: {DST}\n')

# ── 汇率（本地货币 → USD，用 USD* 对的倒数）────────────
FX = {'USD': 1.0}
for pair, cur in [('USDCNY=X','CNY'), ('USDHKD=X','HKD'), ('USDKRW=X','KRW')]:
    try:
        h = yf.Ticker(pair).history(period='5d')
        if not h.empty:
            FX[cur] = 1.0 / float(h['Close'].dropna().iloc[-1])
    except: pass
FX.setdefault('CNY', 1/7.25); FX.setdefault('HKD', 1/7.78); FX.setdefault('KRW', 1/1350)
print(f'汇率: CNY={FX["CNY"]:.4f} HKD={FX["HKD"]:.4f} KRW={FX["KRW"]:.6f}\n')

# ── Wind → yfinance 代码映射 ──────────────────────────────
def wind2yf(code):
    code = code.strip()
    if code.lower().endswith('.o'):  return code[:-2].upper()
    if code.lower().endswith('.n'):  return code[:-2].upper()
    if code.endswith('.SH'):         return code[:-3] + '.SS'
    if code.endswith('.HK'):         return code
    if code.endswith('.KS'):         return code
    return None

IDX_MAP = {
    'IXIC.GI':   '^IXIC',
    'SPX.GI':    '^GSPC',
    'HXC.GI':    '^HXC',
    'HSTECH.HI': '3032.HK',   # 恒生科技ETF 代替指数
}

# ── 类型安全转换（yfinance 有时返回字符串）─────────────
def safe_float(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None

# ── 拉单只股票数据 ────────────────────────────────────────
def fetch(ticker):
    """返回 (市值亿USD, 周%, YTD%, PE, PS) 或全 None"""
    try:
        tk   = yf.Ticker(ticker)
        info = tk.info
        cur  = info.get('currency', 'USD')
        fx   = safe_float(FX.get(cur, 1.0)) or 1.0

        # 市值：优先用 shares×price 自算（避免 KS 等市场 marketCap 单位异常）
        shares = safe_float(info.get('sharesOutstanding'))
        price  = safe_float(info.get('currentPrice')) or safe_float(info.get('regularMarketPrice'))
        if shares and price:
            mc = shares * price * fx / 1e8
        else:
            mc_raw = safe_float(info.get('marketCap'))
            mc = mc_raw * fx / 1e8 if mc_raw else None

        pe = safe_float(info.get('trailingPE'))
        ps = safe_float(info.get('priceToSalesTrailing12Months'))

        # 价格历史
        df = tk.history(start=last_fri.strftime('%Y-%m-%d'),
                        end=(today + timedelta(days=1)).strftime('%Y-%m-%d'))
        df = df.dropna(subset=['Close'])
        wk = (float(df['Close'].iloc[-1]) - float(df['Close'].iloc[0])) / float(df['Close'].iloc[0]) if len(df) >= 2 else None

        df2 = tk.history(start=jan1.strftime('%Y-%m-%d'),
                         end=(today + timedelta(days=1)).strftime('%Y-%m-%d'))
        df2 = df2.dropna(subset=['Close'])
        ytd = (float(df2['Close'].iloc[-1]) - float(df2['Close'].iloc[0])) / float(df2['Close'].iloc[0]) if len(df2) >= 2 else None

        return mc, wk, ytd, pe, ps
    except Exception as e:
        return None, None, None, None, None

# ── 处理指数（无市值/PS，但有PE近似）────────────────────
def fetch_idx(ticker):
    """返回 (周%, YTD%, PE近似, -, -)"""
    try:
        tk   = yf.Ticker(ticker)
        info = tk.info
        pe   = info.get('trailingPE')

        df   = tk.history(start=last_fri.strftime('%Y-%m-%d'),
                          end=(today + timedelta(days=1)).strftime('%Y-%m-%d'))
        df   = df.dropna(subset=['Close'])
        wk   = (float(df['Close'].iloc[-1]) - float(df['Close'].iloc[0])) / float(df['Close'].iloc[0]) if len(df) >= 2 else None

        df2  = tk.history(start=jan1.strftime('%Y-%m-%d'),
                          end=(today + timedelta(days=1)).strftime('%Y-%m-%d'))
        df2  = df2.dropna(subset=['Close'])
        ytd  = (float(df2['Close'].iloc[-1]) - float(df2['Close'].iloc[0])) / float(df2['Close'].iloc[0]) if len(df2) >= 2 else None

        # PE 1yr/3yr 分位数：用价格位置近似（无历史EPS，仅供参考）
        df3y = tk.history(start=(today - timedelta(days=365*3)).strftime('%Y-%m-%d'),
                          end=(today + timedelta(days=1)).strftime('%Y-%m-%d'))
        df3y = df3y.dropna(subset=['Close'])
        df1y = df3y[df3y.index >= str(today - timedelta(days=365))]
        cur_p = float(df3y['Close'].iloc[-1]) if not df3y.empty else None
        pct1y = (df1y['Close'] < cur_p).mean() if cur_p and not df1y.empty else None
        pct3y = (df3y['Close'] < cur_p).mean() if cur_p and not df3y.empty else None

        return wk, ytd, pe, pct1y, pct3y
    except:
        return None, None, None, None, None

# ── 读取并更新 Excel ──────────────────────────────────────
import shutil
shutil.copy2(SRC, DST)
wb = openpyxl.load_workbook(DST)

# ─ 更新「行情」Sheet ─
ws_hq = wb['行情']
# 找表头行（含"Wind代码"的行）
header_row = None
for r in ws_hq.iter_rows():
    for c in r:
        if c.value == 'Wind代码' or c.value == 'Wind代码':
            header_row = c.row
            break
    if header_row: break
if not header_row:
    header_row = 4  # 默认

# 列索引（从第1列=A=1）
# 根据实测：M=13 Wind代码, N=14 公司, O=15 市值, P=16 周%, Q=17 YTD%, R=18 PE, S=19 PS
COL_TICKER = 13; COL_MC = 15; COL_WK = 16; COL_YTD = 17; COL_PE = 18; COL_PS = 19

ok_count = 0
for row in ws_hq.iter_rows(min_row=header_row+1, max_row=ws_hq.max_row):
    wind_cell = row[COL_TICKER - 1]
    wind_code = wind_cell.value
    if not wind_code or not isinstance(wind_code, str) or '.' not in wind_code:
        continue
    yf_code = wind2yf(wind_code)
    if not yf_code:
        continue

    mc, wk, ytd, pe, ps = fetch(yf_code)
    r_idx = wind_cell.row

    def set_val(col, val):
        cell = ws_hq.cell(row=r_idx, column=col)
        cell.value = val

    set_val(COL_MC,  round(mc,  0) if mc  is not None else None)
    set_val(COL_WK,  round(wk,  4) if wk  is not None else None)
    set_val(COL_YTD, round(ytd, 4) if ytd is not None else None)
    set_val(COL_PE,  round(pe,  1) if pe  is not None else None)
    set_val(COL_PS,  round(ps,  1) if ps  is not None else None)
    ok_count += 1
    mc_s  = f'{mc:.0f}亿$'    if mc  is not None else 'N/A'
    wk_s  = f'{wk*100:+.1f}%' if wk  is not None else 'N/A'
    pe_s  = f'{pe:.1f}'        if pe  is not None else '-'
    print(f'  {wind_code:15s} -> {yf_code:12s} | 市值={mc_s:10s} | 周={wk_s:8s} | PE={pe_s}')

# ─ 更新「指数」Sheet ─
ws_idx = wb['指数']
# 列L=12 Wind代码, N=14 周%, O=15 YTD%, P=16 PE-TTM, Q=17 PE1yr分位, R=18 PE3yr分位
COL_I_CODE = 12; COL_I_WK = 14; COL_I_YTD = 15; COL_I_PE = 16; COL_I_P1 = 17; COL_I_P3 = 18
print('\n--- 指数 ---')
for row in ws_idx.iter_rows(min_row=1, max_row=ws_idx.max_row):
    code_cell = row[COL_I_CODE - 1]
    wind_code = code_cell.value
    if not wind_code or not isinstance(wind_code, str) or '.' not in wind_code:
        continue
    yf_code = IDX_MAP.get(wind_code)
    if not yf_code:
        continue

    wk, ytd, pe, p1y, p3y = fetch_idx(yf_code)
    r_idx = code_cell.row
    ws_idx.cell(row=r_idx, column=COL_I_WK).value  = round(wk, 4) if wk is not None else None
    ws_idx.cell(row=r_idx, column=COL_I_YTD).value = round(ytd, 4) if ytd is not None else None
    ws_idx.cell(row=r_idx, column=COL_I_PE).value  = round(pe, 1) if pe else None
    ws_idx.cell(row=r_idx, column=COL_I_P1).value  = round(p1y, 3) if p1y is not None else None
    ws_idx.cell(row=r_idx, column=COL_I_P3).value  = round(p3y, 3) if p3y is not None else None
    wk_s  = f'{wk*100:+.1f}%'  if wk  is not None else 'N/A'
    ytd_s = f'{ytd*100:+.1f}%' if ytd is not None else 'N/A'
    pe_s  = f'{pe:.1f}'         if pe  is not None else '-'
    p1_s  = f'{p1y:.1%}'        if p1y is not None else '-'
    p3_s  = f'{p3y:.1%}'        if p3y is not None else '-'
    print(f'  {wind_code:15s} -> {yf_code:10s} | 周={wk_s} | YTD={ytd_s} | PE={pe_s} | 1yr分位={p1_s} | 3yr分位={p3_s}')

wb.save(DST)
print(f'\n✅ Excel已保存: {DST}')
print(f'   行情更新: {ok_count} 只股票')
```

> **说明**：PE 近一年/三年分位数使用价格百分位近似（原 Wind 用历史PE计算，此处以价格位置代替，数量级参考）。如需精确 PE 分位需接入 Wind 或 Bloomberg。

---

## 第四步：搜索下周重要行业事件

搜索：
- `科技公司 财报 下周 YYYY年MM月`
- `AI发布会 峰会 下周 YYYY年MM月`
- `NVIDIA Meta Microsoft Google Amazon Apple 财报 YYYY年MM月`

重点关注：科技公司财报（Google/Meta/Microsoft/Amazon/Apple/NVIDIA等）、重要AI产品发布会、行业峰会。

---

## 第五步：生成Word文档

将第二至四步的真实内容填入以下Python脚本并执行。**删除所有占位符注释，只写有内容的分类。**

```python
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import date, timedelta

# ===== 日期计算 =====
today = date.today()
monday = today - timedelta(days=today.weekday())
sunday = monday + timedelta(days=6)
date_range = monday.strftime('%Y/%m/%d') + '-' + sunday.strftime('%Y/%m/%d')
file_date = sunday.strftime('%y%m%d')

OUTPUT_DIR = r"D:\Work related\AI传媒互联网\A周报\AI应用周报 - skill"
TEMPLATE = os.path.join(OUTPUT_DIR, 'AI应用周报_模版.docx')
OUTPUT = os.path.join(OUTPUT_DIR, f"AI应用周报_{file_date}.docx")

# ===== 从模版创建（保留样式定义）=====
doc = Document(TEMPLATE)
body = doc.element.body
sect_pr = body.find(qn('w:sectPr'))
for child in list(body):
    if child != sect_pr:
        body.remove(child)

FONT = '楷体'

def _set_font(run):
    run.font.name = FONT
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    for attr in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rFonts.set(qn(attr), FONT)
    rFonts.set(qn('w:hint'), 'eastAsia')

def _para(text, bold=False, center=False, size_pt=None):
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold = bold
    if size_pt:
        r.font.size = Pt(size_pt)
    _set_font(r)
    return p

def blank():
    doc.add_paragraph()

# ===== 封面 =====
_para('AI应用周报', center=True)
_para(date_range, center=True, size_pt=10.5)
blank()

# ===== 周度行情更新 =====
_para('周度行情更新', bold=True, center=True)

# 以下三段替换为真实搜索到的行情内容
_para('本周（X/XX-X/XX），美股整体……纳斯达克……标普500……纳斯达克金龙指数……')
_para('港股方面，恒生科技指数……')
_para('A股方面，AI芯片/算力/半导体板块……')

blank()

# ===== AI行业更新 =====
_para('AI行业更新', bold=True, center=True)


def section(name):
    """分类标题：AI芯片 / AI大模型 等"""
    _para(name, bold=True)

def news(company, headline, body_text):
    """
    一条新闻：
      第1行：【公司名】标题  —— 加粗
      第2行起：正文段落     —— 不加粗，body_text 用 \\n 分段

    ⚠️ 强制格式约束（deal-breaker）：
      body_text 第一句必须以 'X月X日，' 开头（阿拉伯数字 + 月 + 日 + 逗号）。
      违反此规则的内容不允许写入文档。运行前可用以下校验：
          import re
          assert re.match(r'^\\d{1,2}月\\d{1,2}日(至\\d{1,2}月\\d{1,2}日|-\\d{1,2}日)?[，,]',
                          body_text.strip()), f'缺少日期开头: {body_text[:20]}'
    """
    import re
    _first = body_text.strip().split('\n')[0].strip()
    if not re.match(r'^\d{1,2}月\d{1,2}日', _first):
        raise ValueError(f'[news 格式错误] body_text 第一句必须以 "X月X日，" 开头，实际收到: {_first[:30]}')
    _para(f'【{company}】{headline}', bold=True)
    for line in body_text.strip().split('\n'):
        line = line.strip()
        if line:
            _para(line)


# ----------------------------------------------------------------
# 以下分类按本周实际有新闻的填写，无新闻整段删除
# ----------------------------------------------------------------

section('AI芯片')
# news('NVIDIA', '...标题...', 'X月X日，...正文...')
# news('台积电', '...标题...', 'X月X日，...正文...')

blank()
section('AI存储')
# news('SK海力士', '...标题...', 'X月X日，...正文...')

blank()
section('AI云')
# news('AWS', '...标题...', 'X月X日，...正文...')

blank()
section('AI大模型')
# news('OpenAI', '...标题...', 'X月X日，...正文...')
# news('Anthropic', '...标题...', 'X月X日，...正文...')

blank()
section('AI多模态')
# news('快手可灵', '...标题...', 'X月X日，...正文...')

blank()
section('AI Agent')
# news('OpenAI', '...标题...', 'X月X日，...正文...')

blank()
section('AI智驾')
# news('Tesla', '...标题...', 'X月X日，...正文...')

blank()
section('AI端侧/机器人')
# news('特斯拉 Optimus', '...标题...', 'X月X日，...正文...')

# 以下分类仅本周有重要动态时才写
# blank()
# section('AI教育')
# news('...', '...', '...')

# blank()
# section('AI硬件')
# news('...', '...', '...')

blank()

# ===== 下周行业事件预告 =====
_para('下周行业事件预告', bold=True, center=True)


def event(index, date_str, event_name, highlight, extra=''):
    """
    一个事件：
      第1行：N、日期时间｜事件名  —— 加粗
      第2行：亮点：...           —— 不加粗
      第3行（可选）：补充说明
    """
    _para(f'{index}、{date_str}｜{event_name}', bold=True)
    _para(f'亮点：{highlight}')
    if extra:
        _para(extra)


# 填入下周真实事件
# event(1, 'X月XX日 盘后（北京时X月XX日凌晨）', 'Microsoft FY2026 Q4财报',
#       'Azure增速与AI货币化进展，分析师预期EPS约$X.XX、营收约XXX亿美元。')
# event(2, 'X月XX日 盘后（北京时X月XX日凌晨）', 'Meta Q2财报',
#       'AI广告系统效果与资本支出，Llama商业化路径。')

# ===== 保存 =====
os.makedirs(OUTPUT_DIR, exist_ok=True)
doc.save(OUTPUT)
print(f'✅ 文档已保存：{OUTPUT}')
```

---

## 执行规范

### 内容质量
- **信源核实（强制门槛）**：每条新闻必须通过第三·四步的核查 SOP，**2+ 独立信源交叉验证**。SEO 农场内容（无具体数字 / 多家公司同日发布 / 仅单一低质量域名 / 标题"汇总/盘点/横评"）**一律不得写入正文**。
- **本周时效**：所有新闻必须是本周（周一至周日）7天内，早于周一一律不写
- **具体日期（强制 deal-breaker）**：每条新闻 body_text 的第一句**必须**以 `X月X日，` 开头（阿拉伯数字 + 月 + 日 + 中文逗号）。`news()` 函数内置 assert 校验，缺日期会直接抛 ValueError 中断生成——这是顶层设计上的硬约束，不允许跳过。禁用 `本周/近日/日前/周中/X月下旬/X月初` 等模糊表述作为开头。
- **有内容才写**：该公司/分类本周确无重要动态则跳过，不强行凑数。**宁可一周只收 5 条扎实的，也不放 15 条掺水的。**
- **正文标准**：2-4句，含具体数字（金额/参数/涨幅等），客观陈述，不加主观评价。**正文中必须出现可追溯锚点**：明确日期 + 具体数字 + 信源类型（如"Bloomberg 援引知情人士"、"公司公告"、"IR 披露"）。
- **标题**：15字以内，概括核心事件
- **行情三段**：分别写美股+金龙、港股恒生科技、A股AI板块；每段含具体指数点位或涨跌幅数字。**禁止采信无具体点位的"涨跌幅"概述。**

### 格式规范
- 公司名格式：中国公司用中文（阿里巴巴、字节跳动），国际公司用英文或通用中文名（NVIDIA、OpenAI）
- 联合事件用 & 连接（NVIDIA&CoreWeave）
- `news()` 函数的 body_text 用 `\n` 分段（同一条新闻若有多个要点）
- 事件预告的 date_str 格式：`X月XX日 盘后（北京时X月XX日凌晨）` 或 `X月XX日（北京时间周X）`

### 数据扎实度抓手（参考 GPT 版本 2026-05-31 沉淀经验）

GPT 同题对照下发现的差距：我们容易满足于"事件覆盖到"，但缺少"扎实到"的颗粒度。下次必须把以下要素加进正文，作为质量底线：

1. **行情段落要带"周内标志性单股大涨/大跌"**：如戴尔财报后+32.8%、寒武纪市值突破9000亿、上证科创50单日-5.04% 等具体单点数据。不能只写指数涨跌幅。
2. **财报新闻要带"季度收入绝对值 + 同比/环比 + 指引"三件套**：例 Marvell FY27 Q1 24.18亿美元 / +28% / +9%。
3. **融资新闻要带"ARR、算力GW数、产业链股权细节"**：例 Anthropic 5月 ARR 470亿、亚马逊5GW + 谷歌/博通5GW TPU、SpaceX Colossus、三星/SK海力士/美光战略入股。
4. **存储/HBM 新闻要带"HBM bit出货量假设、长协年限+延长期权"**：例 UBS 2026年 HBM 出货77.8亿Gb、2027年 120.5亿Gb；SK海力士与谷歌 DRAM 长协 5+2 年结构。
5. **下周事件预告必须含"行业大会"而不只是财报**：COMPUTEX / GTC / WAIC / 苹果WWDC / 谷歌 I/O 等行业大事 + 主旨演讲人 + 议题（如 Intel CEO Lip-Bu Tan在 COMPUTEX 2026 主题演讲）。仅列财报会丢失50%下周关键信息。
6. **港股行情要带"个股大模型双雄轮动"**：MiniMax / 智谱 / 商汤等个股的盘中动作，对应资金在 AI 硬件 vs 模型间的轮动判断。

> 这 6 条是"颗粒度对齐"的硬抓手，本质是要求每条新闻能给出可以直接抄进研报的具体数据点，而不是"事件提及"。

### 文件命名
- 文件名：`AI应用周报_YYMMDD.docx`（YYMMDD为本周**周日**日期）
- 保存路径：`D:\Work related\AI传媒互联网\A周报\AI应用周报 - skill\`

---

## 执行流程

1. **Bash** → 计算本周日期
2. **WebSearch ×6** → 行情数据（并行执行）
3. **Alpha派 / WebSearch** → 逐分类搜索（共约60个词，分批并行执行，每批6-8个）
4. **🚨 第三·四步 信源核实（强制门槛）** → 对每条候选新闻执行核查 SOP：①找一手源 ②白名单权威媒体核实 ③至少 1 个独立交叉源 ④识别并剔除 SEO 农场内容。**未通过的内容直接丢弃，不进入下一步。**
5. **WebSearch ×2** → 下周事件（同样需信源核实）
6. **Bash** → 将真实内容填入Python脚本，执行生成Word文档
7. **汇报**：文档路径 + 各分类收录条数 + 本周共收录X条 + **Sources 区**（每条对应 1+ 链接）

### 失败案例（反面教材，必读）

**2026-05-17 第一版周报错误示例：**
- ❌ "5月13日七家大模型同日发布旗舰新版本（Gemini 3 Pro / GPT-5.1 / Claude Haiku 4.5 / Grok 4.1 / Kimi-K2-Thinking / MiniMax-M2 / Veo 3.1）"
- 根因：采信了"知乎更新日期为 5/13 的榜单类汇总文章"，把**文章更新日**误当作**事件发生日**
- 应该这样做：每个模型分别去公司官方 X/Newsroom 单独核实发布日，没找到的就不写。结果第二版只保留了真实可核实的 Anthropic 计费拆账、Workday-MS Copilot 集成、百度文心5.1（Create大会5/13-14）等条目。

**关键认知**：在 2026 年这种 LLM 大量参与内容生产的时间窗口，**WebSearch 召回结果的可信度本身就被污染了**。所以信源核实不是"做得好不好"的问题，而是"做不做"的红线问题。

---

## 完成后汇报格式

```
✅ 文档已生成：AI应用周报_YYMMDD.docx

各分类收录：
  AI芯片：X条  AI存储：X条  AI云：X条
  AI大模型：X条  AI多模态：X条  AI Agent：X条
  AI智驾：X条  AI端侧/机器人：X条
  （AI教育：X条  AI硬件：X条）

本周共收录：XX条
搜索覆盖公司：XX家
```
