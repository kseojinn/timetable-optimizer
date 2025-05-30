import random
import math
import copy
from typing import List, Dict, Tuple

class TimetableSimulatedAnnealing:
    def __init__(self, user_profile, course_database, time_parser, cost_function):
        self.user_profile = user_profile
        self.course_db = course_database
        self.time_parser = time_parser
        self.cost_function = cost_function
        
        # SA 파라미터
        self.initial_temperature = 1000.0
        self.final_temperature = 1.0
        self.cooling_rate = 0.95
        self.max_iterations = 1000
        
        # 과목별 가능한 분반들 미리 계산
        self.available_sections = self._build_available_sections()
    
    def _build_available_sections(self):
        """각 과목코드별로 선택 가능한 분반들 매핑"""
        sections_map = {}
        
        # 1. 필수과목들은 자동으로 모든 분반 추가
        required_courses = set(self.user_profile['constraints']['required_courses'])
        
        for course in self.course_db['courses']:
            course_code = course['course_code']
            section = course['section']
            
            # 필수과목이면 모든 분반 자동 추가
            if course_code in required_courses:
                if course_code not in sections_map:
                    sections_map[course_code] = []
                sections_map[course_code].append(section)
        
        # 2. wanted_courses에 있는 과목들 추가 (우선순위 부여용)
        wanted_courses = {wc['course_code']: wc['sections'] 
                         for wc in self.user_profile.get('wanted_courses', [])}
        
        for course in self.course_db['courses']:
            course_code = course['course_code']
            section = course['section']
            
            # wanted_courses에 명시된 과목이고 필수과목이 아닌 경우
            if course_code in wanted_courses and course_code not in required_courses:
                if section in wanted_courses[course_code]:
                    if course_code not in sections_map:
                        sections_map[course_code] = []
                    if section not in sections_map[course_code]:  # 중복 방지
                        sections_map[course_code].append(section)
        
        return sections_map
    
    def generate_initial_solution(self):
        """초기 해 생성 (필수과목 우선, wanted_courses 고려, 학점 목표 달성)"""
        solution = []
        
        # 1. 필수과목부터 우선 선택 (모든 분반 고려)
        required_courses = self.user_profile['constraints']['required_courses']
        
        for course_code in required_courses:
            if course_code in self.available_sections:
                section = random.choice(self.available_sections[course_code])
                solution.append({'course_code': course_code, 'section': section})
        
        # 2. 현재 선택된 과목들의 학점 계산
        current_credits = self._calculate_credits(solution)
        target_credits = self.user_profile['target_credits_this_semester']
        min_credits = self.user_profile['min_credits']
        
        # 3. wanted_courses 중에서 추가 선택 (우선순위 순으로)
        wanted_courses_list = self.user_profile.get('wanted_courses', [])
        # 우선순위 높은 순으로 정렬
        wanted_courses_list.sort(key=lambda x: x['priority'], reverse=True)
        
        for wanted_course in wanted_courses_list:
            course_code = wanted_course['course_code']
            
            # 이미 선택된 과목(필수과목)이면 스킵
            if any(c['course_code'] == course_code for c in solution):
                continue
                
            if course_code in self.available_sections:
                section = random.choice(self.available_sections[course_code])
                candidate_solution = solution + [{'course_code': course_code, 'section': section}]
                
                # 기본적인 제약 확인 (시간 충돌 등)
                if not self._has_hard_constraints_violation(candidate_solution):
                    solution.append({'course_code': course_code, 'section': section})
                    current_credits = self._calculate_credits(solution)
                    
                    # 목표 학점에 도달했으면 중단
                    if current_credits >= target_credits:
                        break
        
        # 4. 최소 학점 미달 시 추가 과목 자동 선택
        current_credits = self._calculate_credits(solution)
        if current_credits < min_credits:
            additional_courses = self._find_additional_courses_for_credits(
                solution, min_credits, target_credits
            )
            solution.extend(additional_courses)
        
        return solution
    
    def _find_additional_courses_for_credits(self, current_solution, min_credits, target_credits):
        """학점 부족 시 추가 과목 자동 선택"""
        additional_courses = []
        current_credits = self._calculate_credits(current_solution)
        current_codes = {c['course_code'] for c in current_solution}
        
        # 선택 가능한 모든 과목들 수집
        available_courses = []
        
        for course in self.course_db['courses']:
            course_code = course['course_code']
            
            # 이미 선택된 과목은 제외
            if course_code in current_codes:
                continue
                
            # 선수과목 확인
            if self._has_prerequisite_violation([{'course_code': course_code, 'section': course['section']}]):
                continue
                
            available_courses.append(course)
        
        # 학점별로 그룹화하여 효율적 선택
        courses_by_credits = {}
        for course in available_courses:
            credits = course['credits']
            if credits > 0:  # 0학점 과목 제외
                if credits not in courses_by_credits:
                    courses_by_credits[credits] = []
                courses_by_credits[credits].append(course)
        
        # 학점 부족분 계산
        needed_credits = min_credits - current_credits
        target_additional = target_credits - current_credits
        
        # 우선 교양영역 요구사항을 만족하는 과목들 선택
        additional_courses.extend(self._select_courses_for_area_requirements(
            current_solution + additional_courses, courses_by_credits
        ))
        
        # 남은 학점 채우기
        current_additional_credits = self._calculate_credits(additional_courses)
        remaining_needed = max(0, needed_credits - current_additional_credits)
        remaining_target = max(0, target_additional - current_additional_credits)
        
        # 효율적으로 학점 채우기 (큰 학점부터)
        credit_values = sorted(courses_by_credits.keys(), reverse=True)
        
        attempts = 0
        max_attempts = 50  # 무한루프 방지
        
        while (current_additional_credits < remaining_needed or 
               (remaining_target > 0 and current_additional_credits < remaining_target)) and attempts < max_attempts:
            
            attempts += 1
            added_course = False
            
            for credits in credit_values:
                if credits > remaining_target and remaining_target > 0:
                    continue  # 목표를 너무 초과하는 과목은 스킵
                    
                available_in_credits = [c for c in courses_by_credits[credits] 
                                      if c['course_code'] not in {ac['course_code'] for ac in additional_courses}]
                
                if available_in_credits:
                    selected_course = random.choice(available_in_credits)
                    course_selection = {
                        'course_code': selected_course['course_code'],
                        'section': selected_course['section']
                    }
                    
                    # 시간 충돌 검사
                    test_solution = current_solution + additional_courses + [course_selection]
                    if not self._has_hard_constraints_violation(test_solution):
                        additional_courses.append(course_selection)
                        current_additional_credits += credits
                        added_course = True
                        break
            
            if not added_course:
                break  # 더 이상 추가할 수 있는 과목이 없음
        
        return additional_courses
    
    def _select_courses_for_area_requirements(self, current_solution, courses_by_credits):
        """교양영역 요구사항을 만족하는 과목 선택"""
        selected_courses = []
        current_areas = self._get_current_area_counts(current_solution)
        area_requirements = self.user_profile['constraints']['area_requirements']
        
        for area, required_count in area_requirements.items():
            current_count = current_areas.get(area, 0)
            if current_count < required_count:
                # 해당 영역의 과목 찾기
                for credits in courses_by_credits:
                    area_courses = [c for c in courses_by_credits[credits] 
                                  if c.get('area') == area and 
                                  c['course_code'] not in {sc['course_code'] for sc in selected_courses}]
                    
                    if area_courses:
                        selected_course = random.choice(area_courses)
                        course_selection = {
                            'course_code': selected_course['course_code'],
                            'section': selected_course['section']
                        }
                        selected_courses.append(course_selection)
                        current_areas[area] = current_areas.get(area, 0) + 1
                        break
        
        return selected_courses
    
    def _get_current_area_counts(self, solution):
        """현재 선택된 과목들의 교양영역별 개수 계산"""
        area_counts = {}
        for course_selection in solution:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course and course.get('area'):
                area = course['area']
                area_counts[area] = area_counts.get(area, 0) + 1
        return area_counts
    
    def _has_prerequisite_violation(self, test_courses):
        """선수과목 위반 여부 확인"""
        selected_codes = [c['course_code'] for c in test_courses]
        completed_codes = self.user_profile['completed_courses']
        available_codes = completed_codes + selected_codes
        
        prereq_rules = self.user_profile['constraints']['prerequisite_rules']
        
        for course_selection in test_courses:
            course_code = course_selection['course_code']
            if course_code in prereq_rules:
                for prerequisite in prereq_rules[course_code]:
                    if prerequisite not in available_codes:
                        return True
        return False
    
    def _calculate_credits(self, solution):
        """해의 총 학점 계산"""
        total_credits = 0
        for course_selection in solution:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course:
                total_credits += course['credits']
        return total_credits
    
    def _get_course_details(self, course_code, section):
        """과목 상세정보 가져오기"""
        for course in self.course_db['courses']:
            if course['course_code'] == course_code and course['section'] == section:
                return course
        return None
    
    def _has_hard_constraints_violation(self, solution):
        """하드 제약 위반 여부 (시간 충돌, 선수과목 등)"""
        # 시간 충돌 검사
        schedules = []
        for course_selection in solution:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course and course['schedule']:
                for existing_schedule in schedules:
                    if self.time_parser.check_time_conflict(course['schedule'], existing_schedule):
                        return True
                schedules.append(course['schedule'])
        
        # 선수과목 검사
        selected_codes = [c['course_code'] for c in solution]
        completed_codes = self.user_profile['completed_courses']
        available_codes = completed_codes + selected_codes
        
        prereq_rules = self.user_profile['constraints']['prerequisite_rules']
        for course_selection in solution:
            course_code = course_selection['course_code']
            if course_code in prereq_rules:
                for prerequisite in prereq_rules[course_code]:
                    if prerequisite not in available_codes:
                        return True
        
        return False
    
    def generate_neighbor(self, current_solution):
        """이웃 해 생성 (필수과목 고려, 전체 과목 풀에서 학점 목표 달성)"""
        if not current_solution:
            return self.generate_initial_solution()
        
        neighbor = copy.deepcopy(current_solution)
        action = random.choice(['change_section', 'add_course', 'remove_course'])
        
        if action == 'change_section' and neighbor:
            # 기존 과목의 분반 변경
            idx = random.randint(0, len(neighbor) - 1)
            course_code = neighbor[idx]['course_code']
            
            if course_code in self.available_sections:
                available_sections = self.available_sections[course_code]
                if len(available_sections) > 1:
                    new_section = random.choice([s for s in available_sections 
                                               if s != neighbor[idx]['section']])
                    neighbor[idx]['section'] = new_section
            else:
                # available_sections에 없는 과목(자동 추가된 과목)의 경우
                # 같은 과목코드의 다른 분반 찾기
                same_course_sections = [c['section'] for c in self.course_db['courses'] 
                                      if c['course_code'] == course_code]
                if len(same_course_sections) > 1:
                    new_section = random.choice([s for s in same_course_sections 
                                               if s != neighbor[idx]['section']])
                    neighbor[idx]['section'] = new_section
        
        elif action == 'add_course':
            # 새로운 과목 추가
            current_codes = [c['course_code'] for c in neighbor]
            
            # 1순위: wanted_courses에서 선택
            wanted_courses_list = self.user_profile.get('wanted_courses', [])
            available_wanted = [wc for wc in wanted_courses_list 
                              if wc['course_code'] not in current_codes 
                              and wc['course_code'] in self.available_sections]
            
            # 2순위: 전체 과목 중에서 선택 (학점 목표 달성용)
            if available_wanted:
                # wanted_courses에서 우선순위 기반 선택
                weights = [wc['priority'] for wc in available_wanted]
                selected_course = random.choices(available_wanted, weights=weights)[0]
                course_code = selected_course['course_code']
                section = random.choice(self.available_sections[course_code])
            else:
                # wanted_courses가 없으면 전체 과목에서 선택
                eligible_course = self._find_random_eligible_course(current_codes)
                if eligible_course:
                    course_code = eligible_course['course_code']
                    section = eligible_course['section']
                else:
                    return neighbor  # 추가할 과목이 없음
            
            neighbor.append({'course_code': course_code, 'section': section})
        
        elif action == 'remove_course' and neighbor:
            # 과목 삭제 (필수과목은 제외)
            required_courses = set(self.user_profile['constraints']['required_courses'])
            removable_indices = [i for i, c in enumerate(neighbor) 
                               if c['course_code'] not in required_courses]
            
            if removable_indices:
                idx = random.choice(removable_indices)
                neighbor.pop(idx)
        
        return neighbor
    
    def _find_random_eligible_course(self, current_codes):
        """현재 선택되지 않은 과목 중에서 랜덤하게 하나 선택"""
        eligible_courses = []
        
        for course in self.course_db['courses']:
            course_code = course['course_code']
            
            # 이미 선택된 과목은 제외
            if course_code in current_codes:
                continue
                
            # 0학점 과목 제외 (채플 같은 것들)
            if course['credits'] <= 0:
                continue
                
            # 선수과목 확인
            if not self._has_prerequisite_violation([{'course_code': course_code, 'section': course['section']}]):
                eligible_courses.append(course)
        
        if eligible_courses:
            return random.choice(eligible_courses)
        return None
    
    def acceptance_probability(self, current_cost, new_cost, temperature):
        """수락 확률 계산"""
        if new_cost < current_cost:
            return 1.0
        else:
            return math.exp(-(new_cost - current_cost) / temperature)
    
    def optimize(self, verbose=True):
        """시뮬레이티드 어닐링 최적화 실행"""
        # 초기 해 생성
        current_solution = self.generate_initial_solution()
        current_cost = self.cost_function.calculate_total_cost(current_solution)
        
        best_solution = copy.deepcopy(current_solution)
        best_cost = current_cost
        
        temperature = self.initial_temperature
        iteration = 0
        
        cost_history = []
        temperature_history = []
        
        if verbose:
            print(f"초기 해: 비용 = {current_cost:.2f}, 과목 수 = {len(current_solution)}")
            print("최적화 시작...")
        
        while temperature > self.final_temperature and iteration < self.max_iterations:
            # 이웃 해 생성
            neighbor_solution = self.generate_neighbor(current_solution)
            neighbor_cost = self.cost_function.calculate_total_cost(neighbor_solution)
            
            # 수락 여부 결정
            if random.random() < self.acceptance_probability(current_cost, neighbor_cost, temperature):
                current_solution = neighbor_solution
                current_cost = neighbor_cost
                
                # 최적해 업데이트
                if current_cost < best_cost:
                    best_solution = copy.deepcopy(current_solution)
                    best_cost = current_cost
                    
                    if verbose and iteration % 100 == 0:
                        print(f"반복 {iteration}: 새로운 최적해 발견! 비용 = {best_cost:.2f}")
            
            # 온도 감소
            temperature *= self.cooling_rate
            iteration += 1
            
            # 히스토리 기록
            cost_history.append(current_cost)
            temperature_history.append(temperature)
            
            if verbose and iteration % 200 == 0:
                print(f"반복 {iteration}: 현재 비용 = {current_cost:.2f}, 온도 = {temperature:.2f}")
        
        if verbose:
            print(f"최적화 완료! 최종 비용 = {best_cost:.2f}")
            print(f"총 반복 횟수: {iteration}")
        
        return {
            'best_solution': best_solution,
            'best_cost': best_cost,
            'cost_history': cost_history,
            'temperature_history': temperature_history,
            'iterations': iteration
        }
    
    def print_solution(self, solution):
        """해 출력"""
        print("\n=== 최적 시간표 ===")
        total_credits = 0
        
        for i, course_selection in enumerate(solution, 1):
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course:
                print(f"{i}. {course['course_name']} ({course['course_code']}-{course['section']})")
                print(f"   교수: {course['professor']}, 학점: {course['credits']}")
                print(f"   시간: {course['schedule']}, 강의실: {course['classroom']}")
                print(f"   분류: {course['category']}, 영역: {course['area']}")
                print()
                total_credits += course['credits']
        
        print(f"총 학점: {total_credits}")
        
        # 시간표 매트릭스 출력
        print("\n=== 주간 시간표 ===")
        courses_with_details = []
        for course_selection in solution:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course:
                courses_with_details.append(course)
        
        matrix = self.time_parser.get_weekly_schedule_matrix(courses_with_details)
        self.time_parser.print_schedule_table(matrix)
    
    def analyze_solution(self, solution):
        """해 분석 및 상세 비용 분석"""
        cost_breakdown = self.cost_function.get_cost_breakdown(solution)
        
        print("\n=== 비용 분석 ===")
        for cost_type, cost_value in cost_breakdown.items():
            if cost_value != 0:  # 0이 아닌 값만 표시
                if cost_type == 'free_days_bonus' and cost_value < 0:
                    print(f"{cost_type}: {cost_value:.2f} (보상!)")
                else:
                    print(f"{cost_type}: {cost_value:.2f}")
        
        print(f"\n총 비용: {cost_breakdown['total']:.2f}")
        
        # 제약조건 만족도 분석
        print("\n=== 제약조건 분석 ===")
        
        # 학점 분석
        total_credits = self._calculate_credits(solution)
        target_credits = self.user_profile['target_credits_this_semester']
        print(f"총 학점: {total_credits} (목표: {target_credits})")
        
        # 필수과목 체크
        selected_codes = [c['course_code'] for c in solution]
        required_courses = self.user_profile['constraints']['required_courses']
        missing_required = [req for req in required_courses if req not in selected_codes]
        if missing_required:
            print(f"누락된 필수과목: {missing_required}")
        else:
            print("모든 필수과목 포함됨")
        
        # 교양영역 분석
        area_counts = {}
        for course_selection in solution:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course and course['area']:
                area = course['area']
                area_counts[area] = area_counts.get(area, 0) + 1
        
        print(f"교양영역별 이수 현황: {area_counts}")
        
        # 공강일 분석 (NEW!)
        print("\n=== 공강일 분석 ===")
        matrix = self.time_parser.get_weekly_schedule_matrix([
            self._get_course_details(c['course_code'], c['section']) 
            for c in solution if self._get_course_details(c['course_code'], c['section'])
        ])
        
        weekdays = ['월', '화', '수', '목', '금']
        days_with_classes = []
        free_days = []
        
        for day_idx, day_name in enumerate(weekdays):
            has_classes = any(period != '' for period in matrix[day_idx])
            if has_classes:
                days_with_classes.append(day_name)
            else:
                free_days.append(day_name)
        
        print(f"수업 있는 요일: {', '.join(days_with_classes)} ({len(days_with_classes)}일)")
        if free_days:
            print(f"🎉 공강일: {', '.join(free_days)} ({len(free_days)}일)")
        else:
            print("공강일 없음")
        
        # 공강일 보상 점수 계산
        free_days_bonus = len(free_days) * len(free_days) * 30
        weight = self.user_profile['cost_function_weights'].get('free_days_bonus', 100)
        total_bonus = free_days_bonus * weight / 100
        if total_bonus > 0:
            print(f"공강일 보상 점수: -{total_bonus:.1f}점")
        
        return cost_breakdown