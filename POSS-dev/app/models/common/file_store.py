"""
파일 경로를 저장하는 중앙 저장소
"""
class FilePaths:
    _paths = {
        "dynamic_excel_file": None,
        "master_excel_file": None,
        "demand_excel_file": None,
        "pre_assign_excel_file": None,
        "etc_excel_file": None,
        "output_file": None,
        "result_file": None,
        "optimizer_file" : None
    }

    # 파일 경로 조회
    @classmethod
    def get(cls, key):
        return cls._paths.get(key)
    
    # 파일 경로 등록
    @classmethod
    def set(cls, key, path):
        cls._paths[key] = path

    # 파일 경로 갱신
    @classmethod
    def update(cls, paths_dict):
        cls._paths.update(paths_dict)

"""
데이터 스토리지 클래스
메모리 내에서 데이터를 저장하고 접근하기 위한 중앙 저장소
"""
class DataStore:
    _data_store = {}

    """
    데이터 저장
    """
    @classmethod
    def set(cls, key, value):
        cls._data_store[key] = value

    """
    데이터 조회
    """
    @classmethod
    def get(cls, key, default=None):
        return cls._data_store.get(key, default)

    """
    데이터 삭제
    """
    @classmethod
    def delete(cls, key):
        if key in cls._data_store:
            del cls._data_store[key]

    """
    모든 데이터 삭제
    """
    @classmethod
    def clear(cls):
        cls._data_store.clear()