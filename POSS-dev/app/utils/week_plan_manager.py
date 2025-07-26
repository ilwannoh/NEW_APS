import os
import json
import pandas as pd
from datetime import datetime
from PyQt5.QtCore import QDate

"""
주차 정보 관리 클래스
사용자가 선택한 날짜를 기반으로 주차를 계산하고 파일명과 메타데이터에 포함
"""
class WeeklyPlanManager:

    """
    WeeklyPlanManager 초기화
    
    Parameters:
            output_dir (str): 결과 저장 디렉토리
    """
    def __init__(self, output_dir="data/export"):

        self.output_dir = output_dir
        self.registry_file = os.path.join("data", "plan_registry.json")

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)

        self.registry = self._load_registry()

    """
    레지스트리 로드
    """
    def _load_registry(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except:
                return {"plans" : []}
            
        else:
            return {"plans" : []}
        
    """
    레지스트리 저장
    """
    def _save_registry(self):
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    """
    선택한 날짜로부터 주차 정보 계산

    Parameters:
        start_date (QDate 또는 datetime): 사용자가 선택한 시작일
        end_date (QDate 또는 datetime): 사용자가 선택한 종료일
    Returns:
        tuple: (week_info, week_start, week_end) - 주차 정보 문자열과 주 시작/종료일
    """
    def get_week_info(self, start_date, end_date):
        if isinstance(start_date, QDate):
            week_start = start_date.toPyDate()
        else:
            week_start = start_date.date() if hasattr(start_date, 'date') else start_date

        if isinstance(end_date, QDate):
            week_end = end_date.toPyDate() 
        else:
            week_end = end_date.date() if hasattr(end_date, 'date') else end_date

        # 해당 월의 주차 정보 생성
        month = week_start.month
        first_day_of_month = datetime(week_start.year, month, 1).date()  # 해당 월의 첫째 날(예: 5월 1일)
        day_of_month = (week_start - first_day_of_month).days + 1 # 시작일이 몇 번째 날인지 계산(예: 5월 15일 -> 15번쨰)
        week_of_month = (day_of_month -1) // 7 + 1  # 몇 번째 주인지 계산

        week_info = f"W{month:02d}{week_of_month:01d}"  # 예: W021(2월 1주차)

        return week_info, week_start, week_end
    
    """
    계획 등록
    """
    def register_plan(self, file_path, week_info, start_date, end_date):
        plan_info = {
            "path" :file_path,
            "week" : week_info,
            "start_date": start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else start_date,
            "end_date": end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else end_date,
            "mod_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.registry["plans"].append(plan_info)
        self._save_registry()
    
    """
    계획 데이터 저장 및 메타데이터 추가

    Parameters:
        plan_df (DataFrame): 계획 데이터
        start_date (QDate): 사용자가 선택한 시작일
        end_date (QDate): 사용자가 선택한 종료일
        previous_plan (str): 이전 계획 파일 경로 (있는 경우)
    Returns:
        str: 저장된 파일 경로
    """
    def save_plan_with_metadata(self, plan_df, start_date, end_date, previous_plan=None):
        week_info, week_start, week_end = self.get_week_info(start_date, end_date)

        # 현재 날짜 및 시간
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")

        week_folder = os.path.join(self.output_dir, week_info)
        os.makedirs(week_folder, exist_ok=True)

        file_name = f"Plan_{week_info}_{date_str}_{time_str}.xlsx"
        file_path = os.path.join(week_folder, file_name)

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            plan_df.to_excel(writer, sheet_name='result', index=False)

            metadata = {
                '속성': [
                    'week_info',
                    'week_start',
                    'week_end',
                    'mod_time',
                    'result_type',
                    'prev_result'
                ],
                '값': [
                    week_info,
                    week_start.strftime("%Y-%m-%d"),
                    week_end.strftime("%Y-%m-%d"),
                    now.strftime("%Y-%m-%d %H:%M:%S"),
                    "Modified Plan" if previous_plan else "Initial Plan",
                    os.path.basename(previous_plan) if previous_plan else "Unknown"
                ]
            }

            metadata_df = pd.DataFrame(metadata)
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)

        self.register_plan(file_path, week_info, week_start, week_end)

        return file_path