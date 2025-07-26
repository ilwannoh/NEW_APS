from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget
from PyQt5.QtGui import QScreen, QGuiApplication

"""
해상도를 설정하는 클래스
픽셀 값을 입력하면 현재 화면에 맞는 비율로 변환하여 적용
"""


class ScreenManager:
    # 기준 해상도
    BASE_WIDTH = 1920
    BASE_HEIGHT = 1080
    BASE_DPI = 96

    # 기준 폰트 크기 (FHD 기준)
    BASE_FONT_SIZE = 16  # 기본 폰트 사이즈

    def __init__(self):
        pass

    """
    현재 위젯이 있는 스크린 또는 마우스 커서가 있는 스크린 반환
    """

    @staticmethod
    def get_current_screen(widget: QWidget = None) -> QScreen:
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

    """
    스크린의 상세 정보 반환
    """

    @staticmethod
    def get_screen_info(screen: QScreen = None) -> dict:
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

    """
    픽셀 값을 입력받아 화면 너비에 대한 비율로 변환하여 픽셀 값 반환
    기준 해상도(FHD)에서 입력한 픽셀 값이 다른 해상도에서도 동일한 비율로 표시됨

    예: rw(194) => FHD에서는 194px, QHD에서는 (194/1920*2560) = 259px
    """

    @staticmethod
    def ratio_width(pixel_value: int, widget: QWidget = None) -> int:
        screen = ScreenManager.get_current_screen(widget)
        if not screen:
            return pixel_value

        # 픽셀 값을 기준 해상도(1920x1080)에 대한 비율로 변환
        ratio = pixel_value / ScreenManager.BASE_WIDTH

        # 현재 화면 너비에 비율 적용
        screen_width = screen.availableGeometry().width()
        return round(screen_width * ratio)

    """
    픽셀 값을 입력받아 화면 높이에 대한 비율로 변환하여 픽셀 값 반환
    기준 해상도(FHD)에서 입력한 픽셀 값이 다른 해상도에서도 동일한 비율로 표시됨

    예: rh(194) => FHD에서는 194px, QHD에서는 (194/1080*1440) = 259px
    """

    @staticmethod
    def ratio_height(pixel_value: int, widget: QWidget = None) -> int:
        screen = ScreenManager.get_current_screen(widget)
        if not screen:
            return pixel_value

        # 픽셀 값을 기준 해상도(1920x1080)에 대한 비율로 변환
        ratio = pixel_value / ScreenManager.BASE_HEIGHT

        # 현재 화면 높이에 비율 적용
        screen_height = screen.availableGeometry().height()
        return round(screen_height * ratio)

    """
    폰트 크기를 입력받아 화면 크기에 맞게 조정
    기준 해상도(FHD)에서 입력한 폰트 크기가 다른 해상도에서도 비율적으로 일관되게 표시됨

    예: rf(14) => FHD에서는 14pt, QHD에서는 약 18.6pt

    화면 대각선 비율을 기준으로 계산하여 더 일관된 폰트 크기 유지
    """

    @staticmethod
    def ratio_font(font_size: int, widget: QWidget = None) -> int:
        screen = ScreenManager.get_current_screen(widget)
        if not screen:
            return font_size

        # 기준 해상도의 대각선 길이 계산
        import math
        base_diagonal = math.sqrt(ScreenManager.BASE_WIDTH ** 2 + ScreenManager.BASE_HEIGHT ** 2)

        # 현재 화면의 대각선 길이 계산
        geometry = screen.availableGeometry()
        screen_diagonal = math.sqrt(geometry.width() ** 2 + geometry.height() ** 2)

        # 대각선 비율에 따라 폰트 크기 조정
        # 이 방식은 화면 크기 변화에 따라 폰트 크기가 일관되게 조정됨
        return round(font_size * (screen_diagonal / base_diagonal))

    """
    최소값을 보장하는 폰트 크기 변환
    """

    @staticmethod
    def ratio_font_min(font_size: int, min_value: int, widget: QWidget = None) -> int:
        value = ScreenManager.ratio_font(font_size, widget)
        return max(value, min_value)

    """
    너비와 높이를 튜플로 반환 (비율 기반)
    """

    @staticmethod
    def get_size_tuple(width: int, height: int, widget: QWidget = None) -> tuple:
        return (
            ScreenManager.ratio_width(width, widget),
            ScreenManager.ratio_height(height, widget)
        )

    """
    여백을 튜플로 반환 (비율 기반)
    """

    @staticmethod
    def get_margins(top: int, right: int, bottom: int, left: int, widget: QWidget = None) -> tuple:
        return (
            ScreenManager.ratio_height(top, widget),
            ScreenManager.ratio_width(right, widget),
            ScreenManager.ratio_height(bottom, widget),
            ScreenManager.ratio_width(left, widget)
        )

    """
    직접 비율 값으로 너비 계산 (고급 사용자용)
    """

    @staticmethod
    def raw_ratio_width(ratio: float, widget: QWidget = None) -> int:
        screen = ScreenManager.get_current_screen(widget)
        if not screen:
            return round(ScreenManager.BASE_WIDTH * ratio)

        screen_width = screen.availableGeometry().width()
        return round(screen_width * ratio)

    """
    직접 비율 값으로 높이 계산 (고급 사용자용)
    """

    @staticmethod
    def raw_ratio_height(ratio: float, widget: QWidget = None) -> int:
        screen = ScreenManager.get_current_screen(widget)
        if not screen:
            return round(ScreenManager.BASE_HEIGHT * ratio)

        screen_height = screen.availableGeometry().height()
        return round(screen_height * ratio)


screen_mgr = ScreenManager()

# 편의를 위한 짧은 별칭
w = screen_mgr.ratio_width  # 픽셀 값 기반 너비 비율 변환
h = screen_mgr.ratio_height  # 픽셀 값 기반 높이 비율 변환
f = screen_mgr.ratio_font  # 폰트 크기 비율 변환
fm = screen_mgr.ratio_font_min  # 최소값 보장 폰트 크기
t = screen_mgr.get_size_tuple  # 크기 튜플 반환
m = screen_mgr.get_margins  # 여백 튜플 반환
rw = screen_mgr.raw_ratio_width  # 직접 비율 지정 (고급)
rh = screen_mgr.raw_ratio_height  # 직접 비율 지정 (고급)