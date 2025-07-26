"""
라인 정렬 메소드
(I_01, I_02, I_03, ... 순서)
""" 
def sort_line(line):
    parts = line.split('_')
    if len(parts) == 2:
        building = parts[0]
        try:
            number = int(parts[1])
            return (building, number)
        except ValueError:
            return (building, 999)
    return (line, 0)
        