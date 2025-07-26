from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt5.QtGui import QCursor
import pandas as pd
from .item_grid_widget import ItemGridWidget
from .item_position_manager import ItemPositionManager
from app.views.components.common.enhanced_message_box import EnhancedMessageBox
from .legend_widget import LegendWidget
from .filter_widget import FilterWidget
from .search_widget import SearchWidget
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

from .manager.data_manager import DataManager
from .manager.filter_manager import FilterManager
from .manager.search_manager import SearchManager

class ModifiedLeftSection(QWidget):
    item_selected = pyqtSignal(object, object)
    itemModified = pyqtSignal(object, dict, dict)
    cellMoved = pyqtSignal(object, dict, dict)
    validation_error_occured = pyqtSignal(dict, str)
    validation_error_resolved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = None
        self.data = None
        self.original_data = None
        self.grouped_data = None
        self.days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        self.time_periods = ['Day', 'Night']
        self.pre_assigned_items = set()  # 사전할당된 아이템 저장
        self.shipment_failure_items = {}  # 출하 실패 아이템 저장

        # MVC 모드 추적
        self.controller = None
        self._mvc_mode = False

        # 매니저들 초기화 (순서 중요)
        self.search_manager = SearchManager(self)
        self.data_manager = DataManager(self) 
        self.filter_manager = FilterManager(self)

        self.init_ui()

        # 매니저 간 시그널 연결
        self._connect_manager_signals()

        # MVC 컴포넌트 초기화
        self.controller = None
        self.validator = None

        # 아이템 이동을 위한 정보 저장
        self.row_headers = []

        # 검색 관련 변수
        self.all_items = []
        self.search_results = []
        self.current_result_index = -1

        if not hasattr(self, 'current_selected_item'):
            self.current_selected_item = None
        if not hasattr(self, 'current_selected_container'):
            self.current_selected_container = None

        # 필터 상태 저장 
        self.current_filter_states = {
            'shortage': False,
            'shipment': False,  
            'pre_assigned': False
        }

        # 엑셀 스타일 필터 상태 저장 (새로 추가된 부분)
        self.current_excel_filter_states = {
            'line': {},
            'project': {}
        }

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 범례 위젯 추가
        self.legend_widget = LegendWidget()
        self.legend_widget.filter_changed.connect(self.on_filter_changed_dict)
        self.legend_widget.filter_activation_requested.connect(self.on_filter_activation_requested)
        main_layout.addWidget(self.legend_widget)

        # 통합 컨트롤 레이아웃 (버튼, 필터, 검색 섹션을 한 줄에 배치)
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(5, 5, 5, 5)
        control_layout.setSpacing(w(5))

        # 왼쪽 버튼 섹션 (Import/Reset)
        button_section = QHBoxLayout()
        button_section.setSpacing(10)

        bold_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        normal_font = font_manager.get_just_font("SamsungOne-700").family()

        # 엑셀 파일 불러오기 버튼 - 길이 증가
        self.load_button = QPushButton("Import Excel")
        self.load_button.setStyleSheet(f"""
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
        self.load_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.load_button.clicked.connect(self.load_excel_file)
        button_section.addWidget(self.load_button)

        # 원본 복원 버튼 
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet(f"""
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
        self.reset_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.reset_button.clicked.connect(self.reset_to_original)
        self.reset_button.setEnabled(False)
        button_section.addWidget(self.reset_button)

        # 버튼 섹션을 통합 레이아웃에 추가 (왼쪽에 붙이기)
        control_layout.addLayout(button_section)
        
        # 가운데 여백 추가
        control_layout.addStretch(1)  # 가운데 여백 추가

        # 필터 위젯 추가 - Line과 Project 버튼 간격 조정 및 스타일 변경
        self.filter_widget = FilterWidget()
        self.filter_widget.filter_changed.connect(self.on_excel_filter_changed)
        control_layout.addWidget(self.filter_widget)
        control_layout.addStretch(1)

        # 검색 위젯 추가 (기존 검색 관련 UI 요소 대체)
        self.search_widget = SearchWidget(self)
        self.search_widget.searchRequested.connect(self.search_manager.search_items)
        self.search_widget.searchCleared.connect(self.search_manager.clear_search)
        self.search_widget.nextResultRequested.connect(self.search_manager.go_to_next_result)
        self.search_widget.prevResultRequested.connect(self.search_manager.go_to_prev_result)
        control_layout.addWidget(self.search_widget)

        # 통합 컨트롤 레이아웃을 메인 레이아웃에 추가
        main_layout.addLayout(control_layout)

        # 새로운 그리드 위젯 추가
        self.grid_widget = ItemGridWidget()
        self.grid_widget.scroll_area.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #CCCCCC;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.grid_widget.itemSelected.connect(self.on_grid_item_selected)  # 아이템 선택 이벤트 연결
        self.grid_widget.itemDataChanged.connect(self.data_manager.on_item_data_changed)  # 아이템 데이터 변경 이벤트 연결
        self.grid_widget.itemCreated.connect(self.data_manager.register_item)
        self.grid_widget.itemRemoved.connect(self.data_manager.on_item_removed)
        self.grid_widget.itemCopied.connect(self.data_manager.on_item_copied)  # 아이템 복사 이벤트 연결
        main_layout.addWidget(self.grid_widget, 1)

    """
    컨트롤러 설정 - MVC 모드 활성화
    """
    def set_controller(self, controller):
        self.controller = controller
        self._mvc_mode = True
        print("ModifiedLeftSection: MVC 모드 활성화")

    """
    검증기 설정
    """
    def set_validator(self, validator):
        self.validator = validator
        if hasattr(self.grid_widget, 'set_validator'):
            self.grid_widget.set_validator(validator)
        print("ModifiedLeftSection: 검증기 설정 완료")

    """
    매니저들 간의 시그널 연결
    """
    def _connect_manager_signals(self):
        # FilterManager의 필터 적용 완료 시그널을 SearchManager에 연결
        if hasattr(self.filter_manager, 'filter_applied'):
            self.filter_manager.filter_applied.connect(self.search_manager.reapply_search_if_active)

        # 범례 위젯을 직접 FilterManager에 연결 
        self.legend_widget.filter_changed.connect(self.filter_manager.apply_legend_filters)
        print("[LeftSection] 매니저 시그널 연결 완료")

    """
    초기화 - 분석 결과와 함께 (MVC 전용)
    """
    def initialize_with_data(self, df, analysis_results):
        self.data = df
        self.original_data = df.copy()
        
        # UI 구성 : 아이템 생성
        self.update_ui_with_signals()

    """
    UI만 업데이트 - 분석 없음 (MVC 전용)
    """
    def update_ui_only(self, df, analysis_results):
        # 스크롤 위치 저장
        scroll_position = self._save_scroll_position()
        
        # 데이터 설정
        self.data = df
        
        # UI 업데이트 (시그널 억제) : 아이템 재생성
        self.update_ui_with_signals()
        self.apply_all_filters()
        
        # 분석 결과 적용 (재분석 없음)
        # self.apply_analysis_results(analysis_results)
        
        # 스크롤 위치 복원
        if scroll_position:
            QTimer.singleShot(100, lambda: self._restore_scroll_position(scroll_position))
        
    """
    데이터프레임 타입 정규화
    """
    def _normalize_data_types(self, df):
        if df is not None and not df.empty:
            # Line은 항상 문자열
            if 'Line' in df.columns:
                df['Line'] = df['Line'].astype(str)
            
            # Time은 항상 정수
            if 'Time' in df.columns:
                df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0).astype(int)
            
            # Item은 항상 문자열
            if 'Item' in df.columns:
                df['Item'] = df['Item'].astype(str)
            
            # Qty는 항상 정수
            if 'Qty' in df.columns:
                df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        
        return df
    

    """
    새로 생성된 아이템 등록
    """
    def register_item(self, item) :
        if item not in self.all_items :
            self.all_items.append(item)

            # 검색이 활성화되어 있으면 해당 아이템에 검색 적용
            if self.search_widget.is_search_active():
                search_text = self.search_widget.get_search_text()
                if search_text:
                    self.data_manager.apply_search_to_item(item, search_text)

    """
    아이템의 상태선 업데이트 
    - FilterManager로 위임
    """
    def update_item_status_line_visibility(self, item):
        return self.filter_manager.update_item_status_line_visibility(item)

    """
    엑셀 스타일 필터 상태 변경 처리
    - 매니저 위임
    """
    def on_excel_filter_changed(self, filter_states):
        print(f"[LeftSection] 엑셀 필터 변경: {filter_states}")
        self.current_excel_filter_states = filter_states
        self.filter_manager.apply_filters(filter_states)

    """
    모든 필터 (범례 & 엑셀 스타일) 적용
    - 매니저 위임
    """
    def apply_all_filters(self):
        excel_filter_active = (
        any(self.current_excel_filter_states.get('line', {}).values()) or 
        any(self.current_excel_filter_states.get('project', {}).values())
        )
        
        if excel_filter_active:
            # print("→ Step 1: 엑셀 필터 적용 (그리드 재구성)")
            self.filter_manager.apply_filters(self.current_excel_filter_states)
        else:
            print("→ Step 1: 엑셀 필터 비활성화, 그리드 재구성 스킵")

        # print("→ Step 2: 범례 필터 적용")
        self.filter_manager._apply_legend_filters_only()

        # 검색이 활성화된 경우 검색 재적용
        if hasattr(self, 'search_widget') and self.search_widget.is_search_active():
            search_text = self.search_widget.get_search_text()
            print(f"→ Step 3: 검색 필터 적용 - 검색어: {search_text}")
            if search_text:
                # SearchManager 사용
                self.search_manager.search_items(search_text)

    """
    활성화된 라인과 프로젝트로 그리드 재구성
    - 매니저 위임
    """
    def rebuild_grid_with_filtered_data(self, active_lines, active_projects=None):
        return self.filter_manager._rebuild_grid_with_filtered_data(active_lines, active_projects)

    """
    빈 그리드 표시 - Clear All 했을 때 사용
    - 매니저 위임
    """
    def show_empty_grid(self):
        return self.filter_manager._show_empty_grid()
    
    """
    범례 위젯에서 필터가 변경될 때 호출 - MVC 모드 고려
    """
    def on_filter_changed_dict(self, filter_states):
        if self.current_filter_states == filter_states:
            return
        
        self.current_filter_states = filter_states
        self.filter_manager.apply_legend_filters(filter_states)

    """
    상태 필터에 따른 아이템 표시 여부 결정 
    """
    def should_show_item_legend_filter(self, item):
        # 모든 필터가 꺼져 있으면 모든 아이템 표시
        if not any(self.current_filter_states.values()):
            return True
        
        # 각 상태 확인
        shortage_filter = self.current_filter_states.get('shortage', False)
        shipment_filter = self.current_filter_states.get('shipment', False)
        pre_assigned_filter = self.current_filter_states.get('pre_assigned', False)
        
        # 아이템 상태 확인
        is_shortage = hasattr(item, 'is_shortage') and item.is_shortage
        is_shipment = hasattr(item, 'is_shipment_failure') and item.is_shipment_failure
        is_pre_assigned = hasattr(item, 'is_pre_assigned') and item.is_pre_assigned
        
        # 필터 적용
        if shortage_filter and not is_shortage:
            return False
        if shipment_filter and not is_shipment:
            return False
        if pre_assigned_filter and not is_pre_assigned:
            return False
        
        return True
                
    """
    상태 필터 활성화 요청 처리
    """
    def on_filter_activation_requested(self, status_type):
        # 필터 상태 업데이트 후 필터 적용
        self.current_filter_states[status_type] = True
        print(f"필터 활성화: {status_type}")
    
    """
    데이터 로드 후 필터 데이터 업데이트
    """
    def update_filter_data(self):
        """
        데이터 로드 후 필터 데이터 업데이트 (Project 컬럼 처리 개선)
        """
        if self.data is None:
            return

        try:
            # 라인 정렬 (기존 로직과 동일)
            temp_data = self.data.copy()
            temp_data['Building'] = temp_data['Line'].str[0]
            building_production = temp_data.groupby('Building')['Qty'].sum()
            sorted_buildings = building_production.sort_values(ascending=False).index.tolist()

            all_lines = temp_data['Line'].unique()
            lines = []
            for building in sorted_buildings:
                building_lines = [line for line in all_lines if line.startswith(building)]
                sorted_building_lines = sorted(building_lines)
                lines.extend(sorted_building_lines)

            remaining_lines = [line for line in all_lines if line not in lines]
            if remaining_lines:
                lines.extend(sorted(remaining_lines))

            # *** 프로젝트 목록 추출 개선 ***
            projects = []
            if 'Project' in self.data.columns:
                unique_projects = self.data['Project'].unique()

                for project in unique_projects:
                    if pd.isna(project):
                        projects.append("N/A")  # NaN 값을 "N/A"로 처리
                    else:
                        projects.append(str(project))

                projects = sorted(set(projects))  # 중복 제거하고 정렬
            else:
                print("DEBUG: Project 컬럼이 데이터에 없습니다")

            # 필터 위젯에 데이터 설정
            self.filter_widget.set_filter_data(lines, projects)

        except Exception as e:
            print(f"필터 데이터 업데이트 중 오류: {e}")
            import traceback
            traceback.print_exc()

    """
    현재 필터 상태에 따라 아이템 가시성 조정 - 원본에 있던 메서드
    """
    def apply_visibility_filter(self):
        if not hasattr(self, 'grid_widget') or not hasattr(self.grid_widget, 'containers'):
            return
        
        self.apply_all_filters()

    """
    컨테이너 가시성 업데이트 - 원본에 있던 메서드
    """
    def container_visibility(self):
        for row_containers in self.grid_widget.containers:
            for container in row_containers:
                if hasattr(container, 'update_visibility'):
                    container.update_visibility()
                elif hasattr(container, 'adjustSize'):
                    container.adjustSize()
    
    """
    아이템이 검색어와 일치하는지 확인 
    """
    def is_search_match(self, item, search_text):
        if not item or not hasattr(item, 'item_data') or not item.item_data:
            return False
        
        try:
            item_code = str(item.item_data.get('Item', '')).lower()
            return search_text in item_code
        except:
            return False

    """
    그리드에서 아이템이 선택되면 호출되는 함수
    """
    def on_grid_item_selected(self, selected_item, container):
        # 현재 선택 상태 저장
        self.current_selected_item = selected_item
        self.current_selected_container = container

        # 선택 시그널 방출
        self.item_selected.emit(selected_item, container)

    def search_items_without_clear(self):
        search_text = self.search_widget.get_search_text()
        if not search_text:
            return

        # 현재 선택된 아이템 저장
        current_selected_item = self.current_selected_item

        # 검색 결과를 행 우선으로 정렬하기 위한 임시 리스트
        row_ordered_results = []
        invalid_items = []

        # 행 우선 순서로 아이템 수집
        if hasattr(self.grid_widget, 'containers'):
            for row_idx, row_containers in enumerate(self.grid_widget.containers):
                for col_idx, container in enumerate(row_containers):
                    for item in container.items:
                        try:
                            # 검색 조건 확인
                            if hasattr(item, 'item_data') and item.item_data:
                                item_code = str(item.item_data.get('Item', '')).lower()
                                is_match = search_text in item_code

                                if is_match:
                                    # 행과 열 정보와 함께 저장 (행 우선 정렬용)
                                    row_ordered_results.append({
                                        'item': item,
                                        'row': row_idx,
                                        'col': col_idx
                                    })

                                # 검색 포커스 설정
                                self.data_manager.apply_search_to_item(item, search_text)

                        except RuntimeError:
                            invalid_items.append(item)
                        except Exception as e:
                            print(f"검색 중 오류 발생: {e}")

        # 잘못된 아이템 제거
        for item in invalid_items:
            if item in self.all_items:
                self.all_items.remove(item)

        # 행 우선 정렬 (row -> col 순서) 
        row_ordered_results.sort(key=lambda x: (x['row'], x['col']))

        # 정렬된 순서로 검색 결과 저장
        self.search_results = [result['item'] for result in row_ordered_results]

        # 모든 필터 적용 (검색 결과 포함)
        self.apply_all_filters()

        # 검색 결과 UI 업데이트
        self.search_widget.show_result_navigation(True)

        # 검색 결과가 있으면 선택 및 네비게이션 업데이트
        if self.search_results:
            # 이전에 선택된 아이템이 검색 결과에 있으면 선택 유지
            if current_selected_item in self.search_results:
                self.current_result_index = self.search_results.index(current_selected_item)
            else:
                self.current_result_index = 0

            self.search_manager.select_current_result()
            self.search_manager.update_result_navigation()
        else:
            # 검색 결과 없음 표시
            self.search_widget.set_result_status(0, 0)

    """
    위치 변경 처리 로직 분리
    """
    def _handle_position_change(self, item, new_data, changed_fields, old_data):
        position_change_needed = False

        if changed_fields:
            if 'Time' in changed_fields:
                position_change_needed = True
                time_change = changed_fields['Time']
                old_time = time_change['from']
                new_time = time_change['to']

            if 'Line' in changed_fields:
                position_change_needed = True
                line_change = changed_fields['Line']
                old_line = line_change['from']
                new_line = line_change['to']

        if position_change_needed:
            # 위치 변경 로직 (기존 코드 유지)
            self._process_position_change(item, new_data, changed_fields, old_data)
        else:
            # 데이터만 업데이트
            if hasattr(item, 'update_item_data'):
                success, error_message = item.update_item_data(new_data)
                if not success:
                    print(f"아이템 데이터 업데이트 실패: {error_message}")
                    return

            self.data_manager.mark_as_modified()
            self.itemModified.emit(item, new_data)

    """
    위치 변경 처리 (기존 로직 유지)
    """
    def _process_position_change(self, item, new_data, changed_fields, old_data):
        old_container = item.parent() if hasattr(item, 'parent') else None
        
        if not isinstance(old_container, QWidget):
            return

        # 변경된 Line과 Time에 따른 새 위치 계산
        line = new_data.get('Line')
        new_time = new_data.get('Time')

        if not line or not new_time:
            return

        # 위치 계산 로직 (기존 코드 유지)
        old_time = changed_fields.get('Time', {}).get('from', new_time) if changed_fields else new_time
        old_line = changed_fields.get('Line', {}).get('from', line) if changed_fields else line

        old_day_idx, old_shift = ItemPositionManager.get_day_and_shift(old_time)
        new_day_idx, new_shift = ItemPositionManager.get_day_and_shift(new_time)

        old_row_key = ItemPositionManager.get_row_key(old_line, old_shift)
        new_row_key = ItemPositionManager.get_row_key(line, new_shift)

        old_row_idx = ItemPositionManager.find_row_index(old_row_key, self.row_headers)
        new_row_idx = ItemPositionManager.find_row_index(new_row_key, self.row_headers)

        old_col_idx = ItemPositionManager.get_col_from_day_idx(old_day_idx, self.days)
        new_col_idx = ItemPositionManager.get_col_from_day_idx(new_day_idx, self.days)

        # 유효한 인덱스인 경우 아이템 이동
        if old_row_idx >= 0 and old_col_idx >= 0 and new_row_idx >= 0 and new_col_idx >= 0:
            # 이전 위치에서 아이템 제거
            if old_container:
                old_container.remove_item(item)

            # 새 위치에 아이템 추가
            item_text = str(new_data.get('Item', ''))
            if 'Qty' in new_data and pd.notna(new_data['Qty']):
                item_text += f"    {new_data['Qty']}"

            # 드롭 위치 정보 처리
            drop_index = 0
            if changed_fields and '_drop_pos' in changed_fields:
                try:
                    drop_pos_info = changed_fields['_drop_pos']
                    x = int(drop_pos_info['x'])
                    y = int(drop_pos_info['y'])
                    target_container = self.grid_widget.containers[new_row_idx][new_col_idx]
                    drop_index = target_container.findDropIndex(QPoint(x, y))
                except Exception as e:
                    drop_index = 0

            # 새 위치에 아이템 추가
            new_item = self.grid_widget.addItemAt(new_row_idx, new_col_idx, item_text, new_data, drop_index)

            if new_item:
                self.data_manager.mark_as_modified()
                
                # 아이템 상태 복원
                self._restore_item_states(new_item, new_data)
                
                # 셀 이동 이벤트 발생
                self.cellMoved.emit(new_item, old_data, new_data)
            else:
                print("새 아이템 생성 실패")

    """
    아이템 상태 복원
    """
    def _restore_item_states(self, new_item, new_data):
        item_code = new_data.get('Item', '')

        # 1. 현재 사용자 설정에 따른 상태선 표시 설정
        if hasattr(self, 'current_filter_states'):
            new_item.show_shortage_line = self.current_filter_states.get('shortage', False)
            new_item.show_shipment_line = self.current_filter_states.get('shipment', False)
            new_item.show_pre_assigned_line = self.current_filter_states.get('pre_assigned', False)
        
        # 사전할당 상태
        if item_code in self.pre_assigned_items:
            new_item.set_pre_assigned_status(True)
            
        # 출하 실패 상태
        if item_code in self.shipment_failure_items:
            failure_info = self.shipment_failure_items[item_code]
            new_item.set_shipment_failure(True, failure_info.get('reason', 'Unknown reason'))

        # 자재부족 상태
        if hasattr(self, 'current_shortage_items') and item_code in self.current_shortage_items:
            shortage_info = self.current_shortage_items[item_code]
            new_item.set_shortage_status(True, shortage_info)
            
        # 상태선 업데이트를 위해 repaint 요청
        new_item.update()
        

    """
    엑셀 파일 로드 -  ResultPage의 통합 메서드 호출
    """
    def load_excel_file(self):
        # 부모 페이지 확인
        if not hasattr(self, 'parent_page') or self.parent_page is None:
            print("[ERROR] parent_page 참조가 없습니다.")
            EnhancedMessageBox.show_validation_error(
                self, 
                "Error", 
                "페이지 참조가 설정되지 않았습니다."
            )
            return
        
        # ResultPage의 load_result_file 메서드 호출
        file_path, _ = QFileDialog.getOpenFileName(
            self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls *.csv)"
        )
        
        if file_path:
            print("LeftSection: MVC 모드 - ResultPage를 통한 파일 로드")
            self.parent_page.load_result_file(file_path)

    """
    아이템 목록과 그리드 초기화하는 메서드
    """
    def clear_all_items(self) :
        self.all_items = []
        self.search_widget.on_clear()
        if hasattr(self, 'grid_widget'):
            self.grid_widget.clearAllItems()

    """
    Line과 Time으로 데이터 그룹화하고 개별 아이템으로 표시
    UI 업데이트 - MVC 모드에서 시그널 발생 제어
    """
    def update_ui_with_signals(self):
        if self.data is None or 'Line' not in self.data.columns or 'Time' not in self.data.columns:
            EnhancedMessageBox.show_validation_error(self, "Grouping Failed",
                                                     "Data is missing or does not contain 'Line' or 'Time' columns.\nPlease load data with the required columns.")
            return

        try:
            # 제조동 정보 추출 (Line 이름의 첫 글자가 제조동)
            self.data['Building'] = self.data['Line'].str[0]  # 라인명의 첫 글자를 제조동으로 사용

            # 제조동별 생산량 계산 (정렬 목적)
            building_production = self.data.groupby('Building')['Qty'].sum()

            # 생산량 기준으로 제조동 정렬 (내림차순)
            sorted_buildings = building_production.sort_values(ascending=False).index.tolist()

            # ---- 데이터프레임 정렬을 위한 전처리 ----
            # 1. 제조동 정렬 순서 생성
            building_order = {b: i for i, b in enumerate(sorted_buildings)}
            self.data['Building_sort'] = self.data['Building'].apply(lambda x: building_order.get(x, 999))

            # 2. 같은 제조동 내에서 라인명으로 정렬 (I_01 -> 01 형태로 변환)
            self.data['Line_sort'] = self.data['Line'].apply(
                lambda x: x.split('_')[1] if '_' in x else x
            )

            # 3. 최종 정렬 적용 (제조동 순위 -> 라인명 -> 시간)
            self.data = self.data.sort_values(by=['Building_sort', 'Line_sort', 'Time']).reset_index(drop=True)

            # 4. 임시 정렬 컬럼 제거
            self.data = self.data.drop(columns=['Building_sort', 'Line_sort'], errors='ignore')

            # 5. 원본 데이터도 정렬된 상태로 저장
            self.original_data = self.data.copy()

            # Line과 Time 값 추출
            all_lines = self.data['Line'].unique()
            times = sorted(self.data['Time'].unique())

            # 제조동 별로 정렬된 라인 목록 생성 (각 제조동 내에서는 라인 이름 기준 오름차순으로 정렬)
            lines = []
            for building in sorted_buildings:
                # 해당 제조동에 속하는 라인들 찾기
                building_lines = [line for line in all_lines if line.startswith(building)]

                # 라인 이름 기준 오름차순 정렬
                sorted_building_lines = sorted(building_lines)

                # 정렬된 라인 추가
                lines.extend(sorted_building_lines)

            # 교대 시간 구분
            shifts = {}
            for time in times:
                if int(time) % 2 == 1:
                    shifts[time] = "Day"
                else:
                    shifts[time] = "Night"

            # 라인별 교대 정보
            line_shifts = {}
            for line in lines:
                line_shifts[line] = ["Day", "Night"]

            # 행 헤더
            self.row_headers = []
            for line in lines:
                for shift in ["Day", "Night"]:
                    self.row_headers.append(f"{line}_({shift})")

            self.grid_widget.setupGrid(
                rows=len(self.row_headers),
                columns=len(self.days),
                row_headers=self.row_headers,
                column_headers=self.days,
                line_shifts=line_shifts
            )

            # 데이터를 행/열별로 그룹화
            grouped_items = {}  # 키: (row_idx, col_idx), 값: 아이템 목록

            # 첫 번째 단계: 아이템을 행과 열 기준으로 그룹화
            for _, row_data in self.data.iterrows():
                if 'Line' not in row_data or 'Time' not in row_data or 'Item' not in row_data:
                    continue

                line = row_data['Line']
                time = row_data['Time']
                shift = shifts[time]
                day_idx = (int(time) - 1) // 2

                if day_idx >= len(self.days):
                    continue

                row_key = f"{line}_({shift})"

                try:
                    row_idx = self.row_headers.index(row_key)
                    col_idx = day_idx

                    # 키 생성 및 데이터 저장
                    grid_key = (row_idx, col_idx)
                    if grid_key not in grouped_items:
                        grouped_items[grid_key] = []

                    # 아이템 데이터 추가
                    item_data = row_data.to_dict()
                    qty = item_data.get('Qty', 0)
                    if pd.isna(qty):
                        qty = 0

                    # 수량을 정수로 변환하여 저장
                    item_data['Qty'] = int(float(qty)) if isinstance(qty, (int, float, str)) else 0
                    grouped_items[grid_key].append(item_data)
                except ValueError as e:
                    print(f"인덱스 찾기 오류: {e}")
                    continue

            # 두 번째 단계: 아이템을 그리드에 추가
            for (row_idx, col_idx), items in grouped_items.items():
                for item_data in items:
                    item_info = str(item_data.get('Item', ''))

                    # Qty 표시
                    qty = item_data.get('Qty', 0)
                    if pd.notna(qty) and qty != 0:
                        item_info += f"    {qty}"

                    # 아이템 추가
                    new_item = self.grid_widget.addItemAt(row_idx, col_idx, item_info, item_data)

                    if new_item:
                        item_code = item_data.get('Item', '')

                        # 사전할당 아이템인 경우
                        if item_code in self.pre_assigned_items:
                            new_item.set_pre_assigned_status(True)

                        # 출하 실패 아이템인 경우
                        if item_code in self.shipment_failure_items:
                            failure_info = self.shipment_failure_items[item_code]
                            new_item.set_shipment_failure(True, failure_info.get('reason', 'Unknown reason'))

                        # 자재부족 아이템인 경우
                        if hasattr(self, 'current_shortage_items') and item_code in self.current_shortage_items:
                            shortage_info = self.current_shortage_items[item_code]
                            new_item.set_shortage_status(True, shortage_info)

            # 그룹화된 데이터 저장 (기존 코드 유지)
            if 'Day' in self.data.columns:
                self.grouped_data = self.data.groupby(['Line', 'Day', 'Time']).first().reset_index()
            else:
                self.grouped_data = self.data.groupby(['Line', 'Time']).first().reset_index()

            # MVC 모드에서는 viewDataChanged 시그널 발생 안함
            if not self._mvc_mode:
                df = self.extract_dataframe()
                self.viewDataChanged.emit(df)
                print("LeftSection: Legacy 모드 - viewDataChanged 시그널 발생")
            else:
                print("LeftSection: MVC 모드 - viewDataChanged 시그널 억제")

            # 필터 데이터를 그리드 설정 직후에 즉시 업데이트
            # 정렬된 라인 순서를 직접 전달
            projects = []
            if 'Project' in self.data.columns:
                projects = [str(project) if not pd.isna(project) else "N/A" for project in self.data['Project']]
                projects = sorted(set(projects))

            # 필터 위젯에 정렬된 라인 순서 직접 설정 - 강제로 호출
            if hasattr(self, 'filter_widget') and self.filter_widget:
                self.filter_widget.set_filter_data(lines, projects)
            else:
                print("DEBUG: 필터 위젯이 없습니다!")

            # 추가로 직접 호출도 해보기
            try:
                self.update_filter_data()
            except Exception as e:
                print(f"DEBUG: update_filter_data 호출 중 오류: {e}")

            # 모든 새 아이템에 현재 범례 필터 상태 적용
            print(f"[DEBUG] 아이템 생성 후 현재 필터 상태 적용: {getattr(self, 'current_filter_states', {})}")
            
            # current_filter_states가 없거나 비어있으면 기본값 설정
            if not hasattr(self, 'current_filter_states') or not self.current_filter_states:
                # 기본값 설정 (자재부족은 True, 나머지는 False)
                self.current_filter_states = {
                    'shortage': True,
                    'shipment': False,
                    'pre_assigned': False
                }
            
            shortage_show = self.current_filter_states.get('shortage', True)  # 기본값 True
            shipment_show = self.current_filter_states.get('shipment', False)
            pre_assigned_show = self.current_filter_states.get('pre_assigned', False)

            # 생성된 모든 아이템에 적용
            if hasattr(self, 'grid_widget') and hasattr(self.grid_widget, 'containers'):
                for row_containers in self.grid_widget.containers:
                    for container in row_containers:
                        for item in container.items:
                            item.show_shortage_line = shortage_show
                            item.show_shipment_line = shipment_show
                            item.show_pre_assigned_line = pre_assigned_show
                            item.update()  # 상태선 업데이트

        except Exception as e:
            # 에러 메시지 표시
            print(f"그룹핑 에러: {e}")
            import traceback
            traceback.print_exc()
            EnhancedMessageBox.show_validation_error(self, "Grouping Error",
                                                     f"An error occurred during data grouping.\n{str(e)}")

    """
    원본 데이터로 되돌리기
    """
    def reset_to_original(self):
        if self.original_data is None:
            EnhancedMessageBox.show_validation_error(self, "Reset Failed", 
                                "No original data to reset to.")
            return
        
        # 사용자 확인 Dialog
        reply = EnhancedMessageBox.show_confirmation(
            self, "Reset to Original", "Are you sure you want to reset all changes and return to the original data?\nAll modifications will be lost."
        )

        if reply:
            # 컨트롤러 연결
            if self._mvc_mode and self.controller:
                print("LeftSection: MVC 모드 - 컨트롤러를 통해 리셋")
                self.controller.reset_data()
                
                # Reset 버튼 비활성화
                self.reset_button.setEnabled(False)

                # 성공 메세지
                EnhancedMessageBox.show_validation_success(
                    self, "Reset Complete", "Data has been successfully reset to the original values."
                )
            else: 
                # 레거시 방식
                print("LeftSection: Legacy 모드 - 직접 리셋")
                self.data = self.original_data.copy()
                self.data_manager.update_table_from_data()

                # Reset 버튼 비활성화
                self.reset_button.setEnabled(False)

                # 성공 메세지
                EnhancedMessageBox.show_validation_success(
                    self, "Reset Complete", "Data has been successfully reset to the original values."
                )

    """
    그리드의 모든 아이템에 사전할당 상태 적용
    """
    def _apply_pre_assigned_status_to_items(self):
        if not hasattr(self, 'grid_widget') or not hasattr(self.grid_widget, 'containers'):
            print("LeftSection: 그리드 위젯이 없음 - 사전할당 상태 적용 스킵")
            return
        
        for row_containers in self.grid_widget.containers:
            for container in row_containers:
                for item in container.items:
                    if hasattr(item, 'item_data') and item.item_data and 'Item' in item.item_data:
                        item_code = item.item_data['Item']
                        
                        # 해당 아이템이 사전할당 목록에 있는지 확인
                        if item_code in self.pre_assigned_items:
                            item.set_pre_assigned_status(True)
                        else:
                            item.set_pre_assigned_status(False)


    """
    사전할당 아이템 목록 설정 및 즉시 적용
    """
    def set_pre_assigned_items(self, pre_assigned_items):
        self.pre_assigned_items = set(pre_assigned_items)
        
        # 그리드가 이미 생성되어 있으면 즉시 적용
        if (hasattr(self, 'grid_widget') and 
            hasattr(self.grid_widget, 'containers') and 
            self.grid_widget.containers):
            self._apply_pre_assigned_status_to_items()
        else:
            print("LeftSection: 그리드 없음 - 나중에 적용 예정")

    """
    현재 자재부족 아이템 정보 저장
    """
    def set_current_shortage_items(self, shortage_items):
        # 자재 부족 정보 저장
        self.current_shortage_items = shortage_items
        
        # 시프트 기반으로 자재 부족 상태 적용
        self.update_left_widget_shortage_status(shortage_items)

    """
    왼쪽 위젯의 아이템들에 자재 부족 상태 적용

    Args:
        shortage_dict: {item_code: [{shift: shift_num, material: material_code, shortage: shortage_amt}]}
    """
    def update_left_widget_shortage_status(self, shortage_dict):
        if not hasattr(self, 'grid_widget') or not hasattr(self.grid_widget, 'containers'):
            return
        
        status_applied_count = 0
        
        # 그리드의 모든 컨테이너 순회
        for row_containers in self.grid_widget.containers:
            for container in row_containers:
                # 각 컨테이너의 아이템들 순회
                for item in container.items:
                    if hasattr(item, 'item_data') and item.item_data and 'Item' in item.item_data:
                        item_code = item.item_data['Item']
                        item_time = item.item_data.get('Time')  # 시프트(Time) 정보 가져오기
                        
                        # 해당 아이템이 자재 부족 목록에 있는지 확인
                        if item_code in shortage_dict:
                            # 시프트별 부족 정보 검사
                            shortages_for_item = shortage_dict[item_code]
                            matching_shortages = []
                            
                            for shortage in shortages_for_item:
                                shortage_shift = shortage.get('shift')
                                
                                # 시프트가 일치하면 부족 정보 저장
                                if shortage_shift and item_time and int(shortage_shift) == int(item_time):
                                    matching_shortages.append(shortage)
                            
                            # 일치하는 시프트의 부족 정보가 있으면 부족 상태로 설정
                            if matching_shortages:
                                item.set_shortage_status(True, matching_shortages)
                                status_applied_count += 1
                            else:
                                item.set_shortage_status(False)
                        else:
                            # 부족 목록에 없는 경우 부족 상태 해제
                            item.set_shortage_status(False)
        
        print(f"자재 부족 상태 적용 완료: {status_applied_count}개 아이템에 적용됨")

    """
    모든 상태 정보를 현재 아이템들에 적용
    """
    def apply_all_states(self):
        if not hasattr(self, 'grid_widget') or not hasattr(self.grid_widget, 'containers'):
            return
        
        for row_containers in self.grid_widget.containers:
            for container in row_containers:
                for item in container.items:
                    if hasattr(item, 'item_data') and item.item_data and 'Item' in item.item_data:
                        item_code = item.item_data['Item']
                        item_time = item.item_data.get('Time')

                        # 사전할당 상태
                        if item_code in self.pre_assigned_items:
                            item.set_pre_assigned_status(True)

                        # 출하 실패 상태
                        if item_code in self.shipment_failure_items:
                            failure_info = self.shipment_failure_items[item_code]
                            item.set_shipment_failure(True, failure_info.get('reason', 'Unknown'))

                        # 자재 부족 상태 - 시프트별 체크 적용
                        if hasattr(self, 'current_shortage_items') and item_code in self.current_shortage_items:
                            shortages = self.current_shortage_items[item_code]
                            matching_shortages = []
                            
                            # 시프트별 부족 정보 검사
                            for shortage in shortages:
                                shortage_shift = shortage.get('shift')
                                
                                # 시프트가 일치하는 경우만 처리
                                if shortage_shift and item_time and int(shortage_shift) == int(item_time):
                                    matching_shortages.append(shortage)
                            
                            # 일치하는 시프트의 부족 정보가 있으면 부족 상태로 설정
                            if matching_shortages:
                                item.set_shortage_status(True, matching_shortages)
                            else:
                                item.set_shortage_status(False)

    """
    안전한 필터 적용 - 드래그앤드롭 후 호출
    """
    def apply_filters_safely(self):
        try:
            # 현재 데이터가 있는지 확인
            if not hasattr(self, 'data') or self.data is None or self.data.empty:
                print("DEBUG: 데이터가 없어서 필터 적용 스킵")
                return

            # 범례 필터만 적용 (엑셀 필터는 건드리지 않음)
            self.filter_manager.apply_legend_filters_only()

            # 검색이 활성화된 경우에만 검색 상태 복원
            if hasattr(self, 'search_widget') and self.search_widget.is_search_active():
                search_text = self.search_widget.get_search_text()
                if search_text:
                    QTimer.singleShot(50, lambda: self.search_manager.search_items(search_text))

        except Exception as e:
            print(f"안전한 필터 적용 중 오류: {e}")
            import traceback
            traceback.print_exc()

    """
    범례 위젯에서 필터가 변경될 때 호출
    """
    def on_filter_changed(self, status_type, is_checked):
        # 이전 상태와 동일하면 불필요한 처리 방지
        if self.current_filter_states.get(status_type) == is_checked:
            return
        
        # 상태 업데이트
        self.current_filter_states[status_type] = is_checked
        
        # 필터 적용
        self.apply_all_filters()
        
        # 필터가 활성화되면 해당 상태 분석 요청 
        if is_checked:
            self.filter_activation_requested.emit(status_type)

    """
    현재 뷰에 로드된 DataFrame(self.data)의 사본 반환
    viewDataChanged 신호를 뿌릴 때 사용 
    """
    def extract_dataframe(self) -> pd.DataFrame:
        if self._mvc_mode and self.controller:
            # MVC 모드에서는 모델에서 데이터 가져오기
            current_data = self.controller.get_current_data()
            if current_data is not None and not current_data.empty:
                return self._normalize_data_types(current_data.copy())
            else:
                return pd.DataFrame()
        else:
            # Legacy 모드에서는 직접 데이터 반환
            if hasattr(self, 'data') and isinstance(self.data, pd.DataFrame):
                return self._normalize_data_types(self.data.copy())
            else:
                return pd.DataFrame()
 
    """
    출하 실패 아이템 정보 설정
    """
    def set_shipment_failure_items(self, failure_items):
                
        # 이전 출하 실패 정보 초기화
        old_failure_items = getattr(self, 'shipment_failure_items', {})
        
        # 새 출하 실패 정보 저장
        self.shipment_failure_items = failure_items
        
        # 상태 변화가 있을 때만 UI 업데이트
        if old_failure_items != failure_items:
            self.apply_shipment_failure_status()

    """
    출하 실패 상태를 모든 아이템에 적용
    """
    def apply_shipment_failure_status(self):
        if not hasattr(self, 'grid_widget') or not hasattr(self.grid_widget, 'containers'):
            return
        
        # 출하 실패 아이템 목록이 없는 경우 초기화
        if not hasattr(self, 'shipment_failure_items'):
            self.shipment_failure_items = {}
        
        status_applied_count = 0
        
        # 모든 컨테이너와 아이템 순회
        for row_containers in self.grid_widget.containers:
            for container in row_containers:
                for item in container.items:
                    if not hasattr(item, 'item_data') or not item.item_data:
                        continue
                        
                    item_data = item.item_data
                    
                    # 필수 필드 확인
                    if 'Item' not in item_data:
                        continue
                        
                    item_code = item_data['Item']
                    
                    # 간단하게 아이템 코드로만 검색 (복합 키는 제외)
                    if item_code in self.shipment_failure_items:
                        # 출하 실패 정보 가져오기
                        failure_info = self.shipment_failure_items[item_code]
                        reason = failure_info.get('reason', '출하 실패')
                        
                        # 출하 실패 상태로 설정
                        item.set_shipment_failure(True, reason)
                        status_applied_count += 1
                    else:
                        # 출하 성공 상태로 설정 (기존 실패였던 경우)
                        if hasattr(item, 'is_shipment_failure') and item.is_shipment_failure:
                            item.set_shipment_failure(False, None)

    """
    스크롤 위치 복원
    """
    def _restore_scroll_position(self, position):
        if hasattr(self.grid_widget, 'scroll_area'):
            # 약간의 지연을 주고 스크롤 위치 복원
            h_bar = self.grid_widget.scroll_area.horizontalScrollBar()
            v_bar = self.grid_widget.scroll_area.verticalScrollBar()

            if 'horizontal' in position:
                h_bar.setValue(position['horizontal'])
            if 'vertical' in position:
                v_bar.setValue(position['vertical'])

    """
    선택된 아이템으로 스크롤 이동
    """
    def _scroll_to_selected_item(self, item_id):
        if not item_id or not hasattr(self, 'grid_widget'):
            return

        # 아이템 ID로 아이템 위젯 찾기
        found_item = None
        found_container = None

        for row_idx, row_containers in enumerate(self.grid_widget.containers):
            for col_idx, container in enumerate(row_containers):
                for item in container.items:
                    if hasattr(item, 'item_data') and item.item_data and item.item_data.get('_id') == item_id:
                        found_item = item
                        found_container = container
                        break
                if found_item:
                    break
            if found_item:
                break

        if found_item and found_container:
            # 아이템 선택 상태 설정
            found_item.set_selected(True)
            self.current_selected_item = found_item
            self.current_selected_container = found_container

            # 스크롤 위치 직접 설정 (아래 방법도 추가)
            QTimer.singleShot(50, lambda: self._force_scroll_to_item(found_container, found_item))

            # ItemGridWidget의 ensure_item_visible 호출 (기존 방식)
            if hasattr(self.grid_widget, 'ensure_item_visible'):
                self.grid_widget.ensure_item_visible(found_container, found_item)

    """
    직접 스크롤 위치 설정 
    """
    def _force_scroll_to_item(self, container, item):
        if not container or not item or not hasattr(self.grid_widget, 'scroll_area'):
            return

        try:
            # 컨테이너 위치 계산
            for row_idx, row in enumerate(self.grid_widget.containers):
                if container in row:
                    col_idx = row.index(container)

                    # 스크롤 영역 가져오기
                    scroll_area = self.grid_widget.scroll_area

                    # 컨테이너와 아이템의 전역 위치 계산
                    container_pos = container.mapTo(self.grid_widget.scroll_content, QPoint(0, 0))
                    item_pos = item.mapTo(container, QPoint(0, 0))

                    # 최종 타겟 위치 계산
                    target_y = container_pos.y() + item_pos.y()

                    # 스크롤바 이동
                    v_bar = scroll_area.verticalScrollBar()

                    # 아이템이 화면 중앙에 오도록 스크롤
                    viewport_height = scroll_area.viewport().height()
                    target_y = max(0, target_y - (viewport_height // 2) + (item.height() // 2))

                    # 스크롤 위치 설정
                    v_bar.setValue(target_y)

                    break
        except Exception as e:
            print(f"강제 스크롤 중 오류 발생: {str(e)}")

    """
    스크롤 위치 저장
    """
    def _save_scroll_position(self):
        try:
            if hasattr(self.grid_widget, 'scroll_area'):
                return {
                    'horizontal': self.grid_widget.scroll_area.horizontalScrollBar().value(),
                    'vertical': self.grid_widget.scroll_area.verticalScrollBar().value()
                }
        except:
            pass
        return {'horizontal': 0, 'vertical': 0}

    """
    스크롤 위치 복원
    """
    def _restore_scroll_position(self, position):
        if not position:
            return
            
        try:
            if hasattr(self.grid_widget, 'scroll_area'):
                h_bar = self.grid_widget.scroll_area.horizontalScrollBar()
                v_bar = self.grid_widget.scroll_area.verticalScrollBar()
                
                
                if 'horizontal' in position:
                    h_bar.setValue(position['horizontal'])
                if 'vertical' in position:
                    v_bar.setValue(position['vertical'])
                
        except Exception as e:
            print(f"스크롤 위치 복원 오류: {e}")
