from PyQt5.QtCore import QObject, QTimer
import pandas as pd
from app.utils.item_key_manager import ItemKeyManager

"""
데이터 관련 로직 담당
"""
class DataManager(QObject):
    def __init__(self, left_section):
        super().__init__()
        self.left_section = left_section
        
    def on_item_data_changed(self, item, new_data, changed_fields=None):
        if not item or not new_data or not hasattr(item, 'item_data'):
            print("아이템 또는 데이터가 없음")
            return

        # 현재 아이템의 원래 위치 정보 확인
        original_data = item.item_data.copy() if hasattr(item, 'item_data') else {}

        # 위치 정보가 변경되지 않았다면 원래 위치 정보 사용
        if changed_fields and 'Line' not in changed_fields and 'Time' not in changed_fields:
            new_data['Line'] = original_data.get('Line', new_data.get('Line'))
            new_data['Time'] = original_data.get('Time', new_data.get('Time'))

        # MVC 모드: Controller에 위임
        if (hasattr(self.left_section, '_mvc_mode') and 
            self.left_section._mvc_mode and 
            hasattr(self.left_section, 'controller') and 
            self.left_section.controller):
            
            self.left_section.itemModified.emit(item, new_data, changed_fields)
            # 분석은 Controller가 담당
            return

        # Legacy 모드: 기존 방식
        self._legacy_item_changed(item, new_data, changed_fields)

    def _legacy_item_changed(self, item, new_data, changed_fields):
        """Legacy 모드 아이템 변경 처리"""
        # 기존 로직 유지
        if hasattr(self.left_section, 'parent_page') and self.left_section.parent_page:
            self.left_section.itemModified.emit(item, new_data, changed_fields)
            self._trigger_analysis()
        
    """
    전체 데이터 새로고침 
    - ResultPage의 on_data_changed 활용
    """
    def trigger_full_data_refresh(self):
        current_data = self.left_section.extract_dataframe()
        
        # ResultPage의 on_data_changed 호출하여 전체 UI 업데이트
        if (hasattr(self.left_section, 'parent_page') and 
            self.left_section.parent_page and 
            hasattr(self.left_section.parent_page, 'on_data_changed')):
            
            print("DataManager: ResultPage.on_data_changed 호출")
            self.left_section.parent_page.on_data_changed(current_data)
        
    def _trigger_analysis(self):
        if hasattr(self.left_section, 'parent_page') and self.left_section.parent_page:
            current_data = self.left_section.extract_dataframe()
        
            # 분산 배치 분석 요청 - SplitView 업데이트
            if hasattr(self.left_section.parent_page, 'update_split_view_analysis'):
                print("DataManager: 분산 배치 분석 실행")
                self.left_section.parent_page.update_split_view_analysis(current_data)

    """
    Legacy 모드 테이블 업데이트
    """
    def update_table_from_data(self):
        if self.left_section.data is None:
            return

        self.left_section.update_ui_with_signals()

        # Legacy 모드에서만 시그널 발생
        if not (hasattr(self.left_section, '_mvc_mode') and self.left_section._mvc_mode):
            df = self.left_section.extract_dataframe()
            self.left_section.viewDataChanged.emit(df)
            self.preload_analyses()
            self._trigger_analysis_legacy()


    """
    Legacy 모드 사전 분석
    """
    def preload_analyses(self):
        # 데이터가 없으면 건너뜀
        if self.left_section.data is None or self.left_section.data.empty:
            return
            
        # 결과 페이지 참조 확인
        result_page = self.left_section.parent_page
        if not result_page:
            return
            
        try:    
            # 범례에도 필터 상태 업데이트 알림
            if hasattr(self.left_section, 'legend_widget'):
                # 현재 필터 상태 가져오기
                current_states = self.left_section.legend_widget.filter_states
                
                # 강제로 필터 변경 이벤트 재발생
                self.left_section.on_filter_changed_dict(current_states)
        except Exception as e:
            print(f"사전 분석 초기화 중 오류: {e}")
    

    """
    필터 데이터 업데이트 (Left Section 전용)
    """
    def handle_filter_data_update(self):
        self.left_section.update_filter_data()

    """
    새로 생성된 아이템 등록
    """
    def register_item(self, item):
        if item not in self.left_section.all_items:
            self.left_section.all_items.append(item)

            # 검색이 활성화되어 있으면 해당 아이템에 검색 적용
            if self.left_section.search_widget.is_search_active():
                search_text = self.left_section.search_widget.get_search_text()
                if search_text:
                    self.apply_search_to_item(item, search_text)
                    
    """
    아이템에 검색 조건 적용
    """
    def apply_search_to_item(self, item, search_text):
        try:
            if not item or not hasattr(item, 'item_data') or not item.item_data:
                return False

            try:
                _ = item.isVisible()
            except RuntimeError:
                if item in self.left_section.all_items:
                    self.left_section.all_items.remove(item)
                return False

            item_code = str(item.item_data.get('Item', '')).lower()
            is_match = search_text in item_code

            if hasattr(item, 'set_search_focus'):
                current_focus = getattr(item, 'is_search_focused', False)
                if current_focus != is_match:
                    item.set_search_focus(is_match)

            return is_match
        except RuntimeError:
            return False
        except Exception as e:
            print(f"아이템 검색 중 오류: {e}")
            return False


    """
    아이템 삭제 처리 메서드 (ItemContainer에서 발생한 삭제를 처리)
    """
    def on_item_removed(self, item_or_id):
        # MVC 모드에서는 Controller가 처리
        if (hasattr(self.left_section, '_mvc_mode') and 
            self.left_section._mvc_mode and 
            hasattr(self.left_section, 'controller') and 
            self.left_section.controller):
            return
        
        # Legacy 모드에서만 직접 처리
        if self.left_section.data is None:
            print("DEBUG: 데이터가 없음")
            return
        
        # item_or_id가 문자열(ID)인 경우
        if isinstance(item_or_id, str):
            item_id = item_or_id

            mask = ItemKeyManager.create_mask_by_id(self.left_section.data, item_id)
            if mask.any():
                self.left_section.data = self.left_section.data[~mask].reset_index(drop=True)
                df = self.left_section.extract_dataframe()
                self.left_section.viewDataChanged.emit(df)
                self.mark_as_modified()

                self._trigger_analysis()
            else:
                print(f"DEBUG: ID {item_id}로 아이템을 찾을 수 없음")
            return
        
        # item_or_id가 아이템 객체인 경우
        if hasattr(item_or_id, 'item_data') and item_or_id.item_data:
            # ID가 있으면 ID로 찾기
            item_id = ItemKeyManager.extract_item_id(item_or_id)
            if item_id:
                mask = ItemKeyManager.create_mask_by_id(self.left_section.data, item_id)
                if mask.any():
                    self.left_section.data = self.left_section.data[~mask].reset_index(drop=True)
                    df = self.left_section.extract_dataframe()
                    self.left_section.viewDataChanged.emit(df)
                    self.mark_as_modified()
                    return
            
            # ID가 없으면 Line/Time/Item으로 찾기
            line, time, item_code = ItemKeyManager.get_item_from_data(item_or_id.item_data)
            if line is not None and time is not None and item_code is not None:
                mask = ItemKeyManager.create_mask_for_item(self.left_section.data, line, time, item_code)
                if mask.any():
                    self.left_section.data = self.left_section.data[~mask].reset_index(drop=True)
                    df = self.left_section.extract_dataframe()
                    self.left_section.viewDataChanged.emit(df)
                    self.mark_as_modified()
                else:
                    print(f"DEBUG: Line/Time/Item으로 아이템을 찾을 수 없음")
        else:
            print("DEBUG: 유효하지 않은 아이템 객체")

        # 처리 완료 후 출하 분석 업데이트
        df = self.left_section.extract_dataframe()
        self.left_section.viewDataChanged.emit(df)
        self.mark_as_modified()
        
        # 출하 분석 업데이트 요청
        self._trigger_analysis()

    """
    복사된 아이템 처리
    """
    def on_item_copied(self, item, data):
        # 아이템 등록
        self.register_item(item)

        # 데이터 처리는 제거 - 이미 컨트롤러에서 처리함
        # MVC 패턴에서는 뷰는 UI 렌더링만 담당, 데이터 처리는 컨트롤러에서
        
        # MVC 모드에서는 Controller가 데이터 처리
        if not (hasattr(self.left_section, '_mvc_mode') and self.left_section._mvc_mode):
            # Legacy 모드에서만 직접 처리
            df = self.left_section.extract_dataframe()
            self.left_section.viewDataChanged.emit(df)

            self._trigger_analysis()

    """
    데이터가 수정되었음을 표시하는 메서드
    """
    def mark_as_modified(self):
        self.left_section.reset_button.setEnabled(True)

    """
    외부에서 데이터 설정
    """
    def set_data_from_external(self, new_data):
        self.left_section.data = self.left_section._normalize_data_types(new_data.copy())
        self.left_section.original_data = self.left_section.data.copy()
        
        # MVC/Legacy 모드에 따라 처리
        if (hasattr(self.left_section, '_mvc_mode') and 
            self.left_section._mvc_mode):
            self.left_section.update_ui_with_signals()  # 시그널 억제
        else:
            self.update_table_from_data()  # 기존 방식

    """
    모델로부터 UI 업데이트 - 이벤트 발생시키지 않음
    """
    def update_from_model(self, model_df=None):
        # MVC 모드: UI만 업데이트 (분석 없음)
        if (hasattr(self.left_section, '_mvc_mode') and
                self.left_section._mvc_mode):
            self._mvc_update_ui_only(model_df)
        else:
            self._legacy_full_update(model_df)

    """
    MVC 모드: UI만 업데이트
    """
    def _mvc_update_ui_only(self, model_df):
        if model_df is not None and not model_df.empty:
            # 스크롤 위치 저장
            scroll_position = self._save_scroll_position()

            # 데이터 설정 - MVC 모드에서는 controller 데이터를 우선 사용
            if hasattr(self.left_section, 'controller') and self.left_section.controller:
                self.left_section.data = self.left_section.controller.get_current_data()
            else:
                self.left_section.data = model_df

            # UI 업데이트만 (시그널 억제)
            self.left_section.update_ui_with_signals()
            self.left_section.apply_all_filters()

            # 스크롤 위치 복원
            self._restore_scroll_position(scroll_position)

    """
    Legacy 모드: 분석 포함 전체 업데이트
    """
    def _legacy_full_update(self, model_df):
        # 기존 복잡한 로직 (변경 없음)
        current_selected_item_id = None
        if self.left_section.current_selected_item and hasattr(self.left_section.current_selected_item, 'item_data'):
            current_selected_item_id = self.left_section.current_selected_item.item_data.get('_id')

        # 현재 상태 백업
        current_search_active = self.left_section.search_widget.is_search_active()
        current_search_text = self.left_section.search_widget.get_search_text()
        current_filter_states = self.left_section.current_filter_states.copy()
        current_excel_filter_states = self.left_section.current_excel_filter_states.copy()
        
        # 스크롤 위치 저장
        scroll_position = self._save_scroll_position()

        # 데이터 가져오기
        if model_df is None:
            if hasattr(self.left_section, 'controller') and self.left_section.controller:
                model_df = self.left_section.controller.model.get_dataframe()

        if model_df is None:
            return

        # 데이터 업데이트 및 UI 재구성
        self.left_section.data = self.left_section._normalize_data_types(model_df.copy())
        self.left_section.update_ui_with_signals()  # viewDataChanged 발생
        
        # 상태 복원
        self.left_section.current_filter_states = current_filter_states
        self.left_section.current_excel_filter_states = current_excel_filter_states
        
        # 필터 재적용
        if any(v for k, v in current_filter_states.items()):
            self.left_section.apply_all_filters()
        
        # 검색 상태 복원
        if current_search_active and current_search_text:
            self.left_section.search_widget.last_search_text = current_search_text
            self.left_section.search_widget.search_active = True
            self.left_section.search_widget.clear_button.setEnabled(True)
            self.left_section.search_manager.search_items(current_search_text)
        
        # 스크롤 위치 복원
        self._restore_scroll_position(scroll_position)
        
        # Legacy 모드에서만 분석 실행
        self._trigger_analysis()

    """
    스크롤 위치 저장
    """
    def _save_scroll_position(self):
        try:
            if hasattr(self.left_section, 'grid_widget') and hasattr(self.left_section.grid_widget, 'scroll_area'):
                h_bar = self.left_section.grid_widget.scroll_area.horizontalScrollBar()
                v_bar = self.left_section.grid_widget.scroll_area.verticalScrollBar()
                return {
                    'horizontal': h_bar.value(),
                    'vertical': v_bar.value()
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
            if hasattr(self.left_section, 'grid_widget') and hasattr(self.left_section.grid_widget, 'scroll_area'):
                h_bar = self.left_section.grid_widget.scroll_area.horizontalScrollBar()
                v_bar = self.left_section.grid_widget.scroll_area.verticalScrollBar()
                
                QTimer.singleShot(50, lambda: h_bar.setValue(position['horizontal']))
                QTimer.singleShot(50, lambda: v_bar.setValue(position['vertical']))
        except:
            pass



    

