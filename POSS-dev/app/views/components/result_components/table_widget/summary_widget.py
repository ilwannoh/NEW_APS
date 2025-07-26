from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
import pandas as pd
from app.analysis.output.capa_ratio import CapaRatioAnalyzer
from app.models.common.file_store import FilePaths
from app.utils.fileHandler import load_file
from app.views.components.common.custom_table import CustomTable
from app.utils.sort_line import sort_line

"""
결과 요약 정보 표시 위젯
"""


class SummaryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_capacity_data = {}  # 라인별 생산능력
        self.line_utilization_data = {}  # 라인별 가동률
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 요약 테이블
        self.summary_table = CustomTable()
        main_layout.addWidget(self.summary_table)

    """
    master 파일에서 라인별 생산능력 로드
    """

    def load_line_capacity_data(self):
        try:
            master_file = FilePaths.get('master_excel_file')
            if not master_file:
                print("마스터 파일 경로를 찾을 수 없습니다.")
                return

            # capa_qty 시트 로드
            capa_data = load_file(master_file, sheet_name='capa_qty')
            if isinstance(capa_data, dict):
                df_capa_qty = capa_data.get('capa_qty', pd.DataFrame())
            else:
                df_capa_qty = capa_data

            if df_capa_qty.empty:
                print("capa_qty 데이터가 비어있습니다.")
                return

            # 라인별 전체 생산능력 계산 (라인별 합계)
            for _, row in df_capa_qty.iterrows():
                if 'Line' in row:
                    line = row['Line']
                    total_capacity = 0
                    for col in df_capa_qty.columns:
                        if isinstance(col, (int, str)) and str(col).isdigit():
                            if pd.notna(row[col]):
                                total_capacity += row[col]
                    self.line_capacity_data[line] = total_capacity
            print(f"라인별 생산능력 로드 완료: {len(self.line_capacity_data)}개 라인")

        except Exception as e:
            print(f"라인별 생산능력 로드 오류: {e}")

    """
    라인별 가동률 계산
    """

    def calculate_line_utilization(self, result_data):
        try:
            # 라인별 생산량 계산
            line_production = result_data.groupby('Line')['Qty'].sum()

            # 라인별 가동률 계산
            for line, production in line_production.items():
                if line in self.line_capacity_data:
                    capacity = self.line_capacity_data[line]
                    if capacity > 0:
                        utilization = (production / capacity) * 100
                        self.line_utilization_data[line] = utilization
                    else:
                        self.line_utilization_data[line] = 0
                else:
                    # 생산능력 정보가 없으면 0으로 설정
                    self.line_utilization_data[line] = 0

            print(f"라인별 가동률 계산 완료: {len(self.line_utilization_data)}개 라인")

        except Exception as e:
            print(f"라인별 가동률 계산 오류: {e}")

    """
    결과 분석 및 테이블 업데이트
    """

    def run_analysis(self, result_data):
        if result_data is None or result_data.empty:
            self.clear_table()
            return

        try:
            # 1. 라인별 생산능력 및 가동률
            self.load_line_capacity_data()
            self.calculate_line_utilization(result_data)

            # 2. 제조동별 비율 계산
            capa_ratios = CapaRatioAnalyzer.analyze_capa_ratio(data_df=result_data, is_initial=True)

            # 3. 상세 정보 추출
            summary_data = self.create_summary(result_data, capa_ratios)

            # 4. 테이블 업데이트
            self.update_table(summary_data)

        except Exception as e:
            print(f"summary 요약 중 에러 : {e}")

    """
    제조동별 생산량 기준 정렬 순서 결정
    """

    def get_sorted_buildings(self, result_data):
        """제조동별 생산량 기준으로 정렬된 제조동 목록 반환"""
        try:
            # 제조동 정보 추출 (Line 이름의 첫 글자가 제조동)
            result_data_temp = result_data.copy()
            result_data_temp['Building'] = result_data_temp['Line'].str[0]

            # 제조동별 생산량 계산 (정렬 목적)
            building_production = result_data_temp.groupby('Building')['Qty'].sum()

            # 생산량 기준으로 제조동 정렬 (내림차순)
            sorted_buildings = building_production.sort_values(ascending=False).index.tolist()

            print(f"제조동별 생산량 정렬 순서: {sorted_buildings}")
            return sorted_buildings

        except Exception as e:
            print(f"제조동 정렬 오류: {e}")
            # 오류 시 기본 순서 반환
            return ['I', 'D', 'K', 'M']

    """
    요약 데이터 생성
    """

    def create_summary(self, result_data, capa_ratios):
        # 제조동별 데이터 추출
        result_data = result_data.copy()
        result_data['Building'] = result_data['Line'].str.split('_').str[0]

        # 제조동별 생산량 집계
        building_qty = result_data.groupby('Building')['Qty'].sum()

        # 제조동별 라인 정보
        building_lines = result_data.groupby('Building')['Line'].nunique()

        # 전체 합계 계산
        total_qty = result_data['Qty'].sum()
        total_capacity = sum(self.line_capacity_data.values())
        total_utilization = (total_qty / total_capacity * 100) if total_capacity > 0 else 0

        # 제조동별 프로젝트-지역 정보 추출
        project_region_data = []

        # 전체 Total 행 먼저 추가
        project_region_data.append({
            'Building(Portion)': 'Total',
            'Line': '-',
            'Capa': f"{total_capacity:,}" if total_capacity > 0 else '',
            'Line_Qty': f"{total_qty:,}",
            'Utilization(%)': f"{total_utilization:.1f}%" if total_utilization > 0 else '',
            'Project': '-',
            'Region': '-',
            'Pjt_Qty': '-',  # 프로젝트별 수량은 총합행에서는 빈값
            'is_total': True  # Total 행 표시용
        })

        # *** 핵심 수정: 제조동별 생산량 기준 정렬 적용 ***
        sorted_buildings = self.get_sorted_buildings(result_data)

        # 정렬된 제조동 순서대로 처리
        for building in sorted_buildings:
            building_data = result_data[result_data['Building'] == building]

            if building_data.empty:
                continue

            # 제조동 전체 정보
            total_qty = building_qty.get(building, 0)
            building_ratio = capa_ratios.get(building, 0)

            # 제조동별 총 생산능력
            building_total_capacity = 0
            building_lines_in_data = building_data['Line'].unique()
            for line in building_lines_in_data:
                if line in self.line_capacity_data:
                    building_total_capacity += self.line_capacity_data[line]

            # 제조동별 가동률 계산
            building_utilization = 0
            if building_total_capacity > 0:
                building_utilization = (total_qty / building_total_capacity) * 100

            # 제조동 별 total 행
            project_region_data.append({
                'Building(Portion)': f"{building}({building_ratio:.1f})",
                'Line': 'Total',
                'Capa': f"{building_total_capacity:,}" if building_total_capacity > 0 else '',
                'Line_Qty': f"{total_qty:,}",  # 라인별 총합 컬럼
                'Utilization(%)': f"{building_utilization:.1f}%" if building_utilization > 0 else '',
                'Project': '-',
                'Region': '-',
                'Pjt_Qty': '-',  # 프로젝트별 수량은 총합행에서는 빈값
                'is_total': True  # Total 행 표시용
            })

            # 라인별 상세정보
            line_data = building_data.groupby('Line').agg({
                'Qty': 'sum',
                'Project': lambda x: list(x.unique()),  # 해당 라인의 모든 프로젝트
                'Item': 'first'  # 지역 추출용
            }).reset_index()

            # *** 수정: 라인 순서로 정렬 (제조동 내에서는 라인명 기준 정렬) ***
            line_data = line_data.sort_values('Line', key=lambda x: x.map(sort_line))

            for _, row in line_data.iterrows():
                line = row['Line']
                line_qty = row['Qty']
                projects = sorted(row['Project'])  # 프로젝트명 정렬

                # 라인별 생산능력과 가동률
                line_capacity = self.line_capacity_data.get(line, 0)
                line_utilization = self.line_utilization_data.get(line, 0)

                # 프로젝트별 세부정보
                for i, project in enumerate(projects):
                    project_data = building_data[
                        (building_data['Line'] == line) &
                        (building_data['Project'] == project)
                        ]

                    if not project_data.empty:
                        project_qty = project_data['Qty'].sum()

                        # 지역 추출 (첫번째 아이템에서)
                        first_item = str(project_data['Item'].iloc[0])
                        region = ''
                        try:
                            proj_idx = first_item.find(project)
                            if proj_idx >= 0 and proj_idx + len(project) < len(first_item):
                                region_char = first_item[proj_idx + len(project)]
                                if region_char.isupper() and region_char.isalpha():
                                    region = region_char
                        except:
                            region = ''

                        # 첫 번째 프로젝트에만 라인 정보와 Capa, Utilization 표시
                        if i == 0:
                            project_region_data.append({
                                'Building(Portion)': '',
                                'Line': f"  {line}",  # 들여쓰기
                                'Capa': f"{line_capacity:,}" if line_capacity > 0 else '',
                                'Line_Qty': f"{line_qty:,}",  # 라인별 총수량
                                'Utilization(%)': f"{line_utilization:.1f}%" if line_utilization > 0 else '',
                                'Project': project,
                                'Region': region,
                                'Pjt_Qty': f"{project_qty:,}",  # 프로젝트별 수량
                                'is_total': False
                            })
                        else:
                            # 두 번째 프로젝트부터는 빈 라인으로 표시
                            project_region_data.append({
                                'Building(Portion)': '',
                                'Line': f"  {line}",  # 같은 라인임을 명시 (병합을 위해)
                                'Capa': '',
                                'Line_Qty': '',  # 두 번째 프로젝트부터는 빈값
                                'Utilization(%)': '',
                                'Project': project,
                                'Region': region,
                                'Pjt_Qty': f"{project_qty:,}",  # 프로젝트별 수량만 표시
                                'is_total': False
                            })

        # DataFrame으로 변환 (정렬은 이미 위에서 처리됨)
        summary_df = pd.DataFrame(project_region_data)

        if summary_df.empty:
            return pd.DataFrame()

        return summary_df

    """
    테이블 업데이트
    """

    def update_table(self, summary_df):
        if summary_df.empty:
            self.clear_table()
            return

        # 표시용 컬럼만 추출 (is_total은 제외하고 표시)
        display_columns = [col for col in summary_df.columns if col != 'is_total']
        fixed_columns = {
            0: 150,  # Building(Portion) 컬럼만 고정
        }

        # 헤더 설정
        self.summary_table.setup_header(display_columns, fixed_columns=fixed_columns, resizable=False)
        self.summary_table.setRowCount(0)  # 기존 데이터 클리어

        # 제조동별 병합
        building_spans = {}
        line_spans = {}

        # 제조동별 행 범위 찾기
        for row_idx, (_, row) in enumerate(summary_df.iterrows()):
            is_total_row = row.get('is_total', False)

            # 행 데이터 생성 (is_total 제외)
            row_data = [str(row[col]) if pd.notna(row[col]) else "" for col in summary_df.columns if col != 'is_total']

            # Total 행은 is_total=True로 추가
            if is_total_row:
                self.summary_table.add_custom_row(row_data, is_total=True)
            else:
                # 일반 행은 기본 스타일로 추가
                self.summary_table.add_custom_row(row_data)

            # 제조동별 병합 정보 수집
            building_portion = row['Building(Portion)']
            if building_portion and '(' in building_portion and building_portion != 'Total':
                building_name = building_portion.split('(')[0]
                building_spans[building_name] = {'start_row': row_idx, 'rows': [row_idx]}

                # 같은 제조동의 다음 행들 찾기
                for next_idx in range(row_idx + 1, len(summary_df)):
                    next_row = summary_df.iloc[next_idx]
                    next_building = next_row['Building(Portion)']
                    if next_building and '(' in next_building:
                        break
                    building_spans[building_name]['rows'].append(next_idx)

            # 라인별 병합 정보 수집
            line_name = row['Line'].strip()
            if line_name and line_name != 'Total' and '_' in line_name:
                if line_name not in line_spans:
                    line_spans[line_name] = {'start_row': row_idx, 'rows': [row_idx]}
                else:
                    line_spans[line_name]['rows'].append(row_idx)

        # 모든 셀 가운데 정렬 적용 (병합 전)
        for row in range(self.summary_table.rowCount()):
            for col in range(self.summary_table.columnCount()):
                item = self.summary_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        # 제조동별 병합 적용
        for building_name, span_info in building_spans.items():
            rows = span_info['rows']
            if len(rows) > 1:
                start_row = min(rows)
                row_count = len(rows)
                self.summary_table.merge_cells(start_row, 0, row_count, 1)

                # 병합된 셀 가운데 정렬 (이미 위에서 설정했지만 명시적으로 재설정)
                item = self.summary_table.item(start_row, 0)
                if item:
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        # 라인별 병합 적용
        for line_name, span_info in line_spans.items():
            rows = span_info['rows']
            if len(rows) > 1 and rows == list(range(min(rows), min(rows) + len(rows))):
                start_row = min(rows)
                row_count = len(rows)

                # Line, Capa, Line_Qty, Utilization 컬럼 병합
                for col_idx in [1, 2, 3, 4]:  # Line, Capa, Line_Qty, Utilization
                    self.summary_table.merge_cells(start_row, col_idx, row_count, 1)
                    item = self.summary_table.item(start_row, col_idx)
                    if item:
                        # 모든 컬럼 가운데 정렬로 통일
                        item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        # 행 높이 조정
        for row in range(self.summary_table.rowCount()):
            self.summary_table.setRowHeight(row, 30)

        # 첫 번째 컬럼은 조금 더 넓게
        self.summary_table.setColumnWidth(0, 150)

    """
    테이블 초기화
    """

    def clear_table(self):
        self.summary_table.setRowCount(0)
        self.summary_table.setColumnCount(0)