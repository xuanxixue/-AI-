import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
import os
import threading
import time


class StorySegmentationWindow:
    """
    故事分段窗口类
    包含左侧章节选择列表和右侧分段结果显示区域
    """
    
    def __init__(self, project_path):
        """
        初始化故事分段窗口
        
        Args:
            project_path (str): 工程文件路径
        """
        self.project_path = project_path
        self.db_path = os.path.join(project_path, 'project.db')
        
        self.root = tk.Toplevel()
        self.root.title("故事分段")
        self.root.geometry("1200x800")
        
        self.setup_ui()
        self.load_generated_chapters()
    
    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        top_frame = tk.Frame(self.root, bg="#f0f0f0", height=50)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # 页面名字标签
        title_label = tk.Label(top_frame, text="故事分段", font=("Microsoft YaHei", 12, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 分割窗口 - 左右两栏
        paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
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
        
        # 添加分段按钮
        segment_btn = tk.Button(left_frame, text="开始分段", command=self.perform_segmentation, 
                              bg="#17a2b8", fg="white", relief="flat")
        segment_btn.pack(pady=5)
        
        # 绑定章节列表选择事件
        self.chapter_listbox.bind("<<ListboxSelect>>", self.on_chapter_select)
        
        # 添加到分割窗口
        paned_window.add(left_frame, stretch="always")
        
        # 右侧 - 分段结果显示区域
        right_frame = tk.Frame(paned_window)
        right_label = tk.Label(right_frame, text="分段结果", font=("Microsoft YaHei", 10))
        right_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 分段结果显示区域
        text_frame = tk.Frame(right_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 滚动条
        result_scrollbar = tk.Scrollbar(text_frame)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文本显示区域
        self.result_display = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=result_scrollbar.set)
        self.result_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar.config(command=self.result_display.yview)
        
        # 添加到分割窗口
        paned_window.add(right_frame, stretch="always")
        
        # 底部 - 日志和进度
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 进度条
        progress_label = tk.Label(bottom_frame, text="进度:", font=("Microsoft YaHei", 10))
        progress_label.pack(anchor=tk.NW, padx=5, pady=(5, 0))
        
        self.progress = ttk.Progressbar(bottom_frame, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 日志显示区域
        log_title = tk.Label(bottom_frame, text="处理日志:", font=("Microsoft YaHei", 10))
        log_title.pack(anchor=tk.NW, padx=5, pady=(5, 0))
        
        self.log_display = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, height=6, state='disabled')
        self.log_display.pack(fill=tk.X, padx=5, pady=5)
    
    def load_generated_chapters(self):
        """加载已生成的章节列表"""
        try:
            # 清空列表框
            self.chapter_listbox.delete(0, tk.END)
            
            # 检查数据库是否存在
            if not os.path.exists(self.db_path):
                self.log_message(f"数据库文件不存在: {self.db_path}")
                # 显示提示信息
                self.chapter_listbox.insert(tk.END, "暂无章节数据，请先生成章节")
                return
            
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
            
            # 检查是否有章节数据
            if not chapters:
                self.log_message("数据库中没有找到已生成的章节")
                self.chapter_listbox.insert(tk.END, "暂无章节数据，请先生成章节")
            else:
                # 添加到列表框
                for chapter in chapters:
                    title, created_at, updated_at = chapter
                    display_text = f"{title} ({created_at})"
                    self.chapter_listbox.insert(tk.END, display_text)
                
                self.log_message(f"加载了 {len(chapters)} 个已生成的章节")
            
            conn.close()
            
        except Exception as e:
            self.log_message(f"加载已生成章节时出错: {str(e)}")
    
    def on_chapter_select(self, event):
        """当选中已生成章节列表中的项目时触发"""
        selection = self.chapter_listbox.curselection()
        if selection:
            index = selection[0]
            chapter_info = self.chapter_listbox.get(index)
            self.log_message(f"选择了章节: {chapter_info}")
            
            # 仅记录选择，不自动执行分段
    
    def perform_segmentation(self):
        """执行故事分段"""
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个章节")
            return
        
        # 获取选中的章节标题
        index = selection[0]
        chapter_info = self.chapter_listbox.get(index)
        chapter_title = chapter_info.split(' (')[0]  # 提取标题（去掉时间部分）
        
        # 在新线程中执行分段，避免阻塞UI
        segmentation_thread = threading.Thread(target=self.segment_chapter, args=(chapter_title,))
        segmentation_thread.daemon = True
        segmentation_thread.start()
    
    def segment_chapter(self, chapter_title):
        """分段指定章节的内容"""
        try:
            # 更新进度条
            self.root.after(0, lambda: setattr(self.progress, 'value', 10))
            
            # 从数据库获取章节内容
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT content FROM generated_chapters WHERE title = ?', (chapter_title,))
            result = cursor.fetchone()
            
            if result:
                content = result[0]
                
                # 更新进度条
                self.root.after(0, lambda: setattr(self.progress, 'value', 30))
                
                self.log_message(f"开始对章节 '{chapter_title}' 进行分段...")
                
                # 按照故事发展进行分段
                segments = self.split_story_by_development(content)
                
                # 更新进度条
                self.root.after(0, lambda: setattr(self.progress, 'value', 80))
                
                # 在主线程中更新显示结果
                self.root.after(0, lambda: self.display_segments(segments, chapter_title))
                
                self.log_message(f"章节 '{chapter_title}' 分段完成，共生成 {len(segments)} 个段落")
            else:
                self.log_message(f"找不到章节: {chapter_title}")
            
            conn.close()
            
            # 完成后重置进度条
            self.root.after(0, lambda: setattr(self.progress, 'value', 100))
            self.root.after(0, lambda: time.sleep(0.5))
            self.root.after(0, lambda: setattr(self.progress, 'value', 0))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"分段过程中出现错误: {str(e)}"))
            self.root.after(0, lambda: setattr(self.progress, 'value', 0))
    
    def split_story_by_development(self, content):
        """使用AI按照故事发展对内容进行分段"""
        import json
        import requests
        import time
        from utils.config_manager import config_manager
        
        # 获取API密钥
        api_key = config_manager.get_api_key()
        
        if not api_key:
            self.log_message("未配置API密钥，使用本地分段方法")
            return self.local_split_story_by_development(content)
        
        try:
            # 记录开始时间
            start_time = time.time()
            self.log_message("开始使用AI进行故事分段...")
            
            # 构建提示词，要求AI按照故事发展进行分段
            prompt = f"""请将以下故事内容按照故事发展进程分成若干段落，每段应该表达一个完整的情节单元，遵循以下要求：
            
            1. 每个段落应该代表故事发展的一个阶段
            2. 段落之间应该有明确的情节转折或时间/地点转换
            3. 每个段落应包含核心目标、核心情绪、场景范围和具体内容
            4. 按照以下JSON格式返回结果：
            
            {{
              "segments": [
                {{
                  "id": "EP01_P01",
                  "core_goal": "本段的核心目标",
                  "core_emotion": "本段的核心情绪",
                  "scene_scope": "本段的场景范围",
                  "content": "本段的具体内容"
                }}
              ]
            }}
            
            请只返回JSON格式数据，不要包含其他内容。
            
            故事内容：
            {content}"""
            
            headers = {
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            
            self.log_message("正在发送AI分段请求...")
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120
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
                        if 'segments' in parsed:
                            segments = parsed['segments']
                            result = []
                            for i, seg in enumerate(segments):
                                result.append({
                                    'id': seg.get('id', f"EP01_P{i+1:02d}"),
                                    'content': seg.get('content', ''),
                                    'core_goal': seg.get('core_goal', ''),
                                    'core_emotion': seg.get('core_emotion', ''),
                                    'scene_scope': seg.get('scene_scope', '')
                                })
                            elapsed_time = time.time() - start_time
                            self.log_message(f"AI故事分段完成，耗时 {elapsed_time:.2f} 秒")
                            return result
                    except json_lib.JSONDecodeError:
                        self.log_message("AI分段JSON解析失败，使用本地分段方法")
                        
            self.log_message("AI分段失败，使用本地分段方法")
            
        except Exception as e:
            self.log_message(f"AI分段过程中出现错误: {str(e)}，使用本地分段方法")
        
        # 如果AI分段失败，使用本地分段方法
        return self.local_split_story_by_development(content)
    
    def local_split_story_by_development(self, content):
        """本地按故事发展分段方法"""
        paragraphs = []
        
        # 首先按双换行符分割基础段落
        raw_paragraphs = content.split('\n\n')
        
        # 过滤空段落并合并短段落以形成有意义的故事单元
        filtered_paragraphs = []
        for para in raw_paragraphs:
            para = para.strip()
            if para:
                filtered_paragraphs.append(para)
        
        # 按一定的策略分段，优先保持段落完整性，同时考虑故事发展的逻辑
        current_segment = []
        current_length = 0
        max_segment_length = 1000  # 每段最大字符数
        
        # 定义一些关键词，用于检测故事转折点
        transition_keywords = ['但是', '然而', '突然', '于是', '因此', '随后', '接着', '然后', '这时', '此刻', '同时', '最终', '最后']
        
        for para in filtered_paragraphs:
            para_length = len(para)
            
            # 检查段落是否包含转折关键词
            has_transition = any(keyword in para for keyword in transition_keywords)
            
            # 如果当前段落加上新段落超过最大长度，或者包含转折关键词且当前段不为空，则开始新段
            if ((current_length + para_length > max_segment_length and current_segment) or 
                (has_transition and current_segment)):
                # 合并当前累积的段落作为一个分段
                combined_content = '\n\n'.join(current_segment)
                paragraphs.append({
                    'id': f"EP01_P{len(paragraphs)+1:02d}",  # 格式: EP01_P01
                    'content': combined_content
                })
                
                # 开始新的段
                current_segment = [para]
                current_length = para_length
            else:
                current_segment.append(para)
                current_length += para_length
        
        # 添加最后一个段
        if current_segment:
            combined_content = '\n\n'.join(current_segment)
            paragraphs.append({
                'id': f"EP01_P{len(paragraphs)+1:02d}",  # 格式: EP01_P01
                'content': combined_content
            })
        
        return paragraphs
    
    def display_segments(self, segments, chapter_title):
        """在右侧结果显示区域显示分段结果"""
        # 清空之前的内容
        self.result_display.delete("1.0", tk.END)
        
        # 添加标题
        self.result_display.insert(tk.END, f"章节: {chapter_title}\n\n")
        
        # 显示每个段落
        for seg in segments:
            segment_text = f"段落 {seg['id'][6:]}: {seg['id']}\n\n"
            segment_text += f"核心目标: {seg.get('core_goal', '')}\n\n"
            segment_text += f"核心情绪: {seg.get('core_emotion', '')}\n\n"
            segment_text += f"场景范围: {seg.get('scene_scope', '')}\n\n"
            segment_text += f"内容: \n{seg['content']}\n\n"
            segment_text += "-" * 50 + "\n\n"
            
            self.result_display.insert(tk.END, segment_text)
    
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


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 使用测试项目路径
    test_project_path = r"./test_project"
    app = StorySegmentationWindow(test_project_path)
    
    root.mainloop()