# AKShare API

[![PyPI version](https://badge.fury.io/py/akshare-api.svg)](https://badge.fury.io/py/akshare-api)
[![Python Support](https://img.shields.io/pypi/pyversions/akshare-api.svg)](https://pypi.org/project/akshare-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/akshare-api)](https://pepy.tech/project/akshare-api)

基于AKTools公开API的AKShare股票数据接口Python调用库，提供完整的股票数据获取功能。

## ✨ 特性

- 🎯 **接口完整**: 涵盖AKShare文档中所有股票相关的数据接口（共98个接口）
- 🌍 **市场全面**: 支持A股、B股、港股、美股等多个市场
- 🔥 **功能丰富**: 包含实时行情、历史数据、基本面分析、资金流向等高级功能
- 🚀 **调用简便**: 通过封装的Python方法，一行代码即可获取数据
- ⚙️ **参数灵活**: 支持多种参数配置，满足不同分析需求
- 🛡️ **错误处理**: 内置异常处理机制，确保程序稳定运行
- 📊 **数据格式**: 统一返回pandas.DataFrame格式，便于数据分析
- 📚 **文档详细**: 每个接口都包含完整的参数说明和使用示例

## 📦 安装

### 从PyPI安装（推荐）

```bash
pip install akshare-api
```

### 从源码安装

```bash
git clone https://github.com/JoshuaMaoJH/akshare-api.git
cd akshare-api
pip install -e .
```

## 🚀 快速开始

### 基础使用

```python
from akshare_api import stock_zh_a_spot_em, stock_zh_a_hist

# 获取A股实时行情
spot_data = stock_zh_a_spot_em()
print(f"共获取到 {len(spot_data)} 只股票数据")

# 获取历史行情数据
hist_data = stock_zh_a_hist(symbol="000001", start_date="20240101", end_date="20240131")
print(hist_data.head())
```

### 面向对象使用

```python
from akshare_api import AKShareAPI

# 创建API客户端
api = AKShareAPI(base_url="http://127.0.0.1:8080")

# 获取数据
data = api.stock_zh_a_spot_em()
print(data.head())
```

### 命令行工具

```bash
# 测试API连接
akshare-api --test-connection

# 列出所有可用接口
akshare-api --list-interfaces

# 指定API基础URL
akshare-api --base-url http://localhost:8080 --test-connection
```

## 📊 支持的接口

### 接口统计总览

| 分类 | 接口数量 | 说明 |
|------|----------|------|
| **A股数据接口** | 47个 | 包含市场总貌、个股信息、实时行情、历史数据、分时数据等 |
| **B股数据接口** | 4个 | B股实时行情、历史数据、分时数据 |
| **港股数据接口** | 3个 | 港股实时行情、历史数据 |
| **美股数据接口** | 3个 | 美股实时行情、历史数据 |
| **高级功能接口** | 36个 | 基本面数据、资金流向、概念板块、行业分析等 |
| **其他功能接口** | 5个 | 股票比较分析相关接口 |
| **总计** | **98个** | **完整的股票数据接口库** |

### 🏢 A股数据接口 (47个)

#### 市场总貌 (5个)
- `stock_sse_summary()` - 上海证券交易所总貌数据
- `stock_szse_summary()` - 深圳证券交易所总貌数据
- `stock_szse_area_summary()` - 深圳证券交易所地区交易排序
- `stock_szse_sector_summary()` - 深圳证券交易所股票行业成交数据
- `stock_sse_deal_daily()` - 上海证券交易所每日概况数据

#### 个股信息查询 (2个)
- `stock_individual_info_em()` - 个股信息查询-东方财富
- `stock_individual_basic_info_xq()` - 个股信息查询-雪球

#### 实时行情数据 (10个)
- `stock_zh_a_spot_em()` - 沪深京A股实时行情-东方财富
- `stock_sh_a_spot_em()` - 沪A股实时行情-东方财富
- `stock_sz_a_spot_em()` - 深A股实时行情-东方财富
- `stock_bj_a_spot_em()` - 京A股实时行情-东方财富
- `stock_new_a_spot_em()` - 新股实时行情-东方财富
- `stock_cy_a_spot_em()` - 创业板实时行情-东方财富
- `stock_kc_a_spot_em()` - 科创板实时行情-东方财富
- `stock_zh_ab_comparison_em()` - AB股比价-东方财富
- `stock_zh_a_spot()` - 沪深京A股实时行情-新浪
- `stock_individual_spot_xq()` - 个股实时行情-雪球

#### 历史行情数据 (3个)
- `stock_zh_a_hist()` - 历史行情数据-东方财富
- `stock_zh_a_daily()` - 历史行情数据-新浪
- `stock_zh_a_hist_tx()` - 历史行情数据-腾讯

#### 分时数据 (5个)
- `stock_zh_a_minute()` - 分时数据-新浪
- `stock_zh_a_hist_min_em()` - 分时数据-东方财富
- `stock_intraday_em()` - 日内分时数据-东方财富
- `stock_intraday_sina()` - 日内分时数据-新浪
- `stock_zh_a_hist_pre_min_em()` - 盘前数据-东方财富

### 🌍 其他市场数据接口

#### B股数据接口 (4个)
- `stock_zh_b_spot_em()` - B股实时行情-东方财富
- `stock_zh_b_spot()` - B股实时行情-新浪
- `stock_zh_b_daily()` - B股历史行情数据-新浪
- `stock_zh_b_minute()` - B股分时数据-新浪

#### 港股数据接口 (3个)
- `stock_hk_spot_em()` - 港股实时行情-东方财富
- `stock_hk_spot()` - 港股实时行情-新浪
- `stock_hk_daily()` - 港股历史行情数据-新浪

#### 美股数据接口 (3个)
- `stock_us_spot()` - 美股实时行情-新浪
- `stock_us_spot_em()` - 美股实时行情-东方财富
- `stock_us_daily()` - 美股历史行情数据-新浪

### 🔥 高级功能接口 (36个)

#### 涨停板行情 (3个)
- `stock_zt_pool_em()` - 涨停股池
- `stock_zt_pool_previous_em()` - 昨日涨停股池
- `stock_dt_pool_em()` - 跌停股池

#### 龙虎榜 (2个)
- `stock_lhb_detail_em()` - 龙虎榜详情
- `stock_lhb_stock_statistic_em()` - 个股上榜统计

#### 机构相关 (5个)
- `stock_institute_visit_em()` - 机构调研统计
- `stock_institute_visit_detail_em()` - 机构调研详细
- `stock_institute_hold_detail()` - 机构持股详情
- `stock_institute_recommend()` - 机构推荐池
- `stock_institute_recommend_detail()` - 股票评级记录

#### 研报资讯 (6个)
- `stock_research_report_em()` - 个股研报
- `stock_info_cjzc_em()` - 财经早餐
- `stock_info_global_em()` - 全球财经快讯-东方财富
- `stock_info_global_sina()` - 全球财经快讯-新浪财经
- `stock_news_em()` - 个股新闻-东方财富
- `stock_news_main_cx()` - 财经内容精选-财新网

## 📖 使用示例

### 1. 获取市场总貌数据

```python
from akshare_api import stock_sse_summary, stock_szse_summary

# 获取上海证券交易所总貌
sse_summary = stock_sse_summary()
print(sse_summary.head())

# 获取深圳证券交易所总貌
szse_summary = stock_szse_summary()
print(szse_summary.head())
```

### 2. 获取实时行情数据

```python
from akshare_api import stock_zh_a_spot_em, stock_cy_a_spot_em

# 获取所有A股实时行情
all_stocks = stock_zh_a_spot_em()
print(f"共获取到 {len(all_stocks)} 只股票数据")

# 获取创业板实时行情
cy_stocks = stock_cy_a_spot_em()
print(f"创业板股票 {len(cy_stocks)} 只")
```

### 3. 获取历史行情数据

```python
from akshare_api import stock_zh_a_hist

# 获取不复权历史数据
hist_data = stock_zh_a_hist(symbol="000001", period="daily", 
                           start_date="20210301", end_date="20210616")

# 获取前复权历史数据
hist_qfq = stock_zh_a_hist(symbol="000001", period="daily", 
                          start_date="20210301", end_date="20210616", adjust="qfq")

# 获取周线数据
weekly_data = stock_zh_a_hist(symbol="000001", period="weekly", 
                             start_date="20210301", end_date="20210616")
```

### 4. 数据分析和保存

```python
import pandas as pd
from akshare_api import stock_zh_a_spot_em

# 获取实时行情数据
spot_data = stock_zh_a_spot_em()

# 数据分析
print(f"总股票数: {len(spot_data)}")
print(f"上涨股票: {len(spot_data[spot_data['涨跌幅'] > 0])}")
print(f"下跌股票: {len(spot_data[spot_data['涨跌幅'] < 0])}")
print(f"平均涨跌幅: {spot_data['涨跌幅'].mean():.2f}%")

# 筛选涨幅大于5%的股票
high_gain_stocks = spot_data[spot_data['涨跌幅'] > 5]
print(f"涨幅大于5%的股票有 {len(high_gain_stocks)} 只")

# 保存数据
spot_data.to_csv('stock_data.csv', index=False, encoding='utf-8-sig')
spot_data.to_excel('stock_data.xlsx', index=False)
```

### 5. 批量数据获取

```python
import time
from akshare_api import stock_zh_a_hist

def batch_get_stock_data(symbols, start_date, end_date):
    """批量获取多只股票的历史数据"""
    results = {}
    for symbol in symbols:
        try:
            df = stock_zh_a_hist(symbol=symbol, start_date=start_date, end_date=end_date)
            results[symbol] = df
            print(f"成功获取 {symbol} 的数据")
            time.sleep(0.5)  # 避免请求过于频繁
        except Exception as e:
            print(f"获取 {symbol} 数据失败: {e}")
    return results

# 使用示例
symbols = ["000001", "000002", "600000", "600036"]
data_dict = batch_get_stock_data(symbols, "20230101", "20231231")
```

## ⚙️ 配置

### 环境要求

- Python 3.7 及以上版本
- AKTools服务已启动（默认端口8080）

### API基础URL配置

```python
from akshare_api import AKShareAPI

# 使用默认URL
api = AKShareAPI()

# 自定义URL
api = AKShareAPI(base_url="http://your-server:8080")
```

## 🛠️ 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black akshare_api/
```

### 类型检查

```bash
mypy akshare_api/
```

## 📝 注意事项

### 数据源限制
- **新浪财经**: 重复运行函数会被暂时封IP，建议增加时间间隔
- **东方财富**: 数据质量高，访问无限制，推荐使用
- **腾讯证券**: 数据稳定，但接口相对较少

### 参数格式
- **日期格式**: 通常使用"YYYYMMDD"格式，如"20210301"
- **分时数据**: 使用"YYYY-MM-DD HH:MM:SS"格式
- **股票代码**: A股使用6位数字，如"000001"

### 复权数据说明
- **不复权**: 默认返回原始价格数据
- **前复权(qfq)**: 保持当前价格不变，调整历史价格
- **后复权(hfq)**: 保持历史价格不变，调整当前价格

## 🤝 贡献

欢迎对本项目提出建议或贡献代码：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📄 许可证

本项目采用 MIT 许可证进行授权，详情请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 感谢 [AKShare](https://github.com/akfamily/akshare) 项目提供的数据接口
- 感谢 [AKTools](https://github.com/akfamily/aktools) 项目提供的API服务

## 📞 联系方式

- 项目地址：https://github.com/JoshuaMaoJH/akshare-api
- 问题反馈：https://github.com/JoshuaMaoJH/akshare-api/issues
- 文档地址：https://github.com/JoshuaMaoJH/akshare-api#readme

如有任何问题或建议，欢迎通过Issue与我们联系。

## 📈 更新日志

### v1.0.0 (2024-01-01)

**初始版本发布**

#### ✨ 新增功能
- 🎉 **完整接口库**: 包含所有98个AKShare接口
- 🌍 **多市场支持**: 支持A股、B股、港股、美股数据接口
- 🔥 **高级功能**: 涨停板、龙虎榜、机构调研、研报资讯等高级功能接口
- 📊 **接口统计**: 完整的接口分类统计和使用说明
- 🐍 **Python封装**: 面向对象和函数式两种调用方式
- 🛠️ **CLI工具**: 命令行工具支持接口列表和连接测试
- 📚 **完整文档**: 详细的API文档和使用示例

#### 📈 接口数量
- **A股数据接口**: 47个（市场总貌、实时行情、历史数据、分时数据等）
- **B股数据接口**: 4个（实时行情、历史数据、分时数据）
- **港股数据接口**: 3个（实时行情、历史数据）
- **美股数据接口**: 3个（实时行情、历史数据）
- **高级功能接口**: 36个（基本面、资金流向、概念板块等）
- **其他功能接口**: 5个（比较分析、特殊功能等）

---

**注意**: 使用前请确保AKTools服务已正确启动，并遵守相关数据源的使用条款。
