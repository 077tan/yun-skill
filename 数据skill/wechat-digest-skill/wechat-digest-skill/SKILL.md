---
name: wechat-daily
description: 微信投研日报 — 读取本地微信聊天记录，自动去重聚类生成投研日报。触发词：微信复盘、微信日报、投研日报、生成日报、/wechat-daily
metadata:
  version: 1.2
  dependencies: pycryptodome, zstandard
---

# 微信投研日报

自动读取本地微信数据库，提取投研相关消息，跨群去重，按主题聚类输出日报。

## 前置准备

### 1. 安装依赖

```bash
pip3 install pycryptodome zstandard
```

### 2. 确保微信已登录

首次运行需要微信在后台登录，以便从内存中提取数据库密钥。

## 使用方法

在 Claude Code 中说"生成日报"或"微信复盘"，会自动运行本 skill。

也可直接在终端运行：

```bash
python3 invest_daily.py               # 分析今天
python3 invest_daily.py 2026-06-01    # 分析指定日期
python3 invest_daily.py --setup       # 重新配置
```

**首次运行**会自动启动交互式向导：
1. 提取微信数据库密钥（需要微信已登录）
2. 扫描你的全部群聊列表
3. 通过关键词或手动选择，标记哪些是投研群
4. 设置主题分类规则
5. 保存到 `~/.wechat-digest/user_config.json`

之后直接运行即出报告，无需再配置。

## 执行流程

1. 加载 `~/.wechat-digest/user_config.json`（不存在则启动向导）
2. 检查密钥文件，不存在则自动提取
3. 解密 `contact.db` 获取联系人名称映射
4. 遍历 `message_0.db ~ message_9.db` 按时间提取消息
5. 按用户配置过滤，仅保留投研相关群/联系人
6. 跨群去重（同内容 >=3 群合并为一条跨群热点）
7. 按主题聚类输出
8. 提取关键事件日历
9. 输出结构化投研日报

## 输出格式

- 跨群热点 — 同内容被 >=3 个群推送的消息
- 投研主题分析 — 按配置的主题分类
- 关键事件 — 含路演/调研/电话会等关键词的日程
- 数据统计 — 覆盖群数、消息数、去重数

## 安全说明

- 全本地运行，不上传任何数据
- 密钥保存在 `~/.wechat-digest/all_keys.json`（仅当前用户可读）
- 用户配置保存在 `~/.wechat-digest/user_config.json`
- 解密后的临时数据库自动清理
