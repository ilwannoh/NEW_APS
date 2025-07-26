from typing import Optional, List, Dict
from datetime import datetime, time
from pydantic import BaseModel, Field
from enum import Enum


class EquipmentStatus(str, Enum):
    """장비 상태 열거형"""
    AVAILABLE = "available"     # 사용 가능
    IN_USE = "in_use"          # 사용 중
    MAINTENANCE = "maintenance"  # 유지보수
    BREAKDOWN = "breakdown"     # 고장
    RESERVED = "reserved"       # 예약됨


class MaintenanceType(str, Enum):
    """유지보수 유형"""
    PREVENTIVE = "preventive"   # 예방정비
    CORRECTIVE = "corrective"   # 사후정비
    EMERGENCY = "emergency"     # 비상정비


class WorkingHours(BaseModel):
    """작업시간 정보"""
    start_time: time = Field(..., description="시작시간")
    end_time: time = Field(..., description="종료시간")
    break_start: Optional[time] = Field(None, description="휴식 시작시간")
    break_end: Optional[time] = Field(None, description="휴식 종료시간")
    
    def get_total_minutes(self) -> int:
        """사용 가능한 총 시간을 분 단위로 반환"""
        # 전체 작업시간 계산
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        
        # 하루를 넘어가는 경우 처리
        if end_minutes < start_minutes:
            end_minutes += 24 * 60
        
        total_minutes = end_minutes - start_minutes
        
        # 휴식시간 제외
        if self.break_start and self.break_end:
            break_start_min = self.break_start.hour * 60 + self.break_start.minute
            break_end_min = self.break_end.hour * 60 + self.break_end.minute
            break_duration = break_end_min - break_start_min
            total_minutes -= break_duration
        
        return total_minutes


class Equipment(BaseModel):
    """
    장비 정보를 나타내는 모델 클래스
    """
    equipment_name: str = Field(..., description="장비명")
    equipment_code: str = Field(..., description="장비 코드")
    equipment_type: str = Field(..., description="장비 유형")
    location: str = Field(..., description="소속실/지역")
    capacity: float = Field(..., description="장비 용량/성능", gt=0)
    capacity_unit: str = Field(..., description="용량 단위")
    
    # 상태 정보
    status: EquipmentStatus = Field(default=EquipmentStatus.AVAILABLE, description="장비 상태")
    utilization_rate: float = Field(default=0.0, description="가동률 (%)", ge=0, le=100)
    efficiency_rate: float = Field(default=100.0, description="효율성 (%)", ge=0, le=150)
    
    # 작업시간 정보
    working_hours: WorkingHours = Field(..., description="작업시간 정보")
    available_days: List[int] = Field(default=[1,2,3,4,5], description="사용 가능 요일 (0=월, 6=일)")
    
    # 유지보수 정보
    last_maintenance: Optional[datetime] = Field(None, description="마지막 유지보수 일시")
    next_maintenance: Optional[datetime] = Field(None, description="다음 유지보수 예정일")
    maintenance_interval_hours: int = Field(default=720, description="유지보수 주기(시간)", gt=0)
    
    # 메타데이터
    manufacturer: Optional[str] = Field(None, description="제조사")
    model: Optional[str] = Field(None, description="모델명")
    purchase_date: Optional[datetime] = Field(None, description="구매일")
    warranty_until: Optional[datetime] = Field(None, description="보증기간 만료일")
    
    created_at: datetime = Field(default_factory=datetime.now, description="등록일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            time: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "equipment_name": "혼합기A",
                "equipment_code": "MIX001",
                "equipment_type": "혼합장비",
                "location": "제1공장",
                "capacity": 500.0,
                "capacity_unit": "kg/batch",
                "working_hours": {
                    "start_time": "08:00:00",
                    "end_time": "18:00:00",
                    "break_start": "12:00:00",
                    "break_end": "13:00:00"
                },
                "available_days": [1, 2, 3, 4, 5],
                "manufacturer": "ABC장비",
                "model": "MIX-500A"
            }
        }
    
    def get_daily_available_time(self) -> int:
        """일일 사용 가능 시간을 분 단위로 반환"""
        return self.working_hours.get_total_minutes()
    
    def is_available(self) -> bool:
        """장비가 사용 가능한지 확인"""
        return self.status == EquipmentStatus.AVAILABLE
    
    def is_in_use(self) -> bool:
        """장비가 사용 중인지 확인"""
        return self.status == EquipmentStatus.IN_USE
    
    def start_using(self) -> bool:
        """장비 사용 시작"""
        if self.status == EquipmentStatus.AVAILABLE:
            self.status = EquipmentStatus.IN_USE
            self.updated_at = datetime.now()
            return True
        return False
    
    def stop_using(self) -> bool:
        """장비 사용 종료"""
        if self.status == EquipmentStatus.IN_USE:
            self.status = EquipmentStatus.AVAILABLE
            self.updated_at = datetime.now()
            return True
        return False
    
    def start_maintenance(self, maintenance_type: MaintenanceType = MaintenanceType.PREVENTIVE) -> bool:
        """유지보수 시작"""
        if self.status in [EquipmentStatus.AVAILABLE, EquipmentStatus.RESERVED]:
            self.status = EquipmentStatus.MAINTENANCE
            self.last_maintenance = datetime.now()
            self.updated_at = datetime.now()
            return True
        return False
    
    def complete_maintenance(self) -> bool:
        """유지보수 완료"""
        if self.status == EquipmentStatus.MAINTENANCE:
            self.status = EquipmentStatus.AVAILABLE
            # 다음 유지보수 예정일 업데이트
            if self.last_maintenance:
                from datetime import timedelta
                self.next_maintenance = self.last_maintenance + timedelta(hours=self.maintenance_interval_hours)
            self.updated_at = datetime.now()
            return True
        return False
    
    def report_breakdown(self) -> bool:
        """장비 고장 신고"""
        if self.status != EquipmentStatus.BREAKDOWN:
            self.status = EquipmentStatus.BREAKDOWN
            self.updated_at = datetime.now()
            return True
        return False
    
    def is_available_on_day(self, weekday: int) -> bool:
        """
        특정 요일에 사용 가능한지 확인
        
        Args:
            weekday: 0=월요일, 1=화요일, ..., 6=일요일
        """
        return weekday in self.available_days
    
    def needs_maintenance(self) -> bool:
        """유지보수가 필요한지 확인"""
        if not self.next_maintenance:
            return False
        return datetime.now() >= self.next_maintenance
    
    def calculate_utilization(self, used_time_minutes: int, total_available_minutes: int) -> float:
        """
        가동률 계산 및 업데이트
        
        Args:
            used_time_minutes: 실제 사용 시간(분)
            total_available_minutes: 총 사용 가능 시간(분)
        
        Returns:
            가동률 (%)
        """
        if total_available_minutes == 0:
            self.utilization_rate = 0.0
        else:
            self.utilization_rate = (used_time_minutes / total_available_minutes) * 100
        
        self.updated_at = datetime.now()
        return self.utilization_rate

