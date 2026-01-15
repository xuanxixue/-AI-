#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

def quick_test():
    """快速测试章节生成窗口是否能正常打开"""
    try:
        from ui.chapter_generation_window import ChapterGenerationWindow
        
        # 使用已有的项目路径
        project_path = r"c:\Users\玄曦雪\OneDrive\Desktop\动慢工具\novel_creation_tool\projects\1"
        
        if not os.path.exists(project_path):
            print(f"项目路径不存在: {project_path}")
            # 尝试使用当前目录下的projects/1
            project_path = os.path.join(os.getcwd(), "projects", "1")
            if not os.path.exists(project_path):
                print(f"项目路径也不存在: {project_path}")
                return False
        
        print("正在测试章节生成窗口...")
        
        # 创建根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 创建章节生成窗口
        window = ChapterGenerationWindow(project_path)
        
        print("章节生成窗口创建成功！")
        
        # 检查大纲树是否包含项目
        tree_items = window.outline_tree.get_children()
        print(f"大纲树中的项目数量: {len(tree_items)}")
        
        if len(tree_items) > 0:
            print("✅ 大纲已成功加载并显示在树形结构中！")
            for item in tree_items:
                item_text = window.outline_tree.item(item, "text")
                print(f"  - {item_text}")
                # 检查子项目
                children = window.outline_tree.get_children(item)
                for child in children:
                    child_text = window.outline_tree.item(child, "text")
                    print(f"    - {child_text}")
        else:
            print("❌ 大纲树中没有项目，请检查数据库内容")
        
        # 在主线程中延迟关闭窗口
        def close_window():
            print("测试完成，关闭窗口...")
            root.quit()
        
        root.after(3000, close_window)  # 3秒后关闭
        
        print("开始运行GUI事件循环...")
        root.mainloop()
        
        print("测试完成！")
        return True
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    quick_test()