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

