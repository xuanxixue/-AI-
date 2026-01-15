import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading
import sqlite3
import os
import requests
import time
from utils.config_manager import config_manager
import tkinter.font as tkFont


class ChapterGenerationWindow:
    """
    章节生成窗口类
    包含三个主要区域：
    - 左侧：大纲显示区域（结构树格式）
    - 中间：生成区域（显示章节内容、保存按钮、局部更改按钮、智能更改按钮）
    - 右侧：已生成章节列表
    - 底部：进度条和日志
    """

    def __init__(self, project_path, outline_data=None):
        """
        初始化章节生成窗口
        
        Args:
            project_path (str): 工程文件路径
            outline_data (str): 大纲数据，如果为空则从数据库加载最新大纲
        """
        self.project_path = project_path
        self.outline_data = outline_data
        self.api_key = config_manager.get_api_key()  # 从全局配置加载API密钥
        
        # 创建工程数据库路径
        self.db_path = os.path.join(project_path, 'project.db')
        
        self.root = tk.Toplevel()
        self.root.title("章节生成")
        self.root.geometry("1400x900")
        
        self.setup_ui()
        self.load_outline_data()
        self.load_generated_chapters()
    
    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        top_frame = tk.Frame(self.root, bg="#f0f0f0", height=50)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # 页面名字标签
        title_label = tk.Label(top_frame, text="章节生成", font=("Microsoft YaHei", 12, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 主内容框架 - 三栏布局
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 分割窗口 - 三列
        paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧 - 大纲显示区域
        left_frame = tk.Frame(paned_window)
        left_label = tk.Label(left_frame, text="大纲显示", font=("Microsoft YaHei", 10))
        left_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 创建大纲树形视图
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 滚动条
        tree_scrollbar = tk.Scrollbar(tree_frame)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 树形视图
        self.outline_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scrollbar.set)
        self.outline_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.config(command=self.outline_tree.yview)
        
        # 设置树形视图列
        self.outline_tree.heading("#0", text="大纲结构", anchor=tk.W)
        
        # 绑定树形视图选择事件
        self.outline_tree.bind("<<TreeviewSelect>>", self.on_outline_select)
        
        # 初始化选择项
        self.selected_outline_item = None
        
        # 添加到分割窗口
        paned_window.add(left_frame, stretch="always")
        
        # 中间 - 生成结果显示区域
        middle_frame = tk.Frame(paned_window)
        middle_label = tk.Label(middle_frame, text="章节生成", font=("Microsoft YaHei", 10))
        middle_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 章节内容显示区域
        self.chapter_display = scrolledtext.ScrolledText(middle_frame, wrap=tk.WORD, width=40, height=20)
        self.chapter_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 控制按钮区域
        control_frame = tk.Frame(middle_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 保存按钮
        save_btn = tk.Button(control_frame, text="保存章节", command=self.save_chapter, 
                            bg="#ffc107", fg="black", relief="flat")
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 局部更改按钮
        partial_update_btn = tk.Button(control_frame, text="局部更改", command=self.partial_update, 
                                      bg="#17a2b8", fg="white", relief="flat")
        partial_update_btn.pack(side=tk.LEFT, padx=5)
        
        # 智能更改按钮
        smart_update_btn = tk.Button(control_frame, text="智能更改", command=self.smart_update, 
                                    bg="#6f42c1", fg="white", relief="flat")
        smart_update_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加生成按钮
        generate_btn = tk.Button(control_frame, text="生成章节", command=self.generate_chapter_from_selection, 
                                bg="#28a745", fg="white", relief="flat")
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加到分割窗口
        paned_window.add(middle_frame, stretch="always")
        
        # 右侧 - 已生成章节列表
        right_frame = tk.Frame(paned_window)
        right_label = tk.Label(right_frame, text="已生成章节", font=("Microsoft YaHei", 10))
        right_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 章节列表框
        listbox_frame = tk.Frame(right_frame)
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
        paned_window.add(right_frame, stretch="always")
        
        # 底部 - 日志和进度
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 进度条
        progress_label = tk.Label(bottom_frame, text="进度:", font=("Microsoft YaHei", 10))
        progress_label.pack(anchor=tk.NW, padx=5, pady=(5, 0))
        
        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 日志显示区域
        log_title = tk.Label(bottom_frame, text="处理日志:", font=("Microsoft YaHei", 10))
        log_title.pack(anchor=tk.NW, padx=5, pady=(5, 0))
        
        self.log_display = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, height=6, state='disabled')
        self.log_display.pack(fill=tk.X, padx=5, pady=5)
    
    def load_outline_data(self):
        """加载大纲数据并构建树形结构"""
        try:
            # 如果提供了outline_data，则解析并构建树
            if self.outline_data:
                self.parse_and_build_outline_tree(self.outline_data)
            else:
                # 否则尝试从数据库加载最新的大纲
                self.load_latest_outline_from_db()
                
        except Exception as e:
            self.log_message(f"加载大纲数据时出错: {str(e)}")
            messagebox.showerror("错误", f"加载大纲数据时出错: {str(e)}")
    
    def parse_and_build_outline_tree(self, outline_text):
        """解析大纲文本并构建树形结构"""
        # 清空现有的树
        for item in self.outline_tree.get_children():
            self.outline_tree.delete(item)
        
        # 解析大纲文本 - 移除可能的标题和元数据
        lines = outline_text.split('\n')
        
        # 尝试识别并跳过标题行（如"大纲生成_YYYYMMDD_HHMMSS"）
        start_idx = 0
        for idx, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith('# ') or stripped_line.startswith('## ') or stripped_line.startswith('### ') or \
               stripped_line.startswith('【') or stripped_line.startswith('第') or \
               ('章' in stripped_line and stripped_line.startswith('第')):
                start_idx = idx
                break
        
        # 重新设置lines为从有意义内容开始
        lines = lines[start_idx:]
        
        # 用于跟踪各级别的父节点
        current_section_node = None  # 当前部分节点
        current_chapter_node = None  # 当前章节节点
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行
            if not line:
                i += 1
                continue
                
            # 检查是否是标题级别（## 【第一部分】或### 第X章）
            if line.startswith('## 【') and '】' in line:
                # 这是一个部分标题
                section_title = line[3:].strip()  # 去掉'## '
                current_section_node = self.outline_tree.insert("", "end", text=section_title, values=(i, "section"))
                current_chapter_node = None  # 重置章节节点
                
            elif line.startswith('### 第') and ('章' in line or '节' in line):
                # 这是章节标题
                chapter_title = line[4:].strip()  # 去掉'### '
                if current_section_node:
                    current_chapter_node = self.outline_tree.insert(current_section_node, "end", text=chapter_title, values=(i, "chapter"))
                else:
                    # 如果没有部分节点，创建一个默认部分
                    current_section_node = self.outline_tree.insert("", "end", text="【默认部分】", values=(i, "section"))
                    current_chapter_node = self.outline_tree.insert(current_section_node, "end", text=chapter_title, values=(i, "chapter"))
                
            # 检查是否是部分标题（如【第一部分：甜如初春】）
            elif line.startswith('【') and '】' in line:
                # 这是一个部分标题
                current_section_node = self.outline_tree.insert("", "end", text=line, values=(i, "section"))
                current_chapter_node = None  # 重置章节节点
                
            # 检查是否是章节标题（如 第1章 樱落时遇见你）
            elif line.startswith('第') and ('章' in line or '节' in line) and len(line) < 100:  # 长度过长的可能不是章节标题
                # 创建章节节点，父节点为当前部分
                if current_section_node:
                    current_chapter_node = self.outline_tree.insert(current_section_node, "end", text=line, values=(i, "chapter"))
                else:
                    # 如果没有部分节点，创建一个默认部分
                    current_section_node = self.outline_tree.insert("", "end", text="【默认部分】", values=(i, "section"))
                    current_chapter_node = self.outline_tree.insert(current_section_node, "end", text=line, values=(i, "chapter"))
                
            # 检查是否是章节描述内容（紧跟在章节标题后的几行）
            elif current_chapter_node and line and not line.startswith('【') and not line.startswith('第') and not line.startswith('#'):
                # 检查是否是连续的描述行
                j = i
                description_lines = []
                while j < len(lines) and lines[j].strip() != "" and not lines[j].strip().startswith('第') and not lines[j].strip().startswith('【') and not lines[j].strip().startswith('#'):
                    description_lines.append(lines[j].strip())
                    j += 1
                    # 限制描述行数量，避免将下一个章节内容包含进来
                    if len(description_lines) >= 3:
                        break
                
                if description_lines:
                    # 将章节描述作为子节点
                    description_text = "  " + "  ".join(description_lines[:2])  # 只取前两行作为描述
                    self.outline_tree.insert(current_chapter_node, "end", text=description_text, values=(i, "description"))
                
                # 跳过已处理的描述行
                i = j - 1
            
            # 添加对小说标题和核心设定的支持
            elif line.startswith('小说标题') and current_section_node is None and current_chapter_node is None:
                # 添加小说标题作为顶级节点
                self.outline_tree.insert("", "end", text=line, values=(i, "novel_title"))
            elif line.startswith('核心设定') and current_section_node is None and current_chapter_node is None:
                # 添加核心设定作为顶级节点
                self.outline_tree.insert("", "end", text=line, values=(i, "core_setting"))
            elif line.startswith('背景：') and current_section_node is None and current_chapter_node is None:
                # 添加背景作为顶级节点
                self.outline_tree.insert("", "end", text=line, values=(i, "background"))
            elif line.startswith('女主：') and current_section_node is None and current_chapter_node is None:
                # 添加角色信息作为顶级节点
                self.outline_tree.insert("", "end", text=line, values=(i, "character"))
            elif line.startswith('男主：') and current_section_node is None and current_chapter_node is None:
                # 添加角色信息作为顶级节点
                self.outline_tree.insert("", "end", text=line, values=(i, "character"))
            elif line.startswith('关键意象：') and current_section_node is None and current_chapter_node is None:
                # 添加关键意象作为顶级节点
                self.outline_tree.insert("", "end", text=line, values=(i, "key_image"))
            
            i += 1
    
    def load_latest_outline_from_db(self):
        """从数据库加载最新大纲，只从生成的大纲表中获取"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 只查询最新的生成大纲
            cursor.execute('''
                SELECT content, created_at 
                FROM generated_outlines 
                ORDER BY created_at DESC 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            
            if result:
                outline_content, created_at = result
                self.log_message(f"正在解析大纲内容: {outline_content[:200]}...")
                self.log_message(f"数据库中找到大纲，创建时间: {created_at}")
                
                # 确保大纲内容被正确解析并显示
                self.parse_and_build_outline_tree(outline_content)
                self.log_message(f"从数据库加载了创建于 {created_at} 的生成大纲，并成功解析")
            else:
                self.log_message("数据库中没有找到大纲数据")
                # 如果没有数据，插入一个提示
                self.outline_tree.insert("", "end", text="没有找到大纲数据，请先生成大纲")
                
            conn.close()
            
        except Exception as e:
            self.log_message(f"从数据库加载大纲时出错: {str(e)}")
    
    def on_outline_select(self, event):
        """当大纲树中选择某个项目时触发"""
        selection = self.outline_tree.selection()
        if selection:
            item = selection[0]
            item_text = self.outline_tree.item(item, "text")
            self.log_message(f"选择了大纲项目: {item_text}")
            
            # 仅记录选择，不自动触发生成，需要用户点击生成按钮
            self.selected_outline_item = item_text
    
    def generate_chapter_from_selection(self):
        """从选定的大纲项目生成章节"""
        if self.selected_outline_item:
            self.generate_chapter_for_outline_item(self.selected_outline_item)
        else:
            messagebox.showwarning("警告", "请先选择一个大纲项目")
    
    def on_chapter_select(self, event):
        """当选中已生成章节列表中的项目时触发"""
        selection = self.chapter_listbox.curselection()
        if selection:
            index = selection[0]
            chapter_info = self.chapter_listbox.get(index)
            self.log_message(f"选择了已生成章节: {chapter_info}")
            
            # 显示选中的章节内容
            self.display_chapter_content(index)
    
    def generate_chapter_for_outline_item(self, outline_item_text):
        """根据选中的大纲项目生成章节内容"""
        try:
            # 检查API密钥
            if not self.api_key:
                messagebox.showwarning("警告", "请先配置API密钥")
                return
            
            # 清空当前章节显示
            self.chapter_display.delete("1.0", tk.END)
            
            # 更新日志
            self.log_message(f"开始生成章节: {outline_item_text}")
            
            # 启动进度条
            self.progress.start()
            
            # 在新线程中生成章节，避免阻塞UI
            generation_thread = threading.Thread(
                target=self.perform_chapter_generation, 
                args=(outline_item_text,)
            )
            generation_thread.daemon = True
            generation_thread.start()
            
        except Exception as e:
            self.log_message(f"生成章节时出错: {str(e)}")
    
    def perform_chapter_generation(self, outline_item_text):
        """执行章节生成"""
        try:
            self.root.after(0, lambda: self.log_message("正在调用AI生成章节内容..."))
            
            # 调用AI生成章节
            result = self.generate_chapter_with_ai(outline_item_text)
            
            # 在主线程中更新结果
            self.root.after(0, self.update_chapter_display, result)
            
            # 停止进度条
            self.root.after(0, lambda: self.progress.stop())
            
            self.root.after(0, lambda: self.log_message("章节生成完成"))
            
        except Exception as e:
            error_msg = "章节生成过程中出现错误: " + str(e)
            self.root.after(0, lambda: self.update_chapter_display(error_msg))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.log_message(f"生成章节时出错: {str(e)}"))
    
    def generate_chapter_with_ai(self, outline_item_text):
        """
        使用AI生成章节内容
        """
        # 构建提示词，根据大纲章节生成详细内容
        prompt = f"""请根据以下章节大纲生成详细的章节内容。要求：
1. 内容丰富，情节连贯
2. 符合原大纲的情感基调
3. 人物对话自然流畅
4. 场景描写生动
5. 字数控制在1000-2000字左右

章节大纲：
{outline_item_text}

请生成完整的章节内容："""

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
    
    def update_chapter_display(self, result):
        """更新章节显示区域"""
        self.chapter_display.delete("1.0", tk.END)
        self.chapter_display.insert("1.0", result)
    
    def save_chapter(self):
        """保存当前章节到数据库"""
        try:
            # 获取当前显示的章节内容
            chapter_content = self.chapter_display.get("1.0", tk.END).strip()
            
            if not chapter_content:
                messagebox.showwarning("警告", "没有章节内容可供保存")
                return
            
            # 获取当前选中的大纲项目作为章节标题
            selected_items = self.outline_tree.selection()
            if selected_items:
                chapter_title = self.outline_tree.item(selected_items[0], "text")
            else:
                # 如果没有选中大纲项目，使用时间戳作为标题
                chapter_title = f"章节_{time.strftime('%Y%m%d_%H%M%S')}"
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建章节表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generated_chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    outline_ref TEXT,  -- 关联的大纲章节
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 检查是否已存在相同标题的章节
            cursor.execute('SELECT id FROM generated_chapters WHERE title = ?', (chapter_title,))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有章节
                cursor.execute('''
                    UPDATE generated_chapters 
                    SET content = ?, outline_ref = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE title = ?
                ''', (chapter_content, selected_items[0] if selected_items else "", chapter_title))
                self.log_message(f"更新了章节: {chapter_title}")
            else:
                # 插入新章节
                cursor.execute('''
                    INSERT INTO generated_chapters (title, content, outline_ref)
                    VALUES (?, ?, ?)
                ''', (chapter_title, chapter_content, selected_items[0] if selected_items else ""))
                self.log_message(f"保存了新章节: {chapter_title}")
            
            conn.commit()
            conn.close()
            
            # 刷新章节列表
            self.load_generated_chapters()
            
            messagebox.showinfo("成功", f"章节 '{chapter_title}' 已保存到数据库")
            
        except Exception as e:
            messagebox.showerror("错误", "保存章节时出现错误: " + str(e))
    
    def partial_update(self):
        """局部更改功能"""
        try:
            # 获取当前章节内容
            current_content = self.chapter_display.get("1.0", tk.END).strip()
            if not current_content:
                messagebox.showwarning("警告", "没有章节内容可供更改")
                return
            
            # 创建局部更改对话框，允许用户选择段落
            dialog = PartialUpdateDialog(self.root, current_content)
            self.root.wait_window(dialog)
            
            if dialog.result:
                selected_text, change_request = dialog.result
                
                # 如果用户没有选择特定文本，则使用整个内容
                if not selected_text:
                    selected_text = current_content
                
                # 启动进度条
                self.progress.start()
                
                # 在新线程中执行更改
                update_thread = threading.Thread(
                    target=self.perform_partial_update, 
                    args=(selected_text, change_request)
                )
                update_thread.daemon = True
                update_thread.start()
            
        except Exception as e:
            self.log_message(f"启动局部更改时出错: {str(e)}")
    
    def perform_partial_update(self, current_content, change_request):
        """执行局部更改"""
        try:
            self.root.after(0, lambda: self.log_message("正在根据您的要求进行局部更改..."))
            
            # 调用AI进行局部更改
            result = self.modify_chapter_partially(current_content, change_request)
            
            # 在主线程中更新结果
            self.root.after(0, self.update_chapter_display, result)
            
            # 停止进度条
            self.root.after(0, lambda: self.progress.stop())
            
            self.root.after(0, lambda: self.log_message("局部更改完成"))
            
        except Exception as e:
            error_msg = "局部更改过程中出现错误: " + str(e)
            self.root.after(0, lambda: self.update_chapter_display(error_msg))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.log_message(f"局部更改时出错: {str(e)}"))
    
    def modify_chapter_partially(self, current_content, change_request):
        """
        使用AI对章节进行局部修改
        """
        prompt = f"""请根据以下要求对章节内容进行局部修改：
        
需要修改的章节内容：
{current_content}

修改要求：
{change_request}

请注意：
1. 保持原有故事情节和人物关系
2. 只修改符合修改要求的部分内容
3. 保持整体风格一致
4. 不要大幅增加或删减内容

请返回修改后的完整章节内容："""

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
    
    def smart_update(self):
        """智能更改功能"""
        try:
            # 获取当前章节内容
            current_content = self.chapter_display.get("1.0", tk.END).strip()
            if not current_content:
                messagebox.showwarning("警告", "没有章节内容可供更改")
                return
            
            # 弹出对话框让用户输入更改想法
            from tkinter.simpledialog import askstring
            change_request = askstring("智能更改", "请输入您希望智能更改的要求（如：扩写、缩写、语气更改等）：")
            
            if not change_request:
                return
            
            # 启动进度条
            self.progress.start()
            
            # 在新线程中执行智能更改
            update_thread = threading.Thread(
                target=self.perform_smart_update, 
                args=(current_content, change_request)
            )
            update_thread.daemon = True
            update_thread.start()
            
        except Exception as e:
            self.log_message(f"启动智能更改时出错: {str(e)}")
    
    def perform_smart_update(self, current_content, change_request):
        """执行智能更改"""
        try:
            self.root.after(0, lambda: self.log_message("正在进行智能更改..."))
            
            # 调用AI进行智能更改
            result = self.modify_chapter_smartly(current_content, change_request)
            
            # 在主线程中更新结果
            self.root.after(0, self.update_chapter_display, result)
            
            # 停止进度条
            self.root.after(0, lambda: self.progress.stop())
            
            self.root.after(0, lambda: self.log_message("智能更改完成"))
            
        except Exception as e:
            error_msg = "智能更改过程中出现错误: " + str(e)
            self.root.after(0, lambda: self.update_chapter_display(error_msg))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.log_message(f"智能更改时出错: {str(e)}"))
    
    def modify_chapter_smartly(self, current_content, change_request):
        """
        使用AI对章节进行智能修改（如扩写、缩写、语气更改等）
        """
        prompt = f"""请根据以下要求对章节内容进行智能修改：
        
原始章节内容：
{current_content}

修改要求：
{change_request}

请注意：
1. 保持大纲章节的基本结构和情节
2. 根据要求进行相应的修改（如扩写、缩写、调整语气、优化表达等）
3. 保持故事的连贯性和逻辑性
4. 确保修改后的内容质量

请返回修改后的完整章节内容："""

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
    
    def load_generated_chapters(self):
        """加载已生成的章节列表"""
        try:
            # 清空列表框
            self.chapter_listbox.delete(0, tk.END)
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询已生成的章节
            cursor.execute('''
                SELECT title, created_at, updated_at 
                FROM generated_chapters 
                ORDER BY created_at DESC
            ''')
            chapters = cursor.fetchall()
            
            # 添加到列表框
            for chapter in chapters:
                title, created_at, updated_at = chapter
                display_text = f"{title} ({created_at})"
                self.chapter_listbox.insert(tk.END, display_text)
            
            conn.close()
            
            self.log_message(f"加载了 {len(chapters)} 个已生成的章节")
            
        except Exception as e:
            self.log_message(f"加载已生成章节时出错: {str(e)}")

    def display_chapter_content(self, chapter_index):
        """显示指定章节的内容"""
        try:
            # 获取章节标题（从列表中）
            chapter_title_with_time = self.chapter_listbox.get(chapter_index)
            # 提取标题（去掉时间部分）
            chapter_title = chapter_title_with_time.split(' (')[0]
            
            # 从数据库获取章节内容
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT content FROM generated_chapters WHERE title = ?', (chapter_title,))
            result = cursor.fetchone()
            
            if result:
                content = result[0]
                # 更新章节显示区域
                self.chapter_display.delete("1.0", tk.END)
                self.chapter_display.insert("1.0", content)
                
                self.log_message(f"显示章节: {chapter_title}")
            else:
                self.log_message(f"找不到章节: {chapter_title}")
            
            conn.close()
            
        except Exception as e:
            self.log_message(f"显示章节内容时出错: {str(e)}")

    def log_message(self, message):
        """向日志区域添加消息"""
        self.log_display.config(state='normal')
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = "[" + timestamp + "] " + message + "\n"
        self.log_display.insert(tk.END, formatted_message)
        self.log_display.see(tk.END)
        self.log_display.config(state='disabled')

    def show(self):
        """显示窗口"""
        self.root.deiconify()


class PartialUpdateDialog(tk.Toplevel):
    """
    局部更改对话框
    允许用户选择特定段落并输入修改要求
    """
    
    def __init__(self, parent, content):
        super().__init__(parent)
        
        self.result = None  # (selected_text, change_request)
        self.content = content
        
        self.setup_ui()
    
    def setup_ui(self):
        self.title("局部更改")
        self.geometry("600x500")
        
        # 居中显示
        self.transient(self.master)
        self.grab_set()
        
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 说明标签
        instruction_label = ttk.Label(main_frame, text="请选择要修改的段落，然后输入修改要求：")
        instruction_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 创建文本编辑区域，用于选择段落
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 文本编辑框和滚动条
        scrollbar_y = tk.Scrollbar(text_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.text_widget = tk.Text(
            text_frame,
            wrap=tk.NONE,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            height=12
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_y.config(command=self.text_widget.yview)
        scrollbar_x.config(command=self.text_widget.xview)
        
        # 插入内容并设置为只读
        self.text_widget.insert(tk.END, self.content)
        self.text_widget.config(state=tk.DISABLED)
        
        # 修改要求输入区域
        request_frame = ttk.Frame(main_frame)
        request_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(request_frame, text="修改要求：").pack(anchor=tk.W)
        
        self.request_entry = tk.Text(request_frame, height=4, wrap=tk.WORD)
        self.request_entry.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ok_btn = ttk.Button(button_frame, text="确定", command=self.ok_clicked)
        ok_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_btn = ttk.Button(button_frame, text="取消", command=self.cancel_clicked)
        cancel_btn.pack(side=tk.LEFT)
        
        # 绑定回车键
        self.request_entry.bind('<Return>', lambda e: self.ok_clicked())
        
        # 窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
    
    def ok_clicked(self):
        """确定按钮点击事件"""
        # 获取选中的文本
        try:
            selected_text = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            # 没有选中文本
            selected_text = ""  # 空字符串表示使用全部内容
        
        # 获取修改要求
        change_request = self.request_entry.get("1.0", tk.END).strip()
        
        if not change_request:
            messagebox.showwarning("警告", "请输入修改要求")
            return
        
        self.result = (selected_text, change_request)
        self.destroy()
    
    def cancel_clicked(self):
        """取消按钮点击事件"""
        self.result = None
        self.destroy()


    def smart_update(self):
        """智能更改功能"""
        try:
            # 获取当前章节内容
            current_content = self.chapter_display.get("1.0", tk.END).strip()
            if not current_content:
                messagebox.showwarning("警告", "没有章节内容可供更改")
                return
            
            # 弹出对话框让用户输入更改想法
            from tkinter.simpledialog import askstring
            change_request = askstring("智能更改", "请输入您希望智能更改的要求（如：扩写、缩写、语气更改等）：")
            
            if not change_request:
                return
            
            # 启动进度条
            self.progress.start()
            
            # 在新线程中执行智能更改
            update_thread = threading.Thread(
                target=self.perform_smart_update, 
                args=(current_content, change_request)
            )
            update_thread.daemon = True
            update_thread.start()
            
        except Exception as e:
            self.log_message(f"启动智能更改时出错: {str(e)}")
    
    def perform_smart_update(self, current_content, change_request):
        """执行智能更改"""
        try:
            self.root.after(0, lambda: self.log_message("正在进行智能更改..."))
            
            # 调用AI进行智能更改
            result = self.modify_chapter_smartly(current_content, change_request)
            
            # 在主线程中更新结果
            self.root.after(0, self.update_chapter_display, result)
            
            # 停止进度条
            self.root.after(0, lambda: self.progress.stop())
            
            self.root.after(0, lambda: self.log_message("智能更改完成"))
            
        except Exception as e:
            error_msg = "智能更改过程中出现错误: " + str(e)
            self.root.after(0, lambda: self.update_chapter_display(error_msg))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.log_message(f"智能更改时出错: {str(e)}"))
    
    def modify_chapter_smartly(self, current_content, change_request):
        """
        使用AI对章节进行智能修改（如扩写、缩写、语气更改等）
        """
        prompt = f"""请根据以下要求对章节内容进行智能修改：
        
原始章节内容：
{current_content}

修改要求：
{change_request}

请注意：
1. 保持大纲章节的基本结构和情节
2. 根据要求进行相应的修改（如扩写、缩写、调整语气、优化表达等）
3. 保持故事的连贯性和逻辑性
4. 确保修改后的内容质量

请返回修改后的完整章节内容："""

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
    
    def load_generated_chapters(self):
        """加载已生成的章节列表"""
        try:
            # 清空列表框
            self.chapter_listbox.delete(0, tk.END)
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询已生成的章节
            cursor.execute('''
                SELECT title, created_at, updated_at 
                FROM generated_chapters 
                ORDER BY created_at DESC
            ''')
            chapters = cursor.fetchall()
            
            # 添加到列表框
            for chapter in chapters:
                title, created_at, updated_at = chapter
                display_text = f"{title} ({created_at})"
                self.chapter_listbox.insert(tk.END, display_text)
            
            conn.close()
            
            self.log_message(f"加载了 {len(chapters)} 个已生成的章节")
            
        except Exception as e:
            self.log_message(f"加载已生成章节时出错: {str(e)}")

    def display_chapter_content(self, chapter_index):
        """显示指定章节的内容"""
        try:
            # 获取章节标题（从列表中）
            chapter_title_with_time = self.chapter_listbox.get(chapter_index)
            # 提取标题（去掉时间部分）
            chapter_title = chapter_title_with_time.split(' (')[0]
            
            # 从数据库获取章节内容
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT content FROM generated_chapters WHERE title = ?', (chapter_title,))
            result = cursor.fetchone()
            
            if result:
                content = result[0]
                # 更新章节显示区域
                self.chapter_display.delete("1.0", tk.END)
                self.chapter_display.insert("1.0", content)
                
                self.log_message(f"显示章节: {chapter_title}")
            else:
                self.log_message(f"找不到章节: {chapter_title}")
            
            conn.close()
            
        except Exception as e:
            self.log_message(f"显示章节内容时出错: {str(e)}")

    def log_message(self, message):
        """向日志区域添加消息"""
        self.log_display.config(state='normal')
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = "[" + timestamp + "] " + message + "\n"
        self.log_display.insert(tk.END, formatted_message)
        self.log_display.see(tk.END)
        self.log_display.config(state='disabled')

    def show(self):
        """显示窗口"""
        self.root.deiconify()


def main():
    """测试函数"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 测试大纲解析功能
    test_outline = '''小说标题（暂定）：《春日长椅没有她》

核心设定：

背景：现代青春校园（高中至大学初期）

男主：沈砚 —— 外冷内热，理性克制，家族为"沈氏"，掌管城市能源命脉

女主：林知夏 —— 表面阳光治愈，实则背负家族秘密，家族"林氏"曾因沈家而家破人亡

关键意象：樱花、长椅、药瓶、旧校徽、未寄出的信

【第一部分：甜如初春】（第1–10章）

第1章 樱落时遇见你

开学日，林知夏在樱花树下捡到沈砚掉落的校徽。两人因一场误会相识，却意外发现彼此是同班同学。

第2章 他替我挡了雨

林知夏没带伞，沈砚默默将伞倾向她，自己半边肩膀湿透。她第一次注意到他耳尖微红。

【第二部分：无声裂痕】（第11–20章）

第11章 家族晚宴的对视

林父带知夏出席商业晚宴，首次见到沈父。沈砚想上前，被林父眼神制止。知夏脸色惨白。

第12章 父亲的警告

林父告知知夏：沈家是灭门仇人，当年林氏破产、母亲自杀皆因沈家设局。她必须远离沈砚。'''
    
    app = ChapterGenerationWindow(r"C:\test\project")  # 测试路径
    # 直接测试大纲解析功能
    app.parse_and_build_outline_tree(test_outline)
    root.mainloop()


if __name__ == "__main__":
    main()