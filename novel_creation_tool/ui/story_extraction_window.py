import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading
import sqlite3
import os
import requests
import time
from utils.config_manager import config_manager
import re
from PIL import Image, ImageTk
from io import BytesIO
import tempfile
import threading


class StoryExtractionWindow:
    """
    故事信息提取窗口类
    包含四个主要区域：
    - 左侧：已生成章节选择列表
    - 中间：实体提取和处理区域
    - 右侧：API配置区域（移除图像生成部分）
    """

    def __init__(self, project_path):
        """
        初始化故事信息提取窗口
        
        Args:
            project_path (str): 工程文件路径
        """
        self.project_path = project_path
        self.api_key = config_manager.get_api_key()  # 从全局配置加载API密钥
        
        # 创建工程数据库路径
        self.db_path = os.path.join(project_path, 'project.db')
        
        # 存储提取的实体数据
        self.entities_data = {}
        self.sentences_data = {}
        self.designs_data = {}
        self.prompts_data = {}
        
        # 操作取消标志
        self.cancel_flag = False
        
        self.root = tk.Toplevel()
        self.root.title("故事信息提取")
        self.root.geometry("1400x900")
        
        self.setup_ui()
        self.load_generated_chapters()
    
    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        top_frame = tk.Frame(self.root, bg="#f0f0f0", height=50)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # 页面名字标签
        title_label = tk.Label(top_frame, text="故事信息提取", font=("Microsoft YaHei", 12, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 主内容框架 - 三栏布局
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 分割窗口 - 三列
        paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧 - 已生成章节选择区域
        left_frame = tk.Frame(paned_window)
        left_label = tk.Label(left_frame, text="已生成章节", font=("Microsoft YaHei", 10))
        left_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 章节列表框
        listbox_frame = tk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 滚动条
        chapter_scrollbar = tk.Scrollbar(listbox_frame)
        chapter_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 列表框
        self.chapter_listbox = tk.Listbox(listbox_frame, yscrollcommand=chapter_scrollbar.set, selectmode=tk.SINGLE)
        self.chapter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chapter_scrollbar.config(command=self.chapter_listbox.yview)
        
        # 绑定章节列表选择事件
        self.chapter_listbox.bind("<<ListboxSelect>>", self.on_chapter_select)
        
        # 添加到分割窗口
        paned_window.add(left_frame, stretch="always")
        
        # 中间 - 实体提取和处理区域
        middle_frame = tk.Frame(paned_window)
        middle_label = tk.Label(middle_frame, text="实体提取与处理", font=("Microsoft YaHei", 10))
        middle_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 创建笔记本控件用于显示四个步骤
        notebook = ttk.Notebook(middle_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 第一步：实体提取表格框架
        entities_frame = tk.Frame(notebook)
        notebook.add(entities_frame, text="实体提取")
        
        # 创建实体表格
        entities_columns = ('类型', '名称', '出现次数', '描述')
        self.entities_tree = ttk.Treeview(entities_frame, columns=entities_columns, show='headings', height=10)
        
        # 定义列宽和标题
        entities_column_widths = {
            '类型': 80, '名称': 120, '出现次数': 80, '描述': 250
        }
        
        for col in entities_columns:
            self.entities_tree.heading(col, text=col)
            self.entities_tree.column(col, width=entities_column_widths[col])
        
        # 添加滚动条
        entities_scrollbar_y = tk.Scrollbar(entities_frame, orient=tk.VERTICAL, command=self.entities_tree.yview)
        entities_scrollbar_x = tk.Scrollbar(entities_frame, orient=tk.HORIZONTAL, command=self.entities_tree.xview)
        self.entities_tree.configure(yscrollcommand=entities_scrollbar_y.set, xscrollcommand=entities_scrollbar_x.set)
        
        # 布局表格和滚动条
        self.entities_tree.grid(row=0, column=0, sticky='nsew')
        entities_scrollbar_y.grid(row=0, column=1, sticky='ns')
        entities_scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        entities_frame.grid_rowconfigure(0, weight=1)
        entities_frame.grid_columnconfigure(0, weight=1)
        
        # 第二步：描述句子提取表格框架
        sentences_frame = tk.Frame(notebook)
        notebook.add(sentences_frame, text="描述句子提取")
        
        # 创建描述句子表格
        sentences_columns = ('实体名称', '相关句子', '句子类型')
        self.sentences_tree = ttk.Treeview(sentences_frame, columns=sentences_columns, show='headings', height=10)
        
        # 定义列宽和标题
        sentences_column_widths = {
            '实体名称': 120, '相关句子': 300, '句子类型': 100
        }
        
        for col in sentences_columns:
            self.sentences_tree.heading(col, text=col)
            self.sentences_tree.column(col, width=sentences_column_widths[col])
        
        # 添加滚动条
        sentences_scrollbar_y = tk.Scrollbar(sentences_frame, orient=tk.VERTICAL, command=self.sentences_tree.yview)
        sentences_scrollbar_x = tk.Scrollbar(sentences_frame, orient=tk.HORIZONTAL, command=self.sentences_tree.xview)
        self.sentences_tree.configure(yscrollcommand=sentences_scrollbar_y.set, xscrollcommand=sentences_scrollbar_x.set)
        
        # 布局表格和滚动条
        self.sentences_tree.grid(row=0, column=0, sticky='nsew')
        sentences_scrollbar_y.grid(row=0, column=1, sticky='ns')
        sentences_scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        sentences_frame.grid_rowconfigure(0, weight=1)
        sentences_frame.grid_columnconfigure(0, weight=1)
        
        # 第三步：样式设计表格框架
        designs_frame = tk.Frame(notebook)
        notebook.add(designs_frame, text="样式设计")
        
        # 创建样式设计表格
        designs_columns = ('实体名称', '样式类型', '详细设计', '参考描述')
        self.designs_tree = ttk.Treeview(designs_frame, columns=designs_columns, show='headings', height=10)
        
        # 定义列宽和标题
        designs_column_widths = {
            '实体名称': 120, '样式类型': 100, '详细设计': 250, '参考描述': 150
        }
        
        for col in designs_columns:
            self.designs_tree.heading(col, text=col)
            self.designs_tree.column(col, width=designs_column_widths[col])
        
        # 添加滚动条
        designs_scrollbar_y = tk.Scrollbar(designs_frame, orient=tk.VERTICAL, command=self.designs_tree.yview)
        designs_scrollbar_x = tk.Scrollbar(designs_frame, orient=tk.HORIZONTAL, command=self.designs_tree.xview)
        self.designs_tree.configure(yscrollcommand=designs_scrollbar_y.set, xscrollcommand=designs_scrollbar_x.set)
        
        # 布局表格和滚动条
        self.designs_tree.grid(row=0, column=0, sticky='nsew')
        designs_scrollbar_y.grid(row=0, column=1, sticky='ns')
        designs_scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        designs_frame.grid_rowconfigure(0, weight=1)
        designs_frame.grid_columnconfigure(0, weight=1)
        
        # 第四步：提示词生成表格框架
        prompts_frame = tk.Frame(notebook)
        notebook.add(prompts_frame, text="提示词生成")
        
        # 创建提示词生成表格
        prompts_columns = ('实体名称', '视角', '详细提示词', '用途')
        self.prompts_tree = ttk.Treeview(prompts_frame, columns=prompts_columns, show='headings', height=10)
        
        # 定义列宽和标题
        prompts_column_widths = {
            '实体名称': 120, '视角': 100, '详细提示词': 300, '用途': 100
        }
        
        for col in prompts_columns:
            self.prompts_tree.heading(col, text=col)
            self.prompts_tree.column(col, width=prompts_column_widths[col])
        
        # 添加滚动条
        prompts_scrollbar_y = tk.Scrollbar(prompts_frame, orient=tk.VERTICAL, command=self.prompts_tree.yview)
        prompts_scrollbar_x = tk.Scrollbar(prompts_frame, orient=tk.HORIZONTAL, command=self.prompts_tree.xview)
        self.prompts_tree.configure(yscrollcommand=prompts_scrollbar_y.set, xscrollcommand=prompts_scrollbar_x.set)
        
        # 布局表格和滚动条
        self.prompts_tree.grid(row=0, column=0, sticky='nsew')
        prompts_scrollbar_y.grid(row=0, column=1, sticky='ns')
        prompts_scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        prompts_frame.grid_rowconfigure(0, weight=1)
        prompts_frame.grid_columnconfigure(0, weight=1)
        
        # 创建按钮框架
        buttons_frame = tk.Frame(middle_frame)
        buttons_frame.pack(pady=5)
        
        # 四个步骤的按钮
        extract_entities_btn = tk.Button(buttons_frame, text="第一步：提取实体", command=self.extract_entities, 
                               bg="#17a2b8", fg="white", relief="flat")
        extract_entities_btn.pack(side=tk.LEFT, padx=5)
        
        extract_sentences_btn = tk.Button(buttons_frame, text="第二步：提取描述句子", command=self.extract_sentences, 
                               bg="#007bff", fg="white", relief="flat")
        extract_sentences_btn.pack(side=tk.LEFT, padx=5)
        
        design_styles_btn = tk.Button(buttons_frame, text="第三步：样式设计", command=self.design_styles, 
                               bg="#28a745", fg="white", relief="flat")
        design_styles_btn.pack(side=tk.LEFT, padx=5)
        
        generate_prompts_btn = tk.Button(buttons_frame, text="第四步：生成提示词", command=self.generate_prompts, 
                               bg="#ffc107", fg="black", relief="flat")
        generate_prompts_btn.pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        save_results_btn = tk.Button(buttons_frame, text="保存结果", command=self.save_results, 
                               bg="#28a55e", fg="white", relief="flat")
        save_results_btn.pack(side=tk.LEFT, padx=5)
        
        # 取消按钮
        cancel_btn = tk.Button(buttons_frame, text="取消操作", command=self.cancel_operation, 
                               bg="#dc3545", fg="white", relief="flat")
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加到分割窗口
        paned_window.add(middle_frame, stretch="always")
        
        # 右侧 - API配置区域
        right_frame = tk.Frame(paned_window)
        right_label = tk.Label(right_frame, text="API配置", font=("Microsoft YaHei", 10))
        right_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # API配置区域
        api_config_frame = tk.LabelFrame(right_frame, text="API配置", padx=5, pady=5)
        api_config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(api_config_frame, text="API Key:").pack(anchor=tk.W)
        self.api_key_entry = tk.Entry(api_config_frame, show="*")
        self.api_key_entry.pack(fill=tk.X, pady=2)
        
        # 显示/隐藏密码按钮
        self.show_password_var = tk.BooleanVar()
        show_password_check = tk.Checkbutton(
            api_config_frame, 
            text="显示密码", 
            variable=self.show_password_var,
            command=self.toggle_password_visibility
        )
        show_password_check.pack(anchor=tk.W)
        
        # 保存按钮
        save_api_btn = tk.Button(
            api_config_frame, 
            text="保存API配置", 
            command=self.save_api_config,
            bg="#ffc107", 
            fg="black", 
            relief="flat"
        )
        save_api_btn.pack(pady=5)
        
        # 底部 - 日志和进度
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 进度条
        progress_label = tk.Label(bottom_frame, text="进度:", font=("Microsoft YaHei", 10))
        progress_label.pack(anchor=tk.NW, padx=5, pady=(5, 0))
        
        self.progress = ttk.Progressbar(bottom_frame, mode='determinate', maximum=100)
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 日志显示区域
        log_title = tk.Label(bottom_frame, text="处理日志:", font=("Microsoft YaHei", 10))
        log_title.pack(anchor=tk.NW, padx=5, pady=(5, 0))
        
        self.log_display = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, height=6, state='disabled')
        self.log_display.pack(fill=tk.X, padx=5, pady=5)
        
        # 初始化API配置
        self.load_api_config()

    def extract_entities(self):
        """提取实体清单（出现次数>=1的实体）"""
        # 首先清空实体表格
        for item in self.entities_tree.get_children():
            self.entities_tree.delete(item)
        
        # 获取当前章节内容
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个章节")
            return
        
        if not self.api_key:
            messagebox.showwarning("警告", "请先配置API密钥")
            return
        
        # 使用线程处理，避免界面卡顿
        def thread_func():
            try:
                index = selection[0]
                chapter_info = self.chapter_listbox.get(index)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 提取标题（去掉时间部分）
                chapter_title = chapter_info.split(' (')[0]
                
                cursor.execute('SELECT content FROM generated_chapters WHERE title = ?', (chapter_title,))
                result = cursor.fetchone()
                
                if result:
                    content = result[0]
                    
                    # 更新进度条
                    self.root.after(0, lambda: self.update_progress(20))
                    
                    # 使用AI提取实体
                    entities = self.extract_entities_with_ai(content)
                    
                    # 更新进度条
                    self.root.after(0, lambda: self.update_progress(60))
                    
                    # 清空之前的数据
                    self.entities_data = {}
                    
                    # 在主线程中更新表格
                    def update_ui():
                        for entity in entities:
                            values = (
                                entity['type'],
                                entity['name'],
                                entity['count'],
                                entity['description']
                            )
                            self.entities_tree.insert('', 'end', values=values)
                            
                            # 存储实体数据
                            self.entities_data[entity['name']] = entity
                        
                        self.log_message(f"实体提取完成，共提取 {len(entities)} 个实体")
                        self.update_progress(100)  # 完成进度
                    
                    self.root.after(0, update_ui)
                else:
                    self.root.after(0, lambda: self.log_message(f"找不到章节: {chapter_title}"))
                
                conn.close()
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"提取实体时出错: {str(e)}"))
                self.root.after(0, lambda: self.update_progress(0))
        
        # 重置取消标志
        self.reset_cancel_flag()
        # 启动线程
        extraction_thread = threading.Thread(target=thread_func)
        extraction_thread.daemon = True
        extraction_thread.start()

    def extract_entities_with_ai(self, text):
        """使用AI提取实体（出现次数>=1）"""
        try:
            if not self.api_key:
                self.log_message("未配置API密钥，跳过AI提取")
                return []
                
            # 记录开始时间
            start_time = time.time()
            self.log_message("开始AI实体提取...")
            
            # 构建提示词，要求AI提取实体并统计出现次数
            prompt = f"""请从以下小说文本中提取所有出现的角色、场景和道具，并统计它们的出现次数（仅包括出现次数>=1的实体），按照JSON格式返回：

要求：
- 只统计在文本中实际出现的实体（出现次数>=1）
- 对每个实体提供基本描述
- 类型分为：CHARACTER（角色）、SCENE（场景）、OBJECT（道具）
- 返回格式严格按照以下JSON格式：
{{
  "entities": [
    {{
      "type": "CHARACTER|SCENE|OBJECT",
      "name": "实体名称",
      "count": 出现次数,
      "description": "实体描述"
    }}
  ]
}}

请只返回JSON格式数据，不要包含其他内容。

文本：{text}"""

            headers = {
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1  # 降低温度，提高一致性
            }
            
            self.log_message("正在发送AI实体提取请求...")
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120  # 减少超时时间到2分钟
            )
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                self.log_message("收到AI响应，正在解析数据...")
                
                # 查找JSON部分
                import json as json_lib
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx+1]
                    try:
                        parsed = json_lib.loads(json_str)
                        if 'entities' in parsed:
                            entities = parsed['entities']
                            # 过滤出现次数>=1的实体
                            filtered_entities = [e for e in entities if e.get('count', 0) >= 1]
                            elapsed_time = time.time() - start_time
                            self.log_message(f"AI实体提取完成，耗时 {elapsed_time:.2f} 秒")
                            return filtered_entities
                    except json_lib.JSONDecodeError:
                        self.log_message("实体提取JSON解析失败，尝试修复...")
                        # 尝试修复常见的JSON问题
                        try:
                            fixed_json = self.fix_common_json_issues(json_str)
                            if fixed_json:
                                parsed = json_lib.loads(fixed_json)
                                if 'entities' in parsed:
                                    entities = parsed['entities']
                                    # 过滤出现次数>=1的实体
                                    filtered_entities = [e for e in entities if e.get('count', 0) >= 1]
                                    elapsed_time = time.time() - start_time
                                    self.log_message(f"AI实体提取完成（经修复），耗时 {elapsed_time:.2f} 秒")
                                    return filtered_entities
                        except json_lib.JSONDecodeError:
                            pass
                
                # 如果JSON解析失败，使用备用方法
                self.log_message("AI返回格式不符合预期，使用备用方法")
                # 这里可以根据需要实现备用解析方法
                return []
            else:
                self.log_message(f"AI实体提取失败: {response.status_code}, {response.text}")
                return []
        except requests.exceptions.Timeout:
            self.log_message("AI实体提取请求超时（超过2分钟）")
            return []
        except Exception as e:
            self.log_message(f"AI实体提取过程中出现错误: {str(e)}")
            return []

    def extract_sentences(self):
        """提取包含实体的描述句子"""
        # 首先清空句子表格
        for item in self.sentences_tree.get_children():
            self.sentences_tree.delete(item)
        
        # 检查是否已有实体数据
        if not self.entities_data:
            messagebox.showwarning("警告", "请先执行实体提取")
            return
        
        # 获取当前章节内容
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个章节")
            return
        
        if not self.api_key:
            messagebox.showwarning("警告", "请先配置API密钥")
            return
        
        # 使用线程处理，避免界面卡顿
        def thread_func():
            try:
                index = selection[0]
                chapter_info = self.chapter_listbox.get(index)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 提取标题（去掉时间部分）
                chapter_title = chapter_info.split(' (')[0]
                
                cursor.execute('SELECT content FROM generated_chapters WHERE title = ?', (chapter_title,))
                result = cursor.fetchone()
                
                if result:
                    content = result[0]
                    
                    # 更新进度条
                    self.root.after(0, lambda: self.update_progress(20))
                    
                    # 使用AI提取包含实体的描述句子
                    sentences = self.extract_sentences_with_ai(content, self.entities_data)
                    
                    # 更新进度条
                    self.root.after(0, lambda: self.update_progress(60))
                    
                    # 清空之前的数据
                    self.sentences_data = {}
                    
                    # 在主线程中更新表格
                    def update_ui():
                        for sentence in sentences:
                            values = (
                                sentence['entity_name'],
                                sentence['sentence'],
                                sentence['sentence_type']
                            )
                            self.sentences_tree.insert('', 'end', values=values)
                            
                            # 存储句子数据
                            if sentence['entity_name'] not in self.sentences_data:
                                self.sentences_data[sentence['entity_name']] = []
                            self.sentences_data[sentence['entity_name']].append(sentence)
                        
                        self.log_message(f"描述句子提取完成，共提取 {len(sentences)} 个句子")
                        self.update_progress(100)  # 完成进度
                    
                    self.root.after(0, update_ui)
                else:
                    self.root.after(0, lambda: self.log_message(f"找不到章节: {chapter_title}"))
                
                conn.close()
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"提取描述句子时出错: {str(e)}"))
                self.root.after(0, lambda: self.update_progress(0))
        
        # 重置取消标志
        self.reset_cancel_flag()
        # 启动线程
        extraction_thread = threading.Thread(target=thread_func)
        extraction_thread.daemon = True
        extraction_thread.start()

    def extract_sentences_with_ai(self, text, entities_data):
        """使用AI提取包含实体的描述句子"""
        try:
            if not self.api_key:
                self.log_message("未配置API密钥，跳过AI提取")
                return []
                
            # 记录开始时间
            start_time = time.time()
            self.log_message("开始AI句子提取...")
            
            # 构建实体列表字符串
            entities_list = [f"{entity['name']} ({entity['type']})" for entity in entities_data.values()]
            entities_str = ", ".join(entities_list)
            
            # 构建提示词，要求AI提取包含实体的描述句子
            prompt = f"""请从以下小说文本中提取包含以下实体的描述性句子：

实体列表：{entities_str}

要求：
- 提取包含实体的描述性句子（不仅仅是提及实体的简单句子）
- 识别句子类型（外观描述、行为描述、环境描述等）
- 每个实体至少提取1个描述句子
- 返回格式严格按照以下JSON格式：

{{
  "sentences": [
    {{
      "entity_name": "实体名称",
      "sentence": "包含该实体的描述句子",
      "sentence_type": "句子类型（如：外观描述、行为描述、环境描述等）"
    }}
  ]
}}

请只返回JSON格式数据，不要包含其他内容。

文本：{text}"""

            headers = {
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1  # 降低温度，提高一致性
            }
            
            self.log_message("正在发送AI句子提取请求...")
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120  # 减少超时时间到2分钟
            )
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                self.log_message("收到AI响应，正在解析数据...")
                
                # 查找JSON部分
                import json as json_lib
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx+1]
                    try:
                        parsed = json_lib.loads(json_str)
                        if 'sentences' in parsed:
                            sentences = parsed['sentences']
                            elapsed_time = time.time() - start_time
                            self.log_message(f"AI句子提取完成，耗时 {elapsed_time:.2f} 秒")
                            return sentences
                    except json_lib.JSONDecodeError:
                        self.log_message("句子提取JSON解析失败，尝试修复...")
                        # 尝试修复常见的JSON问题
                        try:
                            fixed_json = self.fix_common_json_issues(json_str)
                            if fixed_json:
                                parsed = json_lib.loads(fixed_json)
                                if 'sentences' in parsed:
                                    sentences = parsed['sentences']
                                    elapsed_time = time.time() - start_time
                                    self.log_message(f"AI句子提取完成（经修复），耗时 {elapsed_time:.2f} 秒")
                                    return sentences
                        except json_lib.JSONDecodeError:
                            pass
                
                # 如果JSON解析失败，使用备用方法
                self.log_message("AI返回格式不符合预期，使用备用方法")
                # 这里可以根据需要实现备用解析方法
                return []
            else:
                self.log_message(f"AI句子提取失败: {response.status_code}, {response.text}")
                return []
        except requests.exceptions.Timeout:
            self.log_message("AI句子提取请求超时（超过2分钟）")
            return []
        except Exception as e:
            self.log_message(f"AI句子提取过程中出现错误: {str(e)}")
            return []

    def design_styles(self):
        """设计实体的样式"""
        # 首先清空样式设计表格
        for item in self.designs_tree.get_children():
            self.designs_tree.delete(item)
        
        # 检查是否已有实体数据
        if not self.entities_data:
            messagebox.showwarning("警告", "请先执行实体提取")
            return
        
        # 获取当前章节内容
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个章节")
            return
        
        if not self.api_key:
            messagebox.showwarning("警告", "请先配置API密钥")
            return
        
        # 使用线程处理，避免界面卡顿
        def thread_func():
            try:
                index = selection[0]
                chapter_info = self.chapter_listbox.get(index)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 提取标题（去掉时间部分）
                chapter_title = chapter_info.split(' (')[0]
                
                cursor.execute('SELECT content FROM generated_chapters WHERE title = ?', (chapter_title,))
                result = cursor.fetchone()
                
                if result:
                    content = result[0]
                    
                    # 更新进度条
                    self.root.after(0, lambda: self.update_progress(20))
                    
                    # 使用并行方式为实体设计样式
                    designs = self.design_styles_for_entities_parallel(content, self.entities_data)
                    
                    # 更新进度条
                    self.root.after(0, lambda: self.update_progress(60))
                    
                    # 清空之前的数据
                    self.designs_data = {}
                    
                    # 在主线程中更新表格
                    def update_ui():
                        for design in designs:
                            values = (
                                design['entity_name'],
                                design['style_type'],
                                design['detailed_design'],
                                design['reference_description']
                            )
                            self.designs_tree.insert('', 'end', values=values)
                            
                            # 存储设计数据
                            self.designs_data[design['entity_name']] = design
                        
                        self.log_message(f"样式设计完成，共设计 {len(designs)} 个实体样式")
                        self.update_progress(100)  # 完成进度
                    
                    self.root.after(0, update_ui)
                else:
                    self.root.after(0, lambda: self.log_message(f"找不到章节: {chapter_title}"))
                
                conn.close()
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"样式设计时出错: {str(e)}"))
                self.root.after(0, lambda: self.update_progress(0))
        
        # 重置取消标志
        self.reset_cancel_flag()
        # 启动线程
        extraction_thread = threading.Thread(target=thread_func)
        extraction_thread.daemon = True
        extraction_thread.start()

    def design_styles_with_ai(self, text, entities_data):
        """使用AI设计实体样式"""
        try:
            if not self.api_key:
                self.log_message("未配置API密钥，跳过AI提取")
                return []
                
            # 记录开始时间
            start_time = time.time()
            self.log_message(f"开始AI样式设计...（共{len(entities_data)}个实体）")
            
            # 分批处理实体，避免单次请求过大
            entity_names = list(entities_data.keys())
            batch_size = 5  # 每批处理5个实体
            all_designs = []
            
            for i in range(0, len(entity_names), batch_size):
                if self.cancel_flag:
                    self.log_message("样式设计被用户取消")
                    return []
                
                batch_names = entity_names[i:i + batch_size]
                batch_entities = {name: entities_data[name] for name in batch_names}
                
                # 构建实体列表字符串
                entities_list = []
                for name, entity in batch_entities.items():
                    entities_list.append(f"{name} ({entity['type']}) - {entity['description']}")
                entities_str = "; ".join(entities_list)
                
                # 构建提示词，要求AI为实体设计样式
                prompt = f"""请为以下实体设计详细的视觉样式：

实体详情：{entities_str}

要求：
- 为每个实体设计详细的视觉样式
- 包括颜色、形状、材质、大小、状态等具体细节
- 区分不同类型实体的设计重点（角色注重外貌，场景注重环境，道具注重外观）
- 生成的样式描述必须是中文
- 不要添加艺术风格和比例相关的描述
- 返回格式严格按照以下JSON格式：

{{
  "designs": [
    {{
      "entity_name": "实体名称",
      "style_type": "样式类型",
      "detailed_design": "详细的设计描述",
      "reference_description": "参考描述"
    }}
  ]
}}

请只返回JSON格式数据，不要包含其他内容。"""

                headers = {
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1  # 降低温度，提高一致性
                }
                
                self.log_message(f"正在发送样式设计请求（批次{i//batch_size + 1}/{(len(entity_names) + batch_size - 1)//batch_size}）...")
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=120  # 减少超时时间到2分钟
                )
                
                if response.status_code == 200:
                    ai_response = response.json()["choices"][0]["message"]["content"]
                    self.log_message(f"收到批次{i//batch_size + 1}的AI响应，正在解析数据...")
                    
                    # 查找JSON部分
                    import json as json_lib
                    start_idx = ai_response.find('{')
                    end_idx = ai_response.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        json_str = ai_response[start_idx:end_idx+1]
                        try:
                            parsed = json_lib.loads(json_str)
                            if 'designs' in parsed:
                                batch_designs = parsed['designs']
                                all_designs.extend(batch_designs)
                                # 更新进度条
                                progress = min(100, int((i + len(batch_names)) / len(entity_names) * 60) + 20)
                                self.root.after(0, lambda p=progress: self.update_progress(p))
                        except json_lib.JSONDecodeError:
                            self.log_message(f"批次{i//batch_size + 1}的JSON解析失败，尝试备用方法")
                            # 尝试修复常见的JSON问题
                            try:
                                fixed_json = self.fix_common_json_issues(json_str)
                                if fixed_json:
                                    parsed = json_lib.loads(fixed_json)
                                    if 'designs' in parsed:
                                        batch_designs = parsed['designs']
                                        all_designs.extend(batch_designs)
                            except json_lib.JSONDecodeError:
                                pass
                else:
                    self.log_message(f"AI样式设计失败: {response.status_code}, {response.text}")
                    
                # 避免API请求过于频繁，添加小延迟
                time.sleep(1)
            
            elapsed_time = time.time() - start_time
            self.log_message(f"AI样式设计完成，总共耗时 {elapsed_time:.2f} 秒，生成 {len(all_designs)} 个样式")
            return all_designs
            
        except requests.exceptions.Timeout:
            self.log_message("AI样式设计请求超时（超过2分钟）")
            return []
        except Exception as e:
            self.log_message(f"AI样式设计过程中出现错误: {str(e)}")
            return []
    
    def design_styles_for_entity_with_ai(self, entity_name, entity_data, text):
        """使用AI为单个实体设计样式"""
        try:
            if not self.api_key:
                self.log_message("未配置API密钥，跳过AI提取")
                # 返回默认设计
                return {
                    "entity_name": entity_name,
                    "style_type": "默认样式",
                    "detailed_design": f"{entity_name}的默认设计描述",
                    "reference_description": "默认参考描述"
                }
                
            # 记录开始时间
            start_time = time.time()
            self.log_message(f"开始为实体 '{entity_name}' 设计样式...")
            
            # 构建实体列表字符串
            entity_info = f"{entity_name} ({entity_data['type']}) - {entity_data['description']}"
            
            # 构建提示词，要求AI为实体设计样式
            prompt = f"""请为以下实体设计详细的视觉样式：

实体详情：{entity_info}

要求：
- 为实体设计详细的视觉样式
- 包括颜色、形状、材质、大小、状态等具体细节
- 区分不同类型实体的设计重点（角色注重外貌，场景注重环境，道具注重外观）
- 生成的样式描述必须是中文
- 不要添加艺术风格和比例相关的描述
- 返回格式严格按照以下JSON格式：

{{
  "designs": [
    {{
      "entity_name": "{entity_name}",
      "style_type": "样式类型",
      "detailed_design": "详细的设计描述",
      "reference_description": "参考描述"
    }}
  ]
}}

请只返回JSON格式数据，不要包含其他内容。"""

            headers = {
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1  # 降低温度，提高一致性
            }
            
            self.log_message(f"正在发送样式设计请求（实体: {entity_name}）...")
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120  # 减少超时时间到2分钟
            )
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                self.log_message(f"收到实体 '{entity_name}' 的AI响应，正在解析数据...")
                
                # 查找JSON部分
                import json as json_lib
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx+1]
                    try:
                        parsed = json_lib.loads(json_str)
                        if 'designs' in parsed:
                            designs = parsed['designs']
                            elapsed_time = time.time() - start_time
                            self.log_message(f"实体 '{entity_name}' 的AI样式设计完成，耗时 {elapsed_time:.2f} 秒")
                            return designs[0] if len(designs) > 0 else {
                                "entity_name": entity_name,
                                "style_type": "默认样式",
                                "detailed_design": f"{entity_name}的默认设计描述",
                                "reference_description": "默认参考描述"
                            }
                    except json_lib.JSONDecodeError:
                        self.log_message(f"实体 '{entity_name}' 的JSON解析失败，尝试修复...")
                        # 尝试修复常见的JSON问题
                        try:
                            fixed_json = self.fix_common_json_issues(json_str)
                            if fixed_json:
                                parsed = json_lib.loads(fixed_json)
                                if 'designs' in parsed:
                                    designs = parsed['designs']
                                    elapsed_time = time.time() - start_time
                                    self.log_message(f"实体 '{entity_name}' 的AI样式设计完成（经修复），耗时 {elapsed_time:.2f} 秒")
                                    return designs[0] if len(designs) > 0 else {
                                        "entity_name": entity_name,
                                        "style_type": "默认样式",
                                        "detailed_design": f"{entity_name}的默认设计描述",
                                        "reference_description": "默认参考描述"
                                    }
                        except json_lib.JSONDecodeError:
                            pass
            else:
                self.log_message(f"AI样式设计失败: {response.status_code}, {response.text}")
                
            # 如果AI请求失败或解析失败，返回默认设计
            return {
                "entity_name": entity_name,
                "style_type": "默认样式",
                "detailed_design": f"{entity_name}的默认设计描述",
                "reference_description": "默认参考描述"
            }
        except requests.exceptions.Timeout:
            self.log_message(f"实体 '{entity_name}' 的AI样式设计请求超时（超过2分钟）")
            return {
                "entity_name": entity_name,
                "style_type": "默认样式",
                "detailed_design": f"{entity_name}的默认设计描述",
                "reference_description": "默认参考描述"
            }
        except Exception as e:
            self.log_message(f"AI样式设计过程中出现错误: {str(e)}")
            return {
                "entity_name": entity_name,
                "style_type": "默认样式",
                "detailed_design": f"{entity_name}的默认设计描述",
                "reference_description": "默认参考描述"
            }
    
    def design_styles_for_entities_parallel(self, text, entities_data):
        """使用并行方式为多个实体设计样式"""
        import concurrent.futures
        
        all_designs = []
        entities_items = list(entities_data.items())
        
        # 创建一个字典来跟踪每个实体是否已处理
        processed_entities = {}
        
        # 使用ThreadPoolExecutor并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(entities_items), 5)) as executor:
            # 提交所有任务
            future_to_entity = {
                executor.submit(self.design_styles_for_entity_with_ai, entity_name, entity_data, text): entity_name 
                for entity_name, entity_data in entities_items
            }
            
            # 收集已完成的结果
            for future in concurrent.futures.as_completed(future_to_entity):
                entity_name = future_to_entity[future]
                try:
                    entity_design = future.result()
                    if entity_design:
                        all_designs.append(entity_design)
                        processed_entities[entity_name] = True
                        self.log_message(f"实体 '{entity_name}' 的样式设计完成")
                except Exception as e:
                    self.log_message(f"实体 '{entity_name}' 的样式设计失败: {str(e)}")
                    # 添加默认设计作为备选
                    default_design = {
                        "entity_name": entity_name,
                        "style_type": "默认样式",
                        "detailed_design": f"{entity_name}的默认设计描述",
                        "reference_description": "默认参考描述"
                    }
                    all_designs.append(default_design)
                    processed_entities[entity_name] = True
        
        # 确保所有实体都有对应的设计（处理可能遗漏的异常情况）
        for entity_name, entity_data in entities_items:
            if entity_name not in processed_entities:
                # 如果某个实体没有被处理，则创建默认设计
                default_design = {
                    "entity_name": entity_name,
                    "style_type": "默认样式",
                    "detailed_design": f"{entity_name}的默认设计描述",
                    "reference_description": "默认参考描述"
                }
                all_designs.append(default_design)
                self.log_message(f"实体 '{entity_name}' 由于异常情况使用默认设计")
        
        return all_designs
    
    def fix_common_json_issues(self, json_str):
        """修复常见的JSON格式问题"""
        try:
            import re
            # 尝试修复一些常见的JSON问题
            fixed = json_str.strip()
            # 确保引号正确配对
            quote_count = fixed.count('"')
            if quote_count % 2 != 0:
                # 如果引号不成对，尝试找到最后一个正确的闭合位置
                last_quote = fixed.rfind('"')
                fixed = fixed[:last_quote]
                
            # 确保括号配对
            bracket_count = 0
            brace_count = 0
            for i, char in enumerate(fixed):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                
                if bracket_count < 0 or brace_count < 0:
                    fixed = fixed[:i]
                    break
            
            # 尝试添加缺失的结束括号
            while brace_count > 0:
                fixed += "}"
                brace_count -= 1
            while bracket_count > 0:
                fixed += "]"
                bracket_count -= 1
            
            return fixed
        except:
            return None

    def generate_prompts(self):
        """生成4个不同视角的提示词"""
        # 首先清空提示词表格
        for item in self.prompts_tree.get_children():
            self.prompts_tree.delete(item)
        
        # 检查是否已有设计数据
        if not self.designs_data:
            messagebox.showwarning("警告", "请先执行样式设计")
            return
        
        # 获取当前章节内容
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个章节")
            return
        
        if not self.api_key:
            messagebox.showwarning("警告", "请先配置API密钥")
            return
        
        # 使用线程处理，避免界面卡顿
        def thread_func():
            try:
                index = selection[0]
                chapter_info = self.chapter_listbox.get(index)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 提取标题（去掉时间部分）
                chapter_title = chapter_info.split(' (')[0]
                
                cursor.execute('SELECT content FROM generated_chapters WHERE title = ?', (chapter_title,))
                result = cursor.fetchone()
                
                if result:
                    content = result[0]
                    
                    # 更新进度条
                    self.root.after(0, lambda: self.update_progress(10))
                    
                    # 使用并行方式为所有实体生成4个不同视角的提示词
                    all_prompts = self.generate_prompts_for_entities_parallel(self.designs_data, content)
                    
                    # 更新进度条
                    self.root.after(0, lambda: self.update_progress(60))
                    
                    # 清空之前的数据
                    self.prompts_data = {}
                    
                    # 在主线程中更新表格
                    def update_ui():
                        for prompt in all_prompts:
                            values = (
                                prompt['entity_name'],
                                prompt['perspective'],
                                prompt['detailed_prompt'],
                                prompt['usage']
                            )
                            self.prompts_tree.insert('', 'end', values=values)
                            
                            # 存储提示词数据
                            if prompt['entity_name'] not in self.prompts_data:
                                self.prompts_data[prompt['entity_name']] = []
                            self.prompts_data[prompt['entity_name']].append(prompt)
                        
                        self.log_message(f"提示词生成完成，共生成 {len(all_prompts)} 个提示词")
                        self.update_progress(100)  # 完成进度
                    
                    self.root.after(0, update_ui)
                else:
                    self.root.after(0, lambda: self.log_message(f"找不到章节: {chapter_title}"))
                
                conn.close()
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"提示词生成时出错: {str(e)}"))
                self.root.after(0, lambda: self.update_progress(0))
        
        # 重置取消标志
        self.reset_cancel_flag()
        # 启动线程
        extraction_thread = threading.Thread(target=thread_func)
        extraction_thread.daemon = True
        extraction_thread.start()

    def generate_prompts_for_entity_with_ai(self, entity_name, design, text):
        """使用AI为单个实体生成4个不同视角的提示词"""
        try:
            if not self.api_key:
                self.log_message("未配置API密钥，跳过AI提取")
                # 返回默认中文提示词
                return self.get_default_prompts(entity_name)
                
            # 记录开始时间
            start_time = time.time()
            self.log_message(f"开始为实体 '{entity_name}' 生成AI提示词...")
            
            # 构建提示词，要求AI为实体生成4个不同视角的详细提示词
            prompt = f"""请为实体 '{entity_name}' 基于以下设计，生成4个不同视角的详细AI绘画提示词：

实体设计：{design['detailed_design'] if isinstance(design, dict) and 'detailed_design' in design else str(design)}

要求：
- 生成4个不同视角的详细提示词：正面视角(Front View)、侧面视角(Side View)、背面视角(Back View)、特写视角(Close-up View)
- 每个提示词都要非常详细，包含具体的外观特征、颜色、形状、材质、大小、状态等细节信息
- 使用专业AI绘画术语
- 每个提示词都应适合用于文生图模型
- 生成的提示词必须是中文
- 不要添加艺术风格和比例相关的描述
- 返回格式严格按照以下JSON格式：

{{
  "prompts": [
    {{
      "entity_name": "{entity_name}",
      "perspective": "正面视角(Front View)",
      "detailed_prompt": "正面视角的详细AI绘画提示词",
      "usage": "正面展示"
    }},
    {{
      "entity_name": "{entity_name}",
      "perspective": "侧面视角(Side View)",
      "detailed_prompt": "侧面视角的详细AI绘画提示词",
      "usage": "侧面展示"
    }},
    {{
      "entity_name": "{entity_name}",
      "perspective": "背面视角(Back View)",
      "detailed_prompt": "背面视角的详细AI绘画提示词",
      "usage": "背面展示"
    }},
    {{
      "entity_name": "{entity_name}",
      "perspective": "特写视角(Close-up View)",
      "detailed_prompt": "特写视角的详细AI绘画提示词",
      "usage": "细节特写"
    }}
  ]
}}

请只返回JSON格式数据，不要包含其他内容。"""

            headers = {
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1  # 降低温度，提高一致性
            }
            
            self.log_message(f"正在发送AI提示词生成请求（实体: {entity_name}）...")
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60  # 减少超时时间到1分钟
            )
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                self.log_message(f"收到实体 '{entity_name}' 的AI响应，正在解析数据...")
                
                # 查找JSON部分
                import json as json_lib
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx+1]
                    try:
                        parsed = json_lib.loads(json_str)
                        if 'prompts' in parsed:
                            prompts = parsed['prompts']
                            elapsed_time = time.time() - start_time
                            self.log_message(f"实体 '{entity_name}' 的AI提示词生成完成，耗时 {elapsed_time:.2f} 秒")
                            return prompts
                    except json_lib.JSONDecodeError:
                        self.log_message(f"实体 '{entity_name}' 的JSON解析失败，尝试修复...")
                        # 尝试修复常见的JSON问题
                        try:
                            fixed_json = self.fix_common_json_issues(json_str)
                            if fixed_json:
                                parsed = json_lib.loads(fixed_json)
                                if 'prompts' in parsed:
                                    prompts = parsed['prompts']
                                    elapsed_time = time.time() - start_time
                                    self.log_message(f"实体 '{entity_name}' 的AI提示词生成完成（经修复），耗时 {elapsed_time:.2f} 秒")
                                    return prompts
                        except json_lib.JSONDecodeError:
                            pass
                
                # 如果JSON解析失败，使用备用方法
                self.log_message("AI返回格式不符合预期，使用备用方法")
                # 返回默认格式
                return self.get_default_prompts(entity_name)
            else:
                self.log_message(f"AI提示词生成失败: {response.status_code}, {response.text}")
                return self.get_default_prompts(entity_name)
        except requests.exceptions.Timeout:
            self.log_message(f"实体 '{entity_name}' 的AI提示词生成请求超时（超过1分钟）")
            # 返回默认格式作为备选
            return self.get_default_prompts(entity_name)
        except Exception as e:
            self.log_message(f"AI提示词生成过程中出现错误: {str(e)}")
            return self.get_default_prompts(entity_name)

    def generate_prompts_for_entities_parallel(self, entities_designs, text):
        """使用并行方式为多个实体生成提示词"""
        import concurrent.futures
        
        all_prompts = []
        entities_items = list(entities_designs.items())
        
        # 创建一个字典来跟踪每个实体是否已处理
        processed_entities = {}
        
        # 使用ThreadPoolExecutor并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(entities_items), 5)) as executor:
            # 提交所有任务
            future_to_entity = {
                executor.submit(self.generate_prompts_for_entity_with_ai, entity_name, design, text): entity_name 
                for entity_name, design in entities_items
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_entity):
                entity_name = future_to_entity[future]
                try:
                    entity_prompts = future.result()
                    all_prompts.extend(entity_prompts)
                    processed_entities[entity_name] = True
                    self.log_message(f"实体 '{entity_name}' 的提示词生成完成")
                except Exception as e:
                    self.log_message(f"实体 '{entity_name}' 的提示词生成失败: {str(e)}")
                    # 添加默认提示词作为备选
                    default_prompts = self.get_default_prompts(entity_name)
                    all_prompts.extend(default_prompts)
                    processed_entities[entity_name] = True
        
        # 确保所有实体都有对应的提示词（处理可能遗漏的异常情况）
        for entity_name, design in entities_items:
            if entity_name not in processed_entities:
                # 如果某个实体没有被处理，则创建默认提示词
                default_prompts = self.get_default_prompts(entity_name)
                all_prompts.extend(default_prompts)
                self.log_message(f"实体 '{entity_name}' 由于异常情况使用默认提示词")
        
        return all_prompts

    def get_default_prompts(self, entity_name):
        """获取默认的提示词"""
        return [
            {
                "entity_name": entity_name,
                "perspective": "正面视角(Front View)",
                "detailed_prompt": f"正面视角的{entity_name}。清晰地展示所有特征。高质量专业图像。",
                "usage": "正面展示"
            },
            {
                "entity_name": entity_name,
                "perspective": "侧面视角(Side View)",
                "detailed_prompt": f"侧面视角的{entity_name}。展示轮廓和侧面特征。高质量专业图像。",
                "usage": "侧面展示"
            },
            {
                "entity_name": entity_name,
                "perspective": "背面视角(Back View)",
                "detailed_prompt": f"背面视角的{entity_name}。展示背面特征。高质量专业图像。",
                "usage": "背面展示"
            },
            {
                "entity_name": entity_name,
                "perspective": "特写视角(Close-up View)",
                "detailed_prompt": f"{entity_name}的特写细节视图。聚焦于复杂细节和纹理。高质量专业图像。",
                "usage": "细节特写"
            }
        ]

    def load_api_config(self):
        """加载API配置"""
        try:
            # 尝试从配置管理器获取API密钥
            saved_key = config_manager.get_modelscope_api_key()
            if saved_key:
                self.api_key_entry.insert(0, saved_key)
        except:
            # 如果配置管理器中没有存储，使用默认值或空值
            pass
    
    def toggle_password_visibility(self):
        """切换密码可见性"""
        if self.show_password_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
    
    def save_api_config(self):
        """保存API配置"""
        api_key = self.api_key_entry.get().strip()
        if api_key:
            try:
                config_manager.set_modelscope_api_key(api_key)
                messagebox.showinfo("成功", "API配置已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存API配置时出错: {str(e)}")
        else:
            messagebox.showwarning("警告", "请输入API Key")
    
    def load_generated_chapters(self):
        """加载已生成的章节列表"""
        try:
            # 清空列表框
            self.chapter_listbox.delete(0, tk.END)
            
            # 检查数据库是否存在
            if not os.path.exists(self.db_path):
                self.log_message(f"数据库文件不存在: {self.db_path}")
                return
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询已生成的章节
            cursor.execute('''
                SELECT id, title, content, created_at 
                FROM generated_chapters 
                ORDER BY created_at DESC
            ''')
            chapters = cursor.fetchall()
            
            # 添加到列表框
            for chapter in chapters:
                chapter_id, title, content, created_at = chapter
                display_text = f"{title} ({created_at})"
                self.chapter_listbox.insert(tk.END, display_text)
            
            conn.close()
            
            self.log_message(f"加载了 {len(chapters)} 个已生成的章节")
            
        except Exception as e:
            self.log_message(f"加载已生成章节时出错: {str(e)}")
    
    def on_chapter_select(self, event):
        """当选中已生成章节列表中的项目时触发"""
        selection = self.chapter_listbox.curselection()
        if selection:
            index = selection[0]
            chapter_info = self.chapter_listbox.get(index)
            self.log_message(f"选择了已生成章节: {chapter_info}")

    def update_progress(self, value):
        """更新进度条"""
        self.progress['value'] = value

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

    def save_results(self):
        """保存提取和生成的结果到数据库"""
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个章节")
            return
        
        try:
            index = selection[0]
            chapter_info = self.chapter_listbox.get(index)
            chapter_title = chapter_info.split(' (')[0]
            
            # 创建安全的表名（移除特殊字符）
            safe_table_name = self.create_safe_table_name(chapter_title)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建实体表
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS `{safe_table_name}_entities` (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    count INTEGER,
                    description TEXT
                )
            ''')
            
            # 创建句子表
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS `{safe_table_name}_sentences` (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_name TEXT NOT NULL,
                    sentence TEXT NOT NULL,
                    sentence_type TEXT
                )
            ''')
            
            # 创建设计表
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS `{safe_table_name}_designs` (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_name TEXT NOT NULL,
                    style_type TEXT,
                    detailed_design TEXT,
                    reference_description TEXT
                )
            ''')
            
            # 创建提示词表
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS `{safe_table_name}_prompts` (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_name TEXT NOT NULL,
                    perspective TEXT,
                    detailed_prompt TEXT,
                    usage TEXT
                )
            ''')
            
            # 清空现有数据
            cursor.execute(f"DELETE FROM `{safe_table_name}_entities`")
            cursor.execute(f"DELETE FROM `{safe_table_name}_sentences`")
            cursor.execute(f"DELETE FROM `{safe_table_name}_designs`")
            cursor.execute(f"DELETE FROM `{safe_table_name}_prompts`")
            
            # 从界面上获取当前数据显示的数据并保存
            # 保存实体数据
            for item in self.entities_tree.get_children():
                values = self.entities_tree.item(item)['values']
                if len(values) >= 4:
                    cursor.execute(f"INSERT INTO `{safe_table_name}_entities` (type, name, count, description) VALUES (?, ?, ?, ?)", 
                                 (values[0], values[1], values[2], values[3]))
            
            # 保存句子数据
            for item in self.sentences_tree.get_children():
                values = self.sentences_tree.item(item)['values']
                if len(values) >= 3:
                    cursor.execute(f"INSERT INTO `{safe_table_name}_sentences` (entity_name, sentence, sentence_type) VALUES (?, ?, ?)", 
                                 (values[0], values[1], values[2]))
            
            # 保存设计数据
            for item in self.designs_tree.get_children():
                values = self.designs_tree.item(item)['values']
                if len(values) >= 4:
                    cursor.execute(f"INSERT INTO `{safe_table_name}_designs` (entity_name, style_type, detailed_design, reference_description) VALUES (?, ?, ?, ?)", 
                                 (values[0], values[1], values[2], values[3]))
            
            # 保存提示词数据
            for item in self.prompts_tree.get_children():
                values = self.prompts_tree.item(item)['values']
                if len(values) >= 4:
                    cursor.execute(f"INSERT INTO `{safe_table_name}_prompts` (entity_name, perspective, detailed_prompt, usage) VALUES (?, ?, ?, ?)", 
                                 (values[0], values[1], values[2], values[3]))
            
            conn.commit()
            conn.close()
            
            self.log_message(f"结果已保存到章节 '{chapter_title}' 对应的表中")
            messagebox.showinfo("成功", f"章节 '{chapter_title}' 的提取结果已保存")
            
        except Exception as e:
            self.log_message(f"保存结果时出错: {str(e)}")
            messagebox.showerror("错误", f"保存结果时出错: {str(e)}")
    
    def create_safe_table_name(self, title):
        """创建安全的表名，移除非字母数字字符"""
        import re
        # 只保留字母、数字和下划线，其他字符替换为下划线
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', title)
        # 确保表名不超过64个字符
        if len(safe_name) > 50:
            safe_name = safe_name[:50]
        # 确保表名不为空
        if not safe_name:
            safe_name = "default_table"
        return safe_name

    def cancel_operation(self):
        """取消当前操作"""
        self.cancel_flag = True
        self.log_message("操作已被用户取消")
        self.update_progress(0)  # 重置进度条
        
    def reset_cancel_flag(self):
        """重置取消标志"""
        self.cancel_flag = False

def main():
    """测试函数"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    app = StoryExtractionWindow(r"C:\test\project")  # 测试路径
    root.mainloop()


if __name__ == "__main__":
    main()