import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging


class BookManager:
    def __init__(self, app_data_dir: Path):
        self.app_data_dir = app_data_dir
        self.bookshelf_file = app_data_dir / "bookshelf.json"
        self.bookshelf = self._load_bookshelf()
        self.current_book_path = self._get_current_book_path()

    def _load_bookshelf(self) -> Dict:
        """加载书架数据"""
        if self.bookshelf_file.exists():
            try:
                with open(self.bookshelf_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                logging.error(f"Error loading bookshelf file: {e}")
                return {}
        return {}

    def _save_bookshelf(self):
        """保存书架数据"""
        try:
            with open(self.bookshelf_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookshelf, f, ensure_ascii=False, indent=2)
        except (PermissionError, OSError) as e:
            logging.error(f"Error saving bookshelf file: {e}")

    def _get_current_book_path(self) -> Optional[str]:
        """获取当前打开的书籍路径"""
        return self.bookshelf.get("current_book")

    def has_opened_book(self) -> bool:
        """检查是否有打开的书"""
        current_book = self._get_current_book_path()
        # Also validate that the current book is in the bookshelf dict
        if current_book and current_book in self.bookshelf:
            return os.path.exists(current_book)
        return False

    def add_book(self, file_path: str):
        """将书籍添加到书架"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")
        
        if file_path not in self.bookshelf:
            self.bookshelf[file_path] = {
                "progress": 0,
                "total_lines": self._count_lines(file_path)
            }
            self._save_bookshelf()

    def set_current_book(self, file_path: str):
        """设置当前书籍"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")
        
        self.current_book_path = file_path
        self.bookshelf["current_book"] = file_path
        self._save_bookshelf()

    def get_current_progress(self) -> int:
        """获取当前进度"""
        # Validate that the current book path exists in bookshelf and file exists
        if (self.current_book_path and 
            self.current_book_path in self.bookshelf and 
            os.path.exists(self.current_book_path)):
            return self.bookshelf[self.current_book_path].get("progress", 0)
        return 0

    def update_progress(self, line_number: int):
        """更新阅读进度"""
        # Validate that the current book path exists in bookshelf and file exists
        if (self.current_book_path and 
            self.current_book_path in self.bookshelf and 
            os.path.exists(self.current_book_path)):
            self.bookshelf[self.current_book_path]["progress"] = line_number
            self._save_bookshelf()

    def get_total_lines(self) -> int:
        """获取总行数"""
        # Validate that the current book path exists in bookshelf and file exists
        if (self.current_book_path and 
            self.current_book_path in self.bookshelf and 
            os.path.exists(self.current_book_path)):
            book_info = self.bookshelf[self.current_book_path]
            if "total_lines" in book_info:
                return book_info["total_lines"]
            # Only count lines if not cached
            return self._count_lines(self.current_book_path)
        return self._count_lines(self.current_book_path) if self.current_book_path else 0

    def _count_lines(self, file_path: str) -> int:
        """统计文件行数"""
        if not os.path.exists(file_path):
            return 0
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            logging.error(f"Error counting lines in {file_path}: {e}")
            return 0

    def get_book_content(self) -> List[str]:
        """获取书籍内容（分页后的）"""
        if not self.current_book_path:
            return []

        # Check if file exists before attempting to read
        if not os.path.exists(self.current_book_path):
            return [f"文件不存在: {self.current_book_path}"]
        
        # Optional: Check file size to prevent loading extremely large files
        try:
            file_size = os.path.getsize(self.current_book_path)
            # Limit to 100MB for safety (adjust as needed)
            if file_size > 100 * 1024 * 1024:  # 100MB
                return ["文件过大，无法加载"]
        except OSError:
            return [f"无法获取文件大小: {self.current_book_path}"]

        try:
            with open(self.current_book_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 处理每行内容，进行分页
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if not line:  # 跳过空行
                    continue
                formatted_lines.extend(self._split_line(line))

            return formatted_lines
        except Exception as e:
            return [f"读取文件错误: {str(e)}"]

    def _split_line(self, line: str, max_length: int = 50) -> List[str]:
        """将长行分割为适合显示的段落"""
        # Handle empty lines
        if not line.strip():
            return []
        
        words = line.split()
        chunks = []
        current_chunk = []

        for word in words:
            if len(' '.join(current_chunk + [word])) <= max_length:
                current_chunk.append(word)
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks
