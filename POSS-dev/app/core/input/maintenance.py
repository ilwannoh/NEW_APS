import pandas as pd
import numpy as np
from typing import List, Tuple
from app.models.input.maintenance import ItemMaintenance, RMCMaintenance, DataLoader
from app.models.common.file_store import DataStore, FilePaths
from app.utils.fileHandler import load_file

def melt_plan(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=['Line','Shift','Item','Qty'])
    
    records = []
    for _, row in df.iterrows():
        for day in range(1, 8):
            item = row[f'Item{day}']
            qty = row[f'Qty{day}']
            if pd.notna(item) and qty > 0:
                real_shift = (day - 1) * 2 + row['Shift']
                records.append({
                    'Line':  row['Line'],
                    'Shift': real_shift,
                    'Item':  item,
                    'Qty':   qty
                })
    return pd.DataFrame(records)

def get_threshold(
    line: str,
    shift: int,
    mode: str,
    key: Tuple[str, int, str] = None
) -> float:
    # 사용자 설정된 thresholds 검색
    if mode == 'item':
        item_map = DataStore.get('maintenance_thresholds_items', {})
        if key and key in item_map:
            return item_map[key]
    if mode == 'rmc':
        rmc_map = DataStore.get('maintenance_thresholds_rmcs', {})
        if key and key in rmc_map:
            return rmc_map[key]

        # 기본 fallback threshold
    return 0.8 if mode == 'item' else 0.9


def analyze_maintenance(
    prev_df: pd.DataFrame,
    new_df:  pd.DataFrame
) -> Tuple[List[ItemMaintenance], List[RMCMaintenance]]:

    df_prev = melt_plan(prev_df).rename(columns={'Qty':'prev_qty'})
    df_new  = melt_plan(new_df).rename(columns={'Qty':'new_qty'})
    df = (
        pd.merge(df_prev, df_new,
                 on=['Line','Shift','Item'], how='outer')
          .fillna(0)
    )
    df['maintain_qty'] = df[['prev_qty','new_qty']].min(axis=1)
    df['RMC'] = df['Item'].str[3:-7]

    items, rmcs = [], []

    for (line, shift, item), g in df.groupby(['Line','Shift','Item'], sort=False):
        prev_qty = g['prev_qty'].sum()
        new_qty  = g['new_qty'].sum()
        m_qty    = g['maintain_qty'].sum()
        m_rate   = (m_qty/prev_qty) if prev_qty > 0 else None
        thresh   = get_threshold(line, shift, 'item', (line, shift, item))
        below    = (m_rate is not None and m_rate < thresh)
        items.append(ItemMaintenance(
            line, shift, item,
            prev_qty, new_qty, m_qty,
            m_rate, thresh, below
        ))

    # RMCMaintenance 생성
    for (line, shift, rmc), g in df.groupby(['Line','Shift','RMC'], sort=False):
        prev_qty = g['prev_qty'].sum()
        new_qty  = g['new_qty'].sum()
        m_qty    = g['maintain_qty'].sum()
        m_rate   = (m_qty/prev_qty) if prev_qty > 0 else None
        thresh   = get_threshold(line, shift, 'rmc', (line, shift, rmc))
        below    = (m_rate is not None and m_rate < thresh)
        rmcs.append(RMCMaintenance(
            line, shift, rmc,
            prev_qty, new_qty, m_qty,
            m_rate, thresh, below
        ))
    return items, rmcs

def run_maintenance_analysis() -> Tuple[List[ItemMaintenance], List[RMCMaintenance]]:
    prev_df = DataLoader.load_dynamic_data()
    new_df  = DataLoader.load_pre_assign_data()

    items, rmcs = analyze_maintenance(prev_df, new_df)

    failed_items = [i for i in items if i.below_thresh]
    failed_rmcs  = [r for r in rmcs  if r.below_thresh]
    return failed_items, failed_rmcs

""" Item 계획 유지율 계산 함수"""
def calc_item_plan_retention(df_result: pd.DataFrame, df_demand: pd.DataFrame) -> float:
    """
    Parameter:
        df_result: result 시트 데이터프레임
        df_demand: demand 시트 데이터프레임
    Return: 
        int: item 계획 유지율 
    """
    df_demand_mfg = df_demand.groupby('Item')['MFG'].sum()
    df_result['Next MFG'] = 0
    for idx,row in df_result.iterrows():
        max_mfg = min(row['Qty'],df_demand_mfg[row['Item']])
        df_result.loc[idx,'Next MFG'] = max_mfg
        df_demand_mfg[row['Item']] -= max_mfg
    return df_result['Next MFG'].sum()/df_result['Qty'].sum()

""" RMC 계획 유지율 계산 함수"""
def calc_rmc_plan_retention(df_result: pd.DataFrame, df_demand: pd.DataFrame) -> float:
    """
    Parameter:
        df_result: result 시트 데이터프레임
        df_demand: demand 시트 데이터프레임
    Return: 
        int: RMC 계획 유지율 
    """
    df_demand['RMC'] = df_demand['Item'].str[3:11]
    df_demand_mfg = df_demand.groupby('RMC')['MFG'].sum()
    df_result['Next MFG'] = 0
    for idx,row in df_result.iterrows():
        rmc = row['Item'][3:11]
        max_mfg = min(row['Qty'],df_demand_mfg[rmc])
        df_result.loc[idx,'Next MFG'] = max_mfg
        df_demand_mfg[rmc] -= max_mfg
    return df_result['Next MFG'].sum()/df_result['Qty'].sum()

"""계획 유지율 계산 함수"""
def calc_plan_retention():
    """
    Parameter:
        df_result: result 시트 데이터프레임
        df_demand: demand 시트 데이터프레임
    Return: 
        (int,int,df): item 계획 유지율 , RMC 계획 유지율, result 데이터프레임
    """
    demand_path = FilePaths.get("demand_excel_file")
    result_path = FilePaths.get("result_file")
    if (not demand_path) or  (not result_path):
        return (None,None,None)
    demand_file = load_file(demand_path)
    df_demand = demand_file.get('demand', pd.DataFrame())
    df_result = pd.read_excel(result_path,sheet_name=0)
    sum_qty = df_result['Qty'].sum()

    df_demand_item_mfg = df_demand.groupby('Item')['MFG'].sum()
    df_result['Next item MFG'] = 0
    for idx,row in df_result.iterrows():
        if row['Item'] in df_demand_item_mfg.index:
            max_mfg = min(row['Qty'],df_demand_item_mfg[row['Item']])
            df_result.loc[idx,'Next item MFG'] = int(round(max_mfg))
            df_demand_item_mfg[row['Item']] -= int(round(max_mfg))

    sum_item_qty = df_result['Next item MFG'].sum()
    item_plan_retention = sum_item_qty/sum_qty

    df_demand['RMC'] = df_demand['Item'].str[3:11]
    df_demand_rmc_mfg = df_demand.groupby('RMC')['MFG'].sum()
    df_result['Next RMC MFG'] = 0
    for idx,row in df_result.iterrows():
        rmc = row['Item'][3:11]
        if rmc in df_demand_rmc_mfg.index:
            max_mfg = min(row['Qty'],df_demand_rmc_mfg[rmc])
            df_result.loc[idx,'Next RMC MFG'] = int(round(max_mfg))
            df_demand_rmc_mfg[rmc] -= int(round(max_mfg))

    sum_rmc_qty = df_result['Next RMC MFG'].sum()
    rmc_plan_retention = sum_rmc_qty/sum_qty

    df_result = df_result[['Line','Time','RMC','Item','Qty','Next item MFG','Next RMC MFG']]
    df_result.columns = ['Line','Time','RMC','Item','Previous Qty','Max Item Qty','Max RMC Qty']
    df_result = df_result.sort_values(by=['Line','Time','RMC','Previous Qty'],ascending=[True,True,True,False])
    df_result.loc[len(df_result)] = ['total','','','',sum_qty,sum_item_qty,sum_rmc_qty]

    return (item_plan_retention * 100, rmc_plan_retention * 100, df_result)