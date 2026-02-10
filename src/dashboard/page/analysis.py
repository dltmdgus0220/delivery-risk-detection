import json
import pandas as pd
import plotly.express as px
from collections import Counter
import streamlit as st
from streamlit_plotly_events import plotly_events
from datetime import datetime
from dateutil.relativedelta import relativedelta
from src.dashboard.util import fetch_month_df, parse_keywords, set_korean_font, keyword_count, top_n_keywords_extract, detect_keyword_changes


# --- 1. 유틸 ---

# 전역 css
def inject_css():
    st.markdown(
        """
        <style>
          :root{
            --muted:#64748b;
            --text:#0f172a;
            --border:#e2e8f0;
            --green:#16a34a;
            --red:#dc2626;
          }

          /* KPI 카드 */
          .kpi{
            background:#f8fafc;
            border:1px solid var(--border);
            border-radius:12px;
            padding:14px 14px 12px;
          }
          .kpi .label{
            font-size:13px;
            color:var(--muted);
            margin-bottom:6px;
          }
          .kpi .value{
            font-size:28px;
            font-weight:800;
            color:var(--text);
            line-height:1.1;
          }

          /* mini 카드 (확정/불만/없음) */
          .mini{
            background:#f8fafc;
            border:1px solid var(--border);
            border-radius:12px;
            padding:12px;
          }
          .mini .title{
            font-size:13px;
            color:var(--muted);
            margin-bottom:6px;
          }
          .mini .count{
            font-size:20px;
            font-weight:800;
            color:var(--text);
          }
          .mini .ratio{
            font-size:12px;
            color:var(--muted);
            font-weight:500;
            margin-left:6px;
          }

          /* 증감 pill */
          .pill{
            display:inline-flex;
            align-items:center;
            padding:3px 10px;
            border-radius:999px;
            font-size:12px;
            font-weight:700;
            margin-top:10px;
            border:1px solid transparent;
          }
          .pill.pos{
            color:var(--green);
            background:rgba(22,163,74,.10);
            border-color:rgba(22,163,74,.18);
          }
          .pill.neg{
            color:var(--red);
            background:rgba(220,38,38,.10);
            border-color:rgba(220,38,38,.18);
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

