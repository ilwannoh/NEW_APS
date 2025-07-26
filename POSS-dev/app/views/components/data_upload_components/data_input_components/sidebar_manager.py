import os
import pandas as pd
from PyQt5.QtCore import Qt

from app.views.components.data_upload_components.data_table_component import DataTableComponent

"""
사이드바 관리를 위한 클래스
파일 탐색기 사이드바와 파일 데이터 로딩 담당
"""
class SidebarManager:
    def __init__(self, parent):
        self.parent = parent
        self.file_explorer = parent.file_explorer
        self.updating_from_sidebar = False

    """파일을 사이드바에 추가하고 DataStore에 등록"""
    def add_file_to_sidebar(self, file_path):
        # 파일 확장자 확인
        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            # 엑셀 파일인 경우 시트 목록 가져오기
            sheet_names = None
            if file_ext in ['.xls', '.xlsx']:
                excel = pd.ExcelFile(file_path)
                sheet_names = excel.sheet_names

                # 모든 시트 로드하여 저장
                from app.models.common.file_store import DataStore
                df_dict = DataStore.get("dataframes", {})

                # 첫 번째 시트는 기본값으로 로드
                if sheet_names:
                    first_sheet = sheet_names[0]
                    df = DataTableComponent.load_data_from_file(file_path, sheet_name=first_sheet)
                    self.parent.loaded_files[file_path] = {
                        'df': df,
                        'sheets': sheet_names,
                        'current_sheet': first_sheet
                    }
                    df_dict[f"{file_path}:{first_sheet}"] = df

                    # 다른 모든 시트도 로드하여 저장
                    for sheet in sheet_names[1:]:
                        sheet_df = DataTableComponent.load_data_from_file(file_path, sheet_name=sheet)
                        df_dict[f"{file_path}:{sheet}"] = sheet_df

                    DataStore.set("dataframes", df_dict)

            # CSV 파일인 경우
            elif file_ext == '.csv':
                df = DataTableComponent.load_data_from_file(file_path)
                self.parent.loaded_files[file_path] = {
                    'df': df,
                    'sheets': None,
                    'current_sheet': None
                }

                # DataStore에 등록
                from app.models.common.file_store import DataStore
                df_dict = DataStore.get("dataframes", {})
                df_dict[file_path] = df
                DataStore.set("dataframes", df_dict)

            # 파일 탐색기에 파일 추가
            self.file_explorer.add_file(file_path, sheet_names)

            # 첫 번째 파일인 경우 자동 선택
            if len(self.parent.loaded_files) == 1:
                self.file_explorer.select_first_item()

            return True, f"파일 '{os.path.basename(file_path)}'이(가) 로드되었습니다"

        except Exception as e:
            return False, f"파일 로드 오류: {str(e)}"

    """사이드바에서 파일 제거 및 관련 데이터 정리"""
    def remove_file_from_sidebar(self, file_path):
        # 사이드바에서 파일 제거
        result = self.file_explorer.remove_file(file_path)

        # 로드된 파일 목록에서 제거
        if file_path in self.parent.loaded_files:
            del self.parent.loaded_files[file_path]

        # 수정된 데이터 목록에서도 제거
        if file_path in self.parent.data_modifier.modified_data_dict:
            del self.parent.data_modifier.modified_data_dict[file_path]

        # DataStore에서 해당 파일 관련 데이터만 제거
        self._clear_file_related_datastore(file_path)

        # FilePaths에서 해당 경로 제거
        self._clear_file_paths(file_path)

        # 현재 표시 중인 파일이 제거된 경우, 화면 초기화
        if self.parent.current_file == file_path:
            self.parent.current_file = None
            self.parent.current_sheet = None

        return result

    """파일과 관련된 DataStore 데이터 정리"""
    def _clear_file_related_datastore(self, file_path):
        from app.models.common.file_store import DataStore

        # 1. dataframes 정리
        df_dict = DataStore.get("dataframes", {})
        keys_to_remove = [key for key in df_dict.keys()
                          if key == file_path or key.startswith(f"{file_path}:")]
        for key in keys_to_remove:
            del df_dict[key]
        DataStore.set("dataframes", df_dict)

        # 2. original_dataframes 정리
        original_df_dict = DataStore.get('original_dataframes', {})
        keys_to_remove = [key for key in original_df_dict.keys()
                          if key == file_path or key.startswith(f"{file_path}:")]
        for key in keys_to_remove:
            del original_df_dict[key]
        DataStore.set('original_dataframes', original_df_dict)

        # 3. 파일 타입별 처리
        file_name = os.path.basename(file_path).lower()

        # 핵심 파일이 삭제된 경우 관련 분석 데이터 모두 정리
        if any(keyword in file_name for keyword in ['demand', 'dynamic', 'master']):
            DataStore.delete('organized_dataframes')
            DataStore.delete('optimization_result')

        # dynamic 파일이 삭제된 경우 maintenance 관련 데이터 정리
        if 'dynamic' in file_name:
            DataStore.delete('maintenance_thresholds_items')
            DataStore.delete('maintenance_thresholds_rmcs')

    """FilePaths에서 해당 파일 경로 제거"""
    def _clear_file_paths(self, file_path):
        from app.models.common.file_store import FilePaths

        # 현재 등록된 경로들 확인하고 일치하는 것 제거
        path_keys = [
            "demand_excel_file", "dynamic_excel_file", "master_excel_file",
            "pre_assign_excel_file", "etc_excel_file", "result_file"
        ]

        for key in path_keys:
            if FilePaths.get(key) == file_path:
                FilePaths.set(key, None)

    """
    파일 탐색기에서 파일이나 시트 선택 처리
    선택된 항목을 탭으로 표시하거나 기존 탭 활성화
    """
    def on_file_or_sheet_selected(self, file_path, sheet_name):
        # 탭으로부터의 업데이트 중이면 무시 (무한 루프 방지)
        if self.parent.tab_manager.updating_from_tab:
            return

        self.updating_from_sidebar = True

        # 파일이 로드되지 않은 경우
        if file_path not in self.parent.loaded_files:
            self.updating_from_sidebar = False
            return

        self.parent.current_file = file_path
        file_info = self.parent.loaded_files[file_path]

        # 시트 이름 결정
        if sheet_name and file_info['sheets'] and sheet_name in file_info['sheets']:
            self.parent.current_sheet = sheet_name
        else:
            # 시트를 명시적으로 선택하지 않은 경우 (파일만 선택)
            if file_info.get('sheets'):
                # 엑셀 파일이고 시트가 있는 경우 기본값 설정
                self.parent.current_sheet = file_info.get('current_sheet') or file_info['sheets'][0]
            else:
                # CSV 파일인 경우
                self.parent.current_sheet = None

        # 해당 탭이 이미 열려 있는지 확인
        tab_key = (file_path, self.parent.current_sheet)
        if tab_key in self.parent.tab_manager.open_tabs:
            # 이미 열려 있는 탭으로 전환
            self.parent.tab_bar.setCurrentIndex(self.parent.tab_manager.open_tabs[tab_key])
        else:
            # Start Page 탭이 있고 이것이 첫 번째 컨텐츠 탭인지 확인
            if self.parent.tab_bar.count() == 1 and self.parent.tab_bar.tabText(0) == "Start Page":
                # Start Page 제거
                self.parent.tab_manager.remove_start_page()

            # 새 탭 생성 - 수정된 데이터 사용
            self.parent.tab_manager.create_new_tab(file_path, self.parent.current_sheet)

        self.updating_from_sidebar = False

    def get_loaded_sheet_names(self, file_path):
        """로드된 파일의 시트 이름 목록 반환"""
        if file_path in self.parent.loaded_files:
            return self.parent.loaded_files[file_path].get('sheets', [])
        return []