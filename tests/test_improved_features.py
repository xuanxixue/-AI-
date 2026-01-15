"""
测试改进后的大纲理解和想法提取功能
"""
import tkinter as tk
from tkinter import messagebox
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_improved_features():
    """测试改进后的功能特性"""
    print("=== 测试改进后的大纲理解和想法提取功能 ===")
    print("功能改进包括：")
    print("1. 添加了进度条显示处理状态")
    print("2. 添加了日志显示处理过程")
    print("3. 改进了UI布局，增加了上下分栏")
    print("4. 防止重复点击导致的多次请求")
    print("5. 更好的用户体验反馈")
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("功能改进测试")
    root.geometry("500x300")
    
    def test_outline_understanding():
        """测试大纲理解窗口"""
        try:
            from ui.outline_understanding_window import OutlineUnderstandingWindow
            # 使用临时项目路径进行测试
            temp_project_path = os.path.join(os.getcwd(), "temp_test_project")
            os.makedirs(temp_project_path, exist_ok=True)
            app = OutlineUnderstandingWindow(temp_project_path)
            print("✓ 大纲理解窗口创建成功，包含新功能")
            messagebox.showinfo("测试结果", "大纲理解窗口已打开，可以看到新的进度条和日志功能")
        except Exception as e:
            print(f"✗ 大纲理解窗口创建失败: {e}")
            messagebox.showerror("错误", f"大纲理解窗口创建失败: {e}")
    
    def test_idea_extraction():
        """测试想法提取窗口"""
        try:
            from ui.idea_extraction_window import IdeaExtractionWindow
            # 使用临时项目路径进行测试
            temp_project_path = os.path.join(os.getcwd(), "temp_test_project")
            os.makedirs(temp_project_path, exist_ok=True)
            app = IdeaExtractionWindow(temp_project_path)
            print("✓ 想法提取窗口创建成功，包含新功能")
            messagebox.showinfo("测试结果", "想法提取窗口已打开，可以看到新的进度条和日志功能")
        except Exception as e:
            print(f"✗ 想法提取窗口创建失败: {e}")
            messagebox.showerror("错误", f"想法提取窗口创建失败: {e}")
    
    # 创建测试按钮
    tk.Button(root, text="测试大纲理解窗口", command=test_outline_understanding, height=2, width=25).pack(pady=20)
    tk.Button(root, text="测试想法提取窗口", command=test_idea_extraction, height=2, width=25).pack(pady=20)
    
    # 显示功能说明
    features_text = """
改进的功能特性：
• 进度条：显示处理进度，让用户了解当前状态
• 日志系统：实时显示处理步骤和状态信息
• UI优化：采用上下分栏布局，更合理分配空间
• 防重复提交：处理期间禁用按钮，避免重复请求
• 时间戳：日志带有时间戳，便于追踪处理过程
    """
    
    tk.Label(root, text=features_text, justify=tk.LEFT, font=("Arial", 10)).pack(pady=20)
    
    print("测试界面已打开")
    root.mainloop()

if __name__ == "__main__":
    test_improved_features()