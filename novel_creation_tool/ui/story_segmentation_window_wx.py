import wx
import wx.lib.agw.customtreectrl as CT
import sqlite3
import os
import threading
import time


class StorySegmentationWindow:
    """
    故事分段窗口类 (wxPython版本)
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
        
        # 创建主窗口
        self.app = wx.App()
        self.frame = wx.Frame(None, title="故事分段", size=(1200, 800))
        
        self.setup_ui()
        self.load_generated_chapters()
    
    def setup_ui(self):
        """设置界面"""
        # 主面板
        panel = wx.Panel(self.frame)
        
        # 主布局 - 水平布局
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左侧面板 - 章节选择
        left_panel = wx.Panel(panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 左侧标题
        left_title = wx.StaticText(left_panel, label="已生成章节")
        font = left_title.GetFont()
        font.PointSize += 1
        font = font.Bold()
        left_title.SetFont(font)
        left_sizer.Add(left_title, 0, wx.ALL, 5)
        
        # 章节列表控件
        self.chapter_list_ctrl = wx.ListCtrl(left_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.chapter_list_ctrl.InsertColumn(0, "章节标题", width=200)
        self.chapter_list_ctrl.InsertColumn(1, "创建时间", width=150)
        
        # 添加分段按钮
        segment_button = wx.Button(left_panel, label="开始分段")
        segment_button.Bind(wx.EVT_BUTTON, self.on_segment_button_click)
        left_sizer.Add(segment_button, 0, wx.ALL | wx.CENTER, 5)
        
        # 添加保存按钮
        save_button = wx.Button(left_panel, label="保存分段")
        save_button.Bind(wx.EVT_BUTTON, self.on_save_button_click)
        left_sizer.Add(save_button, 0, wx.ALL | wx.CENTER, 5)
        
        # 绑定选择事件
        self.chapter_list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_chapter_select)
        
        left_sizer.Add(self.chapter_list_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        left_panel.SetSizer(left_sizer)
        
        # 右侧面板 - 分段结果
        right_panel = wx.Panel(panel)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 右侧标题
        right_title = wx.StaticText(right_panel, label="分段结果")
        font = right_title.GetFont()
        font.PointSize += 1
        font = font.Bold()
        right_title.SetFont(font)
        right_sizer.Add(right_title, 0, wx.ALL, 5)
        
        # 分段结果显示文本控件
        self.result_text_ctrl = wx.TextCtrl(right_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        right_sizer.Add(self.result_text_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        right_panel.SetSizer(right_sizer)
        
        # 将左右面板加入主布局
        main_sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(right_panel, 2, wx.EXPAND | wx.ALL, 5)
        
        # 底部面板 - 进度和日志
        bottom_panel = wx.Panel(panel)
        bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 进度条
        progress_title = wx.StaticText(bottom_panel, label="进度:")
        bottom_sizer.Add(progress_title, 0, wx.ALL, 5)
        
        self.progress_bar = wx.Gauge(bottom_panel, range=100)
        bottom_sizer.Add(self.progress_bar, 0, wx.EXPAND | wx.ALL, 5)
        
        # 日志标题
        log_title = wx.StaticText(bottom_panel, label="处理日志:")
        bottom_sizer.Add(log_title, 0, wx.ALL, 5)
        
        # 日志显示
        self.log_text_ctrl = wx.TextCtrl(bottom_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        bottom_sizer.Add(self.log_text_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        
        bottom_panel.SetSizer(bottom_sizer)
        
        # 垂直布局 - 上部为主内容，下部为底部面板
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        vertical_sizer.Add(main_sizer, 1, wx.EXPAND)
        vertical_sizer.Add(bottom_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(vertical_sizer)
    
    def load_generated_chapters(self):
        """加载已生成的章节列表"""
        try:
            # 清空列表
            self.chapter_list_ctrl.DeleteAllItems()
            
            # 检查数据库是否存在
            if not os.path.exists(self.db_path):
                self.log_message(f"数据库文件不存在: {self.db_path}")
                # 添加提示信息
                self.chapter_list_ctrl.InsertItem(0, "暂无章节数据，请先生成章节")
                self.chapter_list_ctrl.SetItem(0, 1, "-")
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
                self.chapter_list_ctrl.InsertItem(0, "暂无章节数据，请先生成章节")
                self.chapter_list_ctrl.SetItem(0, 1, "-")
            else:
                # 添加到列表控件
                for i, chapter in enumerate(chapters):
                    title, created_at, updated_at = chapter
                    index = self.chapter_list_ctrl.InsertItem(i, title)
                    self.chapter_list_ctrl.SetItem(index, 1, created_at)
                
                self.log_message(f"加载了 {len(chapters)} 个已生成的章节")
            
            conn.close()
            
        except Exception as e:
            self.log_message(f"加载已生成章节时出错: {str(e)}")
    
    def on_chapter_select(self, event):
        """当选中已生成章节列表中的项目时触发"""
        selected_idx = event.GetIndex()
        if selected_idx != -1:
            chapter_title = self.chapter_list_ctrl.GetItemText(selected_idx, 0)
            self.log_message(f"选择了章节: {chapter_title}")
            
            # 仅记录选择，不自动执行分段
            self.selected_chapter_index = selected_idx
    
    def on_segment_button_click(self, event):
        """分段按钮点击事件"""
        if hasattr(self, 'selected_chapter_index') and self.selected_chapter_index != -1:
            self.perform_segmentation(self.selected_chapter_index)
        else:
            wx.MessageBox("请先选择一个章节", "警告", wx.OK | wx.ICON_WARNING)
    
    def on_save_button_click(self, event):
        """保存按钮点击事件"""
        if hasattr(self, 'current_segments') and self.current_segments:
            self.save_segmentation()
        else:
            wx.MessageBox("没有可保存的分段结果，请先执行分段", "警告", wx.OK | wx.ICON_WARNING)
    
    def perform_segmentation(self, selected_idx):
        """执行故事分段"""
        if selected_idx == -1:
            wx.MessageBox("请先选择一个章节", "警告", wx.OK | wx.ICON_WARNING)
            return
        
        # 获取选中的章节标题
        chapter_title = self.chapter_list_ctrl.GetItemText(selected_idx, 0)
        
        # 在新线程中执行分段，避免阻塞UI
        segmentation_thread = threading.Thread(target=self.segment_chapter, args=(chapter_title,))
        segmentation_thread.daemon = True
        segmentation_thread.start()
    
    def segment_chapter(self, chapter_title):
        """分段指定章节的内容"""
        try:
            # 更新进度条
            wx.CallAfter(lambda: self.progress_bar.SetValue(10))
            
            # 从数据库获取章节内容
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT content FROM generated_chapters WHERE title = ?', (chapter_title,))
            result = cursor.fetchone()
            
            if result:
                content = result[0]
                
                # 更新进度条
                wx.CallAfter(lambda: self.progress_bar.SetValue(30))
                
                self.log_message(f"开始对章节 '{chapter_title}' 进行分段...")
                
                # 按照故事发展进行分段
                segments = self.split_story_by_development(content)
                
                # 更新进度条
                wx.CallAfter(lambda: self.progress_bar.SetValue(80))
                
                # 在主线程中更新显示结果
                wx.CallAfter(lambda: self.display_segments(segments, chapter_title))
                
                self.log_message(f"章节 '{chapter_title}' 分段完成，共生成 {len(segments)} 个段落")
            else:
                self.log_message(f"找不到章节: {chapter_title}")
            
            conn.close()
            
            # 完成后重置进度条
            wx.CallAfter(lambda: self.progress_bar.SetValue(100))
            time.sleep(0.5)
            wx.CallAfter(lambda: self.progress_bar.SetValue(0))
            
        except Exception as e:
            wx.CallAfter(lambda: self.log_message(f"分段过程中出现错误: {str(e)}"))
            wx.CallAfter(lambda: self.progress_bar.SetValue(0))
    
    def split_story_by_development(self, content):
        """使用AI按照故事发展对内容进行分段"""
        import json
        import requests
        import time
        from utils.config_manager import config_manager
        
        # 获取API密钥
        api_key = config_manager.get_api_key()
        
        wx.CallAfter(lambda: self.log_message(f"API密钥配置状态: {'已配置' if api_key else '未配置'}"))
        
        if not api_key:
            wx.CallAfter(lambda: self.log_message("未配置API密钥，使用本地分段方法"))
            return self.local_split_story_by_development(content)
        
        try:
            # 记录开始时间
            start_time = time.time()
            wx.CallAfter(lambda: self.log_message("开始使用AI进行故事分段..."))
            
            # 构建提示词，要求AI按照故事发展进行分段，但不得修改原文内容
            prompt_template = """请将以下故事内容按照故事发展进程分成若干段落，每段应该表达一个完整的情节单元，但请保持原文内容完全不变。遵循以下要求：
            
            1. 每个段落应该代表故事发展的一个阶段
            2. 段落之间应该有明确的情节转折或时间/地点转换
            3. 段落划分后所有内容加起来必须和原文完全一致，不得增删任何内容，不得修改原文任何一个字符
            4. 每个段落应包含核心目标、核心情绪、场景范围和具体内容
            5. 按照以下JSON格式返回结果：
            
            {{
              "segments": [
                {{
                  "id": "EP01_P01",
                  "core_goal": "本段的核心目标",
                  "core_emotion": "本段的核心情绪",
                  "scene_scope": "本段的场景范围",
                  "content": "本段的具体内容，必须与原文完全一致，不得有任何改动"
                }}
              ]
            }}
            
            请只返回JSON格式数据，不要包含其他内容。
            
            故事内容：
            {content}"""
            
            # 将实际内容插入到提示词中
            prompt = prompt_template.format(content=content)
            
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
            
            wx.CallAfter(lambda: self.log_message(f"准备发送AI请求，内容长度: {len(content)} 字符"))
            wx.CallAfter(lambda: self.log_message("正在发送AI分段请求..."))
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120
            )
            
            wx.CallAfter(lambda: self.log_message(f"API响应状态码: {response.status_code}"))
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                wx.CallAfter(lambda: self.log_message("收到AI响应，正在解析数据..."))
                wx.CallAfter(lambda: self.log_message(f"AI响应长度: {len(ai_response)} 字符"))
                
                # 查找JSON部分
                import json as json_lib
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}')
                wx.CallAfter(lambda: self.log_message(f"JSON起始位置: {start_idx}, 结束位置: {end_idx}"))
                
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx+1]
                    wx.CallAfter(lambda: self.log_message(f"提取JSON字符串长度: {len(json_str)} 字符"))
                    try:
                        parsed = json_lib.loads(json_str)
                        if 'segments' in parsed:
                            segments = parsed['segments']
                            wx.CallAfter(lambda: self.log_message(f"成功解析到 {len(segments)} 个段落"))
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
                            wx.CallAfter(lambda: self.log_message(f"AI故事分段完成，耗时 {elapsed_time:.2f} 秒"))
                            return result
                        else:
                            wx.CallAfter(lambda: self.log_message("解析的JSON中没有segments字段"))
                    except json_lib.JSONDecodeError as e:
                        wx.CallAfter(lambda: self.log_message(f"AI分段JSON解析失败: {str(e)}，使用本地分段方法"))
                        
            else:
                wx.CallAfter(lambda: self.log_message(f"API请求失败，状态码: {response.status_code}"))
                wx.CallAfter(lambda: self.log_message(f"API响应内容: {response.text[:500]}..."))  # 只显示前500个字符
                
            wx.CallAfter(lambda: self.log_message("AI分段失败，使用本地分段方法"))
            
        except requests.exceptions.Timeout:
            wx.CallAfter(lambda: self.log_message("AI分段请求超时，使用本地分段方法"))
        except requests.exceptions.RequestException as e:
            wx.CallAfter(lambda: self.log_message(f"网络请求异常: {str(e)}，使用本地分段方法"))
        except Exception as e:
            wx.CallAfter(lambda: self.log_message(f"AI分段过程中出现错误: {str(e)}，使用本地分段方法"))
        
        # 如果AI分段失败，使用本地分段方法
        return self.local_split_story_by_development(content)
    
    def local_split_story_by_development(self, content):
        """本地按故事发展分段方法，确保内容完整性"""
        paragraphs = []
        
        # 按双换行符分割基础段落
        raw_paragraphs = content.split('\n\n')
        
        # 过滤空段落并保留原始内容
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
                    'content': combined_content,
                    'core_goal': '',
                    'core_emotion': '',
                    'scene_scope': ''
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
                'content': combined_content,
                'core_goal': '',
                'core_emotion': '',
                'scene_scope': ''
            })
        
        # 验证内容完整性
        total_content = ''.join([seg['content'] for seg in paragraphs])
        original_clean = ''.join(filtered_paragraphs)
        original_with_separators = '\n\n'.join(filtered_paragraphs)
        
        if total_content.replace('\n', '').replace(' ', '') != original_clean.replace('\n', '').replace(' ', ''):
            self.log_message("警告：分段后内容与原文不匹配，使用原始内容进行分割")
            # 如果内容不匹配，返回整个内容作为一个段落
            return [{'id': 'EP01_P01', 'content': content, 'core_goal': '', 'core_emotion': '', 'scene_scope': ''}]
        
        return paragraphs
    
    def display_segments(self, segments, chapter_title):
        """在右侧结果显示区域显示分段结果"""
        # 清空之前的内容
        self.result_text_ctrl.Clear()
        
        # 添加标题
        self.result_text_ctrl.WriteText(f"章节: {chapter_title}\n\n")
        
        # 保存段落数组供后续保存使用
        self.current_segments = segments
        self.current_chapter_title = chapter_title
        
        # 显示每个段落
        for seg in segments:
            segment_text = f"段落 {seg['id'][6:]}: {seg['id']}\n\n"
            segment_text += f"核心目标: {seg.get('core_goal', '')}\n\n"
            segment_text += f"核心情绪: {seg.get('core_emotion', '')}\n\n"
            segment_text += f"场景范围: {seg.get('scene_scope', '')}\n\n"
            segment_text += f"内容: \n{seg['content']}\n\n"
            segment_text += "-" * 50 + "\n\n"
            
            self.result_text_ctrl.WriteText(segment_text)
    
    def save_segmentation(self):
        """保存分段结果到数据库"""
        if not hasattr(self, 'current_segments') or not self.current_segments:
            wx.MessageBox("没有可保存的分段结果，请先执行分段", "警告", wx.OK | wx.ICON_WARNING)
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 为当前章节创建分段结果表
            chapter_safe_name = self.create_safe_table_name(self.current_chapter_title)
            table_name = f"{chapter_safe_name}_segmentation"
            
            # 创建分段结果表
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS `{table_name}` (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    segment_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    core_goal TEXT,
                    core_emotion TEXT,
                    scene_scope TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 清空之前的数据
            cursor.execute(f"DELETE FROM `{table_name}`")
            
            # 插入新的分段数据
            for seg in self.current_segments:
                cursor.execute(f"INSERT INTO `{table_name}` (segment_id, content, core_goal, core_emotion, scene_scope) VALUES (?, ?, ?, ?, ?)", 
                             (seg['id'], seg['content'], '', '', ''))
            
            conn.commit()
            conn.close()
            
            wx.CallAfter(lambda: self.log_message(f"分段结果已保存到表 '{table_name}'"))
            wx.MessageBox(f"章节 '{self.current_chapter_title}' 的分段结果已保存", "成功", wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            wx.CallAfter(lambda: self.log_message(f"保存分段结果时出错: {str(e)}"))
            wx.MessageBox(f"保存分段结果时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
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
    
    def log_message(self, message):
        """向日志区域添加消息"""
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = "[" + timestamp + "] " + message + "\n"
        self.log_text_ctrl.WriteText(formatted_message)
    
    def show(self):
        """显示窗口"""
        self.frame.Show()
        self.app.MainLoop()


if __name__ == "__main__":
    # 测试代码
    test_project_path = r"./test_project"
    app = StorySegmentationWindow(test_project_path)
    app.show()