import json
from datetime import datetime, timedelta

class TimeTableParser:
    def __init__(self):
        # 교시별 시작 시간 정의 (24시간 형식)
        self.period_times = {
            1: "09:00", 2: "09:55", 3: "10:50", 4: "11:45", 5: "12:40",
            6: "13:35", 7: "14:30", 8: "15:25", 9: "16:20", 10: "17:40",
            11: "18:30", 12: "19:20", 13: "20:10", 14: "21:00", 15: "21:55"
        }
        
        # 요일 매핑
        self.day_mapping = {
            '월': 'MON', '화': 'TUE', '수': 'WED', 
            '목': 'THU', '금': 'FRI', '토': 'SAT'
        }
    
    def parse_schedule(self, schedule_str):
        """
        '월4-6', '화1-3' 같은 형식을 파싱
        Returns: [{'day': 'MON', 'start_period': 4, 'end_period': 6, 'start_time': '11:45', 'end_time': '13:35'}]
        """
        if not schedule_str or schedule_str.strip() == "":
            return []
        
        # 여러 시간대가 있는 경우 (예: "월4-6,수7-9")
        time_blocks = []
        
        # 콤마로 분리된 시간대들 처리
        for block in schedule_str.split(','):
            block = block.strip()
            if not block:
                continue
                
            # 요일과 시간 분리
            day_char = block[0]
            time_part = block[1:]
            
            if day_char not in self.day_mapping:
                continue
                
            # 시간 범위 파싱 (예: "4-6")
            if '-' in time_part:
                start_period, end_period = map(int, time_part.split('-'))
            else:
                # 단일 교시인 경우
                start_period = end_period = int(time_part)
            
            # 시작/종료 시간 계산
            start_time = self.period_times.get(start_period, "09:00")
            # 종료 시간은 마지막 교시 + 45분
            end_time = self._calculate_end_time(end_period)
            
            time_blocks.append({
                'day': self.day_mapping[day_char],
                'start_period': start_period,
                'end_period': end_period,
                'start_time': start_time,
                'end_time': end_time
            })
        
        return time_blocks
    
    def _calculate_end_time(self, end_period):
        """교시 종료 시간 계산 (각 교시는 45분)"""
        start_time_str = self.period_times.get(end_period, "09:00")
        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = start_time + timedelta(minutes=45)
        return end_time.strftime("%H:%M")
    
    def check_time_conflict(self, schedule1, schedule2):
        """두 시간표 간 충돌 검사"""
        blocks1 = self.parse_schedule(schedule1)
        blocks2 = self.parse_schedule(schedule2)
        
        for block1 in blocks1:
            for block2 in blocks2:
                if (block1['day'] == block2['day'] and 
                    self._periods_overlap(block1, block2)):
                    return True
        return False
    
    def _periods_overlap(self, block1, block2):
        """교시 겹침 검사"""
        return not (block1['end_period'] < block2['start_period'] or 
                   block2['end_period'] < block1['start_period'])
    
    def get_weekly_schedule_matrix(self, course_list):
        """
        주간 시간표 매트릭스 생성 (요일 x 교시)
        Returns: 5x15 매트릭스 (월-금 x 1-15교시)
        """
        # 0: 빈 시간, 과목코드: 해당 과목
        matrix = [[''] * 15 for _ in range(5)]
        day_indices = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4}
        
        for course in course_list:
            if 'schedule' not in course or not course['schedule']:
                continue
                
            blocks = self.parse_schedule(course['schedule'])
            for block in blocks:
                if block['day'] in day_indices:
                    day_idx = day_indices[block['day']]
                    for period in range(block['start_period'], block['end_period'] + 1):
                        if 1 <= period <= 15:
                            matrix[day_idx][period-1] = course['course_code']
        
        return matrix
    
    def print_schedule_table(self, matrix):
        """시간표 매트릭스를 보기 좋게 출력"""
        days = ['월', '화', '수', '목', '금']
        
        print("교시\\요일", end="")
        for day in days:
            print(f"\t{day}", end="")
        print()
        
        for period in range(15):
            print(f"{period+1}교시", end="")
            for day_idx in range(5):
                course = matrix[day_idx][period] if matrix[day_idx][period] else "-"
                print(f"\t{course}", end="")
            print()

# 테스트 예제
if __name__ == "__main__":
    parser = TimeTableParser()
    
    # 테스트 데이터
    test_courses = [
        {"course_code": "20405", "schedule": "화7-9"},
        {"course_code": "20470", "schedule": "월4-6"},
        {"course_code": "01605", "schedule": "수4-6"},
    ]
    
    # 시간 파싱 테스트
    schedule = parser.parse_schedule("월4-6")
    print("파싱 결과:", schedule)
    
    # 충돌 검사 테스트
    conflict = parser.check_time_conflict("월4-6", "월5-7")
    print("충돌 여부:", conflict)
    
    # 시간표 매트릭스 생성
    matrix = parser.get_weekly_schedule_matrix(test_courses)
    print("\n시간표:")
    parser.print_schedule_table(matrix)
