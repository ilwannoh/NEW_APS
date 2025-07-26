import pandas as pd
import fnmatch

"""
당주 출하 만족률 계산
"""
def calculate_fulfillment_rate(processed_data) :
    if not processed_data :
        return None
    
    demand_data = processed_data['demand']
    material_data = processed_data['material']
    production_data = processed_data['production']
    due_lt_data = processed_data['due_lt']
    df_demand = demand_data['df']
    due_lt_map = due_lt_data['due_lt_map']

    result_df = df_demand.copy()
    result_df['Production_Qty'] = 0
    result_df['Is_Fulfilled'] = False
    result_df['Constraint_Type'] = ''

    for i, row in result_df.iterrows() :
        item = row['Item']
        project = row['Project']
        tosite_group = row['Tosite_group']
        sop = row['SOP']

        if sop <= 0 :
            result_df.at[i, 'Is_Fulfilled'] = True
            continue

        due_lt = get_due_lt(project, tosite_group, due_lt_map)

        if due_lt is None :
            result_df.at[i, 'Constraint_Type'] = 'No due date info'
            continue

        material_constraint = check_material_availability(
            item, sop, material_data['model_to_materials'],
            material_data['availability'], material_data['material_groups']
        )

        production_constraint = check_production_capacity(
            project, tosite_group, sop, due_lt,
            production_data['project_lines'], production_data['line_capacities']
        )

        if material_constraint['available_qty'] == 0 :
            result_df.at[i, 'Production_Qty'] = 0
            result_df.at[i, 'Constraint_Type'] = 'Material shortage'
        elif production_constraint['available_qty'] == 0 :
            result_df.at[i, 'Production_Qty'] = 0
            result_df.at[i, 'Constraint_Type'] = 'Production CAPA shortage'
        else :
            available_qty = min(
                material_constraint['available_qty'],
                production_constraint['available_qty']
            )

            result_df.at[i, 'Production_Qty'] = available_qty

            if available_qty >= sop :
                result_df.at[i, 'Is_Fulfilled'] = True
            else :
                result_df.at[i, 'Is_Fulfilled'] = False

                if material_constraint['available_qty'] <= production_constraint['available_qty'] :
                    result_df.at[i, 'Constraint_Type'] = 'Material shortage'
                else :
                    result_df.at[i, 'Constraint_Type'] = 'Production CAPA shortage'

    total_sop = result_df['SOP'].sum()
    total_production = result_df['Production_Qty'].sum()

    overall_fulfillment_rate = (total_production / total_sop * 100) if total_sop > 0 else 100

    project_fulfillment = {}

    for project, group in result_df.groupby('Project') :
        project_sop = group['SOP'].sum()
        project_production = group['Production_Qty'].sum()
        project_rate = (project_production / project_sop * 100) if project_sop > 0 else 100
        project_fulfillment[project] = {
            'sop' : project_sop,
            'production' : project_production,
            'rate' : project_rate
        }

    site_fulfillment = {}

    for site, group in result_df.groupby('Tosite_group') :
        site_sop = group['SOP'].sum()
        site_production = group['Production_Qty'].sum()
        site_rate = (site_production / site_sop * 100) if site_sop > 0 else 100
        site_fulfillment[site] = {
            'sop' : site_sop,
            'production' : site_production,
            'rate' : site_rate
        }

    return {
        'overall_rate' : overall_fulfillment_rate,
        'total_sop' : total_sop,
        'total_production' : total_production,
        'project_fulfillment' : project_fulfillment,
        'site_fulfillment' : site_fulfillment,
        'detailed_results' : result_df
    }

"""
납기일 찾는 함수
"""
def get_due_lt(project, tosite_group, due_lt_map) :
    if project in due_lt_map and tosite_group in due_lt_map[project] :
        return due_lt_map[project][tosite_group]
    return None

"""
자재 가용성 확인 및 사용 가능 수량 계산
"""
def check_material_availability(item, required_qty, model_to_materials, material_availability, material_groups) :
    required_materials = []

    for pattern, materials in model_to_materials.items() :
        if fnmatch.fnmatch(item, pattern) :
            required_materials.extend(materials)

    required_materials = list(set(required_materials))

    if not required_materials :
        return {
            'available_qty' : 0,
            'missing_materials' : ['No material info']
        }
    
    material_limits = []
    missing_materials = []

    for material in required_materials :
        available = material_availability.get(material, {}).get('on_hand', 0)

        if material in material_groups :
            alternatives = material_groups[material]

            for alt_material in alternatives :
                if alt_material != material :
                    alt_available = material_availability.get(alt_material, {}).get('on_hand', 0)
                    available += alt_available

        if available <= 0 :
            missing_materials.append(material)
        else :
            material_limits.append(available)

    if missing_materials :
        available_qty = 0
    elif material_limits :
        available_qty = min(material_limits)
    else :
        available_qty = 0

    return {
        'available_qty' : min(available_qty, required_qty),
        'missing_materials' : missing_materials
    }

"""
생산 능력 확인 및 납기 내 생산 가능 수량 계산
"""
def check_production_capacity(project, tosite_group, required_qty, due_lt, project_lines, line_capacities) :
    
    if due_lt is None or due_lt <= 0 :
        return {
            'available_qty': 0,
            'reason': 'Invalid due date'
        }
    
    available_lines = project_lines.get(project, [])

    if not available_lines :
        return {
            'available_qty': 0,
            'reason': 'No available production line'
        }
    
    total_capacity = 0
    line_details = []

    for line in available_lines :
        if line in line_capacities :
            shifts_capacity = {}

            for shift in range(1, min(due_lt + 1, 15)) :
                shift_capacity = line_capacities[line].get(shift, 0)
                shifts_capacity[shift] = shift_capacity

            line_capacity = sum(shifts_capacity.values())

            if line_capacity > 0 :
                line_details.append(f"{line}({line_capacity})")
                total_capacity += line_capacity
    
    available_qty = min(total_capacity, required_qty)

    return {
        'available_qty': available_qty,
        'reason': 'Insufficient production capacity' if total_capacity < required_qty else ''
    }

"""
결과 요약 출력
"""
def get_fulfillment_summary(result) :
    if not result :
        return '계산 결과가 없습니다'
    
    summary = []
    summary.append(f"Weekly shipment fulfillment rate : {result['overall_rate']:.2f}%")
    summary.append(f"Total demand(SOP) : {result['total_sop']}")
    summary.append(f"Total production capacity : {result['total_production']}")
    summary.append("\nProject fulfillment rates :")

    for project, data in result['project_fulfillment'].items() :
        summary.append(f"  - {project}: {data['rate']:.2f}% (Demand: {data['sop']}, Production: {data['production']})")
    
    summary.append("\nSatisfaction rate by site :")

    for site, data in result['site_fulfillment'].items() :
        summary.append(f"  - {site}: {data['rate']:.2f}% (Demand: {data['sop']}, Production: {data['production']})")
    
    return "\n".join(summary)