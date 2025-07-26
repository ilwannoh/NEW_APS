from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy

"""시각화 캔버스"""


class MplCanvas(FigureCanvas):
    def __init__(self, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

        # 크기 정책 설정
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 레이아웃 자동 조정
        self.fig.tight_layout(pad=2.0)  # 패딩 추가

        # 최소 크기 설정하여 차트가 잘리지 않도록
        self.setMinimumSize(500, 400)