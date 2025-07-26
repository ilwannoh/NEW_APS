import pandas as pd
from app.utils.fileHandler import load_file
from app.models.common.file_store import FilePaths, DataStore
from dataclasses import dataclass
from typing import Tuple

class DataLoader:
    @staticmethod
    def load_dynamic_data() -> pd.DataFrame:
        """
        dynamic_excel_file에서 'pre_assign' 시트를 로드
        """
        path = FilePaths.get("dynamic_excel_file")
        if not path:
            return pd.DataFrame()
        
        key = f"{path}:pre_assign"
        dfs = DataStore.get("dataframes", {})
        if key in dfs:
            return dfs[key]

        raw = load_file(path)
        return raw.get('pre_assign', pd.DataFrame())

    @staticmethod
    def load_pre_assign_data() -> pd.DataFrame:
        """
        pre_assign_excel_file을 로드
        """
        path = FilePaths.get("pre_assign_excel_file")
        if not path:
            return pd.DataFrame()
        
        key = f"{path}:pre_assign"
        dfs = DataStore.get("dataframes", {})
        if key in dfs:
            return dfs[key]

        raw = load_file(path)
        return raw.get('pre_assign', pd.DataFrame())

@dataclass
class ItemMaintenance:
    line: str
    shift: int
    item: str
    prev_qty: float
    new_qty: float
    maintain_qty: float
    maint_rate: float | None
    threshold: float
    below_thresh: bool

@dataclass
class RMCMaintenance:
    line: str
    shift: int
    rmc: str
    prev_qty: float
    new_qty: float
    maintain_qty: float
    maint_rate: float | None
    threshold: float
    below_thresh: bool