from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFrame, QLabel,
                             QHBoxLayout, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *


"""
KPI 점수를 표 형태로 표시하는 위젯
"""
class KpiWidget(QWidget):

    # 점수가 업데이트되었을 때 발생하는 시그널
    score_updated = pyqtSignal(dict, dict)  # (base_scores, adjust_scores)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.base_scores = {}
        self.adjust_scores = {}
        self.kpi_labels = {}  # 점수 라벨 저장
        self.init_ui()

    """
    UI 초기화
    """
    def init_ui(self):
        # 폰트 설정
        bold_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        normal_font = font_manager.get_just_font("SamsungOne-700").family()

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # KPI 테이블 컨테이너
        summary_container = QFrame()
        summary_container.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: none;
                border-radius: 0px;
            }
        """)
        summary_layout = QVBoxLayout(summary_container)
        summary_layout.setContentsMargins(w(8), h(8), w(8), h(8))
        summary_layout.setSpacing(0)

        # 표 생성
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 0px;
            }
        """)

        # 테이블 레이아웃
        table_layout = QGridLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(1)  # 셀 간격 최소화

        # 헤더 스타일
        header_style = f"""
            background-color: #F0F0F0;
            padding: 5px;
            font-family: {bold_font};
            font-weight: bold;
            color: #333333;
            border: 1px solid #E0E0E0;
            font-size: {f(11)}px;
        """

        # 내용 셀 기본 스타일 - 모든 행 동일한 배경색
        cell_style = f"""
            background-color: white;
            padding: 5px;
            border: 1px solid #E0E0E0;
            font-family: {bold_font};
            font-size: {f(11)}px;
            text-align: center;
        """

        # 행 라벨 스타일
        row_label_style = f"""
            background-color: #F0F0F0;
            padding: 5px;
            font-family: {bold_font};
            font-weight: bold;
            color: #333333;
            border: 1px solid #E0E0E0;
            font-size: {f(11)}px;
        """

        # 헤더 추가 (열 헤더)
        headers = ["", "Total", "Material", "SOP", "Util."]
        for col, header_text in enumerate(headers):
            header = QLabel(header_text)
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet(header_style)
            header.setMinimumWidth(w(40))
            header.setMinimumHeight(h(25))
            table_layout.addWidget(header, 0, col)

        # 행 추가
        row_names = ["Base", "Adjust"]
        for row, row_name in enumerate(row_names):
            # 행 라벨
            row_label = QLabel(row_name)
            row_label.setAlignment(Qt.AlignCenter)
            row_label.setStyleSheet(row_label_style)
            row_label.setMinimumWidth(w(40))
            table_layout.addWidget(row_label, row + 1, 0)

            # 각 점수 셀 추가
            for col, col_name in enumerate(["Total", "Mat", "SOP", "Util"]):
                cell = QLabel("--")
                cell.setAlignment(Qt.AlignCenter)
                cell.setStyleSheet(cell_style)

                table_layout.addWidget(cell, row + 1, col + 1)

                # 라벨 참조 저장
                key = f"{row_name}_{col_name}"
                self.kpi_labels[key] = cell

        # 열 너비 설정
        table_layout.setColumnStretch(0, 1)  # 첫 번째 열 (행 라벨)
        for i in range(1, 5):
            table_layout.setColumnStretch(i, 1)  # 점수 열들

        summary_layout.addWidget(table_frame)
        main_layout.addWidget(summary_container, 1)  # 나머지 공간 차지

        # 전체 위젯 스타일
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)

        # 최소 사이즈 설정
        self.setMinimumHeight(h(120))

    """
    점수 업데이트
    """
    def update_scores(self, base_scores=None, adjust_scores=None):
        try:
            # 기본 점수
            if base_scores:
                self.base_scores = base_scores
                self.update_base_scores()

            # 조정 점수
            if adjust_scores is not None:
                self.adjust_scores = adjust_scores
                if adjust_scores:
                    self.update_adjust_scores()
                else:  # 빈 딕셔너리면 점수 초기화
                    self.reset_adjust_scores()

            # 점수 업데이트 시그널 발생
            self.score_updated.emit(self.base_scores, self.adjust_scores)
        except Exception as e:
            import traceback
            print(f"KPI 점수 업데이트 오류: {e}")
            traceback.print_exc()

    """
    기본 점수 라벨 업데이트
    """
    def update_base_scores(self):
        for score_type, score in self.base_scores.items():
            label_key = f"Base_{score_type}"
            if label_key in self.kpi_labels:
                # 소수점 한자리까지 표시
                score_text = f"{score:.1f}" if isinstance(score, (int, float)) else str(score)
                self.kpi_labels[label_key].setText(score_text)

                # 점수에 따른 색상 결정
                color = self._get_score_color(score)

                # 기존 스타일에 색상 적용
                self.kpi_labels[label_key].setStyleSheet(f"""
                    background-color: white;
                    padding: 5px;
                    border: 1px solid #E0E0E0;
                    font-family: {font_manager.get_just_font("SamsungSharpSans-Bold").family()};
                    font-size: {f(11)}px;
                    text-align: center;
                    color: {color};
                """)

    """
    조정 점수 라벨 업데이트
    """
    def update_adjust_scores(self):
        for score_type, adjust_score in self.adjust_scores.items():
            label_key = f"Adjust_{score_type}"
            if label_key in self.kpi_labels:
                # 기본 점수 참조
                base_score = self.base_scores.get(score_type, 0)

                # 점수 차이에 따라 스타일 변경
                if adjust_score > base_score:
                    color = "#1428A0"  # 삼성 파란색 (향상)
                    arrow = "↑"
                elif adjust_score < base_score:
                    color = "#FF5733"  # 빨간색 (하락)
                    arrow = "↓"
                else:
                    color = "#555555"  # 회색 (변화 없음)
                    arrow = "-"

                # 소수점 한자리까지 표시
                score_text = f"{adjust_score:.1f} {arrow}" if isinstance(adjust_score,
                                                                         (int, float)) else f"{adjust_score} {arrow}"
                self.kpi_labels[label_key].setText(score_text)

                # 기존 스타일에 색상 적용
                self.kpi_labels[label_key].setStyleSheet(f"""
                    background-color: white;
                    padding: 5px;
                    border: 1px solid #E0E0E0;
                    font-family: {font_manager.get_just_font("SamsungSharpSans-Bold").family()};
                    font-size: {f(11)}px;
                    text-align: center;
                    color: {color};
                """)

    """
    조정 점수 리셋
    """
    def reset_adjust_scores(self):
        for score_type in ['Total', 'Mat', 'SOP', 'Util']:
            label_key = f"Adjust_{score_type}"
            if label_key in self.kpi_labels:
                self.kpi_labels[label_key].setText("--")

                # 기존 스타일에 색상 적용
                self.kpi_labels[label_key].setStyleSheet(f"""
                    background-color: white;
                    padding: 5px;
                    border: 1px solid #E0E0E0;
                    font-family: {font_manager.get_just_font("SamsungSharpSans-Bold").family()};
                    font-size: {f(11)}px;
                    text-align: center;
                    color: #555555;
                """)

    """
    점수에 따른 색상 반환
    """
    def _get_score_color(self, score):
        if score >= 90:
            return "#28a745"  # 초록색 (좋음)
        elif score >= 70:
            return "#ffc107"  # 노란색 (보통)
        else:
            return "#dc3545"  # 빨간색 (나쁨)