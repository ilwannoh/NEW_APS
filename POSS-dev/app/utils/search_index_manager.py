"""
검색 성능 최적화를 위한 인덱스 관리 모듈
"""


class SearchIndexManager:
    """검색 성능 최적화를 위한 인덱스 관리 클래스"""

    def __init__(self):
        self.item_index = {}  # item_code -> [items] 매핑
        self.position_index = {}  # (row, col) -> [items] 매핑
        self.dirty = True  # 인덱스 재구축 필요 여부

    def build_index(self, all_items):
        """검색 인덱스 구축"""
        if not self.dirty and self.item_index:
            return  # 이미 최신 인덱스가 있으면 스킵

        print("SearchIndexManager: 검색 인덱스 구축 시작")
        self.item_index.clear()
        self.position_index.clear()

        valid_items = []
        for item in all_items:
            try:
                # 유효한 아이템인지 확인
                if hasattr(item, 'item_data') and item.item_data and 'Item' in item.item_data:
                    item_code = str(item.item_data['Item']).lower()

                    # 아이템 코드별 인덱스
                    if item_code not in self.item_index:
                        self.item_index[item_code] = []
                    self.item_index[item_code].append(item)

                    # 위치별 인덱스 (향후 확장용)
                    position = self._get_item_position(item)
                    if position:
                        if position not in self.position_index:
                            self.position_index[position] = []
                        self.position_index[position].append(item)

                    valid_items.append(item)

            except RuntimeError:
                # 삭제된 위젯은 무시
                continue
            except Exception as e:
                print(f"인덱스 구축 중 오류: {e}")
                continue

        self.dirty = False
        print(f"SearchIndexManager: 인덱스 구축 완료 - {len(valid_items)}개 아이템, {len(self.item_index)}개 고유 코드")

        return valid_items

    def search(self, search_text):
        """인덱스 기반 빠른 검색"""
        if self.dirty:
            print("SearchIndexManager: 인덱스가 오래됨 - 재구축 필요")
            return []

        search_text = search_text.lower().strip()
        if not search_text:
            return []

        matched_items = []

        # 부분 문자열 매칭으로 검색
        for item_code, items in self.item_index.items():
            if search_text in item_code:
                matched_items.extend(items)

        print(f"SearchIndexManager: '{search_text}' 검색 결과 {len(matched_items)}개")
        return matched_items

    def mark_dirty(self):
        """인덱스 무효화 - 아이템 변경 시 호출"""
        self.dirty = True

    def _get_item_position(self, item):
        """아이템의 그리드 위치 반환"""
        try:
            if hasattr(item, 'parent') and item.parent():
                container = item.parent()
                # 그리드에서 컨테이너 위치 찾기
                return self._find_container_position(container)
        except:
            pass
        return None

    def _find_container_position(self, container):
        """컨테이너의 그리드 위치 찾기"""
        # 구현 복잡성으로 인해 일단 None 반환
        # 향후 필요시 확장
        return None


class SearchResultSorter:
    """검색 결과 정렬 유틸리티"""

    @staticmethod
    def sort_by_position(items, grid_widget):
        """검색 결과를 행 우선 순서로 정렬"""
        if not grid_widget or not hasattr(grid_widget, 'containers'):
            return items

        positioned_items = []

        for item in items:
            position = SearchResultSorter._find_item_position(item, grid_widget)
            if position:
                positioned_items.append({
                    'item': item,
                    'row': position[0],
                    'col': position[1]
                })

        # 행 우선 정렬
        positioned_items.sort(key=lambda x: (x['row'], x['col']))

        return [item_data['item'] for item_data in positioned_items]

    @staticmethod
    def _find_item_position(item, grid_widget):
        """아이템의 그리드 위치 찾기"""
        try:
            container = item.parent()
            if not container:
                return None

            # 그리드에서 컨테이너 위치 찾기
            for row_idx, row_containers in enumerate(grid_widget.containers):
                for col_idx, grid_container in enumerate(row_containers):
                    if grid_container == container:
                        return (row_idx, col_idx)
        except:
            pass
        return None