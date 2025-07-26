from typing import List, Dict, Any, Callable
from PyQt5.QtCore import QObject, pyqtSignal

"""
키보드 명령에 사용할 클래스
"""
class Command:
    
    def __init__(self, description: str= ''):
        self.description = description

    """
    명령 실행
    """
    def execute(self) -> None:
        pass

    """
    명령 실행 취소
    """
    def undo(self) -> None:
        pass

    """
    명령 재실행
    """
    def redo(self) -> None:
        self.execute()

"""
데이터 변경 명령
"""
class DataCommand(Command):
    def __init__(self,
                 file_path: str, 
                 sheet_name: str, 
                 row: int, 
                 col: int, 
                 old_value: Any, 
                 new_value: Any,
                 update_callback: Callable):
        super().__init__(f'Change data at ({row}, {col}) from {old_value} to {new_value}')
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.row = row
        self.col = col
        self.old_value = old_value
        self.new_value = new_value
        self.update_callback = update_callback

    """
    새 값으로 데이터 업데이트
    """
    def execute(self) -> None:
        self.update_callback(self.file_path, self.sheet_name, self.row, self.col, self.new_value)

    """
    이전 값으로 데이터 복원
    """
    def undo(self) -> None:
        self.update_callback(self.file_path, self.sheet_name, self.row, self.col, self.old_value)

"""
행 추가/삭제 명령
"""
class UndoRedoManager(QObject):
    undo_redo_changed = pyqtSignal(bool, bool)
    data_changed = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._is_executing = False

    """
    명령 실행 및 스택 추가
    """
    def execute_command(self, command: Command) -> None:
        if self._is_executing:
            return
        
        self._is_executing = True

        try:
            command.execute()
            self._undo_stack.append(command)
            self._redo_stack.clear()

            if hasattr(command, 'file_path') and hasattr(command, 'sheet_name'):
                self.data_changed.emit(command.file_path, command.sheet_name)

            self.undo_redo_changed.emit(self.can_undo(), self.can_redo())
        finally:
            self._is_executing = False

    """
    가장 최근 명령 취소
    """
    def undo(self) -> None:
        if not self.can_undo() or self._is_executing:
            return
        
        self._is_executing = True

        try:
            command = self._undo_stack.pop()
            command.undo()
            self._redo_stack.append(command)

            if hasattr(command, 'file_path') and hasattr(command, 'sheet_name'):
                self.data_changed.emit(command.file_path, command.sheet_name)

            self.undo_redo_changed.emit(self.can_undo(), self.can_redo())
        finally:
            self._is_executing = False

    """
    가장 최근에 취소된 명령 재실행
    """
    def redo(self) -> None:
        if not self.can_redo() or self._is_executing:
            return
        
        self._is_executing = True

        try:
            command = self._redo_stack.pop()
            command.redo()
            self._undo_stack.append(command)

            if hasattr(command, 'file_path') and hasattr(command, 'sheet_name'):
                self.data_changed.emit(command.file_path, command.sheet_name)

            self.undo_redo_changed.emit(self.can_undo(), self.can_redo())
        finally:
            self._is_executing = False

    """
    실행 취소가 가능한지 확인
    """
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0
    
    """
    다시 실행 가능한지 확인
    """
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0
    
    """
    모든 명령 스택 초기화
    """
    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.undo_redo_changed.emit(False, False)

    """
    특정 파일/시트랑 관련한 명령만 제거
    """
    def clear_for_file(self, file_path: str, sheet_name: str = None) -> None:
        if sheet_name:
            self._undo_stack = [cmd for cmd in self._undo_stack if not (
                hasattr(cmd, 'file_path') and hasattr(cmd, 'sheet_name') and
                cmd.file_path == file_path and cmd.sheet_name == sheet_name
            )]
        else:
            self._undo_stack = [cmd for cmd in self._undo_stack if not(
                hasattr(cmd, 'file_path') and cmd.file_path == file_path
            )]

        if sheet_name:
            self._redo_stack = [cmd for cmd in self._redo_stack if not (
                hasattr(cmd, 'file_path') and hasattr(cmd, 'sheet_name') and
                cmd.file_path == file_path and cmd.sheet_name == sheet_name
            )]
        else:
            self._redo_stack = [cmd for cmd in self._redo_stack if not (
                hasattr(cmd, 'file_path') and cmd.file_path == file_path
            )]

        self.undo_redo_changed.emit(self.can_undo(), self.can_redo())

undo_redo_manager = UndoRedoManager()