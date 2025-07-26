import pandas as pd

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QAbstractScrollArea
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager

bold_font   = font_manager.get_just_font("SamsungSharSans-Bold").family()
normal_font = font_manager.get_just_font("SamsungOne-700").family()

"""
데이터를 요약해서 표시하는 테이블 위젯
"""
class SummaryWidget(QWidget):
    def __init__(self, df: pd.DataFrame, line_order: list=None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 데이터 집계
        df_qty = df.groupby('Line', as_index=False)['Qty'].sum()

        if line_order:
            # 카테고리로 만들어서 순서 고정
            cat = pd.Categorical(df_qty['Line'], categories=line_order, ordered=True)
            df_qty['Line'] = cat
            df_qty = df_qty.sort_values('Line').reset_index(drop=True)
        else:
            df_qty = df_qty.sort_values('Qty', ascending=False).reset_index(drop=True)

        grand_total = df_qty['Qty'].sum()

        # 동별 그룹핑
        groups = {}
        for line in df_qty['Line']:
            prefix = line.split('_')[0]
            groups.setdefault(prefix, []).append(line)

        # 그룹별 총합 계산 및 정렬
        group_summaries = []
        for prefix, lines in groups.items():
            group_sum = df_qty[df_qty['Line'].isin(lines)]['Qty'].sum()
            group_summaries.append((prefix, lines, group_sum))
        group_summaries.sort(key=lambda x: x[2], reverse=True)

        if line_order:
            order_map = {}
            for idx, ln in enumerate(line_order):
                b = ln.split('_')[0]
                order_map.setdefault(b, idx)
            group_summaries.sort(key=lambda x: order_map[x[0]])
        else:
            group_summaries.sort(key=lambda x: x[2], reverse=True)

        # 전체 행 개수 계산
        total_rows = 1 + sum(1 + len(lines) for _, lines, _ in group_summaries)
        table = QTableWidget(total_rows, 4, self)
        table.setHorizontalHeaderLabels(["Building", "Line", "Sum", "Portion"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setAlternatingRowColors(False)

        # 헤더 스타일 및 폰트
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: #1428A0;
                color: white;
                border: none;
                font-family: {bold_font};
                font-size: {f(14)}px;
                font-weight: 900;
            }}
        """)
        
        table.verticalHeader().setDefaultSectionSize(35)

        # 스타일 정의
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                gridline-color: #dddddd;
            }}
            QTableView::item {{
                font-family: {normal_font};
                font-size: {f(14)}px;
            }}
            QHeaderView::section {{
                background-color: #1428A0;
                color: white;
                border: none;
                font-family: {bold_font};
                font-size: {f(14)}px;
                font-weight: 900;
            }}
        """)

        # 첫 행: Total
        row = 0
        table.setSpan(row, 0, 1, 2)
        item_tot_label = QTableWidgetItem("Total")
        item_tot_label.setTextAlignment(Qt.AlignCenter)
        item_tot_label.setBackground(QColor('#e8f4fc'))
        table.setItem(row, 0, item_tot_label)

        item_tot_sum = QTableWidgetItem(f"{int(grand_total):,}")
        item_tot_sum.setTextAlignment(Qt.AlignCenter)
        item_tot_sum.setBackground(QColor('#e8f4fc'))
        table.setItem(row, 2, item_tot_sum)

        item_tot_portion = QTableWidgetItem("-")
        item_tot_portion.setTextAlignment(Qt.AlignCenter)

        table.setItem(row, 3, item_tot_portion)
        row += 1

        # 그룹별
        for prefix, lines, group_sum in group_summaries:
            start = row
            span_count = 1 + len(lines)
            group_share = round(group_sum / grand_total * 100, 1)

            # Building
            table.setSpan(start, 0, span_count, 1)
            item_building = QTableWidgetItem(prefix)
            item_building.setTextAlignment(Qt.AlignCenter)
            item_building.setBackground(QColor('#e8f4fc'))
            table.setItem(start, 0, item_building)

            # Group total (1열)
            item_group = QTableWidgetItem(f"{prefix}_Total")
            item_group.setTextAlignment(Qt.AlignCenter)
            item_group.setBackground(QColor('#e8f4fc'))
            table.setItem(start, 1, item_group)

            # Sum (2열)
            item_group_sum = QTableWidgetItem(f"{int(group_sum):,}")
            item_group_sum.setTextAlignment(Qt.AlignCenter)
            item_group_sum.setBackground(QColor('#e8f4fc'))
            table.setItem(start, 2, item_group_sum)

            # Portion (3열)
            table.setSpan(start, 3, span_count, 1)
            item_group_portion = QTableWidgetItem(f"{group_share}%")
            item_group_portion.setTextAlignment(Qt.AlignCenter)
            item_group_portion.setForeground(QColor('#1428A0'))
            table.setItem(start, 3, item_group_portion)
            row += 1

            # 각 라인
            for ln in lines:
                qty_val = int(df_qty[df_qty['Line'] == ln]['Qty'].iloc[0])
                item_line = QTableWidgetItem(ln)
                item_line.setTextAlignment(Qt.AlignCenter)
                item_line.setData(Qt.DisplayRole, f"    {ln}")
                table.setItem(row, 1, item_line)

                item_line_sum = QTableWidgetItem(f"{qty_val:,}")
                item_line_sum.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 2, item_line_sum)

                row += 1

        table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout.addWidget(table)
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())