# components/__init__.py

# 모든 컴포넌트를 임포트해서 components 패키지에서 직접 접근할 수 있게 함
from app.views.components.navbar.navbar import Navbar
from app.views.components.data_input_page import DataInputPage
from .pre_assigned_page import PlanningPage
from .result_page import ResultPage

# __all__을 정의하여 from components import * 사용 시 가져올 항목 지정
__all__ = ['Navbar', 'DataInputPage', 'PlanningPage', 'ResultPage']