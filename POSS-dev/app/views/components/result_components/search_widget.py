from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                            QPushButton, QLabel, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

class SearchWidget(QWidget):
    # 시그널 정의
    searchRequested = pyqtSignal(str)  # 검색어
    searchCleared = pyqtSignal()  # 검색 초기화
    nextResultRequested = pyqtSignal()  # 다음 결과로 이동
    prevResultRequested = pyqtSignal()  # 이전 결과로 이동
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 검색 상태 변수들
        self.search_active = False
        self.last_search_text = ''
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # 검색 영역 레이아웃
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        
        normal_font = font_manager.get_just_font("SamsungOne-700").family()
        
        # 검색 필드
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText('searching...')
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid #808080;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #1428A0;
                font-size: {f(16)}px;
                padding: 6px 8px;
                font-family:{normal_font};
                min-height: {h(30)}px;
            }}
            QLineEdit:focus {{
                border: 1px solid #1428A0;
            }}
        """)
        self.search_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_field.returnPressed.connect(self.on_search)
        search_layout.addWidget(self.search_field)
        
        # 검색 버튼
        self.search_button = QPushButton('Search')
        self.search_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1428A0;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: {w(80)}px;
                border:none;
                font-family:{normal_font};
                font-size: {f(16)}px;
                min-height: {h(28)}px;
            }}
            QPushButton:hover {{
                background-color: #004C99;
            }}
            QPushButton:pressed {{
                background-color: #003366;
            }}
        """)
        self.search_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.search_button.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_button)
        
        # 검색 초기화 버튼
        self.clear_button = QPushButton('Clear')
        self.clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #808080;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: {w(80)}px;
                border:none;
                font-family:{normal_font};
                font-size: {f(16)}px;
                min-height: {h(28)}px;
            }}
            QPushButton:hover {{
                background-color: #606060;
            }}
            QPushButton:pressed {{
                background-color: #404040;
            }}
        """)
        self.clear_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_button.clicked.connect(self.on_clear)
        self.clear_button.setEnabled(False)
        search_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(search_layout)
        
        # 결과 상태 및 네비게이션 레이아웃
        result_layout = QHBoxLayout()
        result_layout.setContentsMargins(10, 0, 10, 0)
        
        # 결과 레이블
        self.result_label = QLabel('')
        self.result_label.setStyleSheet("""
            QLabel {
                color: #1428A0;
                font-weight: bold;
                font-size: 13px;
                border: None;
                padding: 0 5px;
            }
        """)
        
        # 이전 결과 버튼
        self.prev_button = QPushButton('◀')
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #1428A0;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 4px;
                min-width: 30px;
                max-width: 30px;
                border: 1px solid #d0d0d0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:disabled {
                color: #a0a0a0;
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
            }
        """)
        self.prev_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.prev_button.clicked.connect(self.on_prev)
        self.prev_button.setEnabled(False)
        
        # 다음 결과 버튼
        self.next_button = QPushButton('▶')
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #1428A0;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 4px;
                min-width: 30px;
                max-width: 30px;
                border: 1px solid #d0d0d0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:disabled {
                color: #a0a0a0;
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
            }
        """)
        self.next_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.next_button.clicked.connect(self.on_next)
        self.next_button.setEnabled(False)
        
        result_layout.addStretch(1)
        result_layout.addWidget(self.result_label)
        result_layout.addWidget(self.prev_button)
        result_layout.addWidget(self.next_button)
        
        # 처음에는 결과 네비게이션 숨김
        self.result_label.hide()
        self.prev_button.hide()
        self.next_button.hide()
        
        main_layout.addLayout(result_layout)
    
    def on_search(self):
        search_text = self.search_field.text().strip()
        if not search_text:
            self.on_clear()
            return
            
        self.search_active = True
        self.last_search_text = search_text
        self.clear_button.setEnabled(True)
        
        # 검색 요청 시그널 발생
        self.searchRequested.emit(search_text)
    
    def on_clear(self):
        self.search_active = False
        self.last_search_text = ''
        self.search_field.clear()
        self.clear_button.setEnabled(False)
        
        # 결과 네비게이션 숨김
        self.result_label.hide()
        self.prev_button.hide()
        self.next_button.hide()
        
        # 검색 초기화 시그널 발생
        self.searchCleared.emit()
    
    def on_prev(self):
        # 이전 결과 요청 시그널 발생
        self.prevResultRequested.emit()
    
    def on_next(self):
        # 다음 결과 요청 시그널 발생
        self.nextResultRequested.emit()
    
    def set_result_status(self, current_index, total_results):
        if total_results == 0:
            self.result_label.setText('result: No matching items')
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
        else:
            self.result_label.setText(f'<span style="font-size:26px;">result: {current_index}/{total_results}</span>')
            self.prev_button.setEnabled(current_index > 1)
            self.next_button.setEnabled(current_index < total_results)
    
    def show_result_navigation(self, show=True):
        if show:
            self.result_label.show()
            self.prev_button.show()
            self.next_button.show()
        else:
            self.result_label.hide()
            self.prev_button.hide()
            self.next_button.hide()
    
    def get_search_text(self):
        return self.last_search_text
    
    def is_search_active(self):
        return self.search_active