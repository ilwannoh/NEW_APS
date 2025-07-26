"""
드래그&드롭 문제 확인을 위한 간단한 테스트
"""
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class DraggableItem(QLabel):
    """드래그 가능한 아이템"""
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("background-color: lightblue; border: 1px solid black; padding: 10px;")
        self.setFixedSize(100, 50)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start = event.pos()
            print(f"[DRAG] Mouse pressed on {self.text()}")
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            distance = (event.pos() - self.drag_start).manhattanLength()
            if distance < 5:
                return
            
            print(f"[DRAG] Starting drag for {self.text()}")
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.text())
            drag.setMimeData(mime)
            
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            
            result = drag.exec_(Qt.MoveAction)
            print(f"[DRAG] Drag result: {result}")


class DropZone(QFrame):
    """드롭 가능한 영역"""
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: lightgray; border: 2px dashed black;")
        self.setFixedSize(150, 100)
        
        layout = QVBoxLayout(self)
        self.label = QLabel(name)
        layout.addWidget(self.label)
        
    def dragEnterEvent(self, event):
        print(f"[DROP] Drag entered {self.name}")
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("background-color: yellow; border: 2px solid red;")
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        print(f"[DROP] Drag left {self.name}")
        self.setStyleSheet("background-color: lightgray; border: 2px dashed black;")
    
    def dropEvent(self, event):
        print(f"[DROP] Drop on {self.name}")
        if event.mimeData().hasText():
            text = event.mimeData().text()
            self.label.setText(f"{self.name}\n{text}")
            event.acceptProposedAction()
            self.setStyleSheet("background-color: lightgreen; border: 2px solid green;")
            print(f"[DROP] Successfully dropped '{text}' on {self.name}")
        else:
            event.ignore()


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Drag & Drop Test")
        self.setGeometry(100, 100, 600, 400)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # 왼쪽: 드래그 가능한 아이템들
        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.Box)
        left_layout = QVBoxLayout(left_frame)
        left_layout.addWidget(QLabel("Drag from here:"))
        
        for i in range(3):
            item = DraggableItem(f"Item {i+1}")
            left_layout.addWidget(item)
        left_layout.addStretch()
        
        # 오른쪽: 드롭 영역들
        right_frame = QFrame()
        right_frame.setFrameStyle(QFrame.Box)
        right_layout = QVBoxLayout(right_frame)
        right_layout.addWidget(QLabel("Drop here:"))
        
        for i in range(3):
            zone = DropZone(f"Zone {i+1}")
            right_layout.addWidget(zone)
        right_layout.addStretch()
        
        layout.addWidget(left_frame)
        layout.addWidget(right_frame)
        
        # 상태바
        self.statusBar().showMessage("Drag items from left to right")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())