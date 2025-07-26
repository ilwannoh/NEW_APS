import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QFrame, QSizePolicy, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from typing import List

from ....resources.styles.pre_assigned_style import (
    LINE_LABEL_STYLE, DAY_LABEL_STYLE, NIGHT_LABEL_STYLE, SEPARATOR_STYLE
)
from .calendar_card import CalendarCard
from .detail_dialog import DetailDialog
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager

bold_font   = font_manager.get_just_font("SamsungSharSans-Bold").family()
normal_font = font_manager.get_just_font("SamsungOne-700").family()

"""
주간 캘린더 형태로 데이터 표시하는 위젯
"""
class WeeklyCalendar(QWidget):
    def __init__(self, data: pd.DataFrame, line_order: List[str]=None):
        super().__init__()
        self.data = data.rename(columns={
            "Line": "line",
            "Time": "time",
            "Qty": "qty",
            "Project": "project",
            "Details": "details",
        })
        self.time_map = {
            1: "Mon-Day", 2: "Mon-Night",
            3: "Tue-Day", 4: "Tue-Night",
            5: "Wed-Day", 6: "Wed-Night",
            7: "Thu-Day", 8: "Thu-Night",
            9: "Fri-Day",10: "Fri-Night",
           11: "Sat-Day",12: "Sat-Night",
           13: "Sun-Day",14: "Sun-Night"
        }
        self.line_order = line_order
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        total_cols = 9
        layout.setColumnMinimumWidth(0, 60)
        layout.setColumnMinimumWidth(1, 80)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 0)

        for c in range(2, total_cols):
            layout.setColumnMinimumWidth(c, 100)
            layout.setColumnStretch(c, 1)

        present = set(self.data['time'])

        if not any(t in present for t in (11, 12, 13, 14)):
            layout.setColumnStretch(7, 0)
            layout.setColumnMinimumWidth(7, 75)
            layout.setColumnStretch(8, 0)
            layout.setColumnMinimumWidth(8, 75)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        if self.line_order:
            lines = self.line_order
        else:
            lines = sorted(self.data['line'].unique())
            
        row_index = 0

        for line in lines:
            # 이 라인에 day / night 데이터가 있는지 확인
            day_times   = list(range(1, 15, 2))
            night_times = list(range(2, 15, 2))

            day_data   = self.data[(self.data['line']==line) & self.data['time'].isin(day_times)]
            night_data = self.data[(self.data['line']==line) & self.data['time'].isin(night_times)]

            if day_data.empty and night_data.empty:
                continue

            # Line 레이블
            span = (1 if not day_data.empty else 0) \
                + (1 if not night_data.empty else 0)
            line_label = QLabel(f"<b>{line}</b>")
            line_label.setAlignment(Qt.AlignCenter)
            line_label.setStyleSheet(
                LINE_LABEL_STYLE
                + f" font-family:{bold_font}; font-size:{f(14)}px; font-weight:900;"
            )
            line_label.setMaximumWidth(60)
            line_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            layout.addWidget(line_label, row_index, 0, span, 1)

            # Day 섹션
            if not day_data.empty:
                day_label = QLabel("Day")
                day_label.setAlignment(Qt.AlignCenter)
                day_label.setStyleSheet(
                    DAY_LABEL_STYLE
                    + f" font-family:{normal_font}; font-size:{f(14)}px;"
                )
                day_label.setMaximumWidth(80)
                layout.addWidget(day_label, row_index, 1)

                # Day 카드
                for t in day_times:
                    col = (t-1)//2 + 2
                    cell = QWidget(); cell_layout=QVBoxLayout(cell)
                    cell_layout.setContentsMargins(2,2,2,2); cell_layout.setSpacing(4)
                    subset = day_data[ day_data['time']==t ]

                    for _, r in subset.iterrows():
                        card = CalendarCard(r.to_dict(), is_day=True, parent=cell)
                        card.clicked.connect(self.show_detail_card)
                        cell_layout.addWidget(card)
                    cell_layout.addStretch()
                    layout.addWidget(cell, row_index, col)
                row_index += 1

            # Night 섹션
            if not night_data.empty:
                night_label = QLabel("Night")
                night_label.setAlignment(Qt.AlignCenter)
                night_label.setStyleSheet(
                    NIGHT_LABEL_STYLE
                    + f" font-family:{normal_font}; font-size:{f(14)}px;"
                )
                night_label.setMaximumWidth(80)
                layout.addWidget(night_label, row_index, 1)

                for t in night_times:
                    col = (t-1)//2 + 2
                    cell = QWidget(); cell_layout=QVBoxLayout(cell)
                    cell_layout.setContentsMargins(2,2,2,2); cell_layout.setSpacing(4)
                    subset = night_data[ night_data['time']==t ]

                    for _, r in subset.iterrows():
                        card = CalendarCard(r.to_dict(), is_day=False, parent=cell)
                        card.clicked.connect(self.show_detail_card)
                        cell_layout.addWidget(card)
                    cell_layout.addStretch()
                    layout.addWidget(cell, row_index, col)
                row_index += 1

            # 라인 종료 구분선
            end_sep = QFrame()
            end_sep.setFrameShape(QFrame.HLine)
            end_sep.setStyleSheet(SEPARATOR_STYLE)
            layout.addWidget(end_sep, row_index, 0, 1, layout.columnCount())
            row_index += 1
        
        self.setLayout(layout)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())

    """
    카드 클릭 시 상세 정보 표시 
    """
    def show_detail_card(self):
        card = self.sender()
        record = getattr(card, '_row', {})

        if not record:
            QMessageBox.information(self, "No Details", "상세정보를 찾을 수 없습니다.")
            return

        dlg = DetailDialog(record, self.time_map, parent=self)
        dlg.exec_()

        # 카드 상태 초기화
        card._is_selected = False
        card.setStyleSheet(card.base_style)