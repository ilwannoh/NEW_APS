from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtWidgets import (
    QWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy,
    QDialog, QMessageBox, QFrame, QLabel
)
from PyQt5.QtCore import pyqtSignal, Qt

from .open_dynamic_properties_dialog import DynamicPropertiesDialog
from app.models.common.file_store import FilePaths
from app.models.common.event_bus import EventBus
from app.resources.fonts.font_manager import font_manager


class ParameterComponent(QWidget):
    show_failures = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.failures = {}
        self.current_metric = None
        self._pa_view = 'item'

        self.metric_key_map = {
            'Production Capacity': 'production_capacity',
            'Materials': 'materials',
            'Current Shipment': 'current_shipment',
            'Preassignment': 'preassign',
            'Shippable Quantity': 'shippable_quantity',
            'Plan Adherence Rate': 'plan_adherence_rate',
        }

        self.header_map = {
            'Production Capacity': [
                ('Center', 'center'),
                ('Line', 'line'),
                ('Cap Limit', 'cap_limit'),
                ('Available', 'available'),
                ('Excess', 'excess'),
            ],
            'Materials': [
                ('Material ID', 'material_id'),
                ('Line', 'line'),
                ('Issue', 'reason'),
                ('Stock Avail', 'available'),
                ('Shortage', 'excess'),
            ],
            'Current Shipment': [
                ('Ship ID', 'ship_id'),
                ('Line', 'line'),
                ('Delay Reason', 'reason'),
                ('Can Ship', 'available'),
                ('OverQty', 'excess'),
            ],
            'Preassignment': [
                ('Line', 'line'),
                ('Alloc Reason', 'reason'),
                ('Pending', 'excess'),
            ],
            'Shippable Quantity': [
                ('Ship Date', 'ship_date'),
                ('Line', 'line'),
                ('Shippable', 'available'),
                ('Avail Qty', 'available'),
                ('Excess', 'excess'),
            ],
            'Plan Adherence Rate': {
                'item': [
                    ('Line', 'line'),
                    ('Item', 'item'),
                    ('Prev Qty', 'prev_qty'),
                    ('New Qty', 'new_qty'),
                    ('Maint Qty', 'maintain_qty'),
                    ('Rate', 'maint_rate'),
                ],
                'rmc': [
                    ('Line', 'line'),
                    ('RMC', 'rmc'),
                    ('Prev Qty', 'prev_qty'),
                    ('New Qty', 'new_qty'),
                    ('Maint Qty', 'maintain_qty'),
                    ('Rate', 'maint_rate'),
                ]
            },
        }

        self.dynamic_props_btn = QPushButton("Dynamic 속성 설정")
        self.dynamic_props_btn.setFont(font_manager.get_font('SamsungOne-700', 9))
        self.dynamic_props_btn.setCursor(Qt.PointingHandCursor)
        self.dynamic_props_btn.setFixedHeight(32)
        self.dynamic_props_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.dynamic_props_btn.clicked.connect(self.open_dynamic_properties_dialog)
        self.dynamic_props_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #1428A0;
                border: 2px solid #1428A0;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E8ECFF;
            }
            QPushButton:pressed {
                background-color: #D1D9FF;
            }
        """)

        self.dynamic_props_btn.setVisible(bool(FilePaths.get("dynamic_excel_file")))

        self.buttons = {}
        self._init_ui()
        self._build_metric_buttons()
        self.failure_table.header().hide()
        self.show_failures.connect(self._on_failures)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 전체 배경색 설정
        self.setStyleSheet("background-color: white; border: none;")

        # 버튼 영역을 위한 프레임
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border: none;
                border-bottom: 1px solid #E0E0E0;
            }
        """)

        self.button_bar = QHBoxLayout(button_frame)
        self.button_bar.setSpacing(5)
        self.button_bar.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(button_frame)

        # 컨텐츠 영역
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # 테이블 컨테이너
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.failure_table = QTreeWidget()
        self.failure_table.setRootIsDecorated(False)
        self.failure_table.setSortingEnabled(True)
        self.failure_table.setStyleSheet("""
            QTreeWidget { 
                border: none; 
                outline: none;
                background-color: white;
                border-radius: 8px;
                font-family: %s;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #F5F5F5;
            }
            QTreeWidget::item:selected {
                background-color: #E8ECFF;
                color: black;
            }
            QTreeWidget::item:hover {
                background-color: #F5F7FF;
            }
            QHeaderView::section { 
                background-color: #F5F5F5;
                color: #333333;
                border: none;
                padding: 8px;
                font-weight: bold;
                border-bottom: 2px solid #E0E0E0;
            }
        """ % font_manager.get_just_font("SamsungOne-700").family())

        table_layout.addWidget(self.failure_table)
        content_layout.addWidget(table_container)
        layout.addWidget(content_frame)

    def _build_metric_buttons(self):
        for i in reversed(range(self.button_bar.count())):
            w = self.button_bar.takeAt(i).widget()
            if w:
                w.deleteLater()
        self.buttons.clear()

        for label in self.metric_key_map:
            btn = QPushButton(label)
            btn_font = font_manager.get_font('SamsungOne-700', 9)
            btn_font.setBold(True)
            btn.setFont(btn_font)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.clicked.connect(lambda _, lb=label: self._on_metric_clicked(lb))
            self.button_bar.addWidget(btn)
            self.buttons[label] = btn

        self.button_bar.addStretch()
        self.button_bar.addWidget(self.dynamic_props_btn)
        self._update_button_styles()

    def _on_failures(self, failures: dict):
        self.failures = failures
        self._build_metric_buttons()

        if failures.get('production_capacity'):
            self.current_metric = 'Production Capacity'
        elif failures.get('plan_adherence_rate'):
            self.current_metric = 'Plan Adherence Rate'
        else:
            for lbl, key in self.metric_key_map.items():
                if failures.get(key):
                    self.current_metric = lbl
                    break

        self._populate_for_metric(self.current_metric)

    def _on_metric_clicked(self, label: str):
        self.current_metric = label

        if label == 'Production Capacity':
            EventBus.emit('show_project_analysis', True)
        else:
            EventBus.emit('show_project_analysis', False)

        if label == 'Plan Adherence Rate':
            self._pa_view = 'rmc' if self._pa_view == 'item' else 'item'
        else:
            self.current_metric = label

        self._populate_for_metric(label)
        self._update_button_styles()

    def _populate_for_metric(self, label: str):
        key = self.metric_key_map[label]

        if label == 'Plan Adherence Rate':
            pa = self.failures.get('plan_adherence_rate', {})
            data = pa.get(f"{self._pa_view}_failures", [])
            fields = self.header_map[label][self._pa_view]
        else:
            data = self.failures.get(key, []) or []
            fields = self.header_map[label]

        headers = [h for h, _ in fields]
        self.failure_table.clear()
        self.failure_table.setColumnCount(len(headers))
        self.failure_table.setHeaderLabels(headers)
        self.failure_table.header().show()

        red = QBrush(QColor('#e74c3c'))

        if not hasattr(data, '__iter__') or isinstance(data, bool):
            print(f"경고: '{label}'의 데이터는 반복 가능한 객체가 아닙니다. 타입: {type(data)}")
            data = []

        for info in data:
            vals = []
            for _, field in fields:
                if isinstance(info, dict):
                    v = info.get(field, '')
                else:
                    v = getattr(info, field, '')
                vals.append(str(v))

            item = QTreeWidgetItem(vals)
            for col in range(len(vals)):
                item.setForeground(col, red)
            self.failure_table.addTopLevelItem(item)

        self.failure_table.sortItems(0, Qt.AscendingOrder)
        self._update_button_styles()

    def _update_button_styles(self):
        for label, btn in self.buttons.items():
            key = self.metric_key_map[label]
            failure_data = self.failures.get(key)
            has_data = failure_data is not None and (not isinstance(failure_data, list) or len(failure_data) > 0)

            if label == self.current_metric:
                if has_data:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #E74C3C;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            padding: 6px 12px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #C0392B;
                        }
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #1428A0;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            padding: 6px 12px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #0F1F8A;
                        }
                    """)
            elif has_data:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFE5E5;
                        color: #E74C3C;
                        border: 1px solid #E74C3C;
                        border-radius: 5px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #FFCCCC;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        color: #666666;
                        border: 1px solid #E0E0E0;
                        border-radius: 5px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #F5F5F5;
                        color: #1428A0;
                        border-color: #1428A0;
                    }
                """)

    def open_dynamic_properties_dialog(self):
        dlg = DynamicPropertiesDialog(self)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            QMessageBox.information(
                self,
                "설정 저장됨",
                "라인/시프트별 Item 및 RMC 임계값이 저장되었습니다."
            )

    def on_file_selected(self, filepath: str):
        if FilePaths.get("dynamic_excel_file"):
            self.dynamic_props_btn.setVisible(True)

    def set_project_analysis_data(self, data):
        """
        프로젝트 분석 데이터 설정
        """
        self.project_analysis_data = data

        if not data:
            self.failures['production_capacity'] = None
            self._update_button_styles()
            return

        if isinstance(data, dict) and 'display_df' in data:
            display_df = data.get('display_df')

            if display_df is None or (hasattr(display_df, 'empty') and display_df.empty):
                self.failures['production_capacity'] = None
                self._update_button_styles()
                return

            has_issues = False

            try:
                for _, row in display_df.iterrows():
                    if row.get('PJT') == 'Total' and row.get('status') == 'Error':
                        has_issues = True
                        break
            except Exception:
                has_issues = False

            if has_issues:
                issues = []

                try:
                    for _, row in display_df.iterrows():
                        if row.get('PJT') == 'Total' and row.get('status') == 'Error':
                            issues.append({
                                'line': row.get('PJT Group', ''),
                                'reason': '용량 초과',
                                'available': row.get('CAPA', 0),
                                'excess': int(row.get('MFG', 0)) - int(row.get('CAPA', 0)) if row.get('MFG') and row.get('CAPA') else 0,
                                'cap_limit': row.get('CAPA', 0),
                                'center': row.get('PJT Group', '').split('_')[0] if isinstance(row.get('PJT Group', ''), str) and '_' in row.get('PJT Group', '') else ''
                            })
                except Exception:
                    pass

                self.failures['production_capacity'] = issues if issues else None
            else:
                self.failures['production_capacity'] = None

            self._update_button_styles()
        else:
            self.failures['production_capacity'] = None
            self._update_button_styles()