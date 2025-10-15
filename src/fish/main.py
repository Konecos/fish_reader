import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import Qt
from .floating_window import FloatingWindow
from .book_manager import BookManager


def main():
    app = QApplication(sys.argv)

    # 确保AppData目录存在
    app_data_dir = Path(os.getenv('APPDATA')) / "fish"
    app_data_dir.mkdir(exist_ok=True)

    # 初始化书架管理器
    book_manager = BookManager(app_data_dir)

    try:
        # 如果没有打开的书，提示选择文件
        if not book_manager.has_opened_book():
            file_path, _ = QFileDialog.getOpenFileName(
                None, "选择文本文件", "", "Text Files (*.txt)"
            )
            if not file_path:
                sys.exit(0)  # Properly exit QApplication when user cancels

            # Add validation to ensure the path is not empty
            if not file_path.strip():
                sys.exit(0)

            # 添加到书架并设置进度
            book_manager.add_book(file_path)
            book_manager.set_current_book(file_path)

        # 创建浮动窗口
        window = FloatingWindow(book_manager)

        # 设置窗口始终置顶和焦点 - DO THIS BEFORE SHOWING WINDOW
        window.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )

        window.show()

        sys.exit(app.exec())
    finally:
        # 程序退出时确保保存数据
        book_manager.save()


if __name__ == "__main__":
    main()
