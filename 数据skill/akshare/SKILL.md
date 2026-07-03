---
name: akshare
description: AKShare 中国金融数据接口技能。覆盖 A股、港股、美股、基金、期货、债券、外汇、宏观经济等数据获取。当用户需要获取股票行情、财务数据、基金净值、期货价格、宏观经济指标、沪深股票列表等金融数据时使用本 skill。关键词：AKShare、股票数据、行情、财务报表、基金净值、期货、宏观数据。
metadata:
    version: 1.0
    akshare_version: 1.18.59
---

# AKShare 金融数据 Skill

AKShare 是开源的 Python 金融数据接口库，封装了 100+ 数据源，提供 A股、港股、美股、基金、期货、债券、外汇及宏观经济数据。

**安装**：`pip install akshare --upgrade`  
**文档**：https://akshare.akfamily.xyz/

## 快速验证

```python
import akshare as ak
print(ak.__version__)
```

---

## 一、A股数据

### 1.1 历史行情（最常用）

```python
import akshare as ak

# 日线数据，前复权
df = ak.stock_zh_a_hist(
    symbol="000001",       # 股票代码（不含市场后缀）
    period="daily",        # daily / weekly / monthly
    start_date="20240101",
    end_date="20241231",
    adjust="qfq"           # "" 不复权 | "qfq" 前复权 | "hfq" 后复权
)
# 返回列：日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
```

### 1.2 分钟级行情

```python
df = ak.stock_zh_a_minute(
    symbol="sh000001",     # 需加市场前缀：sh / sz
    period="5",            # 1 / 5 / 15 / 30 / 60
    adjust="qfq"
)
```

### 1.3 实时行情（全市场快照）

```python
# 东方财富源，返回全部 A 股实时行情（PE、市值、换手率等）
df = ak.stock_zh_a_spot_em()

# 五档买卖盘口
df = ak.stock_bid_ask_em(symbol="000001")
```

### 1.4 股票基本信息

```python
# 公司基础信息（总股本、市值、行业、上市日期等）
df = ak.stock_individual_info_em(symbol="000001")

# 沪深全部股票列表
df = ak.stock_info_a_code_name()
```

### 1.5 财务报表

```python
# 利润表（按报告期）
df = ak.stock_financial_report_sina(stock="sh600519", symbol="利润表")

# 资产负债表
df = ak.stock_financial_report_sina(stock="sh600519", symbol="资产负债表")

# 现金流量表
df = ak.stock_financial_report_sina(stock="sh600519", symbol="现金流量表")

# 东财财务指标（ROE、毛利率等）
df = ak.stock_financial_abstract_ths(symbol="600519", indicator="按年度")
```

### 1.6 龙虎榜 / 资金流向

```python
# 个股资金流向（近 10 日）
df = ak.stock_individual_fund_flow(stock="000001", market="sz")

# 大盘资金流向
df = ak.stock_market_fund_flow()

# 当日龙虎榜
df = ak.stock_lhb_detail_em(date="20241231")
```

---

## 二、指数数据

```python
# 上证指数历史数据
df = ak.stock_zh_index_daily(symbol="sh000001")

# 沪深300成分股
df = ak.index_stock_cons(symbol="000300")

# 实时指数行情
df = ak.stock_zh_index_spot_em()
```

---

## 三、基金数据

```python
# 开放式基金净值历史
df = ak.fund_open_fund_info_em(fund="000001", indicator="单位净值走势")

# 全部基金基本信息列表
df = ak.fund_name_em()

# ETF 实时行情
df = ak.fund_etf_spot_em()

# ETF 历史行情
df = ak.fund_etf_hist_em(
    symbol="510300",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq"
)
```

---

## 四、期货数据

```python
# 期货实时行情（可选交易所）
df = ak.futures_zh_spot(subscribe_list=["IF2506"], market="cffex")

# 期货历史行情（主力合约）
df = ak.futures_main_sina(symbol="V0", start_date="20240101", end_date="20241231")

# 商品期货持仓排名（龙虎榜）
df = ak.futures_positions_sina(symbol="I0")
```

---

## 五、宏观经济数据

```python
# CPI 月度数据
df = ak.macro_china_cpi_monthly()

# PPI 月度数据
df = ak.macro_china_ppi_monthly()

# GDP 季度数据
df = ak.macro_china_gdp_yearly()

# M2 货币供应量
df = ak.macro_china_money_supply()

# PMI 制造业
df = ak.macro_china_pmi_monthly()

# 美联储利率决议
df = ak.macro_bank_usa_interest_rate()
```

---

## 六、港股 / 美股

```python
# 港股实时行情
df = ak.stock_hk_spot_em()

# 港股历史行情
df = ak.stock_hk_hist(
    symbol="00700",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq"
)

# 美股实时行情
df = ak.stock_us_spot_em()

# 美股历史行情
df = ak.stock_us_hist(
    symbol="AAPL",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq"
)
```

---

## 七、债券 / 外汇

```python
# 国债收益率曲线
df = ak.bond_china_yield(start_date="20240101", end_date="20241231")

# 人民币汇率中间价
df = ak.currency_boc_sina(currency="USD", start_date="20240101", end_date="20241231")

# 外汇牌价（实时）
df = ak.currency_latest()
```

---

## 八、新闻 / 公告

```python
# 个股新闻（东方财富）
df = ak.stock_news_em(symbol="000001")

# 上市公司公告
df = ak.stock_notice_report(market="A", keyword="分红")
```

---

## 使用规范

1. **代码格式**：A 股代码传 6 位数字（如 `"000001"`），部分接口需加市场前缀（`sh000001` / `sz000001`）——以函数文档为准。
2. **日期格式**：大多数接口用 `"YYYYMMDD"`，少数用 `"YYYY-MM-DD"`——以函数签名为准。
3. **返回类型**：所有接口均返回 `pandas.DataFrame`，可直接用 `.to_csv()` / `.to_excel()` 导出。
4. **频率限制**：部分数据源有 IP 限频，批量拉取时建议加 `time.sleep(0.5)`。
5. **错误处理**：接口偶发网络超时，建议 `try/except` 包裹并重试。

## 常见问题排查

| 现象 | 可能原因 | 解决方案 |
|------|----------|----------|
| 返回空 DataFrame | 日期范围无数据或代码有误 | 检查代码格式、缩短日期范围 |
| 网络超时 | 数据源服务器不稳定 | 重试或换备用接口（如 `_em` 系列） |
| 版本不兼容 | akshare 接口名称有调整 | `pip install akshare --upgrade` |
| 频率限制 | 短时间大量请求 | 添加 `time.sleep()` |

## 升级

```bash
pip install akshare --upgrade
python -c "import akshare as ak; print(ak.__version__)"
```
