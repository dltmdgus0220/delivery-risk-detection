import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit as st

from src.dashboard.util import keyword_count, target_keyword_ratio, top_n_keywords_extract, parse_keywords, fetch_month_df, set_korean_font


# --- 유틸 ---
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

    st.markdown(
        f"""
        <div class="mini">
          <div class="title">{label}</div>
          <div class="count">
            {count:,}건 <span class="ratio">({ratio:.1f}%)</span>
          </div>
          <div class="pill {cls}"> {(delta_p):.1f}%p</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# TopN 키워드 막대그래프 시각화
def render_top_keywords_bar_plotly(df, title: str, top_n=5):
    counter = keyword_count(df)
    top_keywords = top_n_keywords_extract(counter, n=top_n)

    if not top_keywords:
        st.info("표시할 키워드가 없습니다.")
        return None

    chart_df = pd.DataFrame(top_keywords, columns=["keyword", "count"]).sort_values("count")

    fig = px.bar(
        chart_df,
        x="count",
        y="keyword",
        orientation="h",
        title=title,
    )

    # 타이틀
    fig.update_layout(
    title=dict(
        text=title,
        x=0.5, # 중앙 정렬
        xanchor="center",
        font=dict(size=20, family="Arial", color="black"),
    ),
    margin=dict(l=10, r=10, t=50, b=10),
    )

    # 축 이름설정
    fig.update_xaxes(title="빈도 수")
    fig.update_yaxes(title=None)

    # 막대 데이터 표시
    fig.update_traces(
        text=chart_df["count"],
        textposition="outside",
    )

    fig.update_layout(clickmode="event+select")
    selected = st.plotly_chart(
        fig,
        use_container_width=True,
        key="top_keyword_bar",
        on_select="rerun",
    )

    if selected['selection']['points'] != []:
        return top_keywords, selected['selection']['points'][0]['y']  # 클릭한 키워드

    return top_keywords, None

# 타겟 키워드의 클래스별 비중 비교 시각화
def render_keyword_ratio_compare_bar(
    target: str,
    df_cur_confirmed: pd.DataFrame,
    df_cur_complaint: pd.DataFrame,
    df_prev_confirmed: pd.DataFrame,
    df_prev_complaint: pd.DataFrame,
    cur_label: str = "기준달",
    prev_label: str = "전월",
):
    cur_conf_c = keyword_count(df_cur_confirmed)
    cur_comp_c = keyword_count(df_cur_complaint)
    prev_conf_c = keyword_count(df_prev_confirmed)
    prev_comp_c = keyword_count(df_prev_complaint)

    cur_conf_cnt, cur_conf_ratio = target_keyword_ratio(cur_conf_c, target)
    cur_comp_cnt, cur_comp_ratio = target_keyword_ratio(cur_comp_c, target)
    prev_conf_cnt, prev_conf_ratio = target_keyword_ratio(prev_conf_c, target)
    prev_comp_cnt, prev_comp_ratio = target_keyword_ratio(prev_comp_c, target)

    rows = [
        {"month": cur_label,  "class": "확정", "ratio": cur_conf_ratio, "count": cur_conf_cnt},
        {"month": cur_label,  "class": "불만", "ratio": cur_comp_ratio, "count": cur_comp_cnt},
        {"month": prev_label, "class": "확정", "ratio": prev_conf_ratio, "count": prev_conf_cnt},
        {"month": prev_label, "class": "불만", "ratio": prev_comp_ratio, "count": prev_comp_cnt},
    ]
    plot_df = pd.DataFrame(rows)
    plot_df["label"] = plot_df.apply(lambda r: f"{r['ratio']:.2f}%<br>({r['count']}건)", axis=1)

    max_y = float(plot_df["ratio"].max() if len(plot_df) else 0)
    y_pad = max(1.0, max_y * 0.20) # 위 텍스트 공간

    fig = px.bar(
        plot_df,
        x="class",
        y="ratio",
        color="month",
        barmode="group",
        text="label",
    )

    fig.update_layout(
        height=380, # 왼쪽과 높이 맞춰서 “한 덩어리”로 보이게
        margin=dict(l=10, r=10, t=10, b=10),
        legend_title_text="",
    )

    fig.update_yaxes(
        title="비율(%)",
        range=[0, max_y + y_pad], # 위 여유
        fixedrange=True,
        showgrid=False,
    )
    fig.update_xaxes(title=None, fixedrange=True)

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
    )

    st.plotly_chart(fig, use_container_width=True)

# summary 컬럼 추출 (str -> dict)
def _as_dict(x):
    """dict 또는 JSON string을 dict로 변환. 실패하면 빈 dict."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return {}
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}
    return {}

# reason_id 컬럼 추출 (str -> list)
def _as_id_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return []
        # JSON list 형태면 파싱 시도
        if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
            try:
                v = json.loads(s)
                if isinstance(v, list):
                    return v
                if isinstance(v, dict) and "reason_id" in v:
                    return _as_id_list(v["reason_id"])
            except Exception:
                pass
    return [x]

# summary
def render_summary_section(title: str, summary_obj):
    d = _as_dict(summary_obj)

    situations = d.get("situations", "")
    evaluations = d.get("evaluations", "")
    solutions = d.get("solutions", "")

    st.markdown(f"**[{title}]**")

    # 보기 좋게 bullet + 본문 분리
    st.markdown("- **문제 상황**")
    st.write(situations if situations else "요약 내용이 없습니다.")

    st.markdown("- **기존 대응에 대한 평가**")
    st.write(evaluations if evaluations else "요약 내용이 없습니다.")

    st.markdown("- **소비자들이 원하는 대응**")
    st.write(solutions if solutions else "요약 내용이 없습니다.")


def render_sidebar(today: datetime):
    with st.sidebar:    
        st.markdown("### 📅 월 선택")

        # 기준: 지난달
        y, m = today.year, today.month - 1
        if m == 0:
            y -= 1
            m = 12

        # 최근 24개월 생성 (기준달부터)
        months = []

        for _ in range(24):
            months.append(f"{y:04d}-{m:02d}")
            m -= 1
            if m == 0:
                y -= 1
                m = 12

        selected_month = st.selectbox(
            "분석 기준 월",
            options=months,
            index=0, # 항상 지난달이 첫 번째
        )

    return {
        "yyyymm": selected_month,
        "year": int(selected_month.split("-")[0]),
        "month": int(selected_month.split("-")[1]),
    }


def render(cfg: dict, today):
    set_korean_font()
    inject_css()
    db_path = st.session_state.get("db_path")

    # 기준 월
    cur_dt = datetime.strptime(cfg["yyyymm"], "%Y-%m")
    prev_dt = cur_dt - relativedelta(months=1)

    cur_yyyymm = cur_dt.strftime("%Y-%m")
    prev_yyyymm = prev_dt.strftime("%Y-%m")

    # 데이터로드
    df_cur = fetch_month_df(db_path, "data", cur_yyyymm)
    df_cur["keywords"] = df_cur["keywords"].apply(parse_keywords)
    df_prev = fetch_month_df(db_path, "data", prev_yyyymm)
    df_prev["keywords"] = df_prev["keywords"].apply(parse_keywords)
    df_cur_summary = fetch_month_df(db_path, "summary", cur_yyyymm)
    df_prev_summary = fetch_month_df(db_path, "summary", prev_yyyymm)

    # 데이터분리
    df_cur_confirmed = df_cur[df_cur['churn_intent_label'] == 2].copy()
    df_cur_complaint = df_cur[df_cur['churn_intent_label'] == 1].copy()
    df_cur_positive = df_cur[df_cur['churn_intent_label'] == 0].copy()
    df_prev_confirmed = df_prev[df_prev['churn_intent_label'] == 2].copy()
    df_prev_complaint = df_prev[df_prev['churn_intent_label'] == 1].copy()
    df_prev_positive = df_prev[df_prev['churn_intent_label'] == 0].copy()

    # 클래스 비율 계산
    ratio_cur_confirmed = round(len(df_cur_confirmed)/len(df_cur)*100, 1)
    ratio_cur_complaint = round(len(df_cur_complaint)/len(df_cur)*100, 1)
    ratio_cur_positive = round(len(df_cur_positive)/len(df_cur)*100, 1)
    ratio_prev_confirmed = round(len(df_prev_confirmed)/len(df_prev)*100, 1)
    ratio_prev_complaint = round(len(df_prev_complaint)/len(df_prev)*100, 1)
    ratio_prev_positive = round(len(df_prev_positive)/len(df_prev)*100, 1)

    st.caption(
        f"※ 모든 증감 수치는 지난달({prev_dt.year % 100:02d}년 {prev_dt.month:02d}월) 대비 기준입니다."
    )

    year, month = cfg["year"], cfg["month"]

    st.markdown("## 📊 분석 요약")
    st.markdown(f"### {year % 100:02d}년 {month:02d}월 데이터 요약")

    st.divider()

    # 1행 (집계요약, 키워드분석)
    left, right = st.columns([1, 1.8])

    # -------- 집계 요약 --------
    with left:
        st.markdown("#### 📌 수집 현황")

        delta_cnt = len(df_cur) - len(df_prev)
        kpi_left, kpi_right = st.columns(2)

        with kpi_left:
            kpi_card(
                label="데이터 수",
                value=f"{len(df_cur):,}건",
                delta_text=f"{delta_cnt:+,}건",
                delta_is_good=(delta_cnt >= 0),
            )

        with kpi_right:
            churn_value = df_cur_summary.iloc[0]['risk_score']
            churn_delta = churn_value - df_prev_summary.iloc[0]['risk_score']
            kpi_card(
                label="이탈지수",
                value=f"{churn_value:.2f}",
                delta_text=f"{churn_delta:+.2f}",
                delta_is_good=(churn_delta < 0),
            )

        st.divider()

        st.markdown("##### 클래스별 변화")
        r1, r2, r3 = st.columns(3)

        with r1:
            delta_p = round(ratio_cur_confirmed - ratio_prev_confirmed, 1)
            class_mini_card("'확정'", len(df_cur_confirmed), ratio_cur_confirmed, delta_p, (delta_p < 0))

        with r2:
            delta_p = round(ratio_cur_complaint - ratio_prev_complaint, 1)
            class_mini_card("불만", len(df_cur_complaint), ratio_cur_complaint, delta_p, (delta_p < 0))

        with r3:
            delta_p = round(ratio_cur_positive - ratio_prev_positive, 1)
            class_mini_card("없음", len(df_cur_positive), ratio_cur_positive, delta_p, (delta_p > 0))


    # -------- 키워드 분석 --------
    with right:
        st.markdown("#### 🔑 키워드 분석")

        kw_left, kw_right = st.columns([1.5, 1])

        with kw_left:
            topn, select = render_top_keywords_bar_plotly(
                df=df_cur_confirmed,
                title="'확정' Top5 키워드",
                top_n=5,
            )

        with kw_right:
            if select is None:
                st.markdown(
                    f"""
                    <h5 style="text-align:center; margin-top:0.5rem;">
                        키워드를 선택하면 클래스별 비중을 표시합니다
                    </h5>
                    """,
                    unsafe_allow_html=True,
                )
                st.info("왼쪽 막대를 클릭하세요.", icon="👈")
            else:
                st.markdown(
                    f"""
                    <h5 style="text-align:center; margin-top:0.5rem;">
                        '{select}' 클래스별 비중 비교
                    </h5>
                    """,
                    unsafe_allow_html=True,
                )
                
                render_keyword_ratio_compare_bar(
                    target=select,
                    df_cur_confirmed=df_cur_confirmed,
                    df_cur_complaint=df_cur_complaint,
                    df_prev_confirmed=df_prev_confirmed,
                    df_prev_complaint=df_prev_complaint,
                    cur_label=cur_yyyymm, # 예: "2026-01"
                    prev_label=prev_yyyymm, # 예: "2025-12"
                )

    st.divider()

    # 2행 (요약, 드릴다운)
    bottom_left, bottom_right = st.columns([1, 1.7])

    # -------- 요약 & 대응 --------
    with bottom_left:
        st.markdown(f"#### 🧠 '{topn[0][0]}' 중심 요약")

        # ✅ 확정/불만/둘다 선택
        view_mode = st.radio(
            "표시할 요약 선택",
            options=["확정", "불만"],
            horizontal=True,
            label_visibility="collapsed",
            key="summary_view_mode",
        )

        if df_cur_summary is None or df_cur_summary.empty:
            st.info("요약 데이터가 없습니다.")
        else:
            row0 = df_cur_summary.iloc[0]

            confirmed_obj = row0.get("summary_confirmed", None)
            complaint_obj = row0.get("summary_complaint", None)

            if view_mode in ["확정"]:
                render_summary_section("'확정' 리뷰 분석", confirmed_obj)

            elif view_mode in ["불만"]:
                render_summary_section("'불만' 리뷰 분석", complaint_obj)

        st.markdown("#### 🛠 추천 대응")

        st.success(
            "• 배송 SLA 점검\n"
            "• 특정 지역 지연 원인 분석\n"
            "• 고객 커뮤니케이션 강화"
        )

    # -------- 드릴다운 --------
    with bottom_right:
        st.markdown(f"#### 🔍 '{topn[0][0]}' 드릴다운")

        if df_cur_summary is None or df_cur_summary.empty:
            st.info("요약 데이터가 없어 근거 리뷰를 찾을 수 없습니다.", icon="🧩")
        else:
            row0 = df_cur_summary.iloc[0]

            # summary 객체에서 reason_id 모으기
            reason_ids = []

            if view_mode in ["확정"]:
                conf_obj = _as_dict(row0.get("summary_confirmed", None))
                reason_ids += _as_id_list(conf_obj.get("reason_id", None))

            elif view_mode in ["불만"]:
                comp_obj = _as_dict(row0.get("summary_complaint", None))
                reason_ids += _as_id_list(comp_obj.get("reason_id", None))

            # 중복 제거(순서 유지)
            seen = set()
            reason_ids = [x for x in reason_ids if not (str(x) in seen or seen.add(str(x)))]

            if not reason_ids:
                st.info("선택된 요약에 근거 리뷰 ID(reason_id)가 없습니다.", icon="🧩")
            else:
                # df_cur에서 id/날짜/라벨/텍스트 컬럼 자동 탐색
                id_col = "reviewId"
                at_col = "at"
                label_col = "churn_intent"
                text_col = "content"

            if id_col is None:
                st.error("df_cur에서 리뷰 id 컬럼을 찾지 못했습니다. (예: id/review_id)")
            else:
                # 타입 맞추기: reason_ids가 문자열일 수도 있어서 문자열 비교로 통일
                df_tmp = df_cur.copy()
                df_tmp["_id_str"] = df_tmp[id_col].astype(str)
                id_set = set(str(x) for x in reason_ids)

                df_drill = df_tmp[df_tmp["_id_str"].isin(id_set)].copy()

                if df_drill.empty:
                    st.warning("reason_id로 매칭되는 리뷰를 df_cur에서 찾지 못했습니다.")
                else:
                    # 보기용 컬럼 구성
                    out = pd.DataFrame()
                    out["날짜"] = df_drill[at_col].astype(str) if at_col else ""
                    out["클래스"] = df_drill[label_col].astype(str) if label_col else ""
                    out["리뷰"] = df_drill[text_col].astype(str) if text_col else ""

                    # 날짜 컬럼이 있으면 정렬
                    if at_col:
                        try:
                            df_drill["_at_dt"] = pd.to_datetime(df_drill[at_col])
                            out = out.loc[df_drill.sort_values("_at_dt", ascending=False).index]
                        except Exception:
                            pass

                    st.caption(f"근거 리뷰 {len(out)}건 (reason_id 기준)")
                    st.dataframe(out, use_container_width=True, hide_index=True)

    
