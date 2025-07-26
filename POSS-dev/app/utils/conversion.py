import pandas as pd

"""
다양한 값을 지정한 타입으로 변환하는 함수

Args:
    value: 변환할 값
    target_type: 대상 타입 (int, float, str 등)
    default: 변환 실패 시 반환할 기본값
    handle_commas: 문자열에서 콤마 제거 여부
    preserve_empty: None, NaN, 빈 문자열을 보존할지 여부 (True면 default 대신 원래 값 반환)
    special_values: 특별히 보존할 값들의 집합 (예: {'ALL', 'NONE'})
        
    Returns:
        변환된 값 또는 기본값
"""
def convert_value(value, target_type=float, default=None, handle_commas=True, preserve_empty=False, special_values=None):
    # 특수값 처리 : 그대로 보존
    if special_values and value in special_values:
        return value
    
    # None, NaN, 빈문자열 처리 
    if pd.isna(value) or value == '':
        if preserve_empty:
            # 빈값을 보존해야 하는 경우
            if value == '':
                return '' if target_type == str else None  # 타입에 맞는 빈 값 반환
            return value # 원래 값(None, NaN) 그대로 반환
        return default
    
    # 문자열 전처리
    if isinstance(value, str):
        # 콤마 제거
        if handle_commas:
            value = value.replace(',', '')

        # 숫자만 포함된 문자열 제거
        if target_type in (int, float) and value.isdigit():
            pass  

    try:
        if target_type == int and isinstance(value, float):
            return int(value)  # float -> int
        return target_type(value)
    except(ValueError, TypeError):
        return default
    