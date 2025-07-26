import pandas as pd
import numpy as np
import re
import os
import traceback
from app.utils.fileHandler import load_file
from app.models.common.file_store import FilePaths, DataStore

"""
자재 부족량 분석 클래스
자재 부족 모델과 Shift를 식별
"""
class MaterialShortageAnalyzer:

    def __init__(self):
        self.result_df = None          # 결과 데이터프레임 (result 시트)
        self.material_detail_df = None # 자재 부족 정보 데이터프레임 (Material Detail 시트)
        self.shortage_results = {}     # 분석 결과 저장소: {item_code: [{shift, material, shortage}]}
        
    """
    필요한 데이터 로드
    """   
    def load_data(self, result_data=None):
        try:
            # 결과 데이터 직접 전달 시 사용
            if result_data is not None:
                self.result_df = result_data
            
            # Material Detail 시트 별도 로드 시도
            self._load_material_detail()
            
            # 데이터 유효성 검증
            if self.result_df is None or self.material_detail_df is None:
                return False
                
            return True
            
        except Exception as e:
            traceback.print_exc()
            return False
    
    """
    Material Detail 시트 로드 및 처리
    """
    def _load_material_detail(self):
        try:
            # 결과 파일 경로 가져오기
            result_path = FilePaths.get("optimizer_file")
            
            if result_path and os.path.exists(result_path):
                # Material Detail 시트 로드 시도
                try:
                    # 모든 시트 이름 가져오기
                    xl = pd.ExcelFile(result_path)
                    sheet_names = xl.sheet_names
                    
                    # 결과 파일의 두 번째 시트를 material_detail로 가정
                    if len(sheet_names) > 1:
                        material_detail_sheet = sheet_names[1]
                        self.material_detail_df = pd.read_excel(result_path, sheet_name=material_detail_sheet)
                    else:
                        pass
                except Exception as e:
                    pass
            else:
                # DataStore에서 시도
                stored_dataframes = DataStore.get("simplified_dataframes", {})
                
                if "material_detail" in stored_dataframes:
                    self.material_detail_df = stored_dataframes["material_detail"]
            
            # 데이터프레임 전처리
            if self.material_detail_df is not None:
                self._preprocess_material_detail()
                
        except Exception as e:
            traceback.print_exc()
    
    """
    Material Detail 데이터프레임 전처리
    """
    def _preprocess_material_detail(self):
        if self.material_detail_df is None or self.material_detail_df.empty:
            return
            
        try:
            # index 컬럼 (자재 코드)은 첫 번째 컬럼으로 가정
            index_col = self.material_detail_df.columns[0]
            
            # Items 컬럼 (아이템 목록)은 마지막 컬럼으로 가정
            items_col = self.material_detail_df.columns[-1]
            
            # Shift 컬럼 찾기 (1-14) - 숫자 컬럼
            shift_cols = []
            for col in self.material_detail_df.columns:
                # 컬럼 이름이 숫자인 경우
                if isinstance(col, int) or (isinstance(col, str) and col.isdigit()):
                    col_str = str(col)
                    if int(col_str) >= 1 and int(col_str) <= 14:
                        shift_cols.append(col_str)
            
            # 컬럼 매핑 설정
            col_mapping = {index_col: 'index'}
            for col in self.material_detail_df.columns:
                if isinstance(col, int) or (isinstance(col, str) and col.isdigit()):
                    col_str = str(col)
                    if col_str in shift_cols:
                        col_mapping[col] = col_str
            
            col_mapping[items_col] = 'Items'
            
            # 필요한 컬럼만 선택하고 이름 변경
            self.material_detail_df = self.material_detail_df.rename(columns=col_mapping)
            
            # index 컬럼을 문자열로 변환
            if 'index' in self.material_detail_df.columns:
                self.material_detail_df['index'] = self.material_detail_df['index'].astype(str)
            
            # Items 컬럼 처리
            if 'Items' in self.material_detail_df.columns:
                # Items 값 변환
                self.material_detail_df['Items'] = self.material_detail_df['Items'].apply(
                    lambda x: self._parse_items_value(x)
                )
            
        except Exception as e:
            traceback.print_exc()
    
    """
    Items 컬럼 값 파싱 (문자열 -> 리스트)
    """
    def _parse_items_value(self, value):
        try:
            # 이미 리스트인 경우
            if isinstance(value, list):
                return value
            
            # null 값 처리
            if pd.isna(value) or value is None:
                return []
            
            # 문자열인 경우
            if isinstance(value, str):
                # 리스트 형태 문자열 (예: "['item1', 'item2']")
                if (value.startswith('[') and value.endswith(']')):
                    try:
                        parsed = eval(value)
                        if isinstance(parsed, list):
                            return parsed
                        return [str(parsed)]
                    except:
                        # 안전하게 직접 파싱
                        value = value.strip('[]')
                        items = value.split(',')
                        return [item.strip().strip("'\"") for item in items if item.strip()]
                
                # 쉼표로 구분된 문자열 (예: "item1, item2")
                elif ',' in value:
                    items = value.split(',')
                    return [item.strip() for item in items if item.strip()]
                
                # 단일 값
                else:
                    return [value.strip()]
            
            # 그 외의 경우는 단일 값을 리스트로 변환
            return [str(value)]
            
        except Exception as e:
            return []  # 오류 시 빈 리스트 반환
    
    """
    자재 부족량 분석 실행: 시프트 매칭을 고려하여 부족 정보 수집
    """
    def analyze_material_shortage(self, result_data=None):
        try:
            # 데이터 로드 시도
            data_loaded = self.load_data(result_data)
            
            if not data_loaded:
                return {}
            
            # 결과 저장할 딕셔너리
            shortage_results = {}
            
            # Material Detail 시트에서 부족한 자재 찾기
            if self.material_detail_df is not None:
                
                if self.result_df is None:
                    return {}
                    
                # 'Time'과 'Item' 컬럼 확인
                if 'Time' not in self.result_df.columns or 'Item' not in self.result_df.columns:
                    return {}
                
                # 결과 데이터프레임의 아이템과 시프트 조합을 저장 (검색 최적화)
                # (item, time) 형태의 튜플로 저장하여 빠른 검색 가능
                item_shift_pairs = set()
                for _, row in self.result_df.iterrows():
                    item = row['Item']
                    time = row['Time']
                    if pd.notna(item) and pd.notna(time):
                        item_shift_pairs.add((str(item), int(time)))
                
                # 각 행(자재)에 대해 순회
                for idx, row in self.material_detail_df.iterrows():
                    material_code = row.get('index')
                    items_list = row.get('Items', [])
                    
                    # Items가 리스트가 아니면 변환
                    if not isinstance(items_list, list):
                        items_list = self._parse_items_value(items_list)
                    
                    # 아이템 리스트가 비어있으면 스킵
                    if not items_list:
                        continue
                    
                    # 시프트 컬럼들(1-14) 확인
                    for shift in range(1, 15):
                        shift_str = str(shift)
                        
                        # 해당 Shift 컬럼이 있는지 확인
                        if shift_str not in self.material_detail_df.columns:
                            continue
                        
                        # 부족량 값 가져오기
                        shortage_amt = row.get(shift_str)
                        
                        # 부족한 수량이 음수(결손)인 경우만 처리
                        try:
                            # 값이 숫자인지 확인하고 변환
                            if pd.notna(shortage_amt):
                                # 숫자 아닌 값은 변환 시도
                                if not isinstance(shortage_amt, (int, float)):
                                    try:
                                        shortage_amt = float(shortage_amt)
                                    except (ValueError, TypeError):
                                        continue
                                
                                # 부족량이 음수인 경우만 처리
                                if shortage_amt < 0:
                                    # 해당 자재를 사용하는 아이템 중 현재 시프트에 있는 아이템만 처리
                                    for item in items_list:
                                        # 빈 문자열이나 None인 경우 건너뛰기
                                        if not item or pd.isna(item):
                                            continue
                                        
                                        item = str(item).strip()  # 모델 코드 문자열로 변환 및 공백 제거
                                        
                                        # 중요: 해당 아이템이 현재 시프트에 존재하는지 확인
                                        if (item, shift) in item_shift_pairs:
                                            # 아이템 코드로 항목 초기화 (없으면)
                                            if item not in shortage_results:
                                                shortage_results[item] = []
                                            
                                            # 부족 정보 저장
                                            shortage_info = {
                                                'shift': int(shift),
                                                'material': material_code,
                                                'shortage': abs(shortage_amt)  # 절대값으로 변환
                                            }
                                            
                                            # 중복 추가 방지
                                            if shortage_info not in shortage_results[item]:
                                                shortage_results[item].append(shortage_info)
                        except (ValueError, TypeError) as e:
                            pass
            
            # 결과 저장
            self.shortage_results = shortage_results
            
            return shortage_results
            
        except Exception as e:
            traceback.print_exc()
            return {}

    """
    자재 부족이 있는 아이템 목록 반환
    """
    def get_shortage_items(self):
        return list(self.shortage_results.keys())
    
    """
    특정 아이템의 자재 부족 세부 정보 반환
    """
    def get_item_shortages(self, item_code):
        return self.shortage_results.get(item_code, [])
    
    """
    모든 부족 데이터를 테이블 형식으로 반환
    """
    def get_all_shortage_data(self):
        result_rows = []
        
        # 부족이 발생한 모델 및 자재 정보 추가
        for item, shortages in self.shortage_results.items():
            for shortage in shortages:
                result_rows.append({
                    'Material': shortage.get('material', 'Unknown'),
                    'Item': item,
                    'Shortage': shortage.get('shortage', 0),
                    'Shift': shortage.get('shift', 0),
                    'status_type': 'shortage'  # 상태 타입 추가
                })
        
        # 데이터프레임 변환 및 정렬
        df = pd.DataFrame(result_rows)
        if not df.empty:
            # Material로 정렬한 후 Item으로 정렬
            df = df.sort_values(['Material', 'Item'])
        
        return df
            
    """
    차트 표시용 형식의 데이터 가져오기
    """
    def get_shortage_chart_data(self):
        if not self.shortage_results:
            return {}
            
        # 아이템별 부족률 계산
        item_shortage_pct = {}
        
        for item, shortages in self.shortage_results.items():
            # 이 아이템이 Result 데이터에 있는지 확인
            if self.result_df is not None:
                item_rows = self.result_df[self.result_df['Item'] == item]
                
                if not item_rows.empty and 'Qty' in item_rows.columns:
                    # 전체 필요 수량 (모든 시프트 합)
                    total_qty = item_rows['Qty'].sum()
                    
                    # 총 부족 자재 개수
                    shortage_count = len(shortages)
                    
                    # 부족률 계산
                    if total_qty > 0:
                        shortage_pct = min(100, (shortage_count / total_qty) * 100)
                    else:
                        shortage_pct = 0
                else:
                    # 수량 정보가 없는 경우 부족 자재 개수로 점수 부여
                    shortage_pct = min(100, len(shortages) * 20)
            else:
                # Result 데이터가 없는 경우 부족 자재 개수로 점수 부여
                shortage_pct = min(100, len(shortages) * 20)
            
            item_shortage_pct[item] = shortage_pct
        
        return item_shortage_pct