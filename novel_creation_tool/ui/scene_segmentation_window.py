import wx
import wx.lib.agw.customtreectrl as CT
import sqlite3
import os
import threading
import time
import json
import requests


class SceneSegmentationWindow:
    """
    故事分场景窗口类
    左侧是结构树（章节作为父节点，段落作为子节点）
    右侧是显示区域和保存按钮
    """
    
    def __init__(self, project_path):
        """
        初始化故事分场景窗口
        
        Args:
            project_path (str): 工程文件路径
        """
        self.project_path = project_path
        self.db_path = os.path.join(project_path, 'project.db')
        
        # 创建主窗口
        self.app = wx.App()
        self.frame = wx.Frame(None, title="故事分场景", size=(1200, 800))
        
        self.setup_ui()
        self.load_chapters_and_segments()
    
    def setup_ui(self):
        """设置界面"""
        # 主面板
        panel = wx.Panel(self.frame)
        
        # 主布局 - 水平布局
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左侧面板 - 结构树
        left_panel = wx.Panel(panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 左侧标题
        left_title = wx.StaticText(left_panel, label="章节结构树")
        font = left_title.GetFont()
        font.PointSize += 1
        font = font.Bold()
        left_title.SetFont(font)
        left_sizer.Add(left_title, 0, wx.ALL, 5)
        
        # 创建树形控件
        self.tree_ctrl = CT.CustomTreeCtrl(
            left_panel,
            agwStyle=wx.TR_DEFAULT_STYLE | CT.TR_AUTO_CHECK_CHILD | CT.TR_HIDE_ROOT
        )
        
        # 添加生成按钮
        generate_button = wx.Button(left_panel, label="生成场景")
        generate_button.Bind(wx.EVT_BUTTON, self.on_generate_button_click)
        left_sizer.Add(generate_button, 0, wx.ALL | wx.CENTER, 5)
        
        # 添加保存按钮
        save_button = wx.Button(left_panel, label="保存场景")
        save_button.Bind(wx.EVT_BUTTON, self.on_save_button_click)
        left_sizer.Add(save_button, 0, wx.ALL | wx.CENTER, 5)
        
        # 绑定树选择事件
        self.tree_ctrl.Bind(CT.EVT_TREE_SEL_CHANGED, self.on_tree_item_selected)
        self.tree_ctrl.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click)
        
        left_sizer.Add(self.tree_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        left_panel.SetSizer(left_sizer)
        
        # 右侧面板 - 场景显示
        right_panel = wx.Panel(panel)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 右侧标题
        right_title = wx.StaticText(right_panel, label="场景显示")
        font = right_title.GetFont()
        font.PointSize += 1
        font = font.Bold()
        right_title.SetFont(font)
        right_sizer.Add(right_title, 0, wx.ALL, 5)
        
        # 场景结果显示文本控件
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
    
    def load_chapters_and_segments(self):
        """加载章节和段落数据到树形结构"""
        try:
            # 清空树
            self.tree_ctrl.DeleteAllItems()
            
            # 添加根节点
            root = self.tree_ctrl.AddRoot("项目结构")
            
            # 检查数据库是否存在
            if not os.path.exists(self.db_path):
                self.log_message(f"数据库文件不存在: {self.db_path}")
                # 添加提示信息
                self.tree_ctrl.AppendItem(root, "暂无章节数据，请先生成章节")
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
            
            # 检查是否有章节数据
            if not chapters:
                self.log_message("数据库中没有找到已生成的章节")
                self.tree_ctrl.AppendItem(root, "暂无章节数据，请先生成章节")
            else:
                # 添加章节到树形结构
                for chapter in chapters:
                    chapter_id, chapter_title, chapter_content, created_at = chapter
                    chapter_item = self.tree_ctrl.AppendItem(root, f"{chapter_title} ({created_at})")
                    
                    # 为每个章节添加段落（从分段结果中获取）
                    chapter_safe_name = self.create_safe_table_name(chapter_title)
                    segment_table_name = f"{chapter_safe_name}_segmentation"
                    
                    # 查询段落数据
                    try:
                        cursor.execute(f'''
                            SELECT segment_id, content 
                            FROM `{segment_table_name}` 
                            ORDER BY id
                        ''')
                        segments = cursor.fetchall()
                        
                        if segments:
                            loaded_segment_count = 0
                            for segment in segments:
                                segment_id, segment_content = segment
                                # 截取段落内容作为显示文本
                                display_text = f"{segment_id}: {segment_content[:50]}..."
                                if len(segment_content) > 50:
                                    display_text += "..."
                                self.tree_ctrl.AppendItem(chapter_item, display_text)
                                # 存储段落数据，便于后续处理
                                self.tree_ctrl.SetItemData(self.tree_ctrl.GetLastChild(chapter_item), 
                                                           {'type': 'segment', 
                                                           'chapter_id': chapter_id,
                                                           'chapter_title': chapter_title,
                                                           'segment_id': segment_id,
                                                           'content': segment_content})
                                loaded_segment_count += 1
                            self.log_message(f"章节 '{chapter_title}' 加载了 {loaded_segment_count} 个段落")
                        else:
                            # 如果没有段落数据，添加提示信息
                            no_segments_item = self.tree_ctrl.AppendItem(chapter_item, "暂无段落数据，可先进行故事分段")
                            self.tree_ctrl.SetItemData(no_segments_item, 
                                                       {'type': 'no_segments',
                                                                       'chapter_id': chapter_id,
                                                                       'chapter_title': chapter_title})
                    except sqlite3.Error:
                        # 如果段落表不存在，说明还没有进行分段
                        no_segments_item = self.tree_ctrl.AppendItem(chapter_item, "暂无段落数据，可先进行故事分段")
                        self.tree_ctrl.SetItemData(no_segments_item, 
                                                   {'type': 'no_segments',
                                                                   'chapter_id': chapter_id,
                                                                   'chapter_title': chapter_title})
                
                self.log_message(f"加载了 {len(chapters)} 个章节及其段落")
            
            conn.close()
            
            # 展开所有节点
            self.tree_ctrl.ExpandAll()
            
            # 计算总段落数量
            total_segments = self.count_total_segments(root)
            
            # 从数据库中验证实际段落数量
            actual_segment_count = 0
            conn_check = sqlite3.connect(self.db_path)
            cursor_check = conn_check.cursor()
            
            for chapter in chapters:
                chapter_title = chapter[1]  # 获取章节标题
                chapter_safe_name = self.create_safe_table_name(chapter_title)
                segment_table_name = f"{chapter_safe_name}_segmentation"
                
                try:
                    cursor_check.execute(f"SELECT COUNT(*) FROM `{segment_table_name}`")
                    count_result = cursor_check.fetchone()
                    if count_result:
                        actual_segment_count += count_result[0]
                except sqlite3.Error:
                    # 表可能不存在，跳过
                    continue
            
            conn_check.close()
            
            self.log_message(f"加载了 {len(chapters)} 个章节，数据库中共有 {actual_segment_count} 个段落，树形结构中显示 {total_segments} 个段落")
            
        except Exception as e:
            self.log_message(f"加载章节和段落时出错: {str(e)}")
    
    def count_total_segments(self, parent_item):
        """递归计算总的段落数量"""
        count = 0
        child, cookie = self.tree_ctrl.GetFirstChild(parent_item)
        while child.IsOk():  # 确保child是有效的
            # 检查该项目是否有数据以及类型是否为 'segment'
            item_data = self.tree_ctrl.GetItemData(child)
            if item_data:
                data = item_data
                if isinstance(data, dict) and data.get('type') == 'segment':
                    count += 1
            # 递归检查子节点
            count += self.count_total_segments(child)
            child, cookie = self.tree_ctrl.GetNextChild(parent_item, cookie)
        return count
    
    def on_tree_item_selected(self, event):
        """当树形控件中的项目被选中时触发"""
        # 对于 EVT_TREE_SEL_CHANGED 事件，我们需要使用 GetItem 或其他方法获取选中项
        item = self.tree_ctrl.GetSelection()
        if item and item.IsOk():
            # 获取存储的数据
            item_data = self.tree_ctrl.GetItemData(item)
            if item_data:
                data = item_data
                item_text = self.tree_ctrl.GetItemText(item)
                
                if data['type'] == 'segment':
                    self.log_message(f"选中段落: {data['chapter_title']} - {data['segment_id']}")
                    self.selected_segment_data = data
                    # 在右侧显示段落内容
                    self.display_segment_content(data['content'])
                elif data['type'] == 'no_segments':
                    self.log_message(f"选中章节: {data['chapter_title']}，暂无段落数据")
                    self.selected_segment_data = data
                else:
                    self.log_message(f"选中章节: {item_text}")
                    self.selected_segment_data = data
        
        # 确保事件继续传播
        event.Skip()
    
    def on_right_click(self, event):
        """处理右键点击事件"""
        pos = event.GetPosition()
        item, flags = self.tree_ctrl.HitTest(pos)
        
        if item:
            # 获取存储的数据
            item_data = self.tree_ctrl.GetItemData(item)
            if item_data:
                data = item_data
                if data['type'] == 'no_segments':
                    # 弹出上下文菜单，提供分段选项
                    menu = wx.Menu()
                    segment_item = menu.Append(wx.ID_ANY, "对此章节进行故事分段")
                    self.Bind(wx.EVT_MENU, lambda e: self.perform_segmentation_for_chapter(data), segment_item)
                    
                    self.tree_ctrl.PopupMenu(menu)
                    menu.Destroy()
    
    def on_generate_button_click(self, event):
        """生成场景按钮点击事件"""
        if hasattr(self, 'selected_segment_data'):
            data = self.selected_segment_data
            if data['type'] == 'segment':
                # 对选中的段落进行场景分割
                self.perform_scene_segmentation(data)
            elif data['type'] == 'no_segments':
                # 对章节进行故事分段
                self.perform_segmentation_for_chapter(data)
            else:
                wx.MessageBox("请选择一个段落来生成场景", "提示", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("请选择一个段落来生成场景", "提示", wx.OK | wx.ICON_INFORMATION)
    
    def on_save_button_click(self, event):
        """保存按钮点击事件"""
        if hasattr(self, 'current_scenes') and self.current_scenes:
            self.save_scenes()
        else:
            wx.MessageBox("没有可保存的场景结果，请先生成场景", "警告", wx.OK | wx.ICON_WARNING)
    
    def perform_segmentation_for_chapter(self, chapter_data):
        """对章节进行故事分段"""
        # 这里调用之前实现的分段逻辑
        chapter_title = chapter_data['chapter_title']
        
        try:
            # 从数据库获取章节内容
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT content FROM generated_chapters WHERE title = ?', (chapter_title,))
            result = cursor.fetchone()
            
            if result:
                content = result[0]
                
                self.log_message(f"开始对章节 '{chapter_title}' 进行分段...")
                
                # 在新线程中执行分段，避免阻塞UI
                segmentation_thread = threading.Thread(
                    target=self.segment_chapter_for_scenes, 
                    args=(chapter_title, content)
                )
                segmentation_thread.daemon = True
                segmentation_thread.start()
            else:
                self.log_message(f"找不到章节: {chapter_title}")
            
            conn.close()
        except Exception as e:
            self.log_message(f"获取章节内容时出错: {str(e)}")
    
    def segment_chapter_for_scenes(self, chapter_title, content):
        """对章节内容进行分段"""
        try:
            # 更新进度条
            wx.CallAfter(lambda: self.progress_bar.SetValue(10))
            
            self.log_message(f"开始对章节 '{chapter_title}' 进行分段...")
            
            # 使用AI按照故事发展进行分段
            segments = self.split_story_by_development(content)
            
            # 更新进度条
            wx.CallAfter(lambda: self.progress_bar.SetValue(80))
            
            # 在主线程中更新显示结果
            wx.CallAfter(lambda: self.update_tree_after_segmentation, chapter_title, segments)
            
            self.log_message(f"章节 '{chapter_title}' 分段完成，共生成 {len(segments)} 个段落")
            
        except Exception as e:
            wx.CallAfter(lambda: self.log_message(f"分段过程中出现错误: {str(e)}"))
            wx.CallAfter(lambda: self.progress_bar.SetValue(0))
    
    def update_tree_after_segmentation(self, chapter_title, segments):
        """分段完成后更新树形结构"""
        # 重新加载章节和段落数据
        self.load_chapters_and_segments()
        wx.MessageBox(f"章节 '{chapter_title}' 分段完成，共生成 {len(segments)} 个段落", 
                     "分段完成", wx.OK | wx.ICON_INFORMATION)
    
    def perform_scene_segmentation(self, segment_data):
        """对选中的段落进行场景分割"""
        segment_content = segment_data['content']
        chapter_title = segment_data['chapter_title']
        segment_id = segment_data['segment_id']
        
        # 在新线程中执行场景分割，避免阻塞UI
        scene_thread = threading.Thread(
            target=self.segment_scene_content, 
            args=(segment_content, chapter_title, segment_id)
        )
        scene_thread.daemon = True
        scene_thread.start()
    
    def segment_scene_content(self, segment_content, chapter_title, segment_id):
        """执行场景分割"""
        try:
            # 更新进度条
            wx.CallAfter(lambda: self.progress_bar.SetValue(10))
            
            self.log_message(f"开始对段落 '{segment_id}' 进行场景分割...")
            
            # 使用AI进行场景分割
            scenes = self.split_scene_by_requirements(segment_content)
            
            # 更新进度条
            wx.CallAfter(lambda: self.progress_bar.SetValue(80))
            
            # 在主线程中更新显示结果
            wx.CallAfter(lambda: self.display_scenes(scenes, chapter_title, segment_id))
            
            self.log_message(f"段落 '{segment_id}' 场景分割完成，共生成 {len(scenes)} 个场景")
            
        except Exception as e:
            wx.CallAfter(lambda: self.log_message(f"场景分割过程中出现错误: {str(e)}"))
            wx.CallAfter(lambda: self.progress_bar.SetValue(0))
    
    def split_scene_by_requirements(self, content):
        """使用AI按照场景要求对内容进行分割"""
        import json
        import requests
        import time
        from utils.config_manager import config_manager
        
        # 获取API密钥
        api_key = config_manager.get_api_key()
        
        wx.CallAfter(lambda: self.log_message(f"API密钥配置状态: {'已配置' if api_key else '未配置'}"))
        
        if not api_key:
            wx.CallAfter(lambda: self.log_message("未配置API密钥，使用本地分段方法"))
            return self.local_split_scene_by_requirements(content)
        
        try:
            # 记录开始时间
            start_time = time.time()
            wx.CallAfter(lambda: self.log_message("开始使用AI进行场景分割..."))
            
            # 构建提示词，要求AI按照场景要求进行分割
            prompt_template = """请将以下故事内容按照场景进行分割，每个场景应包含时间、地点、出场要素和内容。遵循以下要求：

场景 1: 【格式为：原段落编号_S01，例如：EP01_P01_S01，EP01_P02_S01等】

时间: 【填写具体时代、年份或时间段】

地点: 【填写具体地理位置与环境特征】

出场要素: 【列出场景中出现的核心物品、符号、人物或族群等】

内容: 【在此处粘贴或撰写该场景的完整叙述原文】

请严格按照以上格式对下面的内容进行场景分割，确保每个场景都有完整的要素描述，并保持与原始内容的一致性：

内容：
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
            wx.CallAfter(lambda: self.log_message("正在发送AI场景分割请求..."))
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
                
                # 解析AI返回的场景信息
                scenes = self.parse_scenes_from_ai_response(ai_response)
                
                elapsed_time = time.time() - start_time
                wx.CallAfter(lambda: self.log_message(f"AI场景分割完成，耗时 {elapsed_time:.2f} 秒"))
                return scenes
                
            else:
                wx.CallAfter(lambda: self.log_message(f"API请求失败，状态码: {response.status_code}"))
                wx.CallAfter(lambda: self.log_message(f"API响应内容: {response.text[:500]}..."))  # 只显示前500个字符
                
        except requests.exceptions.Timeout:
            wx.CallAfter(lambda: self.log_message("AI场景分割请求超时，使用本地分段方法"))
        except requests.exceptions.RequestException as e:
            wx.CallAfter(lambda: self.log_message(f"网络请求异常: {str(e)}，使用本地分段方法"))
        except Exception as e:
            wx.CallAfter(lambda: self.log_message(f"AI场景分割过程中出现错误: {str(e)}，使用本地分段方法"))
        
        # 如果AI分割失败，使用本地分段方法
        return self.local_split_scene_by_requirements(content)
    
    def parse_scenes_from_ai_response(self, ai_response):
        """从AI响应中解析场景信息"""
        scenes = []
        
        import re
        
        # 使用更灵活的正则表达式来查找场景块
        # 支持各种格式：场景1:, 场景 1:, 场景1：, 场景 1：, 场景一:, 等
        scene_blocks = re.split(r'\n(?=场景[\s\u3001\uff1a:]*[\d\u4e00-\u9fa5]+[\s\u3001\uff1a:])', ai_response)
        
        # 过滤掉空的块
        scene_blocks = [block.strip() for block in scene_blocks if block.strip()]
        
        for block in scene_blocks:
            # 尝试提取场景编号
            scene_num_match = re.search(r'场景[\s\u3001\uff1a:]*([\d\u4e00-\u9fa5]+)[\s\u3001\uff1a:]?', block)
            if scene_num_match:
                scene_number = scene_num_match.group(1)
                
                # 提取时间、地点、出场要素、内容等信息
                time_match = re.search(r'(?:时间|時|時間)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|地点|地點|出场|場出|內容|内容)', block, re.DOTALL)
                location_match = re.search(r'(?:地点|地點)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|时间|時|時間|出场|場出|內容|内容)', block, re.DOTALL)
                elements_match = re.search(r'(?:出场要素|場出要素|出场|場出)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|时间|時|時間|地点|地點|內容|内容)', block, re.DOTALL)
                content_match = re.search(r'(?:内容|內容)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|时间|時|時間|地点|地點|出场|場出)', block, re.DOTALL)
                
                scene = {
                    '编号': f'场景 {scene_number}',
                    '时间': time_match.group(1).strip().strip(':： ') if time_match else '',
                    '地点': location_match.group(1).strip().strip(':： ') if location_match else '',
                    '出场要素': elements_match.group(1).strip().strip(':： ') if elements_match else '',
                    '内容': content_match.group(1).strip().strip(':： ') if content_match else block
                }
                scenes.append(scene)
        
        # 如果上述方法没有找到任何场景，尝试更宽松的解析
        if not scenes:
            # 检查是否包含场景相关的关键词
            if re.search(r'场景[\s\u3001\uff1a:]*[\d\u4e00-\u9fa5]+', ai_response):
                # 按场景关键词分割，包括中文数字
                scene_parts = re.split(r'场景[\s\u3001\uff1a:]*([\d\u4e00-\u9fa5]+)[\s\u3001\uff1a:]*', ai_response)
                # 重新组合：编号和内容成对
                i = 1
                while i < len(scene_parts):
                    scene_number = scene_parts[i].strip()
                    if i + 1 < len(scene_parts):
                        scene_content = scene_parts[i + 1]
                        
                        # 在场景内容中提取各部分
                        time_match = re.search(r'(?:时间|時|時間)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|地点|地點|出场|場出|內容|内容)', scene_content, re.DOTALL)
                        location_match = re.search(r'(?:地点|地點)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|时间|時|時間|出场|場出|內容|内容)', scene_content, re.DOTALL)
                        elements_match = re.search(r'(?:出场要素|場出要素|出场|場出)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|时间|時|時間|地点|地點|內容|内容)', scene_content, re.DOTALL)
                        content_match = re.search(r'(?:内容|內容)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|时间|時|時間|地点|地點|出场|場出)', scene_content, re.DOTALL)
                        
                        scene = {
                            '编号': f'场景 {scene_number}',
                            '时间': time_match.group(1).strip().strip(':： ') if time_match else '',
                            '地点': location_match.group(1).strip().strip(':： ') if location_match else '',
                            '出场要素': elements_match.group(1).strip().strip(':： ') if elements_match else '',
                            '内容': content_match.group(1).strip().strip(':： ') if content_match else scene_content.strip()
                        }
                        scenes.append(scene)
                    i += 2
        
        # 如果还是没有找到任何场景，但AI确实返回了内容，则尝试查找关键信息
        if not scenes:
            # 尝试从整个响应中提取基本信息
            time_match = re.search(r'(?:时间|時|時間)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|地点|地點|出场|場出|內容|内容)', ai_response, re.DOTALL)
            location_match = re.search(r'(?:地点|地點)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|时间|時|時間|出场|場出|內容|内容)', ai_response, re.DOTALL)
            elements_match = re.search(r'(?:出场要素|場出要素|出场|場出)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|时间|時|時間|地点|地點|內容|内容)', ai_response, re.DOTALL)
            content_match = re.search(r'(?:内容|內容)[\s\u3001\uff1a:\s：:：]*(.*?)(?=\n|$|时间|時|時間|地点|地點|出场|場出)', ai_response, re.DOTALL)
            
            if time_match or location_match or elements_match or content_match:
                # 至少找到了一个字段，创建一个场景
                scene = {
                    '编号': '场景 1',
                    '时间': time_match.group(1).strip().strip(':： ') if time_match else '',
                    '地点': location_match.group(1).strip().strip(':： ') if location_match else '',
                    '出场要素': elements_match.group(1).strip().strip(':： ') if elements_match else '',
                    '内容': content_match.group(1).strip().strip(':： ') if content_match else ai_response.strip()
                }
                scenes.append(scene)
        
        # 如果仍然没有找到任何场景，至少创建一个基本场景
        if not scenes:
            scenes.append({
                '编号': '场景 1',
                '时间': '',
                '地点': '',
                '出场要素': '',
                '内容': ai_response.strip()
            })
        
        return scenes
    
    def local_split_scene_by_requirements(self, content):
        """本地按场景要求分段方法"""
        scenes = []
        
        # 简单地将内容作为一个场景返回
        scenes.append({
            '编号': '场景 1',
            '时间': '未指定',
            '地点': '未指定',
            '出场要素': '未指定',
            '内容': content
        })
        
        return scenes
    
    def display_scenes(self, scenes, chapter_title, segment_id):
        """在右侧结果显示区域显示场景结果"""
        # 清空之前的内容
        self.result_text_ctrl.Clear()
        
        # 添加标题
        self.result_text_ctrl.WriteText(f"章节: {chapter_title}\n")
        self.result_text_ctrl.WriteText(f"段落: {segment_id}\n\n")
        
        # 保存场景数组供后续保存使用
        self.current_scenes = scenes
        self.current_chapter_title = chapter_title
        self.current_segment_id = segment_id
        
        # 显示每个场景
        for i, scene in enumerate(scenes):
            # 为场景生成编号，格式为原段落编号_S01, S02, ...
            scene_number = f"{segment_id}_S{i+1:02d}"
            scene_text = f"场景 {i+1}: {scene_number}\n"
            scene_text += f"时间: {scene.get('时间', '未指定')}\n"
            scene_text += f"地点: {scene.get('地点', '未指定')}\n"
            scene_text += f"出场要素: {scene.get('出场要素', '未指定')}\n"
            scene_text += f"内容: \n{scene.get('内容', '')}\n"
            scene_text += "-" * 50 + "\n\n"
            
            self.result_text_ctrl.WriteText(scene_text)
    
    def display_segment_content(self, content):
        """在右侧显示段落内容"""
        self.result_text_ctrl.Clear()
        self.result_text_ctrl.WriteText("当前选中段落内容:\n\n")
        self.result_text_ctrl.WriteText(content)
    
    def save_scenes(self):
        """保存场景结果到数据库，使用标准scenes表"""
        if not hasattr(self, 'current_scenes') or not self.current_scenes:
            wx.MessageBox("没有可保存的场景结果，请先生成场景", "警告", wx.OK | wx.ICON_WARNING)
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查scenes表是否存在，如果不存在则创建
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scenes';")
            if not cursor.fetchone():
                # 创建scenes表（使用与database.py中相同的结构）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scenes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        segment_id INTEGER,
                        scene_number INTEGER NOT NULL,
                        title TEXT,
                        setting TEXT,  -- 场景设置
                        characters TEXT,  -- 出现场景的角色
                        duration REAL,  -- 持续时间
                        content TEXT,  -- 场景内容
                        notes TEXT,  -- 备注
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                wx.CallAfter(lambda: self.log_message("创建了缺失的scenes表"))
            
            # 清空该段落之前保存的场景数据
            cursor.execute("DELETE FROM scenes WHERE segment_id = ?", (self.current_segment_id,))
            
            # 插入新的场景数据到标准scenes表
            for i, scene in enumerate(self.current_scenes):
                # 生成场景编号，格式为原段落编号_S01, S02, ...
                scene_number_formatted = f"{self.current_segment_id}_S{i+1:02d}"
                cursor.execute("""
                    INSERT INTO scenes 
                    (segment_id, scene_number, title, setting, characters, content, notes) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_segment_id,  # 段落ID
                    i+1,  # 场景序号（数字）
                    scene_number_formatted,  # 场景标题（使用格式化编号，如EP01_P01_S01）
                    scene.get('地点', ''),  # 场景设置（地点）
                    scene.get('出场要素', ''),  # 出现场景的角色/要素
                    scene.get('内容', ''),  # 场景内容
                    f"时间:{scene.get('时间', '')}"  # 备注（时间信息）
                ))
            
            conn.commit()
            conn.close()
            
            wx.CallAfter(lambda: self.log_message(f"场景结果已保存到标准scenes表，共 {len(self.current_scenes)} 个场景"))
            wx.MessageBox(f"场景结果已保存", "成功", wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            wx.CallAfter(lambda: self.log_message(f"保存场景结果时出错: {str(e)}"))
            wx.MessageBox(f"保存场景结果时出错: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def split_story_by_development(self, content):
        """使用AI按照故事发展对内容进行分段（复用之前的逻辑）"""
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
        """本地按故事发展分段方法，确保内容完整性（复用之前的逻辑）"""
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
        # 检查控件是否仍然存在且有效
        if not self.log_text_ctrl or not self.log_text_ctrl.IsShownOnScreen():
            return
        
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = "[" + timestamp + "] " + message + "\n"
        try:
            # 使用AppendText代替WriteText，更安全
            self.log_text_ctrl.AppendText(formatted_message)
        except:
            # 如果AppendText也失败，使用安全的方法
            current_content = self.log_text_ctrl.GetValue()
            self.log_text_ctrl.SetValue(current_content + formatted_message)
            # 滚动到底部
            self.log_text_ctrl.ShowPosition(self.log_text_ctrl.GetLastPosition())
    
    def show(self):
        """显示窗口"""
        self.frame.Show()
        self.app.MainLoop()


if __name__ == "__main__":
    # 测试代码
    test_project_path = r"./test_project"
    app = SceneSegmentationWindow(test_project_path)
    app.show()