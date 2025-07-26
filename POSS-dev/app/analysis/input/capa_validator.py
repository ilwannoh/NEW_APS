import pandas as pd
import numpy as np
from scipy.optimize import linprog
from app.utils.error_handler import (
    error_handler, safe_operation,
    DataError, CalculationError
)

"""
제조동별 물량 분배 비율이 제약 조건을 통과하는지 확인하는 함수 (선형 계획법)
"""
@error_handler(
    show_dialog=True,
    default_return={
        'current_distribution': {},
        'building_ratios': {},
        'violations': {},
        'current_valid': False,
        'alternative_possible': False,
        'has_anomalies': True
    }
)
def validate_distribution_ratios(processed_data):
    try :
        if not processed_data :
            raise DataError('No processed data provided')
        
        demand_items = processed_data['demand_items']
        project_to_buildings = processed_data['project_to_buildings']
        building_constraints = processed_data['building_constraints']

        if not demand_items :
            raise DataError('No demand items found in processed data')
        if not project_to_buildings :
            raise DataError('No project to buildings mapping found in processed data')
        if not building_constraints :
            raise DataError('No building constraints found in processed data')

        current_distribution = safe_operation(
            analyze_current_distribution,
            'Failed to analyze current distribution',
            demand_items, project_to_buildings
        )

        if not current_distribution :
            current_distribution = {}

        total_quantity = sum(current_distribution.values())

        if total_quantity > 0 :
            building_ratios = {
                building: quantity / total_quantity
                for building, quantity in current_distribution.items()
            }
        else :
            building_ratios = {building: 0 for building in current_distribution}

        violations = {}
        distribution_valid = True

        for building, ratio in building_ratios.items() :
            if building in building_constraints :
                try :
                    lower_limit = building_constraints[building].get('lower_limit', 0)
                    upper_limit = building_constraints[building].get('upper_limit', 1)

                    if ratio < lower_limit :
                        violations[building] = {
                            'type': 'below_limit',
                            'current_ratio': ratio,
                            'limit': lower_limit,
                            'gap': lower_limit - ratio
                        }
                        distribution_valid = False
                    
                    elif ratio > upper_limit :
                        violations[building] = {
                            'type': 'above_limit',
                            'current_ratio': ratio,
                            'limit': upper_limit,
                            'gap': ratio - upper_limit
                        }
                        distribution_valid = False
                except Exception as e :
                    continue

        alternative_valid = False

        if not distribution_valid :
            try :
                fixed_projects, flexible_projects = safe_operation(
                    classify_projects,
                    'Failed to classify projects',
                    demand_items, project_to_buildings
                )

                if fixed_projects is None or flexible_projects is None :
                    raise CalculationError('Failed to classify projects')
                
                optimal_result = safe_operation(
                    find_optimal_distribution_with_lp,
                    'Failed to find optimal distribution',
                    fixed_projects, flexible_projects, project_to_buildings, building_constraints
                )
                
                if optimal_result and optimal_result.get('success') :
                    current_distribution = optimal_result['distribution']
                    total_quantity = sum(current_distribution.values())

                    if total_quantity > 0 :
                        building_ratios = {
                            building: quantity / total_quantity
                            for building, quantity in current_distribution.items()
                        }
                    else :
                        building_ratios = {building : 0 for building in current_distribution}
                    
                    violations = {}
                    distribution_valid = True
                    alternative_valid = True
                else:
                    alternative_valid = False
            except Exception as e :
                alternative_valid = False

        return {
            'current_distribution': current_distribution,
            'building_ratios': building_ratios,
            'violations': violations,
            'current_valid': distribution_valid,
            'alternative_possible': alternative_valid,
            'has_anomalies': not (distribution_valid or alternative_valid)
        }
    except Exception as e :
        if not isinstance(e, (DataError, CalculationError)) :
            raise CalculationError(f'Error in validate_distribution_ratios : {str(e)}')
        raise

"""
선형 계획법을 사용한 최적 분배 함수
"""
@error_handler(
    show_dialog=True,
    default_return={'success': False, 'distribution': None}
)
def find_optimal_distribution_with_lp(fixed_projects, flexible_projects, project_to_buildings, building_constraints):
    try :
        if not building_constraints :
            return {'success' : False, 'distribution' : None}
        
        buildings = list(building_constraints.keys())
        n_buildings = len(buildings)

        if n_buildings == 0 :
            return {'success' : False, 'distribution' : None}
        
        fixed_allocation = {building : 0 for building in buildings}
        
        for item in fixed_projects :
            try :
                project = item.get('Basic2', item.get('Project', ''))
                mfg_quantity = float(item.get('MFG', 0)) if pd.notna(item.get('MFG', 0)) else 0
                buildings_for_project = project_to_buildings.get(project, [])
                
                if buildings_for_project and buildings_for_project[0] in fixed_allocation :
                    fixed_allocation[buildings_for_project[0]] += mfg_quantity
            except Exception as e :
                continue
        
        variables = []
        variable_map = {}
        
        idx = 0
        project_quantities = {}
        
        for item in flexible_projects :
            try :
                project = item.get('Basic2', item.get('Project', ''))
                mfg_quantity = float(item.get('MFG', 0)) if pd.notna(item.get('MFG', 0)) else 0
                buildings_for_project = project_to_buildings.get(project, [])
                
                if not buildings_for_project :
                    continue
                    
                project_quantities[project] = project_quantities.get(project, 0) + mfg_quantity
            except Exception as e :
                continue
        
        for project, total_quantity in project_quantities.items() :
            try :
                buildings_for_project = []
                
                for item in flexible_projects :
                    item_project = item.get('Basic2', item.get('Project', ''))

                    if item_project == project :
                        buildings_for_item = project_to_buildings.get(item_project, [])

                        for b in buildings_for_item :
                            if b not in buildings_for_project :
                                buildings_for_project.append(b)
                
                for building in buildings_for_project :
                    if building in buildings :
                        variables.append({
                            'project': project,
                            'building': building,
                            'quantity': total_quantity,
                            'index': idx
                        })
                        variable_map[(project, building)] = idx
                        idx += 1
            except Exception as e :
                continue
        
        if not variables :
            return {'success': False, 'distribution': None}
        
        n_vars = len(variables)
        
        c = np.zeros(n_vars)
        
        A_eq = []
        b_eq = []
        A_ub = []
        b_ub = []
        
        projects_in_variables = set(v['project'] for v in variables)

        for project in projects_in_variables :
            try :
                row = np.zeros(n_vars)

                for v in variables :
                    if v['project'] == project :
                        row[v['index']] = 1

                A_eq.append(row)
                b_eq.append(1.0)
            except Exception as e :
                continue
        
        total_fixed = sum(fixed_allocation.values())
        total_flexible = sum(project_quantities.values())
        total_quantity = total_fixed + total_flexible
        
        if total_quantity == 0 :
            return {'success' : False, 'distribution' : None}
        
        for _, building in enumerate(buildings) :
            try :
                if building in building_constraints :
                    lower_limit = building_constraints[building].get('lower_limit', 0)
                    required_quantity = lower_limit * total_quantity
                    
                    row = np.zeros(n_vars)

                    for v in variables :
                        if v['building'] == building :
                            row[v['index']] = -v['quantity']
                    
                    A_ub.append(row)
                    b_ub.append(-(required_quantity - fixed_allocation[building]))
            except Exception as e :
                continue
        
        for _, building in enumerate(buildings) :
            try :
                if building in building_constraints :
                    upper_limit = building_constraints[building].get('upper_limit', 1)
                    max_quantity = upper_limit * total_quantity
                    
                    row = np.zeros(n_vars)

                    for v in variables :
                        if v['building'] == building :
                            row[v['index']] = v['quantity']
                    
                    A_ub.append(row)
                    b_ub.append(max_quantity - fixed_allocation[building])
            except Exception as e :
                continue
        
        bounds = [(0, 1) for _ in range(n_vars)]
        
        try:
            result = linprog(c, A_eq=A_eq if A_eq else None, b_eq=b_eq if b_eq else None,
                            A_ub=A_ub if A_ub else None, b_ub=b_ub if b_ub else None,
                            bounds=bounds, method='highs')
            
            if result.success :
                final_allocation = {building : fixed_allocation[building] for building in buildings}
                
                for v in variables :
                    try :
                        allocation_ratio = result.x[v['index']]
                        building = v['building']
                        quantity = v['quantity']
                        final_allocation[building] += allocation_ratio * quantity
                    except Exception as e :
                        continue
                
                total = sum(final_allocation.values())

                if total > 0 :
                    valid_solution = True

                    for building in buildings :
                        try :
                            if building in building_constraints :
                                ratio = final_allocation[building] / total
                                lower = building_constraints[building].get('lower_limit', 0)
                                upper = building_constraints[building].get('upper_limit', 1)
                                
                                if ratio < lower - 1e-6 or ratio > upper + 1e-6 :
                                    valid_solution = False
                                    break
                        except Exception as e :
                            continue
                    
                    if valid_solution :
                        return {'success' : True, 'distribution' : final_allocation}
        except Exception as e :
            raise CalculationError(f'Linear programming error : {str(e)}')
        
        return {'success': False, 'distribution': None}
    except Exception as e :
        if not isinstance(e, CalculationError) :
            raise CalculationError(f'Error in find optimal distribution with lp : {str(e)}')
        raise

"""
현재 분배 상태 분석 함수
"""
@error_handler(
    show_dialog=True,
    default_return={}
)
def analyze_current_distribution(demand_items, project_to_buildings) :
    try :
        if not demand_items or not project_to_buildings :
            return {}
        
        all_buildings = set()
        
        for buildings in project_to_buildings.values() :
            all_buildings.update(buildings)
        
        building_quantity = {building : 0 for building in all_buildings}
        
        for item in demand_items :
            try :
                project = item.get('Basic2', item.get('Project', ''))

                if not project :
                    continue

                mfg_quantity = float(item.get('MFG', 0)) if pd.notna(item.get('MFG', 0)) else 0
                buildings = project_to_buildings.get(project, [])
                
                if not buildings :
                    continue
                
                if len(buildings) == 1 :
                    building_quantity[buildings[0]] += mfg_quantity
                else :
                    quantity_per_building = mfg_quantity / len(buildings)
                    
                    for building in buildings :
                        if building in building_quantity :
                            building_quantity[building] += quantity_per_building
            except Exception as e :
                continue
        
        return building_quantity
    except Exception as e :
        raise CalculationError(f'Error in analyze current distribution : {str(e)}')

"""
프로젝트 분류 함수
"""
@error_handler(
    show_dialog=True,
    default_return=([], [])
)
def classify_projects(demand_items, project_to_buildings) :
    try :
        if not demand_items or not project_to_buildings :
            return ([], [])
        
        fixed_projects = []
        flexible_projects = []
        
        for item in demand_items :
            try :
                project = item.get('Basic2', item.get('Project', ''))

                if not project :
                    continue

                buildings = project_to_buildings.get(project, [])
                
                if len(buildings) <= 1 :
                    fixed_projects.append(item)
                else :
                    flexible_projects.append(item)
            except Exception as e :
                continue
        
        return fixed_projects, flexible_projects
    except Exception as e :
        raise CalculationError(f'Error in classify projects : {str(e)}')