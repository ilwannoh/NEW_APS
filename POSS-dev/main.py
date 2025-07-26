import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox, QStyleFactory
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from app.resources.styles.app_style import AppStyle
from splash_start import SplashStart


def exception_hook(exctype, value, traceback_obj):
    """글로벌 예외 처리기"""
    error_msg = ''.join(traceback.format_exception(exctype, value, traceback_obj))
    print("예외 발생:", error_msg)

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("An error has occurred in the application.")
    msg.setInformativeText("Please refer to the details below for more information about the error.")
    msg.setDetailedText(error_msg)
    msg.setWindowTitle("Error Occurred")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()


class MainWindowLoader(QThread):
    """메인 윈도우를 별도 스레드에서 로딩하는 클래스"""
    window_loaded = pyqtSignal(object)  # 메인 윈도우가 로드되면 시그널 발생
    loading_progress = pyqtSignal(int, str)  # 진행률과 상태 메시지
    error_occurred = pyqtSignal(str)  # 에러 발생 시그널

    def __init__(self):
        super().__init__()
        self.main_window = None

    def run(self):
        """백그라운드에서 메인 윈도우 초기화"""
        try:
            # 1단계: 리소스 로딩
            self.loading_progress.emit(25, "Loading resources...")
            self.msleep(300)  # 실제 로딩 시뮬레이션

            # 폰트 매니저 로딩
            from app.resources.fonts.font_manager import font_manager

            # 2단계: 모듈 임포트
            self.loading_progress.emit(50, "Importing modules...")
            self.msleep(300)

            from app.views.main_window import MainWindow

            # 3단계: 메인 윈도우 생성 준비
            self.loading_progress.emit(75, "Creating main window...")
            self.msleep(300)

            # 메인 스레드에서 UI 생성을 위해 시그널 발생
            self.loading_progress.emit(90, "Preparing UI...")
            self.msleep(200)

            # 완료
            self.loading_progress.emit(100, "Starting application...")
            self.window_loaded.emit(MainWindow)  # 클래스 객체 전달

        except Exception as e:
            error_msg = f"Failed to load main window: {str(e)}\n{traceback.format_exc()}"
            self.error_occurred.emit(error_msg)


class SplashController(QObject):
    """스플래시 화면과 메인 윈도우 로딩을 제어하는 컨트롤러"""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.splash = None
        self.main_window = None
        self.loader_thread = None

    def start_application(self):
        """애플리케이션 시작"""

        # 스플래시 화면 생성 및 표시
        self.splash = SplashStart()
        self.splash.show()

        # 메인 윈도우 로더 스레드 시작
        self.loader_thread = MainWindowLoader()
        self.loader_thread.loading_progress.connect(self.update_splash_progress)
        self.loader_thread.window_loaded.connect(self.on_main_window_loaded)
        self.loader_thread.error_occurred.connect(self.on_loading_error)
        self.loader_thread.start()

    def update_splash_progress(self, progress, message):
        """스플래시 화면 진행률 업데이트"""
        if self.splash:
            self.splash.update_progress_external(progress, message)

    def on_main_window_loaded(self, MainWindowClass):
        """메인 윈도우 로딩 완료 시 호출"""
        try:
            # 메인 스레드에서 UI 생성
            self.main_window = MainWindowClass()
            self.main_window.show()

            # 스플래시 화면 숨김
            if self.splash:
                self.splash.hide()
                self.splash.close()

            # 로더 스레드 정리
            if self.loader_thread:
                self.loader_thread.quit()
                self.loader_thread.wait()

        except Exception as e:
            self.on_loading_error(f"Error creating main window: {str(e)}")

    def on_loading_error(self, error_message):
        """로딩 에러 처리"""
        print(f"Loading error: {error_message}")

        # 에러 다이얼로그 표시
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Failed to start application")
        msg.setInformativeText(error_message)
        msg.setWindowTitle("Startup Error")
        msg.exec_()

        # 애플리케이션 종료
        if self.splash:
            self.splash.close()
        self.app.quit()


def _styled_msgbox(parent, title, text,
                   icon=QMessageBox.NoIcon,
                   buttons=QMessageBox.Ok,
                   defaultButton=QMessageBox.NoButton):
    msg = QMessageBox(parent)
    msg.setStyle(QStyleFactory.create("Fusion"))
    msg.setStyleSheet(AppStyle.get_stylesheet())
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(buttons)
    if defaultButton != QMessageBox.NoButton:
        msg.setDefaultButton(defaultButton)
    return msg.exec_()


if __name__ == "__main__":
    # High DPI 설정
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)


    # 스타일된 메시지박스 설정 (람다 함수 구문 오류 수정)
    def warning_box(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        return _styled_msgbox(parent, title, text, QMessageBox.NoIcon, buttons, defaultButton)


    def information_box(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        return _styled_msgbox(parent, title, text, QMessageBox.NoIcon, buttons, defaultButton)


    def critical_box(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        return _styled_msgbox(parent, title, text, QMessageBox.NoIcon, buttons, defaultButton)


    def question_box(parent, title, text, buttons=(QMessageBox.Yes | QMessageBox.No),
                     defaultButton=QMessageBox.NoButton):
        return _styled_msgbox(parent, title, text, QMessageBox.NoIcon, buttons, defaultButton)


    QMessageBox.warning = warning_box
    QMessageBox.information = information_box
    QMessageBox.critical = critical_box
    QMessageBox.question = question_box

    # 글로벌 예외 처리기 설정
    sys.excepthook = exception_hook

    try:
        from app.resources.fonts.font_manager import font_manager
        success = font_manager.set_app_font(app, "SamsungSharpSans-Bold")
        if not success:
            print("경고: 폰트 설정 실패, 기본 폰트 사용")
        # 스플래시 컨트롤러 생성 및 시작
        controller = SplashController(app)
        controller.start_application()

    except Exception as e:
        print(f"초기화 오류: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 이벤트 루프 시작
    sys.exit(app.exec_())