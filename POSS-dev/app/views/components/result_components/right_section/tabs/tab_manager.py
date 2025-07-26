from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QStackedWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QCursor
from app.resources.styles.result_style import ResultStyles
from app.views.components.result_components.right_section.tabs.summary_tab import SummaryTab
from app.views.components.result_components.right_section.tabs.capa_tab import CapaTab
from app.views.components.result_components.right_section.tabs.material_tab import MaterialTab
from app.views.components.result_components.right_section.tabs.plan_tab import PlanTab
from app.views.components.result_components.right_section.tabs.portcapa_tab import PortCapaTab
from app.views.components.result_components.right_section.tabs.shipment_tab import ShipmentTab
from app.views.components.result_components.right_section.tabs.splitview_tab import SplitViewTab
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

"""결과 페이지 시각화 탭 관리 클래스"""
class TabManager(QObject):
    # 탭 설정 정보
    TAB_CONFIGS = {
        'Summary':  {'class': SummaryTab},
        'Capa':     {'class': CapaTab},
        'Material': {'class': MaterialTab},
        'PortCapa': {'class': PortCapaTab},
        'Plan':     {'class': PlanTab},
        'Shipment': {'class': ShipmentTab},
        'SplitView':{'class': SplitViewTab},
    }


    tab_changed = pyqtSignal(str, int)  # 탭이름, 인덱스

    def __init__(self, parent_page):
        super().__init__(parent_page)
        self.parent_page = parent_page
        self.tab_names = list(self.TAB_CONFIGS.keys())
        self.buttons = []
        self.stack_widget = None
        self.current_tab_idx = 0
        self.tab_instances = {}
        self.material_manager = None  # 자재 부족량 관리자

    """
    자재 매니저 설정
    """
    def set_material_manager(self, material_manager):
        self.material_manager = material_manager
        
        # Material 탭이 이미 생성된 경우, 부모 페이지의 참조 업데이트
        if hasattr(self.parent_page, 'material_analyzer') and self.material_manager:
            self.parent_page.material_analyzer = self.material_manager.get_analyzer()

    """
    QStackedWidget 객체 연결
    """
    def set_stack_widget(self, stack_widget: QStackedWidget):
        print("[TabManager] set_stack_widget() 호출 :", stack_widget)
        self.stack_widget = stack_widget
        
    """
    탭 버튼 생성 + 페이지 인스턴스화 → 스택에 추가
    button_layout: 버튼을 붙일 레이아웃
    stack_widget은 반드시 set_stack_widget() 이후에 호출하세요.
    """

    def create_tab_buttons(self, button_layout: QHBoxLayout):
        if self.stack_widget is None:
            raise RuntimeError("Call set_stack_widget() 먼저 해주세요.")

        # 간격 설정
        button_layout.setSpacing(2)  # f(2)에 해당하는 값
        button_layout.setContentsMargins(10, 8, 10, 8)  # w(10), h(8) 등에 해당하는 값

        try:
            btn_font = font_manager.get_just_font("SamsungOne-700").family()
        except:
            btn_font = "Arial"  # 기본 폰트로 대체

        for idx, name in enumerate(self.tab_names):
            # 1) 탭 페이지 생성
            TabClass = self.TAB_CONFIGS[name]['class']
            page = TabClass(parent=self.parent_page)

            # 2) 스택에 추가 & 참조 저장
            self.stack_widget.addWidget(page)
            self.tab_instances[name] = page

            # 3) 버튼 생성
            btn = QPushButton(name)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setMinimumWidth(80)  # w(80)에 해당하는 값
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # 첫 탭만 활성 스타일
            if idx == 0:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #1428A0;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: {w(4)}px {h(8)}px;
                        min-height: {h(26)}px;
                        font-weight: bold;
                        font-family: {btn_font};
                        font-size: {f(13)}px;
                    }}
                    QPushButton:hover {{
                        background-color: #0F1F8A;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: white;
                        color: #666666;
                        border: 1px solid #E0E0E0;
                        border-radius: 5px;
                        padding: {w(4)}px {h(8)}px;
                        min-height: {h(26)}px;
                        font-weight: bold;
                        font-family: {btn_font};
                        font-size: {f(13)}px;
                    }}
                    QPushButton:hover {{
                        background-color: #F5F5F5;
                        color: #1428A0;
                        border-color: #1428A0;
                    }}
                """)

            # 클릭 시 전환
            btn.clicked.connect(lambda _, i=idx: self.switch_tab(i))
            button_layout.addWidget(btn)
            self.buttons.append(btn)

        # 초기 탭 활성화
        self.switch_tab(0)
    
    
    """
    버튼 클릭 시 호출되어 스택 위젯을 전환하고 버튼 스타일 갱신
    """

    def switch_tab(self, idx: int):
        if not self.stack_widget or idx < 0 or idx >= len(self.tab_names):
            return

        # 1) 스택 위젯 인덱스 전환
        self.stack_widget.setCurrentIndex(idx)
        self.current_tab_idx = idx

        # 폰트 설정 - font_manager가 있다고 가정하고, 없으면 시스템 기본 글꼴 사용
        try:
            btn_font = font_manager.get_just_font("SamsungOne-700").family()
        except:
            btn_font = "Arial"  # 기본 폰트로 대체

        # 2) 버튼 스타일 업데이트
        for i, btn in enumerate(self.buttons):
            if i == idx:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #1428A0;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: {w(4)}px {h(8)}px;
                        min-height: {h(26)}px;
                        font-weight: bold;
                        font-family: {btn_font};
                        font-size: {f(13)}px;
                    }}
                    QPushButton:hover {{
                        background-color: #0F1F8A;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: white;
                        color: #666666;
                        border: 1px solid #E0E0E0;
                        border-radius: 5px;
                        padding: {w(4)}px {h(8)}px;
                        min-height: {h(26)}px;
                        font-weight: bold;
                        font-family: {btn_font};
                        font-size: {f(13)}px;
                    }}
                    QPushButton:hover {{
                        background-color: #F5F5F5;
                        color: #1428A0;
                        border-color: #1428A0;
                    }}
                """)

        # 3) 탭별 콘텐츠 업데이트 (필요한 경우)
        tab_name = self.tab_names[idx]
        page = self.tab_instances.get(tab_name)

        # capa 탭은 두가지 parameter 필요
        if tab_name == 'Capa' and page:
            page.update_content(getattr(self.parent_page, 'capa_ratio_data', None),
                                getattr(self.parent_page, 'utilization_data', None))

        # 4) 시그널 방출
        self.tab_changed.emit(tab_name, idx)

        print(f"탭 전환 완료: {tab_name} - 분석 없이 표시만")

    
    """
    탭 인스턴스 반환
    """
    def get_tab_instance(self, tab_name):
        return self.tab_instances.get(tab_name)
    