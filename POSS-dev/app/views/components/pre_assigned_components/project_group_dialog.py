import pandas as pd

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QCursor, QPalette, QColor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QSizePolicy,
    QLabel, QFrame, QScrollArea, QWidget, QPushButton, QProgressBar,
    QStackedLayout, QApplication
)
from .processThread import ProcessThread
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager


class ProjectGroupDialog(QDialog):
    # 최적화 완료 시 결과를 전달하기 위한 시그널
    optimizationDone = pyqtSignal(pd.DataFrame, pd.DataFrame)

    def __init__(self, project_groups: dict, df, on_done_callback=None, parent=None):
        super().__init__(parent)
        # 전달받은 데이터프레임과 그룹 정보를 멤버 변수로 저장
        self.df = df
        self.project_groups = project_groups
        self.df_to_opt = None

        # 콜백 함수가 있으면 완료 시 호출되도록 연결
        if on_done_callback:
            self.optimizationDone.connect(on_done_callback)

        self.setStyleSheet("background: transparent;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Select Project Groups")
        self.setModal(True)

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        bold_font = font_manager.get_just_font("SamsungSharSans-Bold").family()
        normal_font = font_manager.get_just_font("SamsungOne-700").family()

        # 제목 영역
        title_frame = QFrame()
        title_frame.setFixedHeight(h(55))
        title_frame.setStyleSheet("background-color: #1428A0; border: none;")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 0, 20, 0)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label = QLabel("Select Project Groups")
        title_label.setStyleSheet(
            f"font-family:{bold_font}; font-size:{f(16)}px; font-weight:900; color:white;"
        )
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_frame)

        # 설명 + 프로그레스바 영역
        desc_frame = QFrame()
        desc_frame.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
            }
        """)
        desc_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        desc_frame.setMinimumHeight(80)

        self.desc_stack = QStackedLayout(desc_frame)

        # 설명
        page_desc = QWidget()
        pd_layout = QVBoxLayout(page_desc)
        pd_layout.setContentsMargins(20, 15, 20, 15)
        self.desc_label = QLabel(
            "Select the project group to include in the optimization process"
        )
        self.desc_label.setFixedHeight(40)
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet(
            f"font-family:{bold_font}; font-size:{f(14)}px; font-weight:900; "
            "color:#333333; padding:10px;"
        )
        pd_layout.addWidget(self.desc_label)
        self.desc_stack.addWidget(page_desc)

        # 프로그레스바
        page_prog = QWidget()
        pp_layout = QVBoxLayout(page_prog)
        pp_layout.setContentsMargins(20, 15, 20, 15)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                font-family:{normal_font};
                font-size:{f(14)}px;
                font-weight:900;
                border:2px solid #E0E0E0;
                border-radius:8px;
                background-color:white;
                text-align:center;
                height:40px;
                color:#333333;
            }}
           QProgressBar::chunk {{
               background-color: #1428A0;
               border-radius: 6px;
               margin: 2px;
           }}
        """)
        pp_layout.addWidget(self.progress_bar)
        pp_layout.setStretch(pp_layout.indexOf(self.progress_bar), 1)
        self.desc_stack.addWidget(page_prog)

        self.desc_stack.setCurrentIndex(0)
        main_layout.addWidget(desc_frame)

        # 남은 시간
        self.time_label = QLabel("remaining time: 0:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet(
            f"font-family:{normal_font}; font-size:{f(14)}px; "
            "color:#666666; background-color:#F5F5F5;"
        )
        self.time_label.hide()
        main_layout.addWidget(self.time_label)

        # 체크박스 영역(스크롤)
        checkbox_frame = QFrame()
        checkbox_layout = QVBoxLayout(checkbox_frame)
        checkbox_layout.setContentsMargins(20, 15, 20, 15)
        checkbox_layout.setSpacing(10)

        self.checkboxes = {}
        for gid, projects in project_groups.items():
            cb = QCheckBox(", ".join(projects))
            cb.setStyleSheet(f"""
                QCheckBox {{
                    font-family:{normal_font};
                    font-size:{f(14)}px;
                    color:#333333;
                    padding:8px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                }}
                QCheckBox:hover {{
                    background-color: #f0f0f0;
                    border-radius: 4px;
                }}
            """)
            cb.stateChanged.connect(self._update_ok_button)
            checkbox_layout.addWidget(cb)
            self.checkboxes[gid] = cb

        checkbox_layout.addStretch(1)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(checkbox_frame)

        main_scroll_area = QScrollArea()
        main_scroll_area.setWidgetResizable(True)
        main_scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #F5F5F5;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background-color: #F5F5F5;
            }
        """)
        main_scroll_area.setWidget(content_widget)
        main_layout.addWidget(main_scroll_area)

        # 하단 버튼
        button_frame = QFrame()
        button_frame.setFixedHeight(80)
        button_frame.setStyleSheet("background-color: #F0F0F0; border: none;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 20, 30, 20)
        button_layout.addStretch(1)

        # ok 버튼
        self.ok_button = QPushButton("OK")
        self.ok_button.setFixedSize(100, 40)
        self.ok_button.setStyleSheet(f"""
            QPushButton {{
                font-family:{bold_font};
                font-size:{f(14)}px;
                font-weight:900;
                background-color:#1428A0;
                color:white;
                border-radius:8px;
            }}
            QPushButton:hover {{
                background-color:#1e429f;
            }}
            QPushButton:disabled {{
                background-color:#ACACAC;
            }}
        """)
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.ok_button.setEnabled(False)
        button_layout.addWidget(self.ok_button)
        button_layout.addSpacing(15)

        # Cancel 버튼
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedSize(100, 40)
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                font-family:{bold_font};
                font-size:{f(14)}px;
                font-weight:900;
                background-color:#6C757D;
                color:white;
                border-radius:8px;
            }}
            QPushButton:hover {{
                background-color:#545B62;
            }}
        """)
        self.cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addWidget(button_frame)

        self.setFixedWidth(w(700))
        self.adjustSize()

    """
    체크박스 상태에 따라 OK 버튼 활성/비활성 토글
    """
    def _update_ok_button(self):
        any_checked = any(cb.isChecked() for cb in self.checkboxes.values())
        self.ok_button.setEnabled(any_checked)
        self.ok_button.setCursor(Qt.PointingHandCursor if any_checked else Qt.ArrowCursor)

    """
    선택된 그룹 ID 리스트 반환
    """
    def selected_groups(self):
        return [gid for gid, cb in self.checkboxes.items() if cb.isChecked()]

    """
    프로그레스바 페이지 전환, 스레드 시작
    """
    def _on_ok_clicked(self):
        self.desc_stack.setCurrentIndex(1)
        self.ok_button.setEnabled(False)
        for cb in self.checkboxes.values():
            cb.setEnabled(False)

        gids = self.selected_groups()
        projects = sum((self.project_groups[gid] for gid in gids), [])
        self.df_to_opt = self.df[self.df['Project'].isin(projects)].copy()

        self.thread = ProcessThread(self.df_to_opt, projects)
        self.thread.progress.connect(self._on_progress)
        self.thread.finished.connect(self._on_finished)
        self.thread.start()

    """
    스레드 진행률 업데이트
    """
    @pyqtSlot(int, int)
    def _on_progress(self, pct: int, remaining: int):
        self.progress_bar.setValue(pct)

        m, s = divmod(remaining, 60)
        self.time_label.setText(f"remaining time: {m}:{s:02d}")
        if not self.time_label.isVisible():
            self.time_label.show()
            self.adjustSize()

        pal = self.progress_bar.palette()
        text_color = QColor("white") if pct >= 50 else QColor("#333333")
        pal.setColor(QPalette.Text, text_color)
        pal.setColor(QPalette.HighlightedText, text_color)
        self.progress_bar.setPalette(pal)

    """
    최적화 완료
    """
    @pyqtSlot(pd.DataFrame)
    def _on_finished(self, result_df: pd.DataFrame):
        self._on_progress(100, 0)
        QApplication.processEvents()
        self.optimizationDone.emit(result_df, self.df_to_opt)
        self.accept()