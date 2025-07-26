"""
마스터 데이터 관리 뷰
제품, 공정, 장비, 작업자 정보를 편집하는 UI
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QTableWidget, QTableWidgetItem, QPushButton,
                           QMessageBox, QHeaderView, QAbstractItemView,
                           QDialog, QFormLayout, QLineEdit, QSpinBox,
                           QDoubleSpinBox, QComboBox, QCheckBox, QDialogButtonBox,
                           QLabel, QGroupBox, QColorDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QFont

from app.models.master_data import MasterDataManager
from app.resources.styles.screen_manager import w, h, f
from app.resources.styles.app_style import AppStyle
from app.widgets.filter_table_widget import FilterTableWidget
import json
from datetime import datetime


class MasterDataView(QWidget):
    """마스터 데이터 관리 뷰"""
    
    # 시그널
    data_changed = pyqtSignal()  # 데이터 변경 시
    
    def __init__(self, master_data: MasterDataManager, parent=None):
        super().__init__(parent)
        self.master_data = master_data
        self.init_ui()
        self.load_all_data()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(w(20), h(20), w(20), h(20))
        
        # 헤더
        header_label = QLabel("마스터 데이터 관리")
        header_label.setProperty("class", "heading")
        layout.addWidget(header_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 각 탭 생성
        self.product_tab = self.create_product_tab()
        self.process_tab = self.create_process_tab()
        self.equipment_tab = self.create_equipment_tab()
        self.operator_tab = self.create_operator_tab()
        
        self.tab_widget.addTab(self.product_tab, "제품")
        self.tab_widget.addTab(self.process_tab, "공정")
        self.tab_widget.addTab(self.equipment_tab, "장비")
        self.tab_widget.addTab(self.operator_tab, "작업자")
        
        layout.addWidget(self.tab_widget)
    
    def create_product_tab(self):
        """제품 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_product)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("수정")
        edit_btn.clicked.connect(self.edit_product)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("삭제")
        delete_btn.clicked.connect(self.delete_product)
        btn_layout.addWidget(delete_btn)
        
        # 백업 버튼 추가
        backup_btn = QPushButton("백업")
        backup_btn.clicked.connect(self.backup_data)
        btn_layout.addWidget(backup_btn)
        
        layout.addLayout(btn_layout)
        
        # 테이블
        self.product_table = FilterTableWidget()
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels([
            "제품ID", "제품명", "우선순위", "주요장비", "공정순서", "리드타임(일)"
        ])
        
        # 테이블 설정
        self.product_table.setAlternatingRowColors(True)
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.product_table)
        
        return widget
    
    def create_process_tab(self):
        """공정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_process)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("수정")
        edit_btn.clicked.connect(self.edit_process)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("삭제")
        delete_btn.clicked.connect(self.delete_process)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        # 테이블
        self.process_table = FilterTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["공정ID", "공정명", "기본순서", "기본소요시간(h)"])
        
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.process_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.process_table)
        
        return widget
    
    def create_equipment_tab(self):
        """장비 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_equipment)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("수정")
        edit_btn.clicked.connect(self.edit_equipment)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("삭제")
        delete_btn.clicked.connect(self.delete_equipment)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        # 테이블
        self.equipment_table = FilterTableWidget()
        self.equipment_table.setColumnCount(4)
        self.equipment_table.setHorizontalHeaderLabels([
            "장비ID", "장비명", "공정", "가능제품"
        ])
        
        self.equipment_table.setAlternatingRowColors(True)
        self.equipment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.equipment_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.equipment_table)
        
        return widget
    
    def create_operator_tab(self):
        """작업자 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 설명
        info_label = QLabel(
            "공정별 일자별 작업자 수를 설정합니다.\n"
            "작업자는 2인 1조로 작업하며, 총 용량은 공정 소요시간에 따라 자동 계산됩니다.\n"
            "총 용량 = (작업자 수 ÷ 2) × (8시간 ÷ 공정 소요시간)"
        )
        layout.addWidget(info_label)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_operator)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("수정")
        edit_btn.clicked.connect(self.edit_operator)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("삭제")
        delete_btn.clicked.connect(self.delete_operator)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        # 테이블
        self.operator_table = FilterTableWidget()
        self.operator_table.setColumnCount(4)
        self.operator_table.setHorizontalHeaderLabels([
            "공정", "날짜", "작업자수", "총 용량(블록수)"
        ])
        
        self.operator_table.setAlternatingRowColors(True)
        self.operator_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.operator_table.horizontalHeader().setStretchLastSection(True)
        
        # 셀 변경 시그널 연결
        self.operator_table.itemChanged.connect(self.on_operator_item_changed)
        
        layout.addWidget(self.operator_table)
        
        return widget
    
    def load_all_data(self):
        """모든 데이터 로드"""
        self.load_products()
        self.load_processes()
        self.load_equipment()
        self.load_operators()
    
    def load_products(self):
        """제품 데이터 로드"""
        self.product_table.setRowCount(0)
        
        for product_id, product in self.master_data.products.items():
            row = self.product_table.rowCount()
            self.product_table.insertRow(row)
            
            self.product_table.setItem(row, 0, QTableWidgetItem(product['id']))
            self.product_table.setItem(row, 1, QTableWidgetItem(product['name']))
            self.product_table.setItem(row, 2, QTableWidgetItem(str(product['priority'])))
            self.product_table.setItem(row, 3, QTableWidgetItem(', '.join(product['equipment_list'])))
            
            # 공정순서를 더 명확하게 표시 (공정명으로 표시)
            process_names = []
            for process_id in product['process_order']:
                process = self.master_data.processes.get(process_id)
                if process:
                    process_names.append(f"{process['name']}")
                else:
                    process_names.append(process_id)
            self.product_table.setItem(row, 4, QTableWidgetItem(' → '.join(process_names)))
            
            # 리드타임 표시 (일 단위)
            if 'lead_time_days' in product:
                lead_time_days = product['lead_time_days']
            else:
                # 시간 단위로 저장된 경우 일로 변환
                lead_time_hours = product.get('lead_time_hours', 720)
                lead_time_days = int(lead_time_hours / 24)
            self.product_table.setItem(row, 5, QTableWidgetItem(str(lead_time_days)))
    
    def load_processes(self):
        """공정 데이터 로드"""
        self.process_table.setRowCount(0)
        
        processes = sorted(self.master_data.processes.values(), key=lambda x: x['order'])
        for process in processes:
            row = self.process_table.rowCount()
            self.process_table.insertRow(row)
            
            # 글꼴 색상 적용
            font_color = process.get('font_color', '#000000')
            
            id_item = QTableWidgetItem(process['id'])
            id_item.setForeground(QColor(font_color))
            self.process_table.setItem(row, 0, id_item)
            
            name_item = QTableWidgetItem(process['name'])
            name_item.setForeground(QColor(font_color))
            name_item.setFont(QFont("", -1, QFont.Bold))  # 굵게 표시
            self.process_table.setItem(row, 1, name_item)
            
            order_item = QTableWidgetItem(str(process['order']))
            order_item.setForeground(QColor(font_color))
            self.process_table.setItem(row, 2, order_item)
            
            duration_item = QTableWidgetItem(str(process.get('default_duration_hours', 4.0)))
            duration_item.setForeground(QColor(font_color))
            self.process_table.setItem(row, 3, duration_item)
    
    def load_equipment(self):
        """장비 데이터 로드"""
        self.equipment_table.setRowCount(0)
        
        for equipment_id, equipment in self.master_data.equipment.items():
            row = self.equipment_table.rowCount()
            self.equipment_table.insertRow(row)
            
            self.equipment_table.setItem(row, 0, QTableWidgetItem(equipment['id']))
            self.equipment_table.setItem(row, 1, QTableWidgetItem(equipment['name']))
            self.equipment_table.setItem(row, 2, QTableWidgetItem(equipment['process_id']))
            self.equipment_table.setItem(row, 3, QTableWidgetItem(', '.join(equipment['available_products'])))
    
    def load_operators(self):
        """작업자 데이터 로드"""
        self.operator_table.setRowCount(0)
        
        for key, operator in self.master_data.operators.items():
            row = self.operator_table.rowCount()
            self.operator_table.insertRow(row)
            
            # 공정명 표시
            process = self.master_data.processes.get(operator['process_id'], {})
            process_name = f"{process.get('name', operator['process_id'])} ({operator['process_id']})"
            
            # 공정명과 날짜는 편집 불가
            process_item = QTableWidgetItem(process_name)
            process_item.setFlags(process_item.flags() & ~Qt.ItemIsEditable)
            self.operator_table.setItem(row, 0, process_item)
            
            date_item = QTableWidgetItem(operator['date'])
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.operator_table.setItem(row, 1, date_item)
            
            # 작업자 수는 편집 가능
            self.operator_table.setItem(row, 2, QTableWidgetItem(str(operator['worker_count'])))
            
            # 총 용량 계산 (편집 불가)
            teams = operator['worker_count'] // 2  # 2인 1조
            process_duration = process.get('default_duration_hours', 8.0)
            capacity = teams * (8.0 / process_duration)
            capacity_item = QTableWidgetItem(f"{capacity:.1f}")
            capacity_item.setFlags(capacity_item.flags() & ~Qt.ItemIsEditable)
            self.operator_table.setItem(row, 3, capacity_item)
    
    # 제품 관련 메서드
    def add_product(self):
        """제품 추가"""
        dialog = ProductDialog(self.master_data, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            self.master_data.add_product(**data)
            self.load_products()
            self.data_changed.emit()
    
    def edit_product(self):
        """제품 수정"""
        current_row = self.product_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "수정할 제품을 선택하세요.")
            return
        
        product_id = self.product_table.item(current_row, 0).text()
        product = self.master_data.get_product(product_id)
        
        dialog = ProductDialog(self.master_data, product, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            # product_id가 data에 포함되어 있으면 제거
            if 'product_id' in data:
                data.pop('product_id')
            self.master_data.update_product(product_id, **data)
            self.load_products()
            self.data_changed.emit()
    
    def delete_product(self):
        """제품 삭제"""
        current_row = self.product_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "삭제할 제품을 선택하세요.")
            return
        
        product_id = self.product_table.item(current_row, 0).text()
        product_name = self.product_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, "확인", 
            f"제품 '{product_name}'을(를) 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.master_data.delete_product(product_id)
            self.load_products()
            self.data_changed.emit()
    
    # 공정 관련 메서드
    def add_process(self):
        """공정 추가"""
        dialog = ProcessDialog(parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            self.master_data.add_process(**data)
            self.load_processes()
            self.data_changed.emit()
    
    def edit_process(self):
        """공정 수정"""
        current_row = self.process_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "수정할 공정을 선택하세요.")
            return
        
        process_id = self.process_table.item(current_row, 0).text()
        process = self.master_data.get_process(process_id)
        
        dialog = ProcessDialog(process, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            self.master_data.update_process(process_id, **data)
            self.load_processes()
            self.data_changed.emit()
    
    def delete_process(self):
        """공정 삭제"""
        # 구현 생략 (제품과 유사)
        pass
    
    # 장비 관련 메서드
    def add_equipment(self):
        """장비 추가"""
        dialog = EquipmentDialog(self.master_data, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            self.master_data.add_equipment(**data)
            self.load_equipment()
            self.data_changed.emit()
    
    def edit_equipment(self):
        """장비 수정"""
        # 구현 생략
        pass
    
    def delete_equipment(self):
        """장비 삭제"""
        # 구현 생략
        pass
    
    # 작업자 관련 메서드
    def add_operator(self):
        """작업자 설정 추가"""
        dialog = OperatorDialog(self.master_data, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            self.master_data.set_operator_capacity(**data)
            self.load_operators()
            self.data_changed.emit()
    
    def edit_operator(self):
        """작업자 설정 수정"""
        # 구현 생략
        pass
    
    def delete_operator(self):
        """작업자 설정 삭제"""
        # 구현 생략
        pass
    
    def on_operator_item_changed(self, item):
        """작업자 테이블 항목 변경 시 처리"""
        row = item.row()
        col = item.column()
        
        # 작업자 수 열 변경 시
        if col == 2:  # 작업자수 열
            try:
                worker_count = int(item.text())
                
                # 공정 ID 가져오기
                process_text = self.operator_table.item(row, 0).text()
                # "공정명 (ID)" 형식에서 ID 추출
                process_id = process_text.split('(')[-1].rstrip(')')
                
                # 날짜 가져오기
                date = self.operator_table.item(row, 1).text()
                
                # 공정 정보 가져오기
                process = self.master_data.processes.get(process_id, {})
                duration = process.get('default_duration_hours', 8.0)
                
                # 2인 1조 기준 용량 계산
                teams = worker_count // 2
                capacity = teams * (8.0 / duration)
                
                # 총 용량 셀 업데이트
                capacity_item = QTableWidgetItem(f"{capacity:.1f}")
                self.operator_table.setItem(row, 3, capacity_item)
                
                # 데이터 저장
                operator_key = f"{process_id}_{date}"
                if operator_key not in self.master_data.operators:
                    self.master_data.operators[operator_key] = {
                        'process_id': process_id,
                        'date': date
                    }
                
                self.master_data.operators[operator_key]['worker_count'] = worker_count
                self.master_data.operators[operator_key]['total_capacity'] = capacity
                self.master_data.save_data("operators", self.master_data.operators)
                
                # 데이터 변경 시그널 발생
                self.data_changed.emit()
                
            except ValueError:
                # 잘못된 입력값 처리
                pass
    
    def backup_data(self):
        """데이터 백업"""
        from app.utils.backup_manager import BackupManager
        
        backup_mgr = BackupManager()
        try:
            backup_name = f"manual_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_mgr.create_backup(backup_name)
            QMessageBox.information(self, "백업 완료", f"백업이 완료되었습니다: {backup_name}")
        except Exception as e:
            QMessageBox.critical(self, "백업 실패", f"백업 중 오류가 발생했습니다: {str(e)}")


class ProductDialog(QDialog):
    """제품 추가/수정 다이얼로그"""
    
    def __init__(self, master_data: MasterDataManager, product=None, parent=None):
        super().__init__(parent)
        self.master_data = master_data
        self.product = product
        self.init_ui()
        
        if product:
            self.load_data(product)
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("제품 추가" if not self.product else "제품 수정")
        self.setModal(True)
        self.setMinimumWidth(w(500))
        
        layout = QFormLayout()
        
        # 제품 ID
        self.id_edit = QLineEdit()
        if self.product:
            self.id_edit.setEnabled(False)
        layout.addRow("제품 ID:", self.id_edit)
        
        # 제품명
        self.name_edit = QLineEdit()
        layout.addRow("제품명:", self.name_edit)
        
        # 우선순위
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(5)
        layout.addRow("우선순위:", self.priority_spin)
        
        # 주요 장비 (멀티 선택)
        equipment_group = QGroupBox("주요 장비")
        equipment_layout = QVBoxLayout()
        self.equipment_checks = {}
        
        for eq_id, eq in self.master_data.equipment.items():
            check = QCheckBox(f"{eq['name']} ({eq_id})")
            self.equipment_checks[eq_id] = check
            equipment_layout.addWidget(check)
        
        equipment_group.setLayout(equipment_layout)
        layout.addRow(equipment_group)
        
        # 공정 순서
        process_group = QGroupBox("공정 순서 (체크한 공정만 사용)")
        process_layout = QVBoxLayout()
        
        # 공정 선택 체크박스와 순서 입력
        self.process_widgets = {}
        processes = sorted(self.master_data.processes.values(), key=lambda x: x['order'])
        
        for i, process in enumerate(processes):
            process_widget = QWidget()
            h_layout = QHBoxLayout(process_widget)
            h_layout.setContentsMargins(0, 0, 0, 0)
            
            # 체크박스
            check = QCheckBox(f"{process['name']} ({process['id']})")
            check.setChecked(True)  # 기본적으로 모든 공정 선택
            h_layout.addWidget(check)
            
            # 순서 입력
            order_spin = QSpinBox()
            order_spin.setRange(1, 20)
            order_spin.setValue(i + 1)
            order_spin.setPrefix("순서: ")
            h_layout.addWidget(order_spin)
            
            # 소요시간 입력
            duration_spin = QDoubleSpinBox()
            duration_spin.setRange(0.5, 48.0)
            duration_spin.setSingleStep(0.5)
            duration_spin.setValue(process.get('default_duration_hours', 4.0))
            duration_spin.setSuffix(" 시간")
            h_layout.addWidget(duration_spin)
            
            h_layout.addStretch()
            
            self.process_widgets[process['id']] = {
                'check': check,
                'order': order_spin,
                'duration': duration_spin,
                'widget': process_widget
            }
            
            process_layout.addWidget(process_widget)
        
        process_group.setLayout(process_layout)
        layout.addRow(process_group)
        
        # 전체 리드타임 (일 단위)
        lead_time_layout = QHBoxLayout()
        self.leadtime_spin = QSpinBox()
        self.leadtime_spin.setRange(1, 365)
        self.leadtime_spin.setValue(30)
        self.leadtime_spin.setSuffix(" 일")
        lead_time_layout.addWidget(self.leadtime_spin)
        
        # 공정별 리드타임 설정 버튼
        self.process_leadtime_btn = QPushButton("공정별 리드타임 설정")
        self.process_leadtime_btn.clicked.connect(self.set_process_leadtimes)
        lead_time_layout.addWidget(self.process_leadtime_btn)
        
        layout.addRow("전체 리드타임:", lead_time_layout)
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)
    
    def load_data(self, product):
        """제품 데이터 로드"""
        self.id_edit.setText(product['id'])
        self.name_edit.setText(product['name'])
        self.priority_spin.setValue(product['priority'])
        
        # 리드타임 - 시간을 일로 변환 (기존 데이터 호환성)
        if 'lead_time_days' in product:
            self.leadtime_spin.setValue(product['lead_time_days'])
        else:
            # 시간 단위로 저장된 경우 일로 변환
            lead_time_hours = product.get('lead_time_hours', 720)  # 기본 30일
            self.leadtime_spin.setValue(int(lead_time_hours / 24))
        
        # 장비 선택
        for eq_id in product['equipment_list']:
            if eq_id in self.equipment_checks:
                self.equipment_checks[eq_id].setChecked(True)
        
        # 공정 선택 및 순서
        # 먼저 모든 공정 체크 해제
        for process_id, widgets in self.process_widgets.items():
            widgets['check'].setChecked(False)
        
        # 선택된 공정만 체크하고 순서 설정
        for i, process_id in enumerate(product['process_order']):
            if process_id in self.process_widgets:
                self.process_widgets[process_id]['check'].setChecked(True)
                self.process_widgets[process_id]['order'].setValue(i + 1)
                
                # 제품별 공정 소요시간 로드
                if 'process_details' in product and process_id in product['process_details']:
                    duration = product['process_details'][process_id].get('duration_hours')
                    if duration:
                        self.process_widgets[process_id]['duration'].setValue(duration)
        
        # 공정별 리드타임 로드
        if 'process_leadtimes' in product:
            self.process_leadtimes = product['process_leadtimes']
    
    def get_data(self):
        """입력 데이터 반환"""
        equipment_list = [eq_id for eq_id, check in self.equipment_checks.items() 
                         if check.isChecked()]
        
        # 선택된 공정들을 사용자가 지정한 순서대로 정렬
        selected_processes = []
        process_details = {}
        
        for process_id, widgets in self.process_widgets.items():
            if widgets['check'].isChecked():
                order = widgets['order'].value()
                duration = widgets['duration'].value()
                selected_processes.append((process_id, order))
                
                # 기본값과 다른 경우에만 저장
                process = self.master_data.processes.get(process_id, {})
                default_duration = process.get('default_duration_hours', 4.0)
                if abs(duration - default_duration) > 0.01:  # 부동소수점 비교
                    process_details[process_id] = {
                        'order': order,
                        'duration_hours': duration
                    }
        
        # 순서대로 정렬
        selected_processes.sort(key=lambda x: x[1])
        process_order = [p[0] for p in selected_processes]
        
        data = {
            'product_id': self.id_edit.text(),
            'name': self.name_edit.text(),
            'priority': self.priority_spin.value(),
            'equipment_list': equipment_list,
            'process_order': process_order,
            'lead_time_days': self.leadtime_spin.value(),
            'lead_time': self.leadtime_spin.value() * 24  # 시간 단위로도 저장 (호환성)
        }
        
        # process_details가 있으면 추가
        if process_details:
            data['process_details'] = process_details
        
        # 공정별 리드타임 추가
        if hasattr(self, 'process_leadtimes'):
            data['process_leadtimes'] = self.process_leadtimes
            
        return data
    
    def set_process_leadtimes(self):
        """공정별 리드타임 설정 다이얼로그"""
        dialog = QDialog(self)
        dialog.setWindowTitle("공정별 리드타임 설정")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        # 현재 선택된 공정들의 리드타임 입력 필드
        leadtime_spins = {}
        
        for process_id, widgets in self.process_widgets.items():
            if widgets['check'].isChecked():
                process = self.master_data.processes.get(process_id, {})
                process_name = process.get('name', process_id)
                
                leadtime_spin = QSpinBox()
                leadtime_spin.setRange(0, 30)
                leadtime_spin.setValue(1)  # 기본값 1일
                leadtime_spin.setSuffix(" 일")
                
                # 기존 값이 있으면 로드
                if hasattr(self, 'process_leadtimes') and process_id in self.process_leadtimes:
                    leadtime_spin.setValue(self.process_leadtimes[process_id])
                
                layout.addRow(f"{process_name}:", leadtime_spin)
                leadtime_spins[process_id] = leadtime_spin
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        
        main_layout = QVBoxLayout(dialog)
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)
        
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        if dialog.exec_():
            # 리드타임 저장
            if not hasattr(self, 'process_leadtimes'):
                self.process_leadtimes = {}
            
            for process_id, spin in leadtime_spins.items():
                self.process_leadtimes[process_id] = spin.value()


class ProcessDialog(QDialog):
    """공정 추가/수정 다이얼로그"""
    
    def __init__(self, process=None, parent=None):
        super().__init__(parent)
        self.process = process
        self.init_ui()
        
        if process:
            self.load_data(process)
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("공정 추가" if not self.process else "공정 수정")
        self.setModal(True)
        self.setMinimumWidth(w(350))
        
        layout = QFormLayout()
        
        # 공정 ID
        self.id_edit = QLineEdit()
        if self.process:
            self.id_edit.setEnabled(False)
        layout.addRow("공정 ID:", self.id_edit)
        
        # 공정명
        self.name_edit = QLineEdit()
        layout.addRow("공정명:", self.name_edit)
        
        # 순서
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 999)
        layout.addRow("기본순서:", self.order_spin)
        
        # 기본 소요시간
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.5, 24.0)
        self.duration_spin.setSingleStep(0.5)
        self.duration_spin.setValue(4.0)
        self.duration_spin.setSuffix(" 시간")
        layout.addRow("기본 소요시간:", self.duration_spin)
        
        # 글꼴 색상 설정
        color_layout = QHBoxLayout()
        self.font_color = '#000000'  # 기본 검정색
        
        self.color_label = QLabel("글꼴 색상:")
        color_layout.addWidget(self.color_label)
        
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(w(50), h(25))
        self.color_btn.setStyleSheet(f"background-color: {self.font_color};")
        self.color_btn.clicked.connect(self.select_font_color)
        color_layout.addWidget(self.color_btn)
        
        self.color_preview = QLabel("미리보기")
        self.color_preview.setStyleSheet(f"color: {self.font_color}; font-weight: bold;")
        color_layout.addWidget(self.color_preview)
        
        color_layout.addStretch()
        layout.addRow("글꼴 색상:", color_layout)
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)
    
    def select_font_color(self):
        """글꼴 색상 선택"""
        current_color = QColor(self.font_color)
        color = QColorDialog.getColor(current_color, self, "글꼴 색상 선택")
        
        if color.isValid():
            self.font_color = color.name()
            # 버튼 색상 업데이트
            self.color_btn.setStyleSheet(f"background-color: {self.font_color};")
            # 미리보기 텍스트 색상 업데이트
            self.color_preview.setStyleSheet(f"color: {self.font_color}; font-weight: bold;")
    
    def load_data(self, process):
        """공정 데이터 로드"""
        self.id_edit.setText(process['id'])
        self.name_edit.setText(process['name'])
        self.order_spin.setValue(process['order'])
        
        # 기본 소요시간 로드
        if 'default_duration_hours' in process:
            self.duration_spin.setValue(process['default_duration_hours'])
        
        # 글꼴 색상 로드
        if 'font_color' in process:
            self.font_color = process['font_color']
            self.color_btn.setStyleSheet(f"background-color: {self.font_color};")
            self.color_preview.setStyleSheet(f"color: {self.font_color}; font-weight: bold;")
    
    def get_data(self):
        """입력 데이터 반환"""
        return {
            'process_id': self.id_edit.text(),
            'name': self.name_edit.text(),
            'order': self.order_spin.value(),
            'default_duration_hours': self.duration_spin.value(),
            'font_color': self.font_color
        }


class EquipmentDialog(QDialog):
    """장비 추가/수정 다이얼로그"""
    
    def __init__(self, master_data: MasterDataManager, equipment=None, parent=None):
        super().__init__(parent)
        self.master_data = master_data
        self.equipment = equipment
        self.init_ui()
        
        if equipment:
            self.load_data(equipment)
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("장비 추가" if not self.equipment else "장비 수정")
        self.setModal(True)
        self.setMinimumWidth(w(400))
        
        layout = QFormLayout()
        
        # 장비 ID
        self.id_edit = QLineEdit()
        if self.equipment:
            self.id_edit.setEnabled(False)
        layout.addRow("장비 ID:", self.id_edit)
        
        # 장비명
        self.name_edit = QLineEdit()
        layout.addRow("장비명:", self.name_edit)
        
        # 공정
        self.process_combo = QComboBox()
        processes = sorted(self.master_data.processes.values(), key=lambda x: x['order'])
        for process in processes:
            self.process_combo.addItem(f"{process['name']} ({process['id']})", process['id'])
        layout.addRow("공정:", self.process_combo)
        
        # 가능 제품 및 색상 설정
        product_group = QGroupBox("생산 가능 제품 및 색상")
        product_layout = QVBoxLayout()
        self.product_widgets = {}
        
        for prod_id, prod in self.master_data.products.items():
            product_widget = QWidget()
            h_layout = QHBoxLayout(product_widget)
            h_layout.setContentsMargins(0, 0, 0, 0)
            
            # 체크박스
            check = QCheckBox(f"{prod['name']} ({prod_id})")
            h_layout.addWidget(check)
            
            # 색상 버튼
            color_btn = QPushButton("색상")
            color_btn.setFixedWidth(50)
            color_btn.clicked.connect(lambda checked, p_id=prod_id: self.select_color(p_id))
            h_layout.addWidget(color_btn)
            
            h_layout.addStretch()
            
            self.product_widgets[prod_id] = {
                'check': check,
                'color_btn': color_btn,
                'color': '#3498db'  # 기본 색상
            }
            
            product_layout.addWidget(product_widget)
        
        product_group.setLayout(product_layout)
        layout.addRow(product_group)
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)
    
    def select_color(self, product_id):
        """제품 색상 선택"""
        if product_id in self.product_widgets:
            current_color = QColor(self.product_widgets[product_id]['color'])
            color = QColorDialog.getColor(current_color, self, "제품 색상 선택")
            
            if color.isValid():
                self.product_widgets[product_id]['color'] = color.name()
                # 버튼 색상 업데이트
                self.product_widgets[product_id]['color_btn'].setStyleSheet(
                    f"background-color: {color.name()};"
                )
    
    def load_data(self, equipment):
        """장비 데이터 로드"""
        self.id_edit.setText(equipment['id'])
        self.name_edit.setText(equipment['name'])
        
        # 공정 선택
        index = self.process_combo.findData(equipment['process_id'])
        if index >= 0:
            self.process_combo.setCurrentIndex(index)
        
        # 가능 제품 선택 및 색상
        for prod_id in equipment['available_products']:
            if prod_id in self.product_widgets:
                self.product_widgets[prod_id]['check'].setChecked(True)
        
        # 제품별 색상 로드
        if 'product_colors' in equipment:
            for prod_id, color in equipment['product_colors'].items():
                if prod_id in self.product_widgets:
                    self.product_widgets[prod_id]['color'] = color
                    self.product_widgets[prod_id]['color_btn'].setStyleSheet(
                        f"background-color: {color};"
                    )
    
    def get_data(self):
        """입력 데이터 반환"""
        available_products = []
        product_colors = {}
        
        for prod_id, widgets in self.product_widgets.items():
            if widgets['check'].isChecked():
                available_products.append(prod_id)
                product_colors[prod_id] = widgets['color']
        
        return {
            'equipment_id': self.id_edit.text(),
            'name': self.name_edit.text(),
            'process_id': self.process_combo.currentData(),
            'available_products': available_products,
            'product_colors': product_colors
        }


class OperatorDialog(QDialog):
    """작업자 설정 다이얼로그"""
    
    def __init__(self, master_data: MasterDataManager, operator=None, parent=None):
        super().__init__(parent)
        self.master_data = master_data
        self.operator = operator
        self.init_ui()
        
        if operator:
            self.load_data(operator)
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("작업자 설정")
        self.setModal(True)
        
        layout = QFormLayout()
        
        # 공정
        self.process_combo = QComboBox()
        processes = sorted(self.master_data.processes.values(), key=lambda x: x['order'])
        for process in processes:
            self.process_combo.addItem(f"{process['name']} ({process['id']})", process['id'])
        layout.addRow("공정:", self.process_combo)
        
        # 날짜
        from PyQt5.QtWidgets import QDateEdit
        from PyQt5.QtCore import QDate
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addRow("날짜:", self.date_edit)
        
        # 작업자 수
        self.worker_spin = QSpinBox()
        self.worker_spin.setRange(2, 100)
        self.worker_spin.setSingleStep(2)  # 2인씩 증가
        self.worker_spin.setValue(2)
        layout.addRow("작업자 수:", self.worker_spin)
        
        # 2인 1조 정보 표시
        self.team_label = QLabel("1조 (2인 1조)")
        layout.addRow("조 수:", self.team_label)
        
        # 공정 소요시간 표시
        self.duration_label = QLabel("4.0 시간")
        layout.addRow("공정 소요시간:", self.duration_label)
        
        # 총 용량 (자동 계산)
        self.capacity_label = QLabel("2.0")
        layout.addRow("총 용량(블록수):", self.capacity_label)
        
        # 시그널 연결
        self.worker_spin.valueChanged.connect(self.update_capacity)
        self.process_combo.currentIndexChanged.connect(self.update_process_info)
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)
        
        # 초기 용량 계산
        self.update_process_info()
    
    def update_capacity(self):
        """총 용량 업데이트"""
        teams = self.worker_spin.value() // 2
        self.team_label.setText(f"{teams}조 (2인 1조)")
        
        # 현재 선택된 공정의 소요시간 가져오기
        process_id = self.process_combo.currentData()
        if process_id:
            process = self.master_data.processes.get(process_id, {})
            duration = process.get('default_duration_hours', 8.0)
            capacity = teams * (8.0 / duration)
            self.capacity_label.setText(f"{capacity:.1f}")
    
    def update_process_info(self):
        """공정 정보 업데이트"""
        process_id = self.process_combo.currentData()
        if process_id:
            process = self.master_data.processes.get(process_id, {})
            duration = process.get('default_duration_hours', 8.0)
            self.duration_label.setText(f"{duration} 시간")
            self.update_capacity()
    
    def load_data(self, operator):
        """작업자 데이터 로드"""
        # 구현 생략
        pass
    
    def get_data(self):
        """입력 데이터 반환"""
        return {
            'process_id': self.process_combo.currentData(),
            'date': self.date_edit.date().toString('yyyy-MM-dd'),
            'worker_count': self.worker_spin.value()
        }