"""
필터링 파이프라인 시스템
- 복잡한 조건 분기를 단순한 파이프라인으로 변환
- 각 필터를 독립적인 함수로 분리하여 유지보수성 향상
"""

from typing import List, Callable, Any, Dict
import pandas as pd


class FilterPipeline:
    """
    필터링 파이프라인 클래스
    - 여러 필터를 순차적으로 적용
    - 각 필터는 독립적인 함수로 구현
    """

    def __init__(self):
        self.filters: List[Callable] = []
        self.debug_mode = False

    def add_filter(self, filter_func: Callable, name: str = None):
        """필터 함수 추가"""
        if name:
            filter_func._filter_name = name
        self.filters.append(filter_func)
        return self

    def set_debug(self, debug: bool = True):
        """디버그 모드 설정"""
        self.debug_mode = debug
        return self

    def apply(self, items: List, context: Dict = None) -> List:
        """파이프라인의 모든 필터를 순차적으로 적용"""
        if context is None:
            context = {}

        result = items

        for i, filter_func in enumerate(self.filters):
            if self.debug_mode:
                filter_name = getattr(filter_func, '_filter_name', f'Filter_{i}')
                input_count = len(result) if hasattr(result, '__len__') else '?'

            try:
                result = filter_func(result, context)

                if self.debug_mode:
                    output_count = len(result) if hasattr(result, '__len__') else '?'
                    print(f"[파이프라인] {filter_name}: {input_count} → {output_count}")

            except Exception as e:
                if self.debug_mode:
                    print(f"[파이프라인] {filter_name} 오류: {e}")
                continue

        return result

    def clear(self):
        """모든 필터 제거"""
        self.filters.clear()
        return self


class ItemFilterFactory:
    """
    아이템 필터 생성 팩토리
    - 일반적인 필터링 조건들을 미리 정의된 함수로 제공
    """

    @staticmethod
    def create_line_filter(active_lines: List[str]):
        """라인 필터 생성"""

        def line_filter(items: List, context: Dict) -> List:
            if not active_lines:
                return items

            filtered_items = []
            for item in items:
                try:
                    if hasattr(item, 'item_data') and item.item_data:
                        item_line = str(item.item_data.get('Line', ''))
                        if item_line in active_lines:
                            filtered_items.append(item)
                except (RuntimeError, AttributeError):
                    # 삭제된 위젯 무시
                    continue
            return filtered_items

        line_filter._filter_name = f"LineFilter({len(active_lines)}개)"
        return line_filter

    @staticmethod
    def create_project_filter(active_projects: List[str]):
        """프로젝트 필터 생성"""

        def project_filter(items: List, context: Dict) -> List:
            if not active_projects:
                return items

            filtered_items = []
            for item in items:
                try:
                    if hasattr(item, 'item_data') and item.item_data:
                        project = item.item_data.get('Project')
                        if pd.isna(project):
                            project = "N/A"
                        else:
                            project = str(project)

                        if project in active_projects:
                            filtered_items.append(item)
                except (RuntimeError, AttributeError):
                    continue
            return filtered_items

        project_filter._filter_name = f"ProjectFilter({len(active_projects)}개)"
        return project_filter

    @staticmethod
    def create_status_line_filter(filter_states: Dict[str, bool]):
        """상태선 필터 생성 (범례 필터)"""

        def status_line_filter(items: List, context: Dict) -> List:
            shortage_filter = filter_states.get('shortage', False)
            shipment_filter = filter_states.get('shipment', False)
            pre_assigned_filter = filter_states.get('pre_assigned', False)

            # 모든 필터가 꺼져 있으면 모든 아이템 표시
            if not any(filter_states.values()):
                for item in items:
                    try:
                        # 상태선만 업데이트하고 가시성은 유지
                        ItemFilterFactory._update_status_lines(item, filter_states)
                    except (RuntimeError, AttributeError):
                        continue
                return items

            # 활성화된 필터가 있는 경우 상태선 업데이트
            for item in items:
                try:
                    ItemFilterFactory._update_status_lines(item, filter_states)
                except (RuntimeError, AttributeError):
                    continue

            return items

        active_count = sum(1 for v in filter_states.values() if v)
        status_line_filter._filter_name = f"StatusLineFilter({active_count}개 활성)"
        return status_line_filter

    @staticmethod
    def create_search_filter(search_text: str):
        """검색 필터 생성"""

        def search_filter(items: List, context: Dict) -> List:
            if not search_text:
                return items

            search_text_lower = search_text.lower()
            matched_items = []

            for item in items:
                try:
                    if hasattr(item, 'item_data') and item.item_data:
                        item_code = str(item.item_data.get('Item', '')).lower()
                        is_match = search_text_lower in item_code

                        # 검색 포커스 설정
                        if hasattr(item, 'set_search_focus'):
                            item.set_search_focus(is_match)

                        if is_match:
                            matched_items.append(item)
                except (RuntimeError, AttributeError):
                    continue

            return matched_items

        search_filter._filter_name = f"SearchFilter('{search_text}')"
        return search_filter

    @staticmethod
    def _update_status_lines(item, filter_states: Dict[str, bool]):
        """아이템의 상태선 업데이트 (내부 헬퍼 함수)"""
        shortage_filter = filter_states.get('shortage', False)
        shipment_filter = filter_states.get('shipment', False)
        pre_assigned_filter = filter_states.get('pre_assigned', False)

        # 상태선 설정
        if hasattr(item, 'show_shortage_line'):
            item.show_shortage_line = shortage_filter and getattr(item, 'is_shortage', False)
        if hasattr(item, 'show_shipment_line'):
            item.show_shipment_line = shipment_filter and getattr(item, 'is_shipment_failure', False)
        if hasattr(item, 'show_pre_assigned_line'):
            item.show_pre_assigned_line = pre_assigned_filter and getattr(item, 'is_pre_assigned', False)

        # 상태선 업데이트
        if hasattr(item, 'update'):
            item.update()


class ContainerFilterPipeline:
    """
    컨테이너 레벨 필터링 파이프라인
    - 그리드 컨테이너의 가시성 제어
    """

    @staticmethod
    def apply_container_visibility(containers, filter_states: Dict):
        """컨테이너 가시성 적용"""
        try:
            # 라인 필터가 활성화된 경우에만 컨테이너 숨김/표시 처리
            line_filters = filter_states.get('line', {})
            project_filters = filter_states.get('project', {})

            # 모든 라인/프로젝트 필터가 비활성화되면 모든 컨테이너 표시
            if not any(line_filters.values()) and not any(project_filters.values()):
                for row_containers in containers:
                    for container in row_containers:
                        if hasattr(container, 'setVisible'):
                            container.setVisible(True)
                return

            # 필터가 활성화된 경우 해당 조건에 맞는 컨테이너만 표시
            # (구현 복잡성으로 인해 현재는 아이템 레벨에서만 처리)

        except Exception as e:
            print(f"[파이프라인] 컨테이너 가시성 적용 오류: {e}")


# 사전 정의된 파이프라인 템플릿
class PipelineTemplates:
    """자주 사용되는 파이프라인 템플릿"""

    @staticmethod
    def create_full_filter_pipeline():
        """완전한 필터링 파이프라인 생성"""
        return FilterPipeline().set_debug(False)

    @staticmethod
    def create_search_only_pipeline():
        """검색 전용 파이프라인 생성"""
        return FilterPipeline().set_debug(False)

    @staticmethod
    def create_status_only_pipeline():
        """상태 필터 전용 파이프라인 생성"""
        return FilterPipeline().set_debug(False)