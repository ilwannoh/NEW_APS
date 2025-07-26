import pandas as pd
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame, QLabel
)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt

from app.models.common.file_store import FilePaths, DataStore
from app.utils.fileHandler import load_file
from app.core.input.maintenance import melt_plan, get_threshold

class DynamicPropertiesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dynamic 속성 설정")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(800, 600)

        path = FilePaths.get("dynamic_excel_file")
        if not path:
            self.reject(); return
        raw = load_file(path)
        df_pre = raw.get('pre_assign', pd.DataFrame())
        if df_pre.empty:
            self.reject(); return

        try:
            melted = melt_plan(df_pre)
        except Exception:
            self.reject(); return
        melted['RMC'] = melted['Item'].str[3:-7]

        stored_items = DataStore.get('maintenance_thresholds_items', {})
        stored_rmcs  = DataStore.get('maintenance_thresholds_rmcs', {})

        rows = []
        group_info = []
        for idx, ((line, shift, rmc), grp) in enumerate(melted.groupby(['Line','Shift','RMC'], sort=False)):
            items = grp['Item'].unique().tolist()
            span = len(items)
            group_info.append((idx * span, span))
            rm_thr = stored_rmcs.get((line, shift, rmc), get_threshold(line, shift, 'rmc'))
            for item in items:
                it_thr = stored_items.get((line, shift, item), get_threshold(line, shift, 'item'))
                rows.append((line, shift, rmc, item, it_thr, rm_thr))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        title_frame = QFrame()
        title_frame.setFixedHeight(50)
        title_frame.setStyleSheet("background-color: #1428A0; border: none;")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(20,0,20,0)
        title_label = QLabel("Dynamic Threshold 설정")
        title_label.setStyleSheet("color: white;")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #F9F9F9; border:none; border-radius:0;")
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20,20,20,20)
        content_layout.setSpacing(15)

        sheet_lbl = QLabel(f"Pre-Assign 시트: pre_assign")
        sheet_lbl.setFont(QFont("Arial", 10))
        content_layout.addWidget(sheet_lbl)

        headers = ["Line","Shift","RMC","Item","ItemThreshold","RMCThreshold"]
        self.table = QTableWidget(len(rows), len(headers), parent=content)
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)

        self.table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { border:1px solid #ccc; }"
        )
        self.table.setStyleSheet(
            "QTableWidget::item { border-left:1px solid #ccc; }"
            "QTableWidget::item:selected { background: palette(highlight); color: palette(highlighted-text); }"
        )

        for r, (line, shift, rmc, item, it_thr, rm_thr) in enumerate(rows):
            for c, value in enumerate([line, shift, rmc, item, f"{it_thr:.2f}", f"{rm_thr:.2f}"]):
                cell = QTableWidgetItem(str(value))
                flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                if c in (4,5):
                    flags |= Qt.ItemIsEditable
                cell.setFlags(flags)
                self.table.setItem(r, c, cell)

        for start, span in group_info:
            if span > 1:
                self.table.setSpan(start, 2, span, 1)
                self.table.setSpan(start, 5, span, 1)
        start_row = 0; span = 1
        prev_pair = (rows[0][0], rows[0][1])
        for r in range(1, len(rows)):
            curr_pair = (rows[r][0], rows[r][1])
            if curr_pair == prev_pair:
                span += 1
            else:
                if span > 1:
                    self.table.setSpan(start_row, 1, span, 1)
                prev_pair = curr_pair
                start_row = r; span = 1
        if span > 1:
            self.table.setSpan(start_row, 1, span, 1)
        start_row = 0; span = 1
        prev_line = rows[0][0]
        for r in range(1, len(rows)):
            if rows[r][0] == prev_line:
                span += 1
            else:
                if span > 1:
                    self.table.setSpan(start_row, 0, span, 1)
                prev_line = rows[r][0]
                start_row = r; span = 1
        if span > 1:
            self.table.setSpan(start_row, 0, span, 1)

        content_layout.addWidget(self.table)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        btn_frame = QFrame()
        btn_frame.setStyleSheet("background-color: #F0F0F0; border:none;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0,10,20,10)
        btn_layout.addStretch(1)
        save_btn = QPushButton("Save")
        save_btn.setFont(QFont("Arial",10,QFont.Bold))
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.setFixedSize(100,40)
        save_btn.setStyleSheet(
            "QPushButton{background-color:#1428A0;color:white;border:none;border-radius:5px;}"
            "QPushButton:hover{background-color:#1e429f;}"
        )
        save_btn.setStyleSheet(save_btn.styleSheet())
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Arial",10,QFont.Bold))
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setFixedSize(100,40)
        cancel_btn.setStyleSheet(
            "QPushButton{background-color:#ccc;color:black;border:none;}"
            "QPushButton:hover{background-color:#bbb;}"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        main_layout.addWidget(btn_frame)

    def getSelections(self):
        items, rmcs = {}, {}
        for row in range(self.table.rowCount()):
            line = self.table.item(row,0).text()
            shift = int(self.table.item(row,1).text())
            item = self.table.item(row,3).text()
            it_thr = float(self.table.item(row,4).text() or get_threshold(line, shift,'item'))
            items[(line,shift,item)] = it_thr
            rmc_text = self.table.item(row,2).text()
            if rmc_text:
                rm_thr = float(self.table.item(row,5).text() or get_threshold(line, shift,'rmc'))
                rmcs[(line,shift,rmc_text)] = rm_thr
        return items, rmcs

    def accept(self):
        items, rmcs = self.getSelections()
        DataStore.set('maintenance_thresholds_items', items)
        DataStore.set('maintenance_thresholds_rmcs', rmcs)
        super().accept()
