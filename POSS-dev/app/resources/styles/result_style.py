from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

class ResultStyles:
    bold_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
    normal_font = font_manager.get_just_font("SamsungOne-700").family()

    RESULT_TABLE_STYLE = f"""
        QTableWidget {{
            border: 1px solid #ffffff;
            gridline-color: #f0f0f0;
            background-color: white;
            border-radius: 0;
            margin-top: 0px;
        }}
    """

    ACTIVE_BUTTON_STYLE = """
        QPushButton {
            background-color: #1428A0; 
            color: white; 
            font-weight: bold; 
            padding: 8px 8px; 
            border-radius: 4px;
        }
    """
    
    INACTIVE_BUTTON_STYLE = """
        QPushButton {
            background-color: #8E9CC9; 
            color: white; 
            font-weight: bold; 
            padding: 8px 8px; 
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1428A0;
        }
    """
    
    EXPORT_BUTTON_STYLE = f"""
        QPushButton {{
                background-color: #1428A0; 
                color: white; 
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-family: {normal_font};
                font-size: {f(16)}px;
            }}
            QPushButton:hover {{
                background-color: #0069d9;
            }}
            QPushButton:pressed {{
                background-color: #0062cc;
            }}
    """
    
    MATERIAL_TABLE_STYLE = """
        QTableWidget {
            border: 1px solid #ffffff;
            gridline-color: #f0f0f0;
            background-color: white;
            border-radius: 0;
            margin-top: 0px;
            outline: none;
        }
        QHeaderView::section {
            background-color: #1428A0;
            color: white;
            padding: 4px;
            font-weight: bold;
            border: 1px solid #1428A0;
            border-radius: 0;
            outline: none;
        }
    """