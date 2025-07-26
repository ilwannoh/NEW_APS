# 버튼 스타일
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager

button_font = font_manager.get_just_font("SamsungOne-700").family()
normal_font = font_manager.get_just_font("SamsungOne-700").family()

PRIMARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: #1428A0; 
    color: white; 
    border: none;
    border-radius: 5px;
    font-family: {button_font};
    font-size: {f(16)}px;
}}
QPushButton:hover {{
    background-color: #0069d9;
}}
QPushButton:pressed {{
    background-color: #0062cc;
}}
"""

SECONDARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: #ACACAC;
    color: white;
    border-radius: 5px;
    font-family: {button_font};
    font-size: {f(16)}px;
}}
QPushButton:hover {{
    background-color: #C0C0C0;
}}
QPushButton:pressed {{
    background-color: #848282;
}}
"""

ACTIVE_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: #1428A0; 
        color: white; 
        font-weight: bold; 
        padding: 8px 8px; 
        border-radius: 4px;
        font-family: {normal_font};
        font-size: {f(14)}px;
    }}
    QPushButton:disabled {{
        background-color: #1428A0; 
        color: white; 
        font-weight: bold; 
        padding: 8px 8px; 
        border-radius: 4px;
        font-family: {normal_font};
        font-size: {f(14)}px;
    }}
"""

INACTIVE_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: #8E9CC9; 
        color: white; 
        font-weight: bold; 
        padding: 8px 8px; 
        border-radius: 4px;
        font-family: {normal_font};
        font-size: {f(14)}px;
    }}
    QPushButton:disabled {{
        background-color: #8E9CC9; 
        color: white; 
        font-weight: bold; 
        padding: 8px 8px; 
        border-radius: 4px;
        font-family: {normal_font};
        font-size: {f(14)}px;
    }}
    QPushButton:hover {{
        background-color: #1428A0;
    }}
"""

# 캘린더 헤더의 요일 레이블 스타일
WEEKDAY_HEADER_STYLE = """
background-color: #f0f0f0;
color: black;
font-weight: bold;
padding: 10px;
font-size: 14px;
"""

# 구분선 스타일
SEPARATOR_STYLE = """
background-color: #ffffff;
border: none;
"""

# 라인 이름 레이블 스타일
LINE_LABEL_STYLE = """
background-color: #1428A0;
color: white;
font-weight: bold;
padding: 8px;
font-size: 13px;
"""

# Day/Night 레이블 스타일
DAY_LABEL_STYLE = """
font-size: 13px;
background-color: #f8f8f8;
font-weight: bold;
padding: 6px;
"""

NIGHT_LABEL_STYLE = """
font-size: 13px;
background-color: #f0f0f0;
font-weight: bold;
padding: 6px;
"""

# 상세정보 스타일
DETAIL_DIALOG_STYLE = """
QDialog {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
}
"""

DETAIL_LABEL_TRANSPARENT = """
QLabel {
    background-color: transparent;
}
"""

DETAIL_FRAME_TRANSPARENT = """
QFrame {
    background-color: transparent;
}
"""

# 필드 이름 레이블 스타일
DETAIL_FIELD_NAME_STYLE = """
QLabel.field-name {
    background-color: transparent;
    font-weight: bold;
    color: #555;
}
"""

# 필드 값 레이블 스타일
DETAIL_FIELD_VALUE_STYLE = """
QLabel.field-value {
    background-color: transparent;
    color: #333;
}
"""

# 상세정보 버튼 스타일
DETAIL_BUTTON_STYLE = """
QPushButton {
    padding: 6px 12px;
    background-color: #1428A0;
    color: white;
}
QPushButton:hover {
    background-color: #004C99;
}
QPushButton:pressed {
    background-color: #003366;
}
"""