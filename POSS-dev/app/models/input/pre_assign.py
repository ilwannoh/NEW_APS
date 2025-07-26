import pandas as pd
import numpy as np
from app.utils.fileHandler import load_file
from app.models.common.file_store import FilePaths, DataStore
from dataclasses import dataclass
from typing import Any, List, Tuple, Dict


class DataLoader:
    @staticmethod
    def load_dynamic_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        dynamic_excel_file에서 'fixed_option' 및 'pre_assign' 시트를 로드
        """
        path = FilePaths.get("dynamic_excel_file")
        if not path:
            return pd.DataFrame(), pd.DataFrame()
        
        dfs = DataStore.get("dataframes", {})
        fixed_key = f"{path}:fixed_option"
        pre_key = f"{path}:pre_assign"

        raw = None
        if not (fixed_key in dfs and pre_key in dfs):
            raw = load_file(path)

        fixed_opt = dfs.get(
            fixed_key,
            raw.get('fixed_option', pd.DataFrame()) if raw is not None else pd.DataFrame()
        )
        pre_assign = dfs.get(
            pre_key,
            raw.get('pre_assign', pd.DataFrame())   if raw is not None else pd.DataFrame()
        )

        fixed_opt['Fixed_Time'] = fixed_opt['Fixed_Time'].apply(
            lambda x: str(x) if pd.notna(x) else np.nan
        )
        return fixed_opt, pre_assign

    @staticmethod
    def load_demand_data() -> pd.DataFrame:
        """
        demand_excel_file에서 'demand' 시트를 로드
        """
        path = FilePaths.get("demand_excel_file")
        if not path:
            return pd.DataFrame()
        
        dfs = DataStore.get("dataframes", {})
        key = f"{path}:demand"
        if key in dfs:
            return dfs.get(key, pd.DataFrame())
        raw = load_file(path)
        return raw.get('demand', pd.DataFrame())

    @staticmethod
    def load_master_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        dynamic_excel_file에서 'line_available', 'capa_qty' 시트를 로드
        """
        path = FilePaths.get("master_excel_file")
        if not path:
            return pd.DataFrame(), pd.DataFrame()
        
        dfs = DataStore.get("dataframes", {})
        line_key = f"{path}:line_available"
        cap_key = f"{path}:capa_qty"

        raw = None
        if not (line_key in dfs and cap_key in dfs):
            raw = load_file(path)

        line_avail = dfs.get(
            line_key,
            raw.get('line_available', pd.DataFrame()) if raw is not None else pd.DataFrame()
        )
        capa_qty = dfs.get(
            cap_key,
            raw.get('capa_qty', pd.DataFrame()) if raw is not None else pd.DataFrame()
        )
        return line_avail, capa_qty

# 할당 결과 모델
PreAssignFailures = Dict[str, List[Dict[str, Any]]]