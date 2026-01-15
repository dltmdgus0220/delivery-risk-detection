from data_collect import data_collect
from src.classification_bert import classification_bert
from src.dashboard import dashboard

PERIOD = 7 # 일정 주기마다 데이터 수집을 위한 상수


if __name__ == "__main__":
    df = data_collect() # 데이터수집
    


