import pandas as pd
from app.models.master_data import MasterDataManager
from app.core.scheduler import APSScheduler
from datetime import datetime

# 마스터 데이터 로드
master_data = MasterDataManager()
print(f"Loaded {len(master_data.products)} products")

# 판매계획 로드
sales_plan_path = "C:/MYCLAUDE_PROJECT/NEW_APS/data/samples/sales_plan_ginexin_202502.xlsx"
sales_df = pd.read_excel(sales_plan_path)

# 데이터 형식 변환
sales_df['제품코드'] = sales_df['제품코드'].astype(str)
sales_df['제조번호'] = sales_df['제조번호'].astype(str)

print("\n판매계획 데이터:")
print(sales_df.head())

# 스케줄러 생성
scheduler = APSScheduler(master_data)

# 스케줄 생성
start_date = datetime(2025, 2, 1)
print(f"\n스케줄 생성 시작 (시작일: {start_date})")

try:
    plan = scheduler.schedule_from_sales_plan(sales_df, start_date)
    print(f"\n생성된 배치 수: {len(plan.batches)}")
    
    # 첫 5개 배치 정보 출력
    for i, (batch_id, batch) in enumerate(list(plan.batches.items())[:5]):
        print(f"\n배치 {i+1}:")
        print(f"  - ID: {batch.id}")
        print(f"  - 제품: {batch.product_name}")
        print(f"  - 장비: {batch.equipment_id}")
        print(f"  - 시작: {batch.start_time}")
        print(f"  - 제조번호: {batch.lot_number}")
        
except Exception as e:
    print(f"\n에러 발생: {e}")
    import traceback
    traceback.print_exc()