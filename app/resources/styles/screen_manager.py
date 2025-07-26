"""
화면 해상도 관리 유틸리티
POSS-dev 프로젝트에서 가져와 수정
다양한 해상도에서 일관된 UI 표시를 위한 비율 계산 기능 제공
"""

from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget
from PyQt5.QtGui import QScreen, QGuiApplication
import math


class ScreenManager:
    """화면 해상도 관리 클래스"""
    
    # 기준 해상도 (FHD)
    BASE_WIDTH = 1920
    BASE_HEIGHT = 1080
    BASE_DPI = 96
    
    # 기준 폰트 크기
    BASE_FONT_SIZE = 12
    
    @staticmethod
    def get_current_screen(widget: QWidget = None) -> QScreen:
        """현재 스크린 객체 반환"""
        app = QApplication.instance() or QGuiApplication.instance()
        if not app:
            return None
        
        # 위젯의 중심점으로 스크린 찾기
        if widget:
            center = widget.geometry().center()
            global_center = widget.mapToGlobal(center) if hasattr(widget, 'mapToGlobal') else center
            screen = app.screenAt(global_center)
            if screen:
                return screen
        
        # 마우스 커서 위치로 스크린 찾기
        desktop = QDesktopWidget()
        cursor_pos = desktop.cursor().pos()
        return app.screenAt(cursor_pos)
    
    @staticmethod
    def get_screen_info(screen: QScreen = None) -> dict:
        """스크린 정보 딕셔너리 반환"""
        if not screen:
            screen = ScreenManager.get_current_screen()
        
        if not screen:
            return {
                'width': ScreenManager.BASE_WIDTH,
                'height': ScreenManager.BASE_HEIGHT,
                'dpi': ScreenManager.BASE_DPI,
                'scale': 1.0
            }
        
        geometry = screen.geometry()
        available = screen.availableGeometry()
        
        return {
            'name': screen.name(),
            'width': geometry.width(),
            'height': geometry.height(),
            'available_width': available.width(),
            'available_height': available.height(),
            'physical_dpi': screen.physicalDotsPerInch(),
            'logical_dpi': screen.logicalDotsPerInch(),
            'device_pixel_ratio': screen.devicePixelRatio(),
            'orientation': screen.orientation(),
            'is_primary': screen == QGuiApplication.primaryScreen()
        }
    
    @staticmethod
    def ratio_width(pixel_value: int, widget: QWidget = None) -> int:
        """
        너비 픽셀값을 현재 해상도에 맞게 변환
        예: w(100) => FHD에서는 100px, QHD에서는 133px
        """
        screen = ScreenManager.get_current_screen(widget)
        if not screen:
            return pixel_value
        
        ratio = pixel_value / ScreenManager.BASE_WIDTH
        screen_width = screen.availableGeometry().width()
        return round(screen_width * ratio)
    
    @staticmethod
    def ratio_height(pixel_value: int, widget: QWidget = None) -> int:
        """
        높이 픽셀값을 현재 해상도에 맞게 변환
        예: h(100) => FHD에서는 100px, QHD에서는 133px
        """
        screen = ScreenManager.get_current_screen(widget)
        if not screen:
            return pixel_value
        
        ratio = pixel_value / ScreenManager.BASE_HEIGHT
        screen_height = screen.availableGeometry().height()
        return round(screen_height * ratio)
    
    @staticmethod
    def ratio_font(font_size: int, widget: QWidget = None) -> int:
        """
        폰트 크기를 현재 해상도에 맞게 변환
        대각선 비율을 사용하여 더 일관된 크기 유지
        """
        screen = ScreenManager.get_current_screen(widget)
        if not screen:
            return font_size
        
        # 기준 해상도의 대각선 길이
        base_diagonal = math.sqrt(ScreenManager.BASE_WIDTH ** 2 + ScreenManager.BASE_HEIGHT ** 2)
        
        # 현재 화면의 대각선 길이
        geometry = screen.availableGeometry()
        screen_diagonal = math.sqrt(geometry.width() ** 2 + geometry.height() ** 2)
        
        # 대각선 비율에 따라 폰트 크기 조정
        return round(font_size * (screen_diagonal / base_diagonal))
    
    @staticmethod
    def ratio_font_min(font_size: int, min_value: int, widget: QWidget = None) -> int:
        """최소값을 보장하는 폰트 크기 변환"""
        value = ScreenManager.ratio_font(font_size, widget)
        return max(value, min_value)
    
    @staticmethod
    def get_size_tuple(width: int, height: int, widget: QWidget = None) -> tuple:
        """너비와 높이를 튜플로 반환"""
        return (
            ScreenManager.ratio_width(width, widget),
            ScreenManager.ratio_height(height, widget)
        )
    
    @staticmethod
    def get_margins(top: int, right: int, bottom: int, left: int, widget: QWidget = None) -> tuple:
        """여백을 튜플로 반환"""
        return (
            ScreenManager.ratio_height(top, widget),
            ScreenManager.ratio_width(right, widget),
            ScreenManager.ratio_height(bottom, widget),
            ScreenManager.ratio_width(left, widget)
        )


# 전역 인스턴스 생성
screen_mgr = ScreenManager()

# 편의를 위한 짧은 별칭
w = screen_mgr.ratio_width       # 너비 비율 변환
h = screen_mgr.ratio_height      # 높이 비율 변환
f = screen_mgr.ratio_font        # 폰트 크기 변환
fm = screen_mgr.ratio_font_min   # 최소값 보장 폰트
t = screen_mgr.get_size_tuple    # 크기 튜플
m = screen_mgr.get_margins       # 여백 튜플