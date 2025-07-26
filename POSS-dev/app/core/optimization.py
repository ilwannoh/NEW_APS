import pandas as pd
import pulp 
import re
from pulp import LpStatus

class Optimization:
    def __init__(self,input):
        """
        input 데이터를 받아서 optimization 객체를 생성합니다

        Parameters:
        input (dictionary) : 
            {
                'demand':{
                    'demand': df
                },
                'master':{
                    'line_available': df,
                    ...
                },
                'dynamic':{
                    'material_item': df,
                    ...
                }
            }
        """
        # 각 엑셀 파일 불러오기. 시트이름이 키, 데이터프레임이 값인 딕셔너리로 저장됨.
        self.demand_excel = input['demand']
        self.master_excel = input['master']
        self.dynamic_excel = input['dynamic']

        # demand 엑셀 파일의 시트를 데이터프레임으로 만들고 주로 쓰일 변수도 정의
        self.df_demand = self.demand_excel['demand'] 
        for i, row in self.df_demand.iterrows() :    
            self.df_demand.loc[i, "Project"] = row["Item"][3:7]
            self.df_demand.loc[i, "Basic2"] = row['Item'][3:8]
            self.df_demand.loc[i, "Tosite_group"] = row["Item"][7:8]
            self.df_demand.loc[i, "RMC"] = row['Item'][3:-3]
            self.df_demand.loc[i, "Color"] = row['Item'][8:-4]

        self.item = self.df_demand.index.tolist()
        self.project = self.df_demand["Basic2"].unique()
        self.RMC = self.df_demand.RMC.unique()

        # master 엑셀 파일의 시트들을 데이터프레임으로 만들고 주로 쓰일 변수도 정의
        self.df_capa_portion = self.master_excel['capa_portion']
        self.df_capa_qty = self.master_excel['capa_qty']
        self.df_line_available = self.master_excel['line_available']
        self.df_capa_outgoing = self.master_excel['capa_outgoing']
        self.df_capa_imprinter = self.master_excel['capa_imprinter']
        self.df_due_LT = self.master_excel['due_LT']

        self.time = {i for i in self.df_capa_qty.columns}
        self.line = self.df_line_available.columns
        self.port_list = self.df_capa_outgoing.Tosite_port.unique()
        self.day_list = list(reversed(range(1, 8)))

        # dynamic 엑셀 파일의 시트들을 데이터프레임으로 만들고 주로 쓰일 변수도 정의
        self.df_material_item = self.dynamic_excel['material_item']
        self.df_material_qty = self.dynamic_excel['material_qty']
        self.df_material_equal = self.dynamic_excel['material_equal']
        self.df_due_request = self.dynamic_excel['due_request']
        self.df_pre_assign = self.dynamic_excel['pre_assign']
        self.df_fixed_option = self.dynamic_excel['fixed_option']

        # 리스트로 쓰는게 편해서 리스트로 변환
        self.time = self.time.difference({'Line'})
        self.time = list(range(1,15))
        self.line = self.line.to_list()[1:]

        self.df_pre_result = None
        self.df_result = None

        self.df_material_item = self.df_material_item.drop(['종류','가용 L/T'],axis=1)
        self.df_material_item = self.df_material_item[self.df_material_item['Active_OX']=='O']
        # print(self.df_material_item)

        self.df_material_qty = self.df_material_qty[self.df_material_qty['Active_OX']=='O']
        self.df_material_item = pd.merge(self.df_material_item,self.df_material_qty,how='left',on='Material')
        # print(self.df_material_item)

    """사전할당 알고리즘 함수"""
    def pre_assign(self,showlog = False):
        """
        Returns:
            dictionary: 
                {
                    'result': 할당 결과 데이터프레임,
                    'combined': fixed option + pre assign 시트 데이터프레임
                    'error': 에러 문구 문자열
                }
        """
        # pre_assign 시트
        df_demand_item = self.df_demand.groupby("Item")[["MFG","PB","SOP"]].sum()
        columns = ['Item','Line','Time','Qty']
        self.df_combined = pd.DataFrame(columns=columns)
        for idx , row in self.df_pre_assign.iterrows():
            for i in range(1,8):
                if pd.notna(row.iloc[2*i]):
                    self.df_combined.loc[len(self.df_combined)] = [row['Item'+str(i)],row['Line'],2*i+row['Shift']-2,row['Qty'+str(i)] if pd.notna(row['Qty'+str(i)]) else 'ALL']
        
        # fixed_option 시트
        new_labels = []
        for idx, row in self.df_fixed_option.iterrows():
            if '*' in row['Fixed_Group'] and str.isdigit(str(row['Qty'])):
                print('ignore row : ',row)
                continue
            if '*' in row['Fixed_Group'] or str(row['Qty']).lower()=='all':
                regex = '^' + row['Fixed_Group'].replace('*','.') + '$'
                for item in df_demand_item.index:
                    if re.fullmatch(regex,item):
                        qty = df_demand_item.loc[item,'MFG']
                        new_labels.append({'Item':item,'Line':row['Fixed_Line'],'Time':row['Fixed_Time'],'Qty':qty})
            else:
                new_labels.append({'Item':row['Fixed_Group'],'Line':row['Fixed_Line'],'Time':row['Fixed_Time'],'Qty':row['Qty']})


        df_new_labels = pd.DataFrame(new_labels)
        self.df_combined = pd.concat([self.df_combined,df_new_labels], ignore_index=True)

        self.df_line_available = self.df_line_available.set_index('Project')
        self.df_capa_qty = self.df_capa_qty.set_index('Line')
        demands = df_demand_item.index

        df_demand_item = df_demand_item.reset_index()
        df_demand_item['Project'] = df_demand_item['Item'].str[3:7]
        df_demand_item['Tosite_group'] = df_demand_item['Item'].str[7:8]
        df_demand_item = pd.merge(df_demand_item,self.df_due_LT,how='left',on=['Project','Tosite_group'])
        df_demand_item = df_demand_item.set_index('Item')

        # 문제 정의
        x = pulp.LpVariable.dicts("produce", [(d, l, t) for d in demands for l in self.line for t in self.time], lowBound=0, cat='Continuous')
        model = pulp.LpProblem("LineShift_Production_Scheduling", pulp.LpMaximize)
        
        # 제약조건 0: 사전할당 테이블
        for idx, row in self.df_combined.iterrows():
            line = list(map(str.strip,str(row['Line']).split(','))) if pd.notna(row['Line']) else self.line
            time = list(map(int, str(row['Time']).split(','))) if pd.notna(row['Time']) else self.time
            model += (pulp.lpSum([x[(row['Item'], l, t)] for l in line for t in time]) >= row['Qty'], f"pre_assign_{row['Item']}_{idx}")

        # 제약조건 1: 모델별 총 수요량 충족 
        for d in demands:
            model += pulp.lpSum([x[(d, l, t)] for l in self.line for t in self.time]) <= df_demand_item.loc[d,'MFG']

        # 제약조건 2: 라인/시프트에서 생산 가능한 모델만 허용
        for d in demands:
            for l in self.line:
                for t in self.time:
                    if self.df_line_available.loc[d[3:7],l] != 1:
                        model += x[(d, l, t)] == 0

         # 제약조건 3: 제조동별 물량 비중 상한/하한
        for ids,row in self.df_capa_portion.iterrows():
            model += (
               row['upper_limit'] * pulp.lpSum([x[(d, l, t)] for (d, l, t) in x]) >=
               pulp.lpSum([x[(d, l, t)] for (d, l, t) in x if l.startswith(row['name'])])
            )
            model += (
                pulp.lpSum([x[(d, l, t)] for (d, l, t) in x if l.startswith(row['name'])]) >=
                row['lower_limit'] * pulp.lpSum([x[(d, l, t)] for (d, l, t) in x])
            )
        # 제약조건 4: 각 라인/시프트 조합의 최대 생산량 제한.
        for l in self.line:
            for t in self.time:
                model += pulp.lpSum([x[(d, l, t)] for d in demands]) <= self.df_capa_qty.loc[l,t]

        # 제약조건 5: 각 (제조동 * 시프트) 별 가동가능한 최대 라인 수. Max_line.
        y = pulp.LpVariable.dicts("line_shift_active", [(l,t) for l in self.line for t in self.time], cat="Binary")
        BIG_M = 10_000_000  # 충분히 큰 값
        for l in self.line:
            for t in self.time:
                total_produced = pulp.lpSum(x[(d, l, t)] for d in demands)
                model += total_produced <= BIG_M * y[(l, t)]
                model += total_produced >= 1 * y[(l, t)] 

        blocks = list(set(l[0] for l in self.line))
        for b in blocks:
            for time in self.time:
                max_line = self.df_capa_qty.loc[f'Max_line_{b}',time] if pd.notna(self.df_capa_qty.loc[f'Max_line_{b}',time]) else 100
                model += pulp.lpSum(
                    y[(l, t)] for l in self.line for t in self.time if l.startswith(b) and t == time
                ) <= max_line

        # 제약조건 6: 각 (제조동 * 시프트) 별 최대 생산 수량. Max_qty
        for b in blocks:
            for time in self.time:
                max_qty = self.df_capa_qty.loc[f'Max_qty_{b}',time] if pd.notna(self.df_capa_qty.loc[f'Max_qty_{b}',time]) else 10_000_000
                model += pulp.lpSum(
                    x[(d, l, t)] for (d,l,t) in x if l.startswith(b) and t == time
                ) <= max_qty

        

        # 목적함수
        shipment_variable = pulp.LpVariable.dict("shipment_variable",[d for d in demands], cat='Binary')
        # material_variable = pulp.LpVariable.dict("material_variable",)
        for d in demands:
            lt = df_demand_item.loc[d,'Due_date_LT']
            sop = df_demand_item.loc[d,'SOP']
            sop_result = pulp.lpSum(x[(d, l, t)] for l in self.line for t in range(1,lt+1))
            model += sop_result - sop <= BIG_M * shipment_variable[d]
            model += sop_result >= sop * shipment_variable[d]


        shift_weight = [0,0,0.001,0.001,0.003,0.003,0.006,0.006,0.02,0.02,0.1,0.1,0.1,0.1]
        obj1 = pulp.lpSum(shift_weight[t-1] * x[(d, l, t)] for d in demands for l in self.line for t in self.time)
        obj2 = pulp.lpSum(shipment_variable[d] for d in demands)
        # model += -1 * obj1 + obj2
        model += obj2
        model.solve()

        

        print(pulp.value(model.objective))
        results = []
        for l in self.line:
            for t in self.time:
                print(f"{l} - {t} 시프트:")
                for d in demands:
                    units = int(pulp.value(x[(d, l, t)]))
                    if units > 0:
                        print(f"  모델 {d} → {units}개 생산")
                        sop = -99
                        mfg = -99
                        due_lt= -99
                        to_site = "XX"
                        results.append((l,t,d+to_site,d,units,d[3:7],to_site,sop,mfg,d[3:11],due_lt)) 
        print('총 수요량',df_demand_item['MFG'].sum())
        print(f"\n총 생산량: {sum(x[d, l, t].value() for d in demands for l in self.line for t in self.time)}개")
        print('목적함수 값',pulp.value(model.objective))
        total_production = pulp.value(pulp.lpSum([x[(d, l, t)] for (d, l, t) in x]))
        for (idx,row) in self.df_capa_portion.iterrows():
            line_production =pulp.value(pulp.lpSum([x[(d, l, t)] for (d, l, t) in x if l.startswith(row['name'])]))
            line_ratio = (line_production / total_production) * 100 if total_production != 0 else 0
            print(f"{row['name']}라인 생산량: {int(line_production)}개, {row['name']}라인 비중: {line_ratio:.2f}%")
        if LpStatus[model.status] == 'Optimal':
            print("해를 찾았습니다!")
        else:
            print("해를 찾지 못했습니다. 상태:", LpStatus[model.status])
            # for name, constraint in model.constraints.items():
                
                    
            
        self.df_pre_result = pd.DataFrame(results,columns=['Line','Time','Demand','Item','Qty','Project','To_site','SOP','MFG','RMC','Due_LT'])
        return {'result':self.df_pre_result, 'combined' : self.df_combined }
    """사전할당 알고리즘 함수"""
    def linear_programming(self, showlog = False):
        """
        Returns:
            dictionary: 
                {
                    'result': 할당 결과 데이터프레임,
                    'combined': fixed option + pre assign 시트 데이터프레임
                    'error': 에러 문구 문자열
                }

        """
        # 모든 (line * shift) 를 원소로 하는 리스트
        line_shifts = [(l,s) for l in self.line for s in self.time]
        # 생산해야 하는 아이템들 리스트. 
        items = []
        # 아이템별 생산 수요량 딕셔너리. 
        demand = {}

        # pre_assign 을 fixed_option에 통합한 데이터프레임 만들기
        self.df_combined = self.df_fixed_option.copy()
        for idx , row in self.df_pre_assign.iterrows():
            for i in range(1,8):
                if pd.notna(row.iloc[2*i]):
                    self.df_combined.loc[len(self.df_combined)] = [row['Item'+str(i)],row['Line'],2*i+row['Shift']-2,row['Qty'+str(i)] if pd.notna(row['Qty'+str(i)]) else 'ALL']
        
        if showlog: print(self.df_combined)

        # 통합한 시트의 아이템들을 items 와 demand 에 추가
        done_list = []
        for index, row in self.df_combined.iterrows():
            if '*' in row['Fixed_Group']:
                if pd.isna(row['Qty']):
                    if showlog: print(row['Fixed_Group']+' 아이템의 Qty 가 비어있습니다')
                    continue
                elif str(row['Qty']).lower() == 'all':
                    for idx, demandrow in self.df_demand.iterrows():
                        regex =  str(row['Fixed_Group']).replace("*",".")
                        item = demandrow['Item']
                        if bool(re.fullmatch(regex, item)):
                            if item in demand:
                                demand[item] = demand[item] + demandrow['MFG']
                            else: 
                                demand[item] = demandrow['MFG']
                                done_list.append(item)
                else :# 여러 아이템을 ***P205******* 처럼 선택하고 Qty 에 값이 있을 경우
                    if showlog: (row['Fixed_Group'],",",row['Qty'])
                    if showlog: print("여러 아이템을 선택하고 수량을 입력했기 때문에 오류입니다")
            else:
                if pd.isna(row['Qty']):
                    if showlog: print(row['Fixed_Group']+' 아이템의 Qty 가 비어있습니다')
                    continue
                elif str(row['Qty']).lower() == 'all':
                    df_items =self.df_demand[self.df_demand['Item']==row['Fixed_Group']]
                    qty = 0
                    for index, value in df_items.iterrows():
                        qty += value['MFG']
                    demand[row['Fixed_Group']] = qty
                else : # Qty 에 값이 있을 경우
                    if row['Fixed_Group'] in done_list:
                        continue
                    elif row['Fixed_Group'] in demand:
                        demand[row['Fixed_Group']] += row['Qty']
                    else:
                        demand[row['Fixed_Group']] = row['Qty']
        
        items = list(demand.keys())
        
        
        # 라인*시프트 별 Capa (최대 생산 가능량)
        capacity = {(l,s):int(self.df_capa_qty.loc[self.df_capa_qty['Line'] == l, s].values[0]) for (l, s) in line_shifts}


        # 라인*시프트 별 생산가능 아이템. pre_assign, fixed_option 시트의 조건들이 들어가야함.
        allowed_items = {} # (line*shift) 별 생산 가능한 모델
        fixed_line_shifts = {}
        for idx, row in self.df_combined.iterrows():
            fixed_lines = row['Fixed_Line'].split(",") if pd.notna(row['Fixed_Line']) else self.line
            fixed_times = list(map(int,str(row['Fixed_Time']).split(","))) if pd.notna(row['Fixed_Time']) else self.time

            if '*' in str(row['Fixed_Group']):
                regex = str(row['Fixed_Group']).replace("*",".")
                for item in self.df_demand['Item']:
                    if bool(re.fullmatch(regex, item)):
                        fixed_line_shifts[item] = [(line,time) for line in fixed_lines for time in fixed_times]
                continue
            if row['Fixed_Group'] in fixed_line_shifts:
                fixed_line_shifts[row['Fixed_Group']].extend([(line,time) for line in fixed_lines for time in fixed_times])
            else:
                fixed_line_shifts[row['Fixed_Group']] = [(line,time) for line in fixed_lines for time in fixed_times]

        if showlog: print('fixed_line_shifts : ',fixed_line_shifts)

        for l, s in line_shifts:
            if l not in self.df_line_available.columns:
                raise ValueError(f"라인 {l}는 line_available에 존재하지 않습니다.")
            projects = self.df_line_available[self.df_line_available[l] == 1]['Project'].tolist()
            # 특정 라인*시프트에서는 특정 프로젝트의 모델만 생산 가능하고,그 모델은 사전할당에서 지정한 라인*시프트 범위 내여야 한다
            allowed = []
            for m in items:
                if any(m[3:7] == project for project in projects) and (l,s) in fixed_line_shifts[m]:
                    allowed.append(m)
                elif not any(m[3:7] == project for project in projects) and (l,s) in fixed_line_shifts[m]:
                    if showlog: print(f"{m} 아이템은 {l},{s} 에서 생산할 수 없는 아이템입니다")
            allowed_items[(l, s)] = allowed
        if showlog: print('allowed_items : ',allowed_items)

        # 결정 변수: 모델 m을 라인 l, 시프트 s에서 몇 개 생산할지. 카테고리는 정수형.
        x = pulp.LpVariable.dicts("produce", [(m, l, s) for m in items for (l, s) in line_shifts], lowBound=0, cat='Integer')

        # y 는 각 (라인 * 시프트) 를 키값으로, 그 (라인*시프트) 가 가동중이면 1, 아니면 0 을 value 값으로 갖는 pulp 딕셔너리
        y = pulp.LpVariable.dicts("line_shift_active", line_shifts, cat="Binary")

        # 문제 정의. 최대화 문제
        model = pulp.LpProblem("LineShift_Production_Scheduling", pulp.LpMaximize)
        
        # 목적함수: 총 생산량 최대화
        model += pulp.lpSum([x[(m, l, s)] for m in items for (l, s) in line_shifts])
 
        # 제약조건 1: 모델별 총 수요량 충족 + 사전할당 알고리즘에서 모든 아이템은 무조건 할당되어야함
        # 아래의 조건에서는 <= 부등식을 넣었지만 최종 생산량이 수요량과 같지 않은 경우는 사전할당에 실패한 경우로 보고 
        # 딕셔너리에 'error' 키를 담아서 반환
        for m in items:
            model += (pulp.lpSum([x[(m, l, s)] for (l, s) in line_shifts]) <= demand[m],f'constraint1 ({m})')

        # 제약조건 2: 라인/시프트에서 생산 가능한 모델만 허용
        for (l, s) in line_shifts:
            for m in items:
                if m not in allowed_items.get((l, s), []):
                    model += (x[(m, l, s)] == 0, f"constraint2 ({m},{l},{s})")
        #  model += x[(m, l, s)] == 0 으로 넣어도 동작하지만 제약조건 각각에 constraint2 와같이 이름을 붙여준 것은 
        # 해를 찾지 못했을 경우 위배되는 제약조건이 무엇인지 알 수 있게 하기 위함.

        # 제약조건 3: 제조동별 물량 비중 상한/하한 (사전 할당에서는 물량 비중을 고려하지 않는게 맞다는 판단 하에 제약조건 제외)

        # 제약조건 4: 각 라인/시프트 조합의 최대 생산량 제한
        for (l, s) in line_shifts:
            model += (pulp.lpSum([x[(m, l, s)] for m in items]) <= capacity[(l, s)],f'constraint4 ({l},{s})')

        # 제약조건 5: 각 (제조동 * 시프트) 별 가동가능한 최대 라인 수. capa_qty 시트와 관련됨. Max_line
        # 특정 y[(l,s)] 가 1이면 그 (라인*시프트) 에서 생산되는 모델이 적어도 1개는 있다는 뜻.반대로 0이면 하나도 없다는 뜻.
        BIG_M = 1_000_000  # 충분히 큰 값. _ 는 오직 가독성을 위한 표현.
        for (l, s) in line_shifts:
            total_produced = pulp.lpSum(x[(m, l, s)] for m in items)
            model += (total_produced <= BIG_M * y[(l, s)],f'constraint5-1 ({l},{s})')
            model += (y[(l, s)] <= total_produced ,f'constraint5-2 ({l},{s})')
            
        blocks = list(set(l[0] for l in self.line)) # 제조동 리스트 ['I','D','K','M']

        # for (l, s) in line_shifts:
        #     print(f"y[{(l, s)}]:", type(y[(l, s)]))


        for b in blocks:
            for shift in self.time:
                series = self.df_capa_qty.loc[self.df_capa_qty['Line'] == f"Max_line_{b}", shift]
                max_line = int(series.values[0]) if pd.notna(series.values[0]) else 100
                model += (pulp.lpSum(
                    y[(l, s)] for (l, s) in line_shifts if l.startswith(b) and s == shift
                ) <= max_line,f'constraint5-3,({b},{shift})')

        # 제약조건 6: 각 (제조동 * 시프트) 별 최대 생산 수량. capa_qty 시트와 관련됨. Max_qty
        for b in blocks:
            for shift in self.time:
                series = self.df_capa_qty.loc[self.df_capa_qty['Line'] == f"Max_qty_{b}", shift]
                max_qty = int(series.values[0]) if pd.notna(series.values[0]) else 10_000_000
                model += (pulp.lpSum(
                    x[(m, l, s)] for m in items for (l, s) in line_shifts if l.startswith(b) and s == shift
                ) <= max_qty,f'constraint6 ({b},{shift})')

        # 최적화
        model.solve()

        # 결과 저장 & 출력
        results = []
        if showlog: print(y.values())
        for (l, s) in line_shifts:
            if showlog: print(f"{l} - {s} 시프트:")
            for m in items:
                units = int(pulp.value(x[(m, l, s)]))
                if units > 0:
                    if showlog: print(f"  모델 {m} → {units}개 생산")
                    # 아이템의 SOP 와 MFG 값은 demand 시트에서 참조, due_LT 값은 due_LT 시트에서 참조
                    # 해야 하지만 사전할당에서 To_site 값까지 입력하지 않기 때문에 임의 값으로 넣어놓고 추후 생각해보겠음.
                    sop = -99
                    mfg = -99
                    due_lt= -99
                    to_site = "XX"
                    results.append((l,s,m+to_site,m,units,m[3:7],to_site,sop,mfg,m[3:11],due_lt)) 
                    
        # 제조동별 생산량
        total_production = pulp.value(pulp.lpSum([x[(m, l, s)] for (m, l, s) in x]))
        for (idx,row) in self.df_capa_portion.iterrows():
            line_production =pulp.value(pulp.lpSum([x[(m, l, s)] for (m, l, s) in x if l.startswith(row['name'])]))
            line_ratio = (line_production / total_production) * 100 if total_production != 0 else 0
            print(f"{row['name']}라인 생산량:{int(line_production)}개, {row['name']}라인 비중: {line_ratio:.2f}%")

        self.df_pre_result = pd.DataFrame(results,columns=['Line','Time','Demand','Item','Qty','Project','To_site','SOP','MFG','RMC','Due_LT'])
        print(self.df_pre_result)
        #주어진 수요량을 모두 생산 가능하면 해를 찾은 것

        if pulp.LpStatus[model.status] == 'Optimal':
            if int(pulp.value(model.objective)) == sum(demand.values()):
                print(f"\n최적해를 찾았습니다")
                print(f"\n총 생산량: {int(pulp.value(model.objective))}개")
                print(f"\n총 생산 수요량: {sum(demand.values())}개")
            else:
                print("❌ 최적해를 찾지 못했습니다.")
                print(f"\n총 생산 수요량: {sum(demand.values())}")
                print(f"\n총 생산량: {int(pulp.value(model.objective))}개")
                print(f"\n미할당량: {sum(demand.values())-int(pulp.value(model.objective))}개")
                if showlog:
                    for item in y.values():     
                        print(item, item.varValue)
                if showlog:
                    for name, constraint in model.constraints.items():
                        slack_value = constraint.slack
                        if slack_value is not None and slack_value < 0:
                            print(slack_value)
                            print(f"제약조건 '{name}'이 위배됨: slack = {slack_value}")
                            print(f"제약조건: {constraint}")
                return {'result':self.df_pre_result ,'error':f"❌ 최적해를 찾지 못했습니다."}
        else:
            print(f"❌ 모델 최적화 실패: {pulp.LpStatus[model.status]}")
        if showlog:print(pulp.value(model.objective))
        if showlog:
            for name, constraint in model.constraints.items():
                slack_value = constraint.slack
                if slack_value is not None and slack_value < 0:
                    print("=" * 80)
                    print(f"❗ 제약조건 '{name}' 위배: slack = {slack_value}")
                    print(f"제약식 원본: {constraint}")
                    print(f"좌변(lhs) 값: {constraint.value()}")  # 실제 계산된 좌변 값
                    print(f"우변(rhs): {constraint.constant}")  # 우변 값 (우변에 있는 상수)
                    print(f"연산자: {constraint.sense}")  # -1: <=, 0: =, 1: >=
                    
                    # 사용된 변수들의 값도 같이 출력
                    used_vars = constraint.keys()
                    print("사용된 변수 값:")
                    for var in used_vars:
                        print(f"  {var.name} = {var.varValue}")
        

        # df_pre_result.to_excel('pre_assign_result.xlsx',index=False)
        return {'result':self.df_pre_result, 'combined' : self.df_combined }

    """생산계획 최적화 알고리즘 함수"""
    def execute(self,showlog = False):
        # 아이템에 To_site 까지 포함해서 아이템의 단위로 설정 (출하 capa를 목적함수에 포함시키기 위함)
        # 반면에 사전할당은 To_site 미포함
        items = self.df_demand['Item'].tolist()
        line_shifts = [(l,s) for l in self.line for s in self.time]
        demand = dict(zip(self.df_demand['Item'], self.df_demand['MFG']))
        capacity = {(l,s):int(self.df_capa_qty.loc[self.df_capa_qty['Line'] == l, s].values[0]) for (l, s) in line_shifts}

        allowed_items = {}
        for l, s in line_shifts:
            if l not in self.df_line_available.columns:
                print(f"라인 {l}는 line_available에 존재하지 않습니다.")
                continue
            # line_available에서 값이 1 인 프로젝트들의 리스트
            projects = self.df_line_available[self.df_line_available[l] == 1]['Project'].tolist()
            allowed = [m for m in items if any(m[3:7] == project for project in projects)]
            allowed_items[(l, s)] = allowed

        # 결정 변수 x : 모델 m을 라인 l, 시프트 s에서 몇 개 생산할지의 딕셔너리
        x = pulp.LpVariable.dicts("produce", [(m, l, s) for m in items for (l, s) in line_shifts], lowBound=0, cat='Integer')
        # 문제 정의
        model = pulp.LpProblem("LineShift_Production_Scheduling", pulp.LpMaximize)
        
        # 목적함수: 총 생산량 최대화 (추후 지표 8가지를 최적화 하는 목적함수로 수정 예정)
        model += pulp.lpSum([x[(m, l, s)] for m in items for (l, s) in line_shifts])

        # 제약조건 0: 사전할당 결과가 있다면 그 결과를 제약조건에 포함시켜서 고정
        if self.df_pre_result is not None:
            for idx,row in self.df_pre_result.iterrows():
                if (row['Item'], row['Line'], row['Time']) in x:
                    model += x[(row['Item'], row['Line'], row['Time'])] == row['Qty']

        # 제약조건 1: 모델별 수요량 보다 적게 생산. 꼭 모든 수요를 만족시키지 않아도 됨. demand 시트와 관련됨. 
        for m in items:
            model += pulp.lpSum([x[(m, l, s)] for (l, s) in line_shifts]) <= demand[m]

        # 제약조건 2: 라인/시프트에서 생산 가능한 모델만 허용. line_available 시트와 관련됨.
        for (l, s) in line_shifts:
            for m in items:
                if m not in allowed_items.get((l, s), []):
                    model += x[(m, l, s)] == 0

        # 제약조건 3: 제조동별 물량 비중 상한/하한. capa_portion 시트와 관련됨.
        for (ids,row) in self.df_capa_portion.iterrows():
            model += (
               row['upper_limit'] * pulp.lpSum([x[(m, l, s)] for (m, l, s) in x]) >=
               pulp.lpSum([x[(m, l, s)] for (m, l, s) in x if l.startswith(row['name'])])
            )
            model += (
                pulp.lpSum([x[(m, l, s)] for (m, l, s) in x if l.startswith(row['name'])]) >=
                row['lower_limit'] * pulp.lpSum([x[(m, l, s)] for (m, l, s) in x])
            )

        # 제약조건 4: 각 라인/시프트 조합의 최대 생산량 제한. capa_qty 시트와 관련됨.
        for (l, s) in line_shifts:
            model += pulp.lpSum([x[(m, l, s)] for m in items]) <= capacity[(l, s)]
        
        # 제약조건 5: 각 (제조동 * 시프트) 별 가동가능한 최대 라인 수. capa_qty 시트와 관련됨. Max_line
        # 결정변수 y 추가. y 는 각 (라인 * 시프트) 를 키값으로, 그 (라인*시프트) 가 가동중이면 1, 아니면 0 을 value 값으로 갖는 pulp 딕셔너리
        y = pulp.LpVariable.dicts("line_shift_active", line_shifts, cat="Binary")
        # 특정 y[(l,s)] 가 1이면 그 (라인*시프트) 에서 생산되는 모델이 적어도 1개는 있다는 뜻.반대로 0이면 하나도 없다는 뜻.
        BIG_M = 10_000_000  # 충분히 큰 값. _ 는 오직 가독성을 위한 표현.
        for (l, s) in line_shifts:
            total_produced = pulp.lpSum(x[(m, l, s)] for m in items)
            model += total_produced <= BIG_M * y[(l, s)]
            model += total_produced >= 1 * y[(l, s)]  
            
        blocks = list(set(l[0] for l in self.line)) # 제조동 리스트 ['I','D','K','M']

        for b in blocks:
            for shift in self.time:
                series = self.df_capa_qty.loc[self.df_capa_qty['Line'] == f"Max_line_{b}", shift]
                max_line = int(series.values[0]) if pd.notna(series.values[0]) else 100
                model += pulp.lpSum(
                    y[(l, s)] for (l, s) in line_shifts if l.startswith(b) and s == shift
                ) <= max_line

        # 제약조건 6: 각 (제조동 * 시프트) 별 최대 생산 수량. capa_qty 시트와 관련됨. Max_qty
        for b in blocks:
            for shift in self.time:
                series = self.df_capa_qty.loc[self.df_capa_qty['Line'] == f"Max_qty_{b}", shift]
                max_qty = int(series.values[0]) if pd.notna(series.values[0]) else 10_000_000
                model += pulp.lpSum(
                    x[(m, l, s)] for m in items for (l, s) in line_shifts if l.startswith(b) and s == shift
                ) <= max_qty

        # 최적화
        model.solve()

        # 결과 출력
        results = []
        for (l, s) in line_shifts:
            if showlog: print(f"{l} - {s} 시프트:")
            for m in items:
                units = int(pulp.value(x[(m, l, s)]))
                if units > 0:
                    if showlog: print(f"  모델 {m} → {units}개 생산")
                    # 아이템의 SOP 와 MFG 값은 demand 시트에서 참조, due_LT 값은 due_LT 시트에서 참조
                    sop = -99
                    mfg = -99
                    due_lt = -99
                    to_site = "XX"
                    # sop = self.df_demand.loc[(self.df_demand['Item']==m[:-2])&(self.df_demand['To_Site']==m[-2:]),'SOP'].values[0]
                    # mfg = self.df_demand.loc[(self.df_demand['Item']==m[:-2])&(self.df_demand['To_Site']==m[-2:]),'MFG'].values[0]
                    # due_lt= self.df_due_LT.loc[(self.df_due_LT['Project']==m[3:7])&(self.df_due_LT['Tosite_group']==m[7:8]),'Due_date_LT'].values[0]
                    results.append((l,s,m+to_site,m,units,m[3:7],to_site,sop,mfg,m[3:11],due_lt)) 
        print(f"\n총 생산량: {int(pulp.value(model.objective))}개")
        # 제조동별 생산량
        total_production = pulp.value(pulp.lpSum([x[(m, l, s)] for (m, l, s) in x]))
        for (idx,row) in self.df_capa_portion.iterrows():
            line_production =pulp.value(pulp.lpSum([x[(m, l, s)] for (m, l, s) in x if l.startswith(row['name'])]))
            line_ratio = (line_production / total_production) * 100 if total_production != 0 else 0
            print(f"{row['name']}라인 생산량: {int(line_production)}개, {row['name']}라인 비중: {line_ratio:.2f}%")

        df_result = pd.DataFrame(results,columns=['Line','Time','Demand','Item','Qty','Project','To_site','SOP','MFG','RMC','Due_LT'])
        print(df_result)
        return {'result':self.df_result, 'combined' : self.df_combined }
    


if __name__ == "__main__":
    input = {
        'demand': pd.read_excel('ssafy_demand_0507.xlsx',sheet_name=None),
        'master': pd.read_excel('ssafy_master_0507.xlsx',sheet_name=None),
        'dynamic': pd.read_excel('ssafy_dynamic_0507.xlsx',sheet_name=None),
    }

    optimization = Optimization(input)
    optimization.pre_assign()