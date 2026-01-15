import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
import json
import requests
from functools import partial
from ui.outline_understanding_window import OutlineUnderstandingWindow
from ui.idea_extraction_window import IdeaExtractionWindow
from ui.outline_generation_window import OutlineGenerationWindow
from ui.chapter_generation_window import ChapterGenerationWindow
from ui.story_extraction_window import StoryExtractionWindow
try:
    from ui.entity_generation_window_wx import EntityGenerationWindow
except ImportError:
    # 如果wxPython版本不可用，则回退到tkinter版本
    from ui.entity_generation_window import EntityGenerationWindow
from ui.api_config_dialog import show_api_config_dialog
try:
    from ui.story_segmentation_window_wx import StorySegmentationWindow
except ImportError:
    # 如果wxPython版本不可用，则回退到tkinter版本
    from ui.story_segmentation_window import StorySegmentationWindow


class FunctionButton(tk.Button):
    """
    功能按钮类
    """
    
    def __init__(self, parent, title, description="", command=None):
        """
        初始化功能按钮
        
        Args:
            parent: 父组件
            title (str): 按钮标题
            description (str): 按钮描述
            command: 按钮点击事件
        """
        self.title = title
        self.description = description
        
        text = f"{title}\n\n{description}"
        super().__init__(parent, text=text, command=command, width=20, height=6,
                         bg="#ffffff", fg="#2c3e50", relief="flat", bd=1,
                         font=("Microsoft YaHei", 10, "bold"),
                         activebackground="#3498db", activeforeground="white",
                         wraplength=140, cursor="hand2",
                         highlightbackground="#bdc3c7", highlightcolor="#3498db")
        
        # 添加边框和阴影效果
        self.config(highlightthickness=2)
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        self.config(bg="#3498db", fg="white", relief="raised", bd=2)
    
    def on_leave(self, event):
        self.config(bg="#ffffff", fg="#2c3e50", relief="flat", bd=1)


class FunctionPanelWidget(ttk.Frame):
    """
    功能面板组件
    """
    
    def __init__(self, master):
        """初始化功能面板"""
        super().__init__(master)
        
        self.current_project_path = None
        
        self.setup_ui()
        self.setup_functions()
    
    def setup_ui(self):
        """设置界面"""
        # 顶部导航栏
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        back_btn = tk.Button(top_frame, text="← 返回工程文件列表", command=self.back_to_project_list,
                             bg="#34495e", fg="white", relief="flat",
                             font=("Microsoft YaHei", 10, "bold"), height=1,
                             cursor="hand2", padx=15, pady=8)
        back_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 为返回按钮添加悬停效果
        self.add_hover_effect(back_btn, "#2c3e50", "#34495e")
        
        # 当前工程文件信息标签
        self.project_info_label = tk.Label(top_frame, text="未选择工程文件",
                                           font=("Microsoft YaHei", 11, "bold"),
                                           fg="#2c3e50")
        self.project_info_label.pack(side=tk.LEFT, padx=(10, 0), expand=True)
        
        # API配置按钮
        api_config_btn = tk.Button(top_frame, text="API配置", command=self.open_api_config,
                                   bg="#3498db", fg="white", relief="flat",
                                   font=("Microsoft YaHei", 10, "bold"), height=1,
                                   cursor="hand2", padx=15, pady=8)
        api_config_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 为API配置按钮添加悬停效果
        self.add_hover_effect(api_config_btn, "#2980b9", "#3498db")
        
        # 功能按钮区域
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # 创建Canvas和Scrollbar用于滚动
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0, bg="#ecf0f1")
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # 存储回调函数
        self.back_callback = None
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def add_hover_effect(self, widget, enter_color, leave_color):
        """为按钮添加悬停效果"""
        def on_enter(event):
            widget.config(bg=enter_color)
        
        def on_leave(event):
            widget.config(bg=leave_color)
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def set_current_project(self, project_path):
        """设置当前工程文件路径"""
        self.current_project_path = project_path
        
        # 更新项目信息标签
        project_name = os.path.basename(project_path)
        self.project_info_label.config(text=f"当前工程文件: {project_name}")
    
    def setup_functions(self):
        """设置功能按钮"""
        # 功能列表
        functions = [
            {
                "title": "大纲理解",
                "description": "分析现有大纲",
                "handler": self.show_outline_understanding
            },
            {
                "title": "想法提取", 
                "description": "从文本中提取想法",
                "handler": self.show_idea_extraction
            },
            {
                "title": "大纲生成",
                "description": "生成故事大纲",
                "handler": self.show_outline_generation
            },
            {
                "title": "章节生成",
                "description": "生成章节内容",
                "handler": self.show_chapter_generation
            },
            {
                "title": "故事信息提取",
                "description": "提取角色等信息",
                "handler": self.show_story_info_extraction
            },
            {
                "title": "实体生成",
                "description": "生成实体相关信息",
                "handler": self.show_entity_generation
            },
            {
                "title": "故事分段",
                "description": "将故事分成段落",
                "handler": self.show_story_segmentation
            },
            {
                "title": "故事分场景",
                "description": "将故事分成场景",
                "handler": self.show_scene_split
            },
            {
                "title": "故事分镜头",
                "description": "将故事分成镜头",
                "handler": self.show_shot_split
            },
            {
                "title": "故事分关键帧",
                "description": "提取关键帧画面",
                "handler": self.show_keyframe_split
            },
            {
                "title": "关键帧生图",
                "description": "根据关键帧生成图像",
                "handler": self.show_keyframe_image_generation
            },
            {
                "title": "视频生成",
                "description": "生成视频内容",
                "handler": self.show_video_generation
            }
        ]
        
        # 计算每行列数
        items_per_row = 3  # 固定每行3个按钮
        
        # 添加功能按钮到网格布局
        for i, func in enumerate(functions):
            row = i // items_per_row
            col = i % items_per_row
            
            btn = FunctionButton(self.scrollable_frame, func["title"], func["description"], func["handler"])
            btn.grid(row=row, column=col, padx=10, pady=10)
    
    def open_api_config(self):
        """打开API配置对话框"""
        show_api_config_dialog(self.winfo_toplevel())
    
    def show_outline_understanding(self):
        """大纲理解功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        # 创建大纲理解窗口
        app = OutlineUnderstandingWindow(self.current_project_path)
        app.root.mainloop()
    
    def show_idea_extraction(self):
        """想法提取功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        # 创建想法提取窗口
        app = IdeaExtractionWindow(self.current_project_path)
        app.root.mainloop()
    
    def show_outline_generation(self):
        """大纲生成功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        # 创建大纲生成窗口
        app = OutlineGenerationWindow(self.current_project_path)
        app.root.mainloop()
    
    def show_chapter_generation(self):
        """章节生成功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        # 创建章节生成窗口
        app = ChapterGenerationWindow(self.current_project_path)
        app.root.mainloop()
    
    def show_story_info_extraction(self):
        """故事信息提取功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        # 创建故事信息提取窗口
        app = StoryExtractionWindow(self.current_project_path)
        app.root.mainloop()
    
    def show_entity_generation(self):
        """实体生成功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        # 创建实体生成窗口
        app = EntityGenerationWindow(self.current_project_path)
        
        # 检查是否是wxPython版本
        if hasattr(app, 'show'):
            # wxPython版本
            app.show()
        else:
            # tkinter版本
            app.root.mainloop()
    
    def show_story_segmentation(self):
        """故事分段功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        # 创建故事分段窗口
        app = StorySegmentationWindow(self.current_project_path)
            
        # 检查是否是wxPython版本
        if hasattr(app, 'show'):
            # wxPython版本
            app.show()
        else:
            # tkinter版本
            app.root.mainloop()
    
    def show_scene_split(self):
        """故事分场景功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        messagebox.showinfo("故事分场景", "故事分场景功能正在开发中...")
    
    def show_shot_split(self):
        """故事分镜头功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        messagebox.showinfo("故事分镜头", "故事分镜头功能正在开发中...")
    
    def show_keyframe_split(self):
        """故事分关键帧功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        messagebox.showinfo("故事分关键帧", "故事分关键帧功能正在开发中...")
    
    def show_keyframe_image_generation(self):
        """关键帧生图功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        messagebox.showinfo("关键帧生图", "关键帧生图功能正在开发中...")
    
    def show_video_generation(self):
        """视频生成功能"""
        if not self.current_project_path:
            self.show_no_project_warning()
            return
            
        messagebox.showinfo("视频生成", "视频生成功能正在开发中...")
    
    def show_no_project_warning(self):
        """显示未选择工程文件警告"""
        messagebox.showwarning("警告", "请先选择一个工程文件！")
    
    def back_to_project_list(self):
        """返回工程文件列表"""
        if self.back_callback:
            self.back_callback()
    
    def set_back_callback(self, callback):
        """设置返回回调函数"""
        self.back_callback = callback