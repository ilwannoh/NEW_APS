import pandas as pd
from app.models.common.file_store import FilePaths, DataStore
from app.utils.fileHandler import load_file
from app.utils.error_handler import (
    error_handler, safe_operation,
    DataError, FileError
)

"""
당주 출하 만족률 계산을 위한 전처리
"""
@error_handler(
    show_dialog=True,
    default_return=None
)
def preprocess_data_for_fulfillment_rate() :
    try :
        master_file_path = FilePaths.get('master_excel_file')
        material_file_path = FilePaths.get('dynamic_excel_file')
        demand_file_path = FilePaths.get('demand_excel_file')

        if not master_file_path:
            raise FileError('Master file path not found', {'file_type' : 'master_excel_file'})
        
        if not material_file_path:
            raise FileError('Material file path not found', {'file_type' : 'dynamic_excel_file'})
        
        if not demand_file_path:
            raise FileError('Demand file path not found', {'file_type' : 'demand_excel_file'})
            

        dfs = DataStore.get("dataframes", {})
        key_due = f"{master_file_path}:due_LT"
        key_line = f"{master_file_path}:line_available"
        key_cap = f"{master_file_path}:capa_qty"
        key_matq = f"{material_file_path}:material_qty"
        key_mati = f"{material_file_path}:material_item"
        key_mate = f"{material_file_path}:material_equal"
        key_dem = f"{demand_file_path}:demand"

        raw_master = None
        if not (key_due in dfs and key_line in dfs and key_cap in dfs):
            raw_master = safe_operation(load_file, 'Error loading master file', master_file_path)

        raw_mat = None
        if not (key_matq in dfs and key_mati in dfs and key_mate in dfs):
            raw_mat = safe_operation(load_file, 'Error loading material file', material_file_path)

        raw_dem = None
        if key_dem not in dfs:
            raw_dem = safe_operation(load_file, 'Error loading demand file', demand_file_path)

        df_demand = dfs.get(key_dem, (raw_dem or {}).get('demand', pd.DataFrame()))
        df_due_lt = dfs.get(key_due, (raw_master or {}).get('due_LT', pd.DataFrame()))
        df_line_available = dfs.get(key_line, (raw_master or {}).get('line_available', pd.DataFrame()))
        df_capa_qty = dfs.get(key_cap, (raw_master or {}).get('capa_qty', pd.DataFrame()))
        df_material_qty = dfs.get(key_matq, (raw_mat or {}).get('material_qty', pd.DataFrame()))
        df_material_item = dfs.get(key_mati, (raw_mat or {}).get('material_item', pd.DataFrame()))
        df_material_equal = dfs.get(key_mate, (raw_mat or {}).get('material_equal', pd.DataFrame()))

        if any(df.empty for df in [df_demand, df_due_lt, df_line_available, df_capa_qty,
                                   df_material_qty, df_material_item]) :
            return None
        
        try :
            for i, row in df_demand.iterrows() :
                if 'Item' not in row or not isinstance(row['Item'], str) :
                    continue

                df_demand.loc[i, 'Project'] = row['Item'][3:7]
                df_demand.loc[i, "Basic2"] = row['Item'][3:8]
                df_demand.loc[i, "Tosite_group"] = row['Item'][7:8]
                df_demand.loc[i, "RMC"] = row['Item'][3:-3]
                df_demand.loc[i, "Color"] = row['Item'][8:-4]
        except Exception as e :
            raise DataError('Error processing demand items', {'error' : str(e)})

        if 'SOP' in df_demand.columns :
            try :
                df_demand['SOP'] = df_demand['SOP'].apply(lambda x : max(0, x if pd.notna(x) else 0))
            except Exception as e :
                raise DataError('Error processing SOP column', {'error' : str(e)})
        
        try :
            processed_data = {
                'demand' : {
                    'df' : df_demand,
                    'items' : df_demand.to_dict('records'),
                    'project_items' : {proj : group.to_dict('records')
                                    for proj, group in df_demand.groupby('Project')},
                    'site_items' : {site : group.to_dict('records')
                                    for site, group in df_demand.groupby('Tosite_group')
                                    if site and not pd.isna(site)}
                },
                'material' : safe_operation(
                    process_material,
                    'Error processing material data',
                    df_material_qty, df_material_item, df_material_equal
                ),
                'production': safe_operation(
                    process_production, 
                    "Error processing production data",
                    df_line_available, df_capa_qty
                ),
                'due_lt': safe_operation(
                    process_due_lt, 
                    "Error processing due LT data",
                    df_due_lt
                )
            }

            if any(v is None for k, v in processed_data.items() if k != 'material_equal') :
                raise DataError('One or more data processing steps failed')
            
            return processed_data
        except Exception as e :
            raise DataError('Error in final data processing', {'error' : str(e)})
    except Exception as e :
        if not isinstance(e, (FileError, DataError)) :
            raise DataError('Unexpected error in preprocess data for fulfillment rate', {'error' : str(e)})
        raise

"""
자재 관련 데이터 처리
"""
@error_handler(
    show_dialog=True,
    default_return=None
)
def process_material(df_material_qty, df_material_item, df_material_equal) :
    try :
        if 'Active_OX' not in df_material_qty.columns :
            raise DataError('Active_OX column missing in material quantity data')
        
        active_materials_qty = df_material_qty[df_material_qty['Active_OX'] == 'O'].copy()

        if 'Active_OX' not in df_material_item.columns :
            raise DataError('Active_OX column missing in material item data')

        active_materials_item = df_material_item[df_material_item['Active_OX'] == 'O'].copy()

        material_availability = {}

        for _, row in active_materials_qty.iterrows() :
            try :
                material = row['Material']
                on_hand = row['On-Hand'] if pd.notna(row['On-Hand']) else 0
                available_lt = row.get('Available L/T', 0) if pd.notna(row.get('Available L/T', 0)) else 0

                material_availability[material] = {
                    'on_hand' : on_hand,
                    'available_lt' : available_lt
                }
            except Exception as e :
                continue

        material_groups = {}

        if not df_material_equal.empty :
            for _, row in df_material_equal.iterrows() :
                try :
                    group = []

                    for col in ['Material A', 'Material B', 'Material C'] :
                        if col in row and pd.notna(row[col]) and row[col] :
                            group.append(row[col])

                    if group :
                        for material in group :
                            material_groups[material] = group
                except Exception as e :
                    continue

        material_to_models = {}
        model_to_materials = {}

        for _, row in active_materials_item.iterrows() :
            try :
                if 'Material' not in row :
                    continue

                material = row['Material']
                material_to_models[material] = []

                for i in range(1, 11) :
                    col_name = f'Top_Model_{i}'

                    if col_name in row and pd.notna(row[col_name]) and row[col_name] :
                        pattern = row[col_name]
                        material_to_models[material].append(pattern)

                        if pattern not in model_to_materials :
                            model_to_materials[pattern] = []
                        
                        model_to_materials[pattern].append(material)
            except Exception as e :
                continue

        return {
            'availability' : material_availability,
            'material_groups' : material_groups,
            'material_to_models' : material_to_models,
            'model_to_materials' : model_to_materials,
            'df_qty' : active_materials_qty,
            'df_item' : active_materials_item
        }
    except Exception as e :
        if not isinstance(e, DataError) :
            raise DataError('Unexpected error in process_material', {'error' : str(e)})
        raise

"""
생산 관련 데이터 처리
"""
@error_handler(
    show_dialog=True,
    default_return=None
)
def process_production(df_line_available, df_capa_qty) :
    try :
        project_lines = {}

        if 'Project' in df_line_available.columns :
            for _, row in df_line_available.iterrows() :
                try :
                    project = str(row['Project'])
                    available_lines = []

                    for col in df_line_available.columns :
                        if col != 'Project' and pd.notna(row[col]) and row[col] > 0 :
                            available_lines.append(col)

                    project_lines[project] = available_lines
                except Exception as e :
                    continue

        line_capacities = {}

        try :
            df_capa_qty_processed = df_capa_qty.copy()

            if 'Line' in df_capa_qty_processed.columns :
                df_capa_qty_processed = df_capa_qty_processed.set_index('Line')

            meta_prefixes = ['Max_', 'Total_', 'Sum_']
            filtered_capa_qty = df_capa_qty_processed[~df_capa_qty_processed.index.astype(str).str.startswith(tuple(meta_prefixes))]

            shift_columns = [col for col in filtered_capa_qty.columns if isinstance(col, int) or (isinstance(col, str) and col.isdigit())]

            for line, row in filtered_capa_qty.iterrows() :
                try :
                    line_str = str(line)
                    capacities = {}

                    for shift in range(1, 15) :
                        capacity = 0

                        if shift in shift_columns :
                            capacity = row[shift] if pd.notna(row[shift]) else 0

                        capacities[shift] = float(capacity) if pd.notna(capacity) else 0

                    line_capacities[line_str] = capacities
                except Exception as e :
                    continue
        except Exception as e :
            pass
        
        return {
            'project_lines' : project_lines,
            'line_capacities': line_capacities,
            'df_line_available': df_line_available,
            'df_capa_qty': df_capa_qty
        }
    except Exception as e :
        if not isinstance(e, DataError) :
            raise DataError('Unexpected error in process_production', {'error' : str(e)})
        raise

"""
납기 정보 처리
"""
@error_handler(
    show_dialog=True,
    default_return=None
)
def process_due_lt(df_due_lt) :
    try :
        due_lt_map = {}

        for _, row in df_due_lt.iterrows() :
            try :
                project = row['Project']
                tosite_group = row['Tosite_group']
                due_lt = row['Due_date_LT']

                if project not in due_lt_map :
                    due_lt_map[project] = {}

                due_lt_map[project][tosite_group] = due_lt
            except Exception as e :
                continue

        return {
            'df' : df_due_lt,
            'due_lt_map' : due_lt_map
        }
    except Exception as e :
        if not isinstance(e, DataError) :
            raise DataError('Unexpected error in process_due_lt', {'error' : str(e)})
        raise