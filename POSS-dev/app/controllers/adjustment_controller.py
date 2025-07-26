from PyQt5.QtCore import QObject, QTimer
from typing import Any, Dict
import uuid
import pandas as pd
from app.views.components.result_components.manager.analysis_manager import AnalysisManager

"""
Controller 중심 분석 아키텍처
- Controller가 모든 분석 실행
- View/Page들은 결과만 받아서 UI 업데이트
- 구조적으로 중복 불가능
"""
class AdjustmentController(QObject):

    def __init__(self, model: Any, view: Any, error_manager):
        super().__init__()
        self.model = model
        self.view = view  # ModifiedLeftSection
        self.error_manager = error_manager
        self.result_page = None  # 명시적으로 초기화 (result_page는 외부에서 설정)

        #b 분석 매니저 생성 - 모든 분석 위임
        self.analysis_manager = None
        
        # 시그널 연결 상태만 추적 (중복 연결 방지용)
        self._signals_connected = False
        self._views_initialized = False

    """
    ResultPage 설정 및 KPI 엔진 초기화
    """
    def set_result_page(self, result_page):
        self.result_page = result_page

         # 분석 매니저에 모든 분석 위임
        self.analysis_manager = AnalysisManager(result_page, controller=self)
        print("Controller: 분석 매니저 초기화 완료")


    """
    초기 데이터로 뷰 초기화 (시그널 연결 전에 호출)
    """
    def initialize_views(self):
        # 이미 초기화된 경우 중복 초기화 방지
        if self._views_initialized:
            print("Controller: 뷰가 이미 초기화됨.")
            return False
        
        df = self.model.get_dataframe()

         # 초기화는 Controller에서 분석 후 배포
        analysis_results = self.analysis_manager.run_all_analyses(df)
        
        # View 초기화 (분석 결과와 함께)
        self.view.initialize_with_data(df, analysis_results)
        
        # ResultPage 초기화
        if self.result_page:
            self.result_page.initialize_with_data(df, analysis_results)

        # 초기화 상태 설정
        self._views_initialized = True
        
        print("Controller: 뷰 초기 데이터 설정 완료")
        return True

    """
    시그널 연결
    """
    def connect_signals(self):
         # 이미 연결된 경우 중복 연결 방지
        if self._signals_connected:
            print("Controller: 시그널이 이미 연결됨.")
            return False
        
        # 세분화된 Model 시그널들 연결
        self.model.itemAdded.connect(self._on_item_added)
        self.model.itemMoved.connect(self._on_item_moved) 
        self.model.itemDeleted.connect(self._on_item_deleted)
        self.model.quantityUpdated.connect(self._on_quantity_updated)
        
        # Model -> Controller (핵심 시그널)
        self.model.modelDataChanged.connect(self._on_model_change)   # 전체 재구성이 필요한 경우만
        self.model.validationFailed.connect(self.error_manager.add_validation_error)
        self.model.dataModified.connect(self.on_data_modified)
        
        # View -> Controller (아이템 데이터 변경)
        if hasattr(self.view, 'itemModified'):
            self.view.itemModified.connect(self._on_item_data_changed)

        # View -> Controller (아이템 삭제, 복사)
        if hasattr(self.view, 'grid_widget'):
            if hasattr(self.view.grid_widget, 'itemCopied'):
                self.view.grid_widget.itemCopied.connect(self.on_item_copied)

        # 연결 완료 상태 설정
        self._signals_connected = True        
        return True
    
    """
    모델 변경 시 - 분석 + UI 업데이트 통합 처리
    """
    def _on_model_change(self):
        
        df = self.model.get_dataframe()
        
        # 분석 매니저가 모든 분석 담당
        analysis_results = self.analysis_manager.run_all_analyses(df)
        
        # 분석 결과와 함께 UI 업데이트 요청 (재분석 없음)
        self.view.update_ui_only(df, analysis_results)
        
        if self.result_page:
            self.result_page.update_ui_only(df, analysis_results)
        
        # Error Manager 업데이트
        self.error_manager.update_error_display()


    """
    아이템 데이터 변경 처리 → Model로 전달
    - Qty만 바뀌었으면 update_qty 호출
    - Line/Time이 바뀌었으면 move_item 호출
    """
    def _on_item_data_changed(self, item: object, new_data: Dict, changed_fields=None):
        code = new_data.get('Item')
        line = new_data.get('Line')
        time = new_data.get('Time')
        item_id = new_data.get('_id')  # ID 추출
        
        if not code or not line or time is None:
            print(f"Controller: 필수 데이터 누락 - Item: {code}, Line: {line}, Time: {time}")
            return
        
        # Line/Time 변경 = 이동
        if changed_fields and ('Line' in changed_fields or 'Time' in changed_fields):

                # 이전 위치 정보 가져오기
                old_line = changed_fields.get('Line', {}).get('from', line)
                old_time = changed_fields.get('Time', {}).get('from', time)

                self.model.move_item(code, old_line, old_time, line, time, item_id)
                return
        
        # 수량 변경 - 라인과 시간 정보도 함께 전달
        elif 'Qty' in new_data and line and time is not None:
            qty = new_data['Qty']
            # 수정된 모델의 update_qty 메서드 호출 (라인, 시간 포함)
            self.model.update_qty(code, line, time, qty, item_id)

    """
    드래그·드롭으로 위치 이동했을 때 → Model로 전달
    - Controller가 모든 셀 이동 로직 처리
    - 필요시 추가 로직 (시각화 업데이트 등) 수행
    """
    def _on_cell_moved(self, item, old_data, new_data):
        code = new_data.get('Item')
        if not code:
            return
        
        if code:
            item_id = new_data.get('_id')
            old_line = old_data.get('Line')
            old_time = old_data.get('Time')
            new_line = new_data.get('Line')
            new_time = new_data.get('Time')

            self.model.move_item(code, old_line, old_time, new_line, new_time, item_id)

            # 스크롤 처리는 한 번만
            QTimer.singleShot(200, lambda: self._ensure_item_visible(item_id))
            print(f"셀 이동 후 스크롤 예약됨: ID={item_id}")

    """
    복사된 아이템 처리 → Model로 전달

    parameter:
        item: 복사된 아이템 위젯
        data: 아이템 데이터가 포함된 딕셔너리
    """
    def on_item_copied(self, item, data):
        print(f"컨트롤러가 복사 아이템 처리 중: {data.get('Item')} @ {data.get('Line')}-{data.get('Time')}")

        # 필수 정보 추출
        code = data.get('Item')
        line = data.get('Line')
        time = data.get('Time')

        # 필수 데이터 검증
        if not code or not line or time is None:
            print(f"Controller: 복사 시 필수 데이터 누락 - Item: {code}, Line: {line}, Time: {time}")
            return

        # 복사된 항목임을 표시하는 플래그 추가
        if '_is_copy' not in data:
            data['_is_copy'] = True

        # 새로운 ID 생성 (중복 방지)
        data['_id'] = str(uuid.uuid4())
        print(f"Controller: 복사용 새 ID 생성: {data['_id']}")
            
        # 모델에 명시적으로 추가 - 기본적으로 수량은 0으로 설정
        qty = data.get('Qty', 0)
        self.model.add_new_item(code, line, time, qty, data)

    
    """
    아이템 추가 - UI에 해당 아이템만 추가 (전체 재구성 없음)
    """
    def _on_item_added(self, item_data):
        print(f"Controller: 아이템 추가 - {item_data.get('Item')} @ {item_data.get('Line')}-{item_data.get('Time')}")
        
         # UI에 아이템만 추가 (스크롤 위치 유지됨)
        self._add_item_to_ui(item_data)
        
        # 2. 분석 실행
        self._run_complete_analysis("아이템 이동")

    """
    아이템 이동 - UI에서 해당 아이템만 이동 (전체 재구성 없음)
    """
    def _on_item_moved(self, old_data, new_data):
        print(f"Controller: 아이템 이동 - {new_data.get('Item')} @ {old_data.get('Line')}-{old_data.get('Time')} -> {new_data.get('Line')}-{new_data.get('Time')}")

        # 스크롤 처리
        item_id = new_data.get('_id')
        if item_id:
            QTimer.singleShot(200, lambda: self._ensure_item_visible(item_id))

        # 2. 분석 실행
        self._run_complete_analysis("아이템 이동")

    """
    수량 변경 - UI에서 해당 아이템 텍스트만 업데이트 (전체 재구성 없음)
    """
    def _on_quantity_updated(self, item_data):
        print(f"Controller: quantityUpdated 시그널 수신됨!")
        
        # 1. UI 업데이트
        self._update_item_ui_immediately(item_data)
        
        # 2. 전체 분석 및 차트 업데이트 
        self._run_complete_analysis("수량 변경")


    """
    아이템 삭제 - UI에서 해당 아이템만 제거 (전체 재구성 없음)
    """
    def _on_item_deleted(self, item_id):
        print(f"Controller: 아이템 삭제 - ID: {item_id}")
    
        # 완전한 분석 
        self._run_complete_analysis("아이템 삭제")

    """
    UI에 아이템만 추가
    """
    def _add_item_to_ui(self, item_data):
        try:
            line = item_data.get('Line')
            time = int(item_data.get('Time'))
            item_code = item_data.get('Item')
            qty = item_data.get('Qty', 0)
            
            # 해당 위치의 컨테이너 찾기
            row_idx, col_idx = self._find_container_position(line, time)
            if row_idx >= 0 and col_idx >= 0:
                # 아이템 텍스트 생성 (공백 4개)
                item_text = f"{item_code}    {qty}" if qty > 0 else item_code
                
                # 해당 컨테이너에 아이템 추가
                new_item = self.view.grid_widget.addItemAt(row_idx, col_idx, item_text, item_data)

                if new_item:
                    # 상태 복원 (사전할당, 자재부족 등)
                    self._restore_item_states(new_item, item_data)

                    # 현재 범례 필터 상태 적용
                    if hasattr(self.view, 'current_filter_states'):
                        filter_states = self.view.current_filter_states
                        new_item.show_shortage_line = filter_states.get('shortage', False)
                        new_item.show_shipment_line = filter_states.get('shipment', False)
                        new_item.show_pre_assigned_line = filter_states.get('pre_assigned', False)
                        new_item.update()

                    print(f"UI에 아이템 추가 완료: {item_code} @ {line}-{time}")
                else:
                    print(f"Controller: UI 아이템 추가 실패")
        except Exception as e:
            print(f"UI 아이템 추가 중 오류: {e}")

    """
    UI만 즉시 업데이트 (분석 없음)
    """
    def _update_item_ui_immediately(self, item_data):
        item_id = item_data.get('_id')
        if item_id:
            item_widget = self._find_item_widget_by_id(item_id)
            if item_widget:
                item_widget.item_data.update(item_data)
                item_widget.update_text_from_data()
                print("UI 텍스트 업데이트 완료")

    """
    완전한 분석 - 모든 것을 한 번에
    """
    def _run_complete_analysis(self, trigger_reason):
        print(f"완전한 분석 시작 - {trigger_reason}")
        
        try:
            # 1. 현재 데이터로 전체 재분석
            current_df = self.model.get_dataframe()
            if current_df is None or current_df.empty:
                return
            
            # 2. AnalysisManager로 모든 분석 실행
            analysis_results = self.analysis_manager.run_all_analyses(current_df)
            
            # 3. 모든 결과를 UI에 반영
            self._apply_all_analysis_results(analysis_results)
            
            # 4. 에러 상태 업데이트
            self.error_manager.update_error_display()
            
            print("완전한 분석 완료")
            
        except Exception as e:
            print(f"분석 중 오류: {e}")

    """
    분석 결과를 모든 UI에 적용
    """
    def _apply_all_analysis_results(self, analysis_results):
        
        # 1. KPI 업데이트
        if 'kpi' in analysis_results and self.result_page:
            kpi_data = analysis_results['kpi']
            self.result_page.kpi_widget.update_scores(
                base_scores=kpi_data.get('base_scores', {}),
                adjust_scores=kpi_data.get('adjust_scores', {})
            )
            print("KPI 업데이트")
        
        # 2. 차트 데이터 설정
        if self.result_page:
            if 'capa_ratio' in analysis_results:
                self.result_page.capa_ratio_data = analysis_results['capa_ratio']
            if 'utilization' in analysis_results:
                self.result_page.utilization_data = analysis_results['utilization']
            
            # 3. 모든 차트 업데이트
            self.result_page.update_all_visualizations()
        
        # 4. 자재부족/출하실패 상태를 아이템에 적용
        self._apply_status_to_items(analysis_results)
    
    """
    분석 결과를 개별 아이템에 상태로 적용
    """
    def _apply_status_to_items(self, analysis_results):
        
        # 자재부족 상태 적용
        if 'material' in analysis_results and hasattr(self.view, 'set_current_shortage_items'):
            shortage_results = analysis_results['material'].get('shortage_results', {})
            self.view.set_current_shortage_items(shortage_results)
            print("자재부족 상태 적용")
        
        # 출하실패 상태 적용
        if 'shipment' in analysis_results and hasattr(self.view, 'set_shipment_failure_items'):
            shipment_data = analysis_results['shipment']
            if shipment_data.get('analyzed'):
                failure_items = shipment_data.get('failure_items', {})
                self.view.set_shipment_failure_items(failure_items)
                print("출하실패 상태 적용")

    """
    전체 데이터 변경 - 전체 UI 재구성 필요 (리셋, 새 파일 로드 등)
    """
    def _on_full_data_change(self):
        print("Controller: 전체 데이터 변경 - UI 전체 재구성")
        
        df = self.model.get_dataframe()
        analysis_results = self._run_all_analyses(df)
        
        # 전체 UI 업데이트
        self.view.update_ui_only(df, analysis_results)
        if self.result_page:
            self.result_page.update_ui_only(df, analysis_results)
        
        self.error_manager.update_error_display()

    """
    아이템 ID를 기반으로 해당 아이템으로 스크롤
    """
    def _ensure_item_visible(self, item_id):
        if not item_id or not hasattr(self.view, 'grid_widget'):
            return

        # 뷰의 _scroll_to_selected_item 메서드 호출
        if hasattr(self.view, '_scroll_to_selected_item'):
            self.view._scroll_to_selected_item(item_id)


    """
    라인과 시간으로 컨테이너 위치 찾기
    """
    def _find_container_position(self, line, time):
        try:
            # 교대 계산
            shift = "Day" if int(time) % 2 == 1 else "Night"
            row_key = f"{line}_({shift})"
            
            # 행 인덱스 찾기
            row_idx = -1
            if hasattr(self.view.grid_widget, 'row_headers'):
                try:
                    row_idx = self.view.grid_widget.row_headers.index(row_key)
                except ValueError:
                    pass
            
            # 열 인덱스 계산 (요일)
            col_idx = (int(time) - 1) // 2
            
            return row_idx, col_idx
        except:
            return -1, -1
        
    """
    ID로 아이템 위젯 찾기
    """
    def _find_item_widget_by_id(self, item_id):
        try:
            if not hasattr(self.view.grid_widget, 'containers'):
                return None
                
            for row_containers in self.view.grid_widget.containers:
                for container in row_containers:
                    for item in container.items:
                        if (hasattr(item, 'item_data') and 
                            item.item_data and 
                            item.item_data.get('_id') == item_id):
                            return item
        except:
            pass
        return None
    
    """
    아이템 상태 복원 (사전할당, 자재부족 등)
    """
    def _restore_item_states(self, item_widget, item_data):
        # ResultPage의 상태 복원 로직 재사용
        if self.result_page:
            item_code = item_data.get('Item', '')
            
            # 사전할당 상태
            if hasattr(self.result_page, 'pre_assigned_items') and item_code in self.result_page.pre_assigned_items:
                item_widget.set_pre_assigned_status(True)
                
            # 자재부족 상태  
            if (hasattr(self.result_page, 'material_analyzer') and 
                self.result_page.material_analyzer and
                hasattr(self.result_page.material_analyzer, 'shortage_results')):
                shortage_results = self.result_page.material_analyzer.shortage_results
                if item_code in shortage_results:
                    item_widget.set_shortage_status(True, shortage_results[item_code])

    """
    추가된 아이템의 분석 상태 업데이트 (자재부족, 사전할당 등)
    """
    def _update_item_analysis_status(self, item_data):
        try:
            item_id = item_data.get('_id')
            item_widget = self._find_item_widget_by_id(item_id) if item_id else None
            
            if item_widget and self.result_page:
                item_code = item_data.get('Item', '')
                
                # 자재 부족 상태 확인 및 적용
                if (hasattr(self.result_page, 'material_analyzer') and 
                    self.result_page.material_analyzer and
                    hasattr(self.result_page.material_analyzer, 'shortage_results')):
                    
                    shortage_results = self.result_page.material_analyzer.shortage_results
                    if item_code in shortage_results:
                        # 시프트별 부족 정보 확인
                        item_time = item_data.get('Time')
                        matching_shortages = []
                        
                        for shortage in shortage_results[item_code]:
                            shortage_shift = shortage.get('shift')
                            if shortage_shift and item_time and int(shortage_shift) == int(item_time):
                                matching_shortages.append(shortage)
                        
                        if matching_shortages:
                            item_widget.set_shortage_status(True, matching_shortages)
                
                # 사전할당 상태 확인 및 적용
                if hasattr(self.result_page, 'pre_assigned_items') and item_code in self.result_page.pre_assigned_items:
                    item_widget.set_pre_assigned_status(True)
                    
        except Exception as e:
            print(f"아이템 분석 상태 업데이트 중 오류: {e}")

    """
    모델 데이터의 변경 상태에 따라 리셋 버튼 상태 업데이트
    """
    def on_data_modified(self, has_changes: bool):
        if hasattr(self.view, 'reset_button'):
            self.view.reset_button.setEnabled(has_changes)

    """
    재 모델 데이터 반환
    """
    def get_current_data(self):
        return self.model.get_dataframe()

    """
    데이터 리셋
    """
    def reset_data(self):
        self.model.reset()

    """
    변경사항 적용
    """
    def apply_changes(self):
        self.model.apply()

    """
    모델을 완전히 새로운 데이터로 업데이트

    parameter:
        new_data: 사용할 새 데이터가 포함된 DataFrame
    """
    def update_model_data(self, new_df: pd.DataFrame) -> bool:
        if hasattr(self.model, 'set_new_dataframe'):
            self.model.set_new_dataframe(new_df)
            return True
        else:
            print("Controller: model이 set_new_dataframe을 지원하지 않음")
            return False


   