import streamlit as st
import sqlite3
import asyncio
import ast
import altair as alt
import pandas as pd
from datetime import datetime, timedelta
from src.dashboard.pipeline import run_pipeline
from src.dashboard.util import parse_keywords


TABLE = 'data'
DATE_COL = 'at'

# --- 유틸 ---

def _month_range(today:datetime, offset_months: int = 0):
    """offset_months=0 1달전, -1 2달전 (today 기준)"""
    first_month = today.replace(day=1) - timedelta(days=1)

    y = first_month.year
    m = first_month.month + offset_months
    while m <= 0:
        y -= 1
        m += 12
    while m >= 13:
        y += 1
        m -= 12

    start = datetime(y, m, 1)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    end = next_month - timedelta(days=1)
    return start, end

def _count_between(conn, start_dt: datetime, end_dt: datetime) -> int:
    cur = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM {TABLE}
        WHERE date({DATE_COL}) BETWEEN date(?) AND date(?)
        """,
        (start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")),
    )
    n = cur.fetchone()[0]
    cur.close()
    return int(n)

def _minmax_and_total(conn):
    cur = conn.execute(
        f"""
        SELECT MIN(date({DATE_COL})), MAX(date({DATE_COL})), COUNT(*)
        FROM {TABLE}
        """
    )
    mn, mx, total = cur.fetchone()
    cur.close()
    return mn, mx, int(total)

def _fmt_yy_mm_dd(s: str) -> str:
    dt = datetime.strptime(s, "%Y-%m-%d")
    return dt.strftime("%y.%m.%d")

def _fmt_k(n: int) -> str:
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return f"{n}"

# --- 메인 렌더링 유틸 ---

def _has_data_between(conn, start_dt: datetime, end_dt: datetime) -> bool:
    cur = conn.execute(
        f"""
        SELECT 1
        FROM {TABLE}
        WHERE date({DATE_COL}) BETWEEN date(?) AND date(?)
        LIMIT 1
        """,
        (start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")),
    )
    row = cur.fetchone()
    cur.close()
    return row is not None

def _pick_target_month(db_path: str, today: datetime):
    """
    이번달 데이터 있으면 이번달, 없으면 지난달을 선택
    return: (start_dt, end_dt, subtitle_str)
    """
    conn = sqlite3.connect(db_path)
    try:
        cur_s, cur_e = _month_range(today, 0)
        if _has_data_between(conn, cur_s, cur_e):
            target_s, target_e = cur_s, cur_e
        else:
            prev_s, prev_e = _month_range(today, -1)
            target_s, target_e = prev_s, prev_e
    finally:
        conn.close()
    subtitle = target_s.strftime("%y년 %m월 데이터 현황")
    return target_s, target_e, subtitle

def _fetch_month_df(conn, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    df = pd.read_sql_query(
        f"""
        SELECT {DATE_COL} as at, churn_intent_label, keywords
        FROM {TABLE}
        WHERE date({DATE_COL}) BETWEEN date(?) AND date(?)
        """,
        conn,
        params=(start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")),
    )
    df["at"] = pd.to_datetime(df["at"]).dt.date
    return df

def _label_name(x: int) -> str:
    # 네 파이프라인 기준: 0=없음, 1=불만, 2=확정
    return {0: "없음", 1: "불만", 2: "확정"}.get(int(x), str(x))

def _topn_keywords_by_class(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    tmp = df.copy()
    tmp["class_name"] = tmp["churn_intent_label"].fillna(-1).astype(int).map(_label_name)
    tmp["kw_list"] = tmp["keywords"].apply(parse_keywords)

    # explode 후 집계
    tmp = tmp.explode("kw_list")
    tmp = tmp[tmp["kw_list"].notna() & (tmp["kw_list"].astype(str).str.strip() != "")]

    out = (
        tmp.groupby(["class_name", "kw_list"])
        .size()
        .reset_index(name="cnt")
        .sort_values("cnt", ascending=False)
    )

    # 클래스별 topN
    out = out.groupby("class_name", as_index=False, group_keys=False).head(top_n)
    out = out.rename(columns={"kw_list": "keyword"})
    return out

