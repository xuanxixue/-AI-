import tkinter as tk
from tkinter import ttk, messagebox
from utils.config_manager import config_manager


class ApiConfigDialog:
    """
    API配置对话框
    """
    
    def __init__(self, parent):
        """
        初始化API配置对话框
        
        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.result = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("API配置")
        self.dialog.geometry("400x200")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (400 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (200 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标签
        ttk.Label(main_frame, text="请输入Deepseek API密钥:", font=("Microsoft YaHei", 10)).pack(anchor=tk.W, pady=(0, 10))
        
        # 输入框
        self.api_entry = ttk.Entry(main_frame, width=40, show="*")
        self.api_entry.pack(pady=(0, 20))
        
        # 加载已保存的API密钥
        saved_api_key = config_manager.get_api_key()
        if saved_api_key:
            self.api_entry.insert(0, saved_api_key)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        # 取消按钮
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存按钮
        ttk.Button(button_frame, text="保存", command=self.save_api_key).pack(side=tk.LEFT)
        
        # 绑定回车键
        self.api_entry.bind('<Return>', lambda e: self.save_api_key())
        
        # 设置焦点
        self.api_entry.focus()
    
    def save_api_key(self):
        """保存API密钥"""
        api_key = self.api_entry.get().strip()
        if api_key:
            config_manager.set_api_key(api_key)
            messagebox.showinfo("成功", "API密钥已保存")
            self.dialog.destroy()
        else:
            messagebox.showwarning("警告", "请输入有效的API密钥")
    
    def cancel(self):
        """取消"""
        self.dialog.destroy()


def show_api_config_dialog(parent):
    """
    显示API配置对话框
    
    Args:
        parent: 父窗口
    """
    dialog = ApiConfigDialog(parent)
    parent.wait_window(dialog.dialog)
    return dialog.result