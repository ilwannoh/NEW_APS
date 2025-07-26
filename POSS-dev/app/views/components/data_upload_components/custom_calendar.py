from PyQt5.QtWidgets import QCalendarWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QLocale


"""
커스텀 캘린더 위젯
"""
class CustomCalendarWidget(QCalendarWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        try:
            english_locale = QLocale(QLocale.English, QLocale.UnitedStates)
            self.setLocale(english_locale)

            # 기본 설정
            self.setGridVisible(True)
            self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
            self.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)

            # 폰트 설정
            font = QFont("Arial", 9)
            self.setFont(font)

            self.clicked.connect(self.on_date_clicked)

            self.setStyleSheet("""
                /* 전체 캘린더 배경 */
                QCalendarWidget {
                    background-color: #f0f0f0;
                    border: 1px solid #c0c0c0;
                    border-radius: 10px;
                }

                /* 날짜 그리드 */
                QCalendarWidget QTableView {
                    alternate-background-color: #F1F1F1;
                    background-color: white;
                    selection-background-color: #1428A0;
                    selection-color: white;
                }

                /* 헤더 (요일 표시 부분) */
                QCalendarWidget QTableView QHeaderView {
                    background-color: #1428A0;
                    color: white;
                }

                /* 네비게이션 바 (월/년 선택 부분) */
                QCalendarWidget QWidget#qt_calendar_navigationbar {
                    background-color: #1428A0;
                    color: white;
                    border : none;
                }

                /* 네비게이션 바 버튼 */
                QCalendarWidget QToolButton {
                    background-color: #1428A0;
                    color: white;
                    border-radius: 3px;
                    padding: 5px;
                    border:none;
                }

                /* 버튼 호버 효과 */
                QCalendarWidget QToolButton:hover {
                    background-color: #5c7fc1;
                }

                /* 월 표시 */
                QCalendarWidget QSpinBox {
                    background-color: white;
                    color: black;
                    selection-background-color: #4b6eaf;
                    selection-color: white;
                    border : none;
                }
            """)
        except Exception as e:
            print(f"캘린더 초기화 오류: {e}")

    """
    날짜를 클릭했을 때 호출되는 메서드 (필요 시 구현)
    """
    def on_date_clicked(self, date):
        try:
            pass
        except Exception as e:
            print(f"날짜 클릭 처리 오류: {e}")