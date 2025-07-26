import fnmatch
import pulp
from pulp import PULP_CBC_CMD

from typing import Tuple, List

import pandas as pd
import numpy as np

df_opts = {
    'display.max_columns': None,
    'display.max_rows': None,
    'display.width': 0,
    'display.expand_frame_repr': False
}
for k, v in df_opts.items():
    pd.set_option(k, v)

from ...models.input.pre_assign import PreAssignFailures, DataLoader

"""dynamic, demand, master 데이터를 로드"""
def load_data():
    # dynamic 데이터
    try:
        fixed_opt, pre_assign = DataLoader.load_dynamic_data()
    except Exception as e:
        print(f"[load_data] load_dynamic_data 에러: {e}")
        fixed_opt, pre_assign = pd.DataFrame(), pd.DataFrame()

    # demand 데이터
    try:
        demand = DataLoader.load_demand_data()
    except Exception as e:
        print(f"[load_data] load_demand_data 에러: {e}")
        demand = pd.DataFrame(columns=['Item', 'MFG'])

    # master 데이터
    try:
        line_avail, capa_qty = DataLoader.load_master_data()
    except Exception as e:
        print(f"[load_data] load_master_data 에러: {e}")
        line_avail, capa_qty = pd.DataFrame(), pd.DataFrame()

    if not capa_qty.empty and 'Line' in capa_qty.columns:
        capa_qty = capa_qty.set_index('Line')
    else:
        capa_qty = pd.DataFrame()
    return fixed_opt, pre_assign, demand, line_avail, capa_qty

"""pre_assign 데이터 fixed_option 이동"""
def expand_pre_assign(fixed_opt: pd.DataFrame, pre_assign: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in pre_assign.iterrows():
        line  = row['Line']
        shift = row['Shift']
        for k in range(1, 8):
            item, qty = row[f'Item{k}'], row[f'Qty{k}']
            t = (k - 1) * 2 + shift
            if pd.isna(item) and pd.isna(qty):
                continue

            if pd.isna(item) or pd.isna(qty):
                records.append({
                    'Fixed_Group': item,
                    'Fixed_Line' : [row['Line']],
                    'Fixed_Time' : [t],
                    'Qty'        : qty
                })
                continue

            exact_mask = (
                fixed_opt['Qty'].notna()
                & (fixed_opt['Fixed_Group'] == item)
                & fixed_opt['Fixed_Line'].apply(lambda lst: line in lst)
                & fixed_opt['Fixed_Time'].apply(lambda lst: t    in lst)
            )
            fixed_exact = fixed_opt[exact_mask]['Qty'].sum()

            remaining1 = float(qty) - float(fixed_exact)
            if remaining1 <= 0:
                continue

            wc_mask = (
                fixed_opt['Qty'].notna()
                & fixed_opt['Fixed_Group'].notna()
                & fixed_opt['Fixed_Group']
                    .apply(lambda pat: isinstance(pat, str) and fnmatch.fnmatch(item, pat))
                & ~exact_mask
                & fixed_opt['Fixed_Line'].apply(lambda lst: line in lst)
                & fixed_opt['Fixed_Time'].apply(lambda lst: t    in lst)
            )
            fixed_wild = fixed_opt[wc_mask]['Qty'].sum()

            remaining2 = remaining1 - float(fixed_wild)
            if remaining2 <= 0:
                continue

            records.append({
                'Fixed_Group': item,
                'Fixed_Line' : [row['Line']],
                'Fixed_Time' : [t],
                'Qty'        : remaining2
            })
    return pd.concat([fixed_opt, pd.DataFrame(records)], ignore_index=True, sort=False)

"""Fixed_Line이 NaN인 경우 사용 가능한 모든 라인으로 대체"""
def fill_missing_lines(fixed_opt: pd.DataFrame, line_available: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in fixed_opt.iterrows():
        fl = row.get('Fixed_Line')
        if pd.isna(fl):
            proj_code = row['Fixed_Group'][3:7]
            avail = line_available[line_available['Project'] == proj_code]
            if not avail.empty:
                cols = [col for col, val in avail.iloc[0].items() if col != 'Project' and val == 1]
                new_line = cols
            else:
                new_line = []
        else:
            if isinstance(fl, str) and ',' in fl:
                new_line = [x.strip() for x in fl.split(',') if x.strip()]
            else:
                new_line = [fl]
        new_row = row.copy()
        new_row['Fixed_Line'] = new_line
        records.append(new_row)
    return pd.DataFrame(records, columns=fixed_opt.columns)

"""Fixed_Line 검증"""
def validate_fixed_option_lines(
    fixed_opt: pd.DataFrame,
    line_available: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    valid_rows = []
    invalid_rows = []

    for _, row in fixed_opt.iterrows():
        lines = row['Fixed_Line']
        group = row['Fixed_Group']
        proj = group[3:7] if isinstance(group, str) and len(group) >= 7 else None

        valid_lines: List[str] = []
        if proj and not line_available.empty:
            sub = line_available[line_available['Project'] == proj]
            if not sub.empty:
                valid_lines = [
                    col for col, flag in sub.iloc[0].items()
                    if col != 'Project' and flag == 1
                ]

        if any(ln not in valid_lines for ln in lines):
            invalid_rows.append(row)
        else:
            valid_rows.append(row)

    valid_fx   = pd.DataFrame(valid_rows,   columns=fixed_opt.columns)
    invalid_fx = pd.DataFrame(invalid_rows, columns=fixed_opt.columns)
    return valid_fx, invalid_fx

"""Fixed_Time이 NaN인 경우 모든 시프트로 대체"""
def fill_missing_times(fixed_opt: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in fixed_opt.iterrows():
        ft = row.get('Fixed_Time')
        if pd.isna(ft):
            new_val = list(range(1, 15))
        elif isinstance(ft, str) and ',' in ft:
            new_val = [int(x.strip()) for x in ft.split(',') if x.strip().isdigit()]
        else:
            try:
                new_val = [int(ft)]
            except:
                new_val = []
        new_row = row.copy()
        new_row['Fixed_Time'] = new_val
        records.append(new_row)
    return pd.DataFrame(records, columns=fixed_opt.columns)

"""Qty == 'ALL'일 때 demand 합계로 대체"""
def process_all_qty(fixed_opt: pd.DataFrame, demand: pd.DataFrame) -> pd.DataFrame:
    def resolve_qty(qg, fixed_group):
        if isinstance(qg, str) and qg.strip().lower() == 'all':
            pat = fixed_group
            return demand.loc[
                demand['Item'].apply(lambda s: fnmatch.fnmatch(s, pat)),
                'MFG'
            ].sum()
        return qg

    new_records = []
    for _, row in fixed_opt.iterrows():
        qty_resolved = resolve_qty(row['Qty'], row['Fixed_Group'])
        new_row = row.copy()
        new_row['Qty'] = qty_resolved
        new_records.append(new_row)
    return pd.DataFrame(new_records, columns=fixed_opt.columns)

"""1번 제약사항: 라인/시프트별 생산 용량"""
def get_capacity_constraints(capa_qty: pd.DataFrame) -> pd.DataFrame:
    records = []
    for line, row in capa_qty.iterrows():
        if isinstance(line, str) and line.startswith('Max_'):
            continue
        for shift_str, cap in row.items():
            try:
                shift = int(shift_str)
            except:
                continue
            records.append({'Line': line, 'Shift': shift, 'Capacity': cap})
    return pd.DataFrame(records)


"""2번 제약사항: 그룹별 동시 가동 가능한 최대 라인 개수"""
def get_max_line_constraints(capa_qty: pd.DataFrame) -> pd.DataFrame:
    records = []
    for idx, row in capa_qty.iterrows():
        if isinstance(idx, str) and idx.startswith('Max_line_'):
            parts = idx.split('_')
            prefix = parts[-1]
            for shift_str, max_ln in row.items():
                try:
                    shift = int(shift_str)
                except:
                    continue
                max_ln_val = None if pd.isna(max_ln) else int(max_ln)
                records.append({'GroupPrefix': prefix, 'Shift': shift, 'MaxLines': max_ln_val})
    return pd.DataFrame(records)


"""3번 제약사항: 그룹별 최대 생산량"""
def get_max_qty_constraints(capa_qty: pd.DataFrame) -> pd.DataFrame:
    records = []
    for idx, row in capa_qty.iterrows():
        if isinstance(idx, str) and idx.startswith('Max_qty_'):
            parts = idx.split('_')
            prefix = parts[-1]
            for shift_str, max_q in row.items():
                try:
                    shift = int(shift_str)
                except:
                    continue
                max_q_val = None if pd.isna(max_q) else float(max_q)
                records.append({'GroupPrefix': prefix, 'Shift': shift, 'MaxQty': max_q_val})
    return pd.DataFrame(records)

"""
fixed_opt에서 에러(결측 또는 빈 리스트)인 행만 error_fx에,
나머지 정상 행은 valid_fx에 담아 반환
"""
def extract_error_records(fx: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    def is_bad(val):
        if isinstance(val, (list, np.ndarray)):
            return len(val) == 0
        return pd.isna(val)
    
    mask_group = fx['Fixed_Group'].apply(is_bad)
    mask_line = fx['Fixed_Line'].apply(is_bad)
    mask_time = fx['Fixed_Time'].apply(is_bad)
    mask_qty = fx['Qty'].apply(is_bad)

    mask_error = mask_group | mask_line | mask_time | mask_qty
    error_fx = fx[mask_error].copy()
    valid_fx = fx[~mask_error].copy()
    return valid_fx, error_fx

"""1번 제약조건 검사: 요청량(Qty)이 설비용량 합(Capacity)보다 초과하는지 확인"""
def check_capacity_violations(
    fx: pd.DataFrame,
    cap: pd.DataFrame
) -> pd.DataFrame:
    # 요청별로 가능한 모든 (라인, 교대) 조합을 준비합니다.
    combos = {
        r: [(ln, sh)
            for ln in fx.at[r, 'Fixed_Line']
            for sh in fx.at[r, 'Fixed_Time']]
        for r in fx.index
    }

    # 용량 조회를 위한 (라인, 교대) -> 용량 딕셔너리를 만듭니다.
    cap_dict = cap.set_index(['Line','Shift'])['Capacity'].to_dict()

    # 최적화 문제를 생성하고, 슬랙 최소화를 목표로 설정합니다.
    prob = pulp.LpProblem("CapacityCheck", pulp.LpMinimize)

    # 각 요청·조합별 할당량 변수와, 요청별 미할당량 슬랙 변수를 선언합니다.
    x_vars = {
        (r, ln, sh): pulp.LpVariable(f"x_{r}_{ln}_{sh}", lowBound=0)
        for r, cmb in combos.items()
        for ln, sh in cmb
    }
    slack = {
        r: pulp.LpVariable(f"s_req_{r}", lowBound=0)
        for r in fx.index
    }

    # 모든 요청의 미할당량 합을 최소화하도록 목적식을 추가합니다.
    prob += pulp.lpSum(slack[r] for r in fx.index)

    # 각 요청이 요구량만큼 할당되거나 슬랙으로 보완되도록 제약을 설정합니다.
    for r, cmb in combos.items():
        prob += (
            pulp.lpSum(x_vars[(r, ln, sh)] for ln, sh in cmb)
            + slack[r]
            == fx.at[r, 'Qty']
        )

    # 각 설비(라인,교대)에 대한 총 할당량이 용량을 넘지 않도록 제약을 설정합니다.
    for (ln, sh), cap_val in cap_dict.items():
        if pd.isna(cap_val):
            continue
        prob += (
            pulp.lpSum(x_vars.get((r, ln, sh), 0) for r in fx.index)
            <= cap_val
        )

    # 최적화를 실행합니다.
    prob.solve(PULP_CBC_CMD(msg=True))

    # 슬랙이 발생한 요청에 대해, 해당 요청의 모든 조합별로 SlackQty를 기록합니다.
    records = []
    for r in fx.index:
        slack_val = slack[r].varValue or 0
        if slack_val > 1e-6:
            for ln, sh in combos[r]:
                records.append({
                    'Line':     ln,
                    'Shift':    sh,
                    'Capacity': cap_dict.get((ln, sh)),
                    'SlackQty': slack_val
                })

    return pd.DataFrame(records)

"""2번 제약조건 검사: 그룹별 동시 가동 가능한 최대 라인 수(MaxLines)를 초과하는지 확인"""
def check_max_line_violations(
    fx: pd.DataFrame,
    max_lines: pd.DataFrame
) -> pd.DataFrame:
    # 요청별로 가능한 (그룹접두사, 교대) 조합을 만듭니다.
    combos = {
        r: [(ln.split('_')[0], sh)
            for ln in fx.at[r, 'Fixed_Line']
            for sh in fx.at[r, 'Fixed_Time']]
        for r in fx.index
    }

    # 그룹별·교대별 최대 라인 수 딕셔너리로 변환합니다.
    ml_dict = max_lines.set_index(['GroupPrefix','Shift'])['MaxLines'].to_dict()

    # 목적함수에 슬랙 최소화를 설정한 최적화 문제를 생성합니다.
    prob = pulp.LpProblem("MaxLineCheck", pulp.LpMinimize)

    # 조합 선택 변수와 각 (그룹,교대)별 초과 슬랙 변수를 선언합니다.
    z_vars = {
        (r, p, sh): pulp.LpVariable(f"z_{r}_{p}_{sh}", cat="Binary")
        for r, cmb in combos.items()
        for p, sh in cmb
    }
    slack = {
        (p, sh): pulp.LpVariable(f"s_line_{p}_{sh}", lowBound=0)
        for (p, sh), max_ln in ml_dict.items()
        if pd.notna(max_ln)
    }

    # 모든 슬랙의 합을 최소화하도록 목적식을 설정합니다.
    prob += pulp.lpSum(slack.values())

    # 각 요청은 반드시 하나의 (그룹,교대) 조합을 선택하도록 제약합니다.
    for r in fx.index:
        prob += pulp.lpSum(z_vars[(r, p, sh)] for p, sh in combos[r]) == 1

    # 그룹별 동시 가동 라인 수 제약: 초과 시 슬랙변수로 보완합니다.
    for (p, sh), max_ln in ml_dict.items():
        if pd.isna(max_ln):
            continue
        prob += (
            pulp.lpSum(z_vars.get((r, p, sh), 0) for r in fx.index)
            <= max_ln + slack[(p, sh)]
        )

    # 최적화를 실행합니다.
    prob.solve(PULP_CBC_CMD(msg=True))

    # 슬랙이 발생한 (그룹,교대)별로 SlackCount를 기록합니다.
    records = []
    for (p, sh), var in slack.items():
        val = var.varValue or 0
        if val > 1e-6:
            records.append({
                'GroupPrefix': p,
                'Shift':       sh,
                'MaxLines':    ml_dict[(p, sh)],
                'SlackCount':  val
            })

    return pd.DataFrame(records)

"""3번 제약조건 검사: 그룹별 최대 생산량(MaxQty)을 초과하는지 확인"""
def check_max_qty_violations(
    fx: pd.DataFrame,
    max_qtys: pd.DataFrame
) -> pd.DataFrame:
    # 요청별로 가능한 (그룹접두사, 교대) 조합을 생성합니다.
    combos = {
        r: [(ln.split('_')[0], sh)
            for ln in fx.at[r, 'Fixed_Line']
            for sh in fx.at[r, 'Fixed_Time']]
        for r in fx.index
    }

    # 그룹별·교대별 최대 생산량 딕셔너리로 변환합니다.
    mq_dict = max_qtys.set_index(['GroupPrefix','Shift'])['MaxQty'].to_dict()

    # 슬랙 최소화를 목표로 한 최적화 문제를 생성합니다.
    prob = pulp.LpProblem("MaxQtyCheck", pulp.LpMinimize)

    # 조합 선택 변수와 초과 슬랙 변수를 선언합니다.
    z_vars = {
        (r, p, sh): pulp.LpVariable(f"z_{r}_{p}_{sh}", cat="Binary")
        for r, cmb in combos.items()
        for p, sh in cmb
    }
    slack = {
        (p, sh): pulp.LpVariable(f"s_qty_{p}_{sh}", lowBound=0)
        for (p, sh), max_q in mq_dict.items()
        if pd.notna(max_q)
    }

    # 모든 슬랙의 합을 최소화하도록 목적식을 설정합니다.
    prob += pulp.lpSum(slack.values())

    # 각 요청은 반드시 하나의 (그룹,교대) 조합을 선택하도록 제약합니다.
    for r in fx.index:
        prob += pulp.lpSum(z_vars[(r, p, sh)] for p, sh in combos[r]) == 1

    # 그룹별 최대 생산량 제약: 생산 수량을 곱해 합산하고, 초과 시 슬랙으로 보완합니다.
    for (p, sh), max_q in mq_dict.items():
        if pd.isna(max_q):
            continue
        prob += (
            pulp.lpSum(
                z_vars.get((r, p, sh), 0) * fx.at[r, 'Qty']
                for r in fx.index
            )
            <= max_q + slack[(p, sh)]
        )

    # 최적화를 실행합니다.
    prob.solve(PULP_CBC_CMD(msg=True))

    # 슬랙이 발생한 (그룹,교대)별로 SlackQty를 기록합니다.
    records = []
    for (p, sh), var in slack.items():
        val = var.varValue or 0
        if val > 1e-6:
            records.append({
                'GroupPrefix': p,
                'Shift':       sh,
                'MaxQty':      mq_dict[(p, sh)],
                'SlackQty':    val
            })

    return pd.DataFrame(records)

"""모든 제약조건(Capacity, MaxLine, MaxQty)을 동시에 검사하여 위반 제약을 반환합니다."""
def check_all_violations(
    fx: pd.DataFrame,
    cap: pd.DataFrame,
    max_lines: pd.DataFrame,
    max_qtys: pd.DataFrame
) -> pd.DataFrame:
    fx['Qty'] = pd.to_numeric(fx['Qty'], errors='coerce').fillna(0)
    
    # 가능한 모든 (라인, 교대) 조합을 준비합니다.
    combos = {
        r: [(ln, sh)
            for ln in fx.at[r, 'Fixed_Line']
            for sh in fx.at[r, 'Fixed_Time']]
        for r in fx.index
    }

    # 제약치 조회용 딕셔너리를 생성합니다.
    cap_dict = cap.set_index(['Line','Shift'])['Capacity'].to_dict()
    ml_dict  = max_lines.set_index(['GroupPrefix','Shift'])['MaxLines'].to_dict()
    mq_dict  = max_qtys.set_index(['GroupPrefix','Shift'])['MaxQty'].to_dict()

    # MILP 모델 생성 (모든 슬랙 최소화)
    prob = pulp.LpProblem("AllConstraintsCheck", pulp.LpMinimize)

    # 분할 할당을 위한 연속 변수 x_vars[(r,ln,sh)] ≥ 0
    x_vars = {
        (r, ln, sh): pulp.LpVariable(f"x_{r}_{ln}_{sh}", lowBound=0)
        for r, cmb in combos.items()
        for ln, sh in cmb
    }

    # Capacity 초과 슬랙 변수
    s_cap = {
        (ln, sh): pulp.LpVariable(f"s_cap_{ln}_{sh}", lowBound=0)
        for (ln, sh) in cap_dict
    }
    # MaxLine 초과 슬랙 변수 (제약 없는 항목은 제외)
    s_line = {
        (p, sh): pulp.LpVariable(f"s_line_{p}_{sh}", lowBound=0)
        for (p, sh), v in ml_dict.items() if pd.notna(v)
    }
    # MaxQty 초과 슬랙 변수 (제약 없는 항목은 제외)
    s_qty = {
        (p, sh): pulp.LpVariable(f"s_qty_{p}_{sh}", lowBound=0)
        for (p, sh), v in mq_dict.items() if pd.notna(v)
    }

    # MaxLine 활성화를 위한 이진변수 y_vars[(r,ln,sh)] 과 라인·교대별 활성화 z_line[(ln,sh)]
    M   = fx['Qty'].sum()
    eps = 1e-6
    y_vars  = {}
    z_line  = {}
    for r, cmb in combos.items():
        for ln, sh in cmb:
            # 요청별 활성화 여부
            y = pulp.LpVariable(f"y_{r}_{ln}_{sh}", cat="Binary")
            y_vars[(r, ln, sh)] = y
            # 라인·교대별 활성화 여부
            if (ln, sh) not in z_line:
                z_line[(ln, sh)] = pulp.LpVariable(f"z_line_{ln}_{sh}", cat="Binary")
            # Big-M 연계제약
            prob += x_vars[(r, ln, sh)] <= M * y
            prob += x_vars[(r, ln, sh)] >= eps * y
            # y_vars ≤ z_line (same ln,sh 그룹화)
            prob += y <= z_line[(ln, sh)]

    # 목적식: Capacity, MaxLine, MaxQty 슬랙만 최소화
    prob += (
        pulp.lpSum(s_cap.values()) +
        pulp.lpSum(s_line.values()) +
        pulp.lpSum(s_qty.values())
    )

    # 요청량 제약: 분할 할당 합 == Qty
    for r, cmb in combos.items():
        prob += (
            pulp.lpSum(x_vars[(r, ln, sh)] for ln, sh in cmb)
            == fx.at[r, 'Qty']
        )

    # Capacity 제약: 각 (라인,교대)별 할당합 ≤ Capacity + s_cap
    for (ln, sh), cap_val in cap_dict.items():
        if pd.isna(cap_val):
            continue
        prob += (
            pulp.lpSum(x_vars.get((r, ln, sh), 0) for r in fx.index)
            <= cap_val + s_cap[(ln, sh)]
        )

    # MaxLine 제약: 서로 다른 라인 z_line 합 ≤ MaxLines + s_line
    for (p, sh), max_ln in ml_dict.items():
        if pd.isna(max_ln):
            continue
        prob += (
            pulp.lpSum(
                z_line[(ln, ss)]
                for (ln, ss) in z_line
                if ln.split('_')[0] == p and ss == sh
            )
            <= max_ln + s_line[(p, sh)]
        )

    # MaxQty 제약: 할당량 합 ≤ MaxQty + s_qty
    for (p, sh), max_q in mq_dict.items():
        if pd.isna(max_q):
            continue
        prob += (
            pulp.lpSum(
                x_vars.get((r, ln, ss), 0) * fx.at[r, 'Qty']
                for r in fx.index
                for ln, ss in combos[r]
                if ln.split('_')[0] == p and ss == sh
            )
            <= max_q + s_qty[(p, sh)]
        )

    # 최적화 실행
    prob.solve(PULP_CBC_CMD(msg=True))

    # 발생한 슬랙을 모두 모아 테이블로 반환
    records = []
    for (ln, sh), var in s_cap.items():
        v = var.varValue or 0
        if v > 1e-6:
            records.append({
                'Constraint':   'Capacity',
                'Line(GroupPrefix)':         ln,
                'Shift':        sh,
                'Limit':        cap_dict[(ln, sh)],
                'ViolationAmt': v
            })
    for (p, sh), var in s_line.items():
        v = var.varValue or 0
        if v > 1e-6:
            records.append({
                'Constraint':   'MaxLine',
                'Line(GroupPrefix)':  p,
                'Shift':        sh,
                'Limit':        ml_dict[(p, sh)],
                'ViolationAmt': v
            })
    for (p, sh), var in s_qty.items():
        v = var.varValue or 0
        if v > 1e-6:
            records.append({
                'Constraint':   'MaxQty',
                'Line(GroupPrefix)':  p,
                'Shift':        sh,
                'Limit':        mq_dict[(p, sh)],
                'ViolationAmt': v
            })

    return pd.DataFrame(records)

"""전체 할당 실행"""
def run_allocation() -> PreAssignFailures:
    # 데이터 로드 및 전처리
    fx, pa, dm, la, cq = load_data()
    fx = fill_missing_lines(fx, la)
    fx = fill_missing_times(fx)
    fx = process_all_qty(fx, dm)
    fx = expand_pre_assign(fx, pa)

    # 결측 에러 분리
    fx, missing_fixed = extract_error_records(fx)
    fx, fx_invalid = validate_fixed_option_lines(fx, la)
    
    # 제약조건 테이블 생성
    cap = get_capacity_constraints(cq)
    max_lines = get_max_line_constraints(cq)
    max_qtys  = get_max_qty_constraints(cq)

    # 개별 검사 함수
    # bad_cap = check_capacity_violations(fx, cap)
    # bad_max_line = check_max_line_violations(fx, max_lines)
    # bad_max_qty = check_max_qty_violations(fx, max_qtys)

    # 통합 검사 함수
    violations = check_all_violations(fx, cap, max_lines, max_qtys)

    failures: PreAssignFailures = {
        'preassign': []
    }

    # 결측 에러 처리
    for _, row in missing_fixed.iterrows():
        tgt = row['Fixed_Group']
        failures['preassign'].append({
            'Target': None if pd.isna(tgt) else tgt,
            'Shift': None,
            'Reason': 'No group specified' if pd.isna(tgt) else
                'No quantity specified' if pd.isna(row['Qty']) else
                'No fixed line specified' if not row['Fixed_Line'] else
                'No fixed time specified',
            'ViolationAmt': None
        })
    
    for _, row in fx_invalid.iterrows():
        failures['preassign'].append({
            'Target':       row['Fixed_Group'],
            'Shift':        None,
            'Reason':       'Line not available',
            'ViolationAmt': None
        })

    # 제약 위반 에러 처리
    for vr in violations.to_dict('records'):
        tgt = vr.get('Line(GroupPrefix)')
        sh = vr.get('Shift')
        record = {
            'Target': tgt,
            'Shift': sh,
            'Reason': None,
            'ViolationAmt': vr['ViolationAmt']
        }
        if vr['Constraint'] == 'Capacity':
            record['Reason'] = 'equipment capacity'
        elif vr['Constraint'] == 'MaxLine':
            record['Reason'] = 'number of concurrent lines'
        elif vr['Constraint'] == 'MaxQty':
            record['Reason'] = 'maximum production quantity'

        failures['preassign'].append(record)
    return failures