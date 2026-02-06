import json
import pandas as pd
import sqlite3
from src.data_collect import collect_reviews_by_date
from src.classification.classifier import infer_pipeline
from src.keyword.llm_keyword_async import extract_keywords
from src.risk_summary.summary_card_test1 import summary_card_pipeline
from datetime import datetime, timedelta
import asyncio
import argparse


# --- 1. 상수 선언 및 기타 함수 ---
APP_ID = "com.sampleapp"
TABLE = "data"
DATE_COL = "at"
TODAY = datetime(2026, 1, 31)

# 날짜 포멧
def _to_iso_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")

# 특정 기간 데이터 db에서 가져오기
def fetch_rows_between(conn, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    start_s = _to_iso_date(start_dt)
    end_s = _to_iso_date(end_dt)

    cursor = conn.execute(
        f"""
        SELECT *
        FROM {TABLE}
        WHERE date({DATE_COL}) BETWEEN date(?) AND date(?)
        """,
        (start_s, end_s),
    ) # (?) 자리에 각각 start_s, end_s 들어감
    cols = [d[0] for d in cursor.description] # cursor.description: ('컬럼명', 값들...) 이런 식으로 주는데 d[0]으로 컬럼명만 추출
    rows = cursor.fetchall()
    cursor.close()

    return pd.DataFrame(rows, columns=cols)


async def run_pipeline(conn, today, data_table:str="data", summary_table:str="summary", if_exists:str="append", chunksize:int=5000):
    # 날짜 계산
    start_date = today.replace(day=1) # 이번 달 1일로 변경
    end_date = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1) # 이번 달 말일

    prev_end_date = (start_date - timedelta(days=1)) # 지난 달 말일
    prev_start_date = prev_end_date.replace(day=1) # 지난 달 1일

    # 지난 달 데이터 수집(비교군)
    df_prev = fetch_rows_between(conn, prev_start_date, prev_end_date)
    # 이번 달 데이터 있는지 확인
    df_tmp = fetch_rows_between(conn, start_date, end_date)
    df_new = collect_reviews_by_date(APP_ID, start_date, end_date)
    # 이번 달 데이터 추가 수집 -> DB 적재
    if len(df_tmp) != len(df_new):
        flag = 0
        print(f"{len(df_new)}개 수집 완료. ({start_date.strftime('%Y-%m-%d')}~{end_date.strftime('%Y-%m-%d')})")
        
        # 이탈의도분류
        df_new = infer_pipeline(df_new, "model_out/bert-kor-base", text_col="content", batch=16)
        df_new0 = df_new[df_new['churn_intent_label'] == 0].copy()
        df_new1 = df_new[df_new['churn_intent_label'] == 1].copy()
        df_new2 = df_new[df_new['churn_intent_label'] == 2].copy()
        print(f"{len(df_new)}개 이탈의도 분류 완료. (확정:{len(df_new2)}개/불만:{len(df_new1)}개/없음:{len(df_new0)}개)")
        
        # 키워드도출
        df_new = await extract_keywords(df_new, text_col="content", batch=100)
        print(f"{len(df_new)}개 키워드 도출 완료.")

        df_new["keywords"] = df_new["keywords"].map(str)

        # 데이터 적재 (sqliteDB)
        try:
            df_new.to_sql(
                name=data_table,
                con=conn,
                if_exists=if_exists,
                index=False,
                chunksize=chunksize,
                method="multi",  # 여러 row를 한 번에 insert (빠름)
            )
            conn.commit()
            
            # 저장 확인
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {data_table}")
            total_rows = cur.fetchone()[0]

            cur.execute(f"PRAGMA table_info({data_table})")
            col_info = cur.fetchall()
            columns = [c[1] for c in col_info]

            cur.execute(f"SELECT * FROM {data_table} LIMIT 5")
            sample_rows = cur.fetchall()

            sample_df = pd.DataFrame(sample_rows, columns=columns)

            print(f"DB 적재 완료.")
            print("테이블:", data_table)
            print("이번에 저장한 행 수:", len(df_new))
            print("테이블 전체 행 수:", total_rows)
            print("컬럼:", columns)
            print("\n샘플 5행:")
            print(sample_df)
        finally:
            conn.close()

        # 요약 카드 생성
        summary = summary_card_pipeline(df_new, df_prev)
        print("요약 카드 생성 완료")
        print(summary)

    else:
        flag = 1
        print("이미 최신 데이터 입니다.")
        summary = summary_card_pipeline(df_new, df_prev)
        print("요약 카드 생성 완료")
        print(summary)

    return summary, flag

async def main():
    p = argparse.ArgumentParser(description="수집-분류-키워드도출-저장-요약 파이프라인")
    p.add_argument("--db-path", required=True, help="DB 저장 경로")

    args = p.parse_args()
    
    conn = sqlite3.connect(args.db_path)
    summary, flag = await run_pipeline(conn, TODAY)

if __name__ == "__main__":
    asyncio.run(main())