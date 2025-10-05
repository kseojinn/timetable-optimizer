# Timetable Optimizer

시뮬레이티드 어닐링을 활용한 **자동 시간표 생성 시스템**

**Automatic Timetable Generation System using Simulated Annealing**

## 프로젝트 소개

대학생들이 매 학기 겪는 복잡한 시간표 작성 문제를 **인공지능 최적화 알고리즘**으로 해결합니다.

### 핵심 가치
- **시간 절약**: 수동 시간표 작성 시간을 95% 단축
- **최적화**: 개인 선호도를 반영한 맞춤형 시간표
- **공강일 최대화**: 학교 가지 않는 날을 최대한 확보
- **제약조건 만족**: 졸업요건, 선수과목 등 자동 확인

## 주요 기능

### **스마트 최적화**
- **시뮬레이티드 어닐링** 알고리즘으로 최적해 탐색
- **다중 제약조건** 동시 처리 (시간충돌, 선수과목, 교양영역 등)
- **개인 선호도** 반영 (선호 시간대, 교수, 연강 기피 등)

### **공강일 최대화**
- 수업을 최소한의 요일에 집중 배치
- **화/목 공강** 또는 **월/수/금 집중** 패턴 자동 생성
- 학점은 유지하면서 자유시간 극대화

### **졸업요건 관리**
- 필수과목 자동 우선 선택
- 교양영역별 이수 요구사항 확인
- 선수과목 관계 자동 검증

### **결과 분석**
- 최적화 과정 시각화 (matplotlib)
- 상세한 비용 분석 및 제약조건 만족도
- 여러 실행 결과 비교 가능

## 시스템 아키텍처

```
timetable-optimizer/
├── main.py                    # 메인 실행 파일
├── time_parser.py             # 시간표 파싱 모듈
├── cost_function.py           # 비용 함수 모듈  
├── simulated_annealing.py     # SA 알고리즘 모듈
├── requirements.txt           # 의존성 관리
├── README.md                  # 프로젝트 문서
├── data/
│   ├── courses.json          # 전체 과목 데이터
│   └── user_profile.json     # 사용자 설정
└── results/
    ├── timetable_2025-01-15_14-30-25.json
    ├── log_2025-01-15_14-30-25.txt
    ├── latest_timetable.json
    └── latest_log.txt
```

## 설치 방법

### 요구사항
- Python 3.8 이상

### 클론 및 설치

```bash
# 1. 저장소 클론
git clone https://github.com/kseojinn/timetable-optimizer.git
cd timetable-optimizer

# 2. 가상환경 생성 (권장)
python -m venv timetable_env

# 3. 가상환경 활성화
# Windows:
timetable_env\Scripts\activate
# macOS/Linux:
source timetable_env/bin/activate

# 4. 의존성 설치
pip install -r requirements.txt

# 5. 데이터 폴더 생성
mkdir data results
```

## 사용 방법

### 빠른 시작

```bash
# 기본 실행
python main.py
```

### 설정 파일 준비

**1. data/courses.json** - 과목 데이터
```json
{
  "courses": [
    {
      "course_code": "",
      "section": "", 
      "course_name": "데이터베이스",
      "credits": 3,
      "professor": "",
      "schedule": "",
      "classroom": "",
      "category": "",
      "area": "",
      "year_level": 2
    }
  ]
}
```

**2. data/user_profile.json** - 개인 설정
```json
{
  "name": "",
  "current_year": 3,
  "target_credits_this_semester": 18,
  "required_courses": [],
  "preferences": {
    "preferred_times": [],
    "lunch_time_required": true,
    "max_consecutive_classes": 3
  }
}
```

## 설정 가이드

### 개인 맞춤 설정

**공강일을 매우 중요하게 생각한다면:**
```json
"cost_function_weights": {
  "free_days_bonus": 200  // 기본값 100 → 200
}
```

**연강을 정말 싫어한다면:**
```json
"cost_function_weights": {
  "consecutive_classes": 150  // 기본값 50 → 150
}
```

**점심시간이 매우 중요하다면:**
```json
"cost_function_weights": {
  "lunch_time_violation": 200  // 기본값 80 → 200
}
```

### 알고리즘 파라미터

```python
# main.py에서 조정 가능
sa_optimizer.initial_temperature = 1000.0  # 초기 온도
sa_optimizer.cooling_rate = 0.95           # 냉각률
sa_optimizer.max_iterations = 1000         # 최대 반복
```
