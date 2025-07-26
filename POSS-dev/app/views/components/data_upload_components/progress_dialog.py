from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QProgressBar, QLabel,
    QPushButton, QFrame, QHBoxLayout, QMessageBox,
    QApplication, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QTime
from PyQt5.QtGui import QFont

from app.resources.fonts.font_manager import font_manager
from app.models.common.settings_store import SettingsStore
from app.models.common.screen_manager import *


# 최적화 작업을 수행할 작업자 스레드 클래스 추가
class OptimizationWorker(QThread):
    progress_updated = pyqtSignal(int)  # 진행 상황 업데이트 시그널
    status_updated = pyqtSignal(str)  # 상태 메시지 업데이트 시그널
    optimization_finished = pyqtSignal(dict)  # 최적화 완료 시그널 (결과 포함)
    error_occurred = pyqtSignal(str)  # 오류 발생 시그널

    def __init__(self, data_input_page, parent=None):
        super().__init__(parent)
        self.data_input_page = data_input_page
        self.is_cancelled = False
        self.optimization_engine = None

    def run(self):
        try:
            # UI 업데이트 처리를 위한 imports
            from PyQt5.QtWidgets import QApplication
            import time

            # 진행 상황 초기화 - 0%부터 시작
            self.progress_updated.emit(0)
            self.status_updated.emit("Initializing optimization...")
            QApplication.processEvents()
            time.sleep(0.1)  # UI가 업데이트될 시간을 줌

            # 더 세분화된 진행률로 시작
            for i in range(1, 5):
                self.progress_updated.emit(i * 2)
                QApplication.processEvents()
                time.sleep(0.05)

            # 데이터프레임 준비 (초기 10% 진행)
            self.status_updated.emit("Preparing the dataframe...")
            self.progress_updated.emit(10)
            QApplication.processEvents()

            self.data_input_page.prepare_dataframes_for_optimization()

            # 데이터프레임 준비 후 진행률 업데이트
            for i in range(6, 10):
                self.progress_updated.emit(i * 2)
                QApplication.processEvents()
                time.sleep(0.05)

            if self.is_cancelled:
                return

            # 최적화 엔진 초기화 (약 20% 진행)
            self.status_updated.emit("Initializing the optimization engine...")
            self.progress_updated.emit(20)
            QApplication.processEvents()

            from app.core.optimization import Optimization
            from app.models.common.file_store import DataStore

            # 엔진 초기화 중간 진행률 업데이트
            for i in range(11, 15):
                self.progress_updated.emit(i * 2)
                QApplication.processEvents()
                time.sleep(0.05)

            all_dataframes = DataStore.get("organized_dataframes", {})

            # 데이터프레임 로드 후 진행률 업데이트
            for i in range(15, 20):
                self.progress_updated.emit(i * 2)
                QApplication.processEvents()
                time.sleep(0.05)

            self.optimization_engine = Optimization(all_dataframes)

            if self.is_cancelled:
                return

            # 모델 정의 및 제약 조건 설정 (약 40% 진행)
            self.status_updated.emit("Building the optimization model...")
            self.progress_updated.emit(40)
            QApplication.processEvents()

            # 모델 설정 진행률 세분화
            for i in range(21, 30):
                self.progress_updated.emit(i * 2)
                QApplication.processEvents()
                time.sleep(0.05)

            if self.is_cancelled:
                return

            # 최적화 실행 (약 60% 진행)
            self.status_updated.emit("Running the optimization model...")
            self.progress_updated.emit(60)
            QApplication.processEvents()

            # 최적화 진행 중 단계적 업데이트
            for i in range(31, 35):
                self.progress_updated.emit(i * 2)
                QApplication.processEvents()
                time.sleep(0.05)

            # 최적화 실행
            result = self.optimization_engine.pre_assign()

            # 결과 처리 중 진행률 업데이트
            self.status_updated.emit("Processing optimization results...")
            for i in range(70, 95, 5):
                self.progress_updated.emit(i)
                QApplication.processEvents()
                time.sleep(0.05)

            if self.is_cancelled:
                return

            # 완료 및 결과 반환
            self.status_updated.emit("Optimization complete! Please wait a moment...")
            self.progress_updated.emit(100)
            QApplication.processEvents()
            time.sleep(0.2)  # 완료 상태 표시를 위한 약간의 지연

            self.optimization_finished.emit(result)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))

    def cancel(self):
        self.is_cancelled = True


class OptimizationProgressDialog(QDialog):
    """최적화 진행 상황을 표시하는 다이얼로그"""

    optimization_completed = pyqtSignal(dict)  # 결과를 포함하는 시그널로 변경
    optimization_cancelled = pyqtSignal()

    def __init__(self, data_input_page, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initializing optimization.")
        self.setModal(True)
        self.setFixedSize(w(1000), h(600))

        # 데이터 입력 페이지 저장
        self.data_input_page = data_input_page

        # 작업자 스레드 초기화
        self.worker = None

        # WindowStaysOnTopHint 제거하고 대신 다른 플래그 사용
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        # 다이얼로그가 부모 창 중앙에 위치하도록 설정
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

        self.init_ui()

        # 다이얼로그를 최상위로 유지
        self.raise_()
        self.activateWindow()

        # 초기 진행 표시줄 값을 명시적으로 0으로 설정
        self.progress_bar.setValue(0)
        self.progress_bar.repaint()

    def init_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 제목 프레임
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1428A0;
                border: none;
                padding: 0px;
                min-height: {h(50)}px;
            }}
        """)


        # 제목 프레임의 레이아웃을 먼저 생성하고 설정
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(w(20), 0, w(20), 0)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

        # 제목 레이블
        title_label = QLabel("First Optimization")
        title_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: white; font-family: {title_font}; font-weight: bold; font-size: {f(18)}px;")

        # 레이아웃에 레이블 추가
        title_layout.addWidget(title_label)

        main_layout.addWidget(title_frame)

        # 컨텐츠 영역
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #F5F5F5;
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                border: none;
                height: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: #CCCCCC;
                min-width: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(w(30), h(40), w(30), h(30))
        content_layout.setSpacing(w(20))

        # 진행 상태 레이블
        self.status_label = QLabel("Optimization has started...")
        status_font = font_manager.get_font("SamsungOne-700", f(12))
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: #333333;
                padding: {w(10)}px;
            }}
        """)
        content_layout.addWidget(self.status_label)

        # 프로그래스바
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #E0E0E0;
                border-radius: {w(8)}px;
                background-color: white;
                text-align: center;
                height: {h(40)}px;
                font-size: {f(11)}px;
                font-weight: bold;
                color: #333333;
            }}
            QProgressBar::chunk {{
                background-color: #1428A0;
                border-radius: {w(6)}px;
                margin: {w(2)}px;
            }}
        """)
        content_layout.addWidget(self.progress_bar)

        # 시간 정보 레이블
        self.time_label = QLabel("Processing...")
        time_font = font_manager.get_font("SamsungOne-700", f(10))
        self.time_label.setFont(time_font)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet(f"""
            QLabel {{
                color: #666666;
                padding: {w(5)}px;
            }}
        """)
        content_layout.addWidget(self.time_label)

        # 로그 텍스트 영역 추가
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(h(150))
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: {w(4)}px;
                padding: {w(5)}px;
                font-size: {f(9)}px;
            }}
        """)
        content_layout.addWidget(self.log_text)

        content_layout.addStretch()

        main_layout.addWidget(content_frame)

        # 버튼 영역
        button_frame = QFrame()
        button_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #F0F0F0;
                border: none;
                border-top: 1px solid #E0E0E0;
                padding: {w(15)}px;
            }}
        """)
        button_frame.setFixedHeight(h(70))

        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(w(20), 0, w(20), 0)
        button_layout.addStretch()

        # 취소 버튼
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_font = font_manager.get_font("SamsungOne-700", f(10))
        cancel_font.setBold(True)
        self.cancel_button.setFont(cancel_font)
        self.cancel_button.setFixedSize(w(100), h(36))
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #E0E0E0;
                color: #333333;
                border: none;
                border-radius: {w(5)}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #D0D0D0;
            }}
            QPushButton:pressed {{
                background-color: #C0C0C0;
            }}
        """)
        self.cancel_button.clicked.connect(self.cancel_optimization)
        button_layout.addWidget(self.cancel_button)

        main_layout.addWidget(button_frame)

    def start_optimization(self):
        """최적화 프로세스 시작"""
        # 진행 표시줄 초기화 및 UI 업데이트
        self.progress_bar.setValue(0)
        self.status_label.setText("Optimization has started...")
        self.time_label.setText("Preparing...")
        self.log_message("Starting the optimization process.")

        # UI 업데이트 강제 실행
        QApplication.processEvents()

        # 작업자 스레드 생성
        self.worker = OptimizationWorker(self.data_input_page)

        # 시그널 연결
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.status_updated.connect(self.update_status)
        self.worker.optimization_finished.connect(self.on_optimization_finished)
        self.worker.error_occurred.connect(self.on_error_occurred)

        # UI가 업데이트될 시간을 주기 위해 약간의 지연 후 작업 시작
        QTimer.singleShot(200, self.worker.start)
        self.log_message("Starting the optimization process.")

    def update_progress(self, value):
        """프로그래스바 업데이트"""
        self.progress_bar.setValue(value)
        self.progress_bar.repaint()  # 즉시 재그리기

        # 50% 이상일 때 텍스트 색상을 하얀색으로 변경
        if value >= 50:
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid #E0E0E0;
                    border-radius: {w(8)}px;
                    background-color: white;
                    text-align: center;
                    height: {h(40)}px;
                    font-size: {f(11)}px;
                    font-weight: bold;
                    color: white; 
                }}
                QProgressBar::chunk {{
                    background-color: #1428A0;
                    border-radius: {w(6)}px;
                    margin: {w(2)}px;
                }}
            """)

        # 상태 메시지 업데이트
        if value < 20:
            self.time_label.setText("Preparing data...")
        elif value < 40:
            self.time_label.setText("Defining constraints...")
        elif value < 60:
            self.time_label.setText("Configuring model...")
        elif value < 80:
            self.time_label.setText("Optimizing...")
        elif value < 95:
            self.time_label.setText("Almost done...")
        else:
            self.time_label.setText("Completed. Displaying results...")

            if value == 100:
                self.cancel_button.setText("Cancel")

        # 로그에 진행률 기록
        if value % 10 == 0:  # 10% 단위로만 로그 기록
            self.log_message(f"Progress: {value}%")

        # UI 업데이트 강제 실행
        QApplication.processEvents()

    def update_status(self, message):
        """상태 메시지 업데이트"""
        self.status_label.setText(message)
        self.status_label.repaint()  # 즉시 재그리기
        self.log_message(message)

        # UI 업데이트 강제 실행
        QApplication.processEvents()

    def log_message(self, message):
        """로그에 메시지 추가"""
        current_time = QTime.currentTime().toString("hh:mm:ss.zzz")
        self.log_text.append(f"[{current_time}] {message}")
        # 스크롤을 항상 최신 내용으로
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

        # UI 업데이트 강제 실행
        QApplication.processEvents()

    def on_optimization_finished(self, result):
        """최적화 완료 처리"""
        self.update_progress(100)
        self.status_label.setText("Optimization is complete.")
        self.time_label.setText("Complete! Please wait a moment.")
        self.cancel_button.setText("Cancel")
        self.log_message("Optimization is complete. Please wait a moment.")

        # UI 업데이트 강제 실행
        QApplication.processEvents()

        # 결과를 포함하여 완료 시그널 발생
        self.optimization_completed.emit(result)

        # 다이얼로그를 자동으로 닫기 (약간의 지연 후)
        QTimer.singleShot(800, self.accept)  # 0.8초 후 다이얼로그 닫기

    def on_error_occurred(self, error_message):
        """오류 발생 처리"""
        self.status_label.setText(f"Error: {error_message}")
        self.time_label.setText("Fail")
        self.cancel_button.setText("Cancel")
        self.log_message(f"An error has occurred.: {error_message}")

        # UI 업데이트 강제 실행
        QApplication.processEvents()

        # 오류 발생 알림
        QMessageBox.warning(
            self,
            "Optimization error.",
            f"An error occurred during the optimization process.: {error_message}"
        )

        self.optimization_cancelled.emit()

    def cancel_optimization(self):
        """최적화 취소"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()  # 스레드가 종료될 때까지 기다림

            # 취소 메시지 표시
            self.status_label.setText("The optimization has been canceled.")
            self.cancel_button.setText("Cancel")
            self.log_message("The optimization was canceled by the user.")

            # UI 업데이트 강제 실행
            QApplication.processEvents()

            # 취소 시그널 발생
            self.optimization_cancelled.emit()
            self.reject()
        else:
            self.accept()

    def closeEvent(self, event):
        """다이얼로그 닫기 이벤트 처리"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()  # 스레드가 종료될 때까지 기다림
            self.optimization_cancelled.emit()
        event.accept()

    def keyPressEvent(self, event):
        """키 이벤트 처리 - ESC 키 처리"""
        if event.key() == Qt.Key_Escape:
            if self.worker and self.worker.isRunning():
                self.cancel_optimization()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)