from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager


class ItemStyle:
    bold_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
    normal_font = font_manager.get_just_font("SamsungOne-700").family()

    # 기본 스타일 
    DEFAULT_STYLE = f"""
        QFrame {{
            background-color: #F8F9FA;
            border: 1px solid #DEE2E6;
            border-radius: 0px;
            padding: 5px 5px 5px 5px;  
            margin: 2px;
        }}
        QLabel {{
            font-weight: normal;
            font-family: {normal_font};
        }}
    """

    # 선택됐을 때 스타일 
    SELECTED_STYLE = f"""
        QFrame {{
            background-color: #E3F2FD;
            border: 1px solid #1976D2;
            border-radius: 0px;
            padding: 5px 5px 5px 5px;  
            margin: 2px;
        }}
        QLabel {{
            font-weight: normal;
            font-family: {normal_font};
        }}
    """

    # 호버 스타일 
    HOVER_STYLE = f"""
        QFrame {{
            background-color: #E3F2FD;
            border: 1px solid #1976D2;
            border-radius: 0px;
            padding: 5px 5px 5px 5px;
            margin: 2px;
        }}
        QLabel {{
            font-weight: normal;
            font-family: {normal_font};
        }}
    """

    # 각 상태별 스타일들 - 모두 같은 패딩으로 통일
    # 자재 부족 스타일
    SHORTAGE_STYLE = DEFAULT_STYLE
    SHORTAGE_SELECTED_STYLE = SELECTED_STYLE
    SHORTAGE_HOVER_STYLE = HOVER_STYLE

    # 사전할당 스타일
    PRE_ASSIGNED_STYLE = DEFAULT_STYLE
    PRE_ASSIGNED_SELECTED_STYLE = SELECTED_STYLE
    PRE_ASSIGNED_HOVER_STYLE = HOVER_STYLE

    # 출하 실패 스타일
    SHIPMENT_FAILURE_STYLE = DEFAULT_STYLE
    SHIPMENT_FAILURE_SELECTED_STYLE = SELECTED_STYLE
    SHIPMENT_FAILURE_HOVER_STYLE = HOVER_STYLE

    # 복합 상태들도 모두 같은 스타일 사용
    PRE_ASSIGNED_SHORTAGE_STYLE = DEFAULT_STYLE
    PRE_ASSIGNED_SHORTAGE_SELECTED_STYLE = SELECTED_STYLE
    PRE_ASSIGNED_SHORTAGE_HOVER_STYLE = HOVER_STYLE

    PRE_ASSIGNED_SHIPMENT_STYLE = DEFAULT_STYLE
    PRE_ASSIGNED_SHIPMENT_SELECTED_STYLE = SELECTED_STYLE
    PRE_ASSIGNED_SHIPMENT_HOVER_STYLE = HOVER_STYLE

    SHORTAGE_SHIPMENT_STYLE = DEFAULT_STYLE
    SHORTAGE_SHIPMENT_SELECTED_STYLE = SELECTED_STYLE
    SHORTAGE_SHIPMENT_HOVER_STYLE = HOVER_STYLE

    PRE_ASSIGNED_SHORTAGE_SHIPMENT_STYLE = DEFAULT_STYLE
    PRE_ASSIGNED_SHORTAGE_SHIPMENT_SELECTED_STYLE = SELECTED_STYLE
    PRE_ASSIGNED_SHORTAGE_SHIPMENT_HOVER_STYLE = HOVER_STYLE

    # 검색 시 포커스 스타일
    SEARCH_FOCUSED_STYLE = f"""
        QFrame {{
            background-color: #E3F2FD;
            border: 1px solid #DEE2E6;
            border-radius: 0px;
            padding: 5px 5px 5px 5px;
            margin: 2px;
        }}
        QLabel {{
            font-weight: normal;
            font-family: {normal_font};
            color: #3498DB;
        }}
    """

    # 검색 결과 호버 스타일 - 테두리로 강조
    SEARCH_FOCUSED_HOVER_STYLE = f"""
        QFrame {{
            background-color: #EBF5FB;
            border: 1px solid #3498DB;
            border-radius: 0px;
            padding: 5px 5px 5px 5px;
            margin: 2px;
        }}
        QLabel {{
            font-weight: normal;
            font-family: {normal_font};
            color: #3498DB;
        }}
    """
    # 현재 선택된 검색 결과 스타일
    SEARCH_SELECTED_STYLE = f"""
        QFrame {{
            background-color: #D4E6F1;
            border: 2px solid #3498DB;
            border-radius: 0px;
            padding: 5px 5px 5px 5px;
            margin: 1px;
        }}
        QLabel {{
            font-weight: bold;
            font-family: {normal_font};
            color: #2E86C1;
        }}
    """

    # 현재 검색 결과를 위한 특별 강조 스타일
    SEARCH_CURRENT_STYLE = f"""
        QFrame {{
            background-color: #1428A0;
            border: 2px solid #cccccc;
            border-radius: 0px;
            padding: 5px 5px 5px 5px;
            margin: 1px;
        }}
        QLabel {{
            background-color: transparent;
            color: white;
            font-weight: bold;
            font-family: {normal_font};
        }}
    """