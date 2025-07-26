from PyQt5.QtCore import QObject, QTimer

"""
검색 관련 로직 담당
"""
class SearchManager(QObject):
    def __init__(self, left_section):
        super().__init__()
        self.left_section = left_section

        # 최적화 1: 디바운싱 타이머
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._execute_search)
        self._pending_search_text = ""
        
        # 최적화 2: 간단한 캐시 (마지막 검색 결과만)
        self._last_search_text = ""
        self._last_search_results = []

    """
    검색 실행 (디바운싱 적용)
    """
    def search_items(self, search_text):
        search_text = search_text.strip().lower()

        if not search_text:
            self.clear_search()
            return
        
        print(f"[SearchManager] 검색 실행: '{search_text}'")
        self._execute_search(search_text)

    """
    실제 검색 실행
    """
    def _execute_search(self, search_text):

        # 간단한 캐시 확인
        if search_text == self._last_search_text:
            results = self._last_search_results

            # 캐시된 결과도 유효성 검사 
            results = self._validate_search_results(results)
        else:
            results = self._perform_search(search_text)

            # 캐시 저장
            self._last_search_text = search_text
            self._last_search_results = results
        
        self._apply_search_results(results, search_text)
        print(f"[SearchManager] 검색 완료: {len(results)}개 결과")

    """
    검색 결과 유효성 검사 - 삭제된 아이템 제거
    """
    def _validate_search_results(self, results):
        valid_results = []
        for item in results:
            try:
                # 아이템이 여전히 유효한지 확인
                _ = item.isVisible()
                # all_items에도 포함되어 있는지 확인
                if item in self.left_section.all_items:
                    valid_results.append(item)
                else:
                    print(f"[SearchManager] 아이템이 all_items에서 제거됨: {item}")
            except RuntimeError:
                print(f"[SearchManager] 삭제된 아이템 발견, 제거함")
                continue
        return valid_results

    """
    실제 검색 수행
    """
    def _perform_search(self, query):
        results = []

        # 최적화 3: all_items 직접 순회 (기존 3중 순회 대신)
        for item in self.left_section.all_items:
            try:
                 # 아이템 유효성 검사
                _ = item.isVisible()

                if hasattr(item, 'item_data') and item.item_data:
                    item_code = str(item.item_data.get('Item', '')).lower()
                    if query in item_code:
                        # 위치 정보 찾기
                        position = self._get_item_position(item)
                        if position:
                            results.append({
                                'item': item,
                                'row': position[0],
                                'col': position[1]
                            })
            except RuntimeError:
                # 삭제된 아이템은 all_items에서도 제거
                print(f"[SearchManager] 삭제된 아이템을 all_items에서 제거")
                if item in self.left_section.all_items:
                    self.left_section.all_items.remove(item)
                continue

        # 행 우선 정렬 (기존 로직)
        results.sort(key=lambda x: (x['row'], x['col']))
        
        # 정렬된 순서로 검색 결과 저장
        return [result['item'] for result in results]
    
    """
    아이템의 그리드 위치 반환 
    """
    def _get_item_position(self, target_item):
        if not hasattr(self.left_section.grid_widget, 'containers'):
            return None
            
        for row_idx, row_containers in enumerate(self.left_section.grid_widget.containers):
            for col_idx, container in enumerate(row_containers):
                try:
                    if target_item in container.items:
                        return (row_idx, col_idx)
                except RuntimeError:
                    # 컨테이너도 삭제된 경우
                    continue
        return None
    
    """
    검색 결과 적용
    """
    def _apply_search_results(self, results, query):
        # print("=== [DEBUG] 검색 필터 적용 시작 ===")
        # print(f"→ 검색어: '{query}', 검색 결과 수: {len(results)}")

        # 1. 모든 아이템의 검색 포커스 설정 
        for item in self.left_section.all_items:
            try:
                if hasattr(item, 'item_data') and item.item_data:
                    item_code = str(item.item_data.get('Item', '')).lower()
                    is_match = query in item_code

                    # 검색 포커스 설정
                    if hasattr(item, 'set_search_focus'):
                        current_focus = getattr(item, 'is_search_focused', False)
                        if current_focus != is_match:
                            item.set_search_focus(is_match)
            except RuntimeError:
                # 삭제된 아이템은 all_items에서 제거
                if item in self.left_section.all_items:
                    self.left_section.all_items.remove(item)
                continue
                
        # 2. 검색 결과 저장
        self.left_section.search_results = results
        self.left_section.current_result_index = 0 if results else -1
        
        # 3. 검색 위젯 업데이트
        if hasattr(self.left_section, 'search_widget'):
            self.left_section.search_widget.show_result_navigation(True)
            
            if results:
                self.left_section.search_widget.set_result_status(1, len(results))
                # 첫 번째 결과 선택
                if hasattr(self, 'select_current_result'):
                    self.select_current_result()
            else:
                self.left_section.search_widget.set_result_status(0, 0)
    
    """
    검색 초기화
    """
    def clear_search(self):
        # 타이머 중지
        if self._search_timer.isActive():
            self._search_timer.stop()
        
        # 캐시 초기화
        self._last_search_text = ""
        self._last_search_results = []

        try:
            # 모든 아이템의 검색 포커스 해제
            for item in self.left_section.all_items:
                if hasattr(item, 'set_search_focus'):
                    item.set_search_focus(False)
                if hasattr(item, 'set_search_current'):
                    item.set_search_current(False)

            # 선택 상태 초기화
            if hasattr(self.left_section.grid_widget, 'clear_all_selections'):
                self.left_section.grid_widget.clear_all_selections()
            self.left_section.current_selected_item = None
            self.left_section.current_selected_container = None
        except Exception as e:
            print(f"선택 초기화 오류: {e}")

        # 검색 상태 초기화
        self.left_section.search_results = []
        self.left_section.current_result_index = -1

        # 필터 적용 (기존 로직 유지)
        if hasattr(self.left_section, 'apply_all_filters'):
            self.left_section.apply_all_filters()

    """
    이전 검색 결과로 이동 (SearchWidget의 prevResultRequested 시그널에 연결)
    """
    def go_to_prev_result(self):
        if not self.left_section.search_results or self.left_section.current_result_index <= 0:
            return

        try:
            # 인덱스 변경 전에 현재 아이템 정보 저장
            old_index = self.left_section.current_result_index

            # 이전 결과로 인덱스 변경
            self.left_section.current_result_index -= 1

            # 아이템 강조 상태 업데이트 (이전 아이템 -> 일반 검색, 현재 아이템 -> 강조)
            self._update_search_highlight(old_index, self.left_section.current_result_index)

            # 현재 결과 표시 및 네비게이션 업데이트
            self._scroll_to_current_result()
            self.update_result_navigation()
        except Exception as e:
            print(f"이전 결과 이동 오류: {str(e)}")

    """
    다음 검색 결과로 이동 (SearchWidget의 nextResultRequested 시그널에 연결)
    """
    def go_to_next_result(self):
        if not self.left_section.search_results or self.left_section.current_result_index >= len(self.left_section.search_results) - 1:
            return

        try:
            # 인덱스 변경 전에 현재 아이템 정보 저장
            old_index = self.left_section.current_result_index

            # 다음 결과로 인덱스 변경
            self.left_section.current_result_index += 1

            # 아이템 강조 상태 업데이트 (이전 아이템 -> 일반 검색, 현재 아이템 -> 강조)
            self._update_search_highlight(old_index, self.left_section.current_result_index)

            # 현재 결과 표시 및 네비게이션 업데이트
            self._scroll_to_current_result()
            self.update_result_navigation()
        except Exception as e:
            print(f"다음 결과 이동 오류: {str(e)}")

    """
    선택된 검색 결과를 포커스하고 강조 표시
    """
    def select_current_result(self):
        if not self.left_section.search_results or not (0 <= self.left_section.current_result_index < len(self.left_section.search_results)):
            return

        try:
            # 모든 아이템의 현재 검색 포커스 상태 초기화
            for i, item in enumerate(self.left_section.search_results):
                if hasattr(item, 'set_search_current'):
                    # 현재 아이템만 강조
                    is_current = (i == self.left_section.current_result_index)
                    item.set_search_current(is_current)
                    # 강제 업데이트
                    item.repaint()
                    item.update()

            # 현재 아이템 저장 및 스크롤
            self._scroll_to_current_result()
        except Exception as e:
            print(f'항목 선택 오류: {str(e)}')

    """
    검색 결과 상태 업데이트
    """
    def update_result_navigation(self):
        if not self.left_section.search_results:
            # 검색 결과 없음
            self.left_section.search_widget.set_result_status(0, 0)
            return
        
        try:
            total_results = len(self.left_section.search_results)
            current_index = self.left_section.current_result_index + 1  # UI에 표시할 때는 1부터 시작

            # 검색 위젯의 결과 상태 업데이트
            self.left_section.search_widget.set_result_status(current_index, total_results)
        except Exception as e:
            print(f'네비게이션 업데이트 오류: {str(e)}')

    """
    검색 결과 강조 상태 업데이트 (새로운 헬퍼 메서드)
    """
    def _update_search_highlight(self, old_index, new_index):
        # 이전 아이템 강조 해제
        if 0 <= old_index < len(self.left_section.search_results):
            old_item = self.left_section.search_results[old_index]
            if hasattr(old_item, 'set_search_current'):
                old_item.set_search_current(False)

        # 새 아이템 강조 (repaint/update 제거)
        if 0 <= new_index < len(self.left_section.search_results):
            new_item = self.left_section.search_results[new_index]
            if hasattr(new_item, 'set_search_current'):
                new_item.set_search_current(True)

    """
    현재 검색 결과로 스크롤 (새로운 헬퍼 메서드)
    """
    def _scroll_to_current_result(self):
        if not (0 <= self.left_section.current_result_index < len(self.left_section.search_results)):
            return

        current_item = self.left_section.search_results[self.left_section.current_result_index]
        container = current_item.parent()

        # 아이템 표시 확인
        if hasattr(current_item, 'isVisible') and not current_item.isVisible():
            current_item.setVisible(True)

        # 스크롤만 수행 (데이터 변경 시그널 제거)
        if hasattr(self.left_section.grid_widget, 'ensure_item_visible'):
            self.left_section.grid_widget.ensure_item_visible(container, current_item)

        # 데이터 변경 알림 제거 - 이 부분이 중복 호출의 원인
        # df = self.extract_dataframe()
        # self.viewDataChanged.emit(df)

    """
    필터 변경 후 검색이 활성화되어 있으면 재적용
    """
    def reapply_search_if_active(self):
        if (hasattr(self.left_section, 'search_widget') and 
            self.left_section.search_widget.is_search_active()):
            search_text = self.left_section.search_widget.get_search_text()
            if search_text:
                print("[SearchManager] 필터 변경 후 검색 재적용")
                self._invalidate_cache()  # 캐시 무효화 
                self.search_items(search_text)

    """
    캐시 무효화 - 그리드 재구성 시 호출
    """
    def _invalidate_cache(self):
        print("[SearchManager] 캐시 무효화")
        self._last_search_text = ""
        self._last_search_results = []

    """
    그리드 재구성 알림 - FilterManager에서 호출
    """
    def on_grid_rebuilt(self):
        print("[SearchManager] 그리드 재구성 알림 받음")
        # 캐시 완전 초기화
        self._invalidate_cache()
        
        # 현재 검색이 활성화되어 있으면 즉시 재검색
        if (hasattr(self.left_section, 'search_widget') and 
            self.left_section.search_widget.is_search_active()):
            search_text = self.left_section.search_widget.get_search_text()
            if search_text:
                print("[SearchManager] 그리드 재구성 후 즉시 재검색")
                # 강제로 새로운 검색 실행
                self._last_search_text = ""  # 캐시 우회
                self.search_items(search_text)

