import pandas as pd
from google import genai
from typing import Tuple, List, Optional
import argparse
import time
import re
from collections import Counter
import os


EXCEPT_KEYWORD = ['앱-삭제', '앱-탈퇴']

# --- 1. 기타 함수 ---

def str_to_list_keyword(keywords: str) -> List[str]:
    keywords = keywords.strip('[]')
    if len(keywords) == 0:
        return []
    else:
        return [x.strip() for x in keywords.replace("'", "").split(",")]

def clean_one_line(s:str) -> str:
    s = (s or "").strip() # 양쪽 공백 제거
    s = s.strip().strip('"').strip("'").strip() # 양쪽 따옴표 제거
    s = s.replace("\n", " ").replace("\r", " ") # 줄바꿈->공백 변환. 한줄로 결과 바꾸기
    s = re.sub(r"\s+", " ", s).strip() # 연속되는 여러 개의 공백 변환
    s = re.sub(r"^[\-\*\d\.\)\s]+", "", s).strip() # 불릿/번호 형태 제거
    return s

