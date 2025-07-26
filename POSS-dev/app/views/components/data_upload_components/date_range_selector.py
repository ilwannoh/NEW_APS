from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QDateEdit, QFileDialog, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from .custom_calendar import CustomCalendarWidget
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager

class DateRangeSelector(QWidget):
    """날짜 범위 선택 컴포넌트"""
    date_range_changed = pyqtSignal(QDate, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        main_container = QFrame()
        main_container.setStyleSheet("background-color: white;  border-radius: 5px; border:none")

        main_container_layout = QHBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)

        # 시작 날짜
        start_date_label = QLabel("Start Date:")
        data_font = font_manager.get_just_font("SamsungOne-700").family()
        start_date_label.setStyleSheet(f"font-family:{data_font};")

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setStyleSheet(f"font-family:{data_font}; border: 2px solid #cccccc; border-radius: 5px;")

        # 커스텀 캘린더 위젯 적용 - 오류 방지를 위해 try-except 블록으로 감싸기
        try:
            start_calendar = CustomCalendarWidget()
            self.start_date_edit.setCalendarWidget(start_calendar)
        except Exception as e:
            print(f"Start calendar widget error: {e}")

        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setFixedWidth(w(180))
        self.start_date_edit.dateChanged.connect(self.on_date_changed)

        # 종료 날짜
        end_date_label = QLabel("End Date:")
        end_date_label.setStyleSheet(f"font-family:{data_font};")


        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addDays(7))
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setStyleSheet(f"font-family:{data_font}; border: 2px solid #cccccc; border-radius: 5px;")

        # 커스텀 캘린더 위젯 적용 - 오류 방지를 위해 try-except 블록으로 감싸기
        try:
            end_calendar = CustomCalendarWidget()
            self.end_date_edit.setCalendarWidget(end_calendar)
        except Exception as e:
            print(f"End calendar widget error: {e}")

        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setFixedWidth(w(180))
        self.end_date_edit.dateChanged.connect(self.on_date_changed)

        # 위젯 추가
        main_container_layout.addWidget(start_date_label)
        main_container_layout.addWidget(self.start_date_edit)
        main_container_layout.addSpacing(w(20))
        main_container_layout.addWidget(end_date_label)
        main_container_layout.addWidget(self.end_date_edit)
        main_container_layout.addStretch(1)  # 오른쪽 공간 채우기

        # 메인 레이아웃에 컨테이너 추가
        layout.addWidget(main_container)

    def on_date_changed(self):
        """날짜가 변경되면 시그널 발생"""
        try:
            start_date = self.start_date_edit.date()
            end_date = self.end_date_edit.date()

            # 유효성 검사 추가
            if start_date.isValid() and end_date.isValid():
                # 시작일이 종료일보다 늦으면 조정
                if start_date > end_date:
                    self.end_date_edit.setDate(start_date)
                    end_date = start_date

                print(f"날짜 범위 변경: {start_date.toString('yyyy-MM-dd')} ~ {end_date.toString('yyyy-MM-dd')}")
                self.date_range_changed.emit(start_date, end_date)
        except Exception as e:
            print(f"날짜 변경 처리 오류: {e}")

    def get_date_range(self):
        """현재 선택된 날짜 범위 반환"""
        try:
            return self.start_date_edit.date(), self.end_date_edit.date()
        except Exception as e:
            print(f"날짜 범위 조회 오류: {e}")
            return QDate.currentDate(), QDate.currentDate().addDays(6)