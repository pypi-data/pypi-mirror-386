# src/finosdk/__init__.py
from __future__ import annotations

import os
from typing import Any, List, Optional

import pandas as pd

# 轻量 HTTP 客户端
from .client import Client
# 异常定义（并兼容 from finosdk import APIError 的老用法）
from .exceptions import (
    FinoError,
    FinoHTTPError,
    FinoAPIError,
    FinoValidationError,
)
APIError = FinoAPIError  # 兼容别名

__all__ = [
    # 初始化
    "init",
    # 异常
    "FinoError", "FinoHTTPError", "FinoAPIError", "FinoValidationError", "APIError",
    # fac 系列
    "get_fac_carry", "get_fac_trend", "get_fac_position",
    "get_fac_futurespot", "get_fac_value", "get_fac_warrant", "get_fac_volatility",
    # csft 系列
    "get_csft_bkt_perf", "get_csft_bkt_data", "get_csft_bkt_dcp",
    "get_csft_test_perf", "get_csft_test_data", "get_csft_test_dcp",
    # 兼容/泛用入口
    "get_factor_values",
]

# 全局客户端实例（按需初始化）
_CLIENT: Optional[Client] = None


# ===================== 初始化 =====================
def init(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: int = 30,
    username: Optional[str] = None,  # 预留；当前不用
    password: Optional[str] = None,  # 预留；当前不用
) -> Client:
    """
    初始化 SDK 连接信息。

    优先级:
    1) 传参 base_url / api_key
    2) 环境变量 FINOSDK_BASE_URL / FINOSDK_TOKEN
    3) 默认 base_url = http://127.0.0.1:8003/data_api, 无 token
    """
    del username, password  # 当前未使用，避免 lint 提示
    global _CLIENT
    base_url = base_url or os.environ.get("FINOSDK_BASE_URL", "http://127.0.0.1:8003/data_api")
    token = api_key or os.environ.get("FINOSDK_TOKEN")
    _CLIENT = Client(base_url=base_url, token=token, timeout=timeout)
    return _CLIENT


def _require_client() -> Client:
    """确保有可用客户端；若未初始化则按默认值 init()。"""
    global _CLIENT
    if _CLIENT is None:
        init()
    return _CLIENT


# ===================== DataFrame 辅助 =====================
def _maybe_df(
    rows: Any,
    as_df: bool,
    sort_by: Optional[List[str]] = None,
    ascending: Optional[List[bool]] = None,
) -> Any:
    """按需将 rows 转为 DataFrame，并可选排序。"""
    if not as_df:
        return rows
    if rows is None:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if sort_by:
        sort_cols = [c for c in sort_by if c in df.columns]
        if sort_cols:
            asc = ascending if ascending and len(ascending) == len(sort_cols) else [True] * len(sort_cols)
            df = df.sort_values(by=sort_cols, ascending=asc, kind="mergesort")
    return df


# ===================== fac_* 系列 =====================
def _fac_call(
    api: str,
    start_date: str,
    end_date: str,
    code_list: Optional[List[str]] = None,
    factor: Optional[List[str]] = None,
    section: Optional[List[str]] = None,
    *,
    as_df: bool = True,
) -> Any:
    """
    通用 fac_* 入口；默认返回 DataFrame，
    并尝试按 factor_k asc, date asc, value desc 排序（若列存在）。
    """
    c = _require_client()
    rows = getattr(c, api)(
        start_date=start_date,
        end_date=end_date,
        code_list=code_list,
        factor=factor,
        section=section,
    )
    return _maybe_df(
        rows,
        as_df=as_df,
        sort_by=["factor_k", "date", "value"],
        ascending=[True, True, False],
    )


def get_fac_carry(start_date: str, end_date: str,
                  code_list: Optional[List[str]] = None,
                  factor: Optional[List[str]] = None,
                  section: Optional[List[str]] = None,
                  *, as_df: bool = True):
    """期限结构/价差类因子。"""
    return _fac_call("fac_carry", start_date, end_date, code_list, factor, section, as_df=as_df)


def get_fac_trend(start_date: str, end_date: str,
                  code_list: Optional[List[str]] = None,
                  factor: Optional[List[str]] = None,
                  section: Optional[List[str]] = None,
                  *, as_df: bool = True):
    """趋势类因子。"""
    return _fac_call("fac_trend", start_date, end_date, code_list, factor, section, as_df=as_df)


def get_fac_position(start_date: str, end_date: str,
                     code_list: Optional[List[str]] = None,
                     factor: Optional[List[str]] = None,
                     section: Optional[List[str]] = None,
                     *, as_df: bool = True):
    """持仓类因子。"""
    return _fac_call("fac_position", start_date, end_date, code_list, factor, section, as_df=as_df)


def get_fac_futurespot(start_date: str, end_date: str,
                       code_list: Optional[List[str]] = None,
                       factor: Optional[List[str]] = None,
                       section: Optional[List[str]] = None,
                       *, as_df: bool = True):
    """期现类因子。"""
    return _fac_call("fac_futurespot", start_date, end_date, code_list, factor, section, as_df=as_df)


def get_fac_value(start_date: str, end_date: str,
                  code_list: Optional[List[str]] = None,
                  factor: Optional[List[str]] = None,
                  section: Optional[List[str]] = None,
                  *, as_df: bool = True):
    """价值类因子。"""
    return _fac_call("fac_value", start_date, end_date, code_list, factor, section, as_df=as_df)


def get_fac_warrant(start_date: str, end_date: str,
                    code_list: Optional[List[str]] = None,
                    factor: Optional[List[str]] = None,
                    section: Optional[List[str]] = None,
                    *, as_df: bool = True):
    """仓单类因子。"""
    return _fac_call("fac_warrant", start_date, end_date, code_list, factor, section, as_df=as_df)


def get_fac_volatility(start_date: str, end_date: str,
                       code_list: Optional[List[str]] = None,
                       factor: Optional[List[str]] = None,
                       section: Optional[List[str]] = None,
                       *, as_df: bool = True):
    """波动率类因子。"""
    return _fac_call("fac_volatility", start_date, end_date, code_list, factor, section, as_df=as_df)


# ===================== csft_* 系列 =====================
def _csft_call(
    api: str,
    start_date: str,
    end_date: str,
    factor: Optional[List[str]] = None,
    *,
    as_df: bool = True,
) -> Any:
    """
    通用 csft_* 入口；默认返回 DataFrame，不做特定排序（以服务端顺序为准）。
    factor 不传或传 [] => 全量。
    """
    c = _require_client()
    rows = getattr(c, api)(
        start_date=start_date,
        end_date=end_date,
        factor=factor if factor else None,
    )
    return _maybe_df(rows, as_df=as_df, sort_by=None)


def get_csft_bkt_perf(start_date: str, end_date: str,
                      factor: Optional[List[str]] = None, *, as_df: bool = True):
    return _csft_call("csft_bkt_perf", start_date, end_date, factor, as_df=as_df)


def get_csft_bkt_data(start_date: str, end_date: str,
                      factor: Optional[List[str]] = None, *, as_df: bool = True):
    return _csft_call("csft_bkt_data", start_date, end_date, factor, as_df=as_df)


def get_csft_bkt_dcp(start_date: str, end_date: str,
                     factor: Optional[List[str]] = None, *, as_df: bool = True):
    return _csft_call("csft_bkt_dcp", start_date, end_date, factor, as_df=as_df)


def get_csft_test_perf(start_date: str, end_date: str,
                       factor: Optional[List[str]] = None, *, as_df: bool = True):
    return _csft_call("csft_test_perf", start_date, end_date, factor, as_df=as_df)


def get_csft_test_data(start_date: str, end_date: str,
                       factor: Optional[List[str]] = None, *, as_df: bool = True):
    return _csft_call("csft_test_data", start_date, end_date, factor, as_df=as_df)


def get_csft_test_dcp(start_date: str, end_date: str,
                      factor: Optional[List[str]] = None, *, as_df: bool = True):
    return _csft_call("csft_test_dcp", start_date, end_date, factor, as_df=as_df)


# ===================== 兼容：泛用入口 =====================
def get_factor_values(
    start_date: str, end_date: str,
    code_list: Optional[List[str]] = None,
    factor: Optional[List[str]] = None,
    section: Optional[List[str]] = None,
    *, api: str = "fac_carry", as_df: bool = True,
) -> Any:
    """
    兼容老用法：指定 api='fac_carry'|'fac_trend'|...，其余参数一致。
    """
    return _fac_call(api, start_date, end_date, code_list, factor, section, as_df=as_df)
