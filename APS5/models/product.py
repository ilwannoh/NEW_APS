from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Product(BaseModel):
    """
    제품 정보를 나타내는 모델 클래스
    """
    abbreviation: str = Field(..., description="제품 약어명")
    specification: str = Field(..., description="제품 규격")
    manufacturing_number: str = Field(..., description="제조번호")
    batch_quantity: int = Field(..., description="배치수량", gt=0)
    process_sequence: List[str] = Field(..., description="공정순서 리스트")
    lead_time: int = Field(..., description="리드타임(분)", ge=0)
    unit_price: Optional[float] = Field(None, description="단가", ge=0)
    product_type: Optional[str] = Field(None, description="제품 유형")
    priority: int = Field(default=5, description="우선순위 (1=최고, 10=최저)", ge=1, le=10)
    
    # 계산된 속성들
    total_process_time: Optional[int] = Field(None, description="총 공정시간(분)")
    created_at: datetime = Field(default_factory=datetime.now, description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "abbreviation": "PROD001",
                "specification": "10kg 포장",
                "manufacturing_number": "MFG202501001",
                "batch_quantity": 100,
                "process_sequence": ["전처리", "혼합", "포장"],
                "lead_time": 480,
                "unit_price": 1500.0,
                "product_type": "일반제품",
                "priority": 3
            }
        }
    
    def add_process(self, process_name: str) -> None:
        """공정을 추가합니다."""
        if process_name not in self.process_sequence:
            self.process_sequence.append(process_name)
            self.updated_at = datetime.now()
    
    def remove_process(self, process_name: str) -> bool:
        """공정을 제거합니다. 성공시 True, 실패시 False 반환"""
        if process_name in self.process_sequence:
            self.process_sequence.remove(process_name)
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_process_count(self) -> int:
        """총 공정 개수를 반환합니다."""
        return len(self.process_sequence)
    
    def calculate_total_time(self, process_times: dict) -> int:
        """
        공정별 소요시간 딕셔너리를 받아 총 소요시간을 계산합니다.
        
        Args:
            process_times: {"공정명": 소요시간(분)} 형태의 딕셔너리
        
        Returns:
            총 소요시간(분)
        """
        total = sum(process_times.get(process, 0) for process in self.process_sequence)
        self.total_process_time = total
        return total

