from PyQt5.QtCore import QObject


"""
애플리케이션 데이터 모델
파일 경로, 날짜 범위, 분석 결과 등의 데이터를 관리
"""
class DataModel(QObject):

    def __init__(self):
        super().__init__()
        self.file_paths = []
        self.start_date = None
        self.end_date = None
        self.analysis_results = None
        self.settings = {}

    """
    파일 경로 설정
    """
    def set_file_path(self, file_path):
        if file_path not in self.file_paths:
            self.file_paths.append(file_path)

    """
    파일 경로 목록 반환
    """
    def get_file_paths(self):
        return self.file_paths

    """
    날짜 범위 설정
    """
    def set_date_range(self, start_date, end_date):
        try:
            self.start_date = start_date
            self.end_date = end_date
        except Exception as e:
            print(f"날짜 범위 설정 중 오류 발생: {str(e)}")

    """
    날짜 범위 반환
    """
    def get_date_range(self):
        return self.start_date, self.end_date

    """
    분석 결과 설정
    """
    def set_analysis_results(self, results):
        self.analysis_results = results

    """
    분석 결과 반환
    """
    def get_analysis_results(self):
        return self.analysis_results

    """
    설정 업데이트 메서드

    Args:
        settings (dict): 업데이트할 설정 딕셔너리
    """
    def update_settings(self, settings):
        self.settings.update(settings)

        # 설정에 따라 모델 상태 업데이트가 필요한 경우 여기에 구현
        if 'time_limit' in settings:
            pass

        # 필요한 경우 다른 설정에 따른 처리 여기에 구현
        if 'op_InputRoute' in settings and settings['op_InputRoute']:
            pass

        if 'op_SavingRoute' in settings and settings['op_SavingRoute']:
            pass

    """
    현재 설정 반환
    """
    def get_settings(self):
        return self.settings

    """
    모든 데이터 초기화
    """
    def clear(self):
        self.file_paths = []
        self.start_date = None
        self.end_date = None
        self.analysis_results = None
        self.settings = {}