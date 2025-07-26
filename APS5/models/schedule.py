from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum


class ScheduleStatus(str, Enum):
    """스케줄 상태 열거형"""
    PLANNED = "planned"         # 계획됨
    CONFIRMED = "confirmed"     # 확정됨
    IN_PROGRESS = "in_progress" # 진행 중
    COMPLETED = "completed"     # 완료
    CANCELLED = "cancelled"     # 취소
    DELAYED = "delayed"         # 지연


class BatchStatus(str, Enum):
    """배치 상태 열거형"""
    WAITING = "waiting"         # 대기
    READY = "ready"            # 준비
    IN_PROGRESS = "in_progress" # 진행 중
    COMPLETED = "completed"     # 완료
    FAILED = "failed"          # 실패
    CANCELLED = "cancelled"     # 취소


class Batch(BaseModel):
    """
    배치 정보를 나타내는 모델 클래스
    """
    batch_id: str = Field(..., description="배치 ID")
    product_code: str = Field(..., description="제품 코드")
    batch_size: int = Field(..., description="배치 크기", gt=0)
    priority: int = Field(default=5, description="우선순위 (1=최고, 10=최저)", ge=1, le=10)
    
    # 시간 정보
    planned_start_time: datetime = Field(..., description="계획 시작시간")
    planned_end_time: datetime = Field(..., description="계획 종료시간")
    actual_start_time: Optional[datetime] = Field(None, description="실제 시작시간")
    actual_end_time: Optional[datetime] = Field(None, description="실제 종료시간")
    
    # 상태 및 진행 정보
    status: BatchStatus = Field(default=BatchStatus.WAITING, description="배치 상태")
    current_process: Optional[str] = Field(None, description="현재 진행 중인 공정")
    completed_processes: List[str] = Field(default=[], description="완료된 공정 리스트")
    remaining_processes: List[str] = Field(default=[], description="남은 공정 리스트")
    
    # 리소스 할당
    assigned_equipment: Dict[str, str] = Field(default={}, description="공정별 할당된 장비")
    assigned_workers: Dict[str, List[str]] = Field(default={}, description="공정별 할당된 작업자")
    
    # 품질 및 성능 지표
    quality_score: Optional[float] = Field(None, description="품질 점수", ge=0, le=100)
    yield_rate: Optional[float] = Field(None, description="수율 (%)", ge=0, le=100)
    
    created_at: datetime = Field(default_factory=datetime.now, description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "batch_id": "BATCH2025001",
                "product_code": "PROD001",
                "batch_size": 100,
                "priority": 3,
                "planned_start_time": "2025-05-25T08:00:00",
                "planned_end_time": "2025-05-25T16:00:00",
                "remaining_processes": ["전처리", "혼합", "포장"]
            }
        }
    
    def start_batch(self) -> bool:
        """배치 시작"""
        if self.status == BatchStatus.READY:
            self.status = BatchStatus.IN_PROGRESS
            self.actual_start_time = datetime.now()
            self.updated_at = datetime.now()
            return True
        return False
    
    def complete_batch(self) -> bool:
        """배치 완료"""
        if self.status == BatchStatus.IN_PROGRESS:
            self.status = BatchStatus.COMPLETED
            self.actual_end_time = datetime.now()
            self.updated_at = datetime.now()
            return True
        return False
    
    def fail_batch(self, reason: Optional[str] = None) -> bool:
        """배치 실패 처리"""
        if self.status == BatchStatus.IN_PROGRESS:
            self.status = BatchStatus.FAILED
            self.updated_at = datetime.now()
            return True
        return False
    
    def complete_process(self, process_name: str) -> bool:
        """공정 완료 처리"""
        if process_name in self.remaining_processes:
            self.remaining_processes.remove(process_name)
            self.completed_processes.append(process_name)
            
            # 다음 공정 설정
            if self.remaining_processes:
                self.current_process = self.remaining_processes[0]
            else:
                self.current_process = None
                # 모든 공정 완료 시 배치 준비 상태로 변경
                if self.status == BatchStatus.WAITING:
                    self.status = BatchStatus.READY
            
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_progress_percentage(self) -> float:
        """진행률 계산 (%)"""
        total_processes = len(self.completed_processes) + len(self.remaining_processes)
        if total_processes == 0:
            return 0.0
        return (len(self.completed_processes) / total_processes) * 100
    
    def get_planned_duration(self) -> int:
        """계획된 소요시간 반환 (분 단위)"""
        delta = self.planned_end_time - self.planned_start_time
        return int(delta.total_seconds() / 60)
    
    def get_actual_duration(self) -> Optional[int]:
        """실제 소요시간 반환 (분 단위)"""
        if self.actual_start_time and self.actual_end_time:
            delta = self.actual_end_time - self.actual_start_time
            return int(delta.total_seconds() / 60)
        return None
    
    def is_delayed(self) -> bool:
        """지연 여부 확인"""
        if self.actual_end_time:
            return self.actual_end_time > self.planned_end_time
        elif self.status == BatchStatus.IN_PROGRESS:
            return datetime.now() > self.planned_end_time
        return False


class Schedule(BaseModel):
    """
    스케줄 정보를 나타내는 모델 클래스
    """
    schedule_id: str = Field(..., description="스케줄 ID")
    schedule_name: str = Field(..., description="스케줄명")
    description: Optional[str] = Field(None, description="스케줄 설명")
    
    # 시간 정보
    start_date: datetime = Field(..., description="시작일")
    end_date: datetime = Field(..., description="종료일")
    
    # 배치 정보
    batches: List[Batch] = Field(default=[], description="배치 리스트")
    
    # 상태 및 메타데이터
    status: ScheduleStatus = Field(default=ScheduleStatus.PLANNED, description="스케줄 상태")
    version: int = Field(default=1, description="스케줄 버전", ge=1)
    is_baseline: bool = Field(default=False, description="기준 스케줄 여부")
    
    # 성능 지표
    total_batches: int = Field(default=0, description="총 배치 수", ge=0)
    completed_batches: int = Field(default=0, description="완료된 배치 수", ge=0)
    efficiency_score: Optional[float] = Field(None, description="효율성 점수", ge=0, le=100)
    
    created_at: datetime = Field(default_factory=datetime.now, description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    created_by: Optional[str] = Field(None, description="생성자")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "schedule_id": "SCH20250525001",
                "schedule_name": "5월 4주차 생산계획",
                "description": "5월 마지막 주 생산 스케줄",
                "start_date": "2025-05-25T00:00:00",
                "end_date": "2025-05-31T23:59:59",
                "total_batches": 10
            }
        }
    
    def add_batch(self, batch: Batch) -> bool:
        """배치 추가"""
        if batch.batch_id not in [b.batch_id for b in self.batches]:
            self.batches.append(batch)
            self.total_batches = len(self.batches)
            self.updated_at = datetime.now()
            return True
        return False
    
    def remove_batch(self, batch_id: str) -> bool:
        """배치 제거"""
        for i, batch in enumerate(self.batches):
            if batch.batch_id == batch_id:
                self.batches.pop(i)
                self.total_batches = len(self.batches)
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_batch(self, batch_id: str) -> Optional[Batch]:
        """배치 조회"""
        for batch in self.batches:
            if batch.batch_id == batch_id:
                return batch
        return None
    
    def get_batches_by_status(self, status: BatchStatus) -> List[Batch]:
        """상태별 배치 조회"""
        return [batch for batch in self.batches if batch.status == status]
    
    def get_batches_by_priority(self, priority: int) -> List[Batch]:
        """우선순위별 배치 조회"""
        return [batch for batch in self.batches if batch.priority == priority]
    
    def confirm_schedule(self) -> bool:
        """스케줄 확정"""
        if self.status == ScheduleStatus.PLANNED:
            self.status = ScheduleStatus.CONFIRMED
            self.updated_at = datetime.now()
            return True
        return False
    
    def start_schedule(self) -> bool:
        """스케줄 시작"""
        if self.status == ScheduleStatus.CONFIRMED:
            self.status = ScheduleStatus.IN_PROGRESS
            self.updated_at = datetime.now()
            return True
        return False
    
    def complete_schedule(self) -> bool:
        """스케줄 완료"""
        if self.status == ScheduleStatus.IN_PROGRESS:
            self.status = ScheduleStatus.COMPLETED
            self.updated_at = datetime.now()
            return True
        return False
    
    def calculate_completion_rate(self) -> float:
        """완료률 계산 (%)"""
        if self.total_batches == 0:
            return 0.0
        
        completed_count = len([b for b in self.batches if b.status == BatchStatus.COMPLETED])
        self.completed_batches = completed_count
        return (completed_count / self.total_batches) * 100
    
    def get_delayed_batches(self) -> List[Batch]:
        """지연된 배치 조회"""
        return [batch for batch in self.batches if batch.is_delayed()]
    
    def get_schedule_duration(self) -> int:
        """스케줄 기간 반환 (일 단위)"""
        delta = self.end_date - self.start_date
        return delta.days + 1
    
    def optimize_batch_sequence(self) -> List[Batch]:
        """
        배치 순서 최적화 (우선순위 기준)
        높은 우선순위(1)가 먼저 오도록 정렬
        """
        return sorted(self.batches, key=lambda x: (x.priority, x.planned_start_time))
    
    def get_resource_utilization(self) -> Dict[str, float]:
        """
        리소스 활용률 계산
        장비별 사용률을 반환
        """
        equipment_usage = {}
        total_duration = self.get_schedule_duration() * 24 * 60  # 총 분
        
        for batch in self.batches:
            for process, equipment in batch.assigned_equipment.items():
                if equipment not in equipment_usage:
                    equipment_usage[equipment] = 0
                
                batch_duration = batch.get_planned_duration()
                equipment_usage[equipment] += batch_duration
        
        # 활용률 계산 (%)
        utilization_rates = {}
        for equipment, used_time in equipment_usage.items():
            utilization_rates[equipment] = (used_time / total_duration) * 100 if total_duration > 0 else 0
        
        return utilization_rates

