from app.models.master_data import MasterDataManager

# 마스터 데이터 로드 테스트
master_data = MasterDataManager()

print(f"\n제품 데이터: {len(master_data.products)}개")
for key, product in list(master_data.products.items())[:3]:
    print(f"  - {product['id']}: {product['name']}")

print(f"\n공정 데이터: {len(master_data.processes)}개")
for key, process in list(master_data.processes.items())[:3]:
    print(f"  - {process['id']}: {process['name']}")

print(f"\n장비 데이터: {len(master_data.equipment)}개")
for key, equipment in list(master_data.equipment.items())[:3]:
    print(f"  - {equipment['id']}: {equipment['name']}")