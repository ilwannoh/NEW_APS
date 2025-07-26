"""
파일 입출력 유틸리티
Excel 파일 읽기/쓰기 기능 제공
"""
import pandas as pd
import os
from typing import Dict, Optional
import openpyxl
from datetime import datetime


class FileHandler:
    """파일 처리 클래스"""
    
    @staticmethod
    def read_excel(file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Excel 파일 읽기"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        try:
            if sheet_name:
                return pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                # 첫 번째 시트 읽기
                return pd.read_excel(file_path)
        except Exception as e:
            raise Exception(f"Excel 파일 읽기 오류: {str(e)}")
    
    @staticmethod
    def read_all_sheets(file_path: str) -> Dict[str, pd.DataFrame]:
        """Excel 파일의 모든 시트 읽기"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        try:
            # 모든 시트를 딕셔너리로 읽기
            return pd.read_excel(file_path, sheet_name=None)
        except Exception as e:
            raise Exception(f"Excel 파일 읽기 오류: {str(e)}")
    
    @staticmethod
    def write_excel(df: pd.DataFrame, file_path: str, sheet_name: str = 'Sheet1'):
        """DataFrame을 Excel 파일로 저장"""
        try:
            # 디렉토리가 없으면 생성
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            # Excel 파일로 저장
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        except Exception as e:
            raise Exception(f"Excel 파일 쓰기 오류: {str(e)}")
    
    @staticmethod
    def write_multiple_sheets(data_dict: Dict[str, pd.DataFrame], file_path: str):
        """여러 시트를 하나의 Excel 파일로 저장"""
        try:
            # 디렉토리가 없으면 생성
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            # 여러 시트 저장
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in data_dict.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        except Exception as e:
            raise Exception(f"Excel 파일 쓰기 오류: {str(e)}")
    
    @staticmethod
    def read_csv(file_path: str, encoding: str = 'utf-8-sig') -> pd.DataFrame:
        """CSV 파일 읽기"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except Exception as e:
            raise Exception(f"CSV 파일 읽기 오류: {str(e)}")
    
    @staticmethod
    def write_csv(df: pd.DataFrame, file_path: str, encoding: str = 'utf-8-sig'):
        """DataFrame을 CSV 파일로 저장"""
        try:
            # 디렉토리가 없으면 생성
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            # CSV 파일로 저장
            df.to_csv(file_path, index=False, encoding=encoding)
        except Exception as e:
            raise Exception(f"CSV 파일 쓰기 오류: {str(e)}")
    
    @staticmethod
    def validate_sales_plan(file_path: str) -> bool:
        """판매계획 파일 유효성 검사"""
        try:
            df = FileHandler.read_excel(file_path)
            
            # 새로운 형식 확인 (제품코드, 제품명, 제조번호, 수량, 납기일, 우선순위)
            new_format_columns = ['제품코드', '제품명', '제조번호', '수량', '납기일']
            has_new_format = all(col in df.columns for col in new_format_columns)
            
            if has_new_format:
                return True
            
            # 기존 형식 확인 (제품명, 월별 컬럼)
            old_format_columns = ['제품명']
            month_columns = [f'{i}월' for i in range(1, 13)]
            has_old_format = ('제품명' in df.columns and 
                            any(col in df.columns for col in month_columns))
            
            return has_old_format
        except:
            return False
    
    @staticmethod
    def validate_existing_plan(file_path: str) -> bool:
        """기존 생산계획 파일 유효성 검사"""
        try:
            df = FileHandler.read_excel(file_path)
            
            # 필수 컬럼 확인
            required_columns = ['장비', '날짜', '제품', '배치']
            for col in required_columns:
                if col not in df.columns:
                    return False
            
            return True
        except:
            return False
    
    @staticmethod
    def create_sample_files(output_dir: str):
        """샘플 파일 생성"""
        # 판매계획 샘플
        sales_plan = pd.DataFrame({
            '제품명': ['제품A', '제품B', '제품C'],
            '1월': [100, 80, 60],
            '2월': [110, 85, 65],
            '3월': [120, 90, 70],
            '4월': [115, 88, 68],
            '5월': [125, 95, 75],
            '6월': [130, 100, 80]
        })
        
        FileHandler.write_excel(
            sales_plan, 
            os.path.join(output_dir, 'sample_sales_plan.xlsx'),
            '판매계획'
        )
        
        # 마스터 데이터 샘플
        products = pd.DataFrame({
            '제품ID': ['P001', 'P002', 'P003'],
            '제품명': ['제품A', '제품B', '제품C'],
            '우선순위': [1, 2, 3],
            '리드타임(시간)': [16, 24, 20]
        })
        
        processes = pd.DataFrame({
            '공정ID': ['PR01', 'PR02', 'PR03', 'PR04', 'PR05', 'PR06'],
            '공정명': ['계량', '혼합', '타정', '코팅', '선별', '포장'],
            '순서': [1, 2, 3, 4, 5, 6]
        })
        
        equipment = pd.DataFrame({
            '장비ID': ['EQ001', 'EQ002', 'EQ003', 'EQ004'],
            '장비명': ['계량기1', '혼합기1', '타정기1', '코팅기1'],
            '공정ID': ['PR01', 'PR02', 'PR03', 'PR04'],
            '세척필요': [False, True, True, True]
        })
        
        master_data = {
            '제품': products,
            '공정': processes,
            '장비': equipment
        }
        
        FileHandler.write_multiple_sheets(
            master_data,
            os.path.join(output_dir, 'sample_master_data.xlsx')
        )