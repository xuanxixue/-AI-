#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说创作辅助工具
tkinter GUI 版本启动器
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from simple_gui import main

if __name__ == '__main__':
    main()