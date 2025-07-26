from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                             QLabel, QFrame, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor
from app.resources.fonts.font_manager import font_manager


class FileExplorerSidebar(QWidget):
    """
    IDE 스타일의 파일 탐색 사이드바
    파일과 시트를 트리 형태로 보여주는 컴포넌트
    """
    file_or_sheet_selected = pyqtSignal(str, str)  # 파일 경로, 시트 이름 (시트가 없으면 "")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files_data = {}  # {file_path: [sheet_names]}
        self.init_ui()

    def init_ui(self):
        # 메인 위젯의 레이아웃 설정
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 메인 컨테이너 생성
        main_container = QFrame()
        main_container.setStyleSheet("background-color: white; border-radius: 0px; border: 3px solid #CCCCCC;")

        # 메인 컨테이너의 레이아웃 설정
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(0, 0, 0, 0)

        # 타이틀 프레임
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            background-color: #F5F5F5;
            border: none;
            border-radius: 0px;
            border-bottom: 1px solid #CCCCCC;
        """)
        title_frame.setFixedHeight(40)

        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel("Files Explorer")
        title_label_font = QFont()
        title_label_font.setFamily(font_manager.get_just_font("SamsungOne-700").family())
        title_label_font.setPointSize(10)
        title_label.setFont(title_label_font)
        title_label.setStyleSheet("color: black; font-weight: bold;")
        title_layout.addWidget(title_label)

        # 트리 위젯 생성
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)  # 헤더 숨김
        self.tree.setAnimated(True)  # 애니메이션 효과
        self.tree.setIndentation(15)  # 들여쓰기 크기
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border:none;
                margin-left: 10px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 4px;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #1428A0;
                color: white;
                border: none;
            }
            QTreeWidget::item:hover {
                background-color: #E0E0E0;
            }
            QScrollBar:vertical {
                border: none;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #CCCCCC;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        # 선택 변경 이벤트 연결
        self.tree.itemClicked.connect(self.on_item_clicked)

        # 컨테이너 레이아웃에 위젯 추가
        layout.addWidget(title_frame)
        layout.addWidget(self.tree)

        # 메인 레이아웃에 컨테이너 추가
        main_layout.addWidget(main_container)

        # 전체 프레임에 스타일 적용
        self.setStyleSheet("""
            border: 1px solid #CCCCCC;
            border-radius: 10px;
        """)

        # 최소 너비 설정
        self.setMinimumWidth(120)

    def add_file(self, file_path, sheet_names=None, is_modified=False):
        """파일을 트리에 추가 - 수정 상태 표시 지원"""
        # 이미 있는 파일인지 확인
        if file_path in self.files_data:
            # 기존 아이템 업데이트
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if item.data(0, Qt.UserRole) == file_path:
                    # 기존 시트 정보 업데이트
                    self._update_sheets(item, sheet_names, is_modified)
                    return item
        else:
            # 새 파일 아이템 추가
            file_name = file_path.split('/')[-1]

            # 수정된 파일인 경우 표시
            if is_modified:
                file_name += " *"

            # 파일 아이콘 설정 (확장자에 따라 다른 아이콘 사용 가능)
            file_item = QTreeWidgetItem()
            file_item.setText(0, file_name)
            file_item.setData(0, Qt.UserRole, file_path)  # 파일 경로 저장

            # 폰트 설정
            font = QFont(font_manager.get_just_font("SamsungOne-700").family(), 9)
            font.setBold(True)
            file_item.setFont(0, font)

            # 파일 타입에 따라 다른 색 적용
            if file_path.endswith(('.xls', '.xlsx')):
                file_item.setForeground(0, QColor("#1428A0"))  # 엑셀 파일은 녹색
            elif file_path.endswith('.csv'):
                file_item.setForeground(0, QColor("#8B4513"))  # CSV 파일은 갈색

            # 수정된 파일인 경우 색상 변경
            if is_modified:
                file_item.setForeground(0, QColor("#E74C3C"))  # 수정된 파일은 빨간색

            self.tree.addTopLevelItem(file_item)

            # 시트 정보 저장
            self.files_data[file_path] = sheet_names or []

            # 시트 아이템 추가
            self._update_sheets(file_item, sheet_names, is_modified)

            # 파일 노드 확장
            file_item.setExpanded(True)

            return file_item

    def _update_sheets(self, file_item, sheet_names, is_modified=False):
        """파일 아이템에 시트 업데이트 - 수정 상태 표시 지원"""
        # 기존 자식 아이템 모두 제거
        while file_item.childCount() > 0:
            file_item.removeChild(file_item.child(0))

        # 시트가 없으면 종료
        if not sheet_names:
            return

        # 시트 아이템 추가
        for sheet in sheet_names:
            sheet_item = QTreeWidgetItem()

            # 수정된 시트인 경우 표시
            sheet_text = sheet
            if is_modified:
                sheet_text += " *"

            sheet_item.setText(0, sheet_text)
            sheet_item.setData(0, Qt.UserRole + 1, sheet)  # 시트 이름 저장

            font = QFont(font_manager.get_just_font("SamsungOne-700").family(), 9)
            sheet_item.setFont(0, font)

            # 수정된 시트인 경우 색상 변경
            if is_modified:
                sheet_item.setForeground(0, QColor("#E74C3C"))  # 수정된 시트는 빨간색

            file_item.addChild(sheet_item)

    def remove_file(self, file_path):
        """파일을 트리에서 제거"""
        if file_path not in self.files_data:
            return False

        # 트리에서 해당 파일 아이템 찾아 제거
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == file_path:
                self.tree.takeTopLevelItem(i)
                break

        # 데이터에서 제거
        del self.files_data[file_path]
        return True

    def on_item_clicked(self, item, column):
        """아이템 클릭 시 호출되는 함수"""
        # 파일 아이템인 경우
        if item.parent() is None:
            file_path = item.data(0, Qt.UserRole)
            # 파일 자체 선택 시 시트 없음 (빈 문자열)
            self.file_or_sheet_selected.emit(file_path, "")
        # 시트 아이템인 경우
        else:
            file_path = item.parent().data(0, Qt.UserRole)
            sheet_name = item.data(0, Qt.UserRole + 1)
            self.file_or_sheet_selected.emit(file_path, sheet_name)

    def select_first_item(self):
        """첫 번째 아이템 선택"""
        if self.tree.topLevelItemCount() > 0:
            first_item = self.tree.topLevelItem(0)
            self.tree.setCurrentItem(first_item)
            self.on_item_clicked(first_item, 0)

    def clear(self):
        """모든 아이템 제거"""
        self.tree.clear()
        self.files_data.clear()

    def select_file_or_sheet(self, file_path, sheet_name=None):
        """특정 파일과 시트를 선택 상태로 만듦"""
        # 먼저 해당 파일 찾기
        file_item = None
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == file_path:
                file_item = item
                break

        if not file_item:
            return False  # 파일이 없는 경우

        # 파일 아이템 확장
        file_item.setExpanded(True)

        # 시트명이 지정된 경우, 해당 시트 찾기
        if sheet_name and sheet_name in self.files_data.get(file_path, []):
            # 해당 시트 아이템 찾기
            sheet_item = None
            for i in range(file_item.childCount()):
                child = file_item.child(i)
                if child.data(0, Qt.UserRole + 1) == sheet_name:
                    sheet_item = child
                    break

            if sheet_item:
                # 시트 아이템 선택
                self.tree.setCurrentItem(sheet_item)
                return True

        # 시트가 없거나 찾지 못한 경우, 파일 자체 선택
        self.tree.setCurrentItem(file_item)
        return True