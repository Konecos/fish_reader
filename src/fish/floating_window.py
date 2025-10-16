from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeyEvent, QFont, QPalette, QColor

FOCUS_IN_STYLE = """
    QLabel {
        background-color: rgba(255, 255, 255, 240);
        border: 2px solid #2196F3;
        color: #333;
        font-size: 14px;
    }
"""

FOCUS_OUT_STYLE = """
    QLabel {
        background-color: rgba(255, 255, 255, 26);
        border: 1px solid #4CAF5022;
        color: #33333322;
        opacity: 0.1;
        font-size: 14px;
        
    }
"""

LINE_NUMBER_STYLE = """
    QLabel {
        color: #666;
        font-size: 12px;
    }
"""


class FloatingWindow(QWidget):
    def __init__(self, book_manager):
        super().__init__()
        self.book_manager = book_manager
        self.current_line = self.book_manager.get_current_progress()
        self.book_content = self.book_manager.get_book_content()

        # Variables for dragging functionality
        self.is_dragging = False
        self.drag_position = None
        
        # Variable for g key input
        self.waiting_for_line_number = False
        self.line_number_input = ""

        # Track topmost status
        self.was_topmost_last_check = True

        # Timer to check if window is topmost every 1 second
        self.topmost_timer = QTimer(self)
        self.topmost_timer.timeout.connect(self.check_topmost_status)
        self.topmost_timer.start(500)

        self.init_ui()
        self.update_display()

    def init_ui(self):
        """初始化UI"""
        # Remove fixed size to allow dragging
        self.setFixedSize(500, 75)

        # 设置半透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()

        # 创建显示标签
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # 左对齐
        self.content_label.setStyleSheet(FOCUS_IN_STYLE)
        self.content_label.setWordWrap(True)

        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        self.content_label.setFont(font)

        layout.addWidget(self.content_label)
        self.setLayout(layout)

        # 创建行号标签
        self.line_number_label = QLabel()
        self.line_number_label.setStyleSheet(LINE_NUMBER_STYLE)
        self.line_number_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.line_number_label.setParent(self)
        self.update_line_number_position()  # 设置初始位置
        
        # 设置窗口属性
        self.setWindowTitle("Fish")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Enable mouse tracking to support dragging
        self.setMouseTracking(True)
        self.content_label.setMouseTracking(True)

    def update_line_number_position(self):
        """更新行号标签位置到右下角"""
        # 获取窗口大小
        window_width = self.width()
        window_height = self.height()
        
        # 设置行号标签大小和位置 (距离右边和底部10像素)
        label_width = 100  # 估算标签宽度
        label_height = 20  # 估算标签高度
        x = window_width - label_width - 15
        y = window_height - label_height - 10
        
        self.line_number_label.setGeometry(x, y, label_width, label_height)
        self.line_number_label.setAlignment(Qt.AlignmentFlag.AlignRight)  # 右对齐
        
        # 设置50%透明度
        self.line_number_label.setWindowOpacity(0.5)

    def update_display(self):
        """更新显示内容"""
        if not self.book_content:
            self.content_label.setText("没有可显示的内容")
            self.line_number_label.setText("")
            return

        if 0 <= self.current_line < len(self.book_content):
            # 获取实际行号
            actual_line_number = self.book_manager.get_actual_line_number(self.current_line)
            line_content = self.book_content[self.current_line]
            
            # 显示内容（不包含行号）
            self.content_label.setText(line_content)
            
            # 显示行号在单独的标签中
            if actual_line_number != -1:
                self.line_number_label.setText(f"Line {actual_line_number}")
            else:
                self.line_number_label.setText("")
                
            self.book_manager.update_progress(self.current_line)
        elif self.book_content:
            # 超出范围时重置到开头或末尾
            self.current_line = max(0, min(self.current_line, len(self.book_content) - 1))
            actual_line_number = self.book_manager.get_actual_line_number(self.current_line)
            line_content = self.book_content[self.current_line]
            
            # 显示内容（不包含行号）
            self.content_label.setText(line_content)
            
            # 显示行号在单独的标签中
            if actual_line_number != -1:
                self.line_number_label.setText(f"Line {actual_line_number}")
            else:
                self.line_number_label.setText("")
                
            self.book_manager.update_progress(self.current_line)

    def jump_to_line(self):
        """跳转到指定行"""
        if self.waiting_for_line_number and self.line_number_input:
            try:
                target_line = int(self.line_number_input)
                # Convert actual line number to display index
                display_index = self.book_manager.get_display_line_index(target_line)
                
                if display_index != -1:
                    self.current_line = display_index
                    self.update_display()
                else:
                    self.content_label.setText(f"未找到第 {target_line} 行")
                    self.line_number_label.setText("")
                    
            except ValueError:
                self.content_label.setText("请输入有效的行号")
                self.line_number_label.setText("")
            
            # Reset after jump attempt
            self.waiting_for_line_number = False
            self.line_number_input = ""
            self.update_display()  # Restore normal display
        else:
            self.waiting_for_line_number = False
            self.line_number_input = ""
            self.update_display()

    def keyPressEvent(self, event: QKeyEvent):
        """按键事件处理"""
        key = event.key()
        
        # Handle numeric input when waiting for line number
        if self.waiting_for_line_number:
            if event.key() >= Qt.Key.Key_0 and event.key() <= Qt.Key.Key_9:
                self.line_number_input += event.text()
                # Update display to show current input
                self.content_label.setText(f"输入行号: {self.line_number_input}")
                self.line_number_label.setText("")
            elif event.key() == Qt.Key.Key_Return:  # Enter key to confirm
                self.jump_to_line()
            elif event.key() == Qt.Key.Key_Escape:  # Escape to cancel
                self.waiting_for_line_number = False
                self.line_number_input = ""
                self.update_display()
            else:
                super().keyPressEvent(event)
            return

        if key == Qt.Key.Key_G:
            # Start waiting for line number input
            self.waiting_for_line_number = True
            self.line_number_input = ""
            self.content_label.setText("输入行号然后按回车 (g + 行号 + Enter)")
            self.line_number_label.setText("")
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_W):
            self.previous_line()
        elif key in (Qt.Key.Key_Down, Qt.Key.Key_S):
            self.next_line()
        elif key == Qt.Key.Key_Q:
            QApplication.quit()
        else:
            super().keyPressEvent(event)

    def previous_line(self):
        """显示上一行内容"""
        if not self.book_content:
            return

        new_line = self.current_line - 1
        while new_line >= 0 and not self.book_content[new_line].strip():
            new_line -= 1

        if new_line >= 0:
            self.current_line = new_line
            self.update_display()

    def next_line(self):
        """显示下一行内容"""
        if not self.book_content:
            return

        new_line = self.current_line + 1
        while new_line < len(self.book_content) and not self.book_content[new_line].strip():
            new_line += 1

        if new_line < len(self.book_content):
            self.current_line = new_line
            self.update_display()

    def mousePressEvent(self, event):
        """鼠标点击事件 - 设置焦点和开始拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            # Calculate the position relative to the window
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            self.setFocus()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 实现窗口拖拽"""
        if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            # Move the window to the new position
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
        event.accept()

    def focusInEvent(self, event):
        """获得焦点时的事件"""
        self.content_label.setStyleSheet(FOCUS_IN_STYLE)

    def focusOutEvent(self, event):
        """失去焦点时的事件"""
        self.content_label.setStyleSheet(FOCUS_OUT_STYLE)

    def resizeEvent(self, event):
        """窗口大小改变时更新行号位置"""
        super().resizeEvent(event)
        self.update_line_number_position()

    def check_topmost_status(self):
        """检查窗口是否为顶层窗口"""
        # Check if the window is still on top by checking if it's active and visible
        is_currently_topmost = self.isActiveWindow() and self.isVisible()
        
        # Optional: Log or handle changes in topmost status
        if is_currently_topmost != self.was_topmost_last_check:
            # Status changed
            if is_currently_topmost:
                # Window became topmost
                pass  # Could add logic here if needed
            else:
                # Window is no longer topmost
                pass  # Could add logic here if needed
        
        self.was_topmost_last_check = is_currently_topmost
        
        # Ensure the window stays on top by calling raise_()
        self.raise_()  # Bring to top without taking focus
