import json
import os
import re
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

    def _split_line(self, line: str, max_length: int = 66) -> List[str]:
        """将长行分割为适合显示的段落：
        - 每个"段"最多两"行"
        - 每"行"可以有多个"话"，但总长度不超过max_length/2
        - "话"的结尾是[。？！]
        - 行与行之间使用换行符隔开
        """
        # 处理空行
        if not line.strip():
            return []
        # 按句子分割（以。？！为结束标志）
        sentences = self._extract_sentences(line)

        if not sentences:
            return []
        # 每行最大长度
        max_line_length = max_length // 2

        # 先将句子组织成行
        lines = self._group_sentences_into_lines(sentences, max_line_length)

        # 再将行组织成段（每段最多两行）
        paragraphs = self._group_lines_into_paragraphs(lines)

        return paragraphs

    def _extract_sentences(self, text: str) -> List[str]:
        """提取句子"""
        # 使用正则表达式分割句子
        sentences = re.findall(r'[^。？！]*[。？！]?', text)
        # 清理和过滤句子
        cleaned_sentences = []
        for sentence in sentences:
            if sentence.strip() or any(char in sentence for char in '。？！'):
                cleaned_sentences.append(sentence)
        return cleaned_sentences

    def _group_sentences_into_lines(self, sentences: List[str], max_line_length: int) -> List[str]:
        """将句子组织成行"""
        lines = []
        current_line = []
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # 如果单个句子就超长，需要特殊处理
            if sentence_len > max_line_length:
                # 先保存当前行（如果有的话）
                if current_line:
                    lines.append(''.join(current_line))
                    current_line = []
                    current_length = 0

                # 强制分割超长句子
                forced_lines = self._force_split_long_sentence(sentence, max_line_length)
                lines.extend(forced_lines)
            else:
                # 检查是否能加入当前行
                new_length = current_length + sentence_len
                if new_length <= max_line_length:
                    current_line.append(sentence)
                    current_length = new_length
                else:
                    # 开始新行
                    if current_line:
                        lines.append(''.join(current_line))
                    current_line = [sentence]
                    current_length = sentence_len

        # 添加最后一行
        if current_line:
            lines.append(''.join(current_line))

        return lines

    def _force_split_long_sentence(self, sentence: str, max_line_length: int) -> List[str]:
        """强制分割超长句子"""
        if len(sentence) <= max_line_length:
            return [sentence]

        result = []
        start = 0

        while start < len(sentence):
            # 尝试找到合适的分割点
            end = min(start + max_line_length, len(sentence))

            if end < len(sentence):
                # 寻找最近的合适分割点（标点符号）
                split_point = end
                for i in range(end - 1, start + max_line_length // 3, -1):  # 至少保留1/3长度
                    if sentence[i] in '，；：、':
                        split_point = i + 1
                        break
                    elif sentence[i] in ' \t':
                        split_point = i
                        break
                result.append(sentence[start:split_point])
                start = split_point
            else:
                result.append(sentence[start:end])
                break

        return result

    def _group_lines_into_paragraphs(self, lines: List[str]) -> List[str]:
        """将行组织成段（每段最多两行）"""
        paragraphs = []
        i = 0

        while i < len(lines):
            if i + 1 < len(lines):
                # 两行组成一段
                paragraph = lines[i] + '\n' + lines[i + 1]
                paragraphs.append(paragraph)
                i += 2
            else:
                # 最后一行单独成段
                paragraphs.append(lines[i])
                i += 1

        return paragraphs
