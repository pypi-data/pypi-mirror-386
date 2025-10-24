# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2025/6/5 16:58
@author: ZhangYundi
@email: yundi.xxii@outlook.com
---------------------------------------------
"""
from typing import Union, Optional, Iterable

import pandas as pd

from . import tables
import polars as pl
import lidb

def get_secumain() -> pl.DataFrame:
    """
    获取证券主表 (SecuMain) 数据

    Returns
    -------

    Notes
    -----
    - 返回的表格中的 `null` 值表示缺失数据，例如某些证券的 `ListedDate` 可能为空。
    - 上市板块 (`ListedSector`) 的值对应不同的特别处理状态：
        - 1: 主板
        - 2: 中小企业版
        - 3: 三板
        - 4: 其他
        - 5: 大宗交易系统
        - 6: 创业板
        - 7: 科创板
        - 8: 北交所股票
    - 所属市场 (`SecuMarket`) 的值对应不同的特别处理状态：
        - 83: 上海证券交易所
        - 90: 深圳证券交易所
    - 上市状态 (`ListedState`) 的值对应不同的特别处理状态：
        - 1: 上市
        - 2: 预上市
        - 3: 暂停
        - 4: 上市失败
        - 5: 终止
        - 9: 其他
        - 10: 交易
        - 11: 停牌
        - 12: 摘牌
    """
    query = f"select * from {tables.TB_SECU_MAIN};"
    return lidb.sql(query).rename({"SecuCode": "asset"}).collect()

def get_industry() -> pl.DataFrame:
    """
    获取行业分类表 (Industry) 数据, 分类标准: 申万行业(2021版)。返回的表格包含以下信息：

    - `asset`: 证券代码
    - `InfoPublDate`: 信息发布日期
    - `Lv1`: 行业一级分类
    - `Lv2`: 行业二级分类
    - `Lv3`: 行业三级分类

    Returns
    -------
    """
    query = f"select * from {tables.TB_INDUSTRY_SW};"
    return lidb.sql(query).drop("InnerCode").rename({"SecuCode": "asset"}).collect()

def get_shares() -> pl.DataFrame:
    """
    获取股本结构表 (Shares) 数据。返回的表格包括以下字段：

    - `asset`: 证券代码
    - `EndDate`: 截止日期，表示该条股本信息的截止时间
    - `InfoPublDate`: 信息发布日期
    - `TotalShares`: 总股本
    - `AShares`: A股股本
    - `AFloats`: A股流通股本

    Returns
    -------
    """

    query = f"select * from {tables.TB_SHARES_INFO};"
    return lidb.sql(query).drop("InnerCode").rename({"SecuCode": "asset"}).collect()

def get_st() -> pl.DataFrame:
    """
    获取特别处理表 (SpecialTrade) 数据。返回的表格包括以下字段：

    - `asset`: 证券代码
    - `InfoPublDate`: 信息发布日期，表示该特别处理信息的发布日期
    - `SpecialTradeType`: 特别处理类型，表示证券的特别处理类型
    - `SpecialTradeDate`: 特别处理日期，表示证券进入或解除特别处理的日期

    Returns
    -------

    Notes
    -----
    特别处理类型 (`SpecialTradeType`) 的值对应不同的特别处理状态：

    - 1: ST
    - 2: 撤销ST
    - 3: PT
    - 4: 撤销PT
    - 5: *ST
    - 6: 撤销*ST
    - 7: 撤销*ST并实现ST
    - 8: 从ST变为*ST
    - 9: 退市整理期
    - 10: 高风险警示
    - 11: 撤销高风险警示
    - 12: 叠加ST
    - 13: 撤销叠加ST
    - 14: 叠加*ST
    - 15: 撤销叠加*ST

    """
    query = f"select * from {tables.TB_SPECIAL_TRADE};"
    secu_codes = f"select InnerCode, SecuCode from {tables.TB_SECU_MAIN};"
    secu_df = lidb.sql(secu_codes)
    st_df = secu_df.join(lidb.sql(query), on="InnerCode", how="inner")
    return st_df.drop("InnerCode").rename({"SecuCode": "asset"}).collect()

def get_liststatus():
    """
    获取上市状态更改表 (ListStatus) 数据。

    - `asset`: 证券代码
    - `SecuAbbr`: 证券简称
    - `ChangeDate`: 上市状态变更日期
    - `ChangeType`: 上市状态变更类型

    Returns
    -------

    Notes
    -----
    - 上市状态变更类型 (`ChangeType`) 的值代表不同的状态变更：

        - 1: 上市
        - 2: 暂停上市
        - 3: 恢复上市
        - 4: 终止上市
        - 5: 摘牌
        - 6: 退市整理期
        - 9: 其它

    - 返回的表格中的 `ChangeDate` 表示上市状态变更的具体日期

    """
    query = f"select * from {tables.TB_LIST_STATUS};"
    return lidb.sql(query).drop("InnerCode").rename({"SecuCode": "asset"}).collect()

def get_codes(date, )->list[str]:
    """
    每日的可交易的A股个股,提取的逻辑为：每日的第一根分钟k线(09:31:00)有成交
    """
    query = f"select distinct asset from {tables.TB_STOCK_KLINE_MINUTE} where date='{date}' and time <= '09:31:00' and volume > 0;"
    return lidb.sql(query).collect()["asset"].sort().to_list()

def convert_inner2secu(df: Union[pl.DataFrame | pd.DataFrame], codes: Optional[Iterable[str]] = None):
    """
    将 DataFrame 中的 `InnerCode` 转换为对应的 `asset`。

    该函数将 `df` 中的 `InnerCode` 列替换为对应的 `asset` 列。若提供 `codes` 参数，则返回仅包含这些 `asset` 的数据。

    Parameters
    ----------
    df : pl.DataFrame | pd.DataFrame
        包含 `InnerCode` 列的输入 DataFrame。可以是 Polars 或 Pandas 格式。
    codes : Iterable[str] | None
        想要筛选的 `asset` 列表。如果提供此参数，返回值将只包含这些 `asset`。

    Returns
    -------
    pl.DataFrame
        转换后的 DataFrame，`InnerCode` 列将被映射为 `asset`。

    Examples
    --------
    将 Pandas DataFrame 中的 `InnerCode` 转换为 `asset`：

    >>> df = pd.DataFrame({'InnerCode': [3, 6, 11]})
    >>> convert_inner2secu(df)
    shape: (3, 1)
    ┌──────────┐
    │ asset    │
    │ ---      │
    │ str      │
    ├──────────┤
    │ 000001   │
    │ 000002   │
    │ 000003   │
    └──────────┘

    仅返回特定的 `SecuCode`：

    Notes
    -----
    - 函数会自动将 Pandas DataFrame 转换为 Polars DataFrame 处理。
    - 如果提供了 `codes` 参数，返回的 DataFrame 只包含这些 `asset`，并且会去除包含 `NaN` 的行。
    """
    if isinstance(df, pd.DataFrame):
        df = pl.from_pandas(df.reset_index())
    secu_info = get_secumain()
    new_codes = df.select("InnerCode").join(secu_info.select("InnerCode", "asset"), on="InnerCode", how="left")["asset"]
    res = df.with_columns(new_codes.alias("InnerCode")).rename({"InnerCode": "asset"})
    if codes is not None:
        target_index = pl.DataFrame({"asset": codes})
        res = target_index.join(res, on="asset", how="left")
    return res.drop_nulls(subset=["asset"])