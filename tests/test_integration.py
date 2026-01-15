#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from ui.function_panel import FunctionPanelWidget
import os
import sys

def test_function_panel_integration():
    """测试功能面板与章节生成窗口的集成"""
    try:
        # 创建根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 创建功能面板
        panel = FunctionPanelWidget(root)
        
        # 设置项目路径
        project_path = r"c:\Users\玄曦雪\OneDrive\Desktop\动慢工具\novel_creation_tool\projects\1"
        panel.set_current_project(project_path)
        
        print("功能面板创建成功，项目路径已设置")
        
        # 测试章节生成功能
        print("正在测试章节生成功能...")
        panel.show_chapter_generation()
        print("章节生成窗口已打开")
        
        # 由于show_chapter_generation会打开新窗口，我们稍等一下然后结束
        def close_test():
            print("测试完成")
            root.quit()
        
        # 3秒后自动关闭
        root.after(3000, close_test)
        
        print("开始运行测试...")
        root.mainloop()
        
        print("集成测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_function_panel_integration()