# 深度研究报告 JSON 数据结构说明

`generate_report.py` 接收一个结构化 JSON 文件，Claude 在撰写完报告内容后应将内容整理为以下格式，再调用脚本生成 Word 文档。

---

## 顶层结构

```json
{
  "meta": { ... },
  "company_info": { ... },
  "indices": [ ... ],
  "benchmark_name": "上证综合指数",
  "price_performance": [ ... ],
  "financials": { ... },
  "reputation": [ "段落1", "段落2", ... ],
  "annual_review": [ ... ],
  "annual_summary": { ... },
  "price_review": [ ... ],
  "key_pivots": [ ... ],
  "qualitative_analysis": [ "段落1", ... ],
  "trading_logic": { ... }
}
```

---

## meta（封面元数据）

```json
"meta": {
  "company_name_cn": "天山铝业集团股份有限公司",
  "company_name_en": "Tianshan Aluminum Group Co., Ltd.",
  "ticker": "002532.SZ",
  "exchange": "深圳证券交易所",
  "core_view": "产能天花板确立后的最大受益者，新疆低电价+全产业链一体化铸就成本护城河...",
  "report_date": "2026年3月14日"
}
```

---

## company_info（1.1 企业基本信息）

```json
"company_info": {
  "founded": "1997年",
  "listed": "2020年7月，借壳新界泵业（002532）重组上市",
  "ticker": "002532.SZ（深圳证券交易所）",
  "hq": "新疆维吾尔自治区乌鲁木齐市",
  "ownership": "民营企业",
  "controller": "曾超懿、曾超林（兄弟，合计持股约42%）...",
  "bases": "①新疆石河子...②广西靖西...③江阴...",
  "capital_events": "①2024年7月完成1亿元回购..."
}
```

---

## indices（所属股票指数表）

```json
"indices": [
  { "name": "沪深300指数", "note": "A股核心蓝筹指数成分股" },
  { "name": "深证成指",    "note": "深交所综合指数成分股" }
]
```

---

## price_performance（1.2 股价表现，逐年）

```json
"price_performance": [
  {
    "year": "2021",
    "stock_return": "+12.9%",
    "index_return": "+4.8%",
    "excess_return": "+8.1%",
    "driver": "业绩翻倍，铝价大涨至历史高点"
  }
]
```

---

## financials（1.3 财务概况）

```json
"financials": {
  "years": ["2020A", "2021A", "2022A", "2023A", "2024A", "2025前三季"],
  "income_statement": {
    "2020A": {
      "revenue":         "274.6",
      "revenue_yoy":     "—",
      "gross_profit":    "37.5",
      "gross_margin":    "13.7%",
      "opex_ratio":      "3.5%",
      "op_profit":       "23.9",
      "op_margin":       "8.7%",
      "net_profit":      "19.1",
      "net_profit_yoy":  "—",
      "net_margin":      "7.0%"
    }
  },
  "balance_sheet": {
    "2020A": {
      "cash":                 "105.3",
      "trade_receivables":    "9.2",
      "inventory":            "56.0",
      "ppe":                  "240.9",
      "construction":         "30.8",
      "intangibles":          "10.9",
      "goodwill_investments": "—",
      "total_assets":         "505.9",
      "short_debt":           "85.9",
      "long_debt":            "37.9",
      "contract_liabilities": "17.1",
      "trade_payables":       "18.7",
      "equity":               "193.0"
    }
  }
}
```

> **注意**：所有数值均为字符串（已含单位格式），Claude 不需要做数字计算，直接填入即可。

---

## annual_review（2.1 逐年阅读，每年一个对象）

```json
"annual_review": [
  {
    "title": "2020年：借壳上市元年，奠定全链基础",
    "kpis": {
      "营业收入": "274.6亿元",
      "归母净利润": "19.12亿元（超额完成业绩承诺30%）",
      "毛利率": "13.7%（铝价偏弱，广西氧化铝仍在建）",
      "经营现金流": "30.98亿元"
    },
    "content": [
      "2020年是公司历史性一年：7月通过借壳...",
      "广西250万吨氧化铝产线处于爬坡阶段...",
      "管理层在重组上市仪式上确立了全产业链一体化的战略定位..."
    ]
  }
]
```

---

## annual_summary（2.2 综合总结）

键为小标题，值为段落列表：

```json
"annual_summary": {
  "业务发展脉络与商业模式": [
    "公司的生意本质是...",
    "核心竞争力来源于..."
  ],
  "行业周期分析": [
    "公司历史上的景气高峰年份为2021年和2024年..."
  ],
  "关键战略决策复盘": [
    "决策一：广西氧化铝项目...",
    "决策二：几内亚矿权收购..."
  ]
}
```

---

## price_review（第三部分：股价复盘，每个阶段一个对象）

```json
"price_review": [
  {
    "title": "第一阶段：借壳上市蜜月期（2020年7月—2021年10月）│ 4.90→9.94，+103%",
    "content": [
      "2020年7月借壳完成后...",
      "2021年铝价从年初约15,000元/吨大涨至年中约21,000元/吨..."
    ]
  }
]
```

---

## key_pivots（关键拐点汇总表）

```json
"key_pivots": [
  {
    "date":   "2024/02/02",
    "price":  "4.63元",
    "type":   "历史底部",
    "reason": "前复权历史最低点，雪球踩踏引发超跌，PE约7倍，为最大确定性买点。"
  }
]
```

---

## qualitative_analysis（第四部分：定性认识，段落列表）

```json
"qualitative_analysis": [
  "天山铝业是一家在特定约束条件下具备高度竞争力的企业...",
  "它的核心竞争力是真实且持久的——新疆低电价+一体化成本结构...",
  "然而，它并不是一家能够摆脱大宗商品周期的公司..."
]
```

---

## trading_logic（第五部分：当下交易逻辑）

```json
"trading_logic": {
  "current_narrative": [
    "当前市场对天山铝业讲的主要故事是：全球电解铝供给天花板+新能源需求持续增长..."
  ],
  "implied_earnings": [
    "机构一致预测2026年净利润约59亿元，对应2026年PE约10-11倍..."
  ],
  "divergence": [
    "多方逻辑：①4500万吨天花板政策极为刚性...",
    "空方逻辑：①全球海外电解铝产能仍在缓慢增加..."
  ],
  "catalysts": [
    "铝价超预期上涨：若2026年铝价均值达22,000元/吨以上...",
    "24万吨产能超预期提前达产：若2026年Q1即全面达产..."
  ],
  "risks": [
    "铝价大幅下跌：若铝价跌至18,000元/吨附近...",
    "实控人大规模减持：曾氏兄弟近期公告合计再减持约2%..."
  ],
  "peer_comparison": [
    {
      "company":    "天山铝业",
      "advantage":  "新疆低电价+全链一体化+24万吨扩产",
      "profit_est": "~50亿",
      "growth":     "量价齐升，确定性强",
      "risk":       "实控人减持；深加工爬坡慢"
    }
  ],
  "recommendation": [
    "直接结论：当前价格（约13-15元区间）具备持有价值，但不是大仓位激进介入的最佳时机。",
    "逻辑：公司基本面方向清晰，2026年量价齐升的故事可信...",
    "核心观察指标：①铝价LME/沪铝走势；②每月铝土矿到岸成本及自给率进度..."
  ]
}
```

---

## 使用说明

Claude 在完成研究内容撰写后：

1. 将所有内容整理为上述 JSON 格式，存储为 `/home/claude/report_data.json`
2. 执行脚本：
   ```bash
   pip install python-docx --break-system-packages -q
   python scripts/generate_report.py \
     --data /home/claude/report_data.json \
     --output /mnt/user-data/outputs/[公司名]_深度研究报告_[日期].docx
   ```
3. 用 `python scripts/office/validate.py` 验证输出文件

> **字段缺失处理**：所有字段均为可选，JSON 中缺少的字段脚本会自动跳过对应章节，不会报错。
