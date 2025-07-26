from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from app.utils.item_key_manager import ItemKeyManager
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

"""
조정 시 에러 메세지 관리 클래스
"""
class AdjErrorManager():
    def __init__(self, parent_widget, error_scroll_area, navigate_callback, left_section):
        self.parent_widget = parent_widget
        self.error_scroll_area = error_scroll_area
        self.navigate_callback = navigate_callback
        self.left_section = left_section

        # 에러 표시 위젯 초기화
        self.error_display_widget = QWidget()
        self.error_display_layout = QVBoxLayout(self.error_display_widget)
        self.error_display_layout.setContentsMargins(3, 3, 3, 3)
        self.error_display_layout.setSpacing(3)
        self.error_display_layout.setAlignment(Qt.AlignTop)
        
        self.error_scroll_area.setWidget(self.error_display_widget)

        # 에러 저장소
        self.validation_errors = {}

        self.update_error_display()

    """
    에러 관리
    """
    def add_validation_error(self, item_info, error_message):
        # ID 우선으로 에러 키 생성
        error_key = ItemKeyManager.get_item_key(item_info)

        # 기존 에러로그들을 유효한 에러로그들로만 필터링
        updated_errors = {}
        for key, value in self.validation_errors.items():
            info = value['item_info']
            
            # ID 기반 존재 확인 
            if '_id' in info and info['_id']:
                # ID가 있으면 ID로 존재 확인
                mask = ItemKeyManager.create_mask_by_id(self.left_section.data, info['_id'])
                exists = mask.any()
            else:
                # ID가 없으면 기존 방식으로 존재 확인
                line, time, item = info.get('Line'), info.get('Time'), info.get('Item')
                exists = any(
                    (self.left_section.data['Line'] == line) &
                    (self.left_section.data['Time'] == time) &
                    (self.left_section.data['Item'] == item)
                )
                 
            if exists:
                updated_errors[key] = value
        self.validation_errors = updated_errors

        # 새로운 에러 추가
        if error_message:
            self.validation_errors[error_key] = {
                'item_info': item_info,
                'message': error_message
            }
        else:
            # 에러 메시지가 None이면 해당 에러 제거
            if error_key in self.validation_errors:
                del self.validation_errors[error_key]

        # left_section에 정보 전달
        if hasattr(self.left_section, 'set_current_validation_errors'):
            self.left_section.set_current_validation_errors(self.validation_errors)

        # 에러 표시 업데이트
        self.update_error_display()

        # 해당 아이템 카드 강조
        self.highlight_error_item(item_info)

        return self.validation_errors
    

    """
    에러 표시 위젯 업데이트
    """
    def update_error_display(self):
        # 기존 에러 위젯 제거
        for i in reversed(range(self.error_display_layout.count())):
            child = self.error_display_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        # 에러가 없으면 기본 메시지 표시
        if not self.validation_errors:
            no_error_message = QLabel("No adjustment issues detected")
            no_error_message.setAlignment(Qt.AlignCenter)
            no_error_message.setStyleSheet(f"""
                QLabel {{
                    color: #666;
                    font-size: {f(13)}px;
                    padding: 20px;
                    border: none;
                }}
            """)
            self.error_display_layout.addWidget(no_error_message)
            return
        
        # 기존 에러로그들을 유효한 에러로그들로만 필터링
        updated_errors = {}
        for key, value in self.validation_errors.items():
            info = value['item_info']
            item_id = info.get('_id')
            if item_id:
                mask = ItemKeyManager.create_mask_by_id(self.left_section.data, item_id)
                exists = mask.any()
            else:
                line, time, item = info.get('Line'), info.get('Time'), info.get('Item')
                exists = any(
                    (self.left_section.data['Line'] == line) &
                    (self.left_section.data['Time'] == time) &
                    (self.left_section.data['Item'] == item)
                )
            if exists:
                updated_errors[key] = value
        self.validation_errors = updated_errors

        # 각 에러위젯 추가
        for error_key, error_info in self.validation_errors.items():
            error_widget = self.create_error_item_widget(error_info)
            self.error_display_layout.addWidget(error_widget)

        
    """
    에러 항목 위젯 생성
    """
    def create_error_item_widget(self, error_info):
        class ClickableErrorFrame(QFrame):
            def __init__(self, error_info, navigate_callback):
                super().__init__()
                self.error_info = error_info
                self.navigate_callback = navigate_callback

            def mousePressEvent(self, event):
                if event.button() == Qt.LeftButton:
                    self.navigate_callback(self.error_info)
                super().mousePressEvent(event)

        widget = ClickableErrorFrame(error_info, self.navigate_callback)
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
                border-bottom: 1px solid #F0F0F0;
            }
            QFrame:hover {
                background-color: #F8F9FA;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        item_info = error_info['item_info']
        item_location_text = f"Item: {item_info.get('Item', 'N/A')} | Line: {item_info.get('Line', 'N/A')}, Time: {item_info.get('Time', 'N/A')}"
        
        item_location_label = QLabel(item_location_text)
        item_location_label.setStyleSheet(f"""
            font-size: {f(13)}px;
            color: #666666;
            font-family: {font_manager.get_just_font("SamsungOne-700").family()};
            background: transparent;
            border: none;
        """)
        item_location_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(item_location_label)

        # 두 번째 줄: 에러 메시지
        message_label = QLabel(error_info['message'])
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            font-size: {f(13)}px;
            color: #E74C3C;
            font-weight: 500;
            font-family: {font_manager.get_just_font("SamsungOne-700").family()};
            background: transparent;
            border: none;
        """)
        message_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(message_label)

        return widget
    
    """
    현재 검증 에러 반환
    """
    def get_validation_errors(self):
        return self.validation_errors.copy()

    """
    에러 여부 확인
    """
    def has_errors(self):
        return bool(self.validation_errors)
    
    """
    에러가 있는 아이템 카드 강조
    """
    def highlight_error_item(self, item_info):
        if not hasattr(self, 'left_section') or not hasattr(self.left_section, 'grid_widget'):
            return
        
        try: 
            # ID가 있으면 ID로 아이템 찾기
            if '_id' in item_info and item_info['_id']:
                item_id = item_info['_id']
                # 그리드에서 ID로 아이템 찾기
                for row_containers in self.left_section.grid_widget.containers:
                    for container in row_containers:
                        for item in container.items:
                            if (hasattr(item, 'item_data') and item.item_data and 
                                item.item_data.get('_id') == item_id):
                                item.set_selected(True)
                                return
            else:
                for row_containers in self.left_section.grid_widget.containers:
                    for container in row_containers:
                        for item in container.items:
                            if (hasattr(item, 'item_data') and item.item_data and 
                                item.item_data.get('Line') == item_info.get('Line') and 
                                item.item_data.get('Time') == item_info.get('Time') and 
                                item.item_data.get('Item') == item_info.get('Item')):

                                # 에러 스타일 적용 대신 그냥 선택 상태로만 변경
                                item.set_selected(True)
                                return

        except Exception as e:
            print(f"에러 하이라이트 실패:{e}")


    """
    아이템 카드 강조 해제
    """
    def remove_item_highlight(self, item_info):
        if not hasattr(self, 'left_section') or not hasattr(self.left_section, 'grid_widget'):
            return
        
        # 그리드에서 해당 아이템 찾기
        for row_containers in self.left_section.grid_widget.containers:
            for container in row_containers:
                for item in container.items:
                    if (hasattr(item, 'item_data') and item.item_data and 
                        item.item_data.get('Line') == item_info.get('Line') and 
                        item.item_data.get('Time') == item_info.get('Time') and 
                        item.item_data.get('Item') == item_info.get('Item')):

                        # 에러 상태 해제 대신 그냥 선택 해제
                        item.set_selected(False)
                        return
    

