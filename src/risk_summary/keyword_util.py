import pandas as pd
from collections import Counter
from typing import List, Tuple


EXCLUDE = ['앱-삭제', '앱-탈퇴']
KEYWORD_COL = "keywords"

# 키워드 카운팅
def keyword_count(df:pd.DataFrame) -> Counter:
    all_reviews = [k for ks in df[KEYWORD_COL] for k in ks]
    counter = Counter(all_reviews)
    
    return counter

