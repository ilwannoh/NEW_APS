from datetime import datetime, timedelta, time
from typing import List, Optional, Dict, Tuple
import logging
from enum import Enum
import threading


class WorkingDayType(Enum):
    """작업일 유형"""
    WORKING_DAY = "working_day"     # 일반 작업일
    WEEKEND = "weekend"             # 주말
    HOLIDAY = "holiday"             # 공휴일
    OVERTIME = "overtime"           # 연장 근무


class TimeManager:
    """
    시간 관리를 위한 싱글톤 클래스
    8시간 = 1일 규칙 적용
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger(__name__)
            
            # 기본 설정
            self.hours_per_day = 8  # 1일당 근무시간
            self.minutes_per_hour = 60
            self.minutes_per_day = self.hours_per_day * self.minutes_per_hour
            
            # 기본 작업시간 (08:00 ~ 17:00, 12:00~13:00 점심)
            self.default_start_time = time(8, 0)   # 오전 8시
            self.default_end_time = time(17, 0)    # 오후 5시
            self.lunch_start = time(12, 0)         # 점심 시작
            self.lunch_end = time(13, 0)           # 점심 종료
            
            # 공휴일 목록 (2025년 기준)
            self.holidays = set([
                datetime(2025, 1, 1),   # 신정
                datetime(2025, 1, 28),  # 설날 연휴
                datetime(2025, 1, 29),  # 설낡
                datetime(2025, 1, 30),  # 설날 연휴
                datetime(2025, 3, 1),   # 삼일절
                datetime(2025, 5, 5),   # 어린이날
                datetime(2025, 6, 6),   # 현충일
                datetime(2025, 8, 15),  # 광복절
                datetime(2025, 10, 3),  # 개천절
                datetime(2025, 10, 9),  # 한글날
                datetime(2025, 12, 25), # 크리스마스
            ])
            
            # 주말 설정 (0=월요일, 6=일요일)
            self.weekend_days = {5, 6}  # 토요일, 일요일
            
            self.initialized = True
    
    def set_working_hours(self, start_time: time, end_time: time, 
                         lunch_start: Optional[time] = None, 
                         lunch_end: Optional[time] = None) -> None:
        """
        작업시간 설정
        
        Args:
            start_time: 업무 시작 시간
            end_time: 업무 종료 시간  
            lunch_start: 점심 시작 시간
            lunch_end: 점심 종료 시간
        """
        self.default_start_time = start_time
        self.default_end_time = end_time
        
        if lunch_start and lunch_end:
            self.lunch_start = lunch_start
            self.lunch_end = lunch_end
        
        # 실제 작업시간 재계산
        total_minutes = self._calculate_daily_working_minutes()
        self.hours_per_day = total_minutes / 60
        self.minutes_per_day = total_minutes
        
        self.logger.info(f"작업시간 설정: {start_time} ~ {end_time}, 일일 {self.hours_per_day}시간")
    
    def add_holiday(self, holiday_date: datetime) -> None:
        """공휴일 추가"""
        self.holidays.add(holiday_date.replace(hour=0, minute=0, second=0, microsecond=0))
        self.logger.info(f"공휴일 추가: {holiday_date.strftime('%Y-%m-%d')}")
    
    def remove_holiday(self, holiday_date: datetime) -> None:
        """공휴일 제거"""
        date_only = holiday_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if date_only in self.holidays:
            self.holidays.remove(date_only)
            self.logger.info(f"공휴일 제거: {holiday_date.strftime('%Y-%m-%d')}")
    
    def get_working_day_type(self, date: datetime) -> WorkingDayType:
        """
        특정 날짜의 작업일 유형 반환
        
        Args:
            date: 확인할 날짜
        
        Returns:
            작업일 유형
        """
        date_only = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if date_only in self.holidays:
            return WorkingDayType.HOLIDAY
        
        if date.weekday() in self.weekend_days:
            return WorkingDayType.WEEKEND
        
        return WorkingDayType.WORKING_DAY
    
    def is_working_day(self, date: datetime) -> bool:
        """작업일 여부 확인"""
        return self.get_working_day_type(date) == WorkingDayType.WORKING_DAY
    
    def minutes_to_working_days(self, total_minutes: int) -> float:
        """
        분을 작업일로 변환
        
        Args:
            total_minutes: 총 소요시간(분)
        
        Returns:
            작업일 수
        """
        return total_minutes / self.minutes_per_day
    
    def working_days_to_minutes(self, working_days: float) -> int:
        """
        작업일을 분으로 변환
        
        Args:
            working_days: 작업일 수
        
        Returns:
            총 소요시간(분)
        """
        return int(working_days * self.minutes_per_day)
    
    def hours_to_working_days(self, total_hours: float) -> float:
        """
        시간을 작업일로 변환
        
        Args:
            total_hours: 총 소요시간
        
        Returns:
            작업일 수
        """
        return total_hours / self.hours_per_day
    
    def working_days_to_hours(self, working_days: float) -> float:
        """
        작업일을 시간으로 변환
        
        Args:
            working_days: 작업일 수
        
        Returns:
            총 소요시간
        """
        return working_days * self.hours_per_day
    
    def add_working_time(self, start_datetime: datetime, minutes_to_add: int) -> datetime:
        """
        시작 시간에 작업시간을 추가하여 종료 시간 계산
        
        Args:
            start_datetime: 시작 시간
            minutes_to_add: 추가할 작업시간(분)
        
        Returns:
            종료 시간
        """
        current_time = start_datetime
        remaining_minutes = minutes_to_add
        
        while remaining_minutes > 0:
            if not self.is_working_day(current_time):
                # 비작업일이면 다음 작업일로 이동
                current_time = self._get_next_working_day(current_time)
                current_time = current_time.replace(hour=self.default_start_time.hour,
                                                  minute=self.default_start_time.minute,
                                                  second=0, microsecond=0)
                continue
            
            # 하루 내에서 처리 가능한 시간 계산
            day_remaining_minutes = self._get_remaining_minutes_in_day(current_time)
            
            if remaining_minutes <= day_remaining_minutes:
                # 오늘 안에 완료 가능
                current_time = self._add_minutes_in_working_day(current_time, remaining_minutes)
                remaining_minutes = 0
            else:
                # 다음 날로 넘어감
                remaining_minutes -= day_remaining_minutes
                current_time = self._get_next_working_day(current_time)
                current_time = current_time.replace(hour=self.default_start_time.hour,
                                                  minute=self.default_start_time.minute,
                                                  second=0, microsecond=0)
        
        return current_time
    
    def calculate_working_duration(self, start_datetime: datetime, end_datetime: datetime) -> int:
        """
        두 시간 간의 실제 작업시간 계산 (분 단위)
        
        Args:
            start_datetime: 시작 시간
            end_datetime: 종료 시간
        
        Returns:
            실제 작업시간(분)
        """
        if start_datetime >= end_datetime:
            return 0
        
        total_minutes = 0
        current_date = start_datetime.date()
        end_date = end_datetime.date()
        
        while current_date <= end_date:
            current_datetime = datetime.combine(current_date, self.default_start_time)
            
            if not self.is_working_day(current_datetime):
                current_date += timedelta(days=1)
                continue
            
            # 하루 내에서의 작업시간 계산
            day_start = max(start_datetime, 
                          datetime.combine(current_date, self.default_start_time))
            day_end = min(end_datetime, 
                         datetime.combine(current_date, self.default_end_time))
            
            if day_start < day_end:
                day_minutes = self._calculate_working_minutes_in_day(day_start, day_end)
                total_minutes += day_minutes
            
            current_date += timedelta(days=1)
        
        return total_minutes
    
    def get_working_days_between(self, start_date: datetime, end_date: datetime) -> int:
        """
        두 날짜 간의 작업일 수 계산
        
        Args:
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            작업일 수
        """
        working_days = 0
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            current_datetime = datetime.combine(current_date, time())
            if self.is_working_day(current_datetime):
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def _calculate_daily_working_minutes(self) -> int:
        """일일 작업시간 계산 (분 단위)"""
        start_minutes = self.default_start_time.hour * 60 + self.default_start_time.minute
        end_minutes = self.default_end_time.hour * 60 + self.default_end_time.minute
        total_minutes = end_minutes - start_minutes
        
        # 점심시간 제외
        if self.lunch_start and self.lunch_end:
            lunch_start_minutes = self.lunch_start.hour * 60 + self.lunch_start.minute
            lunch_end_minutes = self.lunch_end.hour * 60 + self.lunch_end.minute
            lunch_duration = lunch_end_minutes - lunch_start_minutes
            total_minutes -= lunch_duration
        
        return total_minutes
    
    def _get_next_working_day(self, current_date: datetime) -> datetime:
        """다음 작업일 찾기"""
        next_date = current_date + timedelta(days=1)
        while not self.is_working_day(next_date):
            next_date += timedelta(days=1)
        return next_date
    
    def _get_remaining_minutes_in_day(self, current_time: datetime) -> int:
        """하루 내에서 남은 작업시간 계산"""
        current_time_only = current_time.time()
        end_time = self.default_end_time
        
        # 점심시간 고려
        if current_time_only < self.lunch_start:
            # 점심 전
            morning_remaining = self._time_diff_minutes(current_time_only, self.lunch_start)
            afternoon_total = self._time_diff_minutes(self.lunch_end, end_time)
            return morning_remaining + afternoon_total
        elif current_time_only < self.lunch_end:
            # 점심 시간 중
            afternoon_total = self._time_diff_minutes(self.lunch_end, end_time)
            return afternoon_total
        else:
            # 점심 후
            return self._time_diff_minutes(current_time_only, end_time)
    
    def _add_minutes_in_working_day(self, current_time: datetime, minutes: int) -> datetime:
        """작업일 내에서 분 추가"""
        result_time = current_time
        remaining_minutes = minutes
        
        current_time_only = result_time.time()
        
        # 점심 전 시간 처리
        if current_time_only < self.lunch_start:
            morning_available = self._time_diff_minutes(current_time_only, self.lunch_start)
            if remaining_minutes <= morning_available:
                return result_time + timedelta(minutes=remaining_minutes)
            else:
                remaining_minutes -= morning_available
                result_time = result_time.replace(hour=self.lunch_end.hour, minute=self.lunch_end.minute)
        
        # 점심 시간 중이면 점심 후로 이동
        elif current_time_only < self.lunch_end:
            result_time = result_time.replace(hour=self.lunch_end.hour, minute=self.lunch_end.minute)
        
        # 남은 시간 추가
        return result_time + timedelta(minutes=remaining_minutes)
    
    def _calculate_working_minutes_in_day(self, day_start: datetime, day_end: datetime) -> int:
        """하루 내에서의 작업시간 계산"""
        start_time = day_start.time()
        end_time = day_end.time()
        
        total_minutes = self._time_diff_minutes(start_time, end_time)
        
        # 점심시간과 겹치는 부분 제외
        if start_time < self.lunch_end and end_time > self.lunch_start:
            lunch_overlap_start = max(start_time, self.lunch_start)
            lunch_overlap_end = min(end_time, self.lunch_end)
            lunch_overlap = self._time_diff_minutes(lunch_overlap_start, lunch_overlap_end)
            total_minutes -= lunch_overlap
        
        return max(0, total_minutes)
    
    def _time_diff_minutes(self, start_time: time, end_time: time) -> int:
        """두 time 객체 간의 차이(분)"""
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute
        return max(0, end_minutes - start_minutes)
    
    def get_summary(self) -> Dict[str, any]:
        """
TimeManager 설정 요약 반환"""
        return {
            'hours_per_day': self.hours_per_day,
            'minutes_per_day': self.minutes_per_day,
            'working_hours': f"{self.default_start_time} ~ {self.default_end_time}",
            'lunch_time': f"{self.lunch_start} ~ {self.lunch_end}",
            'weekend_days': list(self.weekend_days),
            'holidays_count': len(self.holidays),
            'total_holidays': [h.strftime('%Y-%m-%d') for h in sorted(self.holidays)]
        }


# 편의 함수들
def get_time_manager() -> TimeManager:
    """
TimeManager 싱글톤 인스턴스 반환"""
    return TimeManager()


def minutes_to_days(minutes: int) -> float:
    """분을 작업일로 변환"""
    tm = get_time_manager()
    return tm.minutes_to_working_days(minutes)


def days_to_minutes(days: float) -> int:
    """작업일을 분으로 변환"""
    tm = get_time_manager()
    return tm.working_days_to_minutes(days)


def is_working_day(date: datetime) -> bool:
    """작업일 여부 확인"""
    tm = get_time_manager()
    return tm.is_working_day(date)


def add_working_time(start: datetime, minutes: int) -> datetime:
    """작업시간 추가"""
    tm = get_time_manager()
    return tm.add_working_time(start, minutes)

