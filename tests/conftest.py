"""Cấu hình chung cho pytest.

test_benchmark.py in kết quả bằng tiếng Việt. Chạy với -s thì pytest không chặn
stdout nữa, output đi thẳng ra console Windows (cp1252) và nổ UnicodeEncodeError,
đúng lệnh README hướng dẫn: python -m pytest tests/test_benchmark.py -v -s
"""
from src.config import use_utf8_stdout

use_utf8_stdout()
