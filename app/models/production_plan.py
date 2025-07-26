"""
생산계획 데이터 모델
스케줄링 결과 및 배치 정보를 관리
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid


class Batch:
    """배치 정보를 나타내는 클래스"""
    
    def __init__(self, batch_id: str, product_id: str, product_name: str,
                 equipment_id: str, start_time: datetime, duration_hours: int = 8,
                 lot_number: str = None):
        self.id = batch_id
        self.product_id = product_id
        self.product_name = product_name
        self.equipment_id = equipment_id
        self.start_time = start_time
        self.duration_hours = duration_hours
        self.end_time = start_time + timedelta(hours=duration_hours)
        self.process_id = None
        self.is_cleaning = False
        self.lot_number = lot_number  # 제조번호 추가
        
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'batch_id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'equipment_id': self.equipment_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_hours': self.duration_hours,
            'process_id': self.process_id,
            'is_cleaning': self.is_cleaning,
            'lot_number': self.lot_number
        }


class ProductionPlan:
    """생산계획 전체를 관리하는 클래스"""
    
    def __init__(self):
        self.batches = {}  # batch_id -> Batch
        self.equipment_schedule = {}  # equipment_id -> List[batch_id]
        self.date_range = None
        self._df = None  # 캐시된 DataFrame
        
    def add_batch(self, batch: Batch):
        """배치 추가"""
        self.batches[batch.id] = batch
        
        # 장비 스케줄에 추가
        if batch.equipment_id not in self.equipment_schedule:
            self.equipment_schedule[batch.equipment_id] = []
        self.equipment_schedule[batch.equipment_id].append(batch.id)
        
        # DataFrame 캐시 무효화
        self._df = None
    
    def remove_batch(self, batch_id: str):
        """배치 제거"""
        if batch_id in self.batches:
            batch = self.batches[batch_id]
            
            # 장비 스케줄에서 제거
            if batch.equipment_id in self.equipment_schedule:
                self.equipment_schedule[batch.equipment_id].remove(batch_id)
            
            del self.batches[batch_id]
            self._df = None
    
    def move_batch(self, batch_id: str, new_equipment_id: str, new_start_time: datetime):
        """배치 이동"""
        if batch_id not in self.batches:
            return False
        
        batch = self.batches[batch_id]
        old_equipment_id = batch.equipment_id
        
        # 기존 장비 스케줄에서 제거
        if old_equipment_id in self.equipment_schedule:
            self.equipment_schedule[old_equipment_id].remove(batch_id)
        
        # 새 장비와 시간으로 업데이트
        batch.equipment_id = new_equipment_id
        batch.start_time = new_start_time
        batch.end_time = new_start_time + timedelta(hours=batch.duration_hours)
        
        # 새 장비 스케줄에 추가
        if new_equipment_id not in self.equipment_schedule:
            self.equipment_schedule[new_equipment_id] = []
        self.equipment_schedule[new_equipment_id].append(batch_id)
        
        self._df = None
        return True
    
    def get_batches_by_equipment(self, equipment_id: str) -> List[Batch]:
        """특정 장비의 배치 목록 반환 (시간순)"""
        batch_ids = self.equipment_schedule.get(equipment_id, [])
        batches = [self.batches[bid] for bid in batch_ids if bid in self.batches]
        return sorted(batches, key=lambda b: b.start_time)
    
    def get_batches_by_date(self, date) -> List[Batch]:
        """특정 날짜의 배치 목록 반환"""
        if isinstance(date, datetime):
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # date 객체인 경우
            date_start = datetime.combine(date, datetime.min.time())
        date_end = date_start + timedelta(days=1)
        
        batches = []
        for batch in self.batches.values():
            if date_start <= batch.start_time < date_end:
                batches.append(batch)
        
        return sorted(batches, key=lambda b: (b.equipment_id, b.start_time))
    
    def check_overlap(self, equipment_id: str, start_time: datetime, 
                     duration_hours: int, exclude_batch_id: Optional[str] = None) -> bool:
        """시간 중복 확인"""
        end_time = start_time + timedelta(hours=duration_hours)
        
        for batch_id in self.equipment_schedule.get(equipment_id, []):
            if batch_id == exclude_batch_id:
                continue
                
            batch = self.batches.get(batch_id)
            if batch:
                # 시간 중복 확인
                if not (end_time <= batch.start_time or start_time >= batch.end_time):
                    return True
        
        return False
    
    def to_dataframe(self) -> pd.DataFrame:
        """DataFrame으로 변환"""
        if self._df is not None:
            return self._df
        
        if not self.batches:
            return pd.DataFrame()
        
        data = []
        for batch in self.batches.values():
            data.append({
                'batch_id': batch.id,
                'date': batch.start_time.date(),
                'equipment_id': batch.equipment_id,
                'product_id': batch.product_id,
                'product_name': batch.product_name,
                'start_time': batch.start_time,
                'end_time': batch.end_time,
                'duration_hours': batch.duration_hours,
                'process_id': batch.process_id,
                'is_cleaning': batch.is_cleaning,
                'lot_number': batch.lot_number
            })
        
        self._df = pd.DataFrame(data)
        return self._df
    
    def to_grid_format(self) -> pd.DataFrame:
        """그리드 뷰용 포맷으로 변환"""
        if not self.batches:
            return pd.DataFrame()
        
        # 날짜 범위 확인
        all_dates = [b.start_time.date() for b in self.batches.values()]
        if not all_dates:
            return pd.DataFrame()
        
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        # 날짜 리스트 생성
        date_list = []
        current_date = min_date
        while current_date <= max_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        
        # 장비 리스트
        equipment_list = sorted(self.equipment_schedule.keys())
        
        # 그리드 데이터 생성
        grid_data = {}
        for equipment_id in equipment_list:
            grid_data[equipment_id] = {}
            for date in date_list:
                grid_data[equipment_id][date.strftime('%Y-%m-%d')] = []
        
        # 배치 정보 채우기
        for batch in self.batches.values():
            date_str = batch.start_time.date().strftime('%Y-%m-%d')
            if batch.equipment_id in grid_data and date_str in grid_data[batch.equipment_id]:
                batch_info = f"{batch.product_name[:3]},B{batch.id[:4]}"
                grid_data[batch.equipment_id][date_str].append(batch_info)
        
        # DataFrame으로 변환
        df = pd.DataFrame.from_dict(grid_data, orient='index')
        df.index.name = 'Equipment'
        
        return df
    
    def export_to_csv(self, file_path: str):
        """CSV 파일로 내보내기"""
        df = self.to_dataframe()
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    def export_to_xml(self, file_path: str):
        """XML 파일로 내보내기"""
        df = self.to_dataframe()
        df.to_xml(file_path, index=False, encoding='utf-8')
    
    def get_production_summary(self) -> Dict:
        """생산 요약 정보 반환"""
        if not self.batches:
            return {
                'total_batches': 0,
                'products': {},
                'equipment_utilization': {},
                'date_range': None
            }
        
        # 제품별 배치 수
        products = {}
        for batch in self.batches.values():
            if batch.product_id not in products:
                products[batch.product_id] = {
                    'name': batch.product_name,
                    'count': 0
                }
            products[batch.product_id]['count'] += 1
        
        # 장비 가동률
        equipment_util = {}
        for eq_id, batch_ids in self.equipment_schedule.items():
            total_hours = sum(self.batches[bid].duration_hours 
                            for bid in batch_ids if bid in self.batches)
            equipment_util[eq_id] = {
                'total_hours': total_hours,
                'batch_count': len(batch_ids)
            }
        
        # 날짜 범위
        all_dates = [b.start_time for b in self.batches.values()]
        date_range = {
            'start': min(all_dates),
            'end': max(all_dates)
        }
        
        return {
            'total_batches': len(self.batches),
            'products': products,
            'equipment_utilization': equipment_util,
            'date_range': date_range
        }