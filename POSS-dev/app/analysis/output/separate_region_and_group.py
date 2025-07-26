import pandas as pd
import numpy as np
import re
from collections import defaultdict
from app.models.common.file_store import FilePaths, DataStore

def extract_region_from_item(item, project):
    """
    Item 문자열에서 지역 정보를 추출합니다.
    AB-P495W5ZJ825U5 같은 문자열에서 프로젝트 코드(P495) 바로 다음 문자(W)를 추출합니다.
    
    Args:
        item (str): item 문자열
        project (str): 프로젝트 식별자
    
    Returns:
        str: 추출된 지역 코드 또는 빈 문자열(추출 실패 시)
    """
    try:
        # 수요 문자열에서 프로젝트 코드 위치 찾기
        project_index = item.find(project)
        if project_index >= 0:
            # 프로젝트 코드 바로 다음 문자 추출
            region_index = project_index + len(project)
            if region_index < len(item):
                region = item[region_index]
                # 대문자만 유효한 지역 코드로 간주
                if region.isupper() and region.isalpha():
                    return region
        return ""
    except:
        return ""

def analyze_line_allocation(result_df=None, only_split=True):
    """
    프로젝트와 모델이 다양한 라인에 어떻게 할당되었는지 분석합니다.
    
    Args:
        result_df (DataFrame): 분석할 결과 데이터프레임. None이면 DataStore에서 가져옴
        only_split (bool): True일 경우 여러 라인에 분산된 항목만 반환
    
    Returns:
        tuple: (원본 데이터프레임, 프로젝트 분석 데이터프레임, 모델 분석 데이터프레임)
    """
    try:
        # 결과 파일 로드 (우선순위: 인자 > DataStore > FilePaths)
        if result_df is None:
            # DataStore에서 먼저 확인
            result_df = DataStore.get("result_dataframe")
            
            # DataStore에 없으면 FilePaths에서 파일 경로 확인
            if result_df is None:
                result_file_path = FilePaths.get("result_file")
                if result_file_path:
                    try:
                        result_df = pd.read_excel(result_file_path)
                        print(f"결과 파일 로드: {result_file_path}")
                    except Exception as e:
                        print(f"결과 파일 로드 실패: {e}")
                        return None, None, None
                else:
                    print("결과 파일 경로를 찾을 수 없습니다.")
                    return None, None, None
        
        if result_df is None or result_df.empty:
            print("분석할 결과 데이터가 없습니다.")
            return None, None, None
        
        # print(f"결과 파일의 총 레코드: {len(result_df)}")
        # print(f"고유 라인 수: {result_df['Line'].nunique()}")
        # print(f"고유 프로젝트 수: {result_df['Project'].nunique()}")
        # print(f"고유 모델(Item) 수: {result_df['Item'].nunique()}")
        
        # 올바른 방법으로 Item에서 지역 추출
        result_df['Region'] = result_df.apply(
            lambda row: extract_region_from_item(str(row['Item']), str(row['Project'])), 
            axis=1
        )
        
        # 1. 프로젝트 & 지역별 라인 할당 분석
        # 프로젝트 + 지역 그룹화
        project_region_groups = defaultdict(lambda: {'records': [], 'lines': set(), 'models': set(), 'qty': 0})
        
        for _, row in result_df.iterrows():
            project = row['Project'] + row['Region']
            region = row['Region']
            line = row['Line']
            item = row['Item']
            qty = row['Qty']
            
            # 지역 정보가 없으면 건너뛰기
            if not region:
                continue
                
            # 프로젝트 & 지역별 그룹화
            project_key = f"{project}_{region}"
            project_region_groups[project_key]['records'].append(row)
            project_region_groups[project_key]['lines'].add(line)
            project_region_groups[project_key]['models'].add(item)
            project_region_groups[project_key]['qty'] += qty
        
        # 프로젝트 분석 데이터 생성
        project_analysis = []
        for project_key, data in project_region_groups.items():
            project, region = project_key.split('_', 1)
            lines = data['lines']
            line_count = len(lines)
            is_split = line_count > 1
            
            # only_split이 True이고 분할되지 않은 경우 건너뛰기
            if only_split and not is_split:
                continue
                
            project_analysis.append({
                'Project': project,
                'Region': region,
                'LineCount': line_count,
                'Lines': ', '.join(sorted(lines)),
                'ModelCount': len(data['models']),
                'TotalQty': data['qty'],
                'IsSplit': is_split
            })
        
        # 데이터프레임으로 변환하고 정렬
        project_df = pd.DataFrame(project_analysis)
        if not project_df.empty:
            project_df.sort_values(by=['LineCount', 'TotalQty'], ascending=[False, False], inplace=True)
        
        # 2. 모델 & 지역별 라인 할당 분석
        # 모델 + 지역 그룹화
        model_region_groups = defaultdict(lambda: {'records': [], 'lines': set(), 'projects': set(), 'qty': 0})
        
        for _, row in result_df.iterrows():
            project = row['Project']
            region = row['Region']
            line = row['Line']
            item = row['Item']
            qty = row['Qty']
            
            # 지역 정보가 없으면 건너뛰기
            if not region:
                continue
            
            # 모델 & 지역별 그룹화
            model_key = f"{item}_{region}"
            model_region_groups[model_key]['records'].append(row)
            model_region_groups[model_key]['lines'].add(line)
            model_region_groups[model_key]['projects'].add(project)
            model_region_groups[model_key]['qty'] += qty
        
        # 모델 분석 데이터 생성
        model_analysis = []
        for model_key, data in model_region_groups.items():
            item, region = model_key.split('_', 1)
            lines = data['lines']
            line_count = len(lines)
            is_split = line_count > 1
            
            # only_split이 True이고 분할되지 않은 경우 건너뛰기
            if only_split and not is_split:
                continue
                
            model_analysis.append({
                'Item': item,
                'Region': region,
                'LineCount': line_count,
                'Lines': ', '.join(sorted(lines)),
                'ProjectCount': len(data['projects']),
                'Projects': ', '.join(sorted(data['projects'])),
                'TotalQty': data['qty'],
                'IsSplit': is_split
            })
        
        # 데이터프레임으로 변환하고 정렬
        model_df = pd.DataFrame(model_analysis)
        if not model_df.empty:
            model_df.sort_values(by=['LineCount', 'TotalQty'], ascending=[False, False], inplace=True)
        
        return result_df, project_df, model_df
        
    except Exception as e:
        print(f"라인 할당 분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None