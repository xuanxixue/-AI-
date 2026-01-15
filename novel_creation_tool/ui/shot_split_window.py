import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import os
import threading
import time
import json
import requests
from utils.config_manager import config_manager


class ShotSplitWindow:
    """
    故事分镜头窗口类
    包含左侧场景列表、中间分镜头处理区域和右侧镜头列表
    """

    def __init__(self, project_path):
        """
        初始化故事分镜头窗口
        
        Args:
            project_path (str): 工程文件路径
        """
        self.project_path = project_path
        self.db_path = os.path.join(project_path, 'project.db')
        
        self.root = tk.Toplevel()
        self.root.title("故事分镜头")
        self.root.geometry("1400x900")
        
        self.selected_scene_id = None
        self.current_shots = []
        
        self.setup_ui()
        self.load_scenes()

    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        top_frame = tk.Frame(self.root, bg="#f0f0f0", height=50)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # 页面名字标签
        title_label = tk.Label(top_frame, text="故事分镜头", font=("Microsoft YaHei", 12, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 主内容框架 - 三栏布局
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 分割窗口 - 三列
        paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧 - 场景选择区域
        left_frame = tk.Frame(paned_window)
        left_label = tk.Label(left_frame, text="场景列表", font=("Microsoft YaHei", 10))
        left_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 场景列表框
        listbox_frame = tk.Frame(left_frame)
        self.scene_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, width=30)
        scene_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.scene_listbox.yview)
        self.scene_listbox.config(yscrollcommand=scene_scrollbar.set)
        
        self.scene_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scene_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 分镜头按钮
        split_button = tk.Button(left_frame, text="分镜头", command=self.perform_shot_split, 
                                 bg="#28a745", fg="white", relief="flat", height=2)
        split_button.pack(pady=5, padx=5, fill=tk.X)
        
        # 添加到分割窗口
        paned_window.add(left_frame)
        
        # 中间 - 分镜头结果显示区域
        middle_frame = tk.Frame(paned_window)
        middle_label = tk.Label(middle_frame, text="分镜头结果", font=("Microsoft YaHei", 10))
        middle_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 分镜头结果显示区域
        self.shot_display = scrolledtext.ScrolledText(middle_frame, wrap=tk.WORD, width=50, height=20)
        self.shot_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 保存按钮
        save_button = tk.Button(middle_frame, text="保存", command=self.save_shots, 
                                bg="#ffc107", fg="black", relief="flat", height=2)
        save_button.pack(pady=5, padx=5, fill=tk.X)
        
        # 添加到分割窗口
        paned_window.add(middle_frame)
        
        # 右侧 - 镜头列表区域
        right_frame = tk.Frame(paned_window)
        right_label = tk.Label(right_frame, text="镜头列表", font=("Microsoft YaHei", 10))
        right_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 镜头列表框
        shot_listbox_frame = tk.Frame(right_frame)
        self.shot_listbox = tk.Listbox(shot_listbox_frame, selectmode=tk.SINGLE, width=30)
        shot_list_scrollbar = tk.Scrollbar(shot_listbox_frame, orient=tk.VERTICAL, command=self.shot_listbox.yview)
        self.shot_listbox.config(yscrollcommand=shot_list_scrollbar.set)
        
        self.shot_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        shot_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        shot_listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定镜头选择事件
        self.shot_listbox.bind('<<ListboxSelect>>', self.on_shot_select)
        
        # 添加到分割窗口
        paned_window.add(right_frame)
        
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
        
        # 绑定场景选择事件
        self.scene_listbox.bind('<<ListboxSelect>>', self.on_scene_select)

    def load_scenes(self):
        """加载已保存的场景，包含镜头数量统计"""
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查scenes表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scenes';")
            if not cursor.fetchone():
                self.log_message("警告: scenes表不存在，可能需要先使用故事分场景功能创建场景数据")
                # 清空列表框
                self.scene_listbox.delete(0, tk.END)
                conn.close()
                return
            
            # 检查shots表是否存在，如果不存在则创建
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shots';")
            if not cursor.fetchone():
                # 创建shots表（使用与database.py中相同的结构）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS shots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scene_id INTEGER,
                        shot_number INTEGER NOT NULL,
                        description TEXT,
                        duration REAL,  -- 持续时间（秒）
                        camera_angle TEXT,  -- 镜头角度
                        character_actions TEXT,  -- 角色动作
                        dialogue TEXT,  -- 对话
                        props TEXT,  -- 道具
                        notes TEXT,  -- 备注
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.log_message("创建了缺失的shots表")
            
            # 查询场景数据和每个场景的镜头数量
            cursor.execute("""
                SELECT s.id, s.scene_number, s.title, s.segment_id,
                       COALESCE(shot_counts.cnt, 0) as shot_count
                FROM scenes s
                LEFT JOIN (
                    SELECT scene_id, COUNT(*) as cnt 
                    FROM shots 
                    GROUP BY scene_id
                ) shot_counts ON s.id = shot_counts.scene_id
                ORDER BY s.segment_id, s.scene_number
            """)
            scenes = cursor.fetchall()
            
            # 清空列表框
            self.scene_listbox.delete(0, tk.END)
            
            # 添加场景到列表框
            for scene in scenes:
                scene_id, scene_number, title, segment_id, shot_count = scene
                # 确保segment_id不是None或空值
                if segment_id is None:
                    segment_id = "UNKNOWN"
                # 使用title字段中的完整格式化编号，如果title字段包含完整编号则优先使用
                if title and '_' in title and title.count('_S') > 0:
                    # title字段包含了完整编号如 "EP01_P01_S01"
                    display_text = title
                else:
                    # 如果title字段不包含完整编号，则构建显示文本
                    display_text = f"场景 {segment_id}_S{scene_number:02d}"
                
                scene_text = f"{display_text}: {title[:30]}... ({shot_count}个镜头)" if title and len(title) > 30 else f"{display_text}: {title} ({shot_count}个镜头)" if title else f"{display_text} ({shot_count}个镜头)"
                self.scene_listbox.insert(tk.END, scene_text)
            
            conn.close()
            
            self.log_message(f"加载了 {len(scenes)} 个场景")
            
        except Exception as e:
            self.log_message(f"加载场景时出错: {str(e)}")

    def on_scene_select(self, event):
        """当选中场景列表中的项目时触发"""
        selection = self.scene_listbox.curselection()
        if selection:
            index = selection[0]
            scene_info = self.scene_listbox.get(index)
            self.log_message(f"选择了场景: {scene_info}")
            
            # 获取场景ID（通过查询数据库）
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 从场景信息中提取segment_id和scene_number
                # 场景格式可能为 "场景 segment_id_S01: title (N个镜头)" 或 "segment_id_S01: title (N个镜头)" 或其他格式
                
                # 提取冒号前的部分
                scene_part = scene_info.split(': ')[0]
                
                # 检查scene_part是否就是完整格式化编号（如 EP01_P01_S01）
                if '_' in scene_part and scene_part.count('_S') > 0:
                    # 这种情况下，scene_part 可能是完整格式化编号，如 "EP01_P01_S01"
                    last_underscore_pos = scene_part.rfind('_')
                    if last_underscore_pos != -1:
                        segment_id = scene_part[:last_underscore_pos]  # 获取 "EP01_P01"
                        scene_num_part = scene_part[last_underscore_pos+1:]  # 获取 "S01"
                        
                        # 提取数字部分 (S01 -> 1)
                        if scene_num_part.startswith('S'):
                            try:
                                scene_number = int(scene_num_part[1:])  # 获取 S 后面的数字
                            except ValueError:
                                self.log_message(f"无法解析场景编号中的数字部分: {scene_num_part[1:]}")
                                return  # 直接返回
                        else:
                            # 如果不是 S 开头，尝试直接转换为整数
                            try:
                                scene_number = int(scene_num_part)
                            except ValueError:
                                self.log_message(f"无法解析场景编号: {scene_num_part}")
                                return  # 直接返回
                        
                        # 查询数据库获取场景ID
                        cursor.execute("SELECT id FROM scenes WHERE segment_id = ? AND scene_number = ?", (segment_id, scene_number))
                        result = cursor.fetchone()
                        if result:
                            self.selected_scene_id = result[0]
                            self.log_message(f"成功获取场景ID: {self.selected_scene_id} 对应 segment_id: {segment_id}, scene_number: {scene_number}")
                        else:
                            self.log_message(f"在数据库中未找到匹配的场景: {segment_id}, {scene_number}")
                            # 尝试只按 scene_number 查询作为备选方案
                            cursor.execute("SELECT id FROM scenes WHERE scene_number = ?", (scene_number,))
                            result = cursor.fetchone()
                            if result:
                                self.selected_scene_id = result[0]
                                self.log_message(f"使用备选方案获取场景ID: {self.selected_scene_id}")
                else:
                    # 传统格式 "场景 segment_id_S01"
                    if ' ' in scene_part:
                        scene_detail = scene_part.split(' ', 1)[1]  # 获取 "segment_id_S01"
                        
                        # 查找最后一个下划线的位置
                        last_underscore_pos = scene_detail.rfind('_')
                        if last_underscore_pos != -1:
                            segment_id = scene_detail[:last_underscore_pos]  # 获取 "EP01_P01"
                            scene_num_part = scene_detail[last_underscore_pos+1:]  # 获取 "S01"
                            
                            # 提取数字部分 (S01 -> 1)
                            if scene_num_part.startswith('S'):
                                try:
                                    scene_number = int(scene_num_part[1:])  # 获取 S 后面的数字
                                except ValueError:
                                    self.log_message(f"无法解析场景编号中的数字部分: {scene_num_part[1:]}")
                                    return  # 直接返回
                            else:
                                # 如果不是 S 开头，尝试直接转换为整数
                                try:
                                    scene_number = int(scene_num_part)
                                except ValueError:
                                    self.log_message(f"无法解析场景编号: {scene_num_part}")
                                    return  # 直接返回
                            
                            # 查询数据库获取场景ID
                            cursor.execute("SELECT id FROM scenes WHERE segment_id = ? AND scene_number = ?", (segment_id, scene_number))
                            result = cursor.fetchone()
                            if result:
                                self.selected_scene_id = result[0]
                                self.log_message(f"成功获取场景ID: {self.selected_scene_id} 对应 segment_id: {segment_id}, scene_number: {scene_number}")
                            else:
                                self.log_message(f"在数据库中未找到匹配的场景: {segment_id}, {scene_number}")
                                # 尝试只按 scene_number 查询作为备选方案
                                cursor.execute("SELECT id FROM scenes WHERE scene_number = ?", (scene_number,))
                                result = cursor.fetchone()
                                if result:
                                    self.selected_scene_id = result[0]
                                    self.log_message(f"使用备选方案获取场景ID: {self.selected_scene_id}")
                    else:
                        # 如果没有下划线，尝试旧的解析方法
                        try:
                            scene_number = int(scene_detail)
                            cursor.execute("SELECT id FROM scenes WHERE scene_number = ?", (scene_number,))
                            result = cursor.fetchone()
                            if result:
                                self.selected_scene_id = result[0]
                        except ValueError:
                            self.log_message(f"无法解析场景编号: {scene_detail}")
                            return  # 直接返回
                
                conn.close()
            except Exception as e:
                self.log_message(f"获取场景ID时出错: {str(e)}")

    def perform_shot_split(self):
        """执行分镜头"""
        if not self.selected_scene_id:
            messagebox.showwarning("警告", "请先选择一个场景")
            return
            
        # 在新线程中执行分镜头，避免阻塞UI
        shot_split_thread = threading.Thread(target=self.split_scene_into_shots)
        shot_split_thread.daemon = True
        shot_split_thread.start()

    def split_scene_into_shots(self):
        """将场景分割成镜头"""
        try:
            self.root.after(0, lambda: self.progress.start())
            self.log_message("开始分镜头处理...")
            
            # 从数据库获取场景内容
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT content, title, segment_id FROM scenes WHERE id = ?", (self.selected_scene_id,))
            result = cursor.fetchone()
            
            if not result:
                self.root.after(0, lambda: self.log_message("未找到选定的场景"))
                self.root.after(0, lambda: self.progress.stop())
                return
                
            scene_content, scene_title, segment_id = result
            conn.close()
            
            # 调用AI进行分镜头
            shots = self.split_scene_with_ai(scene_content)
            
            if shots:
                # 保存结果
                self.current_shots = shots
                self.display_shots(shots)
                
                # 更新镜头列表
                self.root.after(0, self.update_shot_list)
                
                self.log_message(f"分镜头完成，共生成 {len(shots)} 个镜头")
            else:
                self.log_message("分镜头失败或未返回有效结果")
                
            self.root.after(0, lambda: self.progress.stop())
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"分镜头过程中出现错误: {str(e)}"))
            self.root.after(0, lambda: self.progress.stop())

    def split_scene_with_ai(self, scene_content):
        """使用AI将场景分割成镜头"""
        # 获取API密钥
        api_key = config_manager.get_api_key()
        
        if not api_key:
            self.log_message("未配置API密钥，使用本地方法")
            return self.local_split_scene_to_shots(scene_content)
        
        try:
            self.log_message("开始使用AI进行分镜头...")
            
            # 构建提示词，要求AI按照镜头要求进行分割
            prompt = f"""请将以下场景内容分割成多个镜头，并按照以下格式输出：

镜头 1.1.1【编号】

景别：【广角远景/近景/特写等】

视角：【俯视/仰视/平视/主观视角等】

描述：【详细的镜头描述内容】

角色：【出现在镜头中的角色】

道具/环境：【镜头中的道具和环境元素】

光线：【光线条件和效果】

情绪基调：【镜头的情绪氛围】

音效：【背景音效或特殊音效】

旁白：【如有旁白内容】

配乐：【建议的背景音乐类型】

要求：
1. 每个镜头都要有完整的描述
2. 镜头之间要有明确的逻辑关系
3. 保持内容的连贯性
4. 输出格式严格按照上述示例

场景内容：
{scene_content}"""
            
            headers = {
                "Authorization": "Bearer " + api_key,
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
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                self.log_message("AI分镜头完成")
                
                # 解析AI返回的镜头数据
                shots = self.parse_shots_from_ai_response(ai_response)
                return shots
            else:
                self.log_message(f"AI分镜头请求失败: {response.status_code}, {response.text}")
                return self.local_split_scene_to_shots(scene_content)
                
        except requests.exceptions.Timeout:
            self.log_message("AI分镜头请求超时，使用本地方法")
            return self.local_split_scene_to_shots(scene_content)
        except Exception as e:
            self.log_message(f"AI分镜头过程中出现错误: {str(e)}，使用本地方法")
            return self.local_split_scene_to_shots(scene_content)

    def parse_shots_from_ai_response(self, ai_response):
        """从AI响应中解析镜头信息"""
        shots = []
        
        import re
        
        # 更灵活的正则表达式来匹配镜头格式
        # 匹配 "镜头 X.X.X" 或 "镜头 X" 格式的模式，包括各种可能的格式变化
        shot_pattern = r'(镜头\s*[\d\.]+)[^\n]*\n(?:\s*景别[^：：]*[：:][^\n]*【([^】]*)】)?\s*\n(?:\s*视角[^：：]*[：:][^\n]*【([^】]*)】)?\s*\n(?:\s*描述[^：：]*[：:][^\n]*【([^】]*)】)?\s*\n(?:\s*角色[^：：]*[：:][^\n]*【([^】]*)】)?\s*\n(?:\s*道具/环境[^：：]*[：:][^\n]*【([^】]*)】)?\s*\n(?:\s*光线[^：：]*[：:][^\n]*【([^】]*)】)?\s*\n(?:\s*情绪基调[^：：]*[：:][^\n]*【([^】]*)】)?\s*\n(?:\s*音效[^：：]*[：:][^\n]*【([^】]*)】)?\s*\n(?:\s*旁白[^：：]*[：:][^\n]*【([^】]*)】)?\s*\n(?:\s*配乐[^：：]*[：:][^\n]*【([^】]*)】)?'
        
        matches = re.findall(shot_pattern, ai_response, re.MULTILINE)
        
        for match in matches:
            shot_data = {
                'id': match[0].strip(),
                'scene_details': {
                    'shot_number': match[0].strip(),
                    'scene_type': match[1] if match[1] else '未指定',
                    'perspective': match[2] if match[2] else '未指定',
                    'description': match[3] if match[3] else '未指定',
                    'characters': match[4] if match[4] else '未指定',
                    'props_env': match[5] if match[5] else '未指定',
                    'lighting': match[6] if match[6] else '未指定',
                    'emotional_tone': match[7] if match[7] else '未指定',
                    'sound_effects': match[8] if match[8] else '未指定',
                    'narration': match[9] if match[9] else '未指定',
                    'music': match[10] if match[10] else '未指定'
                }
            }
            shots.append(shot_data)
        
        # 如果上面的正则表达式没有匹配到，尝试更简单的模式
        if not shots:
            # 尝试匹配基本的镜头编号格式
            simple_shot_pattern = r'(镜头\s*[\d\.]+)'
            simple_matches = re.findall(simple_shot_pattern, ai_response)
            
            for shot_id in simple_matches:
                # 为每个镜头提取相关信息
                shot_start = ai_response.find(shot_id)
                next_shot_start = -1
                
                # 寻找下一个镜头的开始位置
                for next_shot in re.finditer(simple_shot_pattern, ai_response[shot_start + len(shot_id):]):
                    next_shot_start = shot_start + len(shot_id) + next_shot.start()
                    break
                
                # 提取当前镜头到下一个镜头之间的内容
                if next_shot_start != -1:
                    shot_content = ai_response[shot_start:next_shot_start]
                else:
                    shot_content = ai_response[shot_start:]
                
                shot_data = {
                    'id': shot_id.strip(),
                    'scene_details': {
                        'shot_number': shot_id.strip(),
                        'scene_type': self.extract_field_value(shot_content, '景别'),
                        'perspective': self.extract_field_value(shot_content, '视角'),
                        'description': self.extract_field_value(shot_content, '描述'),
                        'characters': self.extract_field_value(shot_content, '角色'),
                        'props_env': self.extract_field_value(shot_content, '道具/环境'),
                        'lighting': self.extract_field_value(shot_content, '光线'),
                        'emotional_tone': self.extract_field_value(shot_content, '情绪基调'),
                        'sound_effects': self.extract_field_value(shot_content, '音效'),
                        'narration': self.extract_field_value(shot_content, '旁白'),
                        'music': self.extract_field_value(shot_content, '配乐')
                    }
                }
                shots.append(shot_data)
        
        return shots

    def extract_field_value(self, content, field_name):
        """从内容中提取特定字段的值"""
        import re
        
        # 匹配各种格式的字段定义，如：景别：【值】、景别:【值】、景别： 值、景别: 值
        pattern = rf'{field_name}[^：:]*[：:][^【】]*【([^】]*)】|{field_name}[^：:]*[：:]\s*([^\n\r]+)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            # match可能是元组，取第一个非空值
            value = match[0] if match[0] else match[1] if isinstance(match, tuple) and len(match) > 1 else ''
            if value:
                # 清理值，移除多余的空白字符
                value = value.strip()
                return value
        
        return '未指定'

    def local_split_scene_to_shots(self, scene_content):
        """本地将场景分割成镜头的方法"""
        # 简单地将内容作为一个镜头返回
        shots = [{
            'id': '镜头 1.1.1',
            'scene_details': {
                'shot_number': '镜头 1.1.1',
                'scene_type': '中景',
                'perspective': '平视',
                'description': scene_content[:200] + '...' if len(scene_content) > 200 else scene_content,
                'characters': '未指定',
                'props_env': '未指定',
                'lighting': '自然光',
                'emotional_tone': '正常',
                'sound_effects': '无',
                'narration': '无',
                'music': '无'
            }
        }]
        
        return shots

    def display_shots(self, shots):
        """在中间结果显示区域显示镜头结果"""
        # 清空之前的内容
        self.shot_display.delete("1.0", tk.END)
        
        # 显示每个镜头
        for shot in shots:
            details = shot['scene_details']
            shot_text = f"""{details['shot_number']}【编号】

景别：【{details['scene_type']}】

视角：【{details['perspective']}】

描述：【{details['description']}】

角色：【{details['characters']}】

道具/环境：【{details['props_env']}】

光线：【{details['lighting']}】

情绪基调：【{details['emotional_tone']}】

音效：【{details['sound_effects']}】

旁白：【{details['narration']}】

配乐：【{details['music']}】

{'-'*50}

"""
            self.shot_display.insert(tk.END, shot_text)

    def update_shot_list(self):
        """更新右侧镜头列表"""
        # 清空列表框
        self.shot_listbox.delete(0, tk.END)
        
        # 添加镜头到列表框
        for shot in self.current_shots:
            self.shot_listbox.insert(tk.END, shot['id'])

    def on_shot_select(self, event):
        """当选中镜头列表中的项目时触发"""
        selection = self.shot_listbox.curselection()
        if selection:
            index = selection[0]
            shot_id = self.shot_listbox.get(index)
            
            # 在结果显示区域高亮显示选中的镜头
            self.highlight_shot_in_display(shot_id)

    def highlight_shot_in_display(self, shot_id):
        """在结果显示区域高亮显示指定的镜头"""
        # 清除之前的标记
        self.shot_display.tag_remove("highlight", "1.0", tk.END)
        
        # 查找并高亮显示选中的镜头
        content = self.shot_display.get("1.0", tk.END)
        start_idx = content.find(shot_id)
        
        if start_idx != -1:
            # 计算结束位置（到下一个镜头之前）
            end_idx = content.find("\n\n", start_idx)
            if end_idx == -1:
                end_idx = len(content)
            
            # 转换为tkinter的行.列格式
            start_line = content.count('\n', 0, start_idx) + 1
            start_col = start_idx - content.rfind('\n', 0, start_idx) - 1
            end_line = content.count('\n', 0, end_idx) + 1
            end_col = end_idx - content.rfind('\n', 0, end_idx) - 1
            
            start_pos = f"{start_line}.{start_col}"
            end_pos = f"{end_line}.{end_col}"
            
            # 应用高亮标签
            self.shot_display.tag_add("highlight", start_pos, end_pos)
            self.shot_display.tag_config("highlight", background="yellow", foreground="black")
            
            # 滚动到高亮位置
            self.shot_display.see(start_pos)

    def save_shots(self):
        """保存镜头到数据库"""
        if not self.current_shots:
            messagebox.showwarning("警告", "没有可保存的镜头数据")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查shots表是否存在，如果不存在则创建
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shots';")
            if not cursor.fetchone():
                # 创建shots表（使用与database.py中相同的结构）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS shots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scene_id INTEGER,
                        shot_number INTEGER NOT NULL,
                        description TEXT,
                        duration REAL,  -- 持续时间（秒）
                        camera_angle TEXT,  -- 镜头角度
                        character_actions TEXT,  -- 角色动作
                        dialogue TEXT,  -- 对话
                        props TEXT,  -- 道具
                        notes TEXT,  -- 备注
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.log_message("创建了缺失的shots表")
            
            # 删除该场景之前的所有镜头
            cursor.execute("DELETE FROM shots WHERE scene_id = ?", (self.selected_scene_id,))
            
            # 插入新的镜头数据
            for i, shot in enumerate(self.current_shots):
                details = shot['scene_details']
                cursor.execute("""
                    INSERT INTO shots (
                        scene_id, shot_number, description, camera_angle, 
                        character_actions, dialogue, props, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.selected_scene_id,
                    details['shot_number'],
                    details['description'],
                    details['scene_type'],  # 存储为镜头角度
                    details['characters'],  # 存储为角色动作
                    details['narration'],   # 存储为对话
                    details['props_env'],   # 存储为道具
                    f"视角:{details['perspective']}, 光线:{details['lighting']}, 情绪基调:{details['emotional_tone']}, 音效:{details['sound_effects']}, 配乐:{details['music']}"
                ))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", f"成功保存 {len(self.current_shots)} 个镜头")
            self.log_message(f"保存了 {len(self.current_shots)} 个镜头到数据库")
            
            # 重新加载场景以反映保存的镜头
            self.load_shot_counts_for_scenes()
            
        except Exception as e:
            self.log_message(f"保存镜头时出错: {str(e)}")
            messagebox.showerror("错误", f"保存镜头时出错: {str(e)}")

    def load_shot_counts_for_scenes(self):
        """为场景列表加载镜头数量统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询每个场景的镜头数量
            cursor.execute("""
                SELECT scene_id, COUNT(*) as shot_count 
                FROM shots 
                GROUP BY scene_id
            """)
            shot_counts = dict(cursor.fetchall())
            
            # 更新场景列表显示
            for i in range(self.scene_listbox.size()):
                scene_text = self.scene_listbox.get(i)
                
                # 提取场景ID和场景编号
                # 场景格式可能为 "场景 segment_id_S01: title (N个镜头)" 或 "segment_id_S01: title (N个镜头)" 或其他格式
                scene_part = scene_text.split(': ')[0]  # 获取 ": "前的部分
                
                # 检查scene_part是否就是完整格式化编号（如 EP01_P01_S01）
                if '_' in scene_part and scene_part.count('_S') > 0:
                    # 这种情况下，scene_part 可能是完整格式化编号，如 "EP01_P01_S01"
                    last_underscore_pos = scene_part.rfind('_')
                    if last_underscore_pos != -1:
                        segment_id = scene_part[:last_underscore_pos]  # 获取 "EP01_P01"
                        scene_num_part = scene_part[last_underscore_pos+1:]  # 获取 "S01"
                        
                        # 提取数字部分 (S01 -> 1)
                        if scene_num_part.startswith('S'):
                            try:
                                scene_number = int(scene_num_part[1:])  # 获取 S 后面的数字
                            except ValueError:
                                self.log_message(f"无法解析场景编号中的数字部分: {scene_num_part[1:]}")
                                continue  # 跳过当前项
                        else:
                            # 如果不是 S 开头，尝试直接转换为整数
                            try:
                                scene_number = int(scene_num_part)
                            except ValueError:
                                self.log_message(f"无法解析场景编号: {scene_num_part}")
                                continue  # 跳过当前项
                        
                        # 查询场景ID
                        cursor.execute("SELECT id FROM scenes WHERE segment_id = ? AND scene_number = ?", (segment_id, scene_number))
                        result = cursor.fetchone()
                        if result:
                            scene_id = result[0]
                            shot_count = shot_counts.get(scene_id, 0)
                            
                            # 保留原始标题部分
                            original_title_part = ': '.join(scene_text.split(': ')[1:]) if ': ' in scene_text else ''
                            # 移除原有的镜头计数
                            if ' (' in original_title_part:
                                original_title_part = original_title_part.split(' (')[0]
                            
                            updated_text = f"{scene_part}: {original_title_part} ({shot_count}个镜头)"
                            
                            # 重新插入项目
                            self.scene_listbox.delete(i)
                            self.scene_listbox.insert(i, updated_text)
                else:
                    # 传统格式 "场景 segment_id_S01"
                    if ' ' in scene_part:
                        scene_detail = scene_part.split(' ', 1)[1]  # 获取 "segment_id_S01"
                        
                        # 查找最后一个下划线的位置
                        last_underscore_pos = scene_detail.rfind('_')
                        if last_underscore_pos != -1:
                            segment_id = scene_detail[:last_underscore_pos]  # 获取 "EP01_P01"
                            scene_num_part = scene_detail[last_underscore_pos+1:]  # 获取 "S01"
                            
                            # 提取数字部分 (S01 -> 1)
                            if scene_num_part.startswith('S'):
                                try:
                                    scene_number = int(scene_num_part[1:])  # 获取 S 后面的数字
                                except ValueError:
                                    self.log_message(f"无法解析场景编号中的数字部分: {scene_num_part[1:]}")
                                    continue  # 跳过当前项
                            else:
                                # 如果不是 S 开头，尝试直接转换为整数
                                try:
                                    scene_number = int(scene_num_part)
                                except ValueError:
                                    self.log_message(f"无法解析场景编号: {scene_num_part}")
                                    continue  # 跳过当前项
                            
                            # 查询场景ID
                            cursor.execute("SELECT id FROM scenes WHERE segment_id = ? AND scene_number = ?", (segment_id, scene_number))
                            result = cursor.fetchone()
                            if result:
                                scene_id = result[0]
                                shot_count = shot_counts.get(scene_id, 0)
                                
                                # 保留原始标题部分
                                original_title_part = ': '.join(scene_text.split(': ')[1:]) if ': ' in scene_text else ''
                                # 移除原有的镜头计数
                                if ' (' in original_title_part:
                                    original_title_part = original_title_part.split(' (')[0]
                                
                                updated_text = f"场景 {segment_id}_S{scene_number:02d}: {original_title_part} ({shot_count}个镜头)"
                                
                                # 重新插入项目
                                self.scene_listbox.delete(i)
                                self.scene_listbox.insert(i, updated_text)
            
            conn.close()
        
        except Exception as e:
            self.log_message(f"加载镜头统计时出错: {str(e)}")

    def log_message(self, message):
        """向日志区域添加消息"""
        self.log_display.config(state='normal')
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = "[" + timestamp + "] " + message + "\n"
        self.log_display.insert(tk.END, formatted_message)
        self.log_display.see(tk.END)
        self.log_display.config(state='disabled')