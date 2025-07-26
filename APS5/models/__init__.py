"""
APS (Advanced Planning & Scheduling) 데이터 모델 패키지

이 패키지에는 APS 시스템에서 사용되는 모든 데이터 모델이 포함되어 있습니다.

모델 클래스:
    - Product: 제품 정보
    - Process: 공정 정보  
    - Equipment: 장비 정보
    - Schedule: 스케줄 정보
    - Batch: 배치 정보
"""

from .product import Product
from .process import Process, ProcessStatus
from .equipment import (
    Equipment, 
    EquipmentStatus, 
    MaintenanceType, 
    WorkingHours
)
from .schedule import (
    Schedule, 
    Batch, 
    ScheduleStatus, 
    BatchStatus
)

# 모든 모델 클래스와 열거형 export
__all__ = [
    # Core Models
    "Product",
    "Process", 
    "Equipment",
    "Schedule",
    "Batch",
    
    # Status Enums
    "ProcessStatus",
    "EquipmentStatus",
    "ScheduleStatus", 
    "BatchStatus",
    
    # Supporting Classes
    "MaintenanceType",
    "WorkingHours"
]

# 패키지 메타데이터
__version__ = "1.0.0"
__author__ = "APS Development Team"
__description__ = "APS (Advanced Planning & Scheduling) Data Models"


def get_all_models():
    """모든 모델 클래스를 딕셔너리 형태로 반환"""
    return {
        "Product": Product,
        "Process": Process,
        "Equipment": Equipment,
        "Schedule": Schedule,
        "Batch": Batch
    }


def get_status_enums():
    """모든 상태 열거형을 딕셔너리 형태로 반환"""
    return {
        "ProcessStatus": ProcessStatus,
        "EquipmentStatus": EquipmentStatus,
        "ScheduleStatus": ScheduleStatus,
        "BatchStatus": BatchStatus,
        "MaintenanceType": MaintenanceType
    }


def validate_models():
    """
    모든 모델이 올바르게 로드되었는지 확인
    개발 및 테스트 목적으로 사용
    """
    models = get_all_models()
    enums = get_status_enums()
    
    print("=== APS Models Validation ===")
    print(f"Loaded {len(models)} models:")
    for name, model in models.items():
        print(f"  - {name}: {model.__name__}")
    
    print(f"\nLoaded {len(enums)} status enums:")
    for name, enum in enums.items():
        print(f"  - {name}: {enum.__name__}")
    
    print("\n✓ All models loaded successfully!")
    return True


if __name__ == "__main__":
    # 모듈을 직접 실행하면 모델 검증 수행
    validate_models()

