import json
import sqlite3
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import streamlit as st

from src.dashboard.util import keyword_count, target_keyword_ratio, top_n_keywords_extract, parse_keywords


# --- 유틸 ---
# 한글 폰트 설정
def set_korean_font():
    mpl.rcParams["font.family"] = "NanumGothic"
    # 마이너스 기호 깨짐 방지
    mpl.rcParams["axes.unicode_minus"] = False

# 전역 css
def inject_css():
    st.markdown(
        """
        <style>
          :root{
            --bg:#ffffff;
            --card:#ffffff;
            --muted:#64748b;
            --text:#0f172a;
            --border:#e2e8f0;
            --shadow: 0 1px 2px rgba(15,23,42,.06);
            --radius: 14px;
            --gap: 14px;

            --green:#16a34a;
            --red:#dc2626;
            --blue:#2563eb;
          }

          /* 섹션 카드 */
          .panel{
            background:var(--card);
            border:1px solid var(--border);
            border-radius:var(--radius);
            padding:16px;
            box-shadow:var(--shadow);
          }

          /* KPI 그리드 */
          .kpi-grid{
            display:grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--gap);
          }

          /* KPI 카드 */
          .kpi{
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 14px 12px;
          }
          .kpi .label{ font-size:13px; color:var(--muted); margin-bottom:6px; }
          .kpi .value{ font-size:28px; font-weight:800; color:var(--text); line-height:1.1; }
          .kpi .sub{ margin-top:6px; font-size:13px; color:var(--muted); }

          /* delta pill */
          .pill{
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:3px 10px;
            border-radius:999px;
            font-size:12px;
            font-weight:700;
            margin-top:10px;
            border:1px solid transparent;
          }
          .pill.pos{ color:var(--green); background: rgba(22,163,74,.10); border-color: rgba(22,163,74,.18); }
          .pill.neg{ color:var(--red);   background: rgba(220,38,38,.10); border-color: rgba(220,38,38,.18); }

          /* 3개 요약 카드(확정/불만/없음) */
          .mini{
            background:#f8fafc;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
          }
          .mini .title{ font-size:13px; color:var(--muted); margin-bottom:6px; }
          .mini .count{ font-size:20px; font-weight:800; color:var(--text); }
          .mini .ratio{ font-size:12px; color:var(--muted); font-weight:500; margin-left:6px; }

          /* 섹션 타이틀 */
          .section-title{
            font-size:16px;
            font-weight:800;
            margin: 0 0 12px 0;
          }

          /* Streamlit 기본 metric 델타 색이 튀면 숨기고 커스텀으로 통일하고 싶을 때 */
          /* [data-testid="stMetricDelta"] { display:none; } */
        </style>
        """,
        unsafe_allow_html=True,
    )

# 데이터수/이탈지수 카드
def kpi_card(label: str, value: str, delta_text: str, delta_is_good: bool):
    # delta_is_good=True면 초록(긍정), False면 빨강(부정)
    cls = "pos" if delta_is_good else "neg"

    st.markdown(
        f"""
        <div class="kpi">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          <div class="pill {cls}">{delta_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 클래스별 변화 카드
def class_mini_card(label, count, ratio, delta_p, delta_is_good: bool):
    # delta_p가 +면 좋다/나쁘다는 정책이 있을 텐데, 지금은 "증가=초록"으로 유지
    cls = "pos" if delta_is_good else "neg"
    icon = "▲" if delta_is_good else "▼"

    st.markdown(
        f"""
        <div class="mini">
          <div class="title">{label}</div>
          <div class="count">
            {count:,}건 <span class="ratio">({ratio:.1f}%)</span>
          </div>
          <div class="pill {cls}">{icon} {abs(delta_p):.1f}%p</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

