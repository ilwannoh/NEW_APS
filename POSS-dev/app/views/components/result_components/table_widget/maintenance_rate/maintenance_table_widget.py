from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import pandas as pd
from app.views.components.common.custom_table import CustomTable
from app.utils.sort_line import sort_line
from app.utils.item_key_manager import ItemKeyManager

"""
유지율 표시를 위한 테이블 위젯 기본 클래스
"""
class MaintenanceTableWidget(CustomTable):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 라인별 배경색 정의
        self.group_colors = [
            QColor('#ffffff'),  # 흰색
            QColor('#f5f5f5'),  # 연한 회색
        ]
        self.setup_maintenance_style()
        
    """
    유지율 테이블 전용 스타일 설정
    """
    def setup_maintenance_style(self):
        additional_style = """
            QHeaderView::section {
                padding: 6px 8px;
            }
            QTableWidget::item {
                padding: 4px 6px;
            }
        """
        current_style = self.styleSheet()
        self.setStyleSheet(current_style + additional_style)

    """
    헤더 설정 (CustomTable의 setup_header 메서드 오버라이드)
    """
    def setup_header(self, header_labels):
        # CustomTable의 setup_header 호출
        super().setup_header(
            header_labels,
            fixed_columns={0: 80, 1: 80, 2: 250},  # Line과 Shift 열을 고정 너비로 설정
            resizable=False  # 나머지는 균등 분할
        )
        
    """
    그룹 헤더 행 생성
    """
    def create_group_row(self, line, shift, prev_sum, curr_sum, maintenance_sum, group_index):
        # CustomTable의 add_custom_row 사용
        row_data = [
            line,
            shift,
            "",  # Item/RMC는 비워둠
            f"{prev_sum:,.0f}",
            f"{curr_sum:,.0f}",
            f"{maintenance_sum:,.0f}"
        ]
        
        # 라인별 그룹 헤더 배경색 
        bg_color = QColor('#E8E8E8')

        # 스타일 정의
        styles = {}
        for col in range(6):
            style = {'background': bg_color}
            if col >= 3:  # 숫자 열은 우측 정렬
                style['alignment'] = Qt.AlignRight | Qt.AlignVCenter
            else:
                style['alignment'] = Qt.AlignCenter | Qt.AlignVCenter

            styles[col] = style
        
        self.add_custom_row(row_data, styles, is_total=True, is_header=True)
        
    """
    일반 데이터 행 생성
    """
    def create_data_row(self, line="", shift="", item_text="", prev_plan=0, 
                       curr_plan=0, maintenance=0, is_modified=False, group_index=0):
        # CustomTable의 add_custom_row 사용
        row_data = [
            line,
            shift,
            item_text,
            f"{prev_plan:,.0f}",
            f"{curr_plan:,.0f}",
            f"{maintenance:,.0f}"
        ]
        
        # 라인별 배경색 선택
        bg_color = self.group_colors[group_index % len(self.group_colors)]
        
        # 스타일 정의
        styles = {}
        for col in range(6):
            style = {'background': bg_color}
            if col >= 3:  # 숫자 열은 우측 정렬
                style['alignment'] = Qt.AlignRight | Qt.AlignVCenter
            else:
                style['alignment'] = Qt.AlignCenter | Qt.AlignVCenter
            
            # 변경된 항목 강조
            if is_modified and col == 4:  # curr_plan 열
                style['foreground'] = QColor('#F8AC59')
                # 폰트 굵게 만들기
                font = QFont()
                font.setBold(True)
                style['font'] = font
            
            styles[col] = style
        
        self.add_custom_row(row_data, styles)
        
    """
    총계 행 생성
    """
    def create_total_row(self, total_prev, total_curr, total_maintenance):
        row_data = [
            "Total",
            "Total",
            "Total",
            f"{total_prev:,.0f}",
            f"{total_curr:,.0f}",
            f"{total_maintenance:,.0f}"
        ]
        
        self.add_custom_row(row_data, is_total=True)
    
    """
    테이블에 데이터 채우기
    """
    def _populate_table(self, df_data, modified_item_keys, modified_rmc_keys=None, item_field='Item'):
        # 기존 데이터 초기화
        self.setRowCount(0)
        
        # Line-Shift별 그룹화
        groups = {}
        total_prev = 0
        total_curr = 0
        total_maintenance = 0

        # Line별로 그룹화
        line_shift_groups = {}
        
        for idx, row in df_data.iterrows():
            line = str(row['Line'])
            shift = str(row['Shift'])
            item_value = str(row[item_field])
            prev_plan = row['prev_plan'] if not pd.isna(row['prev_plan']) else 0
            curr_plan = row['curr_plan'] if not pd.isna(row['curr_plan']) else 0
            maintenance = row['maintenance'] if not pd.isna(row['maintenance']) else 0
            
            # 그룹 키 생성 (Line-Shift)
            group_key = f"{line}_{shift}" if shift else line
            
            if group_key not in groups:
                groups[group_key] = {
                    'line': line,
                    'shift': shift,
                    'items': [],
                    'prev_sum': 0,
                    'curr_sum': 0,
                    'maintenance_sum': 0
                }
            
            # 항목 추가
            groups[group_key]['items'].append({
                item_field.lower(): item_value,
                'prev_plan': prev_plan,
                'curr_plan': curr_plan, 
                'maintenance': maintenance
            })
            
            # 그룹 합계 업데이트
            groups[group_key]['prev_sum'] += prev_plan
            groups[group_key]['curr_sum'] += curr_plan
            groups[group_key]['maintenance_sum'] += maintenance
            
            # 전체 합계 업데이트
            total_prev += prev_plan
            total_curr += curr_plan
            total_maintenance += maintenance

            # 라인-교대 조합별 색상 인덱스 추적
            line_shift_key = f"{line}_{shift}"
            if line_shift_key not in line_shift_groups:
                line_shift_groups[line_shift_key] = len(line_shift_groups)  # 라인-교대 조합이 처음 나올 때 인덱스 부여
        
        # Line별 그룹 정보 수집 (같은 Line끼리 묶기 위함)
        line_groups = {}
        for group_key, group_data in sorted(groups.items()):
            line = group_data['line']
            if line not in line_groups:
                line_groups[line] = []
            line_groups[line].append(group_key)

        # Line 순서대로 정렬 
        sorted_lines = sorted(line_groups.keys(), key=lambda x: sort_line(x))
        ordered_line_groups = {}

        # 각 라인 내 시프트 순서대로 정렬
        for line in sorted_lines:
            group_keys = line_groups[line]
            # 시프트 순서대로 정렬
            sorted_group_keys = sorted(group_keys, key=lambda x:int(groups[x]['shift']) if groups[x]['shift'].isdigit() else 999)
            ordered_line_groups[line] = sorted_group_keys

        # 병합을 위한 딕셔너리
        line_spans = {}
        shift_spans = {}
        
        # 테이블 행 추가 및 병합 정보 수집
        for line, group_keys in ordered_line_groups.items():
            line_start_row = self.rowCount()  # 라인의 시작 행
            
            for group_key in group_keys:
                group_data = groups[group_key]
                shift = group_data['shift']
                line_shift_key = f"{line}_{shift}"  
                line_group_index = line_shift_groups[line_shift_key]

                # 교대별 시작 행 인덱스 기록
                shift_start_row = self.rowCount()

                # 그룹 헤더 행 추가
                self.create_group_row(
                    group_data['line'],
                    group_data['shift'],
                    group_data['prev_sum'],
                    group_data['curr_sum'],
                    group_data['maintenance_sum'],
                    line_group_index
                )
                
                # 데이터 행 추가
                item_key = item_field.lower()
                for item_data in sorted(group_data['items'], key=lambda x: x[item_key]):
                    # 수정 여부 확인
                    item_value = item_data[item_key]
                    line_value = group_data['line']
                    shift_value = group_data['shift']
                    
                    if item_field == 'Item':
                        is_modified = False
                        # 1. ID 기반 키 먼저 확인 (우선순위)
                        if '_id' in item_data:
                            id_key = f"id_{item_data['_id']}"
                            is_modified = id_key in modified_item_keys
                        
                        # 2. ID로 찾지 못한 경우에만 (Line, Time, Item) 조합 키 확인 (후순위)
                        if not is_modified:
                            current_key = ItemKeyManager.get_item_by_not_id(line_value, shift_value, item_value)
                            is_modified = current_key in modified_item_keys
                    elif item_field == 'RMC':
                        is_modified = False
                        
                        # 1. ID 기반 키 먼저 확인 (우선순위)
                        if '_id' in item_data:
                            id_key = f"id_{item_data['_id']}"
                            is_modified = modified_rmc_keys and id_key in modified_rmc_keys
                        
                        # 2. ID로 찾지 못한 경우에만 (Line, Time, RMC) 조합 키 확인 (후순위)
                        if not is_modified:
                            time_value = shift_value
                            if shift_value.isdigit():
                                time_value = int(shift_value)
                                        
                    # 데이터 행 생성
                    self.create_data_row(
                        "-",  # line은 그룹 헤더에만 표시
                        "-",  # shift는 그룹 헤더에만 표시
                        item_value,
                        item_data['prev_plan'],
                        item_data['curr_plan'],
                        item_data['maintenance'],
                        is_modified,
                        line_group_index
                    )

                # 교대별 행 수 계산 및 Shift 병합 정보 저장
                shift_end_row = self.rowCount() - 1
                shift_row_count = shift_end_row - shift_start_row + 1

                if shift_row_count > 1:
                    shift_spans[shift_start_row] = {
                        'row_count': shift_row_count,
                        'shift': shift
                    }

            # 라인별 행 수 계산 및 Line 병합 정보 저장
            line_end_row = self.rowCount() - 1
            line_row_count = line_end_row - line_start_row + 1
                
            if line_row_count > 1:
                line_spans[line_start_row] = {
                    'row_count': line_row_count,
                    'line': line
                }
        
        # 총계 행 추가
        self.create_total_row(total_prev, total_curr, total_maintenance)

        # Line 열 병합 적용 (먼저 적용)
        for start_row, span_info in line_spans.items():
            row_count = span_info['row_count']
            
            # Line 열 (0번) 병합
            self.merge_cells(start_row, 0, row_count, 1)
            line_item = self.item(start_row, 0)
            if line_item:
                line_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        
        # Shift 열 병합 적용 (나중에 적용)
        for start_row, span_info in shift_spans.items():
            row_count = span_info['row_count']
            
            # Shift 열 (1번) 병합
            self.merge_cells(start_row, 1, row_count, 1)
            shift_item = self.item(start_row, 1)
            if shift_item:
                shift_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)


"""
Item별 유지율 테이블 위젯
"""
class ItemMaintenanceTable(MaintenanceTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_header(["Line", "Shift", "Item", "Previous", "Current", "Maintenance"])
        
    def populate_data(self, df, modified_item_keys):
        """아이템별 데이터 표시"""
        if df is None or df.empty:
            return
            
        df_data = df[df['Line'] != 'Total']  # Total 행만 필터링
        
        # 테이블에 데이터 표시
        self._populate_table(df_data, modified_item_keys, item_field='Item')


"""
RMC별 유지율 테이블 위젯
"""
class RMCMaintenanceTable(MaintenanceTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_header(["Line", "Shift", "RMC", "Previous", "Current", "Maintenance"])
        
    def populate_data(self, df, modified_item_keys, modified_rmc_keys):
        """RMC별 데이터 표시"""
        if df is None or df.empty:
            return
        
        # modified_rmc_keys가 None이면 빈 집합으로 초기화
        if modified_rmc_keys is None:
            modified_rmc_keys = set()
            
        df_data = df[df['Line'] != 'Total']  # Total 행만 필터링
        
        # 테이블에 데이터 표시
        self._populate_table(df_data, modified_item_keys, modified_rmc_keys, item_field='RMC')