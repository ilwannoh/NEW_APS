"""
스케줄 그리드 뷰
드래그&드롭을 지원하는 생산 스케줄 그리드
POSS-dev의 item_grid_widget.py를 참고하여 구현
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                           QGridLayout, QLabel, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QPainter, QColor, QPixmap, QFont, QPen, QPainterPath

from app.models.production_plan import ProductionPlan, Batch
from app.resources.styles.screen_manager import w, h, f
from app.resources.styles.app_style import AppStyle
from datetime import datetime, timedelta
import json


class DraggableBatchLabel(QFrame):
    """드래그 가능한 배치 라벨"""
    
    # 시그널
    batch_selected = pyqtSignal(object)  # 배치 선택
    batch_double_clicked = pyqtSignal(object)  # 배치 더블클릭
    
    def __init__(self, batch: Batch, master_data=None, parent=None):
        super().__init__(parent)
        self.batch = batch
        self.master_data = master_data
        self.is_selected = False
        self.current_row = -1  # 현재 그리드 행
        self.current_col = -1  # 현재 그리드 열
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setFrameStyle(QFrame.NoFrame)  # 프레임 제거
        self.setCursor(Qt.OpenHandCursor)
        
        # 기본 크기 설정 (나중에 부모에서 조정)
        self.setMinimumHeight(h(40))
        self.setMaximumHeight(h(45))
        
        # 레이아웃
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)
        
        # 소요시간 아이콘 표시 (시계 아이콘 대신 시간 표시)
        duration_container = QWidget()
        duration_layout = QHBoxLayout(duration_container)
        duration_layout.setContentsMargins(0, 0, 0, 2)
        duration_layout.setSpacing(2)
        
        # 소요시간을 시각적으로 표시 (블록 개수로)
        duration_hours = int(self.batch.duration_hours)
        block_count = min(4, max(1, duration_hours // 2))  # 2시간당 1블록
        
        for i in range(block_count):
            block = QLabel()
            block.setFixedSize(w(10), h(4))
            block.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: 2px;
            """)
            duration_layout.addWidget(block)
        
        # 시간 텍스트 추가
        time_label = QLabel(f"{duration_hours}h")
        time_label.setStyleSheet(f"color: rgba(255, 255, 255, 0.9); font-size: {f(8)}px;")
        duration_layout.addWidget(time_label)
        
        duration_layout.addStretch()
        layout.addWidget(duration_container, alignment=Qt.AlignHCenter)
        
        # 배치 번호 (엑셀의 배치번호를 125, 225, 325 형식으로 변환)
        if hasattr(self.batch, 'lot_number') and self.batch.lot_number:
            lot_num = int(self.batch.lot_number)
            # 1 -> 125, 2 -> 225, 3 -> 325, 4 -> 425 형식으로 변환
            batch_text = f"{lot_num * 100 + 25}"
        else:
            # 없으면 batch_id에서 숫자 추출
            import re
            numbers = re.findall(r'\d+', self.batch.id)
            if numbers:
                batch_num = int(numbers[0])
                batch_text = f"{batch_num * 100 + 25}"
            else:
                batch_text = "125"
        
        batch_label = QLabel(batch_text)
        batch_label.setAlignment(Qt.AlignCenter)
        batch_label.setStyleSheet(f"font-weight: bold; font-size: {f(12)}px; color: white;")
        layout.addWidget(batch_label)
        
        # 제품명 (짧게)
        product_name_short = self.batch.product_name.split()[0][:6]
        product_label = QLabel(product_name_short)
        product_label.setAlignment(Qt.AlignCenter)
        product_label.setStyleSheet(f"font-size: {f(8)}px; color: rgba(255, 255, 255, 0.9);")
        layout.addWidget(product_label)
        
        # 스타일 적용
        self.update_style()
    
    def update_style(self):
        """스타일 업데이트"""
        # 기본 색상 정의
        default_colors = {
            # 기넥신에프정 - 파란색 계열
            '기넥신에프정 40mg 100T': '#1e88e5',
            '기넥신에프정 40mg 300T': '#1565c0',
            '기넥신에프정 80mg 100T': '#42a5f5',
            '기넥신에프정 80mg 500T': '#0d47a1',
            # 리넥신정 - 녹색 계열
            '리넥신정 80/100mg 300T': '#43a047',
            '리넥신정 80/100mg 30T': '#66bb6a',
            '리넥신서방정 30T': '#2e7d32',
            '리넥신서방정 300T': '#1b5e20',
            # 조인스정 - 주황색 계열
            '조인스정 200mg 500T': '#fb8c00',
            # 페브릭정 - 보라색 계열
            '페브릭정 40mg 30T': '#8e24aa',
            '페브릭정 40mg 100T': '#6a1b9a',
            '페브릭정 80mg 30T': '#ab47bc',
            '페브릭정 80mg 100T': '#4a148c',
            # 신플랙스세이프정 - 빨간색 계열
            '신플랙스세이프정 100T': '#e53935',
            '신플랙스세이프정 30T': '#ef5350'
        }
        
        # 장비별 제품 색상 확인
        bg_color = default_colors.get(self.batch.product_name, '#3498db')
        
        if self.master_data and hasattr(self.batch, 'equipment_id'):
            equipment = self.master_data.equipment.get(self.batch.equipment_id)
            if equipment and 'product_colors' in equipment:
                # 장비에 설정된 제품별 색상이 있으면 사용
                if self.batch.product_id in equipment['product_colors']:
                    bg_color = equipment['product_colors'][self.batch.product_id]
        
        if self.is_selected:
            border_color = '#1428A0'
            border_width = '3px'
        else:
            border_color = '#ddd'
            border_width = '1px'
        
        # 배치 스타일 - 레고/테트리스 스타일
        self.setStyleSheet(f"""
            DraggableBatchLabel {{
                background-color: {bg_color};
                border: {border_width} solid {border_color};
                border-radius: 6px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {bg_color},
                    stop: 0.5 {bg_color},
                    stop: 1 {self._darken_color(bg_color)});
            }}
            QLabel {{
                color: white;
                background: transparent;
            }}
        """)
    
    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.batch_selected.emit(self)
        # 부모 클래스의 이벤트 핸들러도 호출
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if (event.pos() - self.drag_start_position).manhattanLength() < 5:
            return
        
        # 드래그 시작
        print(f"[DEBUG] Starting drag for batch {self.batch.id}")
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 배치 데이터를 JSON으로 직렬화
        batch_data = {
            'batch_id': self.batch.id,
            'product_id': self.batch.product_id,
            'product_name': self.batch.product_name,
            'equipment_id': self.batch.equipment_id,
            'start_time': self.batch.start_time.isoformat(),
            'duration_hours': self.batch.duration_hours,
            'process_id': getattr(self.batch, 'process_id', None),
            'lot_number': getattr(self.batch, 'lot_number', None)
        }
        
        mime_data.setText(json.dumps(batch_data))
        drag.setMimeData(mime_data)
        
        # 드래그 중 표시할 픽스맵 생성
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        drag.exec_(Qt.MoveAction)
    
    def mouseDoubleClickEvent(self, event):
        """마우스 더블클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            self.batch_double_clicked.emit(self)
    
    def set_selected(self, selected):
        """선택 상태 설정"""
        self.is_selected = selected
        self.update_style()
    
    def _darken_color(self, color):
        """색상을 어둡게 만드는 헬퍼 메서드"""
        # 간단한 구현 - 실제로는 더 정교한 색상 변환 필요
        if color.startswith('#'):
            # Hex to RGB
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            # Darken by 20%
            r = int(r * 0.8)
            g = int(g * 0.8)
            b = int(b * 0.8)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color


class EquipmentTimeSlot(QFrame):
    """장비별 시간 슬롯 (1시간 = 1칸)"""
    
    # 시그널
    batch_dropped = pyqtSignal(object, object)  # 이전 컨테이너, 배치 데이터
    
    def __init__(self, equipment_id: str, date, slot: int, parent=None):
        super().__init__(parent)
        self.equipment_id = equipment_id
        self.date = date
        self.slot = slot  # 0-3 (하루 4구간)
        self.batch = None
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box)
        self.setFixedWidth(w(120))  # 각 구간의 너비 (더 크게)
        self.setMinimumHeight(h(70))  # 높이도 증가
        
        # 빈 셀 스타일 - 더 명확한 경계선
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-style: solid;
            }
        """)
    
    def can_accept_batch(self, batch_data):
        """배치를 받을 수 있는지 확인"""
        # 수동 편집 모드에서는 모든 제약 무시 (자유로운 배치)
        # 이미 배치가 있는 곳에만 놓을 수 없음
        print(f"[DEBUG] can_accept_batch - self.batch: {self.batch}, batch_data: {batch_data.get('batch_id')}")
        if self.batch:
            print(f"[DEBUG] Slot already occupied by: {self.batch}")
            return False
        
        # 초안 이후 수동 편집은 완전 자유
        # duration 체크 제거 - 어디든 놓을 수 있음
        return True
    
    def dragEnterEvent(self, event):
        """드래그 진입 이벤트"""
        print(f"[DEBUG] dragEnterEvent - equipment: {self.equipment_id}, date: {self.date}, slot: {self.slot}")
        if event.mimeData().hasText():
            batch_data = json.loads(event.mimeData().text())
            if self.can_accept_batch(batch_data):
                print("[DEBUG] Accepting drag enter")
                event.acceptProposedAction()
                # 드래그 중 하이라이트
                self.setStyleSheet("""
                    QFrame {
                        background-color: #e3f2fd;
                        border: 2px solid #1428A0;
                    }
                """)
            else:
                print("[DEBUG] Ignoring drag enter")
                event.ignore()
        else:
            print("[DEBUG] No text in mime data")
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """드래그 떠남 이벤트"""
        # 하이라이트 제거
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)
    
    def dropEvent(self, event):
        """드롭 이벤트"""
        print(f"[DEBUG] EquipmentTimeSlot.dropEvent called - equipment_id: {self.equipment_id}, date: {self.date}, slot: {self.slot}")
        
        if event.mimeData().hasText():
            batch_data = json.loads(event.mimeData().text())
            print(f"[DEBUG] Batch data: {batch_data.get('batch_id')}")
            
            if self.can_accept_batch(batch_data):
                # 드래그 소스 찾기
                source_widget = event.source()
                source_container = None
                
                print(f"[DEBUG] Source widget type: {type(source_widget).__name__}")
                
                if source_widget and hasattr(source_widget, 'parent'):
                    # DraggableBatchLabel의 부모 찾기
                    parent = source_widget.parent()
                    print(f"[DEBUG] Parent widget type: {type(parent).__name__ if parent else 'None'}")
                    # 그리드 레이아웃에 직접 배치된 경우를 처리
                    if parent and hasattr(parent, 'batch'):
                        source_container = parent
                
                # 배치 이동 시그널 발생
                print(f"[DEBUG] Emitting batch_dropped signal")
                self.batch_dropped.emit(source_container, batch_data)
                event.acceptProposedAction()
            else:
                print("[DEBUG] Cannot accept batch at this location")
        
        # 스타일 복원
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)


class ProcessTimeSlot(QFrame):
    """공정별 시간 슬롯 (1시간 단위)"""
    
    # 시그널
    batch_dropped = pyqtSignal(object, object)  # 이전 컨테이너, 배치 데이터
    
    def __init__(self, process_id: str, team_idx: int, hour: int, parent=None):
        super().__init__(parent)
        self.process_id = process_id
        self.team_idx = team_idx
        self.hour = hour
        self.batch = None  # 이 슬롯의 배치
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box)
        self.setFixedWidth(self.parent().hour_width if hasattr(self.parent(), 'hour_width') else w(20))
        self.setMinimumHeight(h(35))
        
        # 빈 셀 스타일
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)
    
    def can_accept_batch(self, batch_data):
        """배치를 받을 수 있는지 확인"""
        # 이미 배치가 있으면 불가
        if self.batch:
            return False
        
        # 공정이 맞는지 확인
        if batch_data.get('process_id') != self.process_id:
            return False
        
        return True
    
    def dragEnterEvent(self, event):
        """드래그 진입 이벤트"""
        if event.mimeData().hasText():
            batch_data = json.loads(event.mimeData().text())
            if self.can_accept_batch(batch_data):
                event.acceptProposedAction()
                # 드래그 중 하이라이트
                self.setStyleSheet("""
                    QFrame {
                        background-color: #e3f2fd;
                        border: 2px solid #1428A0;
                    }
                """)
            else:
                event.ignore()
    
    def dragLeaveEvent(self, event):
        """드래그 떠남 이벤트"""
        # 하이라이트 제거
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)
    
    def dropEvent(self, event):
        """드롭 이벤트"""
        if event.mimeData().hasText():
            batch_data = json.loads(event.mimeData().text())
            
            if self.can_accept_batch(batch_data):
                # 드래그 소스 찾기
                source_widget = event.source()
                if source_widget and hasattr(source_widget, 'parent'):
                    source_container = source_widget.parent()
                    if isinstance(source_container, ProcessTimeSlot):
                        # 배치 이동 시그널 발생
                        self.batch_dropped.emit(source_container, batch_data)
                
                event.acceptProposedAction()
        
        # 스타일 복원
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)


class BatchContainer(QFrame):
    """배치를 담는 컨테이너 (그리드의 한 셀) - 기존 호환성 유지"""
    
    # 시그널
    batch_dropped = pyqtSignal(object, object)  # 이전 컨테이너, 배치 데이터
    
    def __init__(self, equipment_id: str, date: datetime, parent=None):
        super().__init__(parent)
        self.equipment_id = equipment_id
        self.date = date
        self.batches = []  # 이 셀의 배치들
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box)
        self.setMinimumHeight(h(100))
        self.setMinimumWidth(w(140))
        
        # 레이아웃 - 플로우 레이아웃처럼 동작하도록
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(1)
        
        # 빈 셀 스타일
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)
    
    def add_batch(self, batch_label: DraggableBatchLabel):
        """배치 추가"""
        self.batches.append(batch_label)
        self.layout.addWidget(batch_label)
        
        # 배치가 많을 때 컨테이너 높이 자동 조정
        batch_count = len(self.batches)
        if batch_count > 2:
            # 배치당 높이 + 여백
            new_height = h(35) * batch_count + h(10)
            self.setMinimumHeight(new_height)
    
    def remove_batch(self, batch_label: DraggableBatchLabel):
        """배치 제거"""
        if batch_label in self.batches:
            self.batches.remove(batch_label)
            self.layout.removeWidget(batch_label)
            batch_label.setParent(None)
    
    def dragEnterEvent(self, event):
        """드래그 진입 이벤트"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # 드래그 중 하이라이트
            self.setStyleSheet("""
                QFrame {
                    background-color: #e3f2fd;
                    border: 2px solid #1428A0;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """드래그 떠남 이벤트"""
        # 하이라이트 제거
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)
    
    def dropEvent(self, event):
        """드롭 이벤트"""
        if event.mimeData().hasText():
            # 드롭된 배치 데이터 파싱
            batch_data = json.loads(event.mimeData().text())
            
            # 드래그 소스 찾기
            source_widget = event.source()
            if source_widget and hasattr(source_widget, 'parent'):
                source_container = source_widget.parent()
                if isinstance(source_container, BatchContainer):
                    # 배치 이동 시그널 발생
                    self.batch_dropped.emit(source_container, batch_data)
            
            event.acceptProposedAction()
        
        # 스타일 복원
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)


class ScheduleGridView(QWidget):
    """스케줄 그리드 뷰 - 레고 블록 방식"""
    
    # 시그널
    batch_moved = pyqtSignal(str, str, datetime)  # batch_id, new_equipment_id, new_date
    batch_selected = pyqtSignal(object)  # 선택된 배치
    
    def __init__(self, production_plan: ProductionPlan = None, master_data=None, parent=None):
        super().__init__(parent)
        self.production_plan = production_plan
        self.master_data = master_data
        self.containers = {}  # (equipment_id, date) -> BatchContainer
        self.batch_labels = {}  # batch_id -> DraggableBatchLabel
        self.batch_positions = {}  # batch_id -> (equipment_id, date, slot, duration_slots) - 시각적 위치 추적
        self.selected_batch = None
        self.hour_width = w(60)  # 1시간당 픽셀 너비 (더 크게)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 그리드 위젯
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(2)
        
        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)
    
    def setup_grid(self, equipment_list, date_range):
        """그리드 설정 - Y축: 장비, X축: 날짜"""
        # 기존 위젯 제거
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        self.containers.clear()
        self.batch_labels.clear()
        
        # 날짜 헤더 (각 날짜를 4구간으로 나눔)
        col = 1
        cells_per_day = 4  # 하루를 4구간으로 표현
        
        for date in date_range:
            # 날짜 라벨 (4구간을 차지)
            date_label = QLabel(date.strftime('%m월 %d일'))
            date_label.setAlignment(Qt.AlignCenter)
            date_label.setStyleSheet(f"""
                background-color: #f0f0f0;
                border: 2px solid #999;
                font-weight: bold;
                font-size: {f(12)}px;
                padding: {h(5)}px;
            """)
            self.grid_layout.addWidget(date_label, 0, col, 1, cells_per_day)
            
            # 구간 헤더 추가 (1구간, 2구간, 3구간, 4구간)
            for slot in range(cells_per_day):
                slot_label = QLabel(f"{slot + 1}구간")
                slot_label.setAlignment(Qt.AlignCenter)
                slot_label.setStyleSheet(f"""
                    background-color: #f8f9fa;
                    border: 1px solid #ccc;
                    font-size: {f(10)}px;
                    padding: {h(3)}px;
                """)
                self.grid_layout.addWidget(slot_label, 1, col + slot)
            
            col += cells_per_day
        
        # 장비별 행 생성 (헤더가 2줄이므로 2부터 시작)
        row = 2
        
        # 모든 장비 수집 (공정별로 정렬)
        all_equipment = []
        if self.master_data:
            # 공정 순서대로 처리
            for process in sorted(self.master_data.processes.values(), key=lambda x: x.get('order', 0)):
                process_id = process['id']
                # 해당 공정의 장비들
                process_equipment = [eq for eq in self.master_data.equipment.values() 
                                   if eq.get('process_id') == process_id]
                all_equipment.extend(sorted(process_equipment, key=lambda x: x.get('name', '')))
        
        # 장비별로 행 생성
        for equipment in all_equipment:
            equipment_id = equipment['id']
            equipment_name = equipment['name']
            
            # 장비 헤더
            equipment_label = QLabel(equipment_name)
            equipment_label.setAlignment(Qt.AlignCenter)
            equipment_label.setStyleSheet(f"""
                background-color: #1428A0;
                color: white;
                border: 1px solid #0C1A6B;
                padding: {h(5)}px;
                font-weight: bold;
                font-size: {f(12)}px;
                min-width: {w(100)}px;
            """)
            self.grid_layout.addWidget(equipment_label, row, 0)
            
            # 각 날짜별로 셀 생성
            col = 1
            for date in date_range:
                # 하루를 4개 구간으로 나눔
                for slot in range(cells_per_day):
                    container = EquipmentTimeSlot(equipment_id, date, slot, self)
                    container.batch_dropped.connect(self.handle_batch_drop)
                    # 더 명확한 경계선
                    container.setStyleSheet("""
                        QFrame {
                            background-color: #ffffff;
                            border: 1px solid #dee2e6;
                            border-style: solid;
                        }
                        QFrame:hover {
                            background-color: #f8f9fa;
                        }
                    """)
                    self.grid_layout.addWidget(container, row, col)
                    self.containers[(equipment_id, date, slot)] = container
                    col += 1
            
            row += 1
    
    def load_schedule(self, production_plan: ProductionPlan):
        """스케줄 로드 - 레고 블록 방식"""
        self.production_plan = production_plan
        
        if not production_plan or not production_plan.batches:
            return
        
        # 날짜 범위 추출
        dates = []
        for batch in production_plan.batches.values():
            dates.append(batch.start_time.date())
        
        if not dates:
            return
        
        # 날짜 범위 생성
        min_date = min(dates)
        max_date = max(dates)
        date_range = []
        current_date = min_date
        while current_date <= max_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # 날짜 범위 저장
        self.date_range = date_range
        
        # 그리드 설정 (공정별로 그룹화)
        self.setup_grid(None, date_range)  # equipment_list는 사용하지 않음
        
        # 배치들을 장비 시간 슬롯에 배치
        for batch in production_plan.batches.values():
            self.add_batch_to_equipment_slots(batch)
    
    def add_batch_to_equipment_slots(self, batch: Batch):
        """배치를 장비 시간 슬롯에 추가"""
        # 구간 기반 단순화 - 시간이 0-3이면 그대로 구간으로 사용
        hour = batch.start_time.hour
        if 0 <= hour <= 3:
            start_slot = hour
        else:
            # 레거시 시간 매핑 (8시→0구간, 10시→1구간...)
            if hour >= 8 and hour < 10:
                start_slot = 0
            elif hour >= 10 and hour < 12:
                start_slot = 1
            elif hour >= 13 and hour < 15:
                start_slot = 2
            elif hour >= 15 and hour < 17:
                start_slot = 3
            else:
                return  # 유효하지 않은 시간
        
        # 소요 시간을 구간 수로 변환 (2시간 = 1구간)
        duration_slots = max(1, int(batch.duration_hours / 2))
        
        # 해당 장비의 슬롯 찾기
        date = batch.start_time.date()
        
        # 배치 가능한지 확인
        can_place = True
        for slot_offset in range(duration_slots):
            slot_idx = start_slot + slot_offset
            if slot_idx >= 4:  # 하루 4구간을 넘어가면
                can_place = False
                break
            
            key = (batch.equipment_id, date, slot_idx)
            if key in self.containers:
                if self.containers[key].batch is not None:
                    can_place = False
                    break
            else:
                can_place = False
                break
        
        if can_place:
            # 배치 라벨 생성 (duration에 맞는 크기)
            batch_label = DraggableBatchLabel(batch, self.master_data)
            batch_label.batch_selected.connect(self.on_batch_selected)
            
            # 크기를 duration에 맞게 설정 (구간 단위)
            batch_width = w(120) * duration_slots - 4  # 1구간 = 120픽셀, 경계선 고려
            batch_label.setFixedWidth(batch_width)
            batch_label.setFixedHeight(h(60))  # 높이 고정
            
            # 배치를 그리드에 직접 추가 - 장비명으로 행 찾기
            row = -1
            
            # 장비명으로 정확한 행 찾기
            if self.master_data and batch.equipment_id in self.master_data.equipment:
                equipment_name = self.master_data.equipment[batch.equipment_id]['name']
                
                for r in range(self.grid_layout.rowCount()):
                    item = self.grid_layout.itemAtPosition(r, 0)
                    if item and item.widget():
                        label = item.widget()
                        if isinstance(label, QLabel) and label.text() == equipment_name:
                            row = r
                            break
            
            if row != -1:
                # 열 위치 계산 (날짜별 4구간)
                days_diff = (date - self.date_range[0]).days if hasattr(self, 'date_range') else 0
                col_start = 1 + days_diff * 4 + start_slot
                
                # 배치 라벨을 그리드에 직접 추가 (columnSpan 사용)
                # 중요: 빈 슬롯 위젯들을 숨기거나 제거
                for slot_offset in range(duration_slots):
                    col = col_start + slot_offset
                    item = self.grid_layout.itemAtPosition(row, col)
                    if item and item.widget():
                        widget = item.widget()
                        if isinstance(widget, EquipmentTimeSlot):
                            # 슬롯 위젯 숨기기 (제거하면 레이아웃이 깨짐)
                            widget.hide()
                
                # 배치 라벨 추가
                self.grid_layout.addWidget(batch_label, row, col_start, 1, duration_slots)
                
                # 배치 라벨에 위치 정보 저장
                batch_label.current_row = row
                batch_label.current_col = col_start
                
                # 위치 추적 딕셔너리에 저장
                self.batch_positions[batch.id] = {
                    'equipment_id': batch.equipment_id,
                    'date': date,
                    'slot': start_slot,
                    'duration_slots': duration_slots
                }
                
                # 컨테이너들에 점유 표시
                for slot_offset in range(duration_slots):
                    slot_idx = start_slot + slot_offset
                    key = (batch.equipment_id, date, slot_idx)
                    if key in self.containers:
                        self.containers[key].batch = "occupied"
            
            self.batch_labels[batch.id] = batch_label
    
    def add_batch_to_grid(self, batch: Batch):
        """그리드에 배치 추가 - 기존 호환성 유지"""
        key = (batch.equipment_id, batch.start_time.date())
        if key in self.containers:
            container = self.containers[key]
            
            # 배치 라벨 생성 (master_data 전달)
            batch_label = DraggableBatchLabel(batch, self.master_data)
            batch_label.batch_selected.connect(self.on_batch_selected)
            
            # 컨테이너에 추가
            container.add_batch(batch_label)
            self.batch_labels[batch.id] = batch_label
    
    def handle_batch_drop(self, source_container, batch_data: dict):
        """배치 드롭 처리"""
        print(f"[DEBUG] handle_batch_drop called - batch_id: {batch_data.get('batch_id')}")
        
        target_container = self.sender()
        
        # EquipmentTimeSlot인지 확인
        if not isinstance(target_container, EquipmentTimeSlot):
            print("[DEBUG] Target is not EquipmentTimeSlot")
            return
        
        # 배치 ID로 라벨 찾기
        batch_id = batch_data['batch_id']
        if batch_id not in self.batch_labels:
            print(f"[DEBUG] Batch {batch_id} not found in batch_labels")
            return
        
        batch_label = self.batch_labels[batch_id]
        
        # 대상 슬롯이 비어있는지 확인
        if target_container.batch is not None:
            print("[DEBUG] Target slot is not empty")
            return
        
        print(f"[DEBUG] Target equipment: {target_container.equipment_id}, date: {target_container.date}, slot: {target_container.slot}")
        
        # 기존 위치에서 제거 (슬롯 복원 포함)
        print("[DEBUG] Removing batch from grid and restoring slots...")
        self._remove_batch_from_grid_and_restore_slots(batch_id)
        
        # 새 위치에 배치
        target_date = target_container.date
        target_slot = target_container.slot
        
        # 배치의 duration 정보 가져오기
        duration_hours = batch_data.get('duration_hours', 2)
        duration_slots = max(1, int(duration_hours / 2))
        
        # 위치 추적 딕셔너리만 업데이트 (production_plan은 건드리지 않음)
        self.batch_positions[batch_id] = {
            'equipment_id': target_container.equipment_id,
            'date': target_date,
            'slot': target_slot,
            'duration_slots': duration_slots
        }
        
        print(f"[DEBUG] Updated batch position: {self.batch_positions[batch_id]}")
        
        # 시각적으로만 이동
        print("[DEBUG] Moving batch visually...")
        self._move_batch_visual(batch_id, target_container)
    
    def on_batch_selected(self, batch_label: DraggableBatchLabel):
        """배치 선택 처리"""
        # 이전 선택 해제 - 객체가 삭제되었는지 확인
        if self.selected_batch:
            try:
                # 위젯이 아직 유효한지 확인 - parent가 None이면 삭제된 것
                if self.selected_batch.parent() is not None:
                    self.selected_batch.set_selected(False)
            except RuntimeError:
                # 객체가 삭제된 경우 무시
                pass
        
        # 새로운 선택
        self.selected_batch = batch_label
        if batch_label and batch_label.parent() is not None:
            batch_label.set_selected(True)
            # 시그널 발생
            self.batch_selected.emit(batch_label.batch)
    
    def refresh_view(self):
        """뷰 새로고침"""
        if self.production_plan and self.production_plan.batches:
            self.load_schedule(self.production_plan)
        else:
            # 배치가 없으면 빈 그리드 표시
            self.clear_grid()
    
    def clear_grid(self):
        """그리드 초기화"""
        # 모든 배치 라벨 제거
        for batch_label in self.batch_labels.values():
            batch_label.setParent(None)
        self.batch_labels.clear()
        
        # 숨겨진 슬롯들 다시 표시
        for container in self.containers.values():
            container.batch = None
            container.show()
        
        # 그리드 재설정 (날짜 범위가 있으면)
        if hasattr(self, 'date_range') and self.date_range:
            self.setup_grid(None, self.date_range)
    
    def _validate_process_connection(self, batch_data: dict, target_container) -> bool:
        """공정 연결 규칙 검증 (테트리스 규칙)"""
        if not self.master_data:
            return True
        
        lot_number = batch_data.get('lot_number')
        if not lot_number:
            return True
        
        # 같은 lot_number의 다른 공정들 찾기
        same_lot_batches = []
        for batch in self.production_plan.batches.values():
            if getattr(batch, 'lot_number', None) == lot_number and batch.id != batch_data['batch_id']:
                same_lot_batches.append(batch)
        
        if not same_lot_batches:
            return True
        
        # 현재 공정과 대상 장비의 공정 확인
        current_process_id = batch_data.get('process_id')
        target_equipment_id = target_container.equipment_id
        
        # 대상 장비의 공정 찾기
        target_process_id = None
        for eq in self.master_data.equipment.values():
            if eq['id'] == target_equipment_id:
                target_process_id = eq.get('process_id')
                break
        
        if not current_process_id or not target_process_id:
            return True
        
        # 같은 공정으로는 이동 가능
        if current_process_id == target_process_id:
            return True
        
        # 공정 순서 확인
        product = self.master_data.products.get(batch_data['product_id'])
        if not product:
            return True
        
        process_order = product.get('process_order', [])
        if current_process_id not in process_order or target_process_id not in process_order:
            return True
        
        current_idx = process_order.index(current_process_id)
        target_idx = process_order.index(target_process_id)
        
        # 역순 이동은 불가
        if target_idx < current_idx:
            return False
        
        # 이전 공정이 완료되었는지 확인
        for i in range(current_idx, target_idx):
            process_id = process_order[i]
            found = False
            for batch in same_lot_batches:
                if hasattr(batch, 'process_id') and batch.process_id == process_id:
                    found = True
                    break
            if not found and i < target_idx:
                return False
        
        # 이전 공정의 완료 시점 확인 (다음 구간에서 시작해야 함)
        if target_idx > 0:
            prev_process_id = process_order[target_idx - 1]
            for batch in same_lot_batches:
                if hasattr(batch, 'process_id') and batch.process_id == prev_process_id:
                    # 이전 공정의 종료 구간 계산
                    prev_hour = batch.start_time.hour
                    prev_slot = 0
                    if prev_hour >= 8 and prev_hour < 10:
                        prev_slot = 0
                    elif prev_hour >= 10 and prev_hour < 12:
                        prev_slot = 1
                    elif prev_hour >= 13 and prev_hour < 15:
                        prev_slot = 2
                    elif prev_hour >= 15 and prev_hour < 17:
                        prev_slot = 3
                    
                    duration_slots = max(1, int(batch.duration_hours / 2))
                    prev_end_slot = prev_slot + duration_slots - 1
                    
                    # 같은 날인 경우 다음 구간에서 시작해야 함
                    if batch.start_time.date() == target_container.date:
                        if target_container.slot != prev_end_slot + 1:
                            return False
                    # 다음 날인 경우 첫 구간부터 가능
                    elif batch.start_time.date() < target_container.date:
                        return True
                    else:
                        return False
        
        return True
    
    def _remove_batch_from_grid(self, batch_id: str):
        """그리드에서 배치 제거"""
        if batch_id in self.batch_labels:
            batch_label = self.batch_labels[batch_id]
            
            # 그리드에서 위젯 제거
            index = self.grid_layout.indexOf(batch_label)
            if index != -1:
                self.grid_layout.takeAt(index)
                batch_label.setParent(None)
            
            # 숨겨진 슬롯들 다시 표시
            if batch_id in self.production_plan.batches:
                batch = self.production_plan.batches[batch_id]
                date = batch.start_time.date()
                
                # 시작 슬롯 계산
                hour = batch.start_time.hour
                start_slot = 0
                if hour >= 8 and hour < 10:
                    start_slot = 0
                elif hour >= 10 and hour < 12:
                    start_slot = 1
                elif hour >= 13 and hour < 15:
                    start_slot = 2
                elif hour >= 15 and hour < 17:
                    start_slot = 3
                
                duration_slots = max(1, int(batch.duration_hours / 2))
                
                # 해당 슬롯들의 점유 해제
                for s in range(duration_slots):
                    key = (batch.equipment_id, date, start_slot + s)
                    if key in self.containers:
                        self.containers[key].batch = None
                        self.containers[key].show()  # 숨겨진 슬롯 다시 표시
    
    def _remove_batch_from_grid_and_restore_slots(self, batch_id: str):
        """그리드에서 배치 제거하고 슬롯 복원"""
        if batch_id not in self.batch_labels:
            return
        
        batch_label = self.batch_labels[batch_id]
        
        # 현재 위치 정보 가져오기
        if batch_id in self.production_plan.batches:
            batch = self.production_plan.batches[batch_id]
            date = batch.start_time.date()
            
            # 시작 슬롯 계산 - 구간 기반
            hour = batch.start_time.hour
            if 0 <= hour <= 3:
                start_slot = hour
            else:
                # 레거시 처리
                if hour >= 8 and hour < 10:
                    start_slot = 0
                elif hour >= 10 and hour < 12:
                    start_slot = 1
                elif hour >= 13 and hour < 15:
                    start_slot = 2
                elif hour >= 15 and hour < 17:
                    start_slot = 3
                else:
                    start_slot = 0
            
            duration_slots = max(1, int(batch.duration_hours / 2))
            
            # 저장된 위치 정보 사용
            if batch_label.current_row != -1 and batch_label.current_col != -1:
                row = batch_label.current_row
                col_start = batch_label.current_col
                
                # 숨겨진 슬롯들 다시 표시
                for slot_offset in range(duration_slots):
                    col = col_start + slot_offset
                    # 슬롯 복원을 위해 위젯 찾기
                    for key, container in self.containers.items():
                        if isinstance(container, EquipmentTimeSlot):
                            # 해당 위치의 슬롯 찾기
                            idx = self.grid_layout.indexOf(container)
                            if idx != -1:
                                r, c, _, _ = self.grid_layout.getItemPosition(idx)
                                if r == row and c == col:
                                    container.batch = None
                                    container.show()
                                    container.setStyleSheet("""
                                        QFrame {
                                            background-color: #ffffff;
                                            border: 1px solid #dee2e6;
                                            border-style: solid;
                                        }
                                        QFrame:hover {
                                            background-color: #f8f9fa;
                                        }
                                    """)
                                    break
            else:
                # 기존 방식으로 슬롯 복원
                for s in range(duration_slots):
                    key = (batch.equipment_id, date, start_slot + s)
                    if key in self.containers:
                        self.containers[key].batch = None
                        self.containers[key].show()
                        self.containers[key].setStyleSheet("""
                            QFrame {
                                background-color: #ffffff;
                                border: 1px solid #dee2e6;
                                border-style: solid;
                            }
                            QFrame:hover {
                                background-color: #f8f9fa;
                            }
                        """)
        
        # 그리드에서 위젯 제거
        index = self.grid_layout.indexOf(batch_label)
        if index != -1:
            self.grid_layout.takeAt(index)
            batch_label.setParent(None)
    
    def _move_batch_visual(self, batch_id: str, target_container):
        """배치를 시각적으로만 이동 (전체 새로고침 없이)"""
        if batch_id not in self.batch_labels:
            return
            
        batch_label = self.batch_labels[batch_id]
        batch = self.production_plan.batches[batch_id]
        
        # 새 위치 계산
        target_date = target_container.date
        target_slot = target_container.slot
        
        # 배치의 duration에 따른 슬롯 수 계산
        duration_slots = max(1, int(batch.duration_hours / 2))
        
        # 새 위치가 유효한지 확인
        can_place = True
        for slot_offset in range(duration_slots):
            slot_idx = target_slot + slot_offset
            if slot_idx >= 4:  # 하루 4구간을 넘어가면
                can_place = False
                break
            
            key = (target_container.equipment_id, target_date, slot_idx)
            if key in self.containers:
                if self.containers[key].batch is not None and self.containers[key].batch != "occupied":
                    can_place = False
                    break
            else:
                can_place = False
                break
        
        if not can_place:
            print("[DEBUG] Cannot place batch at target location")
            return
        
        # 그리드에서 배치 라벨의 현재 위치를 찾기
        row = -1
        if self.master_data and target_container.equipment_id in self.master_data.equipment:
            equipment_name = self.master_data.equipment[target_container.equipment_id]['name']
            
            for r in range(self.grid_layout.rowCount()):
                item = self.grid_layout.itemAtPosition(r, 0)
                if item and item.widget():
                    label = item.widget()
                    if isinstance(label, QLabel) and label.text() == equipment_name:
                        row = r
                        break
        
        if row == -1:
            print("[DEBUG] Cannot find equipment row")
            return
        
        # 열 위치 계산
        days_diff = (target_date - self.date_range[0]).days if hasattr(self, 'date_range') else 0
        col_start = 1 + days_diff * 4 + target_slot
        
        # 새 위치의 슬롯들을 숨기기
        for slot_offset in range(duration_slots):
            col = col_start + slot_offset
            item = self.grid_layout.itemAtPosition(row, col)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, EquipmentTimeSlot):
                    widget.hide()
        
        # 배치 라벨을 새 위치로 이동
        self.grid_layout.addWidget(batch_label, row, col_start, 1, duration_slots)
        
        # 배치 라벨에 새 위치 정보 저장
        batch_label.current_row = row
        batch_label.current_col = col_start
        
        # 새 위치의 슬롯들을 점유 상태로 표시
        for slot_offset in range(duration_slots):
            slot_idx = target_slot + slot_offset
            key = (target_container.equipment_id, target_date, slot_idx)
            if key in self.containers:
                self.containers[key].batch = "occupied"
        
        print(f"[DEBUG] Batch {batch_id} moved to new position (row={row}, col={col_start})")
    
    def paintEvent(self, event):
        """페인트 이벤트 - 연결선 그리기"""
        super().paintEvent(event)
        
        if not self.production_plan:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 배치별로 그룹화
        batches_by_product = {}
        for batch in self.production_plan.batches.values():
            key = (batch.product_id, getattr(batch, 'lot_number', None))
            if key not in batches_by_product:
                batches_by_product[key] = []
            batches_by_product[key].append(batch)
        
        # 각 제품의 공정 순서대로 연결선 그리기
        for (product_id, lot_number), batches in batches_by_product.items():
            # 공정 순서대로 정렬
            if self.master_data and product_id in self.master_data.products:
                product = self.master_data.products[product_id]
                process_order = product.get('process_order', [])
                
                # 공정 순서에 따라 정렬
                sorted_batches = []
                for process_id in process_order:
                    for batch in batches:
                        if hasattr(batch, 'process_id') and batch.process_id == process_id:
                            sorted_batches.append(batch)
                
                # 연결선 그리기
                for i in range(len(sorted_batches) - 1):
                    current_batch = sorted_batches[i]
                    next_batch = sorted_batches[i + 1]
                    
                    if current_batch.id in self.batch_labels and next_batch.id in self.batch_labels:
                        # 위젯 위치 가져오기
                        current_widget = self.batch_labels[current_batch.id]
                        next_widget = self.batch_labels[next_batch.id]
                        
                        # 글로벌 좌표를 로컬 좌표로 변환
                        start_pos = self.mapFromGlobal(current_widget.mapToGlobal(
                            QPoint(current_widget.width(), current_widget.height() // 2)
                        ))
                        end_pos = self.mapFromGlobal(next_widget.mapToGlobal(
                            QPoint(0, next_widget.height() // 2)
                        ))
                        
                        # 색상 설정
                        color = QColor(current_widget.batch.product_id in self.master_data.products and 
                                     self.master_data.products[current_widget.batch.product_id].get('color', '#3498db') or '#3498db')
                        color.setAlpha(180)
                        
                        # 펜 설정
                        pen = painter.pen()
                        pen.setColor(color)
                        pen.setWidth(3)
                        painter.setPen(pen)
                        
                        # 곡선 그리기
                        path = QPainterPath()
                        path.moveTo(start_pos)
                        
                        # 제어점 계산
                        control_x = (start_pos.x() + end_pos.x()) // 2
                        control_y = min(start_pos.y(), end_pos.y()) - 20
                        
                        path.quadTo(QPoint(control_x, control_y), end_pos)
                        painter.drawPath(path)
                        
                        # 화살표 그리기
                        arrow_size = 8
                        angle = 150  # 화살표 각도
                        
                        # 화살표 끝점 계산
                        import math
                        arrow_p1 = QPoint(
                            int(end_pos.x() - arrow_size * math.cos(math.radians(angle))),
                            int(end_pos.y() - arrow_size * math.sin(math.radians(angle)))
                        )
                        arrow_p2 = QPoint(
                            int(end_pos.x() - arrow_size * math.cos(math.radians(-angle))),
                            int(end_pos.y() - arrow_size * math.sin(math.radians(-angle)))
                        )
                        
                        painter.drawLine(end_pos, arrow_p1)
                        painter.drawLine(end_pos, arrow_p2)
    
    def extract_schedule_from_grid(self):
        """그리드에서 현재 스케줄을 추출하여 DataFrame으로 반환"""
        import pandas as pd
        
        schedule_data = []
        
        # 그리드의 모든 행과 열을 순회
        for row in range(2, self.grid_layout.rowCount()):  # 헤더 2줄 제외
            # 장비 정보 가져오기
            equipment_item = self.grid_layout.itemAtPosition(row, 0)
            if not equipment_item or not equipment_item.widget():
                continue
                
            equipment_label = equipment_item.widget()
            if not isinstance(equipment_label, QLabel):
                continue
                
            equipment_name = equipment_label.text()
            
            # 해당 행의 모든 배치 찾기
            for col in range(1, self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(row, col)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, DraggableBatchLabel):
                        # 배치 정보 수집
                        batch = widget.batch
                        
                        # 날짜와 슬롯 계산
                        days = (col - 1) // 4  # 하루 4구간
                        slot = (col - 1) % 4
                        date = self.date_range[days] if hasattr(self, 'date_range') and days < len(self.date_range) else None
                        
                        if date:
                            # 시간 계산 (각 슬롯은 2시간)
                            hour = slot * 2 + 8  # 8시부터 시작
                            
                            schedule_data.append({
                                'batch_id': batch.id,
                                'product_id': batch.product_id,
                                'product_name': batch.product_name,
                                'equipment_name': equipment_name,
                                'equipment_id': batch.equipment_id,
                                'date': date,
                                'start_hour': hour,
                                'duration_hours': batch.duration_hours,
                                'lot_number': getattr(batch, 'lot_number', '')
                            })
        
        # DataFrame으로 변환
        df = pd.DataFrame(schedule_data)
        
        # 정렬
        if not df.empty:
            df = df.sort_values(['date', 'equipment_name', 'start_hour'])
        
        return df
    
    def get_equipment_id_from_name(self, equipment_name):
        """장비명으로 장비 ID 찾기"""
        if self.master_data:
            for eq_id, eq_data in self.master_data.equipment.items():
                if eq_data.get('name') == equipment_name:
                    return eq_id
        return None