from google_play_scraper import reviews, Sort
import time
import pandas as pd

# --- 0. 상수선언 ---

PACKAGE_LIST = ['com.sampleapp','com.coupang.mobile.eats','com.fineapp.yogiyo','com.shinhan.o2o'] # 배민, 쿠팡이츠, 요기요, 땡겨요
PACKAGE_NAME_KOR = ['배달의민족', '쿠팡이츠', '요기요', '땡겨요']
PACKAGE_NAME_ENG = ['baemin', 'coupangeats', 'yogiyo', 'ddangyo']
PACKAGE_NUM = 3
NUM_DATA = 7000

APP_ID = PACKAGE_LIST[PACKAGE_NUM]
APP_NAME_KOR = PACKAGE_NAME_KOR[PACKAGE_NUM]
APP_NAME_ENG = PACKAGE_NAME_ENG[PACKAGE_NUM]

