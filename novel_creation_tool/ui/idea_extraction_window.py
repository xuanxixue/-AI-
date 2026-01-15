import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading
import sqlite3
import os
import requests
import time
from utils.config_manager import config_manager


class IdeaExtractionWindow:
    """
    想法提取窗口类
    包含顶部的页面名字和保存按钮，
    以及左右分栏的AI对话区域和提取显示区域
    """

    def __init__(self, project_path):
        """
        初始化想法提取窗口
        
        Args:
            project_path (str): 工程文件路径
        """
        self.project_path = project_path
        self.api_key = config_manager.get_api_key()  # 从全局配置加载API密钥
        
        # 创建工程数据库路径
        self.db_path = os.path.join(project_path, 'project.db')
        
        self.root = tk.Toplevel()
        self.root.title("想法提取")
        self.root.geometry("1000x700")
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        top_frame = tk.Frame(self.root, bg="#f0f0f0", height=50)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # 页面名字标签
        title_label = tk.Label(top_frame, text="想法提取", font=("Microsoft YaHei", 12, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 保存按钮
        save_btn = tk.Button(top_frame, text="保存", command=self.save_ideas, 
                            bg="#ffc107", fg="black", relief="flat")
        save_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 主内容框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建上下分割窗口 - 上半部分放左右分栏，下半部分放日志
        vertical_paned = tk.PanedWindow(main_frame, orient=tk.VERTICAL)
        vertical_paned.pack(fill=tk.BOTH, expand=True)
        
        # 上半部分 - 对话和提取显示
        content_frame = tk.Frame(vertical_paned)
        
        # 分割窗口
        paned_window = tk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧AI对话区域
        left_frame = tk.Frame(paned_window)
        left_label = tk.Label(left_frame, text="AI对话区域", font=("Microsoft YaHei", 10))
        left_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 对话历史显示区域
        self.chat_history = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, width=50, height=15)
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 输入框和发送按钮
        input_frame = tk.Frame(left_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.user_input = tk.Entry(input_frame)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.bind("<Return>", self.send_message)
        
        send_btn = tk.Button(input_frame, text="发送", command=self.send_message, 
                            bg="#28a745", fg="white", relief="flat")
        send_btn.pack(side=tk.RIGHT)
        
        # 右侧提取显示区域
        right_frame = tk.Frame(paned_window)
        right_label = tk.Label(right_frame, text="提取显示区域", font=("Microsoft YaHei", 10))
        right_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        self.extraction_display = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=50, height=20)
        self.extraction_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 提取按钮
        self.extract_btn = tk.Button(right_frame, text="提取想法", command=self.extract_ideas, 
                              bg="#17a2b8", fg="white", relief="flat")
        self.extract_btn.pack(pady=5)
        
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
    
    def send_message(self, event=None):
        """发送消息到AI"""
        user_message = self.user_input.get().strip()
        if not user_message:
            return
        
        # 显示用户消息
        self.chat_history.insert(tk.END, "我: " + user_message + "\n")
        self.chat_history.see(tk.END)
        self.user_input.delete(0, tk.END)
        
        # 在新线程中处理AI响应，避免阻塞UI
        ai_thread = threading.Thread(target=self.get_ai_response, args=(user_message,))
        ai_thread.daemon = True
        ai_thread.start()
    
    def get_ai_response(self, user_message):
        """获取AI响应"""
        try:
            # 检查API密钥
            if not self.api_key:
                self.root.after(0, lambda: self.display_ai_response("错误：请先配置API密钥"))
                return
            
            # 构建提示词
            prompt = "请与我讨论关于故事创作的想法。我说：" + user_message + "。请给出有建设性的回复。"
            
            # API请求参数
            headers = {
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }

            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                
                # 在主线程中更新聊天历史
                self.root.after(0, self.display_ai_response, ai_response)
            else:
                error_msg = "API请求失败，状态码: " + str(response.status_code)
                self.root.after(0, self.display_ai_response, error_msg)
        except Exception as e:
            error_msg = "API调用过程中出现错误: " + str(e)
            self.root.after(0, self.display_ai_response, error_msg)
    
    def display_ai_response(self, ai_response):
        """显示AI响应"""
        self.chat_history.insert(tk.END, "AI: " + ai_response + "\n\n")
        self.chat_history.see(tk.END)
    
    def extract_ideas(self):
        """提取想法"""
        chat_text = self.chat_history.get("1.0", tk.END).strip()
        
        if not chat_text:
            messagebox.showwarning("警告", "请先与AI对话获取想法")
            return
            
        if not self.api_key:
            messagebox.showwarning("警告", "请先配置API密钥")
            return
        
        # 清空之前的日志并添加新的日志
        self.clear_log()
        self.log_message("开始提取想法...")
        
        # 启动进度条
        self.progress.start()
        
        # 禁用提取按钮以防止重复点击
        self.extract_btn.config(state='disabled')
        
        # 在新线程中提取想法，避免阻塞UI
        extraction_thread = threading.Thread(target=self.perform_idea_extraction, args=(chat_text,))
        extraction_thread.daemon = True
        extraction_thread.start()
    
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
    
    def perform_idea_extraction(self, chat_text):
        """执行想法提取"""
        try:
            self.root.after(0, lambda: self.log_message("正在调用AI提取想法..."))
            
            # 构建提取提示词
            prompt = "请从以下AI对话内容中提取有价值的故事创作想法，并按照以下六个方面进行整理：\n\n一、核心故事线（剧情脉络）\n二、人物角色\n三、关键场景细节\n四、世界观设定与科技逻辑\n五、主题与象征\n六、叙事结构特点\n\n对话内容：\n" + chat_text + "\n\n请按照上述六个方面提取和整理故事创作想法。"

            # API请求参数
            headers = {
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }

            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                extracted_ideas = response.json()["choices"][0]["message"]["content"]
                
                # 在主线程中更新提取结果显示
                self.root.after(0, self.update_extraction_display, extracted_ideas)
            else:
                error_msg = "API请求失败，状态码: " + str(response.status_code)
                self.root.after(0, self.update_extraction_display, error_msg)
        except Exception as e:
            error_msg = "提取过程中出现错误: " + str(e)
            self.root.after(0, self.update_extraction_display, error_msg)
    
    def update_extraction_display(self, extracted_ideas):
        """更新提取结果显示区域"""
        self.extraction_display.delete("1.0", tk.END)
        self.extraction_display.insert("1.0", extracted_ideas)
        
        # 停止进度条
        self.progress.stop()
        
        # 重新启用提取按钮
        self.extract_btn.config(state='normal')
        
        # 添加完成日志
        self.log_message("想法提取完成")
    
    def save_ideas(self):
        """保存想法到数据库"""
        try:
            # 获取提取的想法内容
            ideas_text = self.extraction_display.get("1.0", tk.END).strip()
            chat_text = self.chat_history.get("1.0", tk.END).strip()
            
            if not ideas_text or ideas_text.startswith("API请求失败") or ideas_text.startswith("提取过程中出现错误"):
                messagebox.showwarning("警告", "没有有效的想法内容可供保存")
                return
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建想法表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extracted_ideas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    chat_content TEXT,
                    extracted_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入数据
            title = "想法提取分析"
            cursor.execute('''
                INSERT INTO extracted_ideas (title, chat_content, extracted_content)
                VALUES (?, ?, ?)
            ''', (title, chat_text, ideas_text))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "想法提取数据已保存到数据库")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存数据时出现错误: {str(e)}")


def main():
    """测试函数"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    app = IdeaExtractionWindow(r"C:\test\project")  # 测试路径
    root.mainloop()


if __name__ == "__main__":
    main()