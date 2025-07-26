from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from app.utils.command.undo_command import undo_redo_manager

"""
data_input_page의 undo/redo 기능 초기화
"""
def initialize_undo_redo_in_data_input_page(data_input_page):
    if not hasattr(data_input_page, 'undo_shortcut'):
        data_input_page.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), data_input_page)
        
        def undo_wrapper():
            undo_redo_manager.undo()

        data_input_page.undo_shortcut.activated.connect(undo_wrapper)
    
    if not hasattr(data_input_page, 'redo_shortcut'):
        data_input_page.redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), data_input_page)
        data_input_page.redo_shortcut.activated.connect(undo_redo_manager.redo)
    
    if hasattr(data_input_page, 'tab_manager'):
        undo_redo_manager.data_changed.connect(
            data_input_page.tab_manager.on_data_changed_by_undo_redo
        )
        
        undo_redo_manager.undo_redo_changed.connect(
            data_input_page.tab_manager.on_undo_redo_state_changed
        )
    
    original_execute_command = undo_redo_manager.execute_command
    
    def execute_command_wrapper(command):
        original_execute_command(command)
    
    undo_redo_manager.execute_command = execute_command_wrapper