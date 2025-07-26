"""
아이템 위치 관리 유틸리티 클래스
"""
class ItemPositionManager:

    """
    Time 값에 따른 요일과 교대 정보 반환
    """
    @staticmethod
    def get_day_and_shift(time_value):
        try:
            time_int = int(time_value)
            # 1,2(월), 3,4(화), 5,6(수), 7,8(목), 9,10(금), 11,12(토), 13,14(일)
            day_idx = (time_int - 1) // 2

            # 요일 인덱스(0-6)와 교대(주간/야간) 반환
            shift = "Day" if time_int % 2 == 1 else "Night"
            return day_idx, shift
        except (ValueError, TypeError):
            return -1, None

    """
    라인과 교대 정보로 행 키 생성
    """
    @staticmethod
    def get_row_key(line, shift):
        return f"{line}_({shift})"

    """
    요일 인덱스로 열 인덱스 반환
    """
    @staticmethod
    def get_col_from_day_idx(day_idx, days):
        if 0 <= day_idx < len(days):
            return day_idx
        return -1

    """
    행 키로 행 인덱스 찾기
    """
    @staticmethod
    def find_row_index(row_key, row_headers):
        try:
            return row_headers.index(row_key)
        except ValueError:
            return -1

    """
    교대 정보로 교대 인덱스 반환
    """
    @staticmethod
    def get_shift_index(shift, shifts=None):
        if shifts is None:
            shifts = ["Day", "Night"]
        try:
            return shifts.index(shift)
        except ValueError:
            return -1

    """
    셀 병합된 그리드에서 라인과 교대 정보로 행 인덱스 계산

    매개변수:
    - line: 라인명
    - shift: 교대 정보 ("주간" 또는 "야간")
    - lines: 정렬된 라인 목록
    - shifts: 정렬된 교대 목록 (기본값: ["주간", "야간"])

    반환값:
    - 행 인덱스 (실제 그리드에서의 행 번호)
    """
    @staticmethod
    def get_row_index_in_merged_grid(line, shift, lines, shifts=None):
        if shifts is None:
            shifts = ["Day", "Night"]

        try:
            line_idx = lines.index(line)
            shift_idx = ItemPositionManager.get_shift_index(shift, shifts)

            if line_idx >= 0 and shift_idx >= 0:
                # 각 라인마다 교대 수만큼 행이 있음
                return line_idx * len(shifts) + shift_idx
            return -1
        except ValueError:
            return -1