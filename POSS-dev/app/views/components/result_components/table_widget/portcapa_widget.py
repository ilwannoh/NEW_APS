import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,QSizePolicy,QHeaderView)
from PyQt5.QtGui import QColor, QFont
from app.models.common.file_store import FilePaths, DataStore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager
from app.views.components.common.custom_table import CustomTable

"""출하 capa 분석 위젯"""
class PortCapaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)

        headers = ['Tosite_port','SOP','Port_Capa','Rate(%)']
        self.table = CustomTable(headers=headers)

        # 차트 컨테이너
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_container)

        # 레이아웃 추가
        self.main_layout.addWidget(self.chart_container)
        self.main_layout.addWidget(self.table)

    """
    다른 위젯들과 패턴 통일: run_analysis 메서드 추가
    """
    def run_analysis(self, df):
        """
        결과 데이터로 PortCapa 분석 실행
        기존 render_table() 로직을 그대로 사용
        """
        print(f"PortCapaWidget: run_analysis 시작 - 데이터 행 수: {len(df) if df is not None else 0}")
        
        # 기존 render_table() 메서드 호출
        self.render_table()

    """port capa 테이블 그리는 함수"""
    def render_table(self):
        self.organized_dataframes = DataStore.get("organized_dataframes",{})
        if not self.organized_dataframes:
            self.table.set_message("No data available")
            return 
        
        self.df_demand = self.organized_dataframes['demand'].get('demand',pd.DataFrame())
        if self.df_demand.empty:
            self.table.set_message("No demand data available")
            return 
        
        self.df_capa_outgoing = self.organized_dataframes['master'].get('capa_outgoing',pd.DataFrame())
        if self.df_capa_outgoing.empty:
            self.table.set_message("No capacity data available")
            return
        
        # 화면에 그릴 테이블의 데이터프레임 만들기 
        self.df_demand = self.df_demand.drop(columns='Item').groupby('To_Site').sum()
        df_portcapa = self.df_capa_outgoing.drop_duplicates(subset='Tosite_port').reset_index(drop=True)
        df_portcapa['Port Capa'] = df_portcapa.iloc[:, 2:9].sum(axis=1)
        df_portcapa = pd.merge(df_portcapa,self.df_demand,on="To_Site",how='left').fillna(0)
        df_portcapa['Rate(%)'] = df_portcapa['SOP']/df_portcapa['Port Capa'] * 100
        df_portcapa['Rate(%)'] = (df_portcapa['Rate(%)']).round(2)
        df_portcapa = df_portcapa[['Tosite_port','SOP','Port Capa','Rate(%)']].sort_values(by='SOP',ascending=False)

        self.table.setRowCount(len(df_portcapa))
        self.table.setColumnCount(len(df_portcapa.columns))
        for i in range(len(df_portcapa)):
            for j in range(len(df_portcapa.columns)):
                self.table.setItem(i, j, QTableWidgetItem(str(df_portcapa.iat[i, j])))
        
        # 이전 차트 삭제
        for i in reversed(range(self.chart_layout.count())):
            widget = self.chart_layout.itemAt(i).widget()
            if widget: widget.deleteLater()

        # 새 차트 추가
        self.chart_container.setFixedHeight(250)
        self.chart_layout.addWidget(PortCapaChartWidget(df_portcapa))

class PortCapaChartWidget(QWidget):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        layout.addWidget(self.canvas)
        self.plot()

    def plot(self):
        ax = self.canvas.figure.add_subplot(111)
        ax.clear()
        labels = self.df['Tosite_port']
        x = range(len(labels))
        width = 0.35

        # 막대 그래프
        ax.bar([i - width/2 for i in x], self.df['SOP'], width=width, label='SOP', color='#4c72b0')
        ax.bar([i + width/2 for i in x], self.df['Port Capa'], width=width, label='Port Capa', color='#dd8452')

        # 스타일 정리
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_title("Port Capa", fontsize=14)
        ax.legend() # 범례 
        ax.yaxis.grid(True, linestyle='--', color='gray', alpha=0.7)
        
        # 불필요한 테두리 및 축 제거
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # 글자 짤리지 않게 상하 여백 추가 
        self.canvas.figure.subplots_adjust(bottom=0.2,top=0.8)

        self.canvas.draw()