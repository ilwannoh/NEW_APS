"""
APS 생산계획 시스템 메인 엔트리 포인트
"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QStyleFactory
from PyQt5.QtCore import Qt

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.views.main_window import MainWindow
from app.resources.styles.app_style import AppStyle


def exception_hook(exctype, value, traceback_obj):
    """전역 예외 처리기"""
    import traceback
    error_msg = ''.join(traceback.format_exception(exctype, value, traceback_obj))
    print("예외 발생:", error_msg)
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("프로그램 실행 중 오류가 발생했습니다.")
    msg.setInformativeText("자세한 내용은 아래를 참조하세요.")
    msg.setDetailedText(error_msg)
    msg.setWindowTitle("오류 발생")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()


def main():
    """메인 함수"""
    # High DPI 설정
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    # 애플리케이션 생성
    app = QApplication(sys.argv)
    app.setApplicationName("APS Production Planning System")
    app.setOrganizationName("APS Development Team")
    
    # 스타일 설정
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 글로벌 예외 처리기 설정
    sys.excepthook = exception_hook
    
    try:
        # 메인 윈도우 생성 및 표시
        window = MainWindow()
        window.show()
        
        # 이벤트 루프 시작
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(
            None,
            "시작 오류",
            f"프로그램을 시작할 수 없습니다:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()