from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt5.QtCore import Qt

from ....resources.styles.pre_assigned_style import WEEKDAY_HEADER_STYLE
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager

bold_font   = font_manager.get_just_font("SamsungSharSans-Bold").family()
normal_font = font_manager.get_just_font("SamsungOne-700").family()

"""
pre-assigned page의 표 헤더
"""
class CalendarHeader(QWidget):
    def __init__(self, present_times:set, parent=None):
        super().__init__(parent)
        self.present = present_times

        layout = QGridLayout(self)

        layout.setColumnMinimumWidth(0, 60)
        layout.setColumnMinimumWidth(1, 80)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 0)

        for c in range(2, 9):
            layout.setColumnMinimumWidth(c, 100)
            layout.setColumnStretch(c, 1)

        present = set(self.present)

        if not any(t in present for t in (11, 12, 13, 14)):
            layout.setColumnStretch(7, 0)
            layout.setColumnMinimumWidth(7, 75)
            layout.setColumnStretch(8, 0)
            layout.setColumnMinimumWidth(8, 75)    

        layout.setSpacing(6)

        blank0 = QWidget(self)
        blank0.setFixedWidth(60)

        layout.addWidget(blank0, 0, 0, 1, 1)

        blank1 = QWidget(self)
        blank1.setFixedWidth(80)

        layout.addWidget(blank1, 0, 1, 1, 1)

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for col, day in enumerate(weekdays, start=2):
            header = QLabel(f"<b>{day}</b>")
            header.setAlignment(Qt.AlignCenter)
            header.setFixedHeight(40)
            header.setStyleSheet(
                WEEKDAY_HEADER_STYLE
                + f" font-family:{bold_font}; font-size:{f(14)}px; font-weight:900;"
            )
            layout.addWidget(header, 0, col)