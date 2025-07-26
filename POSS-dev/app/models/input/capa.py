import pandas as pd
from app.utils.fileHandler import load_file
from app.models.common.file_store import FilePaths, DataStore
from app.utils.error_handler import (
    error_handler, safe_operation, DataError, FileError
)

@error_handler(
        show_dialog=True,
        default_return=None
)
def process_data():
    try :
        master_file_path = FilePaths.get("master_excel_file")
        dynamic_file_path = FilePaths.get("dynamic_excel_file")
        demand_file_path = FilePaths.get("demand_excel_file")
        etc_file_path = FilePaths.get("etc_excel_file")
    except Exception as e :
        raise FileError('Error getting file path', {'error' : str(e)})
    
    dfs = DataStore.get("dataframes", {})

    if demand_file_path:
        try :
            key_d = f"{demand_file_path}:demand"
            if key_d in dfs:
                df_demand_demand = dfs[key_d]
            else:
                df_demand = safe_operation(load_file, "Error loading demand file", demand_file_path)
                if df_demand is None :
                    raise FileError('Unable to load demand file', {'file_path' : demand_file_path})
                df_demand_demand = df_demand.get('demand', pd.DataFrame())

            if df_demand_demand.empty :
                raise DataError('The demand data sheet is empty or not found')

            for i, row in df_demand_demand.iterrows():
                df_demand_demand.loc[i, "Project"] = row['Item'][3:7]
                df_demand_demand.loc[i, "Basic2"] = row['Item'][3:8]
                df_demand_demand.loc[i, "Tosite_group"] = row['Item'][7:8]
                df_demand_demand.loc[i, "RMC"] = row['Item'][3:-3]
                df_demand_demand.loc[i, "Color"] = row['Item'][8:-4]
        except Exception as e :
            if not isinstance(e, (FileError, DataError)) :
                raise DataError('An error occurred while processing demand data', {'error' : str(e)})

    if dynamic_file_path:
        df_dynamic = safe_operation(load_file, 'Error loading dynamic files', dynamic_file_path)

    if master_file_path:
        try :
            key_la = f"{master_file_path}:line_available"
            key_cp = f"{master_file_path}:capa_portion"
            key_cq = f"{master_file_path}:capa_qty"

            raw_master = None
            if not (key_la in dfs and key_cp in dfs and key_cq in dfs):
                raw_master = safe_operation(load_file, 'Error loading master file', master_file_path)
                if raw_master is None:
                    raise FileError('Unable to load master file', {'file_path': master_file_path})

            df_master_line_available = dfs.get(
                key_la,
                raw_master.get('line_available', pd.DataFrame()) if raw_master else pd.DataFrame()
            )
            df_master_capa_portion = dfs.get(
                key_cp,
                raw_master.get('capa_portion', pd.DataFrame()) if raw_master else pd.DataFrame()
            )
            df_master_capa_qty = dfs.get(
                key_cq,
                raw_master.get('capa_qty', pd.DataFrame()) if raw_master else pd.DataFrame()
            )

            if demand_file_path:
                time = {i for i in df_master_capa_qty.columns}
                line = df_master_line_available.columns
                item = df_demand_demand.index.tolist()
                project = df_demand_demand["Basic2"].unique()

        except Exception as e :
            if not isinstance(e, FileError) :
                raise DataError('An error occurred while processing master data', {'error' : str(e)})
            raise

    if etc_file_path:
        df_etc = safe_operation(load_file, 'Error loading other files', etc_file_path)

    if (demand_file_path and master_file_path
        and not df_demand_demand.empty and not df_master_line_available.empty
        and not df_master_capa_qty.empty and not df_master_capa_portion.empty) :

        try :
            processed_data = safe_operation(
                preprocess_data,
                'Error during data preprocessing',
                df_demand_demand, df_master_line_available, df_master_capa_qty, df_master_capa_portion
            )

            if processed_data is None :
                raise DataError('Data preprocessing failed')

            return processed_data
        except Exception as e :
            if not isinstance(e, DataError) :
                raise DataError('Error during data preprocessing', {'error' : str(e)})
            raise
    else :
        missing_data = []

        if not demand_file_path or df_demand_demand.empty :
            missing_data.append('demand data')
        if not master_file_path or df_master_line_available.empty :
            missing_data.append('line available data')
        if not master_file_path or df_master_capa_qty.empty :
            missing_data.append('capa qty data')
        if not master_file_path or df_master_capa_portion.empty :
            missing_data.append('capa portion data')
            
        raise DataError('A required data file or sheet is missing', {'missing_data' : missing_data})
    
    
"""
이상치 분석을 위한 데이터 전처리
"""
@error_handler(
        show_dialog=True,
        default_return=None
)
def preprocess_data(df_demand, df_line_available, df_capa_qty, df_capa_portion):
    processed_data = {
        'demand_items': [],
        'project_to_buildings': {},
        'line_capacities': {},
        'building_constraints': {},
        'line_available_df': df_line_available,
        'capa_qty_df': df_capa_qty
    }

    try :
        buildings = []

        if not df_capa_portion.empty:
            if 'name' in df_capa_portion.columns:
                buildings = df_capa_portion['name'].tolist()
            else:
                buildings = [col for col in df_capa_portion.columns if col != 'name']
    except Exception as e :
        raise DataError('Error occurred while extracting building information', {'error' : str(e)})

    try :
        for _, row in df_demand.iterrows():
            item = row.to_dict()
            processed_data['demand_items'].append(item)
    except Exception as e :
        raise DataError('An error occurred while processing the demand item', {'error' : str(e)})

    try :
        for _, row in df_line_available.iterrows() :
            project = row['Project'] if 'Project' in row else row.name
            project_buildings = []

            for building in buildings :
                building_columns = [col for col in row.index if col.startswith(f"{building}_")]

                if any(row[col] == 1 for col in building_columns if pd.notna(row[col])) :
                    project_buildings.append(building)

            if 'Basic2' in df_demand.columns :
                for basic2 in df_demand['Basic2'].unique() :
                    if basic2.startswith(project) :
                        processed_data['project_to_buildings'][basic2] = project_buildings

            else :
                processed_data['project_to_buildings'][project] = project_buildings
    except Exception as e :
        raise DataError('Error occurred while mapping project-building', {'error' : str(e)})
 
    try :
        for _, row in df_capa_qty.iterrows() :
            if 'Line' in row and 'Capacity' in row :
                line_id = row['Line']
                capacity = row['Capacity']
                processed_data['line_capacities'][line_id] = capacity
    except Exception as e :
        raise DataError('Error occurred while processing line capacity', {'error' : str(e)})

    try :
        for _, row in df_capa_portion.iterrows() :
            if 'name' in row and 'lower_limit' in row and 'upper_limit' in row :
                building = row['name']
                processed_data['building_constraints'][building] = {
                    'lower_limit' : float(row['lower_limit']),
                    'upper_limit' : float(row['upper_limit'])
                }
    except Exception as e :
        raise DataError('Error occurred while processing manufacturing constraints', {'error' : str(e)})

    return processed_data