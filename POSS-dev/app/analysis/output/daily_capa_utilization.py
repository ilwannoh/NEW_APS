import pandas as pd
import numpy as np
from app.models.common.file_store import FilePaths
from app.utils.fileHandler import load_file
from app.utils.item_key_manager import ItemKeyManager

"""
요일별 가동률 계산 함수
Args:
    data_df (DataFrame): 최적화 결과 데이터프레임
    
Returns:
    dict: 요일별 가동률 데이터 {'Mon': 75.5, 'Tue': 82.3, ...}
"""
class CapaUtilization:
    @staticmethod
    def analyze_utilization(data_df):
        try:
            # 입력 데이터 검증
            if data_df is None or data_df.empty:
                return {day: 0 for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}

            # 데이터 복사본 생성
            df_demand = data_df.copy()
            
            # 마스터 파일에서 생산능력 데이터(capa_qty) 로드
            master_file = FilePaths.get("master_excel_file")
            if not master_file:
                print("마스터 파일 경로가 설정되지 않았습니다.")
                return {day: 0 for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}

            try:
                sheets = load_file(master_file, sheet_name="capa_qty")

                if isinstance(sheets, dict):
                    df_capa_qty = sheets.get('capa_qty', pd.DataFrame())
                else:
                    df_capa_qty = sheets
                
                if df_capa_qty.empty:
                    print("capa_qty 데이터가 비어 있습니다.")
                    return {day: 0 for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
                
            except Exception as e:
                print(f"생산능력 데이터 로드 중 오류 발생: {str(e)}")
                return {day: 0 for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
            
                
            # 근무를 요일에 매핑
            shift_to_day = {
                1: 'Mon', 2: 'Mon',
                3: 'Tue', 4: 'Tue',
                5: 'Wed', 6: 'Wed',
                7: 'Thu', 8: 'Thu',
                9: 'Fri', 10: 'Fri',
                11: 'Sat', 12: 'Sat',
                13: 'Sun', 14: 'Sun',
            }

            # 일별 생산능력 계산
            day_capacity = {}
            for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                day_shifts = [shift for shift, d in shift_to_day.items() if d == day]
                day_total_capacity = 0

                for shift in day_shifts:
                    shift_capacity = 0

                    # 각 제조동별 처리
                    for factory in ['I', 'D', 'K', 'M']:
                        # 해당 공장 라인들 가져오기
                        factory_lines = df_capa_qty[df_capa_qty['Line'].str.startswith(f'{factory}_')].index.tolist()
                    
                        if not factory_lines or shift not in df_capa_qty.columns:
                            continue

                        # 최대 라인/수량 제약 확인
                        max_line_key = f'Max_line_{factory}'
                        max_qty_key = f'Max_qty_{factory}'

                        # 'Line' 컬럼에서 제약 조건 행 찾기
                        max_line_row = df_capa_qty[df_capa_qty['Line'] == max_line_key]
                        max_qty_row = df_capa_qty[df_capa_qty['Line'] == max_qty_key]

                        # 제약 값 확인
                        if not max_line_row.empty and shift in max_line_row.columns and pd.notna(max_line_row.iloc[0][shift]):
                            max_line = max_line_row.iloc[0][shift]
                            
                            # 중요: 제약이 0이면 해당 제조동의 생산량은 0
                            if max_line == 0:
                                continue
                        else:
                            max_line = len(factory_lines)

                        if not max_qty_row.empty and shift in max_qty_row.columns and pd.notna(max_qty_row.iloc[0][shift]):
                            max_qty = max_qty_row.iloc[0][shift]
                            
                            # 중요: 제약이 0이면 해당 제조동의 생산량은 0
                            if max_qty == 0:
                                continue
                        else:
                            max_qty = float('inf')

                        # 각 라인의 생산 능력 가져오기
                        line_capacities = [(line, df_capa_qty.loc[line, shift]) for line in factory_lines if pd.notna(df_capa_qty.loc[line, shift])]
                        line_capacities.sort(key=lambda x:x[1], reverse=True)  # Sort by capacity in descending order
                 
                        # 라인 수와 최대 수량 간의 더 제한적인 제약 적용
                        factory_capacity = 0
                        for i, (line, capacity) in enumerate(line_capacities):
                            if i >= max_line:
                                break  # 라인 수 초과

                            if factory_capacity + capacity <= max_qty:
                                factory_capacity += capacity
                            elif factory_capacity < max_qty:
                                # 남은 만큼만 추가
                                remaining = max_qty - factory_capacity
                                if remaining > 0:
                                    factory_capacity += remaining
                                break
                            else:
                                break

                        shift_capacity += factory_capacity

                    day_total_capacity += shift_capacity
                
                day_capacity[day] = day_total_capacity
            print(f"요일별 생산 가능량: {day_capacity}")
            
            # 수요 수량에 기반한 일별 생산량 계산
            df_demand['Day'] = df_demand['Time'].map(shift_to_day)
            day_production = df_demand.groupby('Day')['Qty'].sum()
      
            # 일별 가동률 계산
            utilization_rate = {}
            for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                if day in day_capacity:
                    # 생산 능력이 있는 경우
                    if day_capacity[day] > 0:
                        if day in day_production:
                            # 생산량이 생산 능력보다 적거나 같은 경우 - 정상 가동률
                            if day_production[day] <= day_capacity[day]:
                                utilization_rate[day] = (day_production[day] / day_capacity[day]) * 100
                            # 생산량이 생산 능력보다 많은 경우 - 과도한 생산
                            else:
                                # 옵션 1: 100%로 클리핑
                                utilization_rate[day] = 100.0
                                print(f"경고: {day}에 생산 능력({day_capacity[day]})보다 많은 생산량({day_production[day]})이 있습니다. 가동률은 100%로 제한됩니다.")
                        else:
                            utilization_rate[day] = 0
                    # 생산 능력이 0인 경우
                    else:
                        if day in day_production and day_production[day] > 0:
                            # 생산 능력은 0이지만 생산량이 있는 경우
                            print(f"경고: {day}에 생산 능력이 0이지만 생산량({day_production[day]})이 있습니다.")
                            # 옵션 1: 100%로 설정 (가장 보수적인 처리)
                            utilization_rate[day] = 100.0
                        else:
                            # 생산 능력도 0이고 생산량도 0인 경우
                            utilization_rate[day] = 0
                else:
                    # day_capacity에 해당 일이 없는 경우 (발생하지 않아야 함)
                    utilization_rate[day] = 0

            print("daily utilization rate(%):")
            for day, rate in utilization_rate.items():
                if rate is not None:
                    print(f"{day}: {rate:.2f}%")
                else:
                    print(f"{day}: No capacity availble")

            return utilization_rate
        
        except Exception as e:
                print(f"가동률 계산 중 오류 발생: {str(e)}")

    """
    셀 이동 시 요일별 가동률 업데이트

    Args:
        data_df (DataFrame): 기존 데이터프레임
        item_data (dict): 이동 전 아이템 데이터
        new_data (dict): 이동 후 아이템 데이터
        is_initial (초기 분석 여부 (True: 출력 안함))
        
    Returns:
        dict: 업데이트된 가동률 데이터
    """  
    @staticmethod
    def update_utilization_for_cell_move(data_df, item_data, new_data, is_initial=False):
        try:
            """
            1. 입력 데이터 검증 및 정규화
            """
            def normalize_data(data):
                normalized = data.copy()
                if 'Time' in normalized:
                    normalized['Time'] = int(normalized['Time'])
                if 'Qty' in normalized:
                    normalized['Qty'] = float(normalized['Qty'])
                return normalized
            
            # 타입 변환 
            old_data_clean = normalize_data(item_data)
            new_data_clean = normalize_data(new_data)

            # 필수 필드 검증
            required_fields = ['Item', 'Line', 'Time']
            for field in required_fields:
                if field not in old_data_clean:
                    print(f"오류: 필수 필드 '{field}'가 old_data에 없습니다.")
                    return None

            # 2. DataFrame에서 타겟 아이템 찾기(이미 새 위치로 이동)
            mask = (
                (data_df['Item'] == new_data_clean['Item']) &
                (data_df['Line'] == new_data_clean['Line']) &
                (data_df['Time'] == new_data_clean['Time'])
            )

            matching_rows = data_df[mask]

            # 3. 데이터 업데이트
            row_idx = matching_rows.index[0]

            # 4. Line 업데이트
            # 라인 정보 업데이트
            if 'Line' in new_data_clean:
                data_df.at[row_idx, 'Line'] = new_data_clean['Line']
                
            # 근무 정보 업데이트
            if 'Time' in new_data_clean:
                data_df.at[row_idx, 'Time'] = new_data_clean['Time']
                
            # 수량 정보 업데이트
            if 'Qty' in new_data_clean:
                old_qty = old_data_clean['Qty']
                new_qty = new_data_clean['Qty']
                data_df.at[row_idx,'Qty'] = new_qty

                if not is_initial:
                    print(f"수량 업데이트: {old_data_clean['Item']} - {old_qty} -> {new_qty}")

            # 4. 가동률 재계산   
            # 업데이트된 데이터로 가동률 분석
            return CapaUtilization.analyze_utilization(data_df)
            
        except Exception as e:
            print(f"셀 이동 시 가동률 업데이트 중 오류 발생: {str(e)}")


