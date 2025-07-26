import os
import pandas as pd
from app.models.common.file_store import DataStore, FilePaths
from app.analysis.output.capa_ratio import CapaRatioAnalyzer
from app.utils.conversion import convert_value
from app.utils.item_key_manager import ItemKeyManager

"""
결과 조정 시 제약사항 점검 클래스

- 라인과 아이템 호환성
- 라인 시프트별 용량 제약
- 납기일 준수 여부
- 요일별 가동률 제약
- 제조동 비율 제약
"""
class PlanAdjustmentValidator:
    """
    validator 초기화
    
    Args:
        result_data (DataFrame): 현재 생산 계획 결과 데이터
    """
    def __init__(self, result_data ,result_page = None):
        self.result_data = result_data
        self.result_page = result_page
         # 1. 먼저 DataStore에서 organized_dataframes 조회
        organized = DataStore.get("organized_dataframes", {})

        # 2. master 데이터 로딩
        self.master_data = organized.get("master", {})
        if not self.master_data:  # 없으면 FilePaths로 시도
            master_path = FilePaths.get("master_excel_file")
            if master_path and os.path.exists(master_path):
                try:
                    self.master_data = {
                        "capa_qty": pd.read_excel(master_path, sheet_name="capa_qty"),
                        "line_available": pd.read_excel(master_path, sheet_name="line_available"),
                        "capa_portion": pd.read_excel(master_path, sheet_name="capa_portion"),
                        "due_LT" : pd.read_excel(master_path, sheet_name="due_LT")
                        # 필요한 시트가 더 있다면 여기에 추가
                    }
                    print(f"[로드] master 파일에서 데이터 로드: {master_path}")
                except Exception as e:
                    print(f"[오류] master 파일 로드 실패: {e}")
            else:
                print(f"[경고] master 파일 경로가 유효하지 않음")

        # 3. demand 데이터 로딩
        self.demand_data = organized.get("demand", {})
        if not self.demand_data:
            demand_path = FilePaths.get("demand_excel_file")
            if demand_path and os.path.exists(demand_path):
                try:
                    self.demand_data = {
                        "demand": pd.read_excel(demand_path, sheet_name="demand"),
                    }
                    print(f"[로드] demand 파일에서 데이터 로드: {demand_path}")
                except Exception as e:
                    print(f"[오류] demand 파일 로드 실패: {e}")
            else:
                print(f"[경고] demand 파일 경로가 유효하지 않음")

        self.capa_qty_data = self.master_data.get("capa_qty", pd.DataFrame())

        # 제약사항 추출 및 캐싱
        self._extract_constraints()
        self._cache_reference_data()


    """
    마스터 데이터에서 각종 제약사항 추출하여 메모리에 캐싱

    - line_capacities: 라인 및 시프트별 용량
    - due_dates: 아이템/프로젝트별 납기일
    - building_constraints: 제조동별 상/하한 비율
    - line_item_compatibility: 라인-아이템 호환성
    """
    def _extract_constraints(self):
        # 초기화
        self.line_capacities = {}    # 라임 및 shift별 용량
        self.due_dates = {}          # 아이템/프로젝트별 납기일
        self.building_constraints = {}  # 제조동 제약
        self.line_item_compatibility = {}  # 라인-아이템 호환성

        # capa_qty 시트에서 라인 용량 추출
        if 'capa_qty' in self.master_data:
            df_capa_qty = self.master_data['capa_qty']
            for _, row in df_capa_qty.iterrows():
                if 'Line' in row:
                    line = row['Line']
                    self.line_capacities[line] = {}

                    # shift별 용량 추출
                    for col in df_capa_qty.columns:
                        if isinstance(col, (int, str)) and col not in ['Line', 'Capacity']:
                            try:
                                time = int(col) if isinstance(col, str) else col
                                self.line_capacities[line][time] = row[col]
                            except (ValueError, TypeError):
                                pass

        # line_available 시트에서 라인 가용성 추출
        if 'line_available' in self.master_data:
            df_line_available = self.master_data['line_available']
            for _, row in df_line_available.iterrows():
                if 'Project' in row:
                    project = row['Project']
                    self.line_item_compatibility[project] = []

                    for col in df_line_available.columns:
                        if col != 'Project' and row[col] == 1:
                            self.line_item_compatibility[project].append(col)

        # 납기일 추출
        if 'due_LT' in self.master_data:
            df_due_lt = self.master_data['due_LT']
            for _, row in df_due_lt.iterrows():
                # 프로젝트별 납기일 추출
                if 'Project' in row and 'Due_date_LT' in row:
                    project = row['Project']
                    due_date = row['Due_date_LT']
                    if project not in self.due_dates:
                        self.due_dates[project] = due_date

         # capa_portion 시트에서 제조동 비율 제약 추출
        if 'capa_portion' in self.master_data:
            df_portion = self.master_data['capa_portion']
            if not df_portion.empty and 'name' in df_portion.columns:
                for _, row in df_portion.iterrows():
                    if 'name' in row and 'lower_limit' in row and 'upper_limit' in row:
                        building = row['name']
                        self.building_constraints[building] = {
                            'lower_limit': convert_value(row['lower_limit'], float, 0.0),
                            'upper_limit': convert_value(row['upper_limit'], float, 0.0)
                        }


    """
    현재 결과 데이터에서 참조 정보 추출하여 캐싱
    - 라인별 시프트별 현재 할당량
    - 라인별 사용 가능한 아이템 목록
    """
    def _cache_reference_data(self):
        if self.result_data is None or self.result_data.empty:
            return

        # 라인별 시프트별 현재 할당량 계산
        self.line_shift_allocation = {}

        # 라인별 사용 가능한 아이템 목록 캐싱
        self.line_available_items = self.result_data.groupby('Line')['Item'].apply(set).to_dict()
        

    """
    현재 결과 데이터를 capaValidator 형식으로 변환
    
    Returns:
        dict: capaValidator에 사용할 데이터 구조
    """
    def _prepare_data_for_validator(self):
        # 결과 데이터를 capaValidator 형식으로 변환
        processed_data = {
            'demand_items': [],
            'project_to_buildings': {},
            'building_constraints': self.building_constraints,
            'line_available_df': self.master_data.get('line_available', pd.DataFrame()),
            'capa_qty_df': self.master_data.get('capa_qty', pd.DataFrame())
        }

        # 결과 데이터를 demand_items 형식으로 변환
        for _, row in self.result_data.iterrows():
            item_dict = {
                'Item': row.get('Item', ''),
                'MFG': row.get('Qty', 0),
                'Project': row.get('Project', ''),
                'RMC': row.get('RMC', '')
            }

            # Item에서 Project, Basic2, Tosite_group 추출
            if 'Item' in item_dict and item_dict['Item']:
                item = item_dict['Item']
                if len(item) >= 7:
                    if not item_dict.get('Project'):
                        item_dict['Project'] = item[3:7]
                    item_dict['Basic2'] = item[3:8] if len(item) >= 8 else item[3:7]
                    item_dict['Tosite_group'] = item[7:8] if len(item) >= 8 else ''
                    item_dict['RMC'] = item[3:-3] if len(item) >= 7 else ''
            
            processed_data['demand_items'].append(item_dict)

        # project_to_buildings 설정 (프로젝트별 생산 가능 제조동)
        if 'line_available' in self.master_data:
            df_line_available = self.master_data['line_available']
            if not df_line_available.empty and 'Project' in df_line_available.columns:
                # 라인 코드에서 제조동 추출
                for _, row in df_line_available.iterrows():
                    project = row['Project']
                    project_buildings = []
                    
                    for col in df_line_available.columns:
                        if col != 'Project' and row[col] == 1 and len(col) > 0:
                            building = col[0]  # 라인 코드의 첫 글자 (예: 'I'_01 -> 'I')
                            if building not in project_buildings:
                                project_buildings.append(building)
                    
                    processed_data['project_to_buildings'][project] = project_buildings
                    
                    # Basic2 기반으로도 매핑
                    for item_dict in processed_data['demand_items']:
                        if 'Basic2' in item_dict and item_dict['Basic2'].startswith(project):
                            processed_data['project_to_buildings'][item_dict['Basic2']] = project_buildings
        
        return processed_data


    """
    라인과 아이템의 호환성 검증
    
    Args:
        line (str): 라인 코드
        item (str): 아이템 코드
        
    Returns:
        tuple: (성공 여부, 오류 메시지)
    """
    def validate_line_item_compatibility(self, line, item):
        # 아이템 코드에서 프로젝트 추출 
        project = item[3:7] if len(item) >= 7 else ""
        
        # 마스터 데이터의 호환성 정보 확인
        if project in self.line_item_compatibility:
            compatible_lines = self.line_item_compatibility[project]
            if line not in compatible_lines:
                return False, f"Item '{item}' (Project {project}) cannot be produced on line '{line}'."
            return True, ""
        
        # 마스터 데이터가 없으면 결과 데이터에서 추론
        if line in self.line_available_items:
            # 이미 해당 라인에 할당된 적이 있는 아이템이면 호환 가능
            if item in self.line_available_items[line]:
                return True, ""
                
            # 아니라면 아이템 프로젝트 코드 비교 (추가 검증)
            for existing_item in self.line_available_items[line]:
                existing_project = existing_item[3:7] if len(existing_item) >= 7 else ""
                if project == existing_project:
                    # 같은 프로젝트의 아이템이 이미 있으면 호환 가능
                    return True, ""
        
        # 마스터 데이터도 없고 결과 데이터에서도 확인 불가능한 경우 기본 통과
        return True, ""
    
    
    """
    라인과 시프트의 용량 초과 여부 검증
    
    Args:
        line (str): 라인 코드
        time (int): 시프트 번호
        new_qty (int): 추가할 생산량
        item (str, optional): 아이템 코드 (이동인 경우)
        is_move (bool): 이동 여부 플래그
        
    Returns:
        tuple: (성공 여부, 오류 메시지)
    """
    def validate_capacity(self, line, time, new_qty, item=None, is_move=False, item_id=None):
        # 현재 데이터 갱신
        self.result_data = self.result_page.left_section.data
        
        # 현재 라인-시프트의 총 할당량 계산
        grouped_data = self.result_data.groupby(['Line', 'Time'])['Qty'].sum()
        self.line_shift_allocation = {f"{line}_{time}": qty for (line, time), qty in grouped_data.items()}
        
        # 라인-시프트 키 생성
        key = f"{line}_{time}"
        
        # 시프트의 현재 할당량 확인
        current_allocation = self.line_shift_allocation.get(key, 0)
        
        # 같은 위치에서 수량만 변경인 경우 기존 할당량 제외
        existing_qty = 0
        if not is_move and item:
            # ID가 있으면 ID로 마스크 생성, 없으면 Line/Time/Item으로 마스크 생성
            if item_id:
                mask = ItemKeyManager.create_mask_by_id(self.result_data, item_id)
            else:
                mask = ItemKeyManager.create_mask_for_item(self.result_data, line, time, item)
                
            if mask.any():
                existing_qty = self.result_data.loc[mask, 'Qty'].iloc[0]
                current_allocation -= existing_qty
            else:
                print(f"해당 아이템을 찾을 수 없음 (수량 변경)")
        
        # 이동인 경우 해당 아이템의 기존 할당량 제외
        if is_move and item:
            
            if item_id:
                # ID로 원래 위치의 아이템 찾기
                mask = ItemKeyManager.create_mask_by_id(self.result_data, item_id)
                if mask.any():
                    original_row = self.result_data.loc[mask].iloc[0]
                    original_qty = original_row['Qty']
                    original_line = original_row['Line']
                    original_time = original_row['Time']
                    
                    # 원래 위치와 목표 위치가 다른 경우
                    if str(original_line) != str(line) or int(original_time) != int(time):
                        print(f"다른 위치로 이동: 목표 위치의 현재 할당량에서 제외하지 않음")
                        # 목표 위치의 할당량은 그대로 유지
                    else:
                        # 같은 위치 내에서의 이동 (순서 변경 등)
                        current_allocation -= original_qty
                        print(f"같은 위치 내 이동: 기존 수량 {original_qty} 제외, 조정된 할당량: {current_allocation}")
                else:
                    # ID로 찾지 못한 경우, Line/Time/Item으로 재시도
                    print(f"Line/Time/Item으로 재시도")
                    mask = ItemKeyManager.create_mask_for_item(self.result_data, line, time, item)
                    print(f"Line/Time/Item 마스크 결과: {mask.sum()}개 매칭")
                    if mask.any():
                        existing_qty = self.result_data.loc[mask, 'Qty'].iloc[0]
                        current_allocation -= existing_qty
                        print(f"기존 수량 {existing_qty} 제외, 조정된 할당량: {current_allocation}")
                    else:
                        print(f"Line/Time/Item으로도 찾을 수 없음")
            else:
                # ID가 없는 경우 기존 로직 (하위 호환성)
                print(f"ID 없이 이동하는 아이템 검색")
                mask = ItemKeyManager.create_mask_for_item(self.result_data, line, time, item)
                if mask.any():
                    existing_qty = self.result_data.loc[mask, 'Qty'].iloc[0]
                    current_allocation -= existing_qty
                    print(f"기존 수량 {existing_qty} 제외, 조정된 할당량: {current_allocation}")
                else:
                    print(f"해당 아이템을 찾을 수 없음 (이동, ID없음)")

        # 마스터 데이터에서 라인과 시프트 용량 가져오기
        capacity = self.get_line_capacity(line, time)
        
        # 용량 검증
        if capacity is not None:  # 용량 정보가 있는 경우만 검증
            # 생산 능력이 명시적으로 0인 경우 
            if capacity <= 0:
                print(f"❌ 용량 0: 생산 불가")
                return False, f"No capacity: line {line}, shift {time}."
                
            # 용량이 양수이고 할당량이 용량을 초과하는 경우
            elif current_allocation + new_qty > capacity:
                print(f"❌ 용량 초과: {current_allocation + new_qty} > {capacity}")
                return False, f"Over capacity({capacity}): line {line}, shift {time}. Current: {current_allocation}, Adding: {new_qty}, Total: {current_allocation + new_qty}"
            else:
                print(f"✅ 용량 내: {current_allocation + new_qty} <= {capacity}")
        else:
            print(f"⚠️ 용량 정보 없음: 제약 없음으로 처리")
        
        # 용량 정보가 없는 경우 (None) - 제약 없음으로 간주
        return True, ""
    
    
    """
    납기일 준수 여부 검증
    
    Args:
        item (str): 아이템 코드
        time (int): 시프트 번호
        
    Returns:
        tuple: (성공 여부, 오류 메시지)
    """
    def validate_due_date(self, item, time):
        # 아이템 또는 프로젝트의 납기일 확인
        due_time = None
        item_project = item[3:7] if len(item) >= 7 else ""
        print("validate_due_date",self.due_dates)
        
        # 직접 아이템에 대한 납기일 확인
        if item in self.due_dates:
            due_time = self.due_dates[item]
        # 프로젝트에 대한 납기일 확인
        elif item_project in self.due_dates:
            due_time = self.due_dates[item_project]

        # 납기일 검증
        if due_time is not None and time > due_time:
            return False, f"Item {item} past due: shift {due_time}."
            
        return True, ""
    
    
    """
    요일별/시프트별 가동률 제약 검증
    
    Args:
        line (str): 라인 코드
        time (int): 시프트 번호
        new_qty (int): 추가할 생산량
        
    Returns:
        tuple: (성공 여부, 오류 메시지)
    """
    def validate_utilization_rate(self, line, time, item, new_qty, item_id=None):
        # 시프트별 최대 가동률 설정 
        max_utilization_by_shift = {
            1: 100, 2: 100, 3: 100,  4: 100,  5: 100,  6: 100,
            7: 100,  8: 100,  9: 100, 10: 100, 11: 100, 12: 100, 13: 100, 14: 100, 
        }

        # 1. 해당 라인/시프트의 전체 현재 할당량 가져오기 (이동하는 라인/시프트)
        current_total_allocation = self.get_current_allocation(line=line, time=time)

        # 2. 해당 아이템의 현재 위치에서의 기존 수량 (같은 아이템이 있을 수 있음.)
        existing_item_qty = self.get_item_qty_at_position(line, time, item)

        # 3. 라인 용량 조회 (이동하는 라인/시프트) 
        line_capacity = self.get_line_capacity(line, time)
        
        # 생산 능력이 0인 경우 
        if line_capacity is not None and line_capacity <= 0:
            return False, f"No capacity: line {line}, shift {time}."

        # 용량 정보가 없는 경우 (None) - 제약 없음
        if line_capacity is None:
            return True, ""
    
        # 4. 새로운 총 할당량 계산
        new_total_allocation = current_total_allocation - existing_item_qty
        
        # 5. 가동률 계산
        utilization_rate = (new_total_allocation / line_capacity) * 100
        
        # 6. 최대 가동률 검증
        max_rate = max_utilization_by_shift.get(int(time), 100)
        
        if utilization_rate > max_rate:
            return False, f"Over utilization: shift {time}."
        
        return True, ""
    

    """
    모든 검증 로직을 통합 실행 - 외부 호출용 메인 함수
    
    Args:
        line (str): 목표 라인 코드
        time (int/str): 목표 시프트 번호
        item (str): 아이템 코드
        new_qty (int/str): 새 생산량
        source_line (str, optional): 이동 시 원래 라인
        source_time (int/str, optional): 이동 시 원래 시프트
        
    Returns:
        tuple: (성공 여부, 오류 메시지)
    """
    def validate_adjustment(self, line, time, item, new_qty, source_line=None, source_time=None, item_id=None):
        # 이동 여부 확인
        is_move = source_line is not None and source_time is not None

        # 기존 수량 조회 (현재 위치에서)
        old_qty = self.get_item_qty_at_position(line, time, item, item_id)

        # 타입 변환 (문자열 -> 숫자)
        time = convert_value(time, int, None)
        new_qty = convert_value(new_qty, int, 0, special_values={'ALL'})
        source_time = convert_value(source_time, int, None) if source_time is not None else None

        # 필수값 검증
        if line is None or time is None or item is None:
            return False, "Missing data."
        
        if new_qty == 'ALL' or new_qty == 'All':
            # 해당 아이템의 전체 수량 가져오기
            new_qty = self._get_total_demand_for_item(item)
            if new_qty <= 0:
                return False, f"No qty for item {item}."
            
        # 각 제약 요소 검증
        validations = [
            self.validate_due_date(item, time),
            self.validate_line_item_compatibility(line, item),
            self.validate_capacity(line, time, new_qty, item, is_move, item_id),
            self.validate_utilization_rate(line, time, item, new_qty, item_id),
            self.validate_building_ratios()  
        ]

        # 개별 검증 결과 확인
        for valid, message in validations:
            if not valid: 
                return False, message
   
        if not valid:
            return False, message
        
        return True, ""

    
    """
    특정 라인과 시프트의 생산 용량을 반환
    
    Args:
        line (str): 라인 코드 
        time (int or str): 시프트 번호 
        
    Returns:
        int or None: 해당 라인과 시프트의 생산 용량, 없으면 None
    """
    def get_line_capacity(self, line, time):
        # 이미 캐싱된 capa_qty_data 사용
        if self.capa_qty_data is None or self.capa_qty_data.empty:
            print("capa_qty 데이터가 비어 있습니다.")
            return None

        try:
            # 핵심 수정: 제조동 제약을 가장 먼저 확인 (CapaUtilization과 동일하게)
            if len(line) >= 1:
                factory = line[0]  # 라인 코드의 첫 글자 (예: 'I'_01 -> 'I')
                
                # 1. Max_line 제약 확인 - 최우선 체크
                max_line_key = f'Max_line_{factory}'
                max_line_rows = self.capa_qty_data[self.capa_qty_data['Line'] == max_line_key]
                
                if not max_line_rows.empty and time in max_line_rows.columns:
                    max_line = max_line_rows.iloc[0][time]
                    
                    # NaN 처리 및 타입 변환
                    if pd.notna(max_line):
                        try:
                            max_line = float(max_line)
                            if max_line == 0:
                                print(f"[DEBUG] ❌ 제조동 {factory}의 Max_line이 0 → 모든 라인 사용 불가")
                                return 0
                        except (ValueError, TypeError):
                            print(f"[DEBUG] Max_line 변환 실패, 제약 무시")
                            # 변환 실패 시 제약 없음으로 처리
                    else:
                        print(f"[DEBUG] Max_line이 NaN이므로 제약 없음")
                
                # 2. Max_qty 제약 확인 - 최우선 체크
                max_qty_key = f'Max_qty_{factory}'
                max_qty_rows = self.capa_qty_data[self.capa_qty_data['Line'] == max_qty_key]
                
                if not max_qty_rows.empty and time in max_qty_rows.columns:
                    max_qty = max_qty_rows.iloc[0][time]
                    
                    # 안전한 NaN 처리 및 타입 변환
                    if pd.notna(max_qty):
                        try:
                            max_qty = float(max_qty)
                            if max_qty == 0:
                                print(f"[DEBUG] ❌ 제조동 {factory}의 Max_qty가 0 → 모든 라인 사용 불가")
                                return 0
                        except (ValueError, TypeError):
                            print(f"[DEBUG] Max_qty 변환 실패, 제약 무시")
                            # 변환 실패 시 제약 없음으로 처리
                    else:
                        print(f"[DEBUG] Max_qty가 NaN이므로 제약 없음")

            # 개별 라인의 기본 용량 확인
            basic_capacity = None
            if 'Line' in self.capa_qty_data.columns and time in self.capa_qty_data.columns:
                line_rows = self.capa_qty_data[self.capa_qty_data['Line'] == line]
                if not line_rows.empty:
                    capacity = line_rows.iloc[0][time]
                    if pd.notna(capacity):
                        basic_capacity = float(capacity)

            # 기본 용량이 없으면 None 반환
            if basic_capacity is None:
                print(f"[DEBUG] 개별 라인 용량 정보 없음 → None 반환")
                return None
            
            # 3. 추가 제조동 제약 적용 (라인 수 제한 및 수량 제한)
            if len(line) >= 1:
                factory = line[0]  # 라인 코드의 첫 글자 ('I'_01 -> 'I')
                
                # 3-1. Max_line 제약: 사용 가능한 라인 수 제한
                max_line_key = f'Max_line_{factory}'
                max_line_rows = self.capa_qty_data[self.capa_qty_data['Line'] == max_line_key]
                
                if not max_line_rows.empty and time in max_line_rows.columns:
                    max_line = max_line_rows.iloc[0][time]
        

                    # NaN이 아니고 유효한 경우만 라인 수 제한 적용
                    if pd.notna(max_line):
                        max_line_float = float(max_line)
                        
                        # 양수인 경우만 라인 수 제한 적용
                        if max_line_float > 0:
                            max_line_int = int(max_line_float)
                
                        # 해당 제조동의 모든 라인 찾기
                        factory_lines = self.capa_qty_data[
                            self.capa_qty_data['Line'].str.startswith(f'{factory}_', na=False)
                        ]
                    
                        # 생산능력 기준으로 라인 정렬 (내림차순)
                        line_capacities = []
                        for l_idx, l_row in factory_lines.iterrows():
                            l_name = l_row['Line']
                            if time in self.capa_qty_data.columns:
                                capacity = self.capa_qty_data.loc[l_idx, time]
                                if pd.notna(capacity):
                                    line_capacities.append((l_name, float(capacity)))
                        
                        line_capacities.sort(key=lambda x: x[1], reverse=True)
                
                        # 상위 N개 라인만 사용 가능
                        if max_line_int > 0 and len(line_capacities) > 0:
                            # 범위를 벗어나지 않도록 안전하게 슬라이싱
                            slice_end = min(max_line_int, len(line_capacities))
                            usable_lines = [l for l, _ in line_capacities[:slice_end]]
                        
                        # 현재 라인이 사용 가능한 라인 목록에 없으면 용량 0 반환
                        if line not in usable_lines:
                            print(f"[DEBUG] ❌ 라인 {line}이 사용 가능 목록에 없음 → 용량 0 반환")
                            return 0
                
                # 3-2. Max_qty 제약: 제조동 전체 수량 제한
                max_qty_key = f'Max_qty_{factory}'
                max_qty_rows = self.capa_qty_data[self.capa_qty_data['Line'] == f'Max_qty_{factory}']
                
                if not max_qty_rows.empty and time in max_qty_rows.columns:
                    max_qty = max_qty_rows.iloc[0][time]

                    if pd.notna(max_qty) and max_qty != float('inf'):
                        # 현재 제조동 할당량 계산
                        current_factory_allocation = self.get_factory_allocation(factory, time)
                        
                        # 남은 용량 계산
                        remaining_capacity = max(0, float(max_qty) - current_factory_allocation)
                        
                        # 개별 라인 용량과 제조동 남은 용량 중 최소값
                        final_capacity = min(basic_capacity, remaining_capacity)
                        return final_capacity
                    
            # 제조동 제약이 없거나 적용되지 않는 경우 기본 용량 반환
            return basic_capacity
        
        except Exception as e:
            print(f"라인 용량 확인 중 오류 발생: {str(e)}")
        
            # 용량 정보를 찾지 못한 경우
            return None

    """
    특정 제조동의 현재 생산 할당량을 계산
    
    Args:
        factory (str): 제조동 코드 (예: 'I', 'D', 'K', 'M')
        time (int or str): 시프트 번호
        
    Returns:
        float: 현재 할당된 생산량
    """
    def get_factory_allocation(self, factory, time):
        return self.get_current_allocation(factory=factory, time=time)
    
    def get_existing_qty(self, line, time):
        return self.get_current_allocation(line=line, time=time)


    """
    현재 할당량을 계산하는 통합 함수
    
    Args:
        line: 특정 라인의 할당량 (line + time)
        time: 시프트 번호
        item: 특정 아이템의 할당량 (line + time + item)
        factory: 제조동 전체 할당량 (factory + time)
    """
    def get_current_allocation(self, line=None, time=None, item=None, factory=None, item_id=None):
        # 0. ID 기준 할당량 조회 (ID로 아이템 검색)
        if item_id:
            mask = ItemKeyManager.create_mask_by_id(self.result_data, item_id)
            if mask.any():
                if time is not None:  # 시간 조건도 확인
                    mask = mask & (self.result_data['Time'] == time)
                return float(self.result_data.loc[mask, 'Qty'].sum())

        # 1. 특정 아이템의 할당량
        if line and time and item:
            mask = ItemKeyManager.create_mask_for_item(self.result_data, line, time, item)
            matched = self.result_data[mask]
            return float(matched.iloc[0]['Qty']) if not matched.empty else 0
        
        # 2. 특정 라인-시프트의 총 할당량
        elif line and time:
            mask = (
                (self.result_data['Line'] == line) &
                (self.result_data['Time'] == time)
            )
            return self.result_data[mask]['Qty'].sum()
        
        # 3. 제조동 전체의 할당량
        elif factory and time:
            mask = (
                self.result_data['Line'].str.startswith(f'{factory}_', na=False) &
                (self.result_data['Time'] == time)
            )
            return self.result_data[mask]['Qty'].sum()
        
        return 0
    

    """
    특정 라인/시프느에서 특정 아이템의 수량 조회
    """
    def get_item_qty_at_position(self, line, time, item, item_id=None):
        try:
            # ID가 있으면 ID로 마스크 생성
            if item_id:
                mask = ItemKeyManager.create_mask_by_id(self.result_data, item_id)
                # 라인/시프트 조건 추가
                if line is not None and time is not None:
                    mask = mask & (
                        (self.result_data['Line'] == str(line)) &
                        (self.result_data['Time'] == int(time))
                    )
            else:
                # Line/Time/Item으로 마스크 생성
                mask = ItemKeyManager.create_mask_for_item(self.result_data, line, time, item)

            matched_rows = self.result_data[mask]

            if not matched_rows.empty:
                qty = matched_rows.iloc[0]['Qty']
                return float(qty)
            else:
                return 0

        except Exception as e:
            print(f"[ERROR] get_item_qty_at_position 오류: {e}")
            return 0

    """
    제조동별 생산량 비율 제약 검증
    
    Args:
        result_data (DataFrame, optional): 검증할 데이터
        
    Returns:
        tuple: (성공 여부, 오류 메시지)
    """
    def validate_building_ratios(self, result_data=None):
        data_df = self.result_data

        building_ratios = CapaRatioAnalyzer.analyze_capa_ratio(
            data_df=data_df,
            is_initial=True
        )
    
        if not building_ratios:
            return True, "No data."
        
        violations = []

        # 각 제조동 별 비율이 제약조건을 만족하는지 검증
        for building, ratio in building_ratios.items():
            # 제약 조건이 있는 제조동만 검증
            if building not in self.building_constraints:
                print(f"제조동 {building}의 제약 조건이 없습니다. 검증 스킵.")
                continue
            
            constraints = self.building_constraints[building]
            lower_limit = constraints.get('lower_limit', 0) * 100
            upper_limit = constraints.get('upper_limit', 0) * 100

            if ratio < lower_limit:
                violations.append(
                    f"Plant '{building}' production ratio {ratio:.2f}% is below "
                    f"minimum limit ({lower_limit:.2f}%)."
                )
            elif ratio > upper_limit:
                violations.append(
                    f"Plant '{building}' production ratio {ratio:.2f}% exceeds "
                    f"maximum limit ({upper_limit:.2f}%)."
                )

        # 위반 사항이 있는지 확인
        if violations:
            return False, "\n".join(violations)
        else:
            return True, ""


    
    """
    아이템의 총 수요량(MFG) 반환
    
    Args:
        item (str): 아이템 코드
        
    Returns:
        int: 총 수요량, 정보 없으면 0
    """
    def _get_total_demand_for_item(self, item):
        if 'demand' in self.demand_data:
            df_demand = self.demand_data['demand']
            item_rows = df_demand[df_demand['Item'] == item]
            if not item_rows.empty and 'MFG' in item_rows.columns:
                return item_rows['MFG'].sum()
            
        # 결과 데이터에서도 확인
        if self.result_data is not None and not self.result_data.empty:
            item_rows = self.result_data[self.result_data['Item'] == item]
            if not item_rows.empty and 'MFG' in item_rows.columns:
                return item_rows['MFG'].iloc[0]
            
        return 0
    
    
