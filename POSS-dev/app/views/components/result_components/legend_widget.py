from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QCheckBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

"""
범례 및 필터 위젯
"""
class LegendWidget(QWidget):

    # 클래스 변수로 색상 미리 정의
    COLOR_SHORTAGE = QColor("#ff6e63")  # 빨간색
    COLOR_SHIPMENT = QColor("#fcc858")  # 주황색
    COLOR_PRE_ASSIGNED = QColor("#a8bbf0")  # 파란색

    # 필터 변경 시그널
    filter_changed = pyqtSignal(dict)  # {status_type: is_checked}
    
    # 특정 필터 활성화 요청 시그널 추가
    filter_activation_requested = pyqtSignal(str)  # status_type

    def __init__(self, parent=None):
        super().__init__(parent)
        font = font_manager.get_just_font("SamsungOne-700").family()
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border: none;
                font-family: {font};
            }}
        """)
        
        # 필터 상태 추적
        self.filter_states = {
            'shortage': True,      # 자재부족은 기본 체크 
            'shipment': False,      # 출하실패  
            'pre_assigned': False   # 사전할당
        }

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(h(40))
        
        # 범례 항목들
        self.checkbox_map = {}  # 체크박스 참조 저장
        self.create_legend_item(main_layout, "shortage", "#ff6e63", 'shortage')
        self.create_legend_item(main_layout, "shipment", "#fcc858", 'shipment')  
        self.create_legend_item(main_layout, "pre_assigned", "#a8bbf0", 'pre_assigned')
        
        # 스페이서 추가
        main_layout.addStretch(1)
        
        # 위젯 스타일
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)

    """
    필터 변경 시 호출
    """
    def on_filter_changed(self, status_type, is_checked):
        # 이전 상태와 동일하면 불필요한 처리 방지
        if self.filter_states.get(status_type) == is_checked:
            print(f"[LegendWidget] 상태 동일함, 스킵")
            return
        
        # 상태 업데이트
        self.filter_states[status_type] = is_checked
        print(f"[LegendWidget] 업데이트된 필터 상태: {self.filter_states}")
        
        # 필터 변경 신호 발생
        self.filter_changed.emit(self.filter_states.copy())
        
        # 필터가 활성화되면 해당 상태 분석 요청 
        if is_checked:
            print(f"[LegendWidget] 필터 활성화 요청: {status_type}")
            self.filter_activation_requested.emit(status_type)

    """
    필터 상태 직접 설정 (UI도 함께 업데이트)
    """
    def set_filter_states(self, filter_states):
        if not filter_states:
            return
            
        print(f"[LegendWidget] 필터 상태 직접 설정: {filter_states}")
        # 상태 업데이트
        self.filter_states = filter_states.copy()
        
        # 체크박스 UI 업데이트
        for status_type, checkbox in self.checkbox_map.items():
            if status_type in filter_states:
                is_checked = filter_states[status_type]
                if checkbox.isChecked() != is_checked:
                    # 시그널 일시 차단
                    checkbox.blockSignals(True)
                    checkbox.setChecked(is_checked)
                    checkbox.blockSignals(False)
                    print(f"[LegendWidget] 체크박스 업데이트: {status_type} = {is_checked}")
        
    """
    개별 범례 항목 생성
    """
    def create_legend_item(self, layout, label_text, color, status_type):
        item_frame = QFrame()
        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(5)
        
        # 체크박스
        checkbox = QCheckBox()
        checkbox.setChecked(True if status_type == 'shortage' else False)  # 기본값(자재부족) 
        checkbox.stateChanged.connect(lambda state, st=status_type: 
                                    self.on_filter_changed(st, state == Qt.Checked))
        
        # 체크박스 참조 저장
        self.checkbox_map[status_type] = checkbox
        item_layout.addWidget(checkbox)
        
        # 색상 표시
        color_frame = QFrame()
        color_frame.setFixedSize(w(15), h(15))
        color_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
            }}
        """)
        item_layout.addWidget(color_frame)
        
        # 라벨
        label = QLabel(label_text)
        item_layout.addWidget(label)
        layout.addWidget(item_frame)

    """
    필터 상태 재설정 (강제 업데이트)
    """
    def refresh_filters(self):
        print(f"[LegendWidget] 필터 새로고침: {self.filter_states}")
        # 현재 상태로 시그널 발생
        self.filter_changed.emit(self.filter_states.copy())
