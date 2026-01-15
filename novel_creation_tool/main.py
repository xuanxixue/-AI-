"""
小说创作辅助工具
主入口文件
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from simple_gui import main


if __name__ == '__main__':
    main()