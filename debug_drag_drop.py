"""
드래그&드롭 디버그 테스트
문제점 분석을 위한 테스트 스크립트
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QDrag, QPalette, QColor, QPixmap
import json


class DebugDraggableLabel(QLabel):
    """디버그용 드래그 가능한 라벨"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFrameStyle(QFrame.Box)
        self.setMinimumSize(100, 50)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: lightblue; border: 2px solid blue;")
        
    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        print(f"[DEBUG] mousePressEvent - Button: {event.button()}")
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            print(f"[DEBUG] Drag start position saved: {self.drag_start_position}")
    
    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        print(f"[DEBUG] mouseMoveEvent - Buttons: {event.buttons()}")
        
        if not (event.buttons() & Qt.LeftButton):
            print("[DEBUG] Left button not pressed, ignoring")
            return
        
        distance = (event.pos() - self.drag_start_position).manhattanLength()
        print(f"[DEBUG] Manhattan distance: {distance}")
        
        if distance < 10:
            print("[DEBUG] Distance too small, not starting drag")
            return
        
        print("[DEBUG] Starting drag operation")
        
        # 드래그 시작
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 데이터 설정
        data = {"text": self.text(), "source": "draggable_label"}
        mime_data.setText(json.dumps(data))
        drag.setMimeData(mime_data)
        
        # 픽스맵 생성
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        print("[DEBUG] Executing drag...")
        result = drag.exec_(Qt.MoveAction)
        print(f"[DEBUG] Drag result: {result}")


class DebugDropZone(QFrame):
    """디버그용 드롭 존"""
    
    batch_dropped = pyqtSignal(object)
    
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box)
        self.setMinimumSize(150, 100)
        self.setStyleSheet("background-color: lightgray; border: 2px solid gray;")
        
        layout = QVBoxLayout(self)
        self.label = QLabel(name)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
    def dragEnterEvent(self, event):
        """드래그 진입 이벤트"""
        print(f"[DEBUG] {self.name} - dragEnterEvent")
        print(f"[DEBUG] Has text: {event.mimeData().hasText()}")
        print(f"[DEBUG] Text: {event.mimeData().text()}")
        
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("background-color: lightyellow; border: 2px solid orange;")
            print(f"[DEBUG] {self.name} - Accepted drag enter")
        else:
            event.ignore()
            print(f"[DEBUG] {self.name} - Ignored drag enter")
    
    def dragLeaveEvent(self, event):
        """드래그 떠남 이벤트"""
        print(f"[DEBUG] {self.name} - dragLeaveEvent")
        self.setStyleSheet("background-color: lightgray; border: 2px solid gray;")
    
    def dropEvent(self, event):
        """드롭 이벤트"""
        print(f"[DEBUG] {self.name} - dropEvent")
        
        if event.mimeData().hasText():
            data = json.loads(event.mimeData().text())
            print(f"[DEBUG] Dropped data: {data}")
            
            self.label.setText(f"{self.name}\n{data['text']}")
            event.acceptProposedAction()
            self.batch_dropped.emit(data)
            print(f"[DEBUG] {self.name} - Drop accepted")
        
        self.setStyleSheet("background-color: lightgreen; border: 2px solid green;")


class DebugMainWindow(QMainWindow):
    """디버그 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("드래그&드롭 디버그 테스트")
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout(central_widget)
        
        # 왼쪽: 드래그 가능한 아이템들
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("드래그 가능한 아이템"))
        
        for i in range(3):
            label = DebugDraggableLabel(f"Item {i+1}")
            left_layout.addWidget(label)
        
        left_layout.addStretch()
        
        # 오른쪽: 드롭 존들
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("드롭 존"))
        
        for i in range(3):
            drop_zone = DebugDropZone(f"Zone {i+1}")
            drop_zone.batch_dropped.connect(self.on_item_dropped)
            right_layout.addWidget(drop_zone)
        
        right_layout.addStretch()
        
        # 패널 추가
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
    def on_item_dropped(self, data):
        """아이템 드롭 처리"""
        print(f"[MAIN] Item dropped: {data}")


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 드래그 거리 설정 확인
    print(f"[DEBUG] startDragDistance: {app.startDragDistance()}")
    
    window = DebugMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()