from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, pyqtSignal
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
        background-color: rgba(255, 255, 255, 150);
        border: 1px solid #4CAF50;
        color: #333;
        font-size: 14px;
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
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setStyleSheet(FOCUS_IN_STYLE)
        self.content_label.setWordWrap(True)

        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        self.content_label.setFont(font)

        layout.addWidget(self.content_label)
        self.setLayout(layout)

        # 设置窗口属性
        self.setWindowTitle("Fish - 摸鱼阅读器")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Enable mouse tracking to support dragging
        self.setMouseTracking(True)
        self.content_label.setMouseTracking(True)

    def update_display(self):
        """更新显示内容"""
        if not self.book_content:
            self.content_label.setText("没有可显示的内容")
            return

        if 0 <= self.current_line < len(self.book_content):
            self.content_label.setText(self.book_content[self.current_line])
            self.book_manager.update_progress(self.current_line)
        elif self.book_content:
            # 超出范围时重置到开头或末尾
            self.current_line = max(0, min(self.current_line, len(self.book_content) - 1))
            self.content_label.setText(self.book_content[self.current_line])
            self.book_manager.update_progress(self.current_line)

    def keyPressEvent(self, event: QKeyEvent):
        """按键事件处理"""
        key = event.key()

        if key in (Qt.Key.Key_Up, Qt.Key.Key_W):
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
        while new_line >= 0 and (not self.book_content[new_line].strip()):
            new_line -= 1

        if new_line >= 0:
            self.current_line = new_line
            self.update_display()

    def next_line(self):
        """显示下一行内容"""
        if not self.book_content:
            return

        new_line = self.current_line + 1
        while new_line < len(self.book_content) and (not self.book_content[new_line].strip()):
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
