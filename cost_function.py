class TimetableCostFunction:
    def __init__(self, user_profile, course_database, time_parser):
        self.user_profile = user_profile
        self.course_db = course_database
        self.time_parser = time_parser
        self.weights = user_profile['cost_function_weights']
    
    def calculate_total_cost(self, selected_courses):
        """
        선택된 과목들에 대한 총 비용 계산
        selected_courses: [{'course_code': '01605', 'section': '001'}, ...]
        """
        total_cost = 0
        
        # 1. 시간 충돌 비용
        total_cost += self._time_conflict_cost(selected_courses)
        
        # 2. 선수과목 위반 비용
        total_cost += self._prerequisite_violation_cost(selected_courses)
        
        # 3. 학점 관련 비용
        total_cost += self._credit_cost(selected_courses)
        
        # 4. 필수과목 누락 비용
        total_cost += self._required_course_cost(selected_courses)
        
        # 5. 연강 비용
        total_cost += self._consecutive_classes_cost(selected_courses)
        
        # 6. 시간 선호도 비용
        total_cost += self._time_preference_cost(selected_courses)
        
        # 7. 점심시간 비용
        total_cost += self._lunch_time_cost(selected_courses)
        
        # 8. 교수 선호도 비용
        total_cost += self._professor_preference_cost(selected_courses)
        
        # 9. 교양영역 요구사항 비용
        total_cost += self._area_requirement_cost(selected_courses)
        
        # 10. 우선순위 비용
        total_cost += self._priority_cost(selected_courses)
        
        # 11. 공강일 비용
        total_cost += self._free_days_cost(selected_courses)
        
        return total_cost
    
    def _get_course_details(self, course_code, section):
        """과목 상세정보 가져오기"""
        for course in self.course_db['courses']:
            if course['course_code'] == course_code and course['section'] == section:
                return course
        return None
    
    def _time_conflict_cost(self, selected_courses):
        """시간 충돌 비용 (하드 제약)"""
        cost = 0
        schedules = []
        
        for course_selection in selected_courses:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course and course['schedule']:
                schedules.append(course['schedule'])
        
        # 모든 쌍에 대해 충돌 검사
        for i in range(len(schedules)):
            for j in range(i + 1, len(schedules)):
                if self.time_parser.check_time_conflict(schedules[i], schedules[j]):
                    cost += self.weights['time_conflict']
        
        return cost
    
    def _prerequisite_violation_cost(self, selected_courses):
        """선수과목 위반 비용"""
        cost = 0
        selected_codes = [c['course_code'] for c in selected_courses]
        completed_codes = self.user_profile['completed_courses']
        available_codes = completed_codes + selected_codes
        
        prereq_rules = self.user_profile['constraints']['prerequisite_rules']
        
        for course_selection in selected_courses:
            course_code = course_selection['course_code']
            if course_code in prereq_rules:
                for prerequisite in prereq_rules[course_code]:
                    if prerequisite not in available_codes:
                        cost += self.weights['prerequisite_violation']
        
        return cost
    
    def _credit_cost(self, selected_courses):
        """학점 관련 비용"""
        total_credits = 0
        for course_selection in selected_courses:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course:
                total_credits += course['credits']
        
        target_credits = self.user_profile['target_credits_this_semester']
        min_credits = self.user_profile['min_credits']
        max_credits = self.user_profile['max_credits']
        
        cost = 0
        if total_credits < min_credits:
            cost += (min_credits - total_credits) * self.weights['credit_shortage']
        elif total_credits > max_credits:
            cost += (total_credits - max_credits) * self.weights['credit_excess']
        
        return cost
    
    def _required_course_cost(self, selected_courses):
        """필수과목 누락 비용"""
        cost = 0
        selected_codes = [c['course_code'] for c in selected_courses]
        required_courses = self.user_profile['constraints']['required_courses']
        
        for required in required_courses:
            if required not in selected_codes:
                cost += self.weights['required_course_missing']
        
        return cost
    
    def _consecutive_classes_cost(self, selected_courses):
        """연강 비용"""
        cost = 0
        matrix = self._build_schedule_matrix(selected_courses)
        max_consecutive = self.user_profile['preferences']['max_consecutive_classes']
        
        # 각 요일별로 연강 검사
        for day_schedule in matrix:
            consecutive_count = 0
            for period in day_schedule:
                if period:  # 수업이 있는 경우
                    consecutive_count += 1
                else:  # 빈 시간
                    if consecutive_count > max_consecutive:
                        cost += (consecutive_count - max_consecutive) * self.weights['consecutive_classes']
                    consecutive_count = 0
            
            # 마지막 연강 체크
            if consecutive_count > max_consecutive:
                cost += (consecutive_count - max_consecutive) * self.weights['consecutive_classes']
        
        return cost
    
    def _time_preference_cost(self, selected_courses):
        """시간 선호도 비용"""
        cost = 0
        preferred_times = self.user_profile['preferences']['preferred_times']
        avoid_times = self.user_profile['preferences']['avoid_times']
        
        for course_selection in selected_courses:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if not course or not course['schedule']:
                continue
            
            # 기피 시간대 위반
            for avoid_time in avoid_times:
                if self.time_parser.check_time_conflict(course['schedule'], avoid_time):
                    cost += self.weights['avoid_time_violation']
            
            # 선호 시간대가 아닌 경우
            is_preferred = False
            for preferred_time in preferred_times:
                if self.time_parser.check_time_conflict(course['schedule'], preferred_time):
                    is_preferred = True
                    break
            
            if not is_preferred:
                cost += self.weights['non_preferred_time']
        
        return cost
    
    def _lunch_time_cost(self, selected_courses):
        """점심시간 확보 비용"""
        if not self.user_profile['preferences']['lunch_time_required']:
            return 0
        
        cost = 0
        matrix = self._build_schedule_matrix(selected_courses)
        lunch_periods = self.user_profile['preferences']['lunch_preferred_periods']
        
        # 각 요일별로 점심시간 확보 여부 체크
        for day_schedule in matrix:
            lunch_available = False
            for lunch_period in lunch_periods:
                if lunch_period <= len(day_schedule) and not day_schedule[lunch_period - 1]:
                    lunch_available = True
                    break
            
            if not lunch_available:
                cost += self.weights['lunch_time_violation']
        
        return cost
    
    def _professor_preference_cost(self, selected_courses):
        """교수 선호도 비용"""
        cost = 0
        preferred_profs = self.user_profile['preferences']['preferred_professors']
        
        for course_selection in selected_courses:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course and course['professor']:
                if course['professor'] not in preferred_profs:
                    cost += self.weights['non_preferred_professor']
        
        return cost
    
    def _area_requirement_cost(self, selected_courses):
        """교양영역 요구사항 비용"""
        cost = 0
        area_counts = {}
        area_requirements = self.user_profile['constraints']['area_requirements']
        
        # 선택된 과목들의 영역별 카운트
        for course_selection in selected_courses:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course and course['area']:
                area = course['area']
                area_counts[area] = area_counts.get(area, 0) + 1
        
        # 각 영역별 요구사항 확인
        for area, required_count in area_requirements.items():
            actual_count = area_counts.get(area, 0)
            if actual_count < required_count:
                cost += (required_count - actual_count) * self.weights['area_requirement_violation']
        
        return cost
    
    def _free_days_cost(self, selected_courses):
        """공강일 비용 (공강일이 많을수록 비용 감소 = 보상)"""
        matrix = self._build_schedule_matrix(selected_courses)
        
        # 각 요일별로 수업이 있는지 확인
        weekdays = ['월', '화', '수', '목', '금']  # 토요일은 제외
        days_with_classes = 0
        
        for day_idx, day_name in enumerate(weekdays):
            has_classes = any(period != '' for period in matrix[day_idx])
            if has_classes:
                days_with_classes += 1
        
        # 공강일 수 계산
        free_days = 5 - days_with_classes  # 최대 5일 중 공강일
        
        # 공강일이 많을수록 보상 (비용 감소)
        # 공강일 0개: 0점, 1개: -50점, 2개: -120점, 3개: -210점, 4개: -320점, 5개: -450점
        free_days_bonus = free_days * free_days * 30  # 제곱으로 보상 증가
        
        # 가중치 적용하여 비용으로 변환 (음수이므로 비용 감소 효과)
        weight = self.weights.get('free_days_bonus', 100)
        
        return -free_days_bonus * weight / 100  # 음수로 보상
    
    def _build_schedule_matrix(self, selected_courses):
        """선택된 과목들로 시간표 매트릭스 구성"""
        courses_with_details = []
        for course_selection in selected_courses:
            course = self._get_course_details(course_selection['course_code'], 
                                           course_selection['section'])
            if course:
                courses_with_details.append(course)
        
        return self.time_parser.get_weekly_schedule_matrix(courses_with_details)
    
    def _priority_cost(self, selected_courses):
        """우선순위 비용 (낮은 우선순위 과목 선택시 패널티)"""
        cost = 0
        wanted_courses = {wc['course_code']: wc['priority'] 
                         for wc in self.user_profile.get('wanted_courses', [])}
        
        for course_selection in selected_courses:
            course_code = course_selection['course_code']
            if course_code in wanted_courses:
                priority = wanted_courses[course_code]
                # 우선순위가 낮을수록 (숫자가 작을수록) 비용 증가
                cost += (10 - priority) * self.weights['low_priority_course']
        
        return cost
    
    def _free_days_cost(self, selected_courses):
        """공강일 비용 (공강일이 많을수록 비용 감소 = 보상)"""
        matrix = self._build_schedule_matrix(selected_courses)
        
        # 각 요일별로 수업이 있는지 확인
        weekdays = ['월', '화', '수', '목', '금']  # 토요일은 제외
        days_with_classes = 0
        
        for day_idx, day_name in enumerate(weekdays):
            has_classes = any(period != '' for period in matrix[day_idx])
            if has_classes:
                days_with_classes += 1
        
        # 공강일 수 계산
        free_days = 5 - days_with_classes  # 최대 5일 중 공강일
        
        # 공강일이 많을수록 보상 (비용 감소)
        # 공강일 0개: 0점, 1개: -50점, 2개: -120점, 3개: -210점, 4개: -320점, 5개: -450점
        free_days_bonus = free_days * free_days * 30  # 제곱으로 보상 증가
        
        # 가중치 적용하여 비용으로 변환 (음수이므로 비용 감소 효과)
        weight = self.weights.get('free_days_bonus', 100)
        
        return -free_days_bonus * weight / 100  # 음수로 보상
    
    def get_cost_breakdown(self, selected_courses):
        """비용 세부 분석"""
        breakdown = {
            'time_conflict': self._time_conflict_cost(selected_courses),
            'prerequisite_violation': self._prerequisite_violation_cost(selected_courses),
            'credit_cost': self._credit_cost(selected_courses),
            'required_course_missing': self._required_course_cost(selected_courses),
            'consecutive_classes': self._consecutive_classes_cost(selected_courses),
            'time_preference': self._time_preference_cost(selected_courses),
            'lunch_time': self._lunch_time_cost(selected_courses),
            'professor_preference': self._professor_preference_cost(selected_courses),
            'area_requirement': self._area_requirement_cost(selected_courses),
            'priority': self._priority_cost(selected_courses),
            'free_days_bonus': self._free_days_cost(selected_courses)  # 음수 값 (보상)
        }
        
        breakdown['total'] = sum(breakdown.values())
        return breakdown