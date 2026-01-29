from google_play_scraper import reviews, Sort
import pandas as pd
import time
from datetime import datetime
import argparse


COLUMNS = ['reviewId', 'userName', 'content', 'score', 'thumbsUpCount', 'at']

def list_to_df(all_reviews: list) -> pd.DataFrame:
    df = pd.DataFrame(all_reviews)

    # userName 결측치 처리
    df.loc[df['userName'].isna(), 'userName'] = "Google 사용자"
    # 리뷰텍스트 결측치 처리
    df = df.dropna(subset=['content'])
    
    return df[COLUMNS]

def collect_reviews_by_num(app_id, num: int=1000, lang="ko", country="kr", batch_size=200, sleep_sec=0.2):
    all_reviews = []
    continuation_token = None
    seen = set()
    collected = 0

    while True:
        result, continuation_token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=batch_size,
            continuation_token=continuation_token
        )

        if not result:
            break

        stop = False

        for r in result:
            # 중복 제거 (수집 중 리뷰가 추가되어 중복된 리뷰가 들어갈 수도 있음)
            rid = r.get("reviewId")
            if rid not in seen:
                seen.add(rid)
                all_reviews.append(r)
                collected += 1
            
            if collected >= num:
                stop = True
                break

        if stop:
            break

        if continuation_token is None:
            break

        time.sleep(sleep_sec)

    return list_to_df(all_reviews)


def collect_reviews_by_date(app_id, start_date, end_date=None, lang="ko", country="kr", batch_size=200, sleep_sec=0.2):
    all_reviews = []
    continuation_token = None
    seen = set()

    start_date = start_date.replace(tzinfo=None)
    if end_date:
        end_date = end_date.replace(tzinfo=None)

    while True:
        result, continuation_token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=batch_size,
            continuation_token=continuation_token
        )

        if not result:
            break

        stop = False

        for r in result:
            review_dt = r["at"].replace(tzinfo=None) # timezone 제거

            # end_date가 있으면 end_date 이후 리뷰는 제외
            if end_date and review_dt > end_date:
                continue

            # start_date보다 오래된 리뷰가 나오면 중단 조건
            if review_dt < start_date:
                stop = True
                break
            
            # 중복 제거 (수집 중 리뷰가 추가되어 중복된 리뷰가 들어갈 수도 있음)
            rid = r.get("reviewId")
            if rid not in seen:
                seen.add(rid)
                all_reviews.append(r)

        if stop:
            break

        if continuation_token is None:
            break

        time.sleep(sleep_sec)

    return list_to_df(all_reviews)


def main():
    p = argparse.ArgumentParser(description="구글플레이스토어 리뷰데이터 수집")
    p.add_argument("--app-id", type=str, default="com.sampleapp", help="앱 ID")
    p.add_argument("--mode", required=True, choices=["num", "date"], help="num/date")
    p.add_argument("--out", required=True, help="수집된 데이터 저장 경로")
    p.add_argument("--lang", default="ko", help="리뷰 언어 코드 (예: en, ja)")
    p.add_argument("--country", default="kr", help="국가 코드 (예: us, jp)")
    p.add_argument("--batch", type=int, default=200, help="한 번 요청할 때 가져올 리뷰 개수")
    p.add_argument("--sleep", type=float, default=0.2, help="요청 간 대기 시간(초)")
    # mode: num
    p.add_argument("--num", type=int, default=1000, help="수집할 개수")
    # mode: date
    p.add_argument("--start-date", type=str, default="2026-01-01", help="기간 시작일(YYYY-MM-DD)")
    p.add_argument("--end-date", type=str, default=None, help="기간 종료일(YYYY-MM-DD)") # 미입력시 최신까지
    args = p.parse_args()

    start_time = time.time()
    if args.mode == 'num':
        df = collect_reviews_by_num(args.app_id, args.num, args.lang, args.country, args.batch, args.sleep)
    elif args.mode == 'date':
        start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else None
        df = collect_reviews_by_date(args.app_id, start_dt, end_dt, args.lang, args.country, args.batch, args.sleep)
    df.to_csv(args.out, encoding='utf-8-sig', index=False)
    end_time = time.time()
    print(f"소요 시간: {time.strftime('%H:%M:%S', time.gmtime(end_time - start_time))}")
    print(f"총 {len(df)}개 수집 및 저장 완료: {args.out}")

if __name__ == "__main__":
    main()