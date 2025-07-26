import pandas as pd

"""
데이터에서 내부 필드를 제거하는 유틸리티 함수

Parameters:
    data: 필터링할 데이터 (dict 또는 pandas DataFrame)
    extra_fields: 추가로 제거할 필드 목록 (선택 사항)

Returns:
    필터링된 데이터 (입력과 동일한 타입)
"""
def filter_internal_fields(data, extra_fields=None):
    # 데이터가 없으면 빈 객체 반환
    if data is None:
        return None
    
    # 기본 내부 필드 목록
    internal_fields = ['_id', '_is_copy', '_drop_pos_x', '_drop_pos_y', 
                      '_validation_failed', '_validation_message']
    
    # 추가 필드가 있으면 병합
    if extra_fields:
        internal_fields.extend(extra_fields)
    
    # DataFrame인 경우
    if isinstance(data, pd.DataFrame):
        filtered_df = data.copy()
        
        # 명시된 내부 필드 제거
        for field in internal_fields:
            if field in filtered_df.columns:
                filtered_df.drop(columns=[field], inplace=True)
        
        # 언더스코어로 시작하는 모든 컬럼 제거
        cols_to_drop = [col for col in filtered_df.columns 
                       if isinstance(col, str) and col.startswith('_')]
        if cols_to_drop:
            filtered_df.drop(columns=cols_to_drop, inplace=True)
            
        return filtered_df
    
    # 딕셔너리인 경우
    elif isinstance(data, dict):
        filtered_dict = {}
        
        for key, value in data.items():
            # 내부 필드 건너뛰기
            if key in internal_fields or (isinstance(key, str) and key.startswith('_')):
                continue
            filtered_dict[key] = value
            
        return filtered_dict
    
    # 지원하지 않는 타입인 경우 원본 반환
    return data