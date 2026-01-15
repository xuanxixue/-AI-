#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import tkinter as tk
from tkinter import messagebox

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

def test_chapter_generation_window():
    """测试章节生成窗口的完整功能"""
    try:
        from ui.chapter_generation_window import ChapterGenerationWindow
        
        # 使用项目1的数据库路径进行测试
        project_path = r"c:\Users\玄曦雪\OneDrive\Desktop\动慢工具\novel_creation_tool\projects\1"
        
        print("正在创建章节生成窗口...")
        
        # 创建Tkinter根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 创建章节生成窗口
        window = ChapterGenerationWindow(project_path)
        
        print("章节生成窗口创建成功")
        
        # 稍微延迟一下以便观察
        root.after(3000, lambda: print("测试完成，即将关闭窗口"))
        
        # 5秒后退出
        root.after(5000, root.quit)
        
        print("开始运行GUI事件循环...")
        root.mainloop()
        
        print("测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chapter_generation_window()