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
