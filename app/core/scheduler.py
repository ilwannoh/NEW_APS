"""
APS 스케줄링 엔진
월별 판매계획을 일/공정 단위로 분할하고 최적화된 생산계획을 생성
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import uuid
from pulp import *

from app.models.master_data import MasterDataManager
from app.models.production_plan import ProductionPlan, Batch


class APSScheduler:
    """APS 스케줄링 엔진"""
    
    def __init__(self, master_data: MasterDataManager):
        self.master_data = master_data
        self.production_plan = ProductionPlan()
        self.daily_work_hours = 8  # 1일 근무시간 8시간
        
    def schedule_from_sales_plan(self, sales_plan_df: pd.DataFrame, 
                               start_date: datetime) -> ProductionPlan:
        """
        판매계획으로부터 생산계획 생성
        
        Args:
            sales_plan_df: 판매계획 DataFrame
            start_date: 생산 시작일
            
        Returns:
            ProductionPlan: 생성된 생산계획
        """
        # 새로운 형식인지 확인
        if '납기일' in sales_plan_df.columns:
            # 새로운 형식: 제품코드, 제품명, 제조번호, 수량, 납기일, 우선순위
            daily_demands = self._process_new_format(sales_plan_df)
        else:
            # 기존 형식: 월별 수요를 일별로 분할
            daily_demands = self._split_monthly_to_daily(sales_plan_df, start_date)
        
        # 제품 우선순위 정렬
        sorted_demands = self._sort_by_priority(daily_demands)
        
        # 스케줄링 실행
        self._run_scheduling(sorted_demands, start_date)
        
        return self.production_plan
    
    def _process_new_format(self, sales_plan_df: pd.DataFrame) -> Dict:
        """새로운 형식의 판매계획 처리"""
        daily_demands = {}
        
        for _, row in sales_plan_df.iterrows():
            product_code = str(row['제품코드'])
            product_name = row['제품명']
            lot_number = str(row['제조번호'])
            quantity = int(row['수량'])
            delivery_date = pd.to_datetime(row['납기일'])
            priority = row.get('우선순위', '보통')
            
            # 제품 정보 조회
            product = self.master_data.products.get(product_code)
            if not product:
                continue
            
            # 엑셀의 각 행을 하나의 배치로 처리 (중복 방지)
            batch_count = 1  # 항상 1개의 배치로 처리
            
            # 우선순위 매핑
            priority_map = {'긴급': 1, '높음': 2, '보통': 3, '낮음': 4}
            priority_value = priority_map.get(priority, 3)
            
            # 납기일 기준으로 역산하여 생산일 계산
            lead_time_hours = product.get('lead_time_hours', 24)
            production_date = delivery_date - timedelta(hours=lead_time_hours)
            
            # 날짜별 수요에 추가
            date_key = production_date.date()
            if date_key not in daily_demands:
                daily_demands[date_key] = []
            
            daily_demands[date_key].append({
                'product_id': product_code,
                'product_name': product_name,
                'lot_number': lot_number,
                'priority': priority_value,
                'batch_count': batch_count,
                'process_order': product['process_order'],
                'equipment_list': product['equipment_list'],
                'quantity': quantity
            })
        
        return daily_demands
    
    def _split_monthly_to_daily(self, sales_plan_df: pd.DataFrame, 
                              start_date: datetime) -> Dict:
        """월별 수요를 일별로 분할"""
        daily_demands = {}
        
        for _, row in sales_plan_df.iterrows():
            product_name = row['제품명']
            
            # 제품 정보 조회
            product = None
            for p in self.master_data.products.values():
                if p['name'] == product_name:
                    product = p
                    break
            
            if not product:
                continue
            
            # 월별 필요 배치수를 일별로 분할
            for month_col in sales_plan_df.columns:
                if '월' in month_col and pd.notna(row[month_col]):
                    month_num = int(month_col.replace('월', ''))
                    batches_needed = int(row[month_col])
                    
                    if batches_needed > 0:
                        # 해당 월의 영업일 계산
                        month_start = datetime(start_date.year, month_num, 1)
                        if month_num == 12:
                            month_end = datetime(start_date.year + 1, 1, 1) - timedelta(days=1)
                        else:
                            month_end = datetime(start_date.year, month_num + 1, 1) - timedelta(days=1)
                        
                        working_days = self._get_working_days(month_start, month_end)
                        
                        # 일별 배치수 계산
                        daily_batch = batches_needed / len(working_days)
                        
                        for day in working_days:
                            if day not in daily_demands:
                                daily_demands[day] = []
                            
                            daily_demands[day].append({
                                'product_id': product['id'],
                                'product_name': product['name'],
                                'priority': product['priority'],
                                'batch_count': daily_batch,
                                'process_order': product['process_order'],
                                'equipment_list': product['equipment_list']
                            })
        
        return daily_demands
    
    def _get_working_days(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """주말을 제외한 영업일 목록 반환"""
        working_days = []
        current = start_date
        
        while current <= end_date:
            # 주말 제외 (토요일: 5, 일요일: 6)
            if current.weekday() < 5:
                working_days.append(current)
            current += timedelta(days=1)
        
        return working_days
    
    def _sort_by_priority(self, daily_demands: Dict) -> Dict:
        """제품 우선순위별로 정렬"""
        sorted_demands = {}
        
        for date, demands in daily_demands.items():
            # 우선순위 높은 순으로 정렬 (숫자가 작을수록 우선순위 높음)
            sorted_demands[date] = sorted(demands, key=lambda x: x['priority'])
        
        return sorted_demands
    
    def _run_scheduling(self, daily_demands: Dict, start_date: datetime):
        """실제 스케줄링 실행 - 레고 블록 방식 (4구간)"""
        
        # 장비별 구간별 할당 관리
        slot_allocation = {}  # {(equipment_id, date, slot): occupied}
        
        # 제품-배치별 마지막 공정 완료 시간 추적
        batch_end_slots = {}  # {(product_id, batch_num, process_idx): (date, end_slot)}
        
        for date, demands in sorted(daily_demands.items()):
            for demand in demands:
                product_id = demand['product_id']
                product_name = demand['product_name']
                batch_count = int(np.ceil(demand['batch_count']))  # 올림 처리
                process_order = demand['process_order']
                equipment_list = demand['equipment_list']
                lot_number = demand.get('lot_number')  # 제조번호
                
                # 각 배치 스케줄링
                for batch_num in range(batch_count):
                    batch_id = str(uuid.uuid4())[:8]
                    
                    # 시작 날짜와 구간 설정
                    current_date = date if not isinstance(date, datetime) else date.date()
                    current_slot = 0  # 첫 구간부터 시작
                    
                    # 공정 순서대로 처리
                    for process_idx, process_id in enumerate(process_order):
                        # 이전 공정이 있으면 그 완료 다음 구간부터 시작
                        if process_idx > 0:
                            prev_key = (product_id, batch_num, process_idx - 1)
                            if prev_key in batch_end_slots:
                                # 이전 공정 완료 위치
                                prev_date, prev_end_slot = batch_end_slots[prev_key]
                                
                                # 다음 구간에서 시작
                                current_date = prev_date
                                current_slot = prev_end_slot + 1
                                
                                # 다음 날로 넘어가야 하는 경우
                                if current_slot >= 4:
                                    current_date = current_date + timedelta(days=1)
                                    current_slot = 0
                                
                                # 공정별 리드타임 적용
                                product = self.master_data.products.get(product_id, {})
                                process_leadtimes = product.get('process_leadtimes', {})
                                leadtime_days = process_leadtimes.get(process_id, 0)
                                
                                if leadtime_days > 0:
                                    current_date = current_date + timedelta(days=leadtime_days)
                                    current_slot = 0  # 리드타임 후 첫 구간부터
                        
                        # 공정별 장비 찾기
                        process_equipment = self.master_data.get_equipment_by_process(process_id)
                        if not process_equipment:
                            continue
                        
                        # 가용한 구간과 장비 찾기
                        scheduled = False
                        search_date = current_date
                        search_slot = current_slot
                        max_search_days = 30
                        
                        # 공정 소요시간을 구간 수로 변환 (2시간 = 1구간)
                        duration = self._get_process_duration(product_id, process_id)
                        duration_slots = max(1, int(duration / 2))
                        
                        # 날짜별로 검색
                        for day_offset in range(max_search_days):
                            check_date = search_date + timedelta(days=day_offset)
                            
                            # 주말 건너뛰기
                            if check_date.weekday() >= 5:
                                continue
                            
                            # 첫 날이 아니면 0구간부터 시작
                            start_slot = search_slot if day_offset == 0 else 0
                            
                            # 구간별로 검색
                            for slot in range(start_slot, 4):
                                # 남은 구간이 충분한지 확인
                                if slot + duration_slots > 4:
                                    break
                                
                                # 작업자 정보 확인
                                operator_info = self.master_data.get_operator_info(
                                    process_id, check_date.strftime('%Y-%m-%d')
                                )
                                
                                if not operator_info:
                                    continue
                                
                                # 장비별로 가용성 확인
                                for eq in process_equipment:
                                    if product_id not in eq['available_products']:
                                        continue
                                    
                                    # 해당 장비-구간이 비어있는지 확인
                                    can_schedule = True
                                    for s in range(duration_slots):
                                        slot_key = (eq['id'], check_date, slot + s)
                                        if slot_key in slot_allocation:
                                            can_schedule = False
                                            break
                                    
                                    if can_schedule:
                                        # 구간 기반 단순화 - 구간 번호를 그대로 시간으로 사용
                                        # 0구간=0시, 1구간=1시, 2구간=2시, 3구간=3시
                                        start_time = datetime.combine(check_date, datetime.min.time()).replace(hour=slot)
                                        
                                        # 배치 생성
                                        batch = Batch(
                                            batch_id=f"{batch_id}_{process_id}",
                                            product_id=product_id,
                                            product_name=product_name,
                                            equipment_id=eq['id'],
                                            start_time=start_time,
                                            duration_hours=duration,
                                            lot_number=lot_number
                                        )
                                        batch.process_id = process_id
                                        
                                        self.production_plan.add_batch(batch)
                                        
                                        # 구간 점유 표시
                                        for s in range(duration_slots):
                                            slot_key = (eq['id'], check_date, slot + s)
                                            slot_allocation[slot_key] = True
                                        
                                        # 완료 구간 저장
                                        end_slot = slot + duration_slots - 1
                                        batch_end_slots[(product_id, batch_num, process_idx)] = (check_date, end_slot)
                                        
                                        scheduled = True
                                        break
                                
                                if scheduled:
                                    break
                            
                            if scheduled:
                                break
    
    def _find_available_equipment(self, process_id: str, product_id: str,
                                preferred_equipment: List[str], 
                                start_time: datetime) -> Optional[str]:
        """가용 장비 찾기"""
        # 해당 공정의 모든 장비 조회
        process_equipment = self.master_data.get_equipment_by_process(process_id)
        
        # 선호 장비 우선 확인
        for eq in process_equipment:
            if eq['id'] in preferred_equipment:
                # 제품 생산 가능 여부 확인
                if product_id in eq['available_products']:
                    # 시간 중복 확인
                    duration = self._get_process_duration(product_id, process_id)
                    if not self.production_plan.check_overlap(
                        eq['id'], start_time, duration
                    ):
                        # 장비 가용성 확인
                        if self.master_data.is_equipment_available(eq['id'], start_time):
                            return eq['id']
        
        # 대체 장비 확인
        for eq in process_equipment:
            if product_id in eq['available_products']:
                duration = self._get_process_duration(product_id, process_id)
                if not self.production_plan.check_overlap(
                    eq['id'], start_time, duration
                ):
                    if self.master_data.is_equipment_available(eq['id'], start_time):
                        return eq['id']
        
        return None
    
    def _count_process_batches(self, process_id: str, date: datetime) -> int:
        """특정 공정의 당일 배치 수 계산"""
        count = 0
        batches = self.production_plan.get_batches_by_date(date)
        
        for batch in batches:
            if batch.process_id == process_id:
                count += 1
        
        return count
    
    def _get_process_duration(self, product_id: str, process_id: str) -> float:
        """제품별 공정 소요시간 가져오기"""
        # 제품 정보 가져오기
        product = self.master_data.products.get(product_id, {})
        
        # 제품별 커스텀 소요시간 확인
        if 'process_details' in product and process_id in product['process_details']:
            return product['process_details'][process_id].get('duration_hours', 8.0)
        
        # 공정 기본 소요시간 사용
        process = self.master_data.processes.get(process_id, {})
        return process.get('default_duration_hours', 8.0)
    
    # 복잡한 시간 기반 스케줄링 메서드들은 이제 사용하지 않음
    # 초안 수준의 단순한 일 단위 스케줄링으로 대체됨
    
    def _count_process_batches_at_time(self, process_id: str, check_time: datetime, 
                                       duration: float) -> int:
        """특정 시간대의 공정 배치 수 계산"""
        count = 0
        batches = self.production_plan.get_batches_by_date(check_time.date())
        
        check_end = check_time + timedelta(hours=duration)
        
        for batch in batches:
            if batch.process_id == process_id:
                batch_end = batch.start_time + timedelta(hours=batch.duration_hours)
                # 시간 중복 체크
                if not (batch_end <= check_time or batch.start_time >= check_end):
                    count += 1
        
        return count
    
    def optimize_schedule(self):
        """선형계획법을 사용한 스케줄 최적화"""
        # PuLP를 사용한 최적화 (추후 구현)
        # 현재는 휴리스틱 방식으로 스케줄링
        pass
    
    def add_cleaning_blocks(self):
        """제품 전환 시 세척 블록 추가 - 현재 비활성화"""
        # 세척 기능 임시 비활성화
        return
        
        # 추후 필요시 아래 코드 활성화
        # for equipment_id in self.production_plan.equipment_schedule:
        #     batches = self.production_plan.get_batches_by_equipment(equipment_id)
        #     ...
    
    def _shift_batches_after(self, equipment_id: str, after_time: datetime,
                           time_shift: timedelta):
        """특정 시간 이후의 배치들을 시간만큼 이동"""
        batches = self.production_plan.get_batches_by_equipment(equipment_id)
        
        for batch in batches:
            if batch.start_time >= after_time:
                batch.start_time += time_shift
                batch.end_time += time_shift