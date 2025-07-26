from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import os
import pandas as pd

from app.views.components.data_upload_components.data_table_component import DataTableComponent
from app.views.components.data_upload_components.enhanced_table_filter_component import EnhancedTableFilterComponent
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *
from app.models.common.file_store import DataStore

"""
파일 탭 관리를 위한 클래스
DataInputPage의 탭 관련 로직을 모두 담당
"""
class FileTabManager:
    def __init__(self, parent):
        self.parent = parent
        self.tab_bar = parent.tab_bar
        self.stacked_widget = parent.stacked_widget
        self.open_tabs = {}  # {(file_path, sheet_name): tab_index}
        self.updating_from_tab = False

        # 탭 스타일 설정 - 스타일 관리를 여기에서만 담당
        self.apply_tab_styles()

        # 탭 바 시그널 연결
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self.on_tab_close_requested)
        self.tab_bar.tabMoved.connect(self.on_tab_moved)
        self.tab_bar.setTabsClosable(True)

        # 시작 페이지 생성
        self.create_start_page()

    def apply_tab_styles(self):
        """모든 탭 관련 스타일을 한 곳에서 적용"""
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setElideMode(Qt.ElideNone)
        self.tab_bar.setStyleSheet(f"""
            QTabBar {{
                background-color: transparent;
                border: none;
            }}
            QTabBar::tab {{
                background: #f0f0f0;
                border: 1px solid #cccccc;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                padding: {h(2)}px {w(5)}px;
                margin-right: 2px;
                min-width: {w(40)}px;
                min-height: {h(10)}px;
                font-family: {font_manager.get_just_font("SamsungOne-700").family()};
                font-weight: bold;
                font-size: {f(12)}px;
            }}
            QTabBar::tab:selected, QTabBar::tab:hover {{
                background: #1428A0;
                color: white;
            }}
            QTabBar::tab:selected {{
                border-bottom-color: white;
            }}
        """)

        self.stacked_widget.setContentsMargins(0, 0, 0, 0)

    """새 탭 생성 - 항상 원본 파일에서 로드"""
    def create_new_tab(self, file_path, sheet_name):
        try:
            # 🔥 항상 원본 파일에서 로드 (우선순위 체크 제거)
            if sheet_name:
                df = DataTableComponent.load_data_from_file(file_path, sheet_name=sheet_name)
            else:
                df = DataTableComponent.load_data_from_file(file_path)

            # 탭 제목 설정
            file_name = os.path.basename(file_path)
            file_name_without_ext = os.path.splitext(file_name)[0]

            if sheet_name:
                tab_title = f"{file_name_without_ext}/{sheet_name}"
            else:
                tab_title = file_name_without_ext

            # 수정된 파일인지 확인하여 표시
            if (file_path in self.parent.data_modifier.modified_data_dict and
                    (sheet_name or 'data') in self.parent.data_modifier.modified_data_dict[file_path]):
                tab_title += " *"

            # 새 탭용 위젯 생성
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            tab_layout.setContentsMargins(3, 3, 3, 3)

            # 필터 컴포넌트 생성
            filter_component = EnhancedTableFilterComponent()

            # 데이터 테이블 생성
            data_container = DataTableComponent.create_table_from_dataframe(
                df,
                file_path=file_path,
                sheet_name=sheet_name,
                filter_component=filter_component
            )
            data_container.setStyleSheet("border-radius: 10px; background-color: white; border:3px solid #cccccc;")
            tab_layout.addWidget(data_container)

            # 새 탭과 스택 위젯 항목 추가
            tab_index = self.tab_bar.addTab(tab_title)
            self.stacked_widget.addWidget(tab_widget)

            # 탭 상태 저장 및 선택
            self.open_tabs[(file_path, sheet_name)] = tab_index
            self.tab_bar.setCurrentIndex(tab_index)  # 새 탭으로 전환

            # DataStore에 저장
            from app.models.common.file_store import DataStore
            df_dict = DataStore.get("dataframes", {})
            key = f"{file_path}:{sheet_name}" if sheet_name else file_path
            df_dict[key] = df
            DataStore.set("dataframes", df_dict)

            # original_dataframes에 원본 데이터 저장 (비교용)
            original_df_dict = DataStore.get('original_dataframes', {})
            if key not in original_df_dict:
                try:
                    # 깊은 복사 수행
                    original_df = pd.DataFrame(df.values.copy(),
                                               index=df.index.copy(),
                                               columns=df.columns.copy())
                    original_df_dict[key] = original_df
                except Exception as e:
                    print(f"원본 데이터프레임 저장 중 오류: {e}")
                    # 오류 발생 시 기본 복사 시도
                    original_df_dict[key] = df.copy()

                DataStore.set('original_dataframes', original_df_dict)

            return tab_index
        except Exception as e:
            print(f"탭 생성 오류: {str(e)}")
            return -1

    """특정 파일과 시트에 해당하는 탭 닫기"""
    def close_tab(self, file_path, sheet_name):
        tab_key = (file_path, sheet_name)

        if tab_key not in self.open_tabs:
            return False

        tab_index = self.open_tabs[tab_key]

        # 탭을 닫기 전에 데이터 저장
        if 0 <= tab_index < self.stacked_widget.count():
            tab_widget = self.stacked_widget.widget(tab_index)
            self.parent.data_modifier.save_tab_data(tab_widget, file_path, sheet_name)

        # 1. 모든 위젯과 키 정보를 저장 (닫을 탭 제외)
        widgets_to_keep = []
        keys_to_keep = []

        for key, idx in sorted(self.open_tabs.items(), key=lambda x: x[1]):
            if key != tab_key:  # 닫을 탭 제외
                if 0 <= idx < self.stacked_widget.count():
                    widget = self.stacked_widget.widget(idx)
                    widgets_to_keep.append(widget)
                    keys_to_keep.append(key)

        # 2. 탭 제거
        self.tab_bar.removeTab(tab_index)

        # 3. 모든 위젯 제거 (삭제하지 않고 제거만 함)
        while self.stacked_widget.count() > 0:
            self.stacked_widget.removeWidget(self.stacked_widget.widget(0))

        # 4. open_tabs 초기화
        self.open_tabs = {}

        # 5. 위젯 재추가 및 딕셔너리 업데이트
        for i, (widget, key) in enumerate(zip(widgets_to_keep, keys_to_keep)):
            self.stacked_widget.addWidget(widget)
            self.open_tabs[key] = i

        # 6. 현재 선택된 탭에 맞게 스택 위젯 설정
        current_idx = self.tab_bar.currentIndex()
        if 0 <= current_idx < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(current_idx)

        # 7. 모든 탭이 닫혔는지 확인
        if self.tab_bar.count() == 0:
            self.create_start_page()

        return True

    """탭이 변경되면 호출되는 함수"""
    def on_tab_changed(self, index):
        # 이전 탭의 데이터 저장
        prev_idx = self.stacked_widget.currentIndex()
        if prev_idx >= 0 and prev_idx < self.stacked_widget.count():
            old_tab_widget = self.stacked_widget.widget(prev_idx)
            if old_tab_widget:
                # 현재 탭에 해당하는 파일과 시트 찾기
                old_file_path = None
                old_sheet_name = None
                for (file_path, sheet_name), idx in self.open_tabs.items():
                    if idx == prev_idx:
                        old_file_path = file_path
                        old_sheet_name = sheet_name
                        break

                if old_file_path:
                    self.parent.data_modifier.save_tab_data(old_tab_widget, old_file_path, old_sheet_name)

        # 스택 위젯 업데이트
        self.stacked_widget.setCurrentIndex(index)

        # 사이드바에서 업데이트 중이면 무시 (무한 루프 방지)
        if self.parent.sidebar_manager.updating_from_sidebar:
            return

        if index < 0 or index >= self.tab_bar.count():
            return

        # 시작 페이지인 경우 (인덱스 0)
        if index == 0 and self.tab_bar.tabText(0) == "Start Page":
            self.parent.current_file = None
            self.parent.current_sheet = None
            return

        # 현재 선택된 탭에 해당하는 파일과 시트 찾기
        found = False
        for (file_path, sheet_name), idx in self.open_tabs.items():
            if idx == index:
                found = True
                self.parent.current_file = file_path
                self.parent.current_sheet = sheet_name

                # 파일 정보 업데이트
                if file_path in self.parent.loaded_files:
                    file_info = self.parent.loaded_files[file_path]
                    if sheet_name:
                        file_info['current_sheet'] = sheet_name

                # 사이드바에서도 동일 항목 선택 처리
                self.updating_from_tab = True
                self.parent.file_explorer.select_file_or_sheet(file_path, sheet_name)
                self.updating_from_tab = False

                break

        if not found:
            self.parent.current_file = None
            self.parent.current_sheet = None

    """탭 닫기 요청 처리"""
    def on_tab_close_requested(self, index):
        # 시작 페이지는 닫을 수 없음
        if index == 0 and self.tab_bar.tabText(0) == "Start Page":
            return

        # 닫을 탭의 키 찾기
        tab_key_to_close = None
        for tab_key, idx in self.open_tabs.items():
            if idx == index:
                tab_key_to_close = tab_key
                break

        if tab_key_to_close:
            # 탭 닫기 실행
            self.close_tab(tab_key_to_close[0], tab_key_to_close[1])

            # 현재 선택된 탭에 맞게 스택 위젯 설정
            current_idx = self.tab_bar.currentIndex()
            if 0 <= current_idx < self.stacked_widget.count():
                self.stacked_widget.setCurrentIndex(current_idx)

    def on_tab_moved(self, from_index, to_index):
        """탭이 이동되면 실행되는 함수"""
        # 1. 이동할 탭의 키 찾기
        moved_tab_key = None
        for key, idx in self.open_tabs.items():
            if idx == from_index:
                moved_tab_key = key
                break

        if not moved_tab_key:
            return

        # 2. 모든 위젯과 키 백업
        widgets_by_index = {}
        for idx in range(self.stacked_widget.count()):
            widgets_by_index[idx] = self.stacked_widget.widget(idx)

        # 3. 인덱스 업데이트
        new_open_tabs = {}
        for key, old_idx in self.open_tabs.items():
            # 이동한 탭
            if key == moved_tab_key:
                new_idx = to_index
            # 범위 내의 다른 탭
            elif from_index < to_index and old_idx > from_index and old_idx <= to_index:
                new_idx = old_idx - 1  # 한 칸 앞으로
            elif from_index > to_index and old_idx < from_index and old_idx >= to_index:
                new_idx = old_idx + 1  # 한 칸 뒤로
            # 영향 받지 않는 탭
            else:
                new_idx = old_idx

            new_open_tabs[key] = new_idx

        # 4. 스택 위젯 재구성
        for i in range(self.stacked_widget.count()):
            self.stacked_widget.removeWidget(self.stacked_widget.widget(0))

        # 5. 새 인덱스 순서대로 위젯 다시 배치
        for key, new_idx in sorted(new_open_tabs.items(), key=lambda x: x[1]):
            old_idx = self.open_tabs[key]
            if old_idx in widgets_by_index:
                widget = widgets_by_index[old_idx]
                self.stacked_widget.insertWidget(new_idx, widget)

        # 6. 새 매핑 적용
        self.open_tabs = new_open_tabs

        # 7. 현재 선택된 탭에 맞게 스택 위젯 설정
        current_idx = self.tab_bar.currentIndex()
        if 0 <= current_idx < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(current_idx)

    """Start Page 탭 제거"""
    def remove_start_page(self):
        if self.tab_bar.count() > 0 and self.tab_bar.tabText(0) == "Start Page":
            # Start Page 위젯 제거
            start_widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(start_widget)
            start_widget.deleteLater()

            # 탭 제거
            self.tab_bar.removeTab(0)

            # open_tabs의 인덱스 조정 (모든 탭 인덱스를 1씩 감소)
            updated_open_tabs = {}
            for key, idx in self.open_tabs.items():
                updated_open_tabs[key] = idx - 1
            self.open_tabs = updated_open_tabs

    """Start Page 생성 및 추가"""
    def create_start_page(self):
        # Start Page 위젯 생성
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_msg = QLabel("Select a file or sheet from the sidebar to open a new tab")
        empty_msg.setAlignment(Qt.AlignCenter)
        empty_msg.setStyleSheet(
            f"color: #888; font-size: {f(24)}px; font-family: {font_manager.get_just_font('SamsungSharpSans-Bold')}; font-weight: bold;")
        empty_layout.addWidget(empty_msg)

        # 위젯 추가
        self.stacked_widget.insertWidget(0, empty_widget)
        self.tab_bar.insertTab(0, "Start Page")
        self.tab_bar.setCurrentIndex(0)

    """파일 관련 모든 탭 닫기"""
    def close_file_tabs(self, file_path):
        # 해당 파일과 관련된 모든 탭 찾아서 닫기
        tabs_to_remove = []
        for (path, sheet), idx in self.open_tabs.items():
            if path == file_path:
                tabs_to_remove.append((path, sheet))

        # 탭 삭제 (역순으로)
        for key in tabs_to_remove:
            self.close_tab(key[0], key[1])

    """탭 제목 업데이트 (수정 상태에 따라)"""
    def update_tab_title(self, file_path, sheet_name, is_modified=False):
        # 해당 탭 찾기
        tab_key = (file_path, sheet_name)
        if tab_key not in self.open_tabs:
            return

        tab_index = self.open_tabs[tab_key]

        # 탭 제목 설정 - 여기서 수정
        file_name = os.path.basename(file_path)
        # 확장자 제거
        file_name_without_ext = os.path.splitext(file_name)[0]

        if sheet_name:
            base_title = f"{file_name_without_ext}/{sheet_name}"
        else:
            base_title = file_name_without_ext

        # 수정된 파일인지 확인
        is_modified = is_modified or (
                file_path in self.parent.data_modifier.modified_data_dict and
                (sheet_name or 'data') in self.parent.data_modifier.modified_data_dict[file_path]
        )

        # 탭 제목 업데이트
        tab_title = base_title + " *" if is_modified else base_title
        current_title = self.tab_bar.tabText(tab_index)
        if current_title != tab_title:
            self.tab_bar.setTabText(tab_index, tab_title)

    """현재 선택된 탭의 데이터 저장"""
    def save_current_tab_data(self):
        current_tab_index = self.tab_bar.currentIndex()
        if current_tab_index >= 0 and current_tab_index < self.stacked_widget.count():
            current_tab_widget = self.stacked_widget.widget(current_tab_index)
            if current_tab_widget:
                # 현재 탭에 해당하는 파일과 시트 찾기
                for (file_path, sheet_name), idx in self.open_tabs.items():
                    if idx == current_tab_index:
                        self.parent.data_modifier.save_tab_data(current_tab_widget, file_path, sheet_name)
                        return True
        return False

    """
    undo/redo 시 호출되는 메서드
    """

    def on_undo_redo_state_changed(self, can_undo, can_redo):
        if hasattr(self.parent, 'undo_btn') and hasattr(self.parent, 'redo_btn'):
            self.parent.undo_btn.setEnabled(can_undo)
            self.parent.redo_btn.setEnabled(can_redo)

    """
    undo/redo 시 데이터 변경되었을 때 호출되는 메서드
    """
    def on_data_changed_by_undo_redo(self, file_path, sheet_name):
        all_dataframes = DataStore.get('dataframes', {})
        key = f'{file_path}:{sheet_name}' if sheet_name else file_path

        if key in all_dataframes:
            df = all_dataframes[key]

            all_original_dataframes = DataStore.get('original_dataframes', {})

            if key in all_original_dataframes:
                original_df = all_original_dataframes[key]

                # 데이터프레임 구조(인덱스와 컬럼) 비교
                if not (original_df.index.equals(df.index) and original_df.columns.equals(df.columns)):
                    print("데이터프레임 구조가 다름 (인덱스 또는 컬럼 불일치)")
                    # 구조가 다른 경우 원본 데이터프레임 업데이트
                    try:
                        # 새로운 원본 데이터로 깊은 복사 수행
                        all_original_dataframes[key] = pd.DataFrame(
                            df.values.copy(),
                            index=df.index.copy(),
                            columns=df.columns.copy()
                        )
                        DataStore.set('original_dataframes', all_original_dataframes)
                    except Exception as e:
                        print(f"원본 데이터프레임 업데이트 중 오류: {e}")
                        all_original_dataframes[key] = df.copy()
                        DataStore.set('original_dataframes', all_original_dataframes)

                    is_modified = True
                else:
                    try:
                        # 구조가 같으면 값 비교
                        is_modified = not original_df.equals(df)
                    except Exception as e:
                        print(f"데이터프레임 비교 중 오류 발생: {e}")
                        is_modified = True

                if is_modified:
                    if file_path not in self.parent.data_modifier.modified_data_dict:
                        self.parent.data_modifier.modified_data_dict[file_path] = {}

                    self.parent.data_modifier.modified_data_dict[file_path][sheet_name or 'data'] = df

                    self.parent.data_modifier.update_modified_status_in_sidebar(file_path, sheet_name)
                    self.update_tab_title(file_path, sheet_name, True)
                else:
                    if file_path in self.parent.data_modifier.modified_data_dict:
                        if sheet_name or 'data' in self.parent.data_modifier.modified_data_dict[file_path]:
                            del self.parent.data_modifier.modified_data_dict[file_path][sheet_name or 'data']

                            if not self.parent.data_modifier.modified_data_dict[file_path]:
                                del self.parent.data_modifier.modified_data_dict[file_path]

                    self.parent.data_modifier.remove_modified_status_in_sidebar(file_path, sheet_name)
                    self.update_tab_title(file_path, sheet_name, False)

                tab_key = (file_path, sheet_name)

                if tab_key in self.open_tabs:
                    tab_index = self.open_tabs[tab_key]
                    tab_widget = self.stacked_widget.widget(tab_index)

                    for i in range(tab_widget.layout().count()):
                        item = tab_widget.layout().itemAt(i)

                        if item and item.widget():
                            widget = item.widget()

                            if hasattr(widget, 'update_data'):
                                widget.update_data(df)
                                break