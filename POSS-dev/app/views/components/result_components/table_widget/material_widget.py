from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QToolTip)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
import pandas as pd

from app.analysis.output.material_shortage_analysis import MaterialShortageAnalyzer

class MaterialWidget(QWidget):
    # 자재 부족 정보 전달용 시그널
    material_shortage_updated = pyqtSignal(dict)  # 자재 부족 정보 전달
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shortage_items_table = None
        self.material_analyzer = None
        self.result_data = None
        self.shortage_results = {}
        self.current_sort_column = 0  # 현재 정렬 중인 컬럼 인덱스 (기본: Material)
        self.current_sort_order = Qt.DescendingOrder  # 정렬 방향 (기본: 내림차순)
        self.shortage_df = None  # 데이터프레임 저장용 변수
        self.init_ui()
    
    """UI 초기화"""
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 자재 부족 테이블 생성
        self.create_shortage_table()
        layout.addWidget(self.shortage_items_table)
    
    """자재 부족 테이블 생성"""
    def create_shortage_table(self):
        self.shortage_items_table = QTableWidget()
        self.shortage_items_table.setColumnCount(4)
        
        # 명시적으로 컬럼 헤더 설정
        headers = ["Material", "Model", "Shortage", "Shift"]
        self.shortage_items_table.setHorizontalHeaderLabels(headers)
        
        # 컬럼 너비 설정
        self.shortage_items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)  # Material
        self.shortage_items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)      # Model
        self.shortage_items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)  # Shortage
        self.shortage_items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)  # Shift
        
        # 기본 컬럼 너비 설정
        self.shortage_items_table.setColumnWidth(0, 250)  # Material 컬럼 너비 증가
        self.shortage_items_table.setColumnWidth(2, 180)  # Shortage 컬럼 너비 증가
        self.shortage_items_table.setColumnWidth(3, 80)   # Shift
        
        # 행 번호 스타일 설정
        self.shortage_items_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.shortage_items_table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333333;
                padding: 4px;
                font-weight: normal;
                border: 1px solid #e0e0e0;
                text-align: center;
            }
        """)
        
        # 테이블 스타일 적용
        self.shortage_items_table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #f0f0f0;
                background-color: white;
                border-radius: 0;
                margin-top: 0px;
                outline: none;
            }
            QHeaderView {
                border: none;
                outline: none;
            }                                       
            QHeaderView::section {
                background-color: #1428A0;
                color: white;
                padding: 4px;
                font-weight: bold;
                border: 1px solid #1428A0;
                border-radius: 0;
                outline: none;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 0;
                outline: none;
            }
            QTableWidget::item:selected {
                background-color: #0078D7;
                color: white;
                border-radius: 0;
                outline: none;
            }
            QTableWidget::focus {
                outline: none;
                border: none;
            }
        """)
        
        # 컬럼 헤더 클릭 시 정렬 기능 활성화
        self.shortage_items_table.setSortingEnabled(True)
        self.shortage_items_table.horizontalHeader().setSortIndicatorShown(True)
        self.shortage_items_table.horizontalHeader().sortIndicatorChanged.connect(self.on_sort_indicator_changed)
        
        # 마우스 트래킹 및 이벤트 연결
        self.shortage_items_table.setMouseTracking(True)
        self.shortage_items_table.cellEntered.connect(self.show_shortage_tooltip)
        
        # 초기 메시지 설정 (영어로 변경)
        self.set_initial_message("Loading material shortage data...")
    
    """초기 메시지 설정"""
    def set_initial_message(self, message):
        self.shortage_items_table.setRowCount(1)
        empty_item = QTableWidgetItem(message)
        empty_item.setTextAlignment(Qt.AlignCenter)
        self.shortage_items_table.setItem(0, 0, empty_item)
        self.shortage_items_table.setSpan(0, 0, 1, 4)  # 4개 컬럼 병합
    
    """자재 부족 분석기 설정"""
    def set_material_analyzer(self, analyzer):
        self.material_analyzer = analyzer
    
    """자재 부족량 분석 실행"""
    def run_analysis(self, result_data=None):
        if result_data is None:
            return
            
        self.result_data = result_data
        
        # 분석기가 없는 경우 생성
        if not self.material_analyzer:
            self.material_analyzer = MaterialShortageAnalyzer()
        
        # 분석 실행
        self.shortage_results = self.material_analyzer.analyze_material_shortage(result_data)
        
        # 테이블 업데이트
        self.update_shortage_items_table()
        
        # 부족 정보 시그널 발생
        # self.material_shortage_updated.emit(self.shortage_results)
    
    """정렬 인디케이터가 변경될 때 호출되는 메서드"""
    def on_sort_indicator_changed(self, column_index, sort_order):
        self.current_sort_column = column_index
        self.current_sort_order = sort_order
        
        # 현재 데이터프레임이 있으면 정렬 적용
        if self.shortage_df is not None and not self.shortage_df.empty:
            self.apply_sort_to_table()
    
    """현재 설정된 정렬 기준으로 테이블 데이터 정렬"""
    def apply_sort_to_table(self):
        # 컬럼 인덱스에 따른 정렬 컬럼 이름 결정
        column_names = ['Material', 'Item', 'Shortage', 'Shift']
        sort_column = column_names[self.current_sort_column]
        
        # 정렬 방향에 따라 오름차순/내림차순 결정
        ascending = self.current_sort_order == Qt.AscendingOrder
        
        # 데이터프레임 정렬
        self.shortage_df = self.shortage_df.sort_values(by=sort_column, ascending=ascending)
        
        # 정렬된 데이터로 테이블 업데이트
        self.populate_table_from_dataframe()
    
    """데이터프레임의 내용으로 테이블 채우기"""
    def populate_table_from_dataframe(self):
        # 테이블 초기화
        self.shortage_items_table.setSortingEnabled(False)  # 정렬 기능 임시 비활성화
        self.shortage_items_table.clearContents()
        self.shortage_items_table.setRowCount(len(self.shortage_df))
        
        # 자재별 그룹 관리를 위한 변수
        current_material = None
        material_start_row = 0
        material_count = 0
        
        # 테이블에 데이터 추가
        for i, (_, row) in enumerate(self.shortage_df.iterrows()):
            material = row['Material']
            item = row['Item']  # 아이템(모델) 코드
            shortage = row['Shortage']
            shift = row['Shift']
            
            # 자재 컬럼
            material_cell = QTableWidgetItem(str(material))
            material_cell.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.shortage_items_table.setItem(i, 0, material_cell)
            
            # 모델(Item) 컬럼
            item_cell = QTableWidgetItem(str(item))
            item_cell.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.shortage_items_table.setItem(i, 1, item_cell)
            
            # 부족량 컬럼 (QTableWidgetItem에 데이터 정렬을 위한 숫자형 값도 저장)
            shortage_cell = QTableWidgetItem()
            shortage_cell.setData(Qt.DisplayRole, f"{int(shortage):,}")  # 표시 형식
            shortage_cell.setData(Qt.UserRole, int(shortage))  # 정렬용 값
            shortage_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.shortage_items_table.setItem(i, 2, shortage_cell)
            
            # 시프트 컬럼 (QTableWidgetItem에 데이터 정렬을 위한 숫자형 값도 저장)
            shift_cell = QTableWidgetItem()
            shift_cell.setData(Qt.DisplayRole, str(int(shift)))  # 표시 형식
            shift_cell.setData(Qt.UserRole, int(shift))  # 정렬용 값
            shift_cell.setTextAlignment(Qt.AlignCenter)
            self.shortage_items_table.setItem(i, 3, shift_cell)

            # 자재별 그룹핑 처리
            if current_material != material:
                # 새 자재로 시작할 때
                if i > 0 and material_count > 1:
                    # 이전 자재 그룹 병합
                    self.shortage_items_table.setSpan(material_start_row, 0, material_count, 1)
                
                # 새 자재 그룹 시작
                current_material = material
                material_start_row = i
                material_count = 1
            else:
                # 같은 자재 그룹 계속
                material_count += 1
        
        # 마지막 자재 그룹 병합
        if material_count > 1:
            self.shortage_items_table.setSpan(material_start_row, 0, material_count, 1)
        
        # 행 높이 설정
        for row in range(len(self.shortage_df)):
            self.shortage_items_table.setRowHeight(row, 25)
            
        # 정렬 상태 복원
        self.shortage_items_table.horizontalHeader().setSortIndicator(
            self.current_sort_column, self.current_sort_order)
        self.shortage_items_table.setSortingEnabled(True)  # 정렬 기능 다시 활성화
    
    """자재 부족 항목 테이블 업데이트"""
    def update_shortage_items_table(self):
        if not self.material_analyzer:
            self.set_initial_message("Material shortage analyzer is not initialized.")
            return
        
        try:
            # 모든 부족 항목 데이터를 수동으로 구성
            shortage_items = []
            
            # shortage_results에서 직접 데이터 가져오기
            # 형식: {item_code: [{shift, material, shortage}]}
            for item_code, shortages in self.shortage_results.items():
                for shortage_info in shortages:
                    shortage_items.append({
                        'Material': shortage_info.get('material', 'Unknown'),
                        'Item': item_code,
                        'Shortage': shortage_info.get('shortage', 0),
                        'Shift': shortage_info.get('shift', 0)
                    })
            
            # 부족 항목이 없으면 메시지 표시하고 종료
            if not shortage_items:
                self.set_initial_message("No material shortage items found.")
                return
            
            # 부족 항목을 DataFrame으로 변환
            self.shortage_df = pd.DataFrame(shortage_items)
            
            # 초기 정렬: Material과 Shift로 정렬
            self.shortage_df = self.shortage_df.sort_values(['Material', 'Shift', 'Item'])
            
            # 테이블 초기화
            self.shortage_items_table.clear()
            self.shortage_items_table.clearSpans()
            self.shortage_items_table.setRowCount(len(self.shortage_df))
            self.shortage_items_table.setColumnCount(4)
            self.shortage_items_table.setHorizontalHeaderLabels(["Material", "Model", "Shortage", "Shift"])
            
            # 데이터프레임을 사용하여 테이블 채우기
            self.populate_table_from_dataframe()
            
            # 컬럼 너비 설정
            self.shortage_items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)  # Material
            self.shortage_items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)      # Model
            self.shortage_items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)  # Shortage
            self.shortage_items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)  # Shift
            
            # Material과 Shortage 컬럼 너비 증가
            self.shortage_items_table.setColumnWidth(0, 250)  # Material 컬럼 너비 증가
            self.shortage_items_table.setColumnWidth(2, 180)  # Shortage 컬럼 너비 증가
            self.shortage_items_table.setColumnWidth(3, 80)   # Shift
            
            print(f"자재 부족 테이블 업데이트 완료: {len(self.shortage_df)}행")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.set_initial_message(f"Error updating table: {str(e)}")
    
    """테이블 셀에 마우스 올릴 때 상세 정보 툴팁 표시"""
    def show_shortage_tooltip(self, row, column):
        if self.material_analyzer is None:
            return
                
        # 현재 셀의 아이템
        material_item = self.shortage_items_table.item(row, 0)  # Material 컬럼
        model_item = self.shortage_items_table.item(row, 1)     # Model 컬럼
        
        if material_item is None or model_item is None:
            return
                
        # 모델 코드 가져오기
        model_code = model_item.text()
        material_code = material_item.text()
        
        if not model_code or not material_code:
            return
                
        # 해당 모델의 부족 정보 가져오기
        shortages = self.material_analyzer.get_item_shortages(model_code)
        if not shortages:
            return
                
        # 툴팁 내용 생성
        tooltip_text = f"<b>{model_code}</b> Material Shortage Details:<br><br>"
        tooltip_text += "<table border='1' cellspacing='0' cellpadding='3'>"
        tooltip_text += "<tr style='background-color:#f0f0f0'><th>Material</th><th>Shift</th><th>Shortage</th></tr>"
        
        for shortage in shortages:
            if shortage.get('material') == material_code:  # 현재 선택된 자재와 일치하는 항목만 표시
                tooltip_text += f"<tr>"
                tooltip_text += f"<td>{shortage.get('material', 'Unknown')}</td>"
                tooltip_text += f"<td align='center'>{shortage.get('shift', 0)}</td>"
                tooltip_text += f"<td align='right' style='color:red'>{int(shortage.get('shortage', 0)):,}</td>"
                tooltip_text += f"</tr>"
                
        tooltip_text += "</table>"
        
        # 현재 마우스 위치에 툴팁 표시
        QToolTip.showText(QCursor.pos(), tooltip_text)
    
    """테이블 객체 반환"""
    def get_table(self):
        return self.shortage_items_table
    
    """자재 부족 분석기 반환"""
    def get_material_analyzer(self):
        return self.material_analyzer
    
    """부족 결과 반환"""
    def get_shortage_results(self):
        return self.shortage_results