"""
아이템 식별을 위한 유틸리티 함수들
"""
import pandas as pd
from typing import Dict, Any, Optional, Tuple

"""
아이템 고유 키 관리 클래스
"""
class ItemKeyManager:
    
    """
    아이템의 고유 키 생성
    Args:
        line: 라인 정보 (문자열/숫자)
        time: 시간 정보 (문자열/숫자)
        item: 아이템 코드
    Returns:
        고유 키 문자열
    """
    @staticmethod
    def get_item_by_not_id(line: Any, time: Any, item: Any) -> str:
        # None이나 빈 값 처리
        line_str = str(line) if line is not None else ""
        time_str = str(time) if time is not None else ""
        item_str = str(item) if item is not None else ""
        
        return f"{line_str}_{time_str}_{item_str}"
    
    """
    아이템 키를 파싱하여 line, time, item 반환
    Args:
        item_key: 고유 키 문자열
    Returns:
        (line, time, item) 튜플
    """
    @staticmethod
    def parse_item_key(item_key: str) -> Tuple[str, str, str]:
        parts = item_key.split('_', 2)  # 최대 3개로 분할
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        return "", "", ""
    
    """
    DataFrame에서 특정 아이템 찾기
    Args:
        df: 검색할 DataFrame
        line: 라인 정보
        time: 시간 정보
        item: 아이템 코드
    Returns:
        해당하는 행(Series) 또는 빈 Series
    """
    @staticmethod
    def find_item_in_dataframe(df: pd.DataFrame, line: Any, time: Any, item: Any) -> pd.Series:
        if df.empty:
            return pd.Series()
        
        mask = (
            (df['Line'].astype(str) == str(line)) &
            (df['Time'].astype(str) == str(time)) &
            (df['Item'].astype(str) == str(item))
        )
        
        matching_rows = df[mask]
        return matching_rows.iloc[0] if not matching_rows.empty else pd.Series()
    
    """
    특정 아이템에 대한 마스크 생성
    Args:
        df: 대상 DataFrame
        line: 라인 정보
        time: 시간 정보
        item: 아이템 코드
    Returns:
        boolean mask Series
    """
    @staticmethod
    def create_mask_for_item(df: pd.DataFrame, line: Any, time: Any, item: Any) -> pd.Series:
        # DataFrame에 필요한 컬럼이 있는지 확인
        if not all(col in df.columns for col in ['Line', 'Time', 'Item']):
            return pd.Series(dtype=bool)
        
        # 타입 변환 보장
        line_str = str(line) if line is not None else ""
        time_val = int(time) if time is not None else 0
        item_str = str(item) if item is not None else ""
        
        # 마스크 생성
        mask = (
            (df['Line'].astype(str) == line_str) &
            (df['Time'].astype(int) == time_val) &
            (df['Item'].astype(str) == item_str)
        )
        
        return mask
    
    """
    아이템 데이터 딕셔너리에서 line, time, item 추출
    Args:
        item_data: 아이템 데이터 딕셔너리
    Returns:
        (line, time, item) 튜플
    """
    @staticmethod
    def get_item_from_data(item_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if not item_data:
            return None, None, None
        
        line = item_data.get('Line')
        time = item_data.get('Time')
        item = item_data.get('Item')
        
        return line, time, item
    

    """
    아이템 ID로 마스크 생성 (수정용)
    Args:
        df: 대상 DataFrame
        item_id: 아이템 고유 ID
    Returns:
        boolean mask Series
    """
    @staticmethod
    def create_mask_by_id(df: pd.DataFrame, item_id: str) -> pd.Series:
        if '_id' not in df.columns:
            return pd.Series(False, index=df.index)
        
        return df['_id'] == item_id
    

    """
    ID로 아이템 찾기 (읽기용)
    Args:
        df: 검색할 DataFrame
        item_id: 아이템 고유 ID
    Returns:
        해당하는 행(Series) 또는 빈 Series
    """
    @staticmethod
    def get_item_by_id(df: pd.DataFrame, item_id: str) -> pd.Series:
        if '_id' not in df.columns or not item_id:
            return pd.Series()
        
        mask = df['_id'] == item_id
        matching_rows = df[mask]
        return matching_rows.iloc[0] if not matching_rows.empty else pd.Series()
    

    """
    아이템 객체 또는 데이터 딕셔너리에서 ID 추출
    Args:
        item_or_data: DraggableItemLabel 객체 또는 데이터 딕셔너리
    Returns:
        str: 추출된 ID 또는 None
    """
    @staticmethod
    def extract_item_id(item_or_data):
        item_id = None
        
        if hasattr(item_or_data, 'item_data') and item_or_data.item_data:
            # DraggableItemLabel 객체인 경우
            if '_id' in item_or_data.item_data:
                item_id = item_or_data.item_data.get('_id')
        elif isinstance(item_or_data, dict):
            # 데이터 딕셔너리인 경우
            if '_id' in item_or_data:
                item_id = item_or_data.get('_id')
        
        return item_id
    
    """
    키 생성 - ID 우선, 없으면 Line-Time-Item 조합
    """
    @staticmethod
    def get_item_key(item_info_or_line: Dict[str, Any]) -> str:
        # 딕셔너리가 전달된 경우
        if isinstance(item_info_or_line, dict):
            item_info = item_info_or_line
            if '_id' in item_info and item_info['_id']:
                return str(item_info['_id'])
            else:
                return ItemKeyManager.get_item_by_not_id(
                    item_info.get('Line'),
                    item_info.get('Time'), 
                    item_info.get('Item')
                )
        else:
            # 개별 파라미터가 전달된 경우
            return ItemKeyManager.get_item_by_not_id(item_info_or_line, time, item)