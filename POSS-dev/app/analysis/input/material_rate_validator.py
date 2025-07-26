import pandas as pd
from app.models.input.material import process_material_satisfaction_data
from app.utils.error_handler import (error_handler, safe_operation, CalculationError)

"""
자재 만족률 분석
"""
@error_handler(
    show_dialog=True,
    default_return={'error': 'Error calculating material satisfaction rate'}
)
def calculate_material_satisfaction(data, threshold=90) :
    if isinstance(data, dict) and 'error' in data :
        return data
    
    try :
        required_keys = ['material_df', 'material_item_df', 'demand_df']

        for key in required_keys :
            if key not in data :
                return {'error' : f'필수 데이터 누락 : {key}'}
            
            material_df = data['material_df']
            material_item_df = data['material_item_df']
            demand_df = data['demand_df']
            material_equal_df = data.get('material_equal_df')
            date_columns = data.get('date_columns', [])

        try :
            if isinstance(material_df, pd.DataFrame) and date_columns :
                material_df['Original_On_Hand'] = material_df['On-Hand'].copy()

                for idx, row in material_df.iterrows() :
                    try :
                        future_supply = 0

                        for date_col in date_columns :
                            if date_col in material_df.columns and pd.notnull(row[date_col]) and isinstance(row[date_col], (int, float)) :
                                future_supply += row[date_col]

                        material_df.at[idx, 'On-Hand'] = row['Original_On_Hand'] + future_supply
                    except Exception as e :
                        continue

                data['date_columns_used'] = date_columns

                if date_columns :
                    data['start_date'] = date_columns[0]
                    data['end_date'] = date_columns[-1]
        except Exception as e :
            pass
            
        substitute_groups, material_to_group = safe_operation(
            create_substitute_groups,
            'Error creating substitute groups',
            material_equal_df
        )

        if substitute_groups is None :
            substitute_groups = []
        
        if material_to_group is None :
            material_to_group = {}

        item_to_materials = safe_operation(
            map_items_to_materials,
            'Error mapping items to materials',
            material_item_df, demand_df
        )

        if item_to_materials is None :
            item_to_materials = {}

        material_onhand = safe_operation(
            extract_material_onhand,
            'Error extracting material on-hand',
            material_df
        )

        if material_onhand is None :
            material_onhand = {}

        material_requirements = safe_operation(
            calculate_material_requirements,
            'Error calculating material requirements',
            item_to_materials, demand_df
        )

        if material_requirements is None :
            material_requirements = {}

        group_requirements, group_onhand = safe_operation(
            calculate_group_values,
            'Error calculating group values',
            substitute_groups, material_requirements, material_onhand
        )

        if group_requirements is None :
            group_requirements = {}

        if group_onhand is None :
            group_onhand = {}

        item_producible = safe_operation(
            calculate_item_producible_quantity,
            'Error calculating item producible quantity',
            item_to_materials, material_onhand, material_to_group,
            group_onhand, material_requirements, group_requirements, demand_df
        )

        if item_producible is None :
            item_producible = {}

        item_satisfaction_rates = safe_operation(
            calculate_item_satisfaction_rates,
            'Error culculating item satisfaction rates',
            item_producible, demand_df
        )

        passed_items = [item for item, rate in item_satisfaction_rates.items() if rate >= threshold]
        failed_items = [item for item, rate in item_satisfaction_rates.items() if rate < threshold]

        rows = []

        for item, rate in item_satisfaction_rates.items() :
            try :
                producible = item_producible.get(item, 0)
                pass_status = '통과' if rate >= threshold else '미통과'

                demand = 0

                if 'Item' in demand_df.columns :
                    item_rows = demand_df[demand_df['Item'] == item]

                    if not item_rows.empty :
                        demand = item_rows['MFG'].values[0]

                rows.append({
                    '모델명' : item,
                    '수요량' : demand,
                    '생산가능수량' : producible,
                    '자재만족률' : round(rate, 2),
                    '통과여부' : pass_status
                })
            except Exception as e :
                continue

        result_df = pd.DataFrame(rows)

        try :
            total_demand = result_df['수요량'].sum()
            total_producible = result_df['생산가능수량'].sum()
            overall_rate = (total_producible / total_demand * 100) if total_demand > 0 else 100
        except Exception as e :
            total_demand = 0
            total_producible = 0
            overall_rate = 0

        date_range_info = "없음"

        if 'start_date' in data and 'end_date' in data :
            date_range_info = f'{data['start_date']} ~ {data['end_date']}'

        summary = {
            "통과 모델 수": len(passed_items),
            "전체 모델 수": len(item_satisfaction_rates),
            "통과율(%)": round(len(passed_items) / len(item_satisfaction_rates) * 100 if item_satisfaction_rates else 0, 2),
            "통과 기준(%)": threshold,
            "입고 날짜 범위": date_range_info,
            "전체 수요량": total_demand,
            "전체 생산가능수량": total_producible,
            "전체 자재만족률(%)": round(overall_rate, 2)
        }

        result = {
            "results_table": result_df,
            "summary": summary,
            "item_satisfaction_rates": item_satisfaction_rates,
            "item_producible": item_producible,
            "passed_items": passed_items,
            "failed_items": failed_items,
            "threshold": threshold,
            "material_requirements": material_requirements,
            "material_onhand": material_onhand
        }

        try :
            if 'Original_On_Hand' in material_df.columns :
                material_df['On-Hand'] = material_df['Original_On_Hand']
                material_df.drop(columns=['Original_On_Hand'], inplace=True)
        except Exception as e :
            pass

        return result
        
    except Exception as e :
        return {'error' : f'자재만족률 분석 중 오류 발생 : {str(e)}'}
    
"""
날짜 컬럼 정렬 함수
"""
def sort_date_columns(date_columns) :
    try :
        if not date_columns :
            return []
        
        def extract_date(col) :
            try :
                date_str = str(col).split('(')[0]
                month, day = map(int, date_str.split('/'))

                return month * 100 + day
            except (ValueError, IndexError) :
                return float('inf')
            
        return sorted(date_columns, key = extract_date)
    except Exception as e :
        return date_columns


"""
대체 가능한 자재 그룹 생성
"""
@error_handler(
    show_dialog=False,
    default_return=([], {})
)
def create_substitute_groups(material_equal_df) :
    try :
        substitute_groups = []
        material_to_group = {}

        if material_equal_df is None or (isinstance(material_equal_df, pd.DataFrame) and material_equal_df.empty) :
            return substitute_groups, material_to_group
        
        valid_columns = [col for col in material_equal_df.columns if col.startswith('Material')]

        if not valid_columns :
            return substitute_groups, material_to_group
        
        for idx, row in material_equal_df.iterrows() :
            try :
                group = []

                for col in valid_columns :
                    if pd.notnull(row[col]) and row[col] :
                        group.append(row[col])

                if group :
                    group_idx = len(substitute_groups)
                    substitute_groups.append(group)

                    for material in group :
                        material_to_group[material] = group_idx
            except Exception as e :
                continue

        return substitute_groups, material_to_group
    except Exception as e :
        raise CalculationError(f'Error creating substitute groups : {str(e)}')

"""
수요 아이템별로 필요한 자재 매핑
"""
@error_handler(
    show_dialog=False,
    default_return={}
)
def map_items_to_materials(material_item_df, demand_df) :
    try :
        item_to_materials = {}

        if material_item_df is None or material_item_df.empty or demand_df is None or demand_df.empty :
            return item_to_materials
        
        model_columns = [col for col in material_item_df.columns if col.startswith('Top_Model_')]

        if not model_columns :
            return item_to_materials
        
        active_materials = material_item_df[material_item_df['Active_OX'] == 'O'].copy()

        for idx, row in demand_df.iterrows() :
            item = row['Item'] if 'Item' in row else row.name
            item_to_materials[item] = []

            for mat_idx, mat_row in active_materials.iterrows() :
                material = mat_row['Material']

                for col in model_columns :
                    if pd.notnull(mat_row[col]) and mat_row[col] :
                        if match_pattern(item, mat_row[col]) :
                            item_to_materials[item].append(material)
                            break

        return item_to_materials
    except Exception as e :
        raise CalculationError(f'Error mapping items to materials : {str(e)}')

"""
와일드카드 패턴 확인
"""
@error_handler(
    show_dialog=False,
    default_return=False
)
def match_pattern(item, pattern) :
    try :
        if not isinstance(item, str) or not isinstance(pattern, str) :
            return False
        
        parts = pattern.split('*')

        if not parts :
            return False

        if not item.startswith(parts[0]) :
            return False
        
        if not item.endswith(parts[-1]) :
            return False
        
        current_pos = len(parts[0])

        for part in parts[1:-1] :
            if part :
                pos = item.find(part, current_pos)

                if pos == -1 :
                    return False
                
                current_pos = pos + len(part)

        return True
    except Exception as e :
        return False

"""
자재별 On-Hand 추출
"""
@error_handler(
    show_dialog=False,
    default_return={}
)
def extract_material_onhand(material_df) :
    try :
        material_onhand = {}

        if material_df is None or material_df.empty :
            return material_onhand
        
        try :
            active_materials = material_df[material_df['Active_OX'] == 'O'].copy()
        except Exception as e :
            active_materials = material_df.copy()

        for idx, row in active_materials.iterrows() :
            try :
                if 'Material' not in row or 'On-Hand' not in row :
                    continue

                material = row['Material']
                onhand = float(row['On-Hand']) if pd.notna(row['On-Hand']) else 0
                material_onhand[material] = onhand
            except Exception as e :
                continue

        return material_onhand
    except Exception as e :
        raise CalculationError(f'Error extracting material on-hand : {str(e)}')

"""
자재별 총 소요량 계산
"""
@error_handler(
    show_dialog=False,
    default_return={}
)
def calculate_material_requirements(item_to_materials, demand_df) :
    try :
        material_requirements = {}

        if not item_to_materials or demand_df is None or demand_df.empty :
            return material_requirements
        
        for item, materials in item_to_materials.items() :
            try :
                demand = 0

                if 'Item' in demand_df.columns :
                    item_rows = demand_df[demand_df['Item'] == item]

                    if not item_rows.empty :
                        demand = float(item_rows['MFG'].values[0]) if pd.notna(item_rows['MFG'].values[0]) else 0
                else :
                    if item in demand_df.index :
                        demand = float(demand_df.loc[item, 'MFG']) if pd.notna(demand_df.loc[item, 'MFG']) else 0

                if demand > 0 :
                    for material in materials :
                        if material in material_requirements :
                            material_requirements[material] += demand
                        else :
                            material_requirements[material] = demand
            except Exception as e :
                continue

        return material_requirements
    except Exception as e :
        raise CalculationError(f'Error calculating material requirements : {str(e)}')

"""
그룹별 총 소요량과 On-Hand 계산
"""
@error_handler(
    show_dialog=False,
    default_return=({}, {})
)
def calculate_group_values(substitute_groups, material_requirements, material_onhand) :
    try :
        group_requirements = {}
        group_onhand = {}

        for group_idx, group in enumerate(substitute_groups) :
            try :
                group_requirements[group_idx] = sum(material_requirements.get(material, 0) for material in group)
                group_onhand[group_idx] = sum(material_onhand.get(material, 0) for material in group)
            except Exception as e :
                group_requirements[group_idx] = 0
                group_onhand[group_idx] = 0

        return group_requirements, group_onhand
    except Exception as e :
        raise CalculationError(f'Error calculating group values : {str(e)}')

"""
모델별 생산 가능 수량 계산
"""
@error_handler(
    show_dialog=False,
    default_return={}
)
def calculate_item_producible_quantity(item_to_materials, material_onhand, material_to_group,
                                       group_onhand, material_requirements, group_requirements, demand_df) :
    try :
        item_producible = {}

        all_demand_items = set()

        if 'Item' in demand_df.columns :
            all_demand_items.update(demand_df['Item'].dropna().unique())
        else :
            all_demand_items.update(demand_df.index)

        for item in all_demand_items :
            try :
                demand = 0

                if 'Item' in demand_df.columns :
                    item_rows = demand_df[demand_df['Item'] == item]

                    if not item_rows.empty :
                        demand = float(item_rows['MFG'].values[0]) if pd.notna(item_rows['MFG'].values[0]) else 0
                else :
                    if item in demand_df.index :
                        demand = float(demand_df.loc[item, 'MFG']) if pd.notna(demand_df.loc[item, 'MFG']) else 0

                if demand <= 0 :
                    item_producible[item] = 0
                    continue

                materials = item_to_materials.get(item, [])

                if not materials :
                    item_producible[item] = 0
                    continue

                material_producible = []

                for material in materials :
                    try :
                        producible = 0

                        if material in material_to_group :
                            group_idx = material_to_group[material]
                            group_oh = group_onhand.get(group_idx, 0)
                            group_req = group_requirements.get(group_idx, 0)

                            if group_oh <= 0 :
                                producible = 0
                            elif group_req > 0 :
                                ratio = demand / group_req
                                allocated_oh = group_oh * ratio
                                producible = max(0, int(allocated_oh))
                            else :
                                producible = min(demand, int(group_oh))
                        else :
                            material_oh = material_onhand.get(material, 0)
                            material_req = material_requirements.get(material, 0)

                            if material_oh <= 0 :
                                producible = 0
                            elif material_req > 0 :
                                ratio = demand / material_req
                                allocated_oh = material_oh * ratio
                                producible = max(0, int(allocated_oh))
                            else :
                                producible = min(demand, int(material_oh))
                        material_producible.append(producible)
                    except Exception as e :
                        material_producible.append(0)
                
                if material_producible :
                    item_producible[item] = min(material_producible)
                else :
                    item_producible[item] = 0
            except Exception as e :
                item_producible[item] = 0

        for item in all_demand_items :
            if item not in item_producible :
                item_producible[item] = 0

        return item_producible
    except Exception as e :
        raise CalculationError(f'Error calculating item producible quantity : {str(e)}')

"""
모델별 자재만족률 계산
"""
@error_handler(
    show_dialog=False,
    default_return={}
)
def calculate_item_satisfaction_rates(item_producible, demand_df) :
    item_satisfaction_rates = {}

    for item, producible in item_producible.items() :
        demand = 0

        if 'Item' in demand_df.columns :
            item_rows = demand_df[demand_df['Item'] == item]

            if not item_rows.empty :
                demand = item_rows['MFG'].values[0]

        else :
            if item in demand_df.index :
                demand = demand_df.loc[item, 'MFG']

        if demand > 0 :
            item_satisfaction_rates[item] = (producible / demand) * 100
        else :
            item_satisfaction_rates[item] = 100.0

    return item_satisfaction_rates

"""
자재만족률 계산 통합
"""
def analyze_material_satisfaction_all(threshold=90) :
    try :
        data = process_material_satisfaction_data()

        if isinstance(data, dict) and 'error' in data :
            return data
        
        results = calculate_material_satisfaction(data, threshold)

        print_material_satisfaction_summary(results)

        return results
    except Exception as e :
        return {'error' : f'자재만족률 분석 중 오류 발생 : {str(e)}'}


"""
자재만족률 분석 결과의 요약 정보 생성
"""
def get_material_satisfaction_summary(results, threshold=None) :
    if isinstance(results, dict) and 'error' in results :
        return f'오류 발생 : {results['error']}'
    
    if 'summary' not in results or 'results_table' not in results :
        return '분석 결과가 올바르지 않습니다'
    
    summary = results['summary']
    results_table = results['results_table']

    if threshold is None :
        threshold = summary['통과 기준(%)']

    failed_models = results_table[results_table['자재만족률'] < threshold].sort_values(by='자재만족률', ascending=True)

    summary_text = []
    summary_text.append(f"[자재만족률 분석 결과 요약]")
    summary_text.append("=" * 70)
    summary_text.append(f"통과 기준: {summary['통과 기준(%)']}%")
    summary_text.append(f"전체 모델 수: {summary['전체 모델 수']}")
    summary_text.append(f"통과 모델 수: {summary['통과 모델 수']}")
    summary_text.append(f"통과율: {summary['통과율(%)']}%")
    summary_text.append("")

    if failed_models.empty :
        summary_text.append(f'자재만족률이 {threshold}% 미만인 모델이 없습니다')

    else :
        failed_count = len(failed_models)
        summary_text.append(f"[자재만족률이 {threshold}% 미만인 모델 목록 (총 {failed_count}개)]")
        summary_text.append("-" * 70)
        summary_text.append(f"{'모델명':<30} {'수요량':<10} {'생산가능수량':<15} {'자재만족률(%)':<15} {'통과여부':<10}")
        summary_text.append("-" * 70)

        for _, row in failed_models.iterrows() :
            model = row['모델명']
            demand = row['수요량']
            producible = row['생산가능수량']
            rate = row['자재만족률(%)']
            status = row['통과여부']

            summary_text.append(f'{model:<30} {demand:<10.0f} {producible:<15.0f} {rate:<15.2f} {status:<10}')

        return '\n'.join(summary_text)
    
"""
자재만족률 분석 결과 로그 출력
"""
def print_material_satisfaction_summary(results) :
    if isinstance(results, dict) and 'error' in results :
        print(f'오류 발생 : {results['error']}')
        return
    
    if 'summary' not in results or 'results_table' not in results :
        print('분석 결과가 올바르지 않습니다')
        return
    
    summary = results['summary']
    results_table = results['results_table']
    threshold = summary['통과 기준(%)']

    print("\n[자재만족률 분석 결과 요약]")
    print("=" * 70)
    print(f"통과 기준: {summary['통과 기준(%)']}%")
    print(f"전체 모델 수: {summary['전체 모델 수']}")
    print(f"통과 모델 수: {summary['통과 모델 수']} ({summary['통과율(%)']}%)")
    print(f"미통과 모델 수: {summary['전체 모델 수'] - summary['통과 모델 수']} ({100 - summary['통과율(%)']}%)")
    
    if '입고 날짜 범위' in summary :
        print(f'입고 날짜 범위 : {summary['입고 날짜 범위']}')

    failed_models = results_table[results_table['통과여부'] == '미통과'].sort_values(by='자재만족률', ascending=True)

    if failed_models.empty :
        print(f'\n자재만족률이 {threshold}% 미만인 모델이 없습니다')
    else :
        failed_count = len(failed_models)

        print(f"\n[자재만족률이 {threshold}% 미만인 모델 목록 (총 {failed_count}개)]")
        print("-" * 70)
        print(f"{'모델명':<30} {'수요량':<10} {'생산가능수량':<15} {'자재만족률':<15} {'통과여부':<10}")
        print("-" * 70)

        for _, row in failed_models.iterrows() :
            model = row['모델명']
            demand = row['수요량']
            producible = row['생산가능수량']
            rate = row['자재만족률']
            status = row['통과여부']

            print(f"{model:<30} {demand:<10.0f} {producible:<15.0f} {rate:<15.2f} {status:<10}")

    passed_models = results_table[results_table['통과여부'] == '통과']