"""
백업 관리 유틸리티
마스터 데이터 백업 및 복원 기능
"""
import os
import json
import shutil
from datetime import datetime
from typing import Dict, List


class BackupManager:
    """백업 관리 클래스"""
    
    def __init__(self, data_dir: str = "data/masters", backup_dir: str = "data/backups"):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, backup_name: str = None) -> str:
        """현재 마스터 데이터 백업 생성"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        # 모든 JSON 파일 복사
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                src = os.path.join(self.data_dir, filename)
                dst = os.path.join(backup_path, filename)
                shutil.copy2(src, dst)
        
        # 백업 정보 저장
        info = {
            'name': backup_name,
            'created_at': datetime.now().isoformat(),
            'files': os.listdir(backup_path)
        }
        
        with open(os.path.join(backup_path, 'backup_info.json'), 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        return backup_path
    
    def restore_backup(self, backup_name: str) -> bool:
        """백업에서 마스터 데이터 복원"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            raise ValueError(f"백업을 찾을 수 없습니다: {backup_name}")
        
        # 현재 데이터 백업 (안전을 위해)
        self.create_backup("before_restore_" + datetime.now().strftime('%Y%m%d_%H%M%S'))
        
        # 백업 파일 복원
        for filename in os.listdir(backup_path):
            if filename.endswith('.json') and filename != 'backup_info.json':
                src = os.path.join(backup_path, filename)
                dst = os.path.join(self.data_dir, filename)
                shutil.copy2(src, dst)
        
        return True
    
    def list_backups(self) -> List[Dict]:
        """사용 가능한 백업 목록"""
        backups = []
        
        for backup_name in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, backup_name)
            if os.path.isdir(backup_path):
                info_path = os.path.join(backup_path, 'backup_info.json')
                if os.path.exists(info_path):
                    with open(info_path, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                        backups.append(info)
        
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)
    
    def delete_backup(self, backup_name: str) -> bool:
        """백업 삭제"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
            return True
        
        return False
    
    def export_to_file(self, export_path: str) -> bool:
        """마스터 데이터를 단일 파일로 내보내기"""
        all_data = {}
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                    data_type = filename.replace('.json', '')
                    all_data[data_type] = json.load(f)
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        return True
    
    def import_from_file(self, import_path: str) -> bool:
        """단일 파일에서 마스터 데이터 가져오기"""
        with open(import_path, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        # 현재 데이터 백업
        self.create_backup("before_import_" + datetime.now().strftime('%Y%m%d_%H%M%S'))
        
        # 데이터 복원
        for data_type, data in all_data.items():
            file_path = os.path.join(self.data_dir, f"{data_type}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True