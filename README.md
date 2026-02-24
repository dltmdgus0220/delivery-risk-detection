# 🛵 배달앱 리뷰 분석을 통한 이탈 리스크 감지 시스템
## “배달의민족” 고객 이탈 방지를 위한 리뷰 분석 프로젝트

## 1. 프로젝트 개요

본 프로젝트는 배달앱 리뷰 데이터 분석을 통해 고객의 이탈 위험 요인을 분석하고, 사전 예측하여 대비하기 위한 **이탈 리스크 감지 시스템**입니다.

관리자가 이탈 리스크를 빠르게 인지하고, 문제 원인에 따른 즉각적인 대응이 가능하도록 지원하는 것을 목표로 합니다.



## 2. 주요 기능
### 2.1 이탈 의도 분류 자동화 (Churn Intent Classification)
* 리뷰 텍스트를 기반으로 고객의 이탈 의도를 자동 분류
* 사전 정의한 3가지 클래스 체계 적용
    * 확정: 명시적인 이탈, 해지, 삭제, 타서비스 권유 및 전환 표현
    * 불만: 불편, 불만, 비판, 개선 요구 중 하나라도 포함된 경우
    * 없음: 순수 긍정 및 만족 표현만 있는 경우
* LLM 기반 라벨링 및 학습 모델을 활용하여 대량 리뷰 자동 처리
* 신규 리뷰 유입 시 자동 분류 가능
  
👉 관리자는 이탈 가능성이 높은 리뷰를 즉시 파악 가능

### 2.2 이탈 지수(KPI) 설계

* 가중치 + Smoothing(K값) 기반 리스크 지표 설계
* 클래스별 가중치 부여
    * 확정, 불만, 없음 각 클래스에 차등 가중치 적용
    * 소비자 거래지수와의 상관관계 분석을 기반으로 가중치 도출
* 리뷰 수가 적은 경우 과도한 변동을 방지하기 위한 K값 기반 스무딩(Smoothing) 적용

👉 단기 노이즈에 흔들리지 않는 안정적인 위험도 지표 제공

### 2.3 키워드 기반 원인 분석

* 이탈/불만 리뷰에서 핵심 키워드를 자동 추출하여 문제의 구체적 원인 카테고리화
* LLM 기반 키워드 도출
* ASPECT, STATUS, SERVICE 사전을 정의하여 "대상-상태", "고유서비스-상태" 형태로 키워드 도출

👉 이탈 원인을 키워드 단위로 도출하여 설명 가능한 분석 제공

### 2.4 타겟 키워드 기반 리뷰 요약 제공

* 가장 많이 등장한 키워드를 **타겟 키워드(Target Keyword)**로 정의
* 해당 키워드를 포함한 리뷰만 필터링
* LLM을 활용하여 핵심 불만 요약 생성
    * 문제상황: 고객이 겪은 구체적인 불편함
    * 기존 대응 평가: 문제 발생 시 기존 대응 방식에 대한 고객의 부정적/긍정적 평가
    * 원하는 대응 방향: 소비자가 기대하는 이상적인 해결책 및 개선 요구 사항

👉 관리자는 여러개 리뷰를 직접 읽지 않아도 핵심 이슈를 한눈에 파악 가능

## 3. 기술 스택



## 4. 데이터




## 5. 설치 및 실행
### 5.1. 환경 설정

1.  **Python 설치:** Python 3.8 이상 버전이 설치되어 있어야 합니다.
2.  **가상 환경 생성 및 활성화 (권장):**
    해당 프로젝트는 conda 가상환경을 사용했습니다.
    ### Windows
    ```bash
    conda create -n env01 python=3.10
    conda activate env01
    ```

3.  **의존성 설치:** `requirements.txt`에 명시된 라이브러리를 설치합니다.
    ```bash
    pip install -r requirements.txt
    ```

### 5.2. 실행
root 디렉토리에서 실행
```bash
streamlit run app.py
```


## 6. 프로젝트 구조

```
.
├── .gitignore
├── README.md                  
├── requirements.txt # Python 의존성 목록
├── data/ # 원시/결과 데이터 저장 경로
├── model_out/ # 학습된 모델 가중치 저장 경로
└── src/
    ├── app.py # 대시보드
    ├── data_collect.py # 데이터수집
    ├── classification/
    |   ├── classifier.py # 이탈의도분류
    |   ├── configs.py
    |   ├── datasets.py
    |   ├── trainer.py
    |   └── utils.py
    ├── dashboard/
    |   ├── pipeline.py 
    |   ├── util.py
    |   └── page/
    |       ├── home.py
    |       └── analysis.py   
    ├── keyword/
    |   ├── llm_keyword_async.py # 비동기식 키워드도출
    |   ├── llm_keyword.py # 동기식 키워드도출
    |   └── 기타파일들
    ├── labeling/
    |   ├── llm_churn_intent_labeling_async.py # 비동기식 이탈의도라벨링
    |   ├── llm_churn_intent_labeling.py # 동기식 이탈의도라벨링
    |   └── eval_labeling.py
    └── risk_summary/
        ├── llm_summary_reviews.py
        └── risk_score_calc.py


```

## 7. 평가

## 기타. 일정관리
https://www.notion.so/2d8864f0902080f79836f0036fddc088

