"""
다양한 시나리오의 판매계획 더미데이터 생성
"""
import pandas as pd
import numpy as np
import os

def create_scenario_1_growth():
    """시나리오 1: 성장형 - 연중 꾸준히 증가하는 수요"""
    products = ['제품A', '제품B', '제품C', '제품D', '제품E']
    
    data = {'제품명': products}
    
    # 기본 수요
    base_demand = [100, 80, 60, 40, 30]
    
    for month in range(1, 13):
        # 성장률 적용 (월 2-5% 성장)
        growth_rate = 1 + (month * 0.03)
        data[f'{month}월'] = [int(base * growth_rate) for base in base_demand]
    
    df = pd.DataFrame(data)
    
    # 파일 저장
    output_path = os.path.join('data', 'sales_plan_growth.xlsx')
    df.to_excel(output_path, sheet_name='성장형_판매계획', index=False)
    print(f"성장형 판매계획 생성: {output_path}")
    
    return df

def create_scenario_2_seasonal():
    """시나리오 2: 계절형 - 특정 시즌에 피크를 보이는 수요"""
    products = ['여름제품A', '여름제품B', '겨울제품A', '겨울제품B', '사계절제품']
    
    data = {'제품명': products}
    
    # 월별 계절 지수
    seasonal_index = {
        1: 0.6,   # 1월 - 겨울
        2: 0.7,   # 2월 - 겨울
        3: 0.9,   # 3월 - 봄
        4: 1.0,   # 4월 - 봄
        5: 1.1,   # 5월 - 봄
        6: 1.4,   # 6월 - 여름
        7: 1.6,   # 7월 - 여름
        8: 1.5,   # 8월 - 여름
        9: 1.2,   # 9월 - 가을
        10: 1.0,  # 10월 - 가을
        11: 0.8,  # 11월 - 겨울
        12: 0.7   # 12월 - 겨울
    }
    
    # 제품별 기본 수요와 계절 특성
    product_config = {
        '여름제품A': {'base': 100, 'summer_boost': 2.0, 'winter_penalty': 0.3},
        '여름제품B': {'base': 80, 'summer_boost': 1.8, 'winter_penalty': 0.4},
        '겨울제품A': {'base': 90, 'summer_boost': 0.4, 'winter_penalty': 2.0},
        '겨울제품B': {'base': 70, 'summer_boost': 0.5, 'winter_penalty': 1.8},
        '사계절제품': {'base': 120, 'summer_boost': 1.2, 'winter_penalty': 1.2}
    }
    
    for month in range(1, 13):
        month_demand = []
        for product in products:
            config = product_config[product]
            base = config['base']
            
            # 계절 조정
            if month in [6, 7, 8]:  # 여름
                if '여름' in product:
                    demand = base * seasonal_index[month] * config['summer_boost']
                elif '겨울' in product:
                    demand = base * seasonal_index[month] * config['summer_boost']
                else:
                    demand = base * seasonal_index[month]
            elif month in [12, 1, 2]:  # 겨울
                if '겨울' in product:
                    demand = base * seasonal_index[month] * config['winter_penalty']
                elif '여름' in product:
                    demand = base * seasonal_index[month] * config['winter_penalty']
                else:
                    demand = base * seasonal_index[month]
            else:
                demand = base * seasonal_index[month]
            
            month_demand.append(int(demand))
        
        data[f'{month}월'] = month_demand
    
    df = pd.DataFrame(data)
    
    # 파일 저장
    output_path = os.path.join('data', 'sales_plan_seasonal.xlsx')
    df.to_excel(output_path, sheet_name='계절형_판매계획', index=False)
    print(f"계절형 판매계획 생성: {output_path}")
    
    return df

def create_scenario_3_irregular():
    """시나리오 3: 불규칙형 - 프로모션과 이벤트에 따른 변동"""
    products = ['신제품X', '인기제품Y', '프로모션제품Z', '일반제품A', '일반제품B']
    
    data = {'제품명': products}
    
    # 월별 이벤트 효과
    events = {
        1: {'신제품X': 0.5, 'default': 1.0},  # 신제품 출시 전
        2: {'신제품X': 2.0, 'default': 1.0},  # 신제품 출시
        3: {'프로모션제품Z': 1.8, 'default': 1.0},  # 프로모션
        4: {'default': 0.9},  # 비수기
        5: {'인기제품Y': 1.5, 'default': 1.0},  # 인기 상승
        6: {'프로모션제품Z': 2.0, 'default': 1.1},  # 대규모 프로모션
        7: {'인기제품Y': 1.7, 'default': 1.2},  # 여름 성수기
        8: {'default': 1.1},
        9: {'프로모션제품Z': 1.6, 'default': 1.0},  # 프로모션
        10: {'default': 1.0},
        11: {'프로모션제품Z': 2.2, 'default': 1.1},  # 연말 프로모션
        12: {'신제품X': 1.8, '인기제품Y': 1.5, 'default': 1.3}  # 연말 특수
    }
    
    # 기본 수요
    base_demands = {
        '신제품X': 80,
        '인기제품Y': 100,
        '프로모션제품Z': 70,
        '일반제품A': 60,
        '일반제품B': 50
    }
    
    for month in range(1, 13):
        month_demand = []
        month_events = events[month]
        
        for product in products:
            base = base_demands[product]
            
            # 이벤트 효과 적용
            if product in month_events:
                multiplier = month_events[product]
            else:
                multiplier = month_events.get('default', 1.0)
            
            # 랜덤 변동 추가 (±10%)
            random_factor = np.random.uniform(0.9, 1.1)
            
            demand = int(base * multiplier * random_factor)
            month_demand.append(demand)
        
        data[f'{month}월'] = month_demand
    
    df = pd.DataFrame(data)
    
    # 파일 저장
    output_path = os.path.join('data', 'sales_plan_irregular.xlsx')
    df.to_excel(output_path, sheet_name='불규칙형_판매계획', index=False)
    print(f"불규칙형 판매계획 생성: {output_path}")
    
    return df

def create_scenario_4_large_scale():
    """시나리오 4: 대규모 - 많은 제품과 높은 수요"""
    # 30개 제품 생성
    products = []
    for category in ['A', 'B', 'C', 'D', 'E']:
        for num in range(1, 7):
            products.append(f'제품{category}{num}')
    
    data = {'제품명': products}
    
    # 카테고리별 기본 수요
    category_base = {
        'A': 200,  # 주력 제품
        'B': 150,  # 중요 제품
        'C': 100,  # 일반 제품
        'D': 70,   # 보조 제품
        'E': 50    # 기타 제품
    }
    
    for month in range(1, 13):
        month_demand = []
        
        for product in products:
            category = product[2]  # 제품A1에서 'A' 추출
            base = category_base[category]
            
            # 제품 번호에 따른 변동
            product_num = int(product[3])
            variation = 1 - (product_num - 1) * 0.1
            
            # 월별 변동 (사인 곡선)
            monthly_variation = 1 + 0.2 * np.sin((month - 1) * np.pi / 6)
            
            demand = int(base * variation * monthly_variation)
            month_demand.append(demand)
        
        data[f'{month}월'] = month_demand
    
    df = pd.DataFrame(data)
    
    # 파일 저장
    output_path = os.path.join('data', 'sales_plan_large_scale.xlsx')
    df.to_excel(output_path, sheet_name='대규모_판매계획', index=False)
    print(f"대규모 판매계획 생성: {output_path}")
    
    return df

def create_all_scenarios():
    """모든 시나리오 실행"""
    print("다양한 판매계획 시나리오 생성 중...\n")
    
    # 디렉토리 확인
    os.makedirs('data', exist_ok=True)
    
    # 각 시나리오 실행
    df1 = create_scenario_1_growth()
    df2 = create_scenario_2_seasonal()
    df3 = create_scenario_3_irregular()
    df4 = create_scenario_4_large_scale()
    
    print("\n모든 판매계획이 생성되었습니다!")
    print("\n생성된 파일:")
    print("1. sales_plan_2025.xlsx - 기본 판매계획")
    print("2. sales_plan_growth.xlsx - 성장형 (꾸준한 증가)")
    print("3. sales_plan_seasonal.xlsx - 계절형 (여름/겨울 피크)")
    print("4. sales_plan_irregular.xlsx - 불규칙형 (프로모션/이벤트)")
    print("5. sales_plan_large_scale.xlsx - 대규모 (30개 제품)")

if __name__ == "__main__":
    create_all_scenarios()