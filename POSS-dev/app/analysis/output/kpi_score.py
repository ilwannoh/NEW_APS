from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
import pandas as pd
import numpy as np
from app.models.common.file_store import FilePaths, DataStore
from app.models.common.settings_store import SettingsStore
from app.utils.fileHandler import load_file

"""
KPI Score 계산
"""
class KpiScore:
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.opts = {}
        self.df = None  # 결과 데이터
        self.material_analyzer = None
        self.demand_df = None
        self.kpi_widget = None

    """
    설정값 가져오기
    """
    def get_options(self):
        # 설정값 가져오기
        all_settings = SettingsStore.get_all()

        # 필요한 설정값 추출
        self.opts = {
            'weight_sop_ox': all_settings.get('weight_sop_ox', 1.0),  # SOP 가중치
            'mat_use': all_settings.get('mat_use', 0),  # 자재제약 반영여부
            'weight_mat_qty': all_settings.get('weight_mat_qty', 1.0),  # 자재 가중치
            'weight_operation': all_settings.get('weight_operation', 1.0),  # 가동률 가중치
            'weight_day_ox': all_settings.get('weight_day_ox', 0),  # shift별 가중치 반영여부
            'weight_day': all_settings.get('weight_day', [1.0, 1.0, 1.0]),  # shift별 가중치
        }

        return self.opts
    
    """
    데이터 설정
    """
    def set_data(self, result_data, material_anaylsis=None, demand_df=None):
        self.df = result_data  # 참조를 저장하여 실시간 업데이트 가능 
        self.material_analyzer = material_anaylsis
        self.demand_df = demand_df

    """
    KPI 위젯 참조 저장
    """
    def set_kpi_widget(self, kpi_widget):
        self.kpi_widget = kpi_widget

    
    """
    자재 점수 계산
    """
    def calculate_material_score(self):
        if not self.material_analyzer or not hasattr(self.material_analyzer, 'shortage_results'):
            return 0
        
        # 총 할당량
        total_qty = self.df['Qty'].sum()
        
        # 자재부족량
        neg_shortage = 0
        for item_shortages in self.material_analyzer.shortage_results.values():
            for shortage_info in item_shortages:
                # 절대값으로 저장되어 있으므로 음수 변환
                shortage_amount = -abs(shortage_info.get('shortage', 0))
                neg_shortage += shortage_amount

        # 점수 계산 : 1 + (부족량 합계 / 총 수량)
        mat_score = (1 + neg_shortage / total_qty) * 100

        return mat_score


    """
    SOP 점수 계산
    """ 
    def calculate_sop_score(self):
        if self.df is None or self.demand_df is None:
            return 0
        
        # Due_LT 내에 모두 충족된 수요
        # Item과 To_site 조합으로 실제 생산량과 요구량 비교
        df = self.df
        demand_copy = self.demand_df.copy()

        if 'To_Site' in demand_copy.columns and 'To_site' not in demand_copy.columns:
            demand_copy = demand_copy.rename(columns={'To_Site': 'To_site'})
            print("demand_df 컬럼명 'To_Site' -> 'To_site'로 변경")
        print(f"통일 후 result_data To_site: {'To_site' in df.columns}")
        print(f"통일 후 demand_df To_site: {'To_site' in demand_copy.columns}")

        demand_summary = pd.DataFrame()
        # 전체 모델/To_site 조합 수
        if 'SOP' in demand_copy.columns:
            demand_summary = demand_copy.groupby(['Item', 'To_site'])['SOP'].first().reset_index()
            demand_summary.rename(columns={'SOP':'DemandQty'}, inplace=True)

        total_demand = len(demand_summary)

        # Due_LT 내의 생산량만 집계
        due_lt_mask = df['Time'] <= df['Due_LT']
        due_lt_production = df[due_lt_mask].groupby(['Item', 'To_site'])['Qty'].sum().reset_index()
        due_lt_production.rename(columns={'Qty': 'ProducedQty'}, inplace=True)

        # 병합하여 비교
        comparison = pd.merge(demand_summary, due_lt_production, on=['Item', 'To_site'], how='left')
        comparison['ProducedQty'] = comparison['ProducedQty'].fillna(0)
        
        # SOP 성공한 모델/To_site 조합 수 (Due_LT 내 생산량 >= SOP 요구량)
        successful_combinations = len(comparison[comparison['ProducedQty'] >= comparison['DemandQty']]) 
        
        # SOP 점수 
        sop_score = (successful_combinations / total_demand * 100) if total_demand > 0 else 100.0
        
        return sop_score


    """
    가동률 점수 계산
    """
    def calculate_utilization_score(self):
        # 마스터 파일에서 생산능력 데이터(capa_qty) 로드
        master_file = FilePaths.get("master_excel_file")
        if not master_file:
            print("마스터 파일 경로가 설정되지 않았습니다.")
            return {}

        try:
            sheets = load_file(master_file, sheet_name="capa_qty")

            if isinstance(sheets, dict):
                df_capa_qty = sheets.get('capa_qty', pd.DataFrame())
            else:
                df_capa_qty = sheets
            
            if df_capa_qty.empty:
                print("capa_qty 데이터가 비어 있습니다.")
                return {}
            
        except Exception as e:
            print(f"생산능력 데이터 로드 중 오류 발생: {str(e)}")
            return {}

        # 총 생산량 계산
        total_qty = self.df['Qty'].sum()
        
        # Shift별 실제 생산량
        result_pivot = self.df.groupby('Time')['Qty'].sum()
        # print(f"Time별 생산량: {result_pivot.to_dict()}")  # 디버깅용

        # 가중치 적용 : weight_day_ox가 켜져있으면 weight_day 사용
        if self.opts.get('weight_day_ox', 0):
            weights = self.opts.get('weight_day', [1.0] * 14)
        else:  # 아니면 균등 가중치
            weights = [1.0] * 14  

        # shift별 best 생산 능력 계산
        shift_capacity = {}
        for shift in range(1, 15):
            if shift not in df_capa_qty.columns:
                shift_capacity[shift] = 0
                continue

            shift_total_capacity = 0

            # 각 제조동별 처리
            for factory in ['I', 'D', 'K', 'M']:
                # 해당 공장 라인들 가져오기
                factory_lines = df_capa_qty[df_capa_qty['Line'].str.startswith(f'{factory}_')].index.tolist()
                # print(f"factor_lines : {factory_lines}")
            
                if not factory_lines:
                    print(f"Factory {factory}에 라인 없음")
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
                    # print(f"Factory {factory} Max Line 값: {max_line}")
                    
                    # 중요: 제약이 0이면 해당 제조동의 생산량은 0
                    if max_line == 0:
                        # print(f"Factory {factory}의 Max Line이 0이므로 생산 능력 0")
                        continue
                else:
                    max_line = len(factory_lines)
                    # print(f"Factory {factory} Max Line 정보 없음, 기본값 사용: {max_line}")

                if not max_qty_row.empty and shift in max_qty_row.columns and pd.notna(max_qty_row.iloc[0][shift]):
                    max_qty = max_qty_row.iloc[0][shift]
                    # print(f"Factory {factory} Max Qty 값: {max_qty}")
                    
                    # 중요: 제약이 0이면 해당 제조동의 생산량은 0
                    if max_qty == 0:
                        # print(f"Factory {factory}의 Max Qty가 0이므로 생산 능력 0")
                        continue
                else:
                    max_qty = float('inf')
                    # print(f"Factory {factory} Max Qty 정보 없음, 무제한으로 설정")

                # 각 라인의 생산 능력 가져오기
                line_capacities = [(line, df_capa_qty.loc[line, shift]) for line in factory_lines if pd.notna(df_capa_qty.loc[line, shift])]
                line_capacities.sort(key=lambda x:x[1], reverse=True)  # 내림차순 정렬 
    
                # 라인 수와 최대 수량 간의 더 제한적인 제약 적용
                factory_capacity = 0
                for i, (line, capacity) in enumerate(line_capacities):
                    if i >= max_line:
                        break  # 라인 수 초과

                    if factory_capacity + capacity <= max_qty:
                        factory_capacity += capacity
                    elif factory_capacity < max_qty:
                        # 남은 만큼만 채움
                        remaining = max_qty - factory_capacity
                        if remaining > 0:
                            factory_capacity += remaining
                        break
                    else:
                        break  # 이미 max_qty를 넘었음

                shift_total_capacity += factory_capacity

            shift_capacity[shift] = shift_total_capacity
            # print(f"Shift {shift} 생산 능력: {shift_total_capacity}")

        # Best 배치 계산: 앞 시프트부터 최대로 채움
        best_allocation = {}
        remaining_qty = total_qty

        for shift in range(1, 15):
            capacity = shift_capacity.get(shift, 0)
            if remaining_qty > 0 and capacity > 0:
                allocated = min(capacity, remaining_qty)
                best_allocation[shift] = allocated
                remaining_qty -= allocated
            else:
                best_allocation[shift] = 0
            
            # print(f"Shift {shift} Best 배치: {best_allocation[shift]}")
        
        # Result 값과 Best 값에 가중치 적용하여 계산
        weighted_result_sum = 0
        weighted_best_sum = 0

        for shift in range(1, 15): 
            if shift <= len(weights):
                weight = weights[shift - 1]
                result_qty = result_pivot.get(shift, 0)
                best_qty = best_allocation.get(shift, 0)
                
                weighted_result_sum += result_qty * weight
                weighted_best_sum += best_qty * weight

                # print(f"Shift {shift}: Weight={weight}, Result={result_qty}, Best={best_qty}")
        
        # 디버깅 정보 출력
        print(f"Util 계산: Result={weighted_result_sum}, Best={weighted_best_sum}")

        # 가동률 계산: 1 - (Result 값 * 가중치 / Best 값 * 가중치)
        if weighted_best_sum > 0:
            util_score = (1 - (weighted_result_sum / weighted_best_sum)/100) * 100
            print(f"Util 점수: {util_score:.2f}%")
        else:
            util_score = 100.0
            print("Best 합계가 0, Util 점수는 100%로 설정")
        
        return util_score
    

    """
    총 점수 계산
    """
    def calculate_total_score(self, mat_score, sop_score, util_score):
        # 가중치 계산
        w_mat = self.opts['weight_mat_qty'] if self.opts['mat_use'] else 0.0  # 자재 가중치
        w_sop = self.opts['weight_sop_ox']  # SOP 가중치
        w_oper = self.opts['weight_operation']  # 가동률 가중치

        w_total = w_mat + w_sop + w_oper

        # 가중치 평균 계산
        total_score = (
            (mat_score * w_mat + sop_score * w_sop + util_score * w_oper) / w_total
        )

        return total_score
    

    """
    모든 점수 계산
    """
    def calculate_all_scores(self):
        self.get_options()

        print("==== KPI 계산 디버깅 ====")
        print(f"결과 데이터프레임 크기: {len(self.df) if self.df is not None else 0}")

        # Mat 점수 계산에 사용되는 데이터 확인
        if hasattr(self, 'material_analyzer') and self.material_analyzer:
            shortage_count = len(self.material_analyzer.shortage_results) if hasattr(self.material_analyzer, 'shortage_results') else 0
            print(f"자재 부족 아이템 수: {shortage_count}")

        # 각 점수 계산
        try:
            mat_score = self.calculate_material_score()
        except Exception as e:
            print(f"자재 점수 계산 오류: {e}")
            mat_score = 0.0
        
        try:
            sop_score = self.calculate_sop_score()
        except Exception as e:
            print(f"SOP 점수 계산 오류: {e}")
            sop_score = 0.0
        
        try:
            util_score = self.calculate_utilization_score()
            # util_score가 딕셔너리인지 확인하고 숫자 값 추출
            if isinstance(util_score, dict):
                print(f"util_score가 딕셔너리입니다: {util_score}")
                # 임시 값으로 처리
                util_value = 0.0
                for key, val in util_score.items():
                    if isinstance(val, (int, float)):
                        util_value = val
                        break
                util_score = util_value
        except Exception as e:
            print(f"가동률 점수 계산 오류: {e}")
            util_score = 0.0

        total_score = self.calculate_total_score(mat_score, sop_score, util_score)

        scores = {
            'Mat': mat_score,
            'SOP': sop_score,
            'Util': util_score,
            'Total': total_score
        }
        
        # 각 점수 로깅 (변수 생성 후에 호출)
        print(f"계산된 KPI 점수: Mat={scores['Mat']:.2f}, SOP={scores['SOP']:.2f}, Util={scores['Util']:.2f}, Total={scores['Total']:.2f}")
        print("=======================")

        return {
            'Mat': mat_score,
            'SOP': sop_score,
            'Util': util_score,
            'Total': total_score
        }


    """
    점수 새로고침 및 위젯 업데이트
    """
    def refresh_kpi_scores(self):
        if self.kpi_widget:
            scores = self.calculate_all_scores()
            self._update_kpi_labels(scores)
            return scores
        return None


    """
    KPI 라벨 업데이트
    """
    def _update_kpi_labels(self, scores):
        if not self.kpi_widget or not scores:
            return
            
        # 기존 위젯 제거
        layout = self.kpi_widget.layout()
        for i in reversed(range(layout.count())):
            child = layout.itemAt(i).widget()
            if child:
                child.setParent(None)
  
        # 점수에 따른 색상 결정
        def get_color(score):
            if score >= 90:
                return "color: #28a745;"  # 초록색
            elif score >= 70:
                return "color: #ffc107;"  # 노란색
            else:
                return "color: #dc3545;"  # 빨간색
        
        # Mat 점수 : 반올림하여 소수점 1자리
        mat_label = QLabel(f"Mat: {scores['Mat']:.1f}%")
        mat_label.setStyleSheet(f"font-weight: bold; {get_color(scores['Mat'])}")
        layout.addWidget(mat_label, 0, 0)
        
        # SOP 점수
        sop_label = QLabel(f"SOP: {scores['SOP']:.1f}%")
        sop_label.setStyleSheet(f"font-weight: bold; {get_color(scores['SOP'])}")
        layout.addWidget(sop_label, 0, 1)
        
        # Util 점수
        util_label = QLabel(f"Util: {scores['Util']:.1f}%")
        util_label.setStyleSheet(f"font-weight: bold; {get_color(scores['Util'])}")
        layout.addWidget(util_label, 0, 2)
        
        # Total 점수
        total_label = QLabel(f"Total: {scores['Total']:.1f}%")
        total_label.setStyleSheet(f"font-weight: bold; font-size: 14pt; {get_color(scores['Total'])}")
        total_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(total_label, 1, 0, 1, 3)
    
    def update_kpi_widget(self, kpi_widget, layout_type='grid'):
        """KPI 위젯 업데이트 (기존 메서드와 호환성 유지)"""
        self.set_kpi_widget(kpi_widget)
        return self.refresh_kpi_scores() 



