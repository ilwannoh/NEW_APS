import hashlib
import colorsys
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager

bold_font   = font_manager.get_just_font("SamsungSharSans-Bold").family()
normal_font = font_manager.get_just_font("SamsungOne-700").family()

"""
pre-assigned에 캘린더처럼 표시되는 카드 UI 컴포넌트
"""
class CalendarCard(QFrame):
    clicked = pyqtSignal(object, dict)

    def __init__(self, row_data: dict, is_day: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._row = row_data

        proj = self._row.get('project', '')
        # 프로젝트명을 MD5 해시 → 앞 두 글자로 hue 결정
        digest = hashlib.md5(proj.encode('utf-8')).hexdigest()
        hue = (int(digest[:2], 16) / 255) * 360

        """
        선택 시 조금 어둡게
        """
        def hsl_to_hex(h, l, s):
            r, g, b = colorsys.hls_to_rgb(h/360, l, s)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

        base_color = hsl_to_hex(hue, 0.8, 0.6)
        sel_color  = hsl_to_hex(hue, 0.6, 0.6)

        self.base_style = f"""
            QFrame {{
                background-color: {base_color};
                border: 1px solid {base_color};
            }}
        """
        self.selected_style = f"""
            QFrame {{
                background-color: {sel_color};
                border: 1px solid {sel_color};
            }}
        """

        self.setStyleSheet(self.base_style)
        self._is_selected = False

        self.setObjectName("cardFrameDay" if is_day else "cardFrameNight")
        self.setFrameShape(QFrame.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.setMouseTracking(True)

        # 내부 레이아웃
        hl = QHBoxLayout(self)
        hl.setContentsMargins(8, 8, 8, 8)
        hl.setSpacing(4)

        lbl_item = QLabel(self._row.get('project', ''), self)
        lbl_item.setStyleSheet(f"font-family:{bold_font}; font-size:{f(14)}px; font-weight:900;")

        lbl_item.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl_item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        lbl_qty = QLabel(str(self._row.get('qty', '')), self)
        lbl_qty.setStyleSheet(f"font-family:{normal_font}; font-size:{f(14)}px;")
        lbl_qty.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        hl.addWidget(lbl_item)
        hl.addWidget(lbl_qty)

    """
    마우스 클릭 시 호출
    """
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._is_selected = not self._is_selected
            self.setStyleSheet(self.selected_style if self._is_selected else self.base_style)
            self.clicked.emit(self, self._row)
        super().mousePressEvent(e)