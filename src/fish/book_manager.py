import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from .config import bookshelf, config

# Set up module-specific logger
logger = logging.getLogger(__name__)


class BookManager:
    def __init__(self, app_data_dir: Path):
        self.line_mapping = {}  # Maps display_line_index -> actual_line_number
        self.reverse_line_mapping = {}  # Maps actual_line_number -> [display_line_indices]
        self.app_data_dir = app_data_dir
        self.bookshelf = bookshelf
        self.current_book_path = self._get_current_book_path()
        self._needs_save = False

    def _get_current_book_path(self) -> Optional[str]:
        """获取当前打开的书籍路径"""
        return self.bookshelf.get("current_book")

    def has_opened_book(self) -> bool:
        """检查是否有打开的书"""
        current_book = self._get_current_book_path()
        logger.info(f"Checking if book is opened, current book: {current_book}")
        # Also validate that the current book is in the bookshelf dict
        if current_book and current_book in self.bookshelf:
            exists = os.path.exists(current_book)
            logger.info(f"Book exists check result: {exists}")
            return exists
        logger.info("No current book found in bookshelf")
        return False

    def add_book(self, file_path: str):
        """将书籍添加到书架"""
        logger.info(f"Attempting to add book to bookshelf: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            raise FileNotFoundError(f"File does not exist: {file_path}")

        if file_path not in self.bookshelf:
            total_lines = self._count_lines(file_path)
            self.bookshelf[file_path] = {
                "progress": 0,
                "total_lines": total_lines
            }
            self._needs_save = True
            logger.info(f"Book added to bookshelf: {file_path} with {total_lines} lines")
        else:
            logger.info(f"Book already in bookshelf: {file_path}")

    def set_current_book(self, file_path: str):
        """设置当前书籍"""
        logger.info(f"Setting current book to: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            raise FileNotFoundError(f"File does not exist: {file_path}")

        self.current_book_path = file_path
        self.bookshelf["current_book"] = file_path
        self._needs_save = True
        logger.info(f"Current book set successfully: {file_path}")

    def get_current_progress(self) -> int:
        """获取当前进度"""
        logger.debug(f"Getting current progress for book: {self.current_book_path}")
        # Validate that the current book path exists in bookshelf and file exists
        if (self.current_book_path and
                self.current_book_path in self.bookshelf and
                os.path.exists(self.current_book_path)):
            progress = self.bookshelf[self.current_book_path].get("progress", 0)
            logger.debug(f"Current progress: {progress}")
            return progress
        logger.warning("No current book or book not in bookshelf, returning 0 progress")
        return 0

    def update_progress(self, line_number: int):
        """更新阅读进度"""
        logger.debug(f"Updating progress to line: {line_number} for book: {self.current_book_path}")
        # Validate that the current book path exists in bookshelf and file exists
        if (self.current_book_path and
                self.current_book_path in self.bookshelf and
                os.path.exists(self.current_book_path)):
            self.bookshelf[self.current_book_path]["progress"] = line_number
            # Only mark for save if auto_save_progress is enabled
            if config.get('auto_save_progress', True):
                self._needs_save = True
            logger.info(f"Progress updated to line: {line_number} for book: {self.current_book_path}")
        else:
            logger.warning(f"Cannot update progress, current book invalid: {self.current_book_path}")

    def get_total_lines(self) -> int:
        """获取总行数"""
        logger.debug(f"Getting total lines for book: {self.current_book_path}")
        # Validate that the current book path exists in bookshelf and file exists
        if (self.current_book_path and
                self.current_book_path in self.bookshelf and
                os.path.exists(self.current_book_path)):
            book_info = self.bookshelf[self.current_book_path]
            if "total_lines" in book_info:
                total_lines = book_info["total_lines"]
                logger.debug(f"Returning cached total lines: {total_lines}")
                return total_lines
            # Only count lines if not cached
            total_lines = self._count_lines(self.current_book_path)
            logger.info(f"Counted lines for book: {self.current_book_path}, total: {total_lines}")
            return total_lines
        total_lines = self._count_lines(self.current_book_path) if self.current_book_path else 0
        logger.info(f"Returning total lines for current book: {total_lines}")
        return total_lines

    def _count_lines(self, file_path: str) -> int:
        """统计文件行数"""
        logger.info(f"Counting lines in file: {file_path}")
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist for line counting: {file_path}")
            return 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
                logger.info(f"File {file_path} has {line_count} lines")
                return line_count
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            logger.error(f"Error counting lines in {file_path}: {e}")
            return 0

    def save(self):
        """保存书架数据到文件"""
        if self._needs_save and config.get('auto_save_progress', True):
            logger.info(f"Saving bookshelf data...")
            try:
                self.bookshelf.save()
                self._needs_save = False
                logger.info("Bookshelf data saved successfully")
            except (PermissionError, OSError) as e:
                logger.error(f"Error saving bookshelf: {e}")
        else:
            if not config.get('auto_save_progress', True):
                logger.info("Auto-save progress is disabled in config")
            else:
                logger.debug("No changes to save, bookshelf data unchanged")

    def get_book_content(self) -> List[str]:
        """获取书籍内容（分页后的）"""
        logger.info(f"Getting content for book: {self.current_book_path}")
        if not self.current_book_path:
            logger.warning("No current book set, returning empty content")
            return []

        # Check if file exists before attempting to read
        if not os.path.exists(self.current_book_path):
            logger.error(f"Current book file does not exist: {self.current_book_path}")
            return [f"文件不存在: {self.current_book_path}"]

        # Optional: Check file size to prevent loading extremely large files
        try:
            file_size = os.path.getsize(self.current_book_path)
            logger.info(f"Book file size: {file_size} bytes")
            # Limit to 100MB for safety (adjust as needed)
            if file_size > 100 * 1024 * 1024:  # 100MB
                logger.error(f"Book file too large ({file_size} bytes), refusing to load")
                return ["文件过大，无法加载"]
        except OSError as e:
            logger.error(f"Cannot get file size for {self.current_book_path}: {e}")
            return [f"无法获取文件大小: {self.current_book_path}"]

        try:
            with open(self.current_book_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
                logger.info(f"Loaded {len(original_lines)} lines from book file")

            # 处理每行内容，进行分页
            formatted_lines = []
            display_line_index = 0  # Track display line index
            logger.info("Processing book content for display formatting")

            for idx, original_line in enumerate(original_lines):
                actual_line_number = idx + 1  # 实际文件行号从1开始
                line = original_line.strip()
                if not line:  # 跳过空行
                    continue

                # 分割长行后，将分割出的每行都映射到原始行号
                split_lines = self._split_line(line)
                for split_line in split_lines:
                    formatted_lines.append(split_line)
                    self.line_mapping[display_line_index] = actual_line_number
                    if actual_line_number not in self.reverse_line_mapping:
                        self.reverse_line_mapping[actual_line_number] = []
                    self.reverse_line_mapping[actual_line_number].append(display_line_index)
                    display_line_index += 1

            logger.info(f"Formatted book content into {len(formatted_lines)} display lines")
            return formatted_lines
        except Exception as e:
            logger.error(f"Error reading book content: {str(e)}")
            return [f"读取文件错误: {str(e)}"]

    def get_actual_line_number(self, display_line_index: int) -> int:
        """根据显示行索引获取实际行号"""
        return self.line_mapping.get(display_line_index, -1)  # 如果没有映射，返回-1

    def get_display_line_index(self, actual_line_number: int) -> int:
        """根据实际行号获取显示行索引"""
        while actual_line_number >= 0:
            indices = self.reverse_line_mapping.get(actual_line_number, [])
            if indices:
                break
            else:
                actual_line_number -= 1
        else:
            indices = None
        return indices[0] if indices else -1

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
