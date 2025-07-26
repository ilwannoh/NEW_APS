# APS 프로젝트 드래그&드롭 문제 분석 보고서

## 1. 문제 요약
APS 프로젝트의 `schedule_grid_view.py`에서 배치(Batch) 블록을 드래그&드롭으로 이동시키는 기능이 작동하지 않는 문제가 발생했습니다.

## 2. 코드 구조 분석

### 2.1 주요 컴포넌트
1. **DraggableBatchLabel**: 드래그 가능한 배치 라벨
   - `mousePressEvent`: 드래그 시작 위치 저장
   - `mouseMoveEvent`: 드래그 동작 처리
   - `mouseDoubleClickEvent`: 더블클릭 처리

2. **EquipmentTimeSlot**: 장비별 시간 슬롯 (드롭 타겟)
   - `dragEnterEvent`: 드래그 진입 시 처리
   - `dragLeaveEvent`: 드래그 떠남 시 처리
   - `dropEvent`: 드롭 시 처리

3. **ScheduleGridView**: 전체 스케줄 그리드 뷰
   - `handle_batch_drop`: 배치 드롭 처리 메서드
   - `batch_moved` 시그널: 배치 이동 완료 시 발생

### 2.2 이벤트 흐름
1. 사용자가 DraggableBatchLabel을 클릭 → `mousePressEvent`
2. 마우스 이동 → `mouseMoveEvent` → 드래그 시작
3. EquipmentTimeSlot 위로 이동 → `dragEnterEvent`
4. 드롭 → `dropEvent` → `batch_dropped` 시그널 발생
5. `handle_batch_drop` 슬롯 호출 → `batch_moved` 시그널 발생
6. MainWindow의 `on_batch_moved` 처리

## 3. 발견된 문제점

### 3.1 주요 문제
1. **소스 위젯 찾기 실패**
   - `EquipmentTimeSlot.dropEvent`에서 드래그 소스를 찾는 로직이 불완전
   - `event.source()`는 DraggableBatchLabel을 반환하지만, 실제 필요한 것은 그 부모 컨테이너

2. **드래그 거리 임계값**
   - `manhattanLength() < 10` 조건이 너무 엄격
   - 사용자가 10픽셀 이상 드래그해야 드래그가 시작됨

3. **시그널-슬롯 연결**
   - `container.batch_dropped.connect(self.handle_batch_drop)` 연결은 정상
   - 하지만 드롭 이벤트에서 소스 컨테이너를 제대로 전달하지 못함

### 3.2 부가적 문제
1. **디버그 정보 부족**
   - 이벤트 처리 과정에서 로그가 없어 문제 추적이 어려움

2. **이벤트 전파**
   - `mousePressEvent`에서 부모 클래스의 이벤트 핸들러를 호출하지 않음

3. **에러 처리 부족**
   - 예외 발생 시 조용히 실패하여 문제 파악이 어려움

## 4. 해결 방안

### 4.1 즉시 적용 가능한 수정
1. **드래그 거리 임계값 감소**
   ```python
   if (event.pos() - self.drag_start_position).manhattanLength() < 5:
   ```

2. **소스 위젯 찾기 로직 개선**
   ```python
   def dropEvent(self, event):
       if event.mimeData().hasText():
           batch_data = json.loads(event.mimeData().text())
           
           if self.can_accept_batch(batch_data):
               # 드래그 소스 찾기
               source_widget = event.source()
               source_container = None
               
               if source_widget and hasattr(source_widget, 'parent'):
                   parent = source_widget.parent()
                   if parent and hasattr(parent, 'batch'):
                       source_container = parent
               
               self.batch_dropped.emit(source_container, batch_data)
               event.acceptProposedAction()
   ```

3. **디버그 로그 추가**
   - 각 이벤트 핸들러에 print 문 추가
   - 문제 발생 지점 추적 가능

### 4.2 장기적 개선 사항
1. **로깅 시스템 도입**
   - Python logging 모듈 사용
   - 디버그 레벨별 로그 관리

2. **에러 처리 강화**
   - try-except 블록 추가
   - 사용자에게 친화적인 에러 메시지

3. **테스트 코드 작성**
   - 단위 테스트로 각 컴포넌트 검증
   - 통합 테스트로 전체 흐름 검증

## 5. 테스트 방법

### 5.1 수동 테스트
1. 프로그램 실행
2. 스케줄 생성 또는 로드
3. 배치 블록 클릭 후 드래그
4. 다른 시간 슬롯으로 드롭
5. 콘솔에서 디버그 메시지 확인

### 5.2 디버그 스크립트
- `debug_drag_drop.py`: 간단한 드래그&드롭 테스트
- `test_drag_drop_issue.py`: 실제 컴포넌트를 사용한 테스트
- `minimal_drag_drop_test.py`: 최소한의 테스트 케이스

## 6. 적용 방법
1. `fix_drag_drop.py` 실행
2. 'y' 입력하여 패치 적용
3. 프로그램 재실행
4. 드래그&드롭 기능 테스트

## 7. 결론
드래그&드롭 문제는 주로 소스 위젯을 찾는 로직의 불완전함과 너무 높은 드래그 거리 임계값 때문에 발생했습니다. 제공된 수정 사항을 적용하면 문제가 해결될 것으로 예상됩니다.

추가적으로 디버그 로그를 통해 문제 발생 시 빠른 진단이 가능하도록 개선했습니다.