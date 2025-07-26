"""
메인 컨트롤러
MVC 패턴의 컨트롤러로 모델과 뷰를 연결
"""
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from datetime import datetime, timedelta

from app.models.master_data import MasterDataManager
from app.models.production_plan import ProductionPlan, Batch
from app.core.scheduler import APSScheduler
from app.utils.file_handler import FileHandler
from app.views.schedule_grid_view import ScheduleGridView


class MainController(QObject):
    """메인 컨트롤러"""
    
    # 시그널
    schedule_generated = pyqtSignal(object)  # ProductionPlan
    schedule_updated = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.master_data = MasterDataManager()
        self.scheduler = APSScheduler(self.master_data)
        self.current_plan = None
        self.current_sales_df = None
    
    def load_sales_plan(self, file_path: str):
        """판매계획 로드"""
        try:
            # 파일 유효성 검사
            if not FileHandler.validate_sales_plan(file_path):
                raise ValueError("잘못된 판매계획 파일 형식입니다.")
            
            # 파일 읽기
            self.current_sales_df = FileHandler.read_excel(file_path)
            
            # 데이터 형식 정리
            if '제품코드' in self.current_sales_df.columns:
                self.current_sales_df['제품코드'] = self.current_sales_df['제품코드'].astype(str)
            if '제조번호' in self.current_sales_df.columns:
                self.current_sales_df['제조번호'] = self.current_sales_df['제조번호'].astype(str)
                
            return True
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            return False
    
    def generate_schedule(self, progress_callback=None):
        """스케줄 생성"""
        if self.current_sales_df is None:
            self.error_occurred.emit("먼저 판매계획을 로드해주세요.")
            return None
        
        try:
            # 시작 날짜 (다음 달 1일)
            today = datetime.now()
            if today.month == 12:
                start_date = datetime(today.year + 1, 1, 1)
            else:
                start_date = datetime(today.year, today.month + 1, 1)
            
            # 스케줄 생성
            if progress_callback:
                progress_callback(20, "판매계획 분석 중...")
            
            
            self.current_plan = self.scheduler.schedule_from_sales_plan(
                self.current_sales_df, 
                start_date
            )
            
            # 세척 기능 임시 비활성화
            # if progress_callback:
            #     progress_callback(60, "세척 블록 추가 중...")
            # 
            # # 세척 블록 추가
            # self.scheduler.add_cleaning_blocks()
            
            if progress_callback:
                progress_callback(80, "최적화 중...")
            
            # 최적화 (추후 구현)
            # self.scheduler.optimize_schedule()
            
            if progress_callback:
                progress_callback(100, "완료!")
            
            # 시그널 발생
            self.schedule_generated.emit(self.current_plan)
            
            return self.current_plan
            
        except Exception as e:
            self.error_occurred.emit(f"스케줄 생성 오류: {str(e)}")
            return None
    
    def move_batch(self, batch_id: str, new_equipment_id: str, new_date: datetime):
        """배치 이동"""
        if not self.current_plan:
            return False
        
        try:
            # 날짜를 datetime으로 변환 (시간은 오전 8시로 설정)
            new_start_time = datetime.combine(new_date, datetime.min.time()).replace(hour=8)
            
            # 중복 검사
            if self.current_plan.check_overlap(
                new_equipment_id, 
                new_start_time, 
                8,  # 기본 8시간
                exclude_batch_id=batch_id
            ):
                self.error_occurred.emit("해당 시간에 이미 다른 배치가 있습니다.")
                return False
            
            # 배치 이동
            success = self.current_plan.move_batch(
                batch_id, 
                new_equipment_id, 
                new_start_time
            )
            
            if success:
                self.schedule_updated.emit()
                return True
            else:
                self.error_occurred.emit("배치 이동에 실패했습니다.")
                return False
                
        except Exception as e:
            self.error_occurred.emit(f"배치 이동 오류: {str(e)}")
            return False
    
    def validate_batch_move(self, batch_id: str, equipment_id: str, date: datetime):
        """배치 이동 유효성 검사"""
        if not self.current_plan or batch_id not in self.current_plan.batches:
            return False, "배치를 찾을 수 없습니다."
        
        batch = self.current_plan.batches[batch_id]
        
        # 장비가 해당 제품을 생산할 수 있는지 확인
        equipment = self.master_data.equipment.get(equipment_id)
        if not equipment:
            return False, "장비를 찾을 수 없습니다."
        
        if batch.product_id not in equipment['available_products']:
            return False, f"해당 장비는 {batch.product_name}을 생산할 수 없습니다."
        
        # 장비 가용성 확인
        if not self.master_data.is_equipment_available(equipment_id, date):
            return False, "해당 날짜에 장비를 사용할 수 없습니다."
        
        # 작업자 용량 확인
        process_id = equipment['process_id']
        operator_capacity = self.master_data.get_operator_capacity(
            process_id, 
            date.strftime('%Y-%m-%d')
        )
        
        if operator_capacity > 0:
            # 해당 날짜의 공정 배치 수 계산
            batches_on_date = self.current_plan.get_batches_by_date(date)
            process_batch_count = sum(
                1 for b in batches_on_date 
                if b.process_id == process_id and b.id != batch_id
            )
            
            if process_batch_count >= operator_capacity:
                return False, f"작업자 용량 초과 (최대 {operator_capacity}개)"
        
        return True, "이동 가능"
    
    def export_schedule(self, file_path: str, format: str = 'csv'):
        """스케줄 내보내기 - 그리드에서 직접 추출"""
        # 그리드 뷰에서 현재 스케줄 추출
        if hasattr(self, 'grid_view') and self.grid_view:
            df = self.grid_view.extract_schedule_from_grid()
            
            if df.empty:
                self.error_occurred.emit("내보낼 스케줄이 없습니다.")
                return False
            
            try:
                if format == 'csv':
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                elif format == 'xlsx':
                    FileHandler.write_excel(df, file_path, "생산계획")
                elif format == 'grid':
                    # 그리드 형식으로 변환
                    pivot_df = df.pivot_table(
                        index='equipment_name',
                        columns=['date', 'start_hour'],
                        values='product_name',
                        aggfunc='first'
                    )
                    FileHandler.write_excel(pivot_df, file_path, "그리드뷰")
                else:
                    raise ValueError(f"지원하지 않는 형식: {format}")
                
                return True
            except Exception as e:
                self.error_occurred.emit(f"내보내기 오류: {str(e)}")
                return False
        
        # 그리드 뷰가 없으면 기존 방식 사용
        elif self.current_plan:
            try:
                if format == 'csv':
                    self.current_plan.export_to_csv(file_path)
                elif format == 'xml':
                    self.current_plan.export_to_xml(file_path)
                elif format == 'xlsx':
                    df = self.current_plan.to_dataframe()
                    FileHandler.write_excel(df, file_path, "생산계획")
                elif format == 'grid':
                    df = self.current_plan.to_grid_format()
                    FileHandler.write_excel(df, file_path, "그리드뷰")
                else:
                    raise ValueError(f"지원하지 않는 형식: {format}")
                
                return True
            except Exception as e:
                self.error_occurred.emit(f"내보내기 오류: {str(e)}")
                return False
        else:
            self.error_occurred.emit("내보낼 스케줄이 없습니다.")
            return False
    
    def get_schedule_summary(self):
        """스케줄 요약 정보"""
        if not self.current_plan:
            return None
        
        return self.current_plan.get_production_summary()
    
    def add_sample_operator_data(self):
        """샘플 작업자 데이터 추가"""
        # 모든 공정에 대해 기본 작업자 설정
        processes = self.master_data.processes.values()
        
        # 향후 30일간의 작업자 설정
        base_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # 주말 제외
            if date.weekday() >= 5:  # 토요일(5), 일요일(6)
                continue
            
            for process in processes:
                # 공정별로 다른 작업자 수 설정
                if process['name'] in ['계량', '혼합']:
                    worker_count = 2
                    batches_per_worker = 3.0
                elif process['name'] in ['타정', '코팅']:
                    worker_count = 3
                    batches_per_worker = 2.5
                else:  # 선별, 포장
                    worker_count = 4
                    batches_per_worker = 2.0
                
                self.master_data.set_operator_capacity(
                    process['id'],
                    date_str,
                    worker_count,
                    batches_per_worker
                )