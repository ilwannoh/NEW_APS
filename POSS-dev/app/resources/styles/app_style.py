"""애플리케이션 전역 스타일시트를 모아두는 클래스"""
class AppStyle:

    # QMessageBox 전용 스타일
    MESSAGE_BOX_QSS = """
            QMessageBox, QDialog {
            background-color: white;
            border: none;
        }
        QMessageBox QFrame {
            background-color: white;
            border: none;
        }
        QMessageBox QWidget {
            background-color: white;
            border: none;
        }
        QMessageBox QLabel, QDialog QLabel {
            background-color: white;
            color: #333;
            padding: 4px 30px 4px 8px;
            font-size: 12px;
        }
        QMessageBox QScrollArea, QMessageBox QScrollArea QWidget {
            background-color: white;
            border: none;
        }
        QMessageBox QPushButton, QDialog QPushButton {
            background-color: #1428A0;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        }
        QMessageBox QPushButton:hover, QDialog QPushButton:hover {
            background-color: #0F1F7E;
        }
    """

    """
    전체 애플리케이션에 적용할 스타일시트를 반환
    """
    @classmethod
    def get_stylesheet(cls) -> str:
        return cls.MESSAGE_BOX_QSS
