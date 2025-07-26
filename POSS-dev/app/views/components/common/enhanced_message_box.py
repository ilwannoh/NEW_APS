from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QDialog)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt

"""
메시지 박스 클래스
"""
class EnhancedMessageBox:
    
    """
    검증 오류 메시지 박스 표시
    """
    @staticmethod
    def show_validation_error(parent, title, message):
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setFixedSize(600, 200)
        
        layout = QVBoxLayout(dialog)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #DC3545;
                border-radius: 10px;
            }
            QLabel {
                color: #333;
                padding: 10px;
                font-size: 20px;
            }
            QPushButton {
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
                font-size: 16px;
            }
        """)
        
        # 제목
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #DC3545; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 메시지
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 14))
        message_label.setStyleSheet("color: #333; padding: 10px;")
        layout.addWidget(message_label)
        
        # 버튼들
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        # OK 버튼
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            background-color: #DC3545;
            color: white;
        """)
        ok_button.setCursor(QCursor(Qt.PointingHandCursor))
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        
        return dialog.exec_() == QDialog.Accepted
    
    """
    검증 성공 메시지 박스 표시
    """
    @staticmethod
    def show_validation_success(parent, title, message):
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setFixedSize(600, 200)
        
        layout = QVBoxLayout(dialog)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #1428A0;
                border-radius: 10px;
            }
            QLabel {
                color: #333;
                padding: 10px;
                font-size: 20px;
            }
            QPushButton {
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
                font-size: 16px;
            }
        """)
        
        # 제목
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #1428A0; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 메시지
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 14))
        message_label.setStyleSheet("color: #333; padding: 10px;")
        layout.addWidget(message_label)
        
        # 버튼들
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        # OK 버튼
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            background-color: #1428A0;
            color: white;
        """)
        ok_button.setCursor(QCursor(Qt.PointingHandCursor))
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        
        return dialog.exec_() == QDialog.Accepted
    

    """
    확인 다이얼로그 (Yes/No)
    """
    @staticmethod
    def show_confirmation(parent, title, message):
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setFixedSize(600, 200)
        
        layout = QVBoxLayout(dialog)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #1428A0;
                border-radius: 10px;
            }
            QLabel {
                color: #333;
                padding: 10px;
                font-size: 20px;
            }
            QPushButton {
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
                font-size: 16px;
            }
        """)
        
        # 제목 (제목이 있을 때만 표시)
        if title:
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setFont(QFont("Arial", 18, QFont.Bold))
            title_label.setStyleSheet("color: #1428A0; font-weight: bold;")
            layout.addWidget(title_label)
        
        # 메시지
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 14))
        message_label.setStyleSheet("color: #333; padding: 10px;")
        layout.addWidget(message_label)
        
        # 버튼들
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        # Yes 버튼
        yes_button = QPushButton("Yes")
        yes_button.setStyleSheet("""
            background-color: #1428A0;
            color: white;
        """)
        yes_button.setCursor(QCursor(Qt.PointingHandCursor))
        yes_button.clicked.connect(dialog.accept)
        button_layout.addWidget(yes_button)
        
        button_layout.addSpacing(10)
        
        # No 버튼
        no_button = QPushButton("No")
        no_button.setStyleSheet("""
            background-color: #808080;
            color: white;
        """)
        no_button.setCursor(QCursor(Qt.PointingHandCursor))
        no_button.clicked.connect(dialog.reject)
        button_layout.addWidget(no_button)
        
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        
        return dialog.exec_() == QDialog.Accepted