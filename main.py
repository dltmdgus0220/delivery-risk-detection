from src.data_collect import data_collect
from src.classification_bert import classification_bert
from src.mixed_text_split import mixed_text_split
from src.dashboard import dashboard

PERIOD = 7 # 일정 주기마다 데이터 수집을 위한 상수


if __name__ == "__main__":
    df = data_collect() # 데이터수집
    df_class = classification_bert(df, flag=False) # 클래스 분류
    df_split = mixed_text_split(df_class) # 혼합문장분리
    df_split_class = classification_bert(df_split, flag=True) # 클래스 재분류, flag=True: 클래스 없는 애들만 봐라 이런느낌으로 사용할 예정
    dashboard(df_split_class) # 아마 대시보드를 바로 띄워주는 느낌으로?


