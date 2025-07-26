import pandas as pd

# 작업자 샘플 데이터 확인
file_path = "C:/MYCLAUDE_PROJECT/NEW_APS/data/samples/operators_sample.xlsx"
df = pd.read_excel(file_path)

print("작업자 샘플 데이터")
print("=" * 80)
print(f"\n컬럼: {df.columns.tolist()}")
print(f"\n총 레코드 수: {len(df)}")

# 날짜별 요약
print("\n날짜별 작업자 수:")
date_summary = df.groupby('날짜')['작업자수'].sum()
print(date_summary.head(5))

# 공정별 평균 작업자 수
print("\n공정별 평균 작업자 수:")
process_summary = df.groupby(['공정ID', '공정명'])['작업자수'].mean()
print(process_summary)

# 첫 10개 데이터 표시
print("\n첫 10개 데이터:")
print(df.head(10))