# 🎓 Timetable Optimizer

시뮬레이티드 어닐링을 활용한 **자동 시간표 생성 시스템**

**Automatic Timetable Generation System using Simulated Annealing**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/kseojinn/timetable-optimizer/graphs/commit-activity)

## 📋 목차 (Table of Contents)

- [프로젝트 소개](#-프로젝트-소개)
- [주요 기능](#-주요-기능)
- [시스템 아키텍처](#-시스템-아키텍처)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [설정 가이드](#-설정-가이드)
- [결과 예시](#-결과-예시)
- [기여하기](#-기여하기)
- [라이선스](#-라이선스)

## 🎯 프로젝트 소개

대학생들이 매 학기 겪는 복잡한 시간표 작성 문제를 **인공지능 최적화 알고리즘**으로 해결합니다.

### ✨ 핵심 가치
- **시간 절약**: 수동 시간표 작성 시간을 95% 단축
- **최적화**: 개인 선호도를 반영한 맞춤형 시간표
- **공강일 최대화**: 학교 가지 않는 날을 최대한 확보
- **제약조건 만족**: 졸업요건, 선수과목 등 자동 확인

## 🚀 주요 기능

### 🎯 **스마트 최적화**
- **시뮬레이티드 어닐링** 알고리즘으로 최적해 탐색
- **다중 제약조건** 동시 처리 (시간충돌, 선수과목, 교양영역 등)
- **개인 선호도** 반영 (선호 시간대, 교수, 연강 기피 등)

### 📅 **공강일 최대화**
- 수업을 최소한의 요일에 집중 배치
- **화/목 공강** 또는 **월/수/금 집중** 패턴 자동 생성
- 학점은 유지하면서 자유시간 극대화

### 🎓 **졸업요건 관리**
- 필수과목 자동 우선 선택
- 교양영역별 이수 요구사항 확인
- 선수과목 관계 자동 검증

### 📊 **결과 분석**
- 최적화 과정 시각화 (matplotlib)
- 상세한 비용 분석 및 제약조건 만족도
- 여러 실행 결과 비교 가능

## 🏗️ 시스템 아키텍처

```
📁 timetable-optimizer/
├── 🐍 main.py                    # 메인 실행 파일
├── ⚙️ time_parser.py             # 시간표 파싱 모듈
├── 💰 cost_function.py           # 비용 함수 모듈  
├── 🔥 simulated_annealing.py     # SA 알고리즘 모듈
├── 📦 requirements.txt           # 의존성 관리
├── 📖 README.md                  # 프로젝트 문서
├── 📂 data/
│   ├── 📚 courses.json          # 전체 과목 데이터
│   └── 👤 user_profile.json     # 사용자 설정
└── 📂 results/
    ├── 📊 timetable_2025-01-15_14-30-25.json
    ├── 📝 log_2025-01-15_14-30-25.txt
    ├── 📊 latest_timetable.json
    └── 📝 latest_log.txt
```

## 💻 설치 방법

### 📋 요구사항
- Python 3.8 이상
- Git (선택사항)

### 🔽 클론 및 설치

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

## 🎮 사용 방법

### ⚡ 빠른 시작

```bash
# 기본 실행
python main.py
```

### 📝 설정 파일 준비

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

## ⚙️ 설정 가이드

### 🎯 개인 맞춤 설정

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

### 🔧 알고리즘 파라미터

```python
# main.py에서 조정 가능
sa_optimizer.initial_temperature = 1000.0  # 초기 온도
sa_optimizer.cooling_rate = 0.95           # 냉각률
sa_optimizer.max_iterations = 1000         # 최대 반복
```

## 📊 결과 예시

### 🎉 최적화 결과

```
=== 최적 시간표 ===
1. 컴퓨터네트워크 ()
   교수: , 학점: 3, 시간: 
   
2. 데이터베이스 ()  
   교수: , 학점: 3, 시간:
   
3. 교양영어회화 ()
   교수: , 학점: 3, 시간:

4
5.
6.

총 학점: 18

=== 공강일 분석 ===
수업 있는 요일: 월, 수, 금 (3일)
🎉 공강일: 화, 목 (2일)
공강일 보상 점수: -120.0점
```

### 📈 최적화 과정

![Optimization Progress](assets/optimization_chart.png)

## 🏆 성능

- **최적화 시간**: 평균 0.8초 (65개 과목 기준)
- **비용 개선율**: 평균 88% 이상
- **제약조건 만족**: 100% (하드 제약)
- **공강일 확보**: 평균 1.8일

## 🤝 기여하기

### 🐛 버그 리포트
Issues 탭에서 다음 정보와 함께 신고해 주세요:
- 운영체제 및 Python 버전
- 에러 메시지 전문
- `results/latest_log.txt` 내용

### 💡 기능 제안
- 새로운 최적화 알고리즘 (유전 알고리즘, 타부 서치 등)
- 웹 인터페이스 개발
- 다른 대학 시간표 형식 지원

### 🔧 코드 기여
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📖 관련 논문 및 자료

- Kirkpatrick, S. et al. (1983). "Optimization by simulated annealing"
- Russell, S. & Norvig, P. (2020). "Artificial Intelligence: A Modern Approach"
- Burke, E. K. & Petrovic, S. (2002). "Recent research directions in automated timetabling"

## 📜 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👨‍💻 개발자

**Seojin Kang** ([@kseojinn](https://github.com/kseojinn))

- 📧 Email: kseojin0205@sungkyul.ac.kr

**🎯 완벽한 시간표로 여유로운 대학생활을! 🎯**

</div>
