#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시뮬레이티드 어닐링을 이용한 자동 시간표 생성 시스템
"""

import json
import matplotlib.pyplot as plt
import numpy as np

# 앞서 구현한 클래스들을 import
from time_parser import TimeTableParser
from cost_function import TimetableCostFunction  
from simulated_annealing import TimetableSimulatedAnnealing

def load_data():
    """JSON 파일에서 데이터 로드"""
    try:
        # 과목 데이터 로드
        with open('data/courses.json', 'r', encoding='utf-8') as f:
            course_database = json.load(f)
        
        # 사용자 프로필 로드
        with open('data/user_profile.json', 'r', encoding='utf-8') as f:
            user_profile = json.load(f)
        
        return course_database, user_profile
    
    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
        print("data/ 폴더에 courses.json과 user_profile.json 파일이 있는지 확인해주세요.")
        return None, None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파일 형식 오류: {e}")
        return None, None

def plot_optimization_progress(cost_history, temperature_history):
    """최적화 과정 시각화"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # 비용 변화
    ax1.plot(cost_history, 'b-', alpha=0.7)
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Cost')
    ax1.set_title('Simulated Annealing Cost Progress')
    ax1.grid(True, alpha=0.3)
    
    # 온도 변화
    ax2.plot(temperature_history, 'r-', alpha=0.7)
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Temperature')
    ax2.set_title('Temperature Schedule')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def compare_algorithms():
    """다른 최적화 알고리즘과 성능 비교 (미래 확장)"""
    # TODO: 유전 알고리즘, 타부 서치 등과 비교
    pass

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("시뮬레이티드 어닐링 기반 자동 시간표 생성 시스템")
    print("=" * 60)
    
    # 1. 데이터 로드
    print("\n1. 데이터 로딩...")
    course_db, user_profile = load_data()
    
    if course_db is None or user_profile is None:
        print("❌ 데이터 로딩 실패. 프로그램을 종료합니다.")
        return
    
    print(f"✅ 과목 데이터: {len(course_db['courses'])}개 과목 로드됨")
    print(f"✅ 사용자: {user_profile['name']} ({user_profile['current_year']}학년)")
    print(f"✅ 원하는 과목: {len(user_profile['wanted_courses'])}개")
    
    # 2. 시스템 초기화
    print("\n2. 시스템 초기화...")
    time_parser = TimeTableParser()
    cost_function = TimetableCostFunction(user_profile, course_db, time_parser)
    sa_optimizer = TimetableSimulatedAnnealing(user_profile, course_db, time_parser, cost_function)
    
    # SA 파라미터 설정
    sa_optimizer.initial_temperature = 1000.0
    sa_optimizer.final_temperature = 1.0
    sa_optimizer.cooling_rate = 0.95
    sa_optimizer.max_iterations = 1000
    
    print("시뮬레이티드 어닐링 파라미터:")
    print(f"  - 초기 온도: {sa_optimizer.initial_temperature}")
    print(f"  - 최종 온도: {sa_optimizer.final_temperature}")
    print(f"  - 냉각률: {sa_optimizer.cooling_rate}")
    print(f"  - 최대 반복: {sa_optimizer.max_iterations}")
    
    # 3. 최적화 실행
    print("\n3. 시간표 최적화 실행...")
    result = sa_optimizer.optimize(verbose=True)
    
    # 4. 결과 출력
    print("\n4. 최적화 결과:")
    sa_optimizer.print_solution(result['best_solution'])
    
    # 5. 상세 분석
    print("\n5. 상세 분석:")
    sa_optimizer.analyze_solution(result['best_solution'])
    
    # 6. 시각화 (matplotlib 사용시)
    try:
        print("\n6. 최적화 과정 시각화...")
        plot_optimization_progress(result['cost_history'], result['temperature_history'])
    except ImportError:
        print("matplotlib가 설치되지 않아 시각화를 건너뜁니다.")
    
    # 7. 결과 저장
    import os
    from datetime import datetime
    
    # results 폴더가 없으면 생성
    if not os.path.exists('results'):
        os.makedirs('results')
    
    # 타임스탬프 생성 (YYYY-MM-DD_HH-MM-SS 형식)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    output = {
        'student_info': {
            'name': user_profile['name'],
            'student_id': user_profile['student_id'],
            'major': user_profile['major'],
            'year': user_profile['current_year']
        },
        'optimized_timetable': result['best_solution'],
        'optimization_stats': {
            'final_cost': result['best_cost'],
            'iterations': result['iterations'],
            'algorithm': 'Simulated Annealing',
            'timestamp': timestamp
        },
        'cost_breakdown': cost_function.get_cost_breakdown(result['best_solution'])
    }
    
    # JSON으로 저장 (타임스탬프 포함한 파일명)
    result_file = f'results/timetable_{timestamp}.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 결과가 '{result_file}'에 저장되었습니다.")
    
    # 추가로 최적화 로그도 저장 (타임스탬프 포함)
    log_file = f'results/log_{timestamp}.txt'
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=== 시뮬레이티드 어닐링 최적화 로그 ===\n")
        f.write(f"실행 시간: {timestamp}\n")
        f.write(f"학생: {user_profile['name']} ({user_profile['student_id']})\n")
        f.write(f"전공: {user_profile['major']}, {user_profile['current_year']}학년\n")
        f.write(f"목표 학점: {user_profile['target_credits_this_semester']}\n\n")
        
        f.write("=== 최적화 파라미터 ===\n")
        f.write(f"초기 온도: {sa_optimizer.initial_temperature}\n")
        f.write(f"최종 온도: {sa_optimizer.final_temperature}\n")
        f.write(f"냉각률: {sa_optimizer.cooling_rate}\n")
        f.write(f"최대 반복: {sa_optimizer.max_iterations}\n\n")
        
        f.write("=== 최적화 결과 ===\n")
        f.write(f"최종 비용: {result['best_cost']:.2f}\n")
        f.write(f"총 반복 횟수: {result['iterations']}\n")
        f.write(f"알고리즘: Simulated Annealing\n\n")
        
        f.write("=== 선택된 과목 ===\n")
        total_credits = 0
        for i, course_selection in enumerate(result['best_solution'], 1):
            for course in course_db['courses']:
                if (course['course_code'] == course_selection['course_code'] and 
                    course['section'] == course_selection['section']):
                    f.write(f"{i}. {course['course_name']} ({course['course_code']}-{course['section']})\n")
                    f.write(f"   교수: {course['professor']}, 학점: {course['credits']}, 시간: {course['schedule']}\n")
                    f.write(f"   강의실: {course['classroom']}, 분류: {course['category']}, 영역: {course['area']}\n\n")
                    total_credits += course['credits']
                    break
        
        f.write(f"총 학점: {total_credits}\n\n")
        
        f.write("=== 비용 분석 ===\n")
        cost_breakdown = cost_function.get_cost_breakdown(result['best_solution'])
        for cost_type, cost_value in cost_breakdown.items():
            if cost_value > 0:
                f.write(f"{cost_type}: {cost_value:.2f}\n")
        
        f.write(f"\n총 비용: {cost_breakdown['total']:.2f}\n")
    
    print(f"✅ 최적화 로그가 '{log_file}'에 저장되었습니다.")
    
    # 최신 결과를 latest로도 복사 (가장 최근 결과를 쉽게 확인)
    latest_json = 'results/latest_timetable.json'
    latest_log = 'results/latest_log.txt'
    
    import shutil
    shutil.copy2(result_file, latest_json)
    shutil.copy2(log_file, latest_log)
    
    print(f"✅ 최신 결과가 'latest_timetable.json'과 'latest_log.txt'로도 저장되었습니다.")
    print("\n🎉 최적화 완료!")

if __name__ == "__main__":
    main()