import pandas as pd
from app.utils.item_key_manager import ItemKeyManager

"""
생산 계획의 유지율을 계산하는 클래스
원본 계획과 현재 계획 간의 유지율을 Item별, RMC별로 계산

- 첫 번째 계획인 경우 이전 계획 없음 처리
- 계획 조정 시 조정 전/후 비교 기능 추가
"""
class PlanMaintenanceAnalyzer:

    """
    계획 유지율 분석
    
    Args:
        current_df: 현재 계획 데이터
        previous_df: 이전 계획 데이터 (없으면 자동 로드)
    
    Returns:
        dict: {
            'analyzed': bool,
            'item_data': {'df': DataFrame, 'rate': float},
            'rmc_data': {'df': DataFrame, 'rate': float},
            'changed_items': set,  # UI 표시용
            'message': str
        }
    """
    @staticmethod
    def analyze_maintenance_rate(current_df, previous_df=None):
        if current_df is None or current_df.empty:
            return {'analyzed': False, 'message': 'No current plan data'}
        
        if previous_df is None or previous_df.empty:
            return {
                'analyzed': False, 
                'message': 'No previous plan loaded'
            }
        
        try:
            # 2. Item별 유지율 계산
            item_df, item_rate, changed_items = PlanMaintenanceAnalyzer._calculate_item_maintenance(
                previous_df, current_df
            )
            
            # 3. RMC별 유지율 계산
            rmc_df, rmc_rate, changed_rmcs = PlanMaintenanceAnalyzer._calculate_rmc_maintenance(
                previous_df, current_df
            )
            
            return {
                'analyzed': True,
                'item_data': {'df': item_df, 'rate': item_rate},
                'rmc_data': {'df': rmc_df, 'rate': rmc_rate},
                'changed_items': changed_items,
                'changed_rmcs': changed_rmcs,
                'message': 'Analysis completed successfully'
            }
            
        except Exception as e:
            return {
                'analyzed': False,
                'message': f'Analysis failed: {str(e)}'
            }
    
    """
    Item별 유지율 계산
    """
    @staticmethod
    def _calculate_item_maintenance(prev_df, curr_df):
        # 1. 그룹화
        prev_grouped = prev_df.groupby(['Line', 'Time', 'Item'])['Qty'].sum().reset_index()
        curr_grouped = curr_df.groupby(['Line', 'Time', 'Item'])['Qty'].sum().reset_index()
        
        # 2. 병합
        merged = pd.merge(
            prev_grouped, curr_grouped,
            on=['Line', 'Time', 'Item'],
            how='outer',
            suffixes=('_prev', '_curr')
        )
        
        # NaN을 0으로 처리
        merged['Qty_prev'] = merged['Qty_prev'].fillna(0)
        merged['Qty_curr'] = merged['Qty_curr'].fillna(0)
        
        # 3. 유지 수량 계산
        merged['maintenance'] = merged.apply(
            lambda x: min(x['Qty_prev'], x['Qty_curr']) 
            if x['Qty_prev'] > 0 and x['Qty_curr'] > 0 else 0, 
            axis=1
        )
        
        # 4. 변경된 아이템 식별 (UI 표시용) - ID 기반으로만
        changed_items = set()
        for _, row in merged.iterrows():
            if row['Qty_prev'] != row['Qty_curr']:
                # ID로 해당 아이템 찾기
                mask = ItemKeyManager.create_mask_for_item(
                    curr_df, 
                    row['Line'], 
                    row['Time'], 
                    row['Item']

                )
                if mask.any():
                    # ID가 있으면 ID 우선, 없으면 Line-Time-Item 조합 사용
                    if '_id' in curr_df.columns:
                        item_ids = curr_df.loc[mask, '_id'].dropna().unique()
                        for item_id in item_ids:
                            changed_items.add(f"id_{item_id}")
                    else:
                        # ID가 없는 경우 Line-Time-Item 조합으로 키 생성
                        item_key = ItemKeyManager.get_item_key(
                            row['Line'], 
                            row['Time'], 
                            row['Item']
                        )
                        changed_items.add(f"key_{item_key}")
        
        # 5. 결과 정리
        result_df = merged.rename(columns={
            'Line': 'Line',
            'Time': 'Shift',
            'Item': 'Item',
            'Qty_prev': 'prev_plan',
            'Qty_curr': 'curr_plan'
        })
        
        # 6. 합계 및 유지율 계산
        prev_sum = result_df['prev_plan'].sum()
        maintenance_sum = result_df['maintenance'].sum()
        rate = (maintenance_sum / prev_sum) * 100 if prev_sum > 0 else 0
        
        # 7. Total 행 추가
        total_row = {
            'Line': 'Total',
            'Shift': '',
            'Item': '',
            'prev_plan': prev_sum,
            'curr_plan': result_df['curr_plan'].sum(),
            'maintenance': maintenance_sum
        }
        result_df = pd.concat([result_df, pd.DataFrame([total_row])], ignore_index=True)
        
        return result_df, rate, changed_items
    
    """
    RMC별 유지율 계산
    """
    @staticmethod
    def _calculate_rmc_maintenance(prev_df, curr_df):
        # RMC 컬럼이 없으면 빈 결과 반환
        if 'RMC' not in prev_df.columns or 'RMC' not in curr_df.columns:
            return pd.DataFrame(), 0.0, set()
        
        # 1. 그룹화
        prev_grouped = prev_df.groupby(['Line', 'Time', 'RMC'])['Qty'].sum().reset_index()
        curr_grouped = curr_df.groupby(['Line', 'Time', 'RMC'])['Qty'].sum().reset_index()
        
        # 2. 병합
        merged = pd.merge(
            prev_grouped, curr_grouped,
            on=['Line', 'Time', 'RMC'],
            how='outer',
            suffixes=('_prev', '_curr')
        )
        
        # NaN을 0으로 처리
        merged['Qty_prev'] = merged['Qty_prev'].fillna(0)
        merged['Qty_curr'] = merged['Qty_curr'].fillna(0)
        
        # 3. 유지 수량 계산
        merged['maintenance'] = merged.apply(
            lambda x: min(x['Qty_prev'], x['Qty_curr']) 
            if x['Qty_prev'] > 0 and x['Qty_curr'] > 0 else 0, 
            axis=1
        )
        
        # 4. 변경된 RMC 식별 (UI 표시용) - ID 기반으로만
        changed_rmcs = set()
        for _, row in merged.iterrows():
            if row['Qty_prev'] != row['Qty_curr']:
                # ID로 해당 RMC 찾기
                rmc_mask = (
                    (curr_df['Line'] == row['Line']) & 
                    (curr_df['Time'] == row['Time']) & 
                    (curr_df['RMC'] == row['RMC'])
                )
                if rmc_mask.any():
                    # ID가 있으면 ID 우선, 없으면 Line-Time-RMC 조합 사용
                    if '_id' in curr_df.columns:
                        rmc_ids = curr_df.loc[rmc_mask, '_id'].dropna().unique()
                        for rmc_id in rmc_ids:
                            changed_rmcs.add(f"id_{rmc_id}")
                    else:
                        # ID가 없는 경우 Line-Time-RMC 조합으로 키 생성
                        rmc_key = f"{row['Line']}_{row['Time']}_{row['RMC']}"
                        changed_rmcs.add(f"key_{rmc_key}")
        
        # 5. 결과 정리
        result_df = merged.rename(columns={
            'Line': 'Line',
            'Time': 'Shift',
            'RMC': 'RMC',
            'Qty_prev': 'prev_plan',
            'Qty_curr': 'curr_plan'
        })
        
        # 6. 합계 및 유지율 계산
        prev_sum = result_df['prev_plan'].sum()
        maintenance_sum = result_df['maintenance'].sum()
        rate = (maintenance_sum / prev_sum) * 100 if prev_sum > 0 else 0
        
        # 7. Total 행 추가
        total_row = {
            'Line': 'Total',
            'Shift': '',
            'RMC': '',
            'prev_plan': prev_sum,
            'curr_plan': result_df['curr_plan'].sum(),
            'maintenance': maintenance_sum
        }
        result_df = pd.concat([result_df, pd.DataFrame([total_row])], ignore_index=True)
        
        return result_df, rate, changed_rmcs


        
    