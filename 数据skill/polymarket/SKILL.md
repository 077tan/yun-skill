---
name: polymarket
description: Polymarket 去中心化预测市场数据查询技能。获取热门市场列表、赔率、交易量、流动性等数据。当用户需要查询预测市场数据、政治/体育/加密货币赔率、Polymarket市场行情时使用。关键词：Polymarket、预测市场、赔率、prediction market、概率、去中心化。
metadata:
    version: 1.0
    py_clob_client_version: 0.34.6
---

# Polymarket 预测市场数据 Skill

Polymarket 是全球最大的去中心化预测市场，基于 Polygon 链，交易量数十亿美元。本 skill 封装两套 API：
- **Gamma API**（推荐）：市场发现、热门排行、赔率、交易量——无需认证
- **CLOB API**（py-clob-client）：订单簿、深度、交易执行——需要钱包签名

**安装**：`pip install py-clob-client`  
**Gamma API**：`https://gamma-api.polymarket.com`（公开，无需 API Key）  
**CLOB API Host**：`https://clob.polymarket.com`

---

## 一、热门市场列表（最常用）

```python
import requests

def get_hot_markets(limit=10, order='volume24hr'):
    """
    获取热门预测市场
    order 可选: volume24hr | volume | liquidity | startDate | endDate
    """
    url = 'https://gamma-api.polymarket.com/markets'
    params = {
        'active': 'true',
        'closed': 'false',
        'order': order,
        'ascending': 'false',
        'limit': limit
    }
    resp = requests.get(url, params=params, timeout=15)
    markets = resp.json()
    
    for i, m in enumerate(markets, 1):
        import json
        outcomes = json.loads(m['outcomes']) if isinstance(m['outcomes'], str) else m['outcomes']
        prices = json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'], str) else m['outcomePrices']
        volume = float(m.get('volume', 0))
        liquidity = float(m.get('liquidity', 0))
        end_date = m.get('endDate', 'N/A')[:10] if m.get('endDate') else 'N/A'
        
        print(f"{i}. {m['question']}")
        odds_str = '  '.join(f"{o}: {float(p)*100:.1f}%" for o, p in zip(outcomes, prices))
        print(f"   {odds_str}")
        print(f"   总交易量: ${volume:,.0f} | 流动性: ${liquidity:,.0f} | 截止: {end_date}")
        print()
    
    return markets

# 使用示例
markets = get_hot_markets(limit=5)
```

---

## 二、搜索特定市场

```python
import requests

def search_markets(keyword, limit=5):
    """按关键词搜索市场"""
    url = 'https://gamma-api.polymarket.com/markets'
    params = {
        'active': 'true',
        'closed': 'false',
        'order': 'volume',
        'ascending': 'false',
        'limit': 100  # 获取更多再过滤
    }
    resp = requests.get(url, params=params, timeout=15)
    markets = resp.json()
    
    keyword_lower = keyword.lower()
    filtered = [m for m in markets if keyword_lower in m.get('question', '').lower()]
    return filtered[:limit]

# 搜索比特币相关市场
btc_markets = search_markets('Bitcoin')
for m in btc_markets:
    print(m['question'])
```

---

## 三、获取市场详情

```python
import requests, json

def get_market_detail(condition_id):
    """获取单个市场详细信息"""
    url = f'https://gamma-api.polymarket.com/markets/{condition_id}'
    resp = requests.get(url, timeout=15)
    return resp.json()

# 也可以通过 CLOB API 获取（需要 condition_id）
from py_clob_client.client import ClobClient
client = ClobClient(host='https://clob.polymarket.com')
market = client.get_market(condition_id='0x...')
```

---

## 四、获取订单簿（实时买卖盘）

```python
from py_clob_client.client import ClobClient

client = ClobClient(host='https://clob.polymarket.com')

# 获取 token_id（从市场的 tokens 字段取）
token_id = "市场token_id"
orderbook = client.get_order_book(token_id)
print("买盘:", orderbook.bids[:3])
print("卖盘:", orderbook.asks[:3])
```

---

## 五、分类查询（政治/体育/加密/科技）

```python
import requests

def get_markets_by_tag(tag, limit=5):
    """
    常用 tag: politics | sports | crypto | science | economics | culture
    """
    url = 'https://gamma-api.polymarket.com/markets'
    params = {
        'active': 'true',
        'closed': 'false',
        'tag': tag,
        'order': 'volume24hr',
        'ascending': 'false',
        'limit': limit
    }
    resp = requests.get(url, params=params, timeout=15)
    return resp.json()

# 获取政治类热门
politics = get_markets_by_tag('politics')
for m in politics:
    print(m['question'])
```

---

## 六、市场数据字段说明

| 字段 | 说明 |
|------|------|
| `question` | 市场问题 |
| `outcomes` | 可能结果列表，如 `["Yes","No"]` |
| `outcomePrices` | 各结果当前概率（0-1），即隐含赔率 |
| `volume` | 历史总交易量（USDC） |
| `volume24hr` | 近24小时交易量 |
| `liquidity` | 当前流动性池大小 |
| `endDate` | 市场结算截止日期 |
| `conditionId` | 市场唯一标识（CLOB API 用） |
| `slug` | URL友好标识，如 `will-bitcoin-hit-100k` |
| `active` | 是否开放交易 |
| `closed` | 是否已结算 |

---

## 七、完整热门市场展示脚本

```python
import requests, json

def show_top_polymarkets(n=5, order='volume24hr'):
    url = 'https://gamma-api.polymarket.com/markets'
    resp = requests.get(url, params={
        'active': 'true', 'closed': 'false',
        'order': order, 'ascending': 'false', 'limit': n
    }, timeout=15)
    
    markets = resp.json()
    print(f"=== Polymarket Top {n} 预测市场 (排序: {order}) ===\n")
    
    for i, m in enumerate(markets, 1):
        outcomes = json.loads(m['outcomes']) if isinstance(m['outcomes'], str) else m['outcomes']
        prices = json.loads(m['outcomePrices']) if isinstance(m['outcomePrices'], str) else m['outcomePrices']
        
        vol = float(m.get('volume24hr') or 0)
        liq = float(m.get('liquidity') or 0)
        end = (m.get('endDate') or 'N/A')[:10]
        
        print(f"{i}. {m['question']}")
        for o, p in zip(outcomes, prices):
            bar = '█' * int(float(p) * 20)
            print(f"   {o:6s}: {float(p)*100:5.1f}% {bar}")
        print(f"   24h量: ${vol:>12,.0f} | 流动性: ${liq:>10,.0f} | 截止: {end}")
        print()

show_top_polymarkets(5)
```

---

## 使用规范

1. **无需 API Key**：Gamma API 公开访问，CLOB 的只读接口（价格/订单簿）也无需认证
2. **需要认证的操作**：下单、取消订单需要以太坊私钥签名（CLOB API）
3. **价格即概率**：`outcomePrices` 是 0-1 之间的小数，直接代表市场对事件发生的概率估计
4. **货币单位**：所有交易量和流动性均为 USDC
5. **网络**：数据来自 Polygon 链，API 服务器在美国，国内可能需要代理

## 常见问题

| 现象 | 原因 | 解决 |
|------|------|------|
| SSL 连接失败 | 网络代理/防火墙 | 检查代理设置或使用 VPN |
| CLOB get_markets() 返回旧数据 | 默认从最旧游标开始分页 | 改用 Gamma API |
| 价格为 0.5/0.5 | 市场刚创建或流动性不足 | 查看 liquidity 字段确认 |
| 市场 closed=True 但 accepting=True | Polymarket 历史数据问题 | 以 Gamma API 的 active+closed 字段为准 |
