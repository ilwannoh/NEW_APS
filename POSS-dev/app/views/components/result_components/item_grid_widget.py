from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from .items_container import ItemsContainer
from app.utils.item_key_manager import ItemKeyManager
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

"""
아이템 그리드 위젯 (테이블 대체)
"""
class ItemGridWidget(QWidget):
    itemSelected = pyqtSignal(object, object)  # 아이템 선택 시그널 추가 (선택된 아이템, 컨테이너)
    itemDataChanged = pyqtSignal(object, dict, dict)  # 아이템 데이터 변경 시그널 추가 (아이템, 새 데이터, 변경 필드 정보)
    itemCreated = pyqtSignal(object)
    itemRemoved = pyqtSignal(object)
    itemCopied = pyqtSignal(object, dict) # 아이템 복사 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        bold_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        normal_font = font_manager.get_just_font("SamsungOne-700").family()

        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)

        # 스크롤 영역 설정
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(w(3))

        self.main_layout.addWidget(self.scroll_area)

        # 컨테이너 위젯 저장용 배열
        self.containers = []

        # 현재 선택된 아이템 정보
        self.current_selected_container = None
        self.current_selected_item = None

        # 행 헤더와 열 헤더 저장
        self.row_headers = []
        self.column_headers = []

        # 라인별 행 그룹 정보 저장
        self.line_row_groups = {}  # 라인명 -> [시작 행 인덱스, 끝 행 인덱스]
        self.row_line_mapping = {}  # 행 인덱스 -> 라인명

    """
    그리드 초기화

    매개변수:
    - rows: 행 수
    - columns: 열 수
    - row_headers: 행 헤더 리스트 (형식: "Line_(교대)")
    - column_headers: 열 헤더 리스트
    - line_shifts: 라인별 교대 정보 (형식: {"라인명": ["주간", "야간"]})
    """
    def setupGrid(self, rows, columns, row_headers=None, column_headers=None, line_shifts=None):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        self.containers = []
        self.line_row_groups = {}
        self.row_line_mapping = {}

        # 헤더 정보 저장
        self.row_headers = row_headers if row_headers else []
        self.column_headers = column_headers if column_headers else []

        # 선택 상태 초기화
        self.current_selected_container = None
        self.current_selected_item = None

        # 열 확장 정책 설정
        self.grid_layout.setColumnStretch(0, 0)  # 라인 열
        self.grid_layout.setColumnStretch(1, 0)  # 교대 열

        # 열 헤더 추가
        if column_headers:
            # 빈 헤더 셀 (첫 번째 행, 첫 번째 열 - 라인 헤더 위)
            empty_header1 = QLabel("")
            empty_header1.setStyleSheet("background-color: transparent; ")
            empty_header1.setFixedWidth(w(60))
            self.grid_layout.addWidget(empty_header1, 0, 0)

            # 빈 헤더 셀 (첫 번째 행, 두 번째 열 - 교대 헤더 위)
            empty_header2 = QLabel("")
            empty_header2.setStyleSheet(f"background-color: transparent;")
            empty_header2.setFixedWidth(w(60))
            self.grid_layout.addWidget(empty_header2, 0, 1)

            # 요일 넣는 곳
            for col, header in enumerate(column_headers):
                label = QLabel(header)
                label.setStyleSheet(
                    f"font-weight: bold; padding: 5px; background-color: #F0F0F0; border: 1px solid #cccccc; margin-left: 2.5px")
                label.setAlignment(Qt.AlignCenter)
                # 데이터 열은 2부터 시작 (0: 라인 헤더, 1: 교대 헤더)
                self.grid_layout.addWidget(label, 0, col + 2)
                # 데이터 열에만 확장 정책 적용
                self.grid_layout.setColumnStretch(col + 2, 1)

            # 헤더 행은 크기 고정 
            self.grid_layout.setRowStretch(0, 0)

        # 라인별 교대 정보가 있는 경우 행 헤더 설정
        if line_shifts:
            row_index = 1  # 실제 행 인덱스

            for line, shifts in line_shifts.items():
                # 라인 헤더 (첫 번째 열, 셀 병합)
                start_row = row_index
                line_label = QLabel(line)
                line_label.setStyleSheet(f"""
                    font-weight: bold; 
                    padding: 5px; 
                    background-color: #1428A0;
                    color: white;
                    border: 1px solid #0C1A6B;
                    border-radius: 0px;
                    font-family: {font_manager.get_just_font("SamsungSharpSans-Bold").family()};
                """)
                line_label.setAlignment(Qt.AlignCenter)
                line_label.setFixedWidth(w(60))

                # 교대 수에 따라 행 구성
                shift_rows = []

                for shift in shifts:
                    # 교대 레이블 추가
                    shift_label = QLabel(shift)

                    # 주간/야간에 따라 스타일 다르게 적용
                    if shift == "Day":
                        shift_style = f"""
                            padding: 5px; 
                            background-color: #F8F8F8;
                            border: 1px solid #D9D9D9;
                            font-weight: bold;
                            font-family: {font_manager.get_just_font("SamsungSharpSans-Bold").family()};
                        """

                    else:  # 야간
                        shift_style = f"""
                            padding: 5px; 
                            background-color: #F0F0F0;
                            border: 1px solid #D9D9D9;
                            color: #666666;
                            font-weight: bold;
                            font-family: {font_manager.get_just_font("SamsungSharpSans-Bold").family()};
                        """
                        # Night 위에 생기는 선
                        separator = QFrame()
                        separator.setFrameShape(QFrame.HLine)
                        separator.setLineWidth(1)
                        separator.setFixedHeight(1)
                        separator.setStyleSheet("background-color: #cccccc")  # 파란색 구분선
                        self.grid_layout.addWidget(separator, row_index, 1, 1, columns + 1)  # 행 전체에 걸쳐 구분선 추가

                        # ===== 구분선 행도 크기 고정 =====
                        self.grid_layout.setRowStretch(row_index, 0)

                        row_index += 1

                    shift_label.setStyleSheet(shift_style)
                    shift_label.setAlignment(Qt.AlignCenter)
                    shift_label.setFixedWidth(w(60))

                    # 교대 레이블을 두 번째 열에 배치
                    self.grid_layout.addWidget(shift_label, row_index, 1)

                    # 행 키 생성 및 저장
                    row_key = f"{line}_({shift})"

                    if row_key not in self.row_headers:
                        self.row_headers.append(row_key)

                    # 라인-행 매핑 저장
                    self.row_line_mapping[row_index] = line

                    # ===== 핵심 수정: 각 데이터 행의 크기를 최소로 제한 =====
                    self.grid_layout.setRowStretch(row_index, 0)

                    # 각 셀에 아이템 컨테이너 추가
                    row_containers = []

                    for col in range(columns):
                        container = ItemsContainer()
                        container.setMinimumHeight(h(60))
                        container.setMinimumWidth(w(214))  # 요일 너비
                        container.setStyleSheet("border: 1px solid #D9D9D9; background-color: white;")

                        # 아이템 선택 이벤트 연결
                        container.itemSelected.connect(self.on_item_selected)

                        # 아이템 데이터 변경 이벤트 연결
                        container.itemDataChanged.connect(self.on_item_data_changed)

                        # 아이템 복사 이벤트 연결
                        container.itemCopied.connect(self.on_item_copied)

                        for item in container.items:
                            if hasattr(item, 'itemDeleteRequested'):
                                item.itemDeleteRequested.connect(
                                    lambda item_obj=item: self.on_item_delete_requested(item_obj, container)
                                )

                        # 컨테이너를 데이터 열에 배치
                        self.grid_layout.addWidget(container, row_index, col + 2)
                        row_containers.append(container)

                    self.containers.append(row_containers)
                    shift_rows.append(row_index)
                    row_index += 1

                # 라인 레이블 세로 병합
                end_row = row_index - 1
                self.line_row_groups[line] = [start_row, end_row]

                if len(shifts) > 1:  # 교대가 2개 이상일 때만 병합
                    # 라인 레이블을 첫 번째 열(인덱스 0)에 배치하고 세로 병합
                    self.grid_layout.addWidget(line_label, start_row, 0, end_row - start_row + 1, 1)
                else:
                    # 교대가 하나뿐이면 병합 필요 없음
                    self.grid_layout.addWidget(line_label, start_row, 0)

                # Night와 다음 Day를 구분하는 선
                spacer = QFrame()
                spacer.setMinimumHeight(10)  # 라인 간 간격 높이 설정
                spacer.setMaximumHeight(10)  # ===== 최대 높이도 제한 =====
                spacer.setStyleSheet("background-color: #F5F5F5;")  # 간격 배경색
                self.grid_layout.addWidget(spacer, row_index, 0, 1, columns + 2)  # 모든 열에 걸쳐 추가

                # ===== 스페이서 행도 크기 고정 =====
                self.grid_layout.setRowStretch(row_index, 0)

                row_index += 1  # 간격 위젯 후 행 인덱스 증가

            # ===== 마지막에 확장 가능한 빈 공간 추가 =====
            final_spacer = QFrame()
            final_spacer.setStyleSheet("background-color: transparent;")
            self.grid_layout.addWidget(final_spacer, row_index, 0, 1, columns + 2)
            self.grid_layout.setRowStretch(row_index, 1)  # 이 행만 확장되어 남은 공간 차지

        else:
            for row in range(rows):
                row_containers = []

                # 행 헤더 추가 (있는 경우)
                if row_headers and row < len(row_headers):
                    label = QLabel(row_headers[row])
                    label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #F0F0F0;")
                    label.setAlignment(Qt.AlignCenter)
                    label.setFixedWidth(120)
                    self.grid_layout.addWidget(label, row + 1, 0)

                # ===== 각 데이터 행의 크기를 최소로 제한 =====
                self.grid_layout.setRowStretch(row + 1, 0)

                # 각 셀에 아이템 컨테이너 추가
                for col in range(columns):
                    container = ItemsContainer()
                    container.setMinimumHeight(h(60))
                    container.setMinimumWidth(w(221))
                    container.setStyleSheet("border: 1px solid #D9D9D9; background-color: white;")

                    # 아이템 선택 이벤트 연결
                    container.itemSelected.connect(self.on_item_selected)

                    # 아이템 데이터 변경 이벤트 연결
                    container.itemDataChanged.connect(self.on_item_data_changed)

                    # 아이템 복사 이벤트 연결
                    container.itemCopied.connect(self.on_item_copied)

                    # 기존 방식에서는 데이터 열이 인덱스 1부터 시작
                    self.grid_layout.addWidget(container, row + 1, col + 1)
                    row_containers.append(container)

                self.containers.append(row_containers)

            # ===== 기존 방식에도 확장 가능한 빈 공간 추가 =====
            final_spacer = QFrame()
            final_spacer.setStyleSheet("background-color: transparent;")
            self.grid_layout.addWidget(final_spacer, rows + 1, 0, 1, columns + 1)
            self.grid_layout.setRowStretch(rows + 1, 1)  # 이 행만 확장되어 남은 공간 차지

    """
    컨테이너에서 아이템이 선택되었을 때 호출되는 핸들러
    """

    def on_item_selected(self, selected_item, container):
        """컨테이너에서 아이템이 선택되었을 때 호출되는 핸들러 - 수정"""

        # *** 수정: 다른 모든 컨테이너의 선택 해제 ***
        for row in self.containers:
            for other_container in row:
                if other_container != container:
                    # 다른 컨테이너의 선택 해제
                    if hasattr(other_container, 'clear_selection'):
                        other_container.clear_selection()

        # 현재 선택된 컨테이너와 아이템 업데이트
        self.current_selected_container = container
        self.current_selected_item = selected_item

        # 상위 위젯에 아이템 선택 이벤트 전달
        self.itemSelected.emit(selected_item, container)

    """
    아이템 데이터가 변경되었을 때 호출되는 핸들러
    """
    def on_item_data_changed(self, item, new_data, changed_fields=None):
        # 상위 위젯에 데이터 변경 이벤트 전달
        self.itemDataChanged.emit(item, new_data, changed_fields)

    """
    특정 위치에 아이템 추가

    매개변수:
    - row: 행 인덱스
    - col: 열 인덱스
    - item_text: 표시할 텍스트
    - item_data: 아이템 관련 데이터 (툴팁에 표시할 전체 정보)
    """
    def addItemAt(self, row, col, item_text, item_data=None, index=-1):
        if 0 <= row < len(self.containers) and 0 <= col < len(self.containers[row]):
            if item_data and '_drop_pos_x' in item_data:
                item_data.pop('_drop_pos_x', None)
                item_data.pop('_drop_pos_y', None)
            new_item = self.containers[row][col].addItem(item_text, index, item_data)

            if new_item :
                self.itemCreated.emit(new_item)

            return new_item
        return None

    """
    모든 아이템 삭제
    """
    def clearAllItems(self):
        self.current_selected_container = None
        self.current_selected_item = None

        for row in self.containers:
            for container in row:
                container.clear_items()

    """
    모든 컨테이너의 선택 상태 초기화
    """
    def clear_all_selections(self):
        for row in self.containers:
            for container in row:
                container.clear_selection()

        self.current_selected_container = None
        self.current_selected_item = None

    """
    행 인덱스에 해당하는 라인명 반환
    """
    def get_line_from_row(self, row_index):
        return self.row_line_mapping.get(row_index)

    """
    검증기 설정
    """
    def set_validator(self, validator):
        self.validator = validator

    """
    컨테이너의 상태 업데이트
    """
    def update_container_visibility(self) :
        pass


    """
    검색 후 선택된 항목이 보이도록 스크롤 이동
    """

    def ensure_item_visible(self, container, item):
        """아이템이 보이도록 스크롤 위치 조정"""
        if not container or not item:
            return

        try:
            # 스크롤 영역 확인
            if not hasattr(self, 'scroll_area'):
                print("스크롤 영역이 없음")
                return

            # 컨테이너 위치 계산
            container_pos = container.mapTo(self.scroll_content, QPoint(0, 0))

            # 아이템 위치 계산
            item_pos = item.pos()

            # 최종 타겟 위치 계산
            target_y = container_pos.y() + item_pos.y()

            # 스크롤바 이동
            v_bar = self.scroll_area.verticalScrollBar()

            # 아이템이 화면 중앙에 오도록 스크롤
            viewport_height = self.scroll_area.viewport().height()
            target_y = max(0, target_y - (viewport_height // 2) + (item.height() // 2))

            # 스크롤 위치 설정
            v_bar.setValue(target_y)

        except Exception as e:
            print(f"아이템 스크롤 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()

    """
    컨테이너 가시성 업데이트
    """
    def container_visibility(self):
        for row_containers in self.containers:
            for container in row_containers:
                if hasattr(container, 'update_visibility'):
                    container.update_visibility()
                elif hasattr(container, 'adjustSize'):
                    container.adjustSize()

    """
    아이템 삭제 메서드
    """
    def on_item_delete_requested(self, item, container):
        print(f"DEBUG: ItemGridWidget.on_item_delete_requested 호출됨")
        if container:
            # 아이템 ID 추출
            item_id = ItemKeyManager.extract_item_id(item)

            # 아이템 정보 백업 (참조 유지를 위해)
            item_data = None
            if hasattr(item, 'item_data') and item.item_data:
                item_data = item.item_data.copy()
                print(f"DEBUG: 삭제 아이템 정보: {item_data.get('Item')} @ {item_data.get('Line')}-{item_data.get('Time')}, ID: {item_id}")

            # 컨테이너에서 아이템 제거
            container.remove_item(item)
            print(f"DEBUG: 삭제 처리를 Container에 위임 완료")

            # print(f"DEBUG: itemRemoved 시그널 발생(item_grid)")
            # if item_id:
            #     # ID가 있는 경우 ID만 전달
            #     self.itemRemoved.emit(item_id)
            # else:
            #     # ID가 없는 경우 아이템 객체 전달 (폴백)
            #     self.itemRemoved.emit(item)
        else:
            print(f"DEBUG: 아이템이 속한 컨테이너를 찾을 수 없음")

    """
    아이템 복사 이벤트 처리
    """
    def on_item_copied(self, item, data):
        # 상위 위젯에 복사 이벤트 전달
        self.itemCopied.emit(item, data)

    def clear_other_selections(self, current_container, except_item):
        """특정 컨테이너와 아이템을 제외하고 다른 모든 선택을 해제"""
        for row in self.containers:
            for container in row:
                if container != current_container:
                    # 다른 컨테이너의 모든 아이템 선택 해제
                    if hasattr(container, 'clear_selection'):
                        container.clear_selection()