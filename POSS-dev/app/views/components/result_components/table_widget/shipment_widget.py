from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QProgressBar, QSplitter, QFrame, QToolTip)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont, QPainter, QPen, QPalette
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from app.analysis.output.this_week_shipment import analyze_and_get_results
from app.resources.fonts.font_manager import font_manager
from PyQt5.QtWidgets import QApplication

"""당주 출하 분석 위젯"""
class ShipmentWidget(QWidget):
    
    # 출하 실패 정보 전달용 시그널
    shipment_status_updated = pyqtSignal(dict)  # 실패 아이템 정보 전달
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_df = None
        self.summary = None
        self.analysis_df = None
        self.failure_items = {}  # 아이템별 실패 정보 저장
        self.failed_models_data = []  # 실패 모델 데이터 저장 (정렬용)
        self.sort_column = 0  # 정렬 기준 컬럼
        self.sort_order = Qt.AscendingOrder  # 정렬 방향
        self.last_analyzed_data_hash = None
        self.init_ui()
        
    def init_ui(self):
        # 폰트 정보 가져오기
        self.bold_font_family = font_manager.get_just_font("SamsungOne=700").family()
        self.regular_font_family = font_manager.get_just_font("SamsungOne=400").family()
        
        # 전역 툴팁 스타일 설정 - SamsungOne 폰트 적용
        tooltip_font = QFont(self.regular_font_family, 10)
        QToolTip.setFont(tooltip_font)
        
        # 툴팁 색상 및 스타일 설정
        app = QApplication.instance()
        palette = QToolTip.palette()
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 225))  # 연한 노란색 배경
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))        # 검은색 텍스트
        QToolTip.setPalette(palette)
        
        # 툴팁의 스타일시트 설정
        tooltip_style = f"""
        QToolTip {{
            font-family: {self.regular_font_family};
            font-size: 10pt;
            background-color: #FFFDE7;
            color: #000000;
            border: 1px solid #FBC02D;
            border-radius: 4px;
            padding: 2px;
        }}
        """
        self.setStyleSheet(tooltip_style)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 메인 레이아웃에 여백 추가
        main_layout.setSpacing(10)  # 위젯 간 여백 추가
        
        # 상단 섹션 - 통계 정보
        self.top_section = QWidget()
        top_layout = QVBoxLayout(self.top_section)
        top_layout.setContentsMargins(5, 5, 5, 5)  # 상단 섹션 여백 추가
        top_layout.setSpacing(8)  # 위젯 간 여백 설정
        
        # 배경색 및 테두리 제거
        self.top_section.setStyleSheet("background-color: transparent; border: none;")
        
        top_title = QLabel("Shipment Satisfaction Rate")
        top_title.setFont(QFont(self.bold_font_family, 12))
        top_title.setContentsMargins(0, 0, 0, 5)  # 제목 아래 여백 추가
        top_layout.addWidget(top_title)
        
        # 만족률 카드 컨테이너
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 5)  # 카드 컨테이너 아래 여백 추가
        cards_layout.setSpacing(10)  # 카드 간 여백 추가
        
        cards_container.setStyleSheet("background-color: transparent; border: none;")
        
        # 수량 기준 만족률 카드
        qty_card = QFrame()
        qty_card.setFrameShape(QFrame.NoFrame)
        qty_card.setStyleSheet("background-color: transparent; border: none;")
        qty_card_layout = QVBoxLayout(qty_card)
        qty_card_layout.setContentsMargins(5, 5, 5, 5)  # 카드 내부 여백 추가
        qty_card_layout.setSpacing(5)  # 카드 내부 요소 간 여백
        
        qty_title = QLabel("Qty-based Satisfaction Rate")
        qty_title.setFont(QFont(self.bold_font_family, 10))
        qty_card_layout.addWidget(qty_title)
        
        # 프로그레스바
        self.qty_progress = QProgressBar()
        self.qty_progress.setTextVisible(True)
        self.qty_progress.setFixedHeight(25)  # 높이 설정
        self.qty_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 5px;
                text-align: center;
                background-color: #F0F0F0;
                color: black;
                font-weight: bold;
                font-family: {self.bold_font_family};
            }}
            QProgressBar::chunk {{
                background-color: #5D92EB;
                border-radius: 5px;
            }}
        """)
        qty_card_layout.addWidget(self.qty_progress)
        
        self.qty_detail = QLabel("0 / 0 (0.0%)")  # 소수점 1자리 표시
        self.qty_detail.setAlignment(Qt.AlignCenter)
        self.qty_detail.setFont(QFont(self.regular_font_family))
        qty_card_layout.addWidget(self.qty_detail)
        
        # 모델 기준 만족률 카드
        model_card = QFrame()
        model_card.setFrameShape(QFrame.NoFrame)
        model_card.setStyleSheet("background-color: transparent; border: none;")
        model_card_layout = QVBoxLayout(model_card)
        model_card_layout.setContentsMargins(5, 5, 5, 5)  # 카드 내부 여백 추가
        model_card_layout.setSpacing(5)  # 카드 내부 요소 간 여백
        
        model_title = QLabel("Model-based Satisfaction Rate")
        model_title.setFont(QFont(self.bold_font_family, 10))
        model_card_layout.addWidget(model_title)
        
        # 프로그레스바 유지
        self.model_progress = QProgressBar()
        self.model_progress.setTextVisible(True)
        self.model_progress.setFixedHeight(25)  # 높이 설정
        self.model_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 5px;
                text-align: center;
                background-color: #F0F0F0;
                color: black;
                font-weight: bold;
                font-family: {self.bold_font_family};
            }}
            QProgressBar::chunk {{
                background-color: #76C47E;
                border-radius: 5px;
            }}
        """)
        model_card_layout.addWidget(self.model_progress)
        
        self.model_detail = QLabel("0 / 0 (0.0%)")
        self.model_detail.setAlignment(Qt.AlignCenter)
        self.model_detail.setFont(QFont(self.regular_font_family))
        model_card_layout.addWidget(self.model_detail)
        
        # 카드 추가
        cards_layout.addWidget(qty_card)
        cards_layout.addWidget(model_card)
        top_layout.addWidget(cards_container)
        
        # 통계 테이블 - 정확히 2행만 표시
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setRowCount(2)  # 정확히 2행만 설정 (Model 행까지)
        self.stats_table.setHorizontalHeaderLabels(["Category", "Total", "Success", "Success Rate"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stats_table.setFixedHeight(200)  # 2행에 맞게 높이 조정
        
        # 통계 테이블 스타일시트
        self.stats_table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background-color: transparent;
                gridline-color: #E0E0E0;
                font-family: {self.regular_font_family};
            }}
            QHeaderView::section {{
                background-color: #1428A0;
                color: white;
                padding: 4px;
                font-weight: bold;
                border: none;
                font-family: {self.bold_font_family};
            }}
            QTableWidget::item {{
                padding: 4px;
                border-bottom: 1px solid #F0F0F0;
            }}
            QTableWidget::item:selected {{
                background-color: #0078D7;
                color: white;
            }}
        """)
        
        # 기본 통계 행 추가
        self.stats_table.setItem(0, 0, QTableWidgetItem("Quantity (Qty)"))
        self.stats_table.setItem(1, 0, QTableWidgetItem("Model"))
        
        # 폰트 적용
        for row in range(2):
            item = self.stats_table.item(row, 0)
            if item:
                item.setFont(QFont(self.bold_font_family))
        
        top_layout.addWidget(self.stats_table)
        
        # 테이블과 제목 사이 여백 추가
        top_layout.addSpacing(10)
        
        # 하단 섹션 - 출하 실패 모델 테이블
        bottom_title = QLabel("Failed Shipment Models")
        bottom_title.setFont(QFont(self.bold_font_family, 12))
        bottom_title.setContentsMargins(0, 0, 0, 5)  # 제목 아래 여백 추가
        top_layout.addWidget(bottom_title)
        
        self.failed_table = QTableWidget()
        # To_site 컬럼 제거 - 4개 컬럼으로 변경
        self.failed_table.setColumnCount(4)
        
        # 컬럼 이름 변경 - To_site 제거
        self.failed_table.setHorizontalHeaderLabels([
            "Item", "Qty", "SOP", "Qty/SOP"
        ])
        
        # 헤더 높이 설정
        self.failed_table.horizontalHeader().setMinimumHeight(30)
        
        # 컬럼 너비 개별 설정 (비율로)
        self.failed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 수직 헤더 숨김
        self.failed_table.verticalHeader().setVisible(False)
        self.failed_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.failed_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 정렬 기능 추가 - 헤더 클릭 이벤트 연결
        self.failed_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        
        # 테이블 스타일시트 업데이트 - 테두리 추가
        self.failed_table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background-color: transparent;
                gridline-color: #E0E0E0;
                font-family: {self.regular_font_family};
            }}
            QHeaderView::section {{
                background-color: #1428A0;
                color: white;
                padding: 4px;
                font-weight: bold;
                border: none;
                min-height: 30px;
                font-family: {self.bold_font_family};
            }}
            QTableWidget::item {{
                padding: 4px;
                border-bottom: 1px solid #F0F0F0;
            }}
            QTableWidget::item:selected {{
                background-color: #0078D7;
                color: white;
            }}
        """)
        
        top_layout.addWidget(self.failed_table, 1)  # 스트레치 팩터 1로 설정
        
        # top_section만 메인 레이아웃에 추가
        main_layout.addWidget(self.top_section)

    """헤더 클릭 이벤트 처리 - 테이블 정렬"""
    def on_header_clicked(self, column):
        # 같은 컬럼을 다시 클릭한 경우 정렬 방향 변경
        if self.sort_column == column:
            self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.sort_column = column
            self.sort_order = Qt.AscendingOrder
        
        # 정렬 실행
        self.sort_failed_table()

    """실패 테이블 정렬"""
    def sort_failed_table(self):
        # 정렬할 데이터가 없으면 종료
        if not self.failed_models_data:
            return
        
        # 테이블이 비어있거나 메시지만 표시하는 경우
        if self.failed_table.rowCount() == 1 and self.failed_table.columnSpan(0, 0) > 1:
            return
        
        # 컬럼에 따른 정렬 키 함수 정의
        def get_sort_key(item):
            if self.sort_column >= len(item) - 1:  # 마지막 항목은 배경색 정보이므로 제외
                return ""
                
            value = item[self.sort_column]
            
            # 컬럼별 타입 변환 처리
            if self.sort_column == 0:  # Item - 문자열 정렬
                return str(value).lower()  # 대소문자 구분 없이 정렬
                
            elif self.sort_column in [1, 2]:  # Qty, SOP - 숫자 정렬 (To_site 제거로 인덱스 변경)
                # 콤마 제거 후 숫자 변환
                try:
                    if isinstance(value, str) and ',' in value:
                        return float(value.replace(',', ''))
                    else:
                        return float(value) if value else 0
                except (ValueError, TypeError):
                    return 0
                    
            elif self.sort_column == 3:  # Qty/SOP - 백분율 정렬
                # % 제거 후 숫자 변환
                try:
                    if isinstance(value, str) and '%' in value:
                        return float(value.replace('%', ''))
                    else:
                        return float(value) if value else 0
                except (ValueError, TypeError):
                    return 0
                    
            # 기본값
            return str(value).lower() if isinstance(value, str) else value
        
        try:
            # 데이터 정렬
            sorted_data = sorted(self.failed_models_data, key=get_sort_key, 
                                reverse=(self.sort_order == Qt.DescendingOrder))
            
            # 정렬된 데이터로 테이블 갱신
            self.failed_table.setRowCount(len(sorted_data))
            
            for row, row_data in enumerate(sorted_data):
                # 배경색 정보 추출 (마지막 항목)
                background_info = {}
                if len(row_data) > 4 and isinstance(row_data[4], dict) and 'background' in row_data[4]:
                    background_info = row_data[4]['background']
                
                # 테이블에 데이터 설정
                for col in range(min(4, len(row_data))):  # 배경색 정보 항목은 제외
                    # To_site 컬럼 제거로 인한 인덱스 조정
                    source_idx = col if col == 0 else col + 1
                    if source_idx < len(row_data):
                        item = QTableWidgetItem(str(row_data[source_idx]))
                        
                        # 텍스트 정렬 설정
                        if col == 0:  # Item
                            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                        else:  # 나머지 컬럼 (숫자 값)
                            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        
                        # 색상 배경 설정
                        if col == 1 and background_info.get('qty', False):  # Qty 열
                            item.setBackground(QBrush(QColor(255, 235, 235)))
                        
                        if col == 3:  # Qty/SOP 열
                            bg_type = background_info.get('ratio', None)
                            if bg_type == 'red':
                                item.setBackground(QBrush(QColor(255, 200, 200)))
                            elif bg_type == 'orange':
                                item.setBackground(QBrush(QColor(255, 235, 200)))
                        
                        # SOP 불일치 강조 (2번째 컬럼 - SOP)
                        if col == 2 and background_info.get('sop_inconsistent', False):
                            item.setBackground(QBrush(QColor(255, 255, 200)))
                            font = QFont(self.bold_font_family)
                            item.setFont(font)
                        else:
                            # 기본 폰트 적용
                            font = QFont(self.regular_font_family)
                            item.setFont(font)
                        
                        self.failed_table.setItem(row, col, item)
                
                # 행 높이 설정
                self.failed_table.setRowHeight(row, 28)
                
        except Exception as e:
            import traceback
            traceback.print_exc()

    """당주 출하 분석 실행"""    
    def run_analysis(self, result_data=None):
        try:
            # 데이터가 없으면 DataStore에서 가져오기 시도
            from app.models.common.file_store import DataStore
            stored_data = DataStore.get("result_data")
            
            # 직접 전달된 데이터가 없으면 DataStore에서 가져오기 시도
            if result_data is None:
                result_data = stored_data
            
            # 데이터가 여전히 없으면 분석 중단
            if result_data is None:
                self.reset_state()
                return
                
            # 데이터 변경 여부 확인 (해시값 기반)
            current_hash = self._compute_data_hash(result_data)
            
            # 같은 데이터로 이미 분석했고 결과가 있다면 재분석 생략
            if hasattr(self, 'last_analyzed_data_hash') and current_hash == self.last_analyzed_data_hash and self.result_df is not None and hasattr(self, 'failure_items'):
                # 기존 결과로 시그널 재발생
                self.shipment_status_updated.emit(self.failure_items)
                return
            
            # 현재 해시 저장
            self.last_analyzed_data_hash = current_hash
            
            # print("왼쪽 결과 테이블 데이터로 출하 분석 실행")
            
            # 기존 분석 코드 계속 실행
            # analyze_and_get_results 함수 호출 및 반환값 예외 처리
            result = analyze_and_get_results(result_data=result_data)
            
            # None이 반환된 경우 처리
            if result is None:
                self.reset_state()  # 상태 초기화
                return
            
            # 반환값이 3개 값을 포함한 튜플인지 확인
            if isinstance(result, tuple) and len(result) == 3:
                self.result_df, self.summary, self.analysis_df = result
            else:
                # 반환값이 예상과 다른 형태인 경우 (단일값 등)
                self.result_df = result if not isinstance(result, tuple) else None
                self.summary = None
                self.analysis_df = None
                self.reset_state()
                return
                
            if self.result_df is None or self.summary is None:
                self.reset_state()
                return
            
            # 기본 정보 업데이트
            self.update_summary_info()
            
            # 출하 실패 테이블 업데이트
            self.update_failed_table()
            
            # 컬럼 너비 설정
            self.adjust_column_widths()
            
            # 실패 아이템 정보 전달
            self.detect_and_emit_failures()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.reset_state()  # 오류 발생 시 상태 초기화

    """데이터 해시값 계산 (변경 감지용)"""
    def _compute_data_hash(self, df):
        if df is None:
            return None
            
        try:
            # 데이터프레임 핵심 정보 기반 해시값 생성
            key_cols = ['Item', 'Line', 'Time', 'Qty']
            cols_to_use = [col for col in key_cols if col in df.columns]
            
            if not cols_to_use:
                # 핵심 컬럼이 없으면 행과 열 수로 간단히 해시
                return hash((df.shape[0], df.shape[1]))
                
            # 주요 컬럼의 값들을 문자열로 연결해 해시
            data_str = str(df[cols_to_use].values.tobytes())
            return hash(data_str)
        except Exception as e:
            print(f"데이터 해시값 계산 오류: {e}")
            return hash(str(df.shape))  # 폴백: 행렬 크기만 고려
            
    """요약 정보 업데이트"""
    def update_summary_info(self):
        if not self.summary:
            return
        
        # 전체 생산량과 성공량 가져오기
        total_produced_qty = int(self.summary.get('total_produced_qty', 0))  # 정수형으로 변환
        success_qty = int(self.summary.get('success_qty', 0))  # 정수형으로 변환
        
        # 수량 기준 성공률 계산 (전체 생산량 기준으로 변경)
        qty_rate = round((success_qty / total_produced_qty * 100) if total_produced_qty > 0 else 0, 1)
        
        # 모델 관련 데이터 - 아이템 갯수 반영
        # 원본 데이터에서 고유한 아이템 개수 계산
        total_unique_items = len(self.result_df['Item'].unique())
        
        # 성공한 아이템 수 계산
        success_model_names = set()
        failed_model_names = set()
        
        if 'models_df' in self.summary:
            # 모델 데이터프레임이 있는 경우
            for _, model in self.summary['models_df'].iterrows():
                item_name = model['Item']
                if isinstance(item_name, tuple):
                    item_name = item_name[0] if len(item_name) > 0 else ""
                    
                if model['IsShippable']:
                    success_model_names.add(item_name)
                else:
                    failed_model_names.add(item_name)
        
        # 성공한 모델 수 계산
        success_models = len(success_model_names)
        
        # 실패한 모델 수 계산 (전체 - 성공)
        failed_models = total_unique_items - success_models
        
        # 모델 성공률 계산
        model_rate = round((success_models / total_unique_items * 100) if total_unique_items > 0 else 0, 1)
        
        # 프로그레스바 업데이트
        self.qty_progress.setValue(int(qty_rate))
        self.qty_progress.setFormat(f"{qty_rate:.1f}%")  # 프로그레스바 텍스트 형식 설정
        
        self.model_progress.setValue(int(model_rate))
        self.model_progress.setFormat(f"{model_rate:.1f}%")  # 프로그레스바 텍스트 형식 설정
        
        # 상세 정보 업데이트 - 전체 생산량 기준으로 변경
        self.qty_detail.setText(f"{success_qty:,} / {total_produced_qty:,} ({qty_rate:.1f}%)")
        self.model_detail.setText(f"{success_models} / {total_unique_items} ({model_rate:.1f}%)")
        
        # 통계 테이블 업데이트 - 전체 생산량 표시 및 성공률 변경
        self.stats_table.setItem(0, 1, QTableWidgetItem(f"{total_produced_qty:,}"))
        self.stats_table.setItem(0, 2, QTableWidgetItem(f"{success_qty:,}"))
        self.stats_table.setItem(0, 3, QTableWidgetItem(f"{qty_rate:.1f}%"))
        
        # 모델 기준 통계 (고유 아이템 수 기준)
        self.stats_table.setItem(1, 1, QTableWidgetItem(f"{total_unique_items}"))
        self.stats_table.setItem(1, 2, QTableWidgetItem(f"{success_models}"))
        self.stats_table.setItem(1, 3, QTableWidgetItem(f"{model_rate:.1f}%"))
        
        # 색상 강조
        for row in range(2):
            success_rate = qty_rate if row == 0 else model_rate
            color = self.get_color_for_rate(success_rate)
            self.stats_table.item(row, 3).setBackground(QBrush(color))
            
            # 모든 셀에 폰트 적용
            for col in range(1, 4):
                item = self.stats_table.item(row, col)
                if item:
                    item.setFont(QFont(self.regular_font_family))
    
    """만족률에 따른 색상 반환"""
    def get_color_for_rate(self, rate):
        if rate >= 90:
            return QColor(200, 255, 200)  # 연한 녹색
        elif rate >= 70:
            return QColor(255, 255, 200)  # 연한 노란색
        else:
            return QColor(255, 200, 200)  # 연한 빨간색
    
    """컬럼 너비 조정"""
    def adjust_column_widths(self):
        # 전체 너비 얻기
        total_width = self.failed_table.viewport().width()
        
        # Item 컬럼에 최소 너비 설정
        min_item_width = 250  # 아이템 컬럼의 최소 너비 (픽셀)
        
        # 컬럼별 너비 비율 설정 - To_site 컬럼 제거 반영
        self.failed_table.setColumnWidth(0, max(int(total_width * 0.40), min_item_width))  # Item - 넓게 설정
        self.failed_table.setColumnWidth(1, int(total_width * 0.20))  # Qty
        self.failed_table.setColumnWidth(2, int(total_width * 0.20))  # SOP
        self.failed_table.setColumnWidth(3, int(total_width * 0.20))  # Qty/SOP
        
        # 헤더 텍스트 정렬 조정 - 컬럼명이 잘리지 않도록
        header = self.failed_table.horizontalHeader()
        for col in range(self.failed_table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        
        # 자동 크기 조정 후 다시 Interactive로 변경하여 사용자 조정 가능하게
        header.setSectionResizeMode(QHeaderView.Interactive)
    
    """출하 실패 모델 테이블 업데이트"""
    def update_failed_table(self):
        if self.analysis_df is None or self.result_df is None or self.summary is None:
            return
        
        # 정렬 데이터 초기화
        self.failed_models_data = []
        
        # SOP 불일치 정보 가져오기
        sop_inconsistencies = self.summary.get('sop_inconsistencies', [])
        inconsistent_items_dict = {}
        for inc in sop_inconsistencies:
            inconsistent_items_dict[inc['Item']] = {
                'values': inc['SOP_Values'],
                'selected': inc['Selected_SOP']
            }
        
        # 모델 단위로 고유한 실패 모델만 필터링
        # SOP 불일치 모델도 실패에 포함
        if 'models_df' in self.summary:
            # 새로운 방식: models_df가 있는 경우
            # 출하 실패 모델과 SOP 불일치 모델을 모두 표시
            failed_models = self.summary['models_df'][
                (~self.summary['models_df']['IsShippable']) | 
                (self.summary['models_df']['SOP_Inconsistent'] == True)
            ]
        else:
            # 기존과 호환성 유지: 분석 결과에서 모델 단위로 실패 항목 찾기
            model_keys = set()
            failed_models_list = []
            
            for _, row in self.analysis_df.iterrows():
                key = row['Item']
                # 출하 실패이거나 SOP 불일치인 경우
                if not row['IsShippable'] or row.get('SOP_Inconsistent', False):
                    if key not in model_keys:
                        model_keys.add(key)
                        failed_models_list.append(row)
            
            failed_models = pd.DataFrame(failed_models_list)
        
        # 테이블 초기화
        self.failed_table.setRowCount(0)
        
        if len(failed_models) == 0:
            self.failed_table.setRowCount(1)
            empty_message = QTableWidgetItem("No failed shipment models")
            empty_message.setTextAlignment(Qt.AlignCenter)
            empty_message.setFont(QFont(self.regular_font_family))
            self.failed_table.setItem(0, 0, empty_message)
            self.failed_table.setSpan(0, 0, 1, 4)  # 컬럼 수 변경 (4개 컬럼)
            return
        
        # 테이블에 데이터 추가
        self.failed_table.setRowCount(len(failed_models))
        
        for row_idx, (_, model) in enumerate(failed_models.iterrows()):
            # 데이터 준비 - Item이 튜플인 경우 문자열로 변환
            item_text = model['Item']
            if isinstance(item_text, tuple):
                item_text = str(item_text[0]) if len(item_text) > 0 else ""
            else:
                item_text = str(item_text)
            
            # SOP 값과 불일치 표시를 위한 준비
            is_inconsistent = model.get('SOP_Inconsistent', False)
            sop_tooltip = ""
            
            # 아이템이 불일치 목록에 있는지 확인
            if item_text in inconsistent_items_dict:
                is_inconsistent = True
                inc_info = inconsistent_items_dict[item_text]

            # 수량 정보
            due_lt_production = model.get('DueLTProduction', 0)
            qty_text = f"{due_lt_production:,}"
            sop = model.get('SOP', 0)
            sop_text = f"{sop:,}"
            
            # SOP 불일치가 있는 경우 표시 추가
            if is_inconsistent:
                sop_text += " (!)" # 불일치 표시 추가
            
            # Qty/SOP 비율
            if sop > 0:
                ratio = due_lt_production / sop * 100
                ratio_text = f"{ratio:.1f}%"
            else:
                ratio = 0
                ratio_text = "0.0%"
            
            # 색상 정보 저장
            background_info = {}
            
            # 수량 부족인 경우 강조
            if due_lt_production < sop:
                background_info['qty'] = True
            
            # SOP 불일치인 경우
            if is_inconsistent:
                background_info['sop_inconsistent'] = True
            
            # 비율에 따른 색상 설정
            if ratio < 80:
                background_info['ratio'] = 'red'  # 빨간색
            elif ratio < 100:
                background_info['ratio'] = 'orange'  # 주황색
                
            # 정렬을 위한 데이터 저장 - To_site 제거
            row_data = [item_text, qty_text, sop_text, ratio_text]
            row_data.append({'background': background_info})  # 색상 정보 함께 저장
            self.failed_models_data.append(row_data)
            
            # 셀 설정
            item_cell = QTableWidgetItem(item_text)
            item_cell.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            # 기본 폰트 적용
            item_cell.setFont(QFont(self.regular_font_family))
            
            # SOP 불일치 항목은 아이템명에도 표시
            if is_inconsistent:
                # 폰트 변경
                font = QFont(self.bold_font_family)
                item_cell.setFont(font)
                
                
            self.failed_table.setItem(row_idx, 0, item_cell)
            
            qty_cell = QTableWidgetItem(qty_text)
            qty_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            qty_cell.setFont(QFont(self.regular_font_family))
            
            if background_info.get('qty', False):
                qty_cell.setBackground(QBrush(QColor(255, 235, 235)))
                
            self.failed_table.setItem(row_idx, 1, qty_cell)
            
            sop_cell = QTableWidgetItem(sop_text)
            sop_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # 기본 폰트 설정
            sop_cell.setFont(QFont(self.regular_font_family))
            
            # 불일치가 있는 경우 배경색 변경 및 툴팁 추가
            if is_inconsistent:
                sop_cell.setBackground(QBrush(QColor(255, 255, 200)))  # 노란색 배경
                # 굵은 폰트 사용
                sop_cell.setFont(QFont(self.bold_font_family))
                
            self.failed_table.setItem(row_idx, 2, sop_cell)
            
            ratio_cell = QTableWidgetItem(ratio_text)
            ratio_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ratio_cell.setFont(QFont(self.regular_font_family))
            
            # 비율에 따른 색상 설정
            if background_info.get('ratio') == 'red':
                ratio_cell.setBackground(QBrush(QColor(255, 200, 200)))
            elif background_info.get('ratio') == 'orange':
                ratio_cell.setBackground(QBrush(QColor(255, 235, 200)))
                
            self.failed_table.setItem(row_idx, 3, ratio_cell)
        
        # 행 높이 조정
        for row in range(self.failed_table.rowCount()):
            self.failed_table.setRowHeight(row, 28)

    """실패 이유 반환"""
    def get_failure_reason(self, data):
        if not data.get('InDemand', True):
            return "Not in Demand"
        elif not data.get('TimeConditionMet', False) and not data.get('QtyConditionMet', False):
            return "Time>Due_LT & Qty<SOP"
        elif not data.get('TimeConditionMet', False):
            return "Time>Due_LT"
        elif not data.get('QtyConditionMet', False):
            return "Qty<SOP"
        return "Unknown reason"
    
    def detect_and_emit_failures(self):
        try:
            # 모든 검증 통과 후 실패 아이템 정보 수집
            failure_items = {}
            
            # 모델 단위 출하 정보 확인
            models_df = self.summary.get('models_df')
            if models_df is None or models_df.empty:
                self.failure_items = {}  # 빈 딕셔너리로 초기화
                self.shipment_status_updated.emit({})
                return
                
            # SOP 불일치 정보 검사
            sop_inconsistencies = self.summary.get('sop_inconsistencies', [])
            inconsistent_items = {inc['Item'] for inc in sop_inconsistencies} if sop_inconsistencies else set()
            
            # 출하 실패 또는 SOP 불일치 모델 필터링
            failed_models = models_df[
                (~models_df['IsShippable']) | 
                (models_df['SOP_Inconsistent'] == True)
            ]
            
            # 각 실패 모델에 대한 정보 수집
            for _, row in failed_models.iterrows():
                # Item 정보 처리 - 튜플인 경우 처리
                item_code = row['Item']
                if isinstance(item_code, tuple):
                    item_code = item_code[0] if len(item_code) > 0 else ""
                
                # SOP와 생산량 정보 가져오기
                sop = row.get('SOP', 0)
                production = row.get('DueLTProduction', 0)
                is_inconsistent = row.get('SOP_Inconsistent', False) or (item_code in inconsistent_items)
                
                # 출하 실패 이유 결정
                if is_inconsistent:
                    reason = "SOP Value Inconsistency"
                    for inc in sop_inconsistencies:
                        if inc['Item'] == item_code:
                            all_values = inc['SOP_Values']
                            selected = inc.get('Selected_SOP', inc.get('selected', 0))
                            reason = f"SOP Value Inconsistency (Found: {all_values} / Used: {selected})"
                            break
                elif production < sop:
                    reason = f"Insufficient Production (Produced: {production}, Required: {sop})"
                else:
                    reason = row.get('FailureReason', 'Unknown reason')
                    
                # 출하 실패 정보 구성
                failure_items[item_code] = {
                    'item': item_code,
                    'sop': sop,
                    'production': production,
                    'reason': reason,
                    'sop_inconsistent': is_inconsistent,  # SOP 불일치 플래그
                    'status_type': 'shipment'  # 상태 타입 추가
                }
            
            # 중요: 실패 아이템 정보 저장
            self.failure_items = failure_items
            
            # 시그널 발생
            print(f"출하 상태 업데이트: {len(failure_items)} 개의 실패 아이템")
            # self.shipment_status_updated.emit(failure_items)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            # 에러 발생시 빈 값 설정
            self.failure_items = {}
            self.shipment_status_updated.emit({})

    """위젯 상태 초기화"""   
    def reset_state(self):
        # 데이터 초기화
        self.result_df = None
        self.summary = None
        self.analysis_df = None
        self.failure_items = {}
        self.failed_models_data = []  # 정렬 데이터도 초기화
        
        # 프로그레스바 초기화
        self.qty_progress.setValue(0)
        self.qty_progress.setFormat("0.0%")  # 초기 텍스트 형식 설정
        
        self.model_progress.setValue(0)
        self.model_progress.setFormat("0.0%")  # 초기 텍스트 형식 설정
        
        self.qty_detail.setText("0 / 0 (0.0%)")  # 소수점 1자리 표시
        self.model_detail.setText("0 / 0 (0.0%)")  # 소수점 1자리 표시
        
        # 통계 테이블 초기화
        for row in range(2):
            for col in range(1, 4):
                self.stats_table.setItem(row, col, QTableWidgetItem("0"))
        
        # 실패 테이블 초기화
        self.failed_table.setRowCount(1)
        empty_message = QTableWidgetItem("No analysis data")
        empty_message.setTextAlignment(Qt.AlignCenter)
        empty_message.setFont(QFont(self.regular_font_family))
        self.failed_table.setItem(0, 0, empty_message)
        self.failed_table.setSpan(0, 0, 1, 4)  # 컬럼 수에 맞게 스팬 조정 (4개 컬럼)
        
        # 컬럼 너비 재설정
        self.adjust_column_widths()
        
        # 출하 실패 항목 초기화 시그널 발생
        self.shipment_status_updated.emit({})
    
    """위젯이 표시될 때 호출됨"""    
    def showEvent(self, event):
        super().showEvent(event)
        # 컬럼 너비 조정
        self.adjust_column_widths()
        
    """위젯 크기가 변경될 때 호출됨"""
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 테이블 컬럼 너비 재조정
        self.adjust_column_widths()