from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ProcessStatus(str, Enum):
    """공정 상태 열거형"""
    READY = "ready"           # 준비
    IN_PROGRESS = "in_progress"  # 진행 중
    COMPLETED = "completed"     # 완료
    PAUSED = "paused"          # 일시정지
    FAILED = "failed"          # 실패


class Process(BaseModel):
    """
    공정 정보를 나타내는 모델 클래스
    """
    process_name: str = Field(..., description="공정명")
    process_code: str = Field(..., description="공정 코드")
    description: Optional[str] = Field(None, description="공정 설명")
    required_equipment: List[str] = Field(..., description="필요 장비 리스트")
    standard_time: int = Field(..., description="표준 소요시간(분)", gt=0)
    setup_time: int = Field(default=0, description="준비시간(분)", ge=0)
    cleanup_time: int = Field(default=0, description="정리시간(분)", ge=0)
    worker_count: int = Field(default=1, description="필요 작업자 수", gt=0)
    skill_level: int = Field(default=1, description="필요 숙련도 (1-5)", ge=1, le=5)
    
    # 상태 및 메타데이터
    status: ProcessStatus = Field(default=ProcessStatus.READY, description="공정 상태")
    process_order: int = Field(..., description="공정 순서", ge=1)
    is_critical: bool = Field(default=False, description="핵심 공정 여부")
    quality_check_required: bool = Field(default=False, description="품질검사 필요 여부")
    
    # 시간 추적
    created_at: datetime = Field(default_factory=datetime.now, description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    started_at: Optional[datetime] = Field(None, description="시작일시")
    completed_at: Optional[datetime] = Field(None, description="완료일시")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "process_name": "혼합공정",
                "process_code": "MIX001",
                "description": "원료 혼합 공정",
                "required_equipment": ["혼합기A", "혼합기B"],
                "standard_time": 120,
                "setup_time": 15,
                "cleanup_time": 10,
                "worker_count": 2,
                "skill_level": 3,
                "process_order": 2,
                "is_critical": True,
                "quality_check_required": True
            }
        }
    
    def get_total_time(self) -> int:
        """준비시간 + 표준시간 + 정리시간을 반환합니다."""
        return self.setup_time + self.standard_time + self.cleanup_time
    
    def start_process(self) -> bool:
        """공정을 시작합니다."""
        if self.status == ProcessStatus.READY:
            self.status = ProcessStatus.IN_PROGRESS
            self.started_at = datetime.now()
            self.updated_at = datetime.now()
            return True
        return False
    
    def complete_process(self) -> bool:
        """공정을 완료합니다."""
        if self.status == ProcessStatus.IN_PROGRESS:
            self.status = ProcessStatus.COMPLETED
            self.completed_at = datetime.now()
            self.updated_at = datetime.now()
            return True
        return False
    
    def pause_process(self) -> bool:
        """공정을 일시정지합니다."""
        if self.status == ProcessStatus.IN_PROGRESS:
            self.status = ProcessStatus.PAUSED
            self.updated_at = datetime.now()
            return True
        return False
    
    def resume_process(self) -> bool:
        """일시정지된 공정을 재개합니다."""
        if self.status == ProcessStatus.PAUSED:
            self.status = ProcessStatus.IN_PROGRESS
            self.updated_at = datetime.now()
            return True
        return False
    
    def fail_process(self, reason: Optional[str] = None) -> bool:
        """공정을 실패로 처리합니다."""
        if self.status in [ProcessStatus.IN_PROGRESS, ProcessStatus.PAUSED]:
            self.status = ProcessStatus.FAILED
            self.updated_at = datetime.now()
            return True
        return False
    
    def is_ready_to_start(self) -> bool:
        """공정이 시작 가능한 상태인지 확인합니다."""
        return self.status == ProcessStatus.READY
    
    def is_in_progress(self) -> bool:
        """공정이 진행 중인지 확인합니다."""
        return self.status == ProcessStatus.IN_PROGRESS
    
    def is_completed(self) -> bool:
        """공정이 완료되었는지 확인합니다."""
        return self.status == ProcessStatus.COMPLETED
    
    def get_duration(self) -> Optional[int]:
        """
        공정의 실제 소요시간을 반환합니다 (분 단위).
        시작일시와 완료일시가 모두 있어야 계산 가능합니다.
        """
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)  # 분 단위로 변환
        return None

