import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading
import sqlite3
import os
import requests
import time
from utils.config_manager import config_manager


class OutlineUnderstandingWindow:
    """
    大纲理解窗口类
    包含顶部的页面名字和运行按钮，
    以及左右分栏的文本输入区域和AI提取显示区域
    """

    def __init__(self, project_path):
        """
        初始化大纲理解窗口
        
        Args:
            project_path (str): 工程文件路径
        """
        self.project_path = project_path
        self.api_key = config_manager.get_api_key()  # 从全局配置加载API密钥
        
        # 创建工程数据库路径
        self.db_path = os.path.join(project_path, 'project.db')
        
        self.root = tk.Toplevel()
        self.root.title("大纲理解")
        self.root.geometry("1000x700")
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        top_frame = tk.Frame(self.root, bg="#f0f0f0", height=50)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # 页面名字标签
        title_label = tk.Label(top_frame, text="大纲理解", font=("Microsoft YaHei", 12, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 运行按钮
        self.run_btn = tk.Button(top_frame, text="运行", command=self.run_ai_analysis, 
                           bg="#28a745", fg="white", relief="flat")
        self.run_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 保存按钮
        save_btn = tk.Button(top_frame, text="保存", command=self.save_outline_data, 
                            bg="#ffc107", fg="black", relief="flat")
        save_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 主内容框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建上下分割窗口 - 上半部分放左右分栏，下半部分放日志
        vertical_paned = tk.PanedWindow(main_frame, orient=tk.VERTICAL)
        vertical_paned.pack(fill=tk.BOTH, expand=True)
        
        # 上半部分 - 文本输入和结果展示
        content_frame = tk.Frame(vertical_paned)
        
        # 分割窗口
        paned_window = tk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧文本输入区域
        left_frame = tk.Frame(paned_window)
        left_label = tk.Label(left_frame, text="文本输入区域", font=("Microsoft YaHei", 10))
        left_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        self.text_input = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, width=50, height=20)
        self.text_input.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 右侧AI提取显示区域
        right_frame = tk.Frame(paned_window)
        right_label = tk.Label(right_frame, text="AI提取显示区域", font=("Microsoft YaHei", 10))
        right_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        self.result_display = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=50, height=20)
        self.result_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加左右面板到分割窗口
        paned_window.add(left_frame)
        paned_window.add(right_frame)
        
        # 下半部分 - 日志和进度
        log_frame = tk.Frame(vertical_paned)
        
        # 进度条
        progress_label = tk.Label(log_frame, text="进度:", font=("Microsoft YaHei", 10))
        progress_label.pack(anchor=tk.NW, padx=5, pady=(5, 0))
        
        self.progress = ttk.Progressbar(log_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 日志显示区域
        log_title = tk.Label(log_frame, text="处理日志:", font=("Microsoft YaHei", 10))
        log_title.pack(anchor=tk.NW, padx=5, pady=(5, 0))
        
        self.log_display = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=6, state='disabled')
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加上下两部分到垂直分割窗口
        vertical_paned.add(content_frame)
        vertical_paned.add(log_frame)
        
        # 默认禁用运行按钮直到有文本输入
        self.run_btn.config(state='disabled')
        self.text_input.bind('<KeyRelease>', self.check_text_input)
    
    def check_text_input(self, event=None):
        """检查文本输入并启用/禁用运行按钮"""
        input_text = self.text_input.get("1.0", tk.END).strip()
        if input_text:
            self.run_btn.config(state='normal')
        else:
            self.run_btn.config(state='disabled')
        
    def run_ai_analysis(self):
        """运行AI分析"""
        input_text = self.text_input.get("1.0", tk.END).strip()
            
        if not input_text:
            messagebox.showwarning("警告", "请输入要分析的文本")
            return
                
        if not self.api_key:
            messagebox.showwarning("警告", "请先配置API密钥")
            return
            
        # 清空之前的日志并添加新的日志
        self.clear_log()
        self.log_message("开始分析...")
            
        # 启动进度条
        self.progress.start()
            
        # 禁用运行按钮以防止重复点击
        self.run_btn.config(state='disabled')
            
        # 在新线程中运行AI分析，避免阻塞UI
        analysis_thread = threading.Thread(target=self.perform_ai_analysis, args=(input_text,))
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def perform_ai_analysis(self, input_text):
        """执行AI分析"""
        try:
            self.root.after(0, lambda: self.log_message("正在调用AI进行分析..."))
            
            # 调用AI分析（使用真实的API调用）
            result = self.ai_analysis(input_text)
            
            # 在主线程中更新结果
            self.root.after(0, self.update_result_display, result)
        except Exception as e:
            error_msg = "分析过程中出现错误: " + str(e)
            self.root.after(0, self.update_result_display, error_msg)
    
    def ai_analysis(self, input_text):
        """
        AI分析函数 - 使用真实的DeepSeek API
        """
        # 构建提示词
        prompt = ("请对以下故事文本进行详细分析，按照以下六个方面进行整理：\n\n一、核心故事线（剧情脉络）\n二、人物角色\n三、关键场景细节\n四、世界观设定与科技逻辑\n五、主题与象征\n六、叙事结构特点\n\n故事文本：\n" + input_text + "\n\n请按照上述六个方面进行详细分析。")

        # API请求参数
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",  # 或其他适用的模型
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"]
                return result
            else:
                error_msg = "API请求失败，状态码: " + str(response.status_code) + ", 错误信息: " + str(response.text)
                return error_msg
        except Exception as e:
            return "API调用过程中出现错误: " + str(e)
    
    def log_message(self, message):
        """向日志区域添加消息"""
        self.log_display.config(state='normal')
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = "[" + timestamp + "] " + message + "\n"
        self.log_display.insert(tk.END, formatted_message)
        self.log_display.see(tk.END)
        self.log_display.config(state='disabled')
    
    def clear_log(self):
        """清空日志区域"""
        self.log_display.config(state='normal')
        self.log_display.delete(1.0, tk.END)
        self.log_display.config(state='disabled')
    
    def update_result_display(self, result):
        """更新结果显示区域"""
        self.result_display.delete("1.0", tk.END)
        self.result_display.insert("1.0", result)
        
        # 停止进度条
        self.progress.stop()
        
        # 重新启用运行按钮
        self.run_btn.config(state='normal')
        
        # 添加完成日志
        self.log_message("分析完成")
    
    def save_outline_data(self):
        """保存大纲数据到数据库"""
        try:
            # 获取当前分析结果
            result_text = self.result_display.get("1.0", tk.END).strip()
            input_text = self.text_input.get("1.0", tk.END).strip()
            
            if not result_text or result_text.startswith("API请求失败") or result_text.startswith("API调用过程中出现错误"):
                messagebox.showwarning("警告", "没有有效的分析结果可供保存")
                return
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建大纲理解表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outline_understanding (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    input_content TEXT,
                    analysis_result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入数据
            title = "大纲理解分析"
            cursor.execute('''
                INSERT INTO outline_understanding (title, input_content, analysis_result)
                VALUES (?, ?, ?)
            ''', (title, input_text, result_text))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "大纲理解数据已保存到数据库")
            
        except Exception as e:
            messagebox.showerror("错误", "保存数据时出现错误: " + str(e))


def main():
    # 测试函数
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    app = OutlineUnderstandingWindow(r"C:\test\project")  # 测试路径
    root.mainloop()


if __name__ == "__main__":
    main()