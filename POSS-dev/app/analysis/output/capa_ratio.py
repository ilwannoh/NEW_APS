import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from app.models.common.file_store import FilePaths

class CapaRatioAnalyzer:  
    @staticmethod
    def analyze_capa_ratio(data_df=None, file_path=None, sheet_name=None, is_initial=False):
        """
        데이터프레임 또는 엑셀 파일에서 제조동별 생산량 비율을 분석
        
        Args:
            data_df (DataFrame, optional): 분석할 데이터프레임
            file_path (str, optional): 분석할 엑셀 파일 경로
            sheet_name (str, optional): 분석할 엑셀 시트명
            is_initial (bool, optional): 초기 분석 여부 (True: 출력 안함)
            
        Returns:
            dict: 제조동별 비율 데이터 {'I': 30.5, 'K': 25.2, ...}
        """
        try:
            # 데이터 소스 확인 및 로드
            if data_df is not None:
                # 데이터프레임이 직접 제공된 경우
                df = data_df.copy()
            elif file_path:
                # 파일 경로가 제공된 경우
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File '{file_path}' does not exist.")
                
                try:
                    # 시트명이 제공된 경우
                    if sheet_name:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    else:
                        # 시트명이 제공되지 않은 경우 첫 번째 시트 사용
                        df = pd.read_excel(file_path)
                except ValueError:
                    # 시트명이 없을 경우 첫 번째 시트를 사용
                    # print(f"Sheet '{sheet_name}' not found. Using the first sheet instead.")
                    df = pd.read_excel(file_path)
            else:
                raise ValueError("Either data_df or file_path must be provided.")
            
            # 'Line' 컬럼 존재 여부 확인
            if 'Line' not in df.columns:
                raise KeyError("Column 'Line' does not exist in the data.")
            
            # 'Qty' 컬럼 존재 여부 확인
            if 'Qty' not in df.columns:
                # 'Qty' 컬럼이 없는 경우 다른 숫자형 컬럼을 찾아 사용
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    qty_col = numeric_cols[0]
                    # print(f"Column 'Qty' not found. Using '{qty_col}' column instead.")
                    df['Qty'] = df[qty_col]
                else:
                    raise KeyError("Column 'Qty' or any usable numeric column does not exist in the data.")
            
            # Line 컬럼에서 제조동 이름 추출
            df['name'] = df['Line'].astype(str).str.split('_').str[0]
            
            # 누락된 값 처리
            df['name'] = df['name'].fillna('Unknown')
            df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
            
            # 제조동별 QTY 합계 계산
            pivot_table = df.pivot_table(
                index='name',  # 제조동을 행으로
                values='Qty',  # QTY 열을 집계
                aggfunc='sum'  # 합계 계산
            ).reset_index()
            
            # 데이터가 비어있는지 확인
            if len(pivot_table) == 0:
                raise ValueError("No data to analyze.")
            
            # 전체 QTY 합계 계산
            total_qty = pivot_table['Qty'].sum()
            
            # 전체 합계가 0인 경우 처리
            if total_qty == 0:
                # print("Warning: Total QTY sum is 0.")
                pivot_table['ratio'] = 0
            else:
                # 비중(%) 컬럼 추가
                pivot_table['ratio'] = (pivot_table['Qty'] / total_qty * 100).round(2)
            
            # 결과 딕셔너리 생성 (Plant: Ratio 형태)
            result_dict = dict(zip(pivot_table['name'], pivot_table['ratio']))
            
            # 상세 분석 결과 출력 (초기 분석이 아닐 때만)
            if not is_initial:
                print("\nPlant Allocation Analysis Results:")
                for plant, ratio in result_dict.items():
                    print(f"{plant}: {ratio}%")
                
            return result_dict
            
        except Exception as e:
            # print(f"Error in analyze_capa_ratio: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}  # 오류 발생 시 빈 딕셔너리 반환
    
    # 플랜트별 생산량 업데이트 (셀 이동 시)
    @staticmethod
    def update_capa_ratio_for_cell_move(data_df, item_data, new_data, is_initial=False):
        """
        셀 이동 시 플랜트별 생산량 비율 업데이트
        
        Args:
            data_df (DataFrame): 기존 데이터프레임
            item_data (dict): 이동 전 아이템 데이터
            new_data (dict): 이동 후 아이템 데이터
            is_initial (bool, optional): 초기 분석 여부 (True: 출력 안함)
            
        Returns:
            dict: 업데이트된 제조동별 비율 데이터
        """
        try:
            # 아이템 정보 찾기
            # item_id = item_data.get('Item')

            # 아이템 정보 추출
            item_id = item_data.get('Item')
            old_line = item_data.get('Line')
            old_time = int(item_data.get('Time'))
            old_qty = float(item_data.get('Qty', 0))
            
            if item_id is None or old_line is None:
                print("필수 정보 누락: 아이템명 또는 라인 정보")
                return None
            
            # 데이터프레임 복사본 생성
            df_copy = data_df.copy()
            
            # 데이터 타입 일관성 보장
            df_copy['Time'] = df_copy['Time'].astype(int)
            df_copy['Qty'] = df_copy['Qty'].astype(float)
            
            # 기존 항목 찾기 (Line, Time, Item 모두 일치)
            mask = (
                (df_copy['Item'] == item_id) &
                (df_copy['Line'] == old_line) &
                (df_copy['Time'] == old_time)
            )
            
            item_rows = df_copy[mask]
            
            if item_rows is not None:
                print(f"업데이트 전 Qty 합계: {data_df['Qty'].sum()}")
                print(f"업데이트 대상 아이템: {item_id}")
                print(f"대상 라인/시프트: {item_data.get('Line')}/{item_data.get('Time')}")
                # 해당 아이템 행 찾기
                # item_row = data_df[data_df['Item'] == item_id]
                
                if not item_rows.empty:
                    # 인덱스 가져오기
                    idx = item_rows.index[0]

                    # 기존 수량 확인
                    current_qty = df_copy.at[idx, 'Qty']
                    print(f"현재 수량: {current_qty}")
                    
                    # 라인 정보 업데이트
                    if 'Line' in new_data:
                        data_df.at[idx, 'Line'] = new_data['Line']
                        
                    # 수량 정보 업데이트
                    if 'Qty' in new_data:
                        data_df.at[idx, 'Qty'] = int(new_data['Qty'])
                        
            # 업데이트된 데이터로 비율 분석
            return CapaRatioAnalyzer.analyze_capa_ratio(data_df=data_df, is_initial=is_initial)
            
        except Exception as e:
            # print(f"Error in update_capa_ratio_for_cell_move: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}  # 오류 발생 시 빈 딕셔너리 반환
        
    @staticmethod
    def get_capa_thresholds():
        try:
            # 마스터 파일 경로 가져오기
            master_file = FilePaths.get("master_excel_file")
            if not master_file or not os.path.exists(master_file):
                print("마스터 파일을 찾을 수 없습니다.")
                return {}
            
            # capa_portion 시트 로드
            try:
                portion_df = pd.read_excel(master_file, sheet_name="capa_portion")
            except Exception as e:
                print(f"capa_portion 시트 로드 오류: {str(e)}")
                return {}
            
            # 필요한 열이 있는지 확인
            if not all(col in portion_df.columns for col in ['name', 'upper_limit', 'lower_limit']):
                return {}
        
            
            # 퍼센트 값 처리
            for col in ['upper_limit', 'lower_limit']:
                # 값이 문자열인 경우 '%' 제거 후 숫자로 변환
                for idx, value in enumerate(portion_df[col].values):
                    if isinstance(value, str):
                        # '%' 제거 후 숫자로 변환
                        try:
                            numeric_value = float(value.replace('%', ''))
                            portion_df.at[idx, col] = numeric_value
                        except (ValueError, TypeError):
                            # print(f"변환 오류: {value}를 숫자로 변환할 수 없습니다.")
                            portion_df.at[idx, col] = None
                    # 숫자인 경우: 1 이하이면 100을 곱함 (소수점 표현 -> 퍼센트)
                    elif isinstance(value, (int, float)):
                        if value <= 1:
                            portion_df.at[idx, col] = value * 100
                
                # 값이 100인 경우 확인해서 처리
                for idx, value in enumerate(portion_df[col].values):
                    if value == 1.0:  # 1.0으로 잘못 변환된 100% 값
                        portion_df.at[idx, col] = 100.0
            
            # 결과 딕셔너리 생성
            result = {}
            for _, row in portion_df.iterrows():
                result[row['name']] = {
                    'upper_limit': row['upper_limit'],
                    'lower_limit': row['lower_limit']
                }
            
            return result
            
        except Exception as e:
            print(f"임계점 데이터 로드 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}