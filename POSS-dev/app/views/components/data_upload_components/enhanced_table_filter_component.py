from PyQt5.QtGui import QBrush, QColor, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QHeaderView, QMenu, QWidgetAction,
    QCheckBox, QScrollArea
)
from PyQt5.QtCore import (
    pyqtSignal, Qt, QAbstractTableModel, QModelIndex,
    QVariant, QSortFilterProxyModel, QPoint, QTimer
)
import pandas as pd
import numpy as np
from app.resources.fonts.font_manager import font_manager
from app.utils.command.undo_command import undo_redo_manager, DataCommand
from app.models.common.screen_manager import *

"""
헤더 필터링을 위한 사용자 정의 헤더
"""
class FilterHeader(QHeaderView):

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)

    def paintSection(self, painter, rect, logicalIndex):
        super().paintSection(painter, rect, logicalIndex)
        # 필터 아이콘이나 추가 표시가 필요한 경우 여기에 구현


"""
다중 필터 프록시 모델
"""
class MultiFilterProxy(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        # 컬럼 인덱스 -> 선택된 값 리스트
        self.filters = {}

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if not self.filters:
            return True

        model = self.sourceModel()
        for col, vals in self.filters.items():
            if not vals:
                continue

            cell = model.data(model.index(sourceRow, col), Qt.DisplayRole)
            if cell not in vals:
                return False

        return True

    def sort(self, column, order=Qt.AscendingOrder):
        super().sort(column, order)
    
    def lessThan(self, left, right):
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)

        try:
            # 숫자 비교 시도 (정수/실수 모두 지원)
            return float(left_data) < float(right_data)
        except (ValueError, TypeError):
            # 숫자가 아니면 문자열 사전식 비교
            return str(left_data) < str(right_data)

"""
pandas DataFrame을 위한 테이블 모델
"""
class PandasModel(QAbstractTableModel):

    def __init__(self, df=None, parent=None):
        super().__init__(parent)
        self._df = pd.DataFrame() if df is None else df

    def rowCount(self, parent=QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    # PandasModel 클래스의 data 메서드에 다음 코드 추가:
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        value = self._df.iat[index.row(), index.column()]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            # None이나 NaN 값 처리
            if pd.isna(value):
                return ""
            return str(value)

        # 폰트 역할 추가
        elif role == Qt.FontRole:
            font = QFont(font_manager.get_just_font("SamsungOne-700").family())
            font.setPixelSize(f(14))
            return font

        # 배경색 역할 추가 (필요 시)
        elif role == Qt.BackgroundRole:
            # 특정 조건에 따라 다른 배경색 반환 가능
            # 예: 특정 값에 따라 배경색 변경
            return QBrush(QColor("white"))

        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._df.columns[section]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(self._df.index[section])
        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False

        try:
            row, col = index.row(), index.column()

            # 빈 문자열이 입력되면 NaN으로 변경
            if value == "":
                import numpy as np
                self._df.iloc[row, col] = np.nan
                self.dataChanged.emit(index, index)
                return True

            # 컬럼의 데이터 타입 가져오기 - iloc 사용하여 경고 제거
            column_dtype = self._df.dtypes.iloc[col]

            # 데이터 타입에 따른 적절한 변환
            try:
                if pd.api.types.is_integer_dtype(column_dtype):
                    converted_value = int(value)
                elif pd.api.types.is_float_dtype(column_dtype):
                    converted_value = float(value)
                else:
                    converted_value = str(value)
            except ValueError:
                # 변환 실패시 문자열로 처리
                converted_value = str(value)

            # 데이터프레임 업데이트 - 명시적 형변환
            self._df.iloc[row, col] = converted_value
            self.dataChanged.emit(index, index)

            # 엔터키 후 원본과 비교하여 상태 업데이트
            from app.models.common.file_store import DataStore

            # 모델이 속한 테이블 뷰 찾기
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'table_view') and hasattr(parent, 'edited_cells'):
                    # EnhancedTableFilterComponent 인스턴스 찾음
                    filter_component = parent

                    # 원본 데이터와 비교
                    if hasattr(filter_component, '_file_path') and hasattr(filter_component, '_sheet_name'):
                        original_df_dict = DataStore.get('original_dataframes', {})
                        key = f'{filter_component._file_path}:{filter_component._sheet_name}' if filter_component._sheet_name else filter_component._file_path
                        original_df = original_df_dict.get(key)

                        if original_df is not None:
                            try:
                                if 0 <= row < len(original_df) and 0 <= col < len(original_df.columns):
                                    original_value = original_df.iloc[row, col]

                                    # 원본 값과 현재 값 문자열 변환하여 비교
                                    if pd.isna(original_value):
                                        original_str = ""
                                    else:
                                        original_str = str(original_value)

                                    current_str = str(converted_value)

                                    # 원본과 동일하면 수정 목록에서 제거
                                    if original_str == current_str:
                                        if (row, col) in filter_component.edited_cells:
                                            del filter_component.edited_cells[(row, col)]
                                            print(f"셀 ({row}, {col})이 원본 값으로 되돌아감")

                                            # 모든 수정 사항이 제거되었는지 확인
                                            if not filter_component.edited_cells:
                                                # 데이터 입력 페이지 찾기
                                                data_input_page = None
                                                p = filter_component.parent()
                                                while p is not None:
                                                    if hasattr(p,
                                                               '__class__') and 'DataInputPage' in p.__class__.__name__:
                                                        data_input_page = p
                                                        break
                                                    p = p.parent()

                                                # 수정 표시 제거
                                                if data_input_page:
                                                    data_input_page.data_modifier.remove_modified_status_in_sidebar(
                                                        filter_component._file_path, filter_component._sheet_name)
                                                    data_input_page.tab_manager.update_tab_title(
                                                        filter_component._file_path, filter_component._sheet_name,
                                                        False)

                                    # 데이터 변경 시그널 발생
                                    filter_component.data_changed.emit()
                            except Exception as e:
                                print(f"원본 데이터 비교 오류: {e}")
                    break

                if hasattr(parent, 'parent'):
                    parent = parent.parent()
                else:
                    parent = None

            return True
        except Exception as e:
            print("데이터 수정 오류:", e)
            return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


"""
커스텀 메뉴 클래스 - 구분선 없는 스타일 적용
"""
class CustomMenu(QMenu):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #cccccc;
                padding: 0px;
                margin: 0px;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
                border: none;
                margin: 0px;
            }
            QMenu::item:selected {
                background-color: #f0f0f0;
                color: black;
            }
            QMenu::separator {
                height: 0px;
                margin: 0px;
                padding: 0px;
                border: none;
                background: transparent;
            }
            QCheckBox {
                border: none;
                margin: 0px;
                padding: 3px;
                spacing: 5px;
                background: transparent;
            }
            QWidget {
                border: none;
                margin: 0px;
                padding: 0px;
            }
            QScrollArea {
                border-bottom: 1px solid #cccccc; 
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #cccccc;
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
        """)


"""
테두리가 없는 체크박스
"""
class NoOutlineCheckBox(QCheckBox):

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QCheckBox {
                border: none;
                background: transparent;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #b1b1b1;
            }
            QCheckBox::indicator:checked {
                background-color: #1428A0;
                border: 1px solid #1428A0;
            }
        """)


"""
향상된 테이블 필터 컴포넌트
헤더 클릭으로 다중 필터 선택 기능 제공
"""
class EnhancedTableFilterComponent(QWidget):
    filter_applied = pyqtSignal()  # 필터가 적용되었을 때 발생하는 시그널
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_view = None
        self.proxy_model = None
        self._df = pd.DataFrame()
        self._original_df = pd.DataFrame()
        self.edited_cells = {}
        self.init_ui()

    def init_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)


        # 테이블 뷰 생성
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        # 테이블 수정가능하게 하는것
        self.table_view.setEditTriggers(QTableView.DoubleClicked | QTableView.EditKeyPressed)
        self.table_view.verticalHeader().setDefaultSectionSize(h(19))
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        # 사용자 정의 헤더 설정
        header = FilterHeader(Qt.Horizontal, self.table_view)
        header.setStyleSheet(f"""
            QHeaderView {{
                border: none;
                background-color: transparent;
                border-radius: 0px;
            }}
            QHeaderView::section {{
                background-color: #F5F5F5;
                border-right: 1px solid #cccccc;
                padding: 2px;
                border-radius: 0px; 
                font-size: {f(16)}px;
                min-height: {h(30)}px;
            }}
        """)
        self.table_view.setHorizontalHeader(header)
        header.setStretchLastSection(False)  # 마지막 열 늘리지 않음
        self.table_view.verticalHeader().setVisible(False)  # 행 번호 숨김

        # 다중 필터 프록시 모델 설정
        self.proxy_model = MultiFilterProxy(self)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.table_view.setModel(self.proxy_model)

        source_model = PandasModel()
        source_model.dataChanged.connect(self.on_data_changed)
        self.proxy_model.setSourceModel(source_model)

        # 헤더 클릭 이벤트 연결
        header.sectionClicked.connect(self.on_header_clicked)

        # 레이아웃에 테이블 뷰 추가
        main_layout.addWidget(self.table_view)

    """
    데이터가 변경되었을 때 호출되는 메서드
    """
    def on_data_changed(self, topLeft, bottomRight) :
        for row in range(topLeft.row(), bottomRight.row() + 1) :
            for col in range(topLeft.column(), bottomRight.column() + 1) :
                source_index = self.proxy_model.mapToSource(self.proxy_model.index(row, col))

                if source_index.isValid() :
                    source_row = source_index.row()
                    source_col = source_index.column()

                    value = self.proxy_model.sourceModel().data(source_index, Qt.DisplayRole)

                    self.edited_cells[(source_row, source_col)] = value

        self.data_changed.emit()

    """
    필터 업데이트 (체크박스 상태 변경시 호출)
    """
    def _update_filter(self, col, value, checked):
        current = set(self.proxy_model.filters.get(col, []))
        if checked:
            current.add(value)
        else:
            current.discard(value)
        self.proxy_model.filters[col] = list(current)
        self.proxy_model.invalidateFilter()
        self.filter_applied.emit()

    """
    체크박스 위젯 생성
    """
    def create_checkbox_widget(self, val, is_checked, col_index):
        widget = QWidget()
        widget.setStyleSheet("border: none; background-color: transparent;")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(0)

        # 테두리가 없는 체크박스 사용
        checkbox = NoOutlineCheckBox(val)
        checkbox.setChecked(is_checked)
        checkbox.toggled.connect(
            lambda checked, v=val, c=col_index: self._update_filter(c, v, checked)
        )

        layout.addWidget(checkbox)
        return widget

    """
    헤더 클릭 시 필터 메뉴 표시
    """
    def on_header_clicked(self, logicalIndex):
        # 현재 컬럼의 고유 값 가져오기
        col_name = self._df.columns[logicalIndex]
        raw = self._df[col_name].dropna().tolist()

        # 숫자인 경우 숫자 정렬로 처리, 아닌 경우 문자열 정렬
        try:
            nums = sorted({float(v) for v in raw})
            vals = [str(int(n)) if n.is_integer() else str(n) for n in nums]
        except ValueError:
            vals = sorted(set(raw), key=lambda x: str(x))

        # 커스텀 메뉴 생성 (구분선 없는 스타일)
        menu = CustomMenu(self)
        header = self.table_view.horizontalHeader()
        width = header.sectionSize(logicalIndex)
        menu.setFixedWidth(max(width, 200))  # 최소 너비 설정

        # 최대 높이 설정 (화면 높이의 절반으로 제한)
        screen_height = self.screen().size().height()
        max_menu_height = int(screen_height * 0.5)  # 화면 높이의 50%로 제한

        # 스크롤 영역 생성
        if len(vals) > 10:
            container = QWidget()
            container.setStyleSheet(" background-color: transparent;")
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)

            # 현재 선택된 필터 항목 가져오기
            current = set(self.proxy_model.filters.get(logicalIndex, []))

            # 체크박스 추가
            for v in vals:
                checkbox_widget = self.create_checkbox_widget(v, v in current, logicalIndex)
                container_layout.addWidget(checkbox_widget)

            # 스크롤 영역 설정
            scroll_area = QScrollArea()
            scroll_area.setStyleSheet("background-color: transparent;")
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setMaximumHeight(max_menu_height)
            scroll_area.setWidget(container)

            # 메뉴에 스크롤 영역 추가
            scroll_action = QWidgetAction(menu)
            scroll_action.setDefaultWidget(scroll_area)
            menu.addAction(scroll_action)
        else:
            # 아이템이 적은 경우 스크롤 없이 직접 메뉴에 추가
            current = set(self.proxy_model.filters.get(logicalIndex, []))
            for v in vals:
                act = QWidgetAction(menu)
                # 테두리가 없는 체크박스 위젯 사용
                cb_widget = self.create_checkbox_widget(v, v in current, logicalIndex)
                act.setDefaultWidget(cb_widget)
                menu.addAction(act)

        # 정렬 옵션 추가
        menu.addSeparator()
        asc = menu.addAction("Ascending")
        desc = menu.addAction("Descending")

        # 메뉴 표시 위치 계산
        pos = header.mapToGlobal(
            QPoint(header.sectionViewportPosition(logicalIndex), header.height())
        )

        # 메뉴 실행 및 선택 처리
        sel = menu.exec(pos)
        if sel == asc:
            self.proxy_model.sort(logicalIndex, Qt.AscendingOrder)
        elif sel == desc:
            self.proxy_model.sort(logicalIndex, Qt.DescendingOrder)

    """
    데이터프레임 설정
    """
    def set_data(self, df):
        self._df = df.copy()
        self._original_df = df.copy()

        if hasattr(self, '_file_path'):
            self._original_df_for_undo = df.copy()
    
        self.edited_cells = {}

        model = PandasModel(self._df, self)
        model.dataChanged.connect(self.on_data_changed)

        self.proxy_model.filters.clear()
        self.proxy_model.setSourceModel(model)

        # 사용자가 열 너비를 조정할 수 있도록 Interactive 모드 설정
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # 마지막 열이 남은 공간을 채우지 않도록 설정
        self.table_view.horizontalHeader().setStretchLastSection(False)

        # 위젯이 화면에 표시된 후에 열 너비 균등하게 조정 (100ms 지연)
        column_count = len(df.columns)
        QTimer.singleShot(100, lambda: self._adjust_column_widths_evenly())

        self.filter_applied.emit()

    """
    테이블 뷰의 열 너비를 균등하게 조정
    """
    def _adjust_column_widths_evenly(self):
        if self._df.empty:
            return

        total_width = self.table_view.viewport().width()
        column_count = len(self._df.columns)

        if column_count > 0:
            column_width = total_width // column_count
            for i in range(column_count):
                self.table_view.setColumnWidth(i, column_width)

    """
    필터 초기화
    """
    def reset_filter(self):
        self.proxy_model.filters.clear()
        self.proxy_model.invalidateFilter()
        self.filter_applied.emit()

    """
    QTableWidget을 DataFrame으로 변환
    """
    def convert_table_to_dataframe(self, table_widget):
        rows = table_widget.rowCount()
        cols = table_widget.columnCount()

        # 컬럼명 추출
        headers = []
        for col in range(cols):
            item = table_widget.horizontalHeaderItem(col)
            headers.append(item.text() if item else f"Column {col}")

        # 데이터 추출
        data = []
        for row in range(rows):
            row_data = []
            for col in range(cols):
                item = table_widget.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        # DataFrame 생성
        return pd.DataFrame(data, columns=headers)

    """
    필터링된 데이터를 DataFrame으로 반환
    """
    def get_filtered_data(self):
        result_df = self._original_df.copy()

        for (row, col), value in self.edited_cells.items() :
            try :
                if pd.api.types.is_numeric_dtype(result_df.iloc[:, col].dtype) :
                    try :
                        if value.strip() == '' :
                            result_df.iloc[row, col] = np.nan
                        else :
                            if '.' in value :
                                result_df.iloc[row, col] = float(value)
                            else :
                                result_df.iloc[row, col] = int(value)
                    except ValueError :
                        result_df.iloc[row, col] = value
                else :
                    result_df.iloc[row, col] = value
            except (IndexError, ValueError) as e :
                print(f"데이터 업데이트 오류: ({row}, {col}) -> {value}, 에러: {e}")
        
        return result_df
    
    """
    undo/redo 기능을 위한 연결
    """
    def connect_undo_redo_signals(self, file_path, sheet_name):
        self._file_path = file_path
        self._sheet_name = sheet_name
        self._original_df_for_undo = self._df.copy()
        
        self.proxy_model.sourceModel().dataChanged.connect(
            lambda topLeft, bottomRight: self.on_data_changed_for_undo_redo(topLeft, bottomRight)
        )

    """
    데이터 변경 시 undo/redo 호출
    """

    def on_data_changed_for_undo_redo(self, topLeft, bottomRight):
        if not hasattr(self, '_file_path') or not hasattr(self, '_sheet_name'):
            return

        model = topLeft.model()

        for row in range(topLeft.row(), bottomRight.row() + 1):
            for col in range(topLeft.column(), bottomRight.column() + 1):
                source_index = model.index(row, col)

                if not source_index.isValid():
                    continue

                new_value = model.data(source_index, Qt.DisplayRole)

                try:
                    old_value = ""

                    if 0 <= row < len(self._original_df_for_undo) and 0 <= col < len(
                            self._original_df_for_undo.columns):
                        old_value_raw = self._original_df_for_undo.iloc[row, col]

                        if pd.isna(old_value_raw):
                            old_value = ""
                        else:
                            old_value = str(old_value_raw)
                except Exception as e:
                    old_value = ""

                if new_value != old_value:
                    command = DataCommand(
                        file_path=self._file_path,
                        sheet_name=self._sheet_name,
                        row=row,
                        col=col,
                        old_value=old_value,
                        new_value=new_value,
                        update_callback=lambda fp, sn, r, c, v: self.update_cell_value(r, c, v)
                    )

                    undo_redo_manager.execute_command(command)

                    try:
                        # 여기를 수정: dtypes[col] -> dtypes.iloc[col]
                        column_dtype = self._original_df_for_undo.dtypes.iloc[col]
                        converted_value = new_value

                        if pd.api.types.is_integer_dtype(column_dtype):
                            if new_value.strip() == '':
                                converted_value = pd.NA
                            else:
                                try:
                                    converted_value = int(float(new_value))
                                except ValueError:
                                    pass
                        elif pd.api.types.is_float_dtype(column_dtype):
                            if new_value.strip() == '':
                                converted_value = pd.NA
                            else:
                                try:
                                    converted_value = float(new_value)
                                except ValueError:
                                    pass

                        self._original_df_for_undo.iloc[row, col] = converted_value
                    except Exception as e:
                        print(f"원본 데이터프레임 업데이트 오류: {e}")

    """
    undo/redo 시 호출되는 함수
    """

    def update_cell_value(self, row, col, value):
        model = self.proxy_model.sourceModel()
        index = model.index(row, col)

        if index.isValid():
            current_value = model.data(index, Qt.DisplayRole)

            if current_value != value:
                model.setData(index, value, Qt.EditRole)

                if value != "":
                    self.edited_cells[(row, col)] = value
                elif (row, col) in self.edited_cells:
                    del self.edited_cells[(row, col)]

                if hasattr(self, '_original_df_for_undo'):
                    try:
                        # 여기를 수정: dtypes[col] -> dtypes.iloc[col]
                        column_dtype = self._original_df_for_undo.dtypes.iloc[col]
                        converted_value = value

                        if pd.api.types.is_integer_dtype(column_dtype):
                            if value.strip() == '':
                                converted_value = pd.NA
                            else:
                                try:
                                    converted_value = int(float(value))
                                except ValueError:
                                    pass
                        elif pd.api.types.is_float_dtype(column_dtype):
                            if value.strip() == '':
                                converted_value = pd.NA
                            else:
                                try:
                                    converted_value = float(value)
                                except ValueError:
                                    pass

                        self._original_df_for_undo.iloc[row, col] = converted_value
                    except Exception as e:
                        print(f"원본 데이터프레임 업데이트 오류 (undo/redo): {e}")