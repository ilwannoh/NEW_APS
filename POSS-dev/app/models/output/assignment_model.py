from PyQt5.QtCore import QObject, pyqtSignal
import uuid  
import pandas as pd
from typing import List, Optional
from app.utils.item_key_manager import ItemKeyManager
from app.utils.field_filter import filter_internal_fields

"""
내부에 DataFrame을 들고 다니며,수량 변경, 이동, 리셋, 적용 같은 모든 로직을 한곳에서 처리
시그널:
    - modelDataChanged: 모델의 데이터가 바뀌었음을 뷰(View)에 알림 
    - validationFailed: 검증 오류 메시지를 뷰에 전달 
    - dataModified: 데이터 변경 여부 전달
"""
class AssignmentModel(QObject):
    # 세분화된 시그널들
    itemAdded = pyqtSignal(dict)          # 아이템 추가 (복사 등)
    itemMoved = pyqtSignal(dict, dict)    # 아이템 이동 (old_data, new_data)
    itemDeleted = pyqtSignal(str)         # 아이템 삭제 (item_id)
    quantityUpdated = pyqtSignal(dict)    # 수량 변경 (item_data)

    # 기존 시그널들 (대량 변경 시에만 사용)
    modelDataChanged = pyqtSignal()  # 모델의 데이터가 바뀌었음을 뷰(View)에 알리는 시그널
    validationFailed = pyqtSignal(dict, str)  # 검증(validation) 오류가 발생했을 때 오류 메시지를 전달하는 시그널
    dataModified = pyqtSignal(bool)  # True: 변경됨, False: 원본과 동일

    """
    assignment_df: 최적화 결과로 넘어온 전체 DataFrame
    pre_assigned: 사전할당된 아이템 리스트
    validator: PlanAdjustmentValidator 인스턴스
    """
    def __init__(self, assignment_df: pd.DataFrame, pre_assigned: List[str], validator):
        super().__init__()

        assignment_df = self._ensure_correct_types(assignment_df.copy()) # 초기 데이터프레임에 타입 강제 적용

        # ID 컬럼이 없거나 모두 NaN이면 ID 생성
        if '_id' not in assignment_df.columns or assignment_df['_id'].isna().all():
            import uuid
            # 모든 행에 고유 ID 할당
            assignment_df['_id'] = [str(uuid.uuid4()) for _ in range(len(assignment_df))]

        self._original_df = assignment_df.copy()  # 리셋 가능하게 복사
        self._df = assignment_df.copy()  # 실제 뷰로 전달되고 수정할 데이터
        self.pre_assigned = set(pre_assigned)  # 사전할당된 아이템 집합
        self.validator = validator  # 검증 인스턴스
    
    """
    DataFrame의 타입을 올바르게 강제 변환
    """
    def _ensure_correct_types(self, df):
        if df is not None and not df.empty:
            # Line은 항상 문자열
            if 'Line' in df.columns:
                df['Line'] = df['Line'].astype(str)
            
            # Time은 항상 정수
            if 'Time' in df.columns:
                df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0).astype(int)
            
            # Item은 항상 문자열
            if 'Item' in df.columns:
                df['Item'] = df['Item'].astype(str)
            
            # Qty는 항상 정수
            if 'Qty' in df.columns:
                df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        
        return df

    """
    현재 할당 결과 반환
    """
    def get_dataframe(self) -> pd.DataFrame:
        print(f"[Model] get_dataframe 호출, self._df 타입: {type(self._df)}")
    
        if not isinstance(self._df, pd.DataFrame):
            print(f"[Model ERROR] self._df가 DataFrame이 아님: {type(self._df)}")
            if isinstance(self._df, dict):
                print(f"[Model ERROR] dict 키들: {list(self._df.keys())}")
            return pd.DataFrame()  # 빈 DataFrame 반환
    
        df = self._df.copy()
        return self._ensure_correct_types(df)

    """
    수량 변경 업데이트
    """
    def update_qty(self, item: str, line: str, time: int, new_qty: int, item_id: str = None):
        # 1) 라인, 시간, 아이템으로 정확한 행 찾기
        # ID가 제공된 경우 ID로 찾기
        if item_id:
            mask = ItemKeyManager.create_mask_by_id(self._df, item_id)
        else:
            # 기존 방식으로 찾기
            mask = ItemKeyManager.create_mask_for_item(self._df, line, time, item)
    
        if not mask.any():
            print(f"Model: 해당 아이템({item}, {line}, {time})을 찾을 수 없습니다.")
            return
        
        # 변경이 필요한지 확인
        current_qty = self._df.loc[mask, 'Qty'].iloc[0]
        if current_qty == new_qty:
            return True  # 이미 동일한 값이면 변경 없이 성공으로 처리

        # 2) 해당 행의 수량만 업데이트
        self._df.loc[mask, 'Qty'] = int(new_qty)
        print(f"Model: {item} @ {line}-{time} 수량 변경: {new_qty}")

        # 3) 수정된 아이템에 대해 검증 수행
        error_msg = self._validate_item(item, line, time, item_id)
        row = self._df.loc[mask].iloc[0].to_dict()  # 현재 행 전체 정보
        self.validationFailed.emit(row, error_msg)

        # 원본과 현재 데이터 비교하여 변경 여부 확인
        has_changes = self._check_for_changes()
        self.dataModified.emit(has_changes)
        
        # 4) 모든 처리 후 뷰에 데이터 변경 알림
        self.quantityUpdated.emit(row)

        return True

    """
    아이템을 new_line, new_shift로 이동
    """
    def move_item(self, item, old_line, old_time, new_line, new_time, item_id=None):
        # 변경사항이 없으면 조기 종료 (기존 코드 유지)
        if str(old_line) == str(new_line) and int(old_time) == int(new_time):
            return

        # ID 또는 조건으로 마스크 생성
        if item_id:
            mask = ItemKeyManager.create_mask_by_id(self._df, item_id)
        else:
            mask = ItemKeyManager.create_mask_for_item(self._df, old_line, old_time, item)

        if not mask.any():
            print(f"Model: 해당 아이템을 찾을 수 없습니다.")
            return
        
        # 이동 전 데이터 백업
        old_data = self._df.loc[mask].iloc[0].to_dict()

        # Line/Time 컬럼 업데이트
        self._df.loc[mask, 'Line'] = str(new_line)
        self._df.loc[mask, 'Time'] = int(new_time)

        # 검증과 시그널을 한 번에 처리
        error_msg = self._validate_item(item, new_line, new_time, item_id, source_line=old_line, source_time=old_time)
        new_data = self._df.loc[mask].iloc[0].to_dict()
        row = self._df.loc[mask].iloc[0].to_dict()

        # 변경 여부 확인
        has_changes = self._check_for_changes()

        # 시그널을 한 번에 발생 (중복 방지)
        self.dataModified.emit(has_changes)
        self.itemMoved.emit(old_data, new_data)
        self.validationFailed.emit(row, error_msg)
        

    """
    원본 상태로 복원
    """
    def reset(self):
        self._df = self._original_df.copy()
        self.dataModified.emit(False)
        self.modelDataChanged.emit()

    """
    현재 상태를 원본에 반영
    """
    def apply(self):
        self._original_df = self._df.copy()
        self.modelDataChanged.emit()

    """
    PlanAdjustmentValidator로 검증, 오류 메시지 반환
    """
    def _validate_item(self, item: str, line: str = None, time: int = None, item_id: str = None, source_line: str = None, source_time: int = None) -> Optional[str]:
        try:
           # ID가 제공된 경우 ID로 찾기
            if item_id:
                mask = ItemKeyManager.create_mask_by_id(self._df, item_id)
                if mask.any():
                    row = self._df.loc[mask].iloc[0]
                    item = row['Item']
                    line = row['Line']
                    time = row['Time']
                else:
                    return f"ID {item_id}를 가진 아이템을 찾을 수 없습니다."
            # 라인과 시간이 지정되지 않은 경우, DataFrame에서 해당 아이템 검색
            elif line is None or time is None:
                mask = self._df['Item'] == item
                if not mask.any():
                    return f"아이템 {item}을 찾을 수 없습니다."
                    
                row = self._df.loc[mask].iloc[0]
                line = row.get('Line')
                time = row.get('Time')
            
            # 실제 검증 수행
            valid, message = self.validator.validate_adjustment(
                line,
                time, 
                item,
                self.get_item_qty(item, line, time, item_id),
                source_line=source_line,  # 이동 모드 파라미터 추가
                source_time=source_time,  # 이동 모드 파라미터 추가
                item_id=item_id
            )
            return None if valid else message
        
        except Exception as e:
            print(f"검증 오류: {e}")
            return f"검증 중 오류 발생: {str(e)}"
        

    """
    특정 위치의 아이템 수량 가져오기
    """
    def get_item_qty(self, item: str, line: str, time: int, item_id: str=None) -> int:
        if item_id:
            mask = ItemKeyManager.create_mask_by_id(self._df, item_id)
        else:
            mask = ItemKeyManager.create_mask_for_item(self._df, line, time, item)

        if mask.any():
            return int(self._df.loc[mask, 'Qty'].iloc[0])
        return 0
    

    """
    새 아이템을 데이터프레임에 추가
    """
    def add_new_item(self, item, line, time, qty, full_data=None):
       # 새 행 데이터 준비
        new_row = {'Line': line, 'Time': time, 'Item': item, 'Qty': qty}
        
        # 고유 ID 처리 - 복사 작업인지 확인하여 ID 생성 또는 재사용
        if full_data and '_id' in full_data:
            # 복사 작업인 경우 항상 새 ID 생성
            if full_data.get('_is_copy') == True:
                new_row['_id'] = str(uuid.uuid4())
            else:
                # 복사가 아닌 경우 기존 ID 유지
                new_row['_id'] = full_data['_id']
        else:
            # ID가 없는 경우 새로 생성
            new_row['_id'] = str(uuid.uuid4())
        
        # 추가 데이터가 있으면 병합
        if full_data:
            for key, value in full_data.items():
                if key not in new_row and not key.startswith('_') or key == '_is_copy':
                    # '_is_copy' 플래그는 유지, 다른 내부 필드는 제외
                    new_row[key] = value
        
        # 복사 작업이 아닌 경우 기존 아이템 업데이트
        if not (full_data and full_data.get('_is_copy')):
            mask = ItemKeyManager.create_mask_for_item(self._df, line, time, item)
            if mask.any():
                self._df.loc[mask, 'Qty'] = qty

                #기존 아이템 업데이트 시에도 검증 필요
                error_msg = self._validate_item(item, line, time, new_row['_id'])
                updated_row = self._df.loc[mask].iloc[0].to_dict()
                self.validationFailed.emit(updated_row, error_msg)
                
                # 수량 업데이트 시그널
                self.quantityUpdated.emit(updated_row)
                return True
        
        # 새 행을 DataFrame에 추가
        self._df = pd.concat([self._df, pd.DataFrame([new_row])], ignore_index=True)

        # 새 아이템 추가 시에도 검증 필요 (복사 시 CAPA 초과 등 확인)
        error_msg = self._validate_item(item, line, time, new_row['_id'])
        self.validationFailed.emit(new_row, error_msg)

        # 원본과 현재 데이터 비교하여 변경 여부 확인
        has_changes = self._check_for_changes()
        self.dataModified.emit(has_changes)

        # 아이템 추가 시그널만 발생 (전체 재구성 없음)
        self.itemAdded.emit(new_row)

        return True

    """
    ID로 아이템 삭제
    """
    def delete_item_by_id(self, item_id: str) -> bool:
        # ItemKeyManager를 사용하여 마스크 생성
        mask = ItemKeyManager.create_mask_by_id(self._df, item_id)
        
        if not mask.any():
            print(f"Model: 삭제할 아이템(ID: {item_id})을 찾을 수 없습니다.")
            return False
        
        # 아이템 정보 로깅
        row = self._df.loc[mask].iloc[0]
        line, time, item = ItemKeyManager.get_item_from_data(row.to_dict())
        
        # 아이템 삭제
        self._df = self._df[~mask].reset_index(drop=True)
        print(f"Model: 아이템 {item} @ {line}-{time} (ID: {item_id}) 삭제됨")

        # 원본과 현재 데이터 비교하여 변경 여부 확인
        has_changes = self._check_for_changes()
        self.dataModified.emit(has_changes)

        # 아이템 삭제 시그널만 발생 (전체 재구성 없음)
        self.itemDeleted.emit(item_id)
        
        return True
    

    def get_comparison_dataframe(self):
        return {
            'original': self._ensure_correct_types(self._original_df.copy()),
            'adjusted': self._ensure_correct_types(self._df.copy())
        }

    def set_new_dataframe(self, new_df: pd.DataFrame):
        new_df = self._ensure_correct_types(new_df.copy())

        # ID가 없거나 비어 있으면 새로 생성
        if '_id' not in new_df.columns or new_df['_id'].isna().all():
            new_df['_id'] = [str(uuid.uuid4()) for _ in range(len(new_df))]

        self._df = new_df.copy()
        self._original_df = new_df.copy()
        print("[DEBUG] 모델에 새 데이터프레임 설정 완료")

        self.modelDataChanged.emit()

    
    """
    UI 표시용 필터링된 데이터프레임 반환
    """
    def get_dataframe_for_display(self):
        df = self.get_dataframe()
        return filter_internal_fields(df)
    

    """
    원본 데이터와 현재 데이터 비교하여 변경 여부 확인
    """
    def _check_for_changes(self) -> bool:
        # 행 수가 다르면 변경된 것
        if len(self._original_df) != len(self._df):
            return True
            
        # 주요 컬럼 비교
        key_columns = ['Line', 'Time', 'Item', 'Qty']
        for col in key_columns:
            if col in self._original_df.columns and col in self._df.columns:
                if not self._original_df[col].equals(self._df[col]):
                    return True
        
        return False