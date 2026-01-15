"""
测试故事信息提取功能
"""

import tkinter as tk
from ui.story_extraction_window import StoryExtractionWindow


def test_story_extraction():
    """测试故事信息提取功能"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 创建测试项目路径
    test_project_path = "./test_project"
    
    # 创建故事信息提取窗口
    app = StoryExtractionWindow(test_project_path)
    
    # 运行应用
    root.mainloop()


if __name__ == "__main__":
    test_story_extraction()