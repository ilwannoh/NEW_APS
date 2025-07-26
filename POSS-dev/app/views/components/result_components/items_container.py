from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen
from .draggable_item_label import DraggableItemLabel
from .item_edit_dialog import ItemEditDialog
import json
import uuid
from app.utils.item_key_manager import ItemKeyManager
from app.models.common.screen_manager import *

"""
아이템들을 담는 컨테이너 위젯
"""
class ItemsContainer(QWidget):
    itemsChanged = pyqtSignal(object)
    itemSelected = pyqtSignal(object, object)  # (선택된 아이템, 컨테이너) 시그널 추가
    itemDataChanged = pyqtSignal(object, dict, dict)  # (아이템, 새 데이터, 변경 필드 정보) 시그널 추가
    itemCopied = pyqtSignal(object, dict)  # 복사된 아이템 시그널 추가

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(w(2))
        self.setAcceptDrops(True)
        self.items = []  # 아이템 라벨 리스트
        self.selected_item = None  # 현재 선택된 아이템

        self.base_height = 100
        self.item_height = 30  # 각 아이템의 예상 높이
        self.setMinimumHeight(self.base_height)

        # 드롭 인디케이터 관련 변수
        self.drop_indicator_position = -1
        self.show_drop_indicator = False

        self.default_style = "border: 1px solid  background-color: white;"
        self.empty_style = "background-color: rgba(245, 245, 245, 0.5); border: 1px dashed #cccccc;"

        # 늘어나는 공간을 위한 스페이서 추가
        self.spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addSpacerItem(self.spacer)

    """
    아이템 상태 업데이트
    """
    def update_visibility(self):
        # 모든 아이템은 항상 visible 상태로 유지
        # 필터링은 선의 표시 여부로만 처리
        pass

    """
    현재 컨테이너의 부모 찾기
    """
    def find_parent_grid_widget(self):
        parent = self.parent()

        while parent:
            if hasattr(parent, 'containers') and isinstance(parent.containers, list):
                return parent
            parent = parent.parent()
        return None

    """
    아이템을 추가합니다. index가 -1이면 맨 뒤에 추가, 그 외에는 해당 인덱스에 삽입
    item_data: 아이템에 대한 추가 정보 (pandas Series 또는 딕셔너리)
    """
    def addItem(self, item_text, index=-1, item_data=None):
        self.layout.removeItem(self.spacer)

        item_label = DraggableItemLabel(item_text, self, item_data)
        # item_label.setFont(QFont('Arial', 8, QFont.Normal))

        # 아이템 선택 이벤트 연결
        item_label.itemSelected.connect(self.on_item_selected)

        # 아이템 더블클릭 이벤트 연결
        item_label.itemDoubleClicked.connect(self.on_item_double_clicked)

        # 삭제 요청 이벤트 연결
        item_label.itemDeleteRequested.connect(self.on_item_delete_requested)

        if index == -1 or index >= len(self.items):
            # 맨 뒤에 추가
            self.layout.addWidget(item_label)
            self.items.append(item_label)
        else:
            # 특정 위치에 삽입
            self.layout.insertWidget(index, item_label)
            self.items.insert(index, item_label)

        # 스페이서 다시 추가 (항상 맨 아래에 위치하도록)
        self.layout.addSpacerItem(self.spacer)

        # self.update_visibility()
        # 모든 아이템이 항상 보이도록
        item_label.show()

        return item_label

    """
    아이템이 선택되었을 때 처리
    """
    def on_item_selected(self, selected_item):
        # 이전에 선택된 아이템이 있고, 현재 선택된 아이템과 다르다면 선택 해제
        if self.selected_item and self.selected_item != selected_item:
            self.selected_item.set_selected(False)

        # 새로 선택된 아이템 저장
        self.selected_item = selected_item

        # 선택 이벤트 발생 (상위 위젯에서 다른 컨테이너의 선택 해제 등을 처리할 수 있도록)
        self.itemSelected.emit(selected_item, self)

    """
    아이템이 더블클릭되었을 때 처리
    """
    def on_item_double_clicked(self, item):
        print(f"DEBUG: on_item_double_clicked 호출됨")
        if not item or not hasattr(item, 'item_data'):
            return

        # 수정 다이얼로그 생성
        dialog = ItemEditDialog(item.item_data, self)

        # 데이터 변경 이벤트 연결 (변경된 필드 정보 포함)
        dialog.itemDataChanged.connect(lambda new_data, changed_fields:
                                       self.update_item_data(item, new_data, changed_fields))

        # 다이얼로그 실행
        dialog.exec_()

    """
    아이템 데이터 업데이트
    """
    def update_item_data(self, item, new_data, changed_fields=None):
        print(f"DEBUG: update_item_data 호출됨 - 아이템: {item}, 변경필드: {changed_fields}")

        if item and item in self.items and new_data:
            # 데이터 변경 시그널 발생
            self.itemDataChanged.emit(item, new_data, changed_fields)

            item_id = ItemKeyManager.extract_item_id(item)
            self.itemsChanged.emit(item_id)
            return True, ""

        return False, "유효하지 않은 아이템 또는 데이터"

    """
    모든 아이템 선택 해제
    """
    def clear_selection(self):
        # 모든 아이템 선택 해제
        selection_changed = False

        for item in self.items:
            if hasattr(item, 'is_selected') and item.is_selected:
                item.set_selected(False)
                selection_changed = True

        # 컨테이너 레벨에서 선택된 아이템도 초기화
        if self.selected_item:
            self.selected_item = None
            selection_changed = True

        return selection_changed
    """
    특정 아이템 삭제
    """
    def remove_item(self, item):
        if item in self.items:
            # ID 추출
            item_id = ItemKeyManager.extract_item_id(item)

            # 선택된 아이템을 삭제하는 경우 선택 상태 초기화
            if item == self.selected_item:
                self.selected_item = None

            # 아이템 UI에서 제거
            self.layout.removeWidget(item)
            self.items.remove(item)
            item.deleteLater()

            # MVC 모드에서는 Controller만 호출 
            controller = self._find_controller()
            if controller:
                # Controller의 모델을 통해 삭제 처리 (분석 포함)
                controller.model.delete_item_by_id(item_id)
                return
            else:
                # Legacy 모드: 기존 방식
                self.itemsChanged.emit(item_id)
            
            self.update_visibility()

    """
    모든 아이템 삭제
    """
    def clear_items(self):
        self.selected_item = None  # 선택 상태 초기화

        # 스페이서 제거
        self.layout.removeItem(self.spacer)

        items_to_remove = self.items.copy()

        for item in items_to_remove:
            self.layout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        self.items.clear()

        # 스페이서 다시 추가
        self.layout.addSpacerItem(self.spacer)

        self.update_visibility()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

            # 드래그 소스 확인 - 같은 컨테이너인지 다른 컨테이너인지 판단
            source = event.source()
            source_container = None
            if isinstance(source, DraggableItemLabel):
                source_container = source.parent()

            # 다른 컨테이너에서 드래그 중인 경우
            if source_container and source_container != self:
                # 전체 컨테이너를 인디케이터로 표시
                self.show_drop_indicator = True
                self.drop_indicator_position = -2  # 특수값: 전체 컨테이너 표시
            else:
                # 같은 컨테이너 내에서는 기존 로직 유지
                self.show_drop_indicator = True
                self.drop_indicator_position = self.findDropIndex(event.pos())

            self.update()

    """
    드래그가 위젯을 벗어날 때 인디케이터 숨김
    """
    def dragLeaveEvent(self, event):
        self.show_drop_indicator = False
        self.update()

    """
    드래그 중 드롭 가능한 위치에 시각적 표시
    """
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

            # 드래그 소스 확인 - 같은 컨테이너인지 다른 컨테이너인지 판단
            source = event.source()
            source_container = None
            if isinstance(source, DraggableItemLabel):
                source_container = source.parent()

            # 다른 컨테이너에서 드래그 중인 경우
            if source_container and source_container != self:
                # 전체 컨테이너를 인디케이터로 표시
                self.drop_indicator_position = -2  # 특수값: 전체 컨테이너 표시
            else:
                # 같은 컨테이너 내에서는 기존 로직 유지
                self.drop_indicator_position = self.findDropIndex(event.pos())

            self.update()

    """
    드롭된 위치에 해당하는 아이템 인덱스를 찾습니다.
    """
    def findDropIndex(self, pos):
        if not self.items:
            return 0  # 아이템이 없으면 첫 번째 위치에 삽입

        # 각 아이템의 위치를 검사하여 드롭 위치 결정
        for i, item in enumerate(self.items):
            item_rect = item.geometry()
            item_mid_y = item_rect.top() + item_rect.height() / 2

            if pos.y() < item_mid_y:
                return i  # 아이템의 중간점보다 위에 드롭되면 해당 아이템 앞에 삽입

        return len(self.items)  # 모든 아이템보다 아래에 드롭되면 마지막에 삽입


    def dropEvent(self, event):
        if event.mimeData().hasText():
            # 드래그된 아이템 텍스트 가져오기
            item_text = event.mimeData().text()

            # 전체 아이템 데이터 가져오기 (JSON 형식)
            item_data = None
            if event.mimeData().hasFormat("application/x-item-full-data"):
                try:
                    data_bytes = event.mimeData().data("application/x-item-full-data")
                    json_str = data_bytes.data().decode()
                    item_data = json.loads(json_str)

                    if isinstance(item_data, dict):
                        item_data['_drop_pos_x'] = event.pos().x()
                        item_data['_drop_pos_y'] = event.pos().y()
                except Exception as e:
                    print(f"아이템 데이터 파싱 오류: {e}")

            # 원본 위젯 (드래그된 아이템)
            source = event.source()
            is_ctrl_pressed = event.keyboardModifiers() & Qt.ControlModifier

            # 드롭 인디케이터 숨기기 
            self.show_drop_indicator = False
            self.update()

            # 기존 아이템 상태 백업
            source_states = {}
            was_selected = False  # 선택 상태 백업 추가
            if isinstance(source, DraggableItemLabel):
                source_states = {
                    'is_shortage': getattr(source, 'is_shortage', False),
                    'shortage_data': getattr(source, 'shortage_data', None),
                    'is_pre_assigned': getattr(source, 'is_pre_assigned', False),
                    'is_shipment_failure': getattr(source, 'is_shipment_failure', False),
                    'shipment_failure_reason': getattr(source, 'shipment_failure_reason', None),
                }
                # 선택 상태 백업 
                was_selected = getattr(source, 'is_selected', False)

            if is_ctrl_pressed and isinstance(source, DraggableItemLabel):
                # Ctrl+드래그 복사 처리
                source_container = source.parent()

                if item_data is None and hasattr(source, 'item_data') and source.item_data:
                    item_data = source.item_data.copy()

                if item_data:
                    item_data['Qty'] = 0
                    item_data['_is_copy'] = True
                    # 새로운 ID 생성 (기존 ID 덮어쓰기)
                    item_data['_id'] = str(uuid.uuid4())
                    item_data.pop('_drop_pos_x', None)
                    item_data.pop('_drop_pos_y', None)

                    # 위치 계산
                    grid_widget = self.find_parent_grid_widget()
                    if grid_widget:
                        for row_idx, row in enumerate(grid_widget.containers):
                            if self in row:
                                target_row = row_idx
                                target_col = row.index(self)
                                break

                        if target_row < len(grid_widget.row_headers) and '_(' in grid_widget.row_headers[target_row]:
                            line_part = grid_widget.row_headers[target_row].split('_(')[0]
                            shift_part = grid_widget.row_headers[target_row].split('_(')[1].rstrip(')')

                            item_data['Line'] = line_part
                            day_idx = target_col
                            is_day_shift = shift_part == "Day"
                            new_time = (day_idx * 2) + (1 if is_day_shift else 2)
                            item_data['Time'] = str(new_time)

               # MVC 모드에서는 Controller가 처리하도록 변경
                controller = self._find_controller()
                if controller:
                    print("복사: Controller가 처리")
                    # Controller를 통해 복사 처리 (UI 생성은 Controller에서 담당)
                    controller.on_item_copied(None, item_data)
                    event.acceptProposedAction()
                    return
                else:
                    # Legacy 모드: 기존 방식으로 UI에 직접 추가
                    print("복사: Legacy 모드 - 직접 UI 추가")
                    new_item = self.addItem(item_data.get('Item', ''), -1, item_data)

                    if new_item:
                        # 3. 현재 범례 필터 상태에 따른 상태선 설정
                        parent_left_section = self._find_parent_left_section()
                        if parent_left_section and hasattr(parent_left_section, 'current_filter_states'):
                            filter_states = parent_left_section.current_filter_states
                            
                            # 핵심: 현재 사용자 설정에 따른 상태선 표시 
                            new_item.show_shortage_line = filter_states.get('shortage', False)
                            new_item.show_shipment_line = filter_states.get('shipment', False)
                            new_item.show_pre_assigned_line = filter_states.get('pre_assigned', False)
                            
                            print(f"[DEBUG] 현재 필터 상태 적용: shortage={new_item.show_shortage_line}, shipment={new_item.show_shipment_line}, pre_assigned={new_item.show_pre_assigned_line}")

                        # 상태 복원
                        if source_states['is_shortage']:
                            new_item.set_shortage_status(True, source_states['shortage_data'])
                        if source_states['is_pre_assigned']:
                            new_item.set_pre_assigned_status(True)
                        if source_states['is_shipment_failure']:
                            new_item.set_shipment_failure(True, source_states['shipment_failure_reason'])

                        # 복사본은 선택하지 않음
                        new_item.set_selected(False)
                        new_item.update_text_from_data()

                    # 복사 시그널 발생
                    self.itemCopied.emit(new_item, item_data)

                    event.acceptProposedAction()
                    return

            # 일반 드래그 처리 
            if isinstance(source, DraggableItemLabel):
                source_container = source.parent()

                if source_container == self:
                    # *** 같은 컨테이너 내 이동 ***
                    drop_index = self.findDropIndex(event.pos())
                    source_index = self.items.index(source)

                    if source_index < drop_index:
                        drop_index -= 1

                    if source_index == drop_index:
                        event.acceptProposedAction()
                        return

                    # 레이아웃 업데이트
                    self.layout.removeItem(self.spacer)
                    self.layout.removeWidget(source)
                    self.items.remove(source)
                    self.layout.insertWidget(drop_index, source)
                    self.items.insert(drop_index, source)
                    self.layout.addSpacerItem(self.spacer)

                    # 별도 처리 없음 - 기존 선택 상태 그대로 유지

                # 다른 컨테이너에서 이동 
                elif isinstance(source_container, ItemsContainer):
                    grid_widget = self.find_parent_grid_widget()
                    target_row, target_col = -1, -1

                    if grid_widget:
                        for row_idx, row in enumerate(grid_widget.containers):
                            if self in row:
                                target_row = row_idx
                                target_col = row.index(self)
                                break

                    # 아이템 데이터 처리
                    if item_data is None and hasattr(source, 'item_data'):
                        item_data = source.item_data.copy() if source.item_data else {}

                    # 새 위치 계산
                    if item_data and target_row >= 0 and target_col >= 0:
                        if (target_row < len(grid_widget.row_headers) and
                                '_(' in grid_widget.row_headers[target_row]):

                            line_part = grid_widget.row_headers[target_row].split('_(')[0]
                            shift_part = grid_widget.row_headers[target_row].split('_(')[1].rstrip(')')

                            item_data['Line'] = line_part
                            day_idx = target_col
                            is_day_shift = shift_part == "Day"
                            new_time = (day_idx * 2) + (1 if is_day_shift else 2)
                            item_data['Time'] = str(new_time)

                            # 검증 처리 
                            try:
                                validator = getattr(grid_widget, 'validator', None)
                                if validator:
                                    source_line = source.item_data.get('Line') if hasattr(source, 'item_data') else None
                                    source_time = source.item_data.get('Time') if hasattr(source, 'item_data') else None
                                    source_item_id = source.item_data.get('_id') if hasattr(source, 'item_data') else None

                                    valid, message = validator.validate_adjustment(
                                        line_part, new_time, item_data.get('Item', ''),
                                        item_data.get('Qty', 0), source_line, source_time,
                                        item_id=source_item_id
                                    )
                                    if not valid:
                                        item_data['_validation_failed'] = True
                                        item_data['_validation_message'] = message
                                        
                            except Exception as e:
                                print(f"드롭 검증 에러: {e}")

                    # 다른 컨테이너에서 이동할 때 항상 맨 마지막에 추가
                    new_item = self.addItem(item_text, -1, item_data)  # -1로 맨 마지막에 추가

                    if new_item:
                        # 일반 이동에서도 필터 상태 적용 
                        parent_left_section = self._find_parent_left_section()
                        if parent_left_section and hasattr(parent_left_section, 'current_filter_states'):
                            filter_states = parent_left_section.current_filter_states
                            
                            # 현재 사용자 설정에 따른 상태선 표시
                            new_item.show_shortage_line = filter_states.get('shortage', False)
                            new_item.show_shipment_line = filter_states.get('shipment', False)
                            new_item.show_pre_assigned_line = filter_states.get('pre_assigned', False)

                        # 상태 복원
                        if source_states['is_shortage']:
                            new_item.set_shortage_status(True, source_states['shortage_data'])
                        if source_states['is_pre_assigned']:
                            new_item.set_pre_assigned_status(True)
                        if source_states['is_shipment_failure']:
                            new_item.set_shipment_failure(True, source_states['shipment_failure_reason'])

                        new_item.update_text_from_data()

                        # 드래그앤드롭 시 자동 선택하지 않음 
                        # 기존 선택 상태가 있었던 경우에만 선택
                        if was_selected:
                            # 원본 아이템의 선택 상태를 해제하고 새 아이템을 선택
                            if hasattr(source, 'set_selected'):
                                source.set_selected(False)
                            new_item.set_selected(True)
                            self.on_item_selected(new_item)
                        else:
                            # 선택되지 않았던 아이템은 선택하지 않음
                            new_item.set_selected(False)

                        controller = self._find_controller()
                        if controller:
                            # 변경 필드 정보 생성
                            changed_fields = {}
                            if hasattr(source, 'item_data') and source.item_data:
                                if ('Line' in source.item_data and 'Line' in item_data and
                                        source.item_data.get('Line', '') != item_data.get('Line', '')):
                                    changed_fields['Line'] = {
                                        'from': source.item_data.get('Line', ''),
                                        'to': item_data.get('Line', '')
                                    }

                                if ('Time' in source.item_data and 'Time' in item_data and
                                        source.item_data.get('Time', '') != item_data.get('Time', '')):
                                    changed_fields['Time'] = {
                                        'from': source.item_data.get('Time', ''),
                                        'to': item_data.get('Time', '')
                                    }

                            # 검증 실패한 경우 에러 섹션에 표시
                            if item_data.get('_validation_failed'):
                                if controller and hasattr(controller, 'error_manager'):
                                    # 드롭 완료 후 에러 표시
                                    controller.error_manager.add_validation_error(
                                        item_data, 
                                        item_data.get('_validation_message', 'Validation failed')
                                    )

                            # 직접 Model 조작하지 않고 Controller에 시그널로만 알림
                            if changed_fields:
                                self.itemDataChanged.emit(new_item, item_data, changed_fields)

                    # 원본 삭제는 시그널 없이 수행
                    if source_container and hasattr(source_container, '_remove_item_without_signal'):
                        source_container._remove_item_without_signal(source)
                    else:
                        # 폴백: 기존 방식
                        source_container.remove_item(source)

            event.acceptProposedAction()

            # 최종 시그널 발생
            item_id = None
            if 'new_item' in locals() and new_item is not None:
                item_id = ItemKeyManager.extract_item_id(new_item)
            elif item_data is not None and '_id' in item_data:
                item_id = item_data.get('_id')

            self.itemsChanged.emit(item_id)
    
    """
    부모 위젯 체인에서 ModifiedLeftSection 찾기
    """
    def _find_parent_left_section(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'current_filter_states'):  # ModifiedLeftSection의 특징
                return parent
            parent = parent.parent()
        return None
            
    """
    부모 위젯 체인에서 Controller 찾기
    """
    def _find_controller(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'controller') and parent.controller:
                return parent.controller
            parent = parent.parent()
        return None

    """
    시그널 없이 아이템 제거 (드래그앤드롭 전용)
    """
    def _remove_item_without_signal(self, item):
        if item in self.items:
            # 선택 상태 해제
            if item == self.selected_item:
                self.selected_item = None

            # UI에서만 제거 (시그널 발생 안함)
            self.layout.removeWidget(item)
            self.items.remove(item)
            item.deleteLater()

    """
    시프트별 자재 부족 상태 업데이트
    """
    def update_item_shortage_status(self, item, shortage_dict):
        if not hasattr(item, 'item_data') or not item.item_data or 'Item' not in item.item_data:
            return
        
        item_code = item.item_data['Item']
        item_time = item.item_data.get('Time')
        
        # 해당 아이템이 부족 목록에 있는지 확인
        if item_code in shortage_dict:
            shortages_for_item = shortage_dict[item_code]
            matching_shortages = []
            
            # 시프트별 부족 정보 검사
            for shortage in shortages_for_item:
                shortage_shift = shortage.get('shift')
                
                # 시프트가 일치하는 경우만 처리
                if shortage_shift and item_time and int(shortage_shift) == int(item_time):
                    matching_shortages.append(shortage)
            
            # 일치하는 시프트의 부족 정보가 있으면 부족 상태로 설정
            if matching_shortages:
                item.set_shortage_status(True, matching_shortages)
                return True
        
        # 부족 상태가 아니거나 시프트가 일치하지 않으면 상태 해제
        item.set_shortage_status(False)
        return False


    """
    컨테이너 위젯 그리기 - 드롭 인디케이터 표시
    """
    def paintEvent(self, event):
        super().paintEvent(event)

        # 드롭 인디케이터 그리기
        if self.show_drop_indicator:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # 인디케이터 스타일 설정
            pen = QPen(QColor(0, 120, 215))  # 파란색
            pen.setWidth(2)
            painter.setPen(pen)

            # 특수값(-2)인 경우: 전체 컨테이너 인디케이터
            if self.drop_indicator_position == -2:
                # 컨테이너 전체에 테두리 그리기
                width = self.width() - 2
                height = self.height() - 2
                painter.drawRect(1, 1, width, height)
            else:
                # 기존 인디케이터 로직 (아이템 사이의 선)
                if self.drop_indicator_position >= 0:
                    # 인디케이터 위치 계산
                    if self.drop_indicator_position == 0:
                        # 첫 번째 위치
                        y = 2
                    elif self.drop_indicator_position >= len(self.items):
                        # 마지막 위치
                        if len(self.items) > 0:
                            last_item = self.items[-1]
                            y = last_item.geometry().bottom() + 2
                        else:
                            y = self.height() // 2
                    else:
                        # 중간 위치
                        item = self.items[self.drop_indicator_position]
                        y = item.geometry().top() - 2

                    # 선 그리기
                    width = self.width() - 4  # 양쪽 여백 2픽셀씩
                    painter.drawLine(2, y, width, y)

                    # 화살표 그리기 (양쪽에 작은 삼각형)
                    arrow_size = 5
                    painter.setBrush(QColor(0, 120, 215))

                    # 왼쪽 화살표
                    points_left = [
                        QPoint(2, y),
                        QPoint(2 + arrow_size, y - arrow_size),
                        QPoint(2 + arrow_size, y + arrow_size)
                    ]
                    painter.drawPolygon(points_left)

                    # 오른쪽 화살표
                    points_right = [
                        QPoint(width, y),
                        QPoint(width - arrow_size, y - arrow_size),
                        QPoint(width - arrow_size, y + arrow_size)
                    ]
                    painter.drawPolygon(points_right)

    def get_container_position(self, grid_widget):
        if not grid_widget or not hasattr(grid_widget, 'containers'):
            return -1, -1

        for row_idx, row in enumerate(grid_widget.containers):
            for col_idx, container in enumerate(row):
                if container == self:
                    return row_idx, col_idx
        return -1, -1

    """
    그리드 위치를 기반으로 Line과 Time 계산
    """
    def calculate_new_position(self, grid_widget, row_idx, col_idx):
        if not grid_widget or not hasattr(grid_widget, 'row_headers'):
            return None, None

        # 행 헤더에서 Line과 교대 정보 추출
        if row_idx < len(grid_widget.row_headers):
            row_key = grid_widget.row_headers[row_idx]
            if '_(' in row_key:
                line_part = row_key.split('_(')[0]
                shift_part = row_key.split('_(')[1].rstrip(')')

                # Time 계산
                is_day_shift = shift_part == "Night"
                new_time = (col_idx * 2) + (1 if is_day_shift else 2)

                return line_part, new_time

        return None, None

    """
    삭제 요청 처리 메서드
    """
    def on_item_delete_requested(self, item):
        print("DEBUG: ItemsContainer.on_item_delete_requested 호출됨")
        # EnhancedMessageBox를 사용하여 확인 다이얼로그 표시
        from app.views.components.common.enhanced_message_box import EnhancedMessageBox

        reply = EnhancedMessageBox.show_confirmation(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this item?"
        )

        # 확인한 경우에만 삭제 진행
        if reply:
            print("DEBUG: 사용자가 삭제 확인함")
            if item in self.items:
                # 아이템 ID 정보 추출 (삭제 시 전달)
                item_id = ItemKeyManager.extract_item_id(item)

                # 선택된 아이템을 삭제하는 경우 선택 상태 초기화
                if self.selected_item == item:
                    self.selected_item = None

                # 아이템 제거
                print("DEBUG: ItemsContainer에서 아이템 제거 시작")
                self.remove_item(item)
                print("DEBUG: ItemsContainer에서 아이템 제거 완료")

                # 변경 신호 발생
                print("DEBUG: itemsChanged 시그널 발생")
                self.itemsChanged.emit(item_id)

    """
    특정 아이템을 제외하고 다른 모든 아이템의 선택을 해제
    """
    def clear_selection_except(self, except_item):
        for item in self.items:
            if item != except_item and hasattr(item, 'set_selected'):
                if getattr(item, 'is_selected', False):
                    item.set_selected(False)

        # 다른 컨테이너의 선택도 해제하도록 그리드 위젯에 요청
        grid_widget = self.find_parent_grid_widget()
        if grid_widget and hasattr(grid_widget, 'clear_other_selections'):
            grid_widget.clear_other_selections(self, except_item)