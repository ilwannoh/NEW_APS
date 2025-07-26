import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from app.views.components.data_upload_components.data_table_component import DataTableComponent
from app.models.common.file_store import DataStore

class DataModifier:
    """데이터 수정 관련 로직을 처리하는 클래스"""

    def __init__(self, parent):
        self.parent = parent
        self.modified_data_dict = {}

    def get_modified_data_from_tab(self, tab_widget):
        """탭 위젯에서 수정된 데이터를 가져옴"""
        # 데이터 컨테이너 찾기
        for i in range(tab_widget.layout().count()):
            widget = tab_widget.layout().itemAt(i).widget()
            if hasattr(widget, 'get_filtered_data'):
                return widget.get_filtered_data()
        return None

    def update_modified_status_in_sidebar(self, file_path, sheet_name=None):
        """사이드바에서 수정된 파일이나 시트를 표시"""
        # 파일 탐색기에서 아이템 찾기
        for i in range(self.parent.file_explorer.tree.topLevelItemCount()):
            item = self.parent.file_explorer.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == file_path:
                # 파일 아이템에 수정 표시 (빨간색 텍스트 또는 '*' 추가)
                current_text = item.text(0)
                if not current_text.endswith('*'):
                    item.setText(0, current_text + ' *')
                    item.setForeground(0, QColor("#E74C3C"))  # 빨간색으로 표시

                # 시트가 있는 경우 해당 시트 아이템에도 표시
                if sheet_name:
                    for j in range(item.childCount()):
                        sheet_item = item.child(j)
                        if sheet_item.data(0, Qt.UserRole + 1) == sheet_name:
                            sheet_text = sheet_item.text(0)
                            if not sheet_text.endswith('*'):
                                sheet_item.setText(0, sheet_text + ' *')
                                sheet_item.setForeground(0, QColor("#E74C3C"))  # 빨간색으로 표시
                            break
                break

        # 탭 제목에도 수정 표시 업데이트
        self.parent.tab_manager.update_tab_title(file_path, sheet_name, True)

    def remove_modified_status_in_sidebar(self, file_path, sheet_name=None):
        """사이드바에서 수정 표시 제거"""
        # 파일 탐색기에서 아이템 찾기
        for i in range(self.parent.file_explorer.tree.topLevelItemCount()):
            item = self.parent.file_explorer.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == file_path:
                # 파일 아이템에서 수정 표시 제거
                current_text = item.text(0)
                if current_text.endswith(' *'):
                    # 별표 제거
                    item.setText(0, current_text[:-2])

                    # 파일 타입에 따라 원래 색상으로 복원
                    if file_path.endswith(('.xls', '.xlsx')):
                        item.setForeground(0, QColor("#1D7144"))  # 엑셀 파일은 녹색
                    elif file_path.endswith('.csv'):
                        item.setForeground(0, QColor("#8B4513"))  # CSV 파일은 갈색
                    else:
                        # 기본 색상
                        item.setForeground(0, QColor("black"))

                # 시트가 있는 경우 해당 시트 아이템에서도 표시 제거
                if sheet_name:
                    for j in range(item.childCount()):
                        sheet_item = item.child(j)
                        if sheet_item.data(0, Qt.UserRole + 1) == sheet_name:
                            sheet_text = sheet_item.text(0)
                            if sheet_text.endswith(' *'):
                                # 별표 제거
                                sheet_item.setText(0, sheet_text[:-2])
                                # 색상 복원
                                sheet_item.setForeground(0, QColor("black"))
                            break

                # 다른 모든 시트가 수정되지 않았는지 확인
                all_sheets_unmodified = True
                for j in range(item.childCount()):
                    sheet_item = item.child(j)
                    if sheet_item.text(0).endswith(' *'):
                        all_sheets_unmodified = False
                        break

                # 모든 시트가 수정되지 않았다면 파일 자체도 수정 표시 제거
                if all_sheets_unmodified:
                    current_text = item.text(0)
                    if current_text.endswith(' *'):
                        item.setText(0, current_text[:-2])
                        # 파일 타입에 따라 원래 색상으로 복원
                        if file_path.endswith(('.xls', '.xlsx')):
                            item.setForeground(0, QColor("#1D7144"))
                        elif file_path.endswith('.csv'):
                            item.setForeground(0, QColor("#8B4513"))
                        else:
                            item.setForeground(0, QColor("black"))

                break

        # 탭 제목에서도 수정 표시 제거
        self.parent.tab_manager.update_tab_title(file_path, sheet_name, False)

    def update_data_store(self, file_path, sheet_name, df):
        """DataStore에 데이터프레임 저장/업데이트"""

        # 데이터프레임 저장 키 생성
        key = f"{file_path}:{sheet_name}" if sheet_name else file_path

        # 기존 데이터프레임 딕셔너리 불러오기
        df_dict = DataStore.get("dataframes", {})

        # 데이터프레임 딕셔너리 업데이트
        df_dict[key] = df

        # 업데이트된 딕셔너리 DataStore에 저장
        DataStore.set("dataframes", df_dict)

    def save_tab_data(self, tab_widget, file_path, sheet_name):
        """특정 탭의 데이터 저장"""
        modified_df = self.get_modified_data_from_tab(tab_widget)
        if modified_df is not None:
            # 원본 데이터 로드
            original_df = None
            try:
                if sheet_name:
                    original_df = DataTableComponent.load_data_from_file(file_path, sheet_name=sheet_name)
                else:
                    if file_path in self.parent.loaded_files:
                        original_df = self.parent.loaded_files[file_path].get('df')
            except Exception as e:
                print(f"원본 데이터 로드 오류: {e}")

            # 수정 여부 확인
            is_modified = False
            if original_df is not None:
                # 데이터프레임 크기 비교
                if modified_df.shape != original_df.shape:
                    is_modified = True
                else:
                    # 데이터프레임 값 비교
                    try:
                        if not modified_df.equals(original_df):
                            # 값만 비교 (데이터 타입 무시)
                            try :
                                for col in modified_df.columns :
                                    if col in original_df.columns :
                                        if not (modified_df[col].astype(str).values == original_df[col].astype(str).values).all() :
                                            is_modified = True
                                            break
                            except Exception as e :
                                modified_values = modified_df.astype(str).values
                                original_values = original_df.astype(str).values

                                try :
                                    if not (modified_values == original_values).all():
                                        is_modified = True
                                except Exception as e2 :
                                    is_modified = True
                    except Exception as e:
                        print(f"데이터 비교 중 오류 발생: {e}")
                        is_modified = False

            # 수정 여부와 관계없이 DataStore에 항상 최신 데이터프레임 저장
            self.update_data_store(file_path, sheet_name, modified_df)

            # 수정된 경우만 내부 저장소에 저장
            if is_modified:
                # 수정된 데이터 저장
                if file_path not in self.modified_data_dict:
                    self.modified_data_dict[file_path] = {}
                self.modified_data_dict[file_path][sheet_name or 'data'] = modified_df

                # 사이드바에 수정 표시 갱신
                self.update_modified_status_in_sidebar(file_path, sheet_name)

                # 분석 실행
                try:
                    self.parent.run_combined_analysis()
                except Exception as e:
                    print(f"[자동 분석 실행 오류] {e}")
            else:
                # 수정되지 않았지만 이전에 수정됨으로 표시된 경우, 표시 제거
                if (file_path in self.modified_data_dict and
                        (sheet_name or 'data') in self.modified_data_dict[file_path]):
                    # 수정 표시 제거
                    del self.modified_data_dict[file_path][sheet_name or 'data']

                    # 해당 파일에 다른 수정된 시트가 없으면 파일 자체도 제거
                    if not self.modified_data_dict[file_path]:
                        del self.modified_data_dict[file_path]

                    # 사이드바 업데이트 - 수정 표시 제거
                    self.remove_modified_status_in_sidebar(file_path, sheet_name)

    def get_all_modified_data(self):
        """모든 수정된 데이터 반환 - 현재 열린 탭의 최신 데이터 포함"""
        # 먼저 현재 탭의 데이터 저장
        current_tab_index = self.parent.tab_bar.currentIndex()
        if current_tab_index >= 0 and current_tab_index < self.parent.stacked_widget.count():
            current_tab_widget = self.parent.stacked_widget.widget(current_tab_index)
            if current_tab_widget:
                # 현재 탭에 해당하는 파일과 시트 찾기
                current_file_path = None
                current_sheet_name = None
                for (file_path, sheet_name), idx in self.parent.tab_manager.open_tabs.items():
                    if idx == current_tab_index:
                        current_file_path = file_path
                        current_sheet_name = sheet_name
                        break

                if current_file_path:
                    self.save_tab_data(current_tab_widget, current_file_path, current_sheet_name)

        # 저장된 모든 수정 데이터 반환
        return self.modified_data_dict.copy()