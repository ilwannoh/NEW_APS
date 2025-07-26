"""
마스터 데이터 모델
제품, 공정, 장비, 작업자 정보를 관리
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd


class MasterDataManager:
    """마스터 데이터를 관리하는 클래스"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # 프로젝트 루트 경로 찾기
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            self.data_dir = os.path.join(project_root, "data", "masters")
        else:
            self.data_dir = data_dir
        
        self.products = {}
        self.processes = {}
        self.equipment = {}
        self.operators = {}
        self._ensure_data_dir()
        self.load_all_data()
    
    def _ensure_data_dir(self):
        """데이터 디렉토리 확인 및 생성"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _get_file_path(self, data_type: str) -> str:
        """데이터 타입별 파일 경로 반환"""
        return os.path.join(self.data_dir, f"{data_type}.json")
    
    def load_all_data(self):
        """모든 마스터 데이터 로드"""
        self.products = self._load_data("products")
        self.processes = self._load_data("processes")
        self.equipment = self._load_data("equipment")
        self.operators = self._load_data("operators")
    
    def _load_data(self, data_type: str) -> Dict:
        """특정 타입의 데이터 로드"""
        file_path = self._get_file_path(data_type)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                return {}
        else:
            pass
        return {}
    
    def save_data(self, data_type: str, data: Dict):
        """데이터 저장"""
        file_path = self._get_file_path(data_type)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 제품 관련 메서드
    def add_product(self, product_id: str, name: str, priority: int, 
                   equipment_list: List[str], process_order: List[str], 
                   lead_time: float):
        """제품 추가"""
        self.products[product_id] = {
            "id": product_id,
            "name": name,
            "priority": priority,
            "equipment_list": equipment_list,
            "process_order": process_order,
            "lead_time_hours": lead_time
        }
        self.save_data("products", self.products)
    
    def update_product(self, product_id: str, **kwargs):
        """제품 정보 업데이트"""
        if product_id in self.products:
            self.products[product_id].update(kwargs)
            self.save_data("products", self.products)
    
    def delete_product(self, product_id: str):
        """제품 삭제"""
        if product_id in self.products:
            del self.products[product_id]
            self.save_data("products", self.products)
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """제품 정보 조회"""
        return self.products.get(product_id)
    
    # 공정 관련 메서드
    def add_process(self, process_id: str, name: str, order: int):
        """공정 추가"""
        self.processes[process_id] = {
            "id": process_id,
            "name": name,
            "order": order
        }
        self.save_data("processes", self.processes)
    
    def get_process_list(self) -> List[Dict]:
        """공정 목록 반환 (순서대로)"""
        return sorted(self.processes.values(), key=lambda x: x['order'])
    
    # 장비 관련 메서드
    def add_equipment(self, equipment_id: str, name: str, process_id: str,
                     available_products: List[str], requires_cleaning: bool,
                     restrictions: Optional[Dict] = None):
        """장비 추가"""
        self.equipment[equipment_id] = {
            "id": equipment_id,
            "name": name,
            "process_id": process_id,
            "available_products": available_products,
            "requires_cleaning": requires_cleaning,
            "restrictions": restrictions or {}
        }
        self.save_data("equipment", self.equipment)
    
    def get_equipment_by_process(self, process_id: str) -> List[Dict]:
        """특정 공정의 장비 목록 반환"""
        return [eq for eq in self.equipment.values() 
                if eq['process_id'] == process_id]
    
    def is_equipment_available(self, equipment_id: str, date: datetime) -> bool:
        """특정 날짜에 장비 사용 가능 여부 확인"""
        equipment = self.equipment.get(equipment_id)
        if not equipment:
            return False
        
        restrictions = equipment.get('restrictions', {})
        if not restrictions:
            return True
        
        # 제한 기간 확인
        start_date = restrictions.get('start_date')
        end_date = restrictions.get('end_date')
        
        if start_date and end_date:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            return not (start <= date <= end)
        
        return True
    
    # 작업자 관련 메서드
    def set_operator_capacity(self, process_id: str, date: str, 
                            worker_count: int, batches_per_worker: float = None):
        """작업자 용량 설정"""
        key = f"{process_id}_{date}"
        self.operators[key] = {
            "process_id": process_id,
            "date": date,
            "worker_count": worker_count
        }
        
        # 기존 방식과의 호환성 유지
        if batches_per_worker is not None:
            self.operators[key]["batches_per_worker"] = batches_per_worker
            self.operators[key]["total_capacity"] = worker_count * batches_per_worker
            
        self.save_data("operators", self.operators)
    
    def get_operator_capacity(self, process_id: str, date: str) -> float:
        """특정 공정/날짜의 작업자 용량 반환"""
        key = f"{process_id}_{date}"
        operator_data = self.operators.get(key)
        if operator_data:
            return operator_data['total_capacity']
        return 0.0
    
    def get_operator_info(self, process_id: str, date: str) -> Optional[Dict]:
        """특정 공정/날짜의 작업자 정보 반환"""
        key = f"{process_id}_{date}"
        return self.operators.get(key)
    
    def get_all_products_df(self) -> pd.DataFrame:
        """모든 제품 정보를 DataFrame으로 반환"""
        if not self.products:
            return pd.DataFrame()
        return pd.DataFrame.from_dict(self.products, orient='index')
    
    def get_all_equipment_df(self) -> pd.DataFrame:
        """모든 장비 정보를 DataFrame으로 반환"""
        if not self.equipment:
            return pd.DataFrame()
        return pd.DataFrame.from_dict(self.equipment, orient='index')