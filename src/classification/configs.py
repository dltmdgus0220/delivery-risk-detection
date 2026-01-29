import torch


MODEL_ID = ["klue/bert-base", "kykim/bert-kor-base", "kykim/albert-kor-base", "kykim/funnel-kor-base", "kykim/electra-kor-base"] # 참고:https://github.com/kiyoungkim1/LMkor
MAX_LEN = 128
DEVICE = "cuda" if torch.cuda.is_available() else "cpu" # gpu를 위한 코드
EPS = 1e-6

id2label = {0: "없음", 1: "불만", 2: "확정"}
