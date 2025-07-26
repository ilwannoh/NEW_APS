"""
애플리케이션 전역 스타일시트
POSS-dev 프로젝트에서 가져와 수정
"""

class AppStyle:
    """애플리케이션 스타일 정의"""
    
    # 메인 컬러 팔레트
    PRIMARY_COLOR = "#1428A0"  # Samsung Blue
    PRIMARY_HOVER = "#0F1F7E"
    SECONDARY_COLOR = "#2ecc71"
    ERROR_COLOR = "#e74c3c"
    WARNING_COLOR = "#f39c12"
    SUCCESS_COLOR = "#27ae60"
    INFO_COLOR = "#3498db"
    
    # 배경색
    BG_COLOR = "#F5F5F5"
    WIDGET_BG = "#FFFFFF"
    
    # 텍스트 색상
    TEXT_PRIMARY = "#333333"
    TEXT_SECONDARY = "#666666"
    TEXT_DISABLED = "#999999"
    
    # 보더 색상
    BORDER_COLOR = "#e9ecef"
    BORDER_HOVER = "#ced4da"
    
    # 메시지박스 스타일
    MESSAGE_BOX_QSS = f"""
        QMessageBox, QDialog {{
            background-color: {WIDGET_BG};
            border: none;
        }}
        QMessageBox QFrame {{
            background-color: {WIDGET_BG};
            border: none;
        }}
        QMessageBox QWidget {{
            background-color: {WIDGET_BG};
            border: none;
        }}
        QMessageBox QLabel, QDialog QLabel {{
            background-color: {WIDGET_BG};
            color: {TEXT_PRIMARY};
            padding: 4px 30px 4px 8px;
            font-size: 12px;
        }}
        QMessageBox QScrollArea, QMessageBox QScrollArea QWidget {{
            background-color: {WIDGET_BG};
            border: none;
        }}
        QMessageBox QPushButton, QDialog QPushButton {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        }}
        QMessageBox QPushButton:hover, QDialog QPushButton:hover {{
            background-color: {PRIMARY_HOVER};
        }}
    """
    
    # 메인 윈도우 스타일
    MAIN_WINDOW_QSS = f"""
        QMainWindow {{
            background-color: {BG_COLOR};
        }}
        
        QWidget {{
            font-family: "맑은 고딕", "Malgun Gothic", sans-serif;
            font-size: 12px;
            color: {TEXT_PRIMARY};
        }}
        
        /* 탭 위젯 스타일 */
        QTabWidget::pane {{
            background-color: {WIDGET_BG};
            border: none;
            border-top: 1px solid {BORDER_COLOR};
            border-radius: 0px;
        }}
        
        QTabBar {{
            background-color: #f8f9fa;
            border: none;
            border-radius: 0px;
        }}
        
        QTabBar::tab {{
            background: transparent;
            color: {TEXT_SECONDARY};
            padding: 8px 12px;
            font-size: 13px;
            font-weight: 600;
            border-bottom: 3px solid transparent;
            margin-right: 0px;
            min-width: 10px;
        }}
        
        QTabBar::tab:hover {{
            color: {PRIMARY_COLOR};
            background: rgba(20, 40, 160, 0.05);
        }}
        
        QTabBar::tab:selected {{
            color: {PRIMARY_COLOR};
            font-weight: 700;
            border-bottom: 3px solid {PRIMARY_COLOR};
            background: rgba(20, 40, 160, 0.05);
        }}
        
        /* 버튼 스타일 */
        QPushButton {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        }}
        
        QPushButton:hover {{
            background-color: {PRIMARY_HOVER};
        }}
        
        QPushButton:pressed {{
            background-color: #0A1460;
        }}
        
        QPushButton:disabled {{
            background-color: #cccccc;
            color: #666666;
        }}
        
        /* 보조 버튼 */
        QPushButton[class="secondary"] {{
            background-color: {WIDGET_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_COLOR};
        }}
        
        QPushButton[class="secondary"]:hover {{
            background-color: #f8f9fa;
            border-color: {BORDER_HOVER};
        }}
        
        /* 입력 필드 */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {WIDGET_BG};
            border: 1px solid {BORDER_COLOR};
            padding: 6px;
            border-radius: 4px;
            font-size: 12px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, 
        QDoubleSpinBox:focus, QComboBox:focus {{
            border-color: {PRIMARY_COLOR};
            outline: none;
        }}
        
        /* 테이블 스타일 */
        QTableWidget {{
            background-color: {WIDGET_BG};
            border: 1px solid {BORDER_COLOR};
            gridline-color: {BORDER_COLOR};
        }}
        
        QTableWidget::item {{
            padding: 4px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: rgba(20, 40, 160, 0.1);
            color: {TEXT_PRIMARY};
        }}
        
        QHeaderView::section {{
            background-color: #f8f9fa;
            padding: 6px;
            border: none;
            border-bottom: 2px solid {BORDER_COLOR};
            font-weight: bold;
        }}
        
        /* 스크롤바 */
        QScrollBar:vertical {{
            background: #f0f0f0;
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: #c0c0c0;
            min-height: 20px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: #a0a0a0;
        }}
        
        /* 툴팁 */
        QToolTip {{
            background-color: {TEXT_PRIMARY};
            color: white;
            border: none;
            padding: 4px 8px;
            font-size: 11px;
            border-radius: 4px;
        }}
        
        /* 라벨 */
        QLabel {{
            background-color: transparent;
        }}
        
        QLabel[class="heading"] {{
            font-size: 16px;
            font-weight: bold;
            color: {TEXT_PRIMARY};
            padding: 8px 0;
        }}
        
        QLabel[class="subheading"] {{
            font-size: 14px;
            font-weight: 600;
            color: {TEXT_SECONDARY};
            padding: 4px 0;
        }}
    """
    
    @classmethod
    def get_stylesheet(cls) -> str:
        """전체 스타일시트 반환"""
        return cls.MESSAGE_BOX_QSS + cls.MAIN_WINDOW_QSS
    
    @classmethod
    def get_color(cls, color_name: str) -> str:
        """색상 이름으로 색상 코드 반환"""
        colors = {
            'primary': cls.PRIMARY_COLOR,
            'primary_hover': cls.PRIMARY_HOVER,
            'secondary': cls.SECONDARY_COLOR,
            'error': cls.ERROR_COLOR,
            'warning': cls.WARNING_COLOR,
            'success': cls.SUCCESS_COLOR,
            'info': cls.INFO_COLOR,
            'bg': cls.BG_COLOR,
            'widget_bg': cls.WIDGET_BG,
            'text': cls.TEXT_PRIMARY,
            'text_secondary': cls.TEXT_SECONDARY,
            'border': cls.BORDER_COLOR
        }
        return colors.get(color_name, '#000000')