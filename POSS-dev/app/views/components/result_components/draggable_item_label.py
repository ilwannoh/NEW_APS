from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QApplication, QToolTip, QSizePolicy, QMenu, QAction
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QColor, QFont
import pandas as pd
import json
import uuid
from app.resources.styles.item_style import ItemStyle
from app.utils.field_filter import filter_internal_fields
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager


"""
드래그 가능한 아이템 라벨
"""
class DraggableItemLabel(QFrame):

    # 아이템 선택 이벤트를 위한 시그널 추가
    itemSelected = pyqtSignal(object)  # 선택된 아이템 참조를 전달

    # 아이템 더블클릭 이벤트를 위한 시그널 추가
    itemDoubleClicked = pyqtSignal(object)  # 더블클릭된 아이템 참조를 전달

    # 검색 포커스 상태 변수
    is_search_focused = False

    # 아이템 삭제를 위한 시그널 추가
    itemDeleteRequested = pyqtSignal(object) # 마우스 우측 클릭하면 삭제 버튼이 나옴

    def __init__(self, text, parent=None, item_data=None):
        super().__init__(parent)

        self.setStyleSheet(ItemStyle.DEFAULT_STYLE)
        
        # 출하 실패 상태 변수
        self.is_shipment_failure = False
        self.shipment_failure_reason = None
        
        # 사전할당 상태 관련 속성 
        self.is_pre_assigned = False

        # 선택 상태 추가
        self.is_selected = False

        # 자재 부족 상태 관련 속성 추가
        self.is_shortage = False
        self.shortage_data = None

        # 기본 설정
        self.setStyleSheet(ItemStyle.DEFAULT_STYLE)
        self.setCursor(Qt.OpenHandCursor)
        self.setAcceptDrops(False)
        self.drag_start_position = None
        self.setMinimumHeight(25)
        self.setMinimumWidth(w(215))
        self.setMaximumWidth(w(215))

        self.adjustSize()

        # 아이템 데이터 저장 (엑셀 행 정보)
        self.item_data = item_data

        # 고유 ID 확인 및 생성
        if self.item_data and '_id' not in self.item_data:
            self.item_data['_id'] = str(uuid.uuid4())

        # 아이템 상태선 제어 속성
        self.show_shortage_line = True  # 자재부족 선 표시 여부
        self.show_shipment_line = False
        self.show_pre_assigned_line = False

        # 내부 레이아웃 생성
        self.setup_layout(text)

        # 툴팁 관련 설정
        QToolTip.setFont(QFont(font_manager.get_just_font("SamsungOne-700").family(), f(10)))

        # 아이템 데이터가 있으면 툴팁 생성
        if self.item_data is not None:
            self.setToolTip(self._create_tooltip_text())
        else:
            self.setToolTip(text if text else "")

        # 툴팁 자동 표시 활성화
        self.setMouseTracking(True)

        # 검색 포커스 상태
        self.is_search_focused = False
        # 현재 검색 결과 표시 여부
        self.is_search_current = False

        # 컨텍스트 메뉴 설정
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    """
    내부 레이아웃 설정 - 아이템명과 수량을 분리
    """
    def setup_layout(self, text):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(w(2))

        # 텍스트에서 아이템명과 수량 분리
        if self.item_data and 'Item' in self.item_data:
            item_name = str(self.item_data['Item'])
            qty = self.item_data.get('Qty', 0)  # 숫자로 저장 (기본값 0)
        else:
            # 기존 텍스트 파싱 (Item    Qty 형태)
            parts = text.split()
            if len(parts) >= 2:
                item_name = parts[0]
                qty = int(parts[-1])
            else:
                item_name = text
                qty = 0

        # 아이템명 라벨 (왼쪽 정렬)
        self.item_label = QLabel(item_name)
        font = font_manager.get_just_font("SamsungOne-700").family()
        self.item_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.item_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.item_label.setStyleSheet(f"background: transparent; border: none; font-family: {font}; font-size: {f(14)}px; font-weight: bold;")
        self.item_label.setWordWrap(True)  # WordWrap 활성화 : 활성화해야 컨테이너 높이 자동화 가능 

        # 수량 라벨 (오른쪽 정렬)
        self.qty_label = QLabel(str(qty) if qty > 0 else "0")  # 0이어도 표시
        self.qty_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.qty_label.setStyleSheet(f"background: transparent; border: none; font-family: {font}; font-size: {f(14)}px; font-weight: bold;")
        self.item_label.setWordWrap(True)  # WordWrap 활성화

        layout.addWidget(self.item_label)
        layout.addWidget(self.qty_label)

    """
    QLabel 호환성을 위한 text() 메서드
    """
    def text(self):
        item_text = self.item_label.text() if hasattr(self, 'item_label') else ''
        qty_text = self.qty_label.text() if hasattr(self, 'qty_label') else ''
        return f"{item_text}  {qty_text}" if qty_text else item_text

    """
    QLabel 호환성을 위한 setText() 메서드
    """
    def setText(self, text):
        # 텍스트 파싱해서 아이템명과 수량 분리
        parts = text.split()
        if len(parts) >= 2:
            item_name = parts[0]
            qty = parts[-1]
        else:
            item_name = text
            qty = ''
        
        if hasattr(self, 'item_label'):
            self.item_label.setText(item_name)
        if hasattr(self, 'qty_label'):
            self.qty_label.setText(qty)


    def _create_tooltip_text(self):
        if self.item_data is None:
            return self.text()
        
        # 필터링된 데이터로 툴팁 생성
        filtered_data = filter_internal_fields(self.item_data)

        # 통일된 테이블 스타일
        tooltip = """
        <style>
            table.tooltip-table {
                border-collapse: collapse;
                font-family: Arial, sans-serif;
                font-size: 10pt;
            }
            table.tooltip-table th {
                background-color: #1428A0;
                color: white;
                padding: 4px 8px;
            }
            table.tooltip-table td {
                background-color: #F5F5F5;
                padding: 4px 8px;
                border-bottom: 1px solid #E0E0E0;
            }
            table.tooltip-table tr:last-child td {
                border-bottom: none;
            }
        </style>
        <table class='tooltip-table'>
            <tr><th colspan='2'>Item Information</th></tr>
        """

        for key, value in filtered_data.items():
            if pd.notna(value):
                tooltip += f"<tr><td><b>{key}</b></td><td>{value}</td></tr>"

        if self.is_pre_assigned:
            tooltip += "<tr><td><b>Pre-Assigned</b></td><td style='color:green;'>Yes</td></tr>"
        if self.is_shortage:
            tooltip += "<tr><td><b>Material Shortage</b></td><td style='color:red;'>Yes</td></tr>"
        if self.is_shipment_failure:
            tooltip += "<tr><td><b>Shipment Status</b></td><td style='color:red;'>Failure</td></tr>"
            if self.shipment_failure_reason:
                tooltip += f"<tr><td><b>Failure Reason</b></td><td>{self.shipment_failure_reason}</td></tr>"

        tooltip += "</table>"
        return tooltip

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.setCursor(Qt.ClosedHandCursor)  # 마우스 누를 때 커서 변경

            # *** 수정: 클릭 시 다른 아이템 선택 해제 후 현재 아이템 선택 ***
            # 부모 컨테이너를 통해 다른 아이템들의 선택 해제 요청
            parent_container = self.parent()
            if hasattr(parent_container, 'clear_selection'):
                # 현재 아이템을 제외하고 다른 아이템들 선택 해제
                parent_container.clear_selection_except(self)

            # 현재 아이템 선택
            if not self.is_selected:
                self.set_selected(True)
                # 선택 상태 변경 이벤트 발생
                self.itemSelected.emit(self)



    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.OpenHandCursor)  # 마우스 놓을 때 커서 원래대로

    """
    더블클릭 이벤트 처리
    """
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 더블클릭 이벤트 발생
            self.itemDoubleClicked.emit(self)
            event.accept()

    """
    마우스가 위젯 위에 올라갔을 때 호출됨
    """
    def enterEvent(self, event):
        # 현재 검색 아이템이면 hover 스타일 적용하지 않음
        if hasattr(self, 'is_search_current') and self.is_search_current:
            return

        if self.is_search_current:
            pass
        elif self.is_search_focused:
            self.setStyleSheet(ItemStyle.SEARCH_FOCUSED_HOVER_STYLE)
        elif not self.is_selected:
            if self.is_pre_assigned and self.is_shortage and self.is_shipment_failure:  # 사전할당/자재부족/출하실패
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SHORTAGE_SHIPMENT_HOVER_STYLE)
            elif self.is_pre_assigned and self.is_shortage:  # 사전할당/자재부족
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SHORTAGE_HOVER_STYLE)
            elif self.is_pre_assigned and self.is_shipment_failure:  # 사전할당/출하실패
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SHIPMENT_HOVER_STYLE)
            elif self.is_shortage and self.is_shipment_failure:  # 자재부족/출하실패
                self.setStyleSheet(ItemStyle.SHORTAGE_SHIPMENT_HOVER_STYLE)
            elif self.is_pre_assigned:
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_HOVER_STYLE)
            elif self.is_shortage:
                self.setStyleSheet(ItemStyle.SHORTAGE_HOVER_STYLE)
            elif self.is_shipment_failure:
                self.setStyleSheet(ItemStyle.SHIPMENT_FAILURE_HOVER_STYLE)
            else:
                self.setStyleSheet(ItemStyle.HOVER_STYLE)
        super().enterEvent(event)

    """
    마우스가 위젯을 벗어났을 때 호출됨
    """
    def leaveEvent(self, event):
        # 현재 검색 아이템이면 원래 스타일 유지
        if hasattr(self, 'is_search_current') and self.is_search_current:
            self.update_search_style()
            return

        if not self.is_selected:
            self.update_style()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self.drag_start_position is None:
            return

        # 최소 드래그 거리 확인 (맨해튼 거리)
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = QMimeData()

        # 텍스트 데이터 저장
        mime_data.setText(self.text())

        # 아이템 데이터를 JSON으로 직렬화하여 저장
        if self.item_data is not None:
            # 딕셔너리의 모든 값을 문자열로 변환 (JSON 직렬화를 위해)
            serializable_data = {}
            for k, v in self.item_data.items():
                if pd.isna(v):  # NaN 값은 None으로 변환
                    serializable_data[k] = None
                elif isinstance(v, (int, float, bool)):  #  숫자타입은 그대로 유지
                    serializable_data[k] = v
                else:
                    serializable_data[k] = str(v)

            # 고유 ID 확인
            if '_id' not in serializable_data:
                serializable_data['_id'] = str(uuid.uuid4())
                # 원본 item_data에도 ID 추가
                self.item_data['_id'] = serializable_data['_id']

            # JSON으로 직렬화하여 MIME 데이터에 저장
            json_data = json.dumps(serializable_data)
            mime_data.setData("application/x-item-full-data", json_data.encode())

            # 디버깅을 위한 출력
            # print(f"직렬화된 데이터: {json_data}")

        # 기본 아이템 식별자도 함께 저장 (이전 버전과의 호환성 유지)
        mime_data.setData("application/x-item-data", self.text().encode())

        drag.setMimeData(mime_data)

        # 드래그 중 표시될 이미지 생성
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)  # 투명 배경으로 시작

        # 아이템의 현재 모습을 픽스맵에 그리기
        painter = QPainter(pixmap)
        painter.setOpacity(0.7)  # 약간 투명하게 만들기
        self.render(painter)
        painter.end()

        # 드래그 이미지 설정
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())  # 마우스 커서 위치 설정

        # 드래그 액션 실행
        drag.exec_(Qt.MoveAction)

    """
    선택 상태 토글 및 스타일 적용
    """
    def toggle_selected(self):
        self.is_selected = not self.is_selected
        self.update_style()

    """
    선택 상태 직접 설정
    """
    def set_selected(self, selected):
        if self.is_selected != selected:
            self.is_selected = selected
            self.update_style()

    """
    사전할당 상태 설정
    """
    def set_pre_assigned_status(self, is_pre_assigned):
        self.is_pre_assigned = is_pre_assigned
        self.update_style()

        # 툴팁에도 사전할당 정보 표시
        if self.item_data is not None:
            self.setToolTip(self._create_tooltip_text())

    """
    자재 부족 상태 설정
    """
    def set_shortage_status(self, is_shortage, shortage_data=None):
        self.is_shortage = is_shortage
        self.shortage_data = shortage_data
        self.update_style()
        
        # 자재 부족 상태에 따라 툴팁 업데이트
        if is_shortage and shortage_data:
            self.setToolTip(self._create_shortage_tooltip())
        else:
            # 기본 툴팁 사용
            if self.item_data is not None:
                self.setToolTip(self._create_tooltip_text())
            else:
                self.setToolTip(self.text())

    """
    자재 부족 정보 툴팁 생성
    """
    def _create_shortage_tooltip(self):
        if not self.shortage_data:
            return self._create_tooltip_text()
        
        item_code = self.item_data.get('Item', 'Unknown Item') if self.item_data else 'Unknown Item'
        
        tooltip = f"<b>{item_code}</b> Material Shortage Details:<br><br>"
        tooltip += "<table border='1' cellspacing='0' cellpadding='3'>"
        
        # Material과 Shortage 컬럼은 항상 있지만, Required와 Available은 없을 수 있음
        has_required = any('Required' in s or 'required' in s for s in self.shortage_data)
        has_available = any('Available' in s or 'available' in s for s in self.shortage_data)
        
        # 테이블 헤더 동적 생성
        if has_required and has_available:
            tooltip += "<tr style='background-color:#f0f0f0'><th>Material</th><th>Required</th><th>Available</th><th>Shortage</th></tr>"
        else:
            tooltip += "<tr style='background-color:#f0f0f0'><th>Material</th><th>Shortage</th></tr>"
        
        for shortage in self.shortage_data:
            tooltip += f"<tr>"
            # Material 키는 소문자로 통일 (KeyError 방지)
            material = shortage.get('material')
            if material:
                tooltip += f"<td>{material}</td>"
            else:
                tooltip += f"<td>Unknown</td>"
                
            # Required와 Available 컬럼이 있을 경우에만 표시
            if has_required and has_available:
                required = shortage.get('Required', shortage.get('required', 0))
                available = shortage.get('Available', shortage.get('available', 0))
                tooltip += f"<td align='right'>{int(required):,}</td>"
                tooltip += f"<td align='right'>{int(available):,}</td>"
            
            # Shortage는 항상 있음
            shortage_amt = shortage.get('shortage', 0)
            tooltip += f"<td align='right' style='color:red'>{int(shortage_amt):,}</td>"
            tooltip += f"</tr>"
        
        tooltip += "</table>"
        return tooltip

    """
    현재 상태에 맞게 스타일 업데이트
    """
    def update_style(self):
        # 검색 포커스 스타일
        if self.is_search_focused:
            self.setStyleSheet(ItemStyle.SEARCH_FOCUSED_STYLE)
            return
        if self.is_selected:
            if self.is_pre_assigned and self.is_shortage and self.is_shipment_failure:  
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SHORTAGE_SHIPMENT_SELECTED_STYLE)
            elif self.is_pre_assigned and self.is_shortage:
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SHORTAGE_SELECTED_STYLE)
            elif self.is_pre_assigned and self.is_shipment_failure:
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SHIPMENT_SELECTED_STYLE)
            elif self.is_shortage and self.is_shipment_failure:
                self.setStyleSheet(ItemStyle.SHORTAGE_SHIPMENT_SELECTED_STYLE)  
            elif self.is_pre_assigned:
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SELECTED_STYLE)
            elif self.is_shortage:
                self.setStyleSheet(ItemStyle.SHORTAGE_SELECTED_STYLE)
            elif self.is_shipment_failure:
                self.setStyleSheet(ItemStyle.SHIPMENT_FAILURE_SELECTED_STYLE)
            else:
                self.setStyleSheet(ItemStyle.SELECTED_STYLE)
        else:
            if self.is_pre_assigned and self.is_shortage and self.is_shipment_failure:
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SHORTAGE_SHIPMENT_STYLE)
            elif self.is_pre_assigned and self.is_shortage:
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SHORTAGE_STYLE)
            elif self.is_pre_assigned and self.is_shipment_failure:
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_SHIPMENT_STYLE)
            elif self.is_shortage and self.is_shipment_failure:
                self.setStyleSheet(ItemStyle.SHORTAGE_SHIPMENT_STYLE) 
            elif self.is_pre_assigned:
                self.setStyleSheet(ItemStyle.PRE_ASSIGNED_STYLE)
            elif self.is_shortage:
                self.setStyleSheet(ItemStyle.SHORTAGE_STYLE)
            elif self.is_shipment_failure:
                self.setStyleSheet(ItemStyle.SHIPMENT_FAILURE_STYLE)
            else:
                self.setStyleSheet(ItemStyle.DEFAULT_STYLE)

    """
    템 데이터로부터 표시 텍스트 업데이트
    """
    def update_text_from_data(self):        
        if self.item_data and 'Item' in self.item_data:
            item_info = str(self.item_data['Item'])
            qty = self.item_data.get('Qty', 0)
            
            # 수량 처리 - None이나 공백도 0으로 표시
            if qty is None or qty == '':
                qty = 0
            
            # 문자열인 경우 정수로 변환 시도
            if isinstance(qty, str):
                qty_value = int(qty)
            else:
                qty_value = qty
                
            if hasattr(self, 'item_label'):
                self.item_label.setText(item_info)
            if hasattr(self, 'qty_label'):
                self.qty_label.setText(str(qty) if qty_value > 0 else "0")

    """
    아이템 데이터 업데이트
    """
    def update_item_data(self, new_data):
        if new_data:
            # 데이터 변경 전 검증 (부모 위젯을 통해 validator 찾기)
            validator = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'validator'):
                    validator = parent.validator
                    break
                # 그리드 위젯을 통해 validator 찾기
                if hasattr(parent, 'grid_widget') and hasattr(parent.grid_widget, 'validator'):
                    validator = parent.grid_widget.validator
                    break
                parent = parent.parent()
            
            # validator가 있으면 검증 수행
            if validator:
                # 현재 데이터와 신규 데이터 비교하여 변경 항목 검출
                is_move = False
                if self.item_data:
                    if ('Line' in new_data and 'Line' in self.item_data and 
                        new_data['Line'] != self.item_data['Line']):
                        is_move = True
                    if ('Time' in new_data and 'Time' in self.item_data and 
                        new_data['Time'] != self.item_data['Time']):
                        is_move = True
                
                # 검증 실행
                valid, message = validator.validate_adjustment(
                    new_data.get('Line'), 
                    new_data.get('Time'),
                    new_data.get('Item', ''),
                    new_data.get('Qty', 0),
                    self.item_data.get('Line') if is_move else None,
                    self.item_data.get('Time') if is_move else None
                )
                
                # 검증 실패 시 데이터 변경하지 않고 False 반환
                if not valid:
                    validation_failed = True
                    validation_mesasge = message
                    print(f"검증 실패지만 변경 허용: {message}")
                
            # 검증 상관없이 데이터 업데이트 진행
            self.item_data = new_data.copy() if new_data else None

            # 텍스트와 툴팁 업데이트
            self.update_text_from_data()
            self.setToolTip(self._create_tooltip_text())
            return True, ""
            
        return False, "데이터가 없습니다."
    
    """
    출하 실패 상태 설정
    """
    def set_shipment_failure(self, is_failure, reason=None):
        self.is_shipment_failure = is_failure
        self.shipment_failure_reason = reason if is_failure else None
        self.update_style()  # 스타일 업데이트
        
        # 툴팁 업데이트 
        self.setToolTip(self._create_tooltip_text())
        

    """
    아이템 상태별 색상 선 표시
    """
    def paintEvent(self, event):
        # 기본 QLabel 의 paintEvent 호출
        super().paintEvent(event)
        
        # 현재 표시 상태 확인
        has_status_lines = (self.is_shortage and self.show_shortage_line) or \
                        (self.is_shipment_failure and self.show_shipment_line) or \
                        (self.is_pre_assigned and self.show_pre_assigned_line)
        
        # 상태선이 있는 경우만 그리기 로직 실행
        if has_status_lines:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 선 너비 및 위치 설정
            line_width = 5
            line_gap = 0
            current_x = 0
            
            # 각 상태에 맞는 색상 선 그리기
            if self.is_shortage and self.show_shortage_line:
                painter.fillRect(current_x, 0, line_width, self.height(), QColor("#ff6e63"))
                current_x += line_width + line_gap
                
            if self.is_shipment_failure and self.show_shipment_line:
                painter.fillRect(current_x, 0, line_width, self.height(), QColor("#fcc858"))
                current_x += line_width + line_gap
                
            if self.is_pre_assigned and self.show_pre_assigned_line:
                painter.fillRect(current_x, 0, line_width, self.height(), QColor("#a8bbf0"))
            
            painter.end()

    """
    QLabel 호환성을 위한 setWordWrap() 메서드
    """
    def setWordWrap(self, wrap):
        if hasattr(self, 'item_label'):
            self.item_label.setWordWrap(wrap)
        if hasattr(self, 'qty_label'):
            self.qty_label.setWordWrap(wrap)

    """
    검색 포커스 설정 메서드
    """
    def set_search_focus(self, focused=True):
        # 상태가 동일하면 중복 처리 방지
        if hasattr(self, 'is_search_focused') and self.is_search_focused == focused:
            return

        self.is_search_focused = focused

        # 포커스가 해제되면 현재 선택 상태도 함께 해제
        if not focused and hasattr(self, 'is_search_current'):
            self.is_search_current = False

        # 스타일 업데이트만 수행 (추가 업데이트 방지)
        if focused:
            self.setStyleSheet(ItemStyle.SEARCH_FOCUSED_STYLE)
        else:
            self.update_style()

    """
    아이템을 삭제할 때 사용
    """
    def show_context_menu(self, position):
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
            }
            QMenu::item {
                background-color: transparent;
                padding: 6px 20px;
                border-radius: 4px;
                margin: 3px;
            }
            QMenu::item:selected {
                background-color: #1428A0;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #c0c0c0;
                margin: 5px 10px;
            }
        """)

        delete_action = QAction("Delete Item", self)
        delete_action.triggered.connect(self.request_delete)
        context_menu.addAction(delete_action)

        context_menu.exec_(self.mapToGlobal(position))

    """
    삭제 요청 메서드
    """
    def request_delete(self):
        self.itemDeleteRequested.emit(self)

    """
    검색 결과 중 현재 선택된 아이템 특별 스타일 적용
    """
    def set_search_selected(self, selected=False):
        if selected:
            self.setStyleSheet(ItemStyle.SEARCH_SELECTED_STYLE)
        else:
            if self.is_search_focused:
                self.setStyleSheet(ItemStyle.SEARCH_FOCUSED_STYLE)
            else:
                self.update_style()

    """
    현재 검색 결과에서 특별히 강조할 아이템 설정
    """
    def set_search_current(self, is_current=False):
        # 상태가 동일하면 중복 처리 방지
        if hasattr(self, 'is_search_current') and self.is_search_current == is_current:
            return

        self.is_search_current = is_current

        # 스타일 업데이트만 수행 (repaint/update 제거)
        if is_current:
            # 인라인 스타일로 직접 적용
            self.setStyleSheet(ItemStyle.SEARCH_CURRENT_STYLE)
        else:
            self.update_search_style()

    """
    검색 관련 스타일 업데이트
    """
    def update_search_style(self):
        if hasattr(self, 'is_search_current') and self.is_search_current:
            # 현재 검색 위치 강조 스타일 (최우선)
            self.setStyleSheet(ItemStyle.SEARCH_CURRENT_STYLE)
        elif self.is_search_focused:
            # 일반 검색 결과 스타일
            self.setStyleSheet(ItemStyle.SEARCH_FOCUSED_STYLE)
        else:
            # 기본 스타일
            self.update_style()

