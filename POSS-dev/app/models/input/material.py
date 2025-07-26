import pandas as pd
import logging
from app.utils.fileHandler import load_file
from app.models.common.file_store import FilePaths, DataStore
from app.utils.error_handler import (
    error_handler, safe_operation, DataError, FileError
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""
자재와 수요 데이터 로드
"""
@error_handler(
        show_dialog=True,
        default_return=None
)
def process_material_data():
    try :
        material_file_path = FilePaths.get("dynamic_excel_file")

        if not material_file_path :
            raise FileError('Material file path not found', {'file_type' : 'dynamic_excel_file'})
    except Exception as e :
        raise FileError('Error getting material file path', {'error' : str(e)})
    
    dfs = DataStore.get("dataframes", {})
    key_mat = f"{material_file_path}:material_qty"

    try :
        if key_mat in dfs:
            df_material_qty = dfs[key_mat]
        else:
            df_material = load_file(material_file_path)
            df_material_qty = df_material.get('material_qty', pd.DataFrame())

        if df_material_qty.empty:
            return None
        
        processed_data = preprocess_material_data(df_material_qty)

        return processed_data
    except Exception as e :
        if not isinstance(e, (FileError, DataError)) :
            raise DataError(f'Unexpected error in process material data : {str(e)}')
        raise

"""
자재 만족률 분석을 위한 데이터 처리
"""
@error_handler(
        show_dialog=True,
        default_return={'error' : 'Error processing material satisfaction data'}
)
def process_material_satisfaction_data() :
    try :
        dynamic_file_path = FilePaths.get('dynamic_excel_file')
        demand_file_path = FilePaths.get('demand_excel_file')

        if not dynamic_file_path :
            return {'error' : 'Faild to load dynamic file'}
        
        if not demand_file_path :
            return {'error' : 'Failed to load demand file'}
    except Exception as e :
        return {'error' : f'Error getting file paths : {str(e)}'}
    
    dfs = DataStore.get("dataframes", {})
    key_qty  = f"{dynamic_file_path}:material_qty"
    key_item = f"{dynamic_file_path}:material_item"
    key_eq   = f"{dynamic_file_path}:material_equal"
    key_dem  = f"{demand_file_path}:demand"

    try :
        raw_dyn = None
        if not (key_qty in dfs and key_item in dfs and key_eq in dfs):
            raw_dyn = safe_operation(load_file, 'Error loading dynamic file', dynamic_file_path)
            
        raw_dem = None
        if key_dem not in dfs:
            raw_dem = safe_operation(load_file, 'Error loading demand file', demand_file_path)
            
        df_material_qty = dfs.get(key_qty,
                                   (raw_dyn or {}).get('material_qty', pd.DataFrame()))
        df_material_item = dfs.get(key_item,
                                   (raw_dyn or {}).get('material_item', pd.DataFrame()))
        df_material_eq = dfs.get(key_eq,
                                   (raw_dyn or {}).get('material_equal', pd.DataFrame()))
        df_demand_data = dfs.get(key_dem,
                                   (raw_dem or {}).get('demand', pd.DataFrame()))

        if df_demand_data.empty :
            return {'error' : 'Demand data not found in file'}

        if 'SOP' in df_demand_data.columns :
            df_demand_data['SOP'] = df_demand_data['SOP'].apply(
                lambda x : max(0, float(x)) if pd.notnull(x) else 0
            )

        if df_material_qty.empty :
            return {'error': 'Material quantity data not found in file'}
        
        if df_material_item.empty :
            return {'error': 'Material item data not found in file'}
        
        material_data = safe_operation(
            preprocess_material_data,
            'Error preprocessing material data',
            df_material_qty
        )

        if material_data is None :
            return {'error' : 'Failed to preprocess material data'}

        return {
            'material_df': material_data['material_df'],
            'material_item_df': df_material_item.copy(),
            'material_equal_df': df_material_eq if not df_material_eq.empty else None,
            'demand_df': df_demand_data,
            'date_columns': material_data['date_columns'],
            'weekly_columns': material_data['weekly_columns']
        }

    except Exception as e :
        return {'error' : f'Error loading and preprocessing data : {str(e)}'}
    
    
"""
자재 데이터 전처리 후 변환
"""
@error_handler(
        show_dialog=True,
        default_return=None
)
def preprocess_material_data(df_material_qty) :
    try :
        if 'Active_OX' not in df_material_qty.columns and isinstance(df_material_qty.iloc[0, 0], str) :
            column_names = df_material_qty.iloc[0].tolist()
            df_material_qty = df_material_qty.iloc[1:].reset_index(drop=True)
            df_material_qty.columns = column_names

        required_columns = ['Active_OX', 'Material', 'On-Hand']

        all_columns = list(df_material_qty.columns)

        if 'On-Hand' in all_columns :
            on_hand_index = all_columns.index('On-Hand')
            date_columns = all_columns[on_hand_index + 1:]
        else :
            date_columns = []
        
        required_columns.extend(date_columns)

        existing_columns = [col for col in required_columns if col in df_material_qty.columns]

        if not existing_columns :
            raise DataError('No required columns found in material data')
        
        df_filtered = df_material_qty[existing_columns].copy()

        numeric_columns = ['On-Hand'] + date_columns

        for col in numeric_columns :
            if col in df_filtered.columns :
                df_filtered[col] = df_filtered[col].apply(lambda x : safe_operation(
                    convert_to_numeric,
                    f'Error converting column {col} to numeric',
                    x
                ) or 0)

        weekly_columns = date_columns

        processed_data = {
            'material_df' : df_filtered,
            'date_columns' : date_columns,
            'weekly_columns' : weekly_columns
        }

        return processed_data
    
    except Exception as e :
        if not isinstance(e, DataError) :
            raise DataError(f'Unexpected error in preprocess material data : {str(e)}')
        raise

"""
값을 숫자로 변환하는 함수
"""
@error_handler(
        show_dialog=False,
        default_return=0
)
def convert_to_numeric(value) :
    if pd.isna(value) or value == '' :
        return 0
    
    if isinstance(value, str) :
        try :
            value = value.replace(',', '')
            return float(value)
        except ValueError :
            return 0
        except Exception as e :
            return 0
        
    return float(value) if value else 0
