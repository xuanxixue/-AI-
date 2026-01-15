import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import os
import threading
import time
import json
import requests
from utils.config_manager import config_manager


class KeyframeSplitWindow:
    """
    故事分关键帧窗口类
    包含左侧镜头列表、中间关键帧处理区域和右侧关键帧展示区
    """

    def __init__(self, project_path):
        """
        初始化故事分关键帧窗口
        
        Args:
            project_path (str): 工程文件路径
        """
        self.project_path = project_path
        self.db_path = os.path.join(project_path, 'project.db')
        
        self.root = tk.Toplevel()
        self.root.title("故事分关键帧")
        self.root.geometry("1400x900")
        
        self.selected_shot_id = None
        self.current_keyframes = []
        
        self.setup_ui()
        self.load_shots()

    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        top_frame = tk.Frame(self.root, bg="#f0f0f0", height=50)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # 页面名字标签
        title_label = tk.Label(top_frame, text="故事分关键帧", font=("Microsoft YaHei", 12, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 主内容框架 - 三栏布局
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 分割窗口 - 三列
        paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧 - 镜头选择区域
        left_frame = tk.Frame(paned_window)
        left_label = tk.Label(left_frame, text="镜头列表", font=("Microsoft YaHei", 10))
        left_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 镜头列表框
        listbox_frame = tk.Frame(left_frame)
        self.shot_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, width=30)
        shot_scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.shot_listbox.yview)
        self.shot_listbox.config(yscrollcommand=shot_scrollbar.set)
        
        self.shot_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        shot_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 分关键帧按钮
        split_button = tk.Button(left_frame, text="分关键帧", command=self.perform_keyframe_split, 
                                 bg="#28a745", fg="white", relief="flat", height=2)
        split_button.pack(pady=5, padx=5, fill=tk.X)
        
        # 添加到分割窗口
        paned_window.add(left_frame)
        
        # 中间 - 关键帧结果显示区域
        middle_frame = tk.Frame(paned_window)
        middle_label = tk.Label(middle_frame, text="关键帧生成结果", font=("Microsoft YaHei", 10))
        middle_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 关键帧结果显示区域
        self.keyframe_display = scrolledtext.ScrolledText(middle_frame, wrap=tk.WORD, width=50, height=20)
        self.keyframe_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 保存按钮
        save_button = tk.Button(middle_frame, text="保存关键帧", command=self.save_keyframes, 
                                bg="#ffc107", fg="black", relief="flat", height=2)
        save_button.pack(pady=5, padx=5, fill=tk.X)
        
        # 添加到分割窗口
        paned_window.add(middle_frame)
        
        # 右侧 - 关键帧展示区域
        right_frame = tk.Frame(paned_window)
        right_label = tk.Label(right_frame, text="关键帧展示", font=("Microsoft YaHei", 10))
        right_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 关键帧展示框
        keyframe_listbox_frame = tk.Frame(right_frame)
        self.keyframe_listbox = tk.Listbox(keyframe_listbox_frame, selectmode=tk.SINGLE, width=30)
        keyframe_list_scrollbar = tk.Scrollbar(keyframe_listbox_frame, orient=tk.VERTICAL, command=self.keyframe_listbox.yview)
        self.keyframe_listbox.config(yscrollcommand=keyframe_list_scrollbar.set)
        
        self.keyframe_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        keyframe_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        keyframe_listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定关键帧选择事件
        self.keyframe_listbox.bind('<<ListboxSelect>>', self.on_keyframe_select)
        
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
        
        # 绑定镜头选择事件
        self.shot_listbox.bind('<<ListboxSelect>>', self.on_shot_select)

    def load_shots(self):
        """加载已保存的镜头数据"""
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查shots表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shots';")
            if not cursor.fetchone():
                self.log_message("警告: shots表不存在，可能需要先使用故事分镜头功能生成镜头数据")
                # 清空列表框
                self.shot_listbox.delete(0, tk.END)
                conn.close()
                return
            
            # 查询镜头数据
            cursor.execute("""
                SELECT s.id, s.shot_number, s.description, s.scene_id
                FROM shots s
                ORDER BY s.scene_id, s.shot_number
            """)
            shots = cursor.fetchall()
            
            # 清空列表框
            self.shot_listbox.delete(0, tk.END)
            
            # 添加镜头到列表框
            for shot in shots:
                shot_id, shot_number, description, scene_id = shot
                # 确保shot_number不是None或空值
                if shot_number is None:
                    shot_number = f"镜头_{shot_id}"
                
                # 截取描述的前30个字符作为显示内容
                display_desc = description[:30] + "..." if description and len(description) > 30 else description if description else ""
                
                shot_text = f"{shot_number}: {display_desc}" if display_desc else f"{shot_number}"
                self.shot_listbox.insert(tk.END, shot_text)
            
            conn.close()
            
            self.log_message(f"加载了 {len(shots)} 个镜头")
            
        except Exception as e:
            self.log_message(f"加载镜头时出错: {str(e)}")

    def on_shot_select(self, event):
        """当选中镜头列表中的项目时触发"""
        selection = self.shot_listbox.curselection()
        if selection:
            index = selection[0]
            shot_info = self.shot_listbox.get(index)
            self.log_message(f"选择了镜头: {shot_info}")
            
            # 获取镜头ID（通过查询数据库）
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 从镜头信息中提取shot_number
                shot_number = shot_info.split(':')[0]  # 获取 ":" 前的部分
                
                # 查询数据库获取镜头ID
                cursor.execute("SELECT id FROM shots WHERE shot_number = ?", (shot_number,))
                result = cursor.fetchone()
                if result:
                    self.selected_shot_id = result[0]
                    self.log_message(f"成功获取镜头ID: {self.selected_shot_id} 对应 shot_number: {shot_number}")
                else:
                    self.log_message(f"在数据库中未找到匹配的镜头: {shot_number}")
                
                conn.close()
            except Exception as e:
                self.log_message(f"获取镜头ID时出错: {str(e)}")

    def perform_keyframe_split(self):
        """执行分关键帧"""
        if not self.selected_shot_id:
            messagebox.showwarning("警告", "请先选择一个镜头")
            return
            
        # 在新线程中执行分关键帧，避免阻塞UI
        keyframe_split_thread = threading.Thread(target=self.split_shot_into_keyframes)
        keyframe_split_thread.daemon = True
        keyframe_split_thread.start()

    def split_shot_into_keyframes(self):
        """将镜头分割成关键帧"""
        try:
            self.root.after(0, lambda: self.progress.start())
            self.log_message("开始分关键帧处理...")
            
            # 从数据库获取镜头内容
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT description, shot_number, scene_id FROM shots WHERE id = ?", (self.selected_shot_id,))
            result = cursor.fetchone()
            
            if not result:
                self.root.after(0, lambda: self.log_message("未找到选定的镜头"))
                self.root.after(0, lambda: self.progress.stop())
                return
                
            shot_description, shot_number, scene_id = result
            conn.close()
            
            # 调用AI进行关键帧生成
            keyframes = self.generate_keyframes_with_ai(shot_description, shot_number)
            
            if keyframes:
                # 保存结果
                self.current_keyframes = keyframes
                self.display_keyframes(keyframes)
                
                # 更新关键帧列表
                self.root.after(0, self.update_keyframe_list)
                
                self.log_message(f"分关键帧完成，共生成 {len(keyframes)} 个关键帧")
            else:
                self.log_message("分关键帧失败或未返回有效结果")
                
            self.root.after(0, lambda: self.progress.stop())
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"分关键帧过程中出现错误: {str(e)}"))
            self.root.after(0, lambda: self.progress.stop())

    def generate_keyframes_with_ai(self, shot_description, shot_number):
        """使用AI将镜头分割成关键帧"""
        # 获取API密钥
        api_key = config_manager.get_api_key()
        
        if not api_key:
            self.log_message("未配置API密钥，使用本地方法")
            return self.local_generate_keyframes(shot_description, shot_number)
        
        try:
            self.log_message("开始使用AI进行关键帧生成...")
            
            # 构建提示词，要求AI按照关键帧要求进行生成
            prompt = f"""请将以下镜头内容分割成多个关键帧，并按照以下格式输出：

关键帧ID: EP01_P01_S01_SH01_KF01

时间戳: 0.0秒

描述: 镜头起始帧。广角远景展现埃索斯大陆东北荒原全景。灰白天空低垂，风沙在地表形成细微流动轨迹。天然石窟嵌于陡峭岩壁中，入口呈异常规整的长方形，边缘锐利如被巨力切割，与周围自然地貌形成强烈反差。远处稀疏植被在风中轻微摇曳。

构图: 广角远景（焦距≈16mm），画面三分法：石窟位于右下交叉点，天际线压低以强调荒原压迫感。

视角：无

角色动作: 无具体人物，仅2–3个模糊人影从石窟入口缓慢进出，呈剪影状，动作迟缓而有序。

情绪: 原始、肃穆、秩序初萌；带有神秘的非自然感。

摄像机姿态: 固定机位，略带俯角（-5°），模拟"神之视角"审视人类早期聚居。

光影变化: 自然天光漫射，整体冷调（色温≈7500K），石窟入口因背光形成深邃剪影，但边缘受侧光勾勒出微弱高光。

音效提示: 风声低鸣，夹杂细沙摩擦岩壁的窸窣声。

旁白：

配乐：

要求：
1. 每个关键帧都要有完整的时间戳、描述、构图、视角、角色动作、情绪、摄像机姿态、光影变化、音效提示、旁白和配乐信息
2. 关键帧之间要有明确的时间序列关系
3. 保持内容的连贯性和逻辑性
4. 输出格式严格按照上述示例

镜头内容：
{shot_description}"""
            
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
                self.log_message("AI关键帧生成完成")
                
                # 解析AI返回的关键帧数据
                keyframes = self.parse_keyframes_from_ai_response(ai_response, shot_number)
                return keyframes
            else:
                self.log_message(f"AI关键帧生成请求失败: {response.status_code}, {response.text}")
                return self.local_generate_keyframes(shot_description, shot_number)
                
        except requests.exceptions.Timeout:
            self.log_message("AI关键帧生成请求超时，使用本地方法")
            return self.local_generate_keyframes(shot_description, shot_number)
        except Exception as e:
            self.log_message(f"AI关键帧生成过程中出现错误: {str(e)}，使用本地方法")
            return self.local_generate_keyframes(shot_description, shot_number)

    def parse_keyframes_from_ai_response(self, ai_response, shot_number):
        """从AI响应中解析关键帧信息"""
        keyframes = []
        
        import re
        
        # 正则表达式匹配关键帧格式
        # 匹配 "关键帧ID: ..." 的格式
        keyframe_pattern = r'(关键帧ID:\s*[A-Z0-9_]+)\s*\n(?:\s*时间戳:[^\n]*\n)?(?:\s*描述:[^\n]*\n)?(?:\s*构图:[^\n]*\n)?(?:\s*视角:[^\n]*\n)?(?:\s*角色动作:[^\n]*\n)?(?:\s*情绪:[^\n]*\n)?(?:\s*摄像机姿态:[^\n]*\n)?(?:\s*光影变化:[^\n]*\n)?(?:\s*音效提示:[^\n]*\n)?(?:\s*旁白:[^\n]*\n)?(?:\s*配乐:[^\n]*\n)?'
        
        # 更灵活的正则表达式，能够捕获完整的段落
        keyframe_pattern = r'(关键帧ID:\s*([A-Z0-9_]+))\s*\n时间戳:\s*([^\n]*)\n描述:\s*([^\n]*)\n构图:\s*([^\n]*)\n视角:\s*([^\n]*)\n角色动作:\s*([^\n]*)\n情绪:\s*([^\n]*)\n摄像机姿态:\s*([^\n]*)\n光影变化:\s*([^\n]*)\n音效提示:\s*([^\n]*)\n旁白:\s*([^\n]*)\n配乐:\s*([^\n]*)'
        
        matches = re.findall(keyframe_pattern, ai_response, re.MULTILINE)
        
        for match in matches:
            keyframe_data = {
                'id': match[0],  # 完整的关键帧ID
                'keyframe_id': match[1],  # 纯关键帧ID
                'timestamp': match[2],
                'description': match[3],
                'composition': match[4],
                'perspective': match[5],
                'character_actions': match[6],
                'emotion': match[7],
                'camera_pose': match[8],
                'lighting_changes': match[9],
                'audio_hint': match[10],
                'narration': match[11],
                'music': match[12]
            }
            keyframes.append(keyframe_data)
        
        # 如果上面的正则表达式没有匹配到，尝试更简单的模式
        if not keyframes:
            # 尝试匹配基本的关键帧ID格式
            simple_keyframe_pattern = r'(关键帧ID:\s*[A-Z0-9_]+)'
            simple_matches = re.findall(simple_keyframe_pattern, ai_response)
            
            for keyframe_id in simple_matches:
                # 为每个关键帧提取相关信息
                keyframe_start = ai_response.find(keyframe_id)
                next_keyframe_start = -1
                
                # 寻找下一个关键帧的开始位置
                for next_keyframe in re.finditer(simple_keyframe_pattern, ai_response[keyframe_start + len(keyframe_id):]):
                    next_keyframe_start = keyframe_start + len(keyframe_id) + next_keyframe.start()
                    break
                
                # 提取当前关键帧到下一个关键帧之间的内容
                if next_keyframe_start != -1:
                    keyframe_content = ai_response[keyframe_start:next_keyframe_start]
                else:
                    keyframe_content = ai_response[keyframe_start:]
                
                keyframe_data = {
                    'id': keyframe_id.strip(),
                    'keyframe_id': keyframe_id.replace('关键帧ID: ', '').strip(),
                    'timestamp': self.extract_field_value(keyframe_content, '时间戳'),
                    'description': self.extract_field_value(keyframe_content, '描述'),
                    'composition': self.extract_field_value(keyframe_content, '构图'),
                    'perspective': self.extract_field_value(keyframe_content, '视角'),
                    'character_actions': self.extract_field_value(keyframe_content, '角色动作'),
                    'emotion': self.extract_field_value(keyframe_content, '情绪'),
                    'camera_pose': self.extract_field_value(keyframe_content, '摄像机姿态'),
                    'lighting_changes': self.extract_field_value(keyframe_content, '光影变化'),
                    'audio_hint': self.extract_field_value(keyframe_content, '音效提示'),
                    'narration': self.extract_field_value(keyframe_content, '旁白'),
                    'music': self.extract_field_value(keyframe_content, '配乐')
                }
                keyframes.append(keyframe_data)
        
        # 如果仍然没有匹配到，但AI确实返回了内容，则尝试查找关键信息
        if not keyframes:
            # 尝试从整个响应中提取基本信息
            timestamp_match = re.search(r'时间戳:\s*([^\n]+)', ai_response)
            description_match = re.search(r'描述:\s*([^\n]+)', ai_response)
            composition_match = re.search(r'构图:\s*([^\n]+)', ai_response)
            perspective_match = re.search(r'视角:\s*([^\n]+)', ai_response)
            character_actions_match = re.search(r'角色动作:\s*([^\n]+)', ai_response)
            emotion_match = re.search(r'情绪:\s*([^\n]+)', ai_response)
            camera_pose_match = re.search(r'摄像机姿态:\s*([^\n]+)', ai_response)
            lighting_changes_match = re.search(r'光影变化:\s*([^\n]+)', ai_response)
            audio_hint_match = re.search(r'音效提示:\s*([^\n]+)', ai_response)
            narration_match = re.search(r'旁白:\s*([^\n]+)', ai_response)
            music_match = re.search(r'配乐:\s*([^\n]+)', ai_response)
            
            # 生成关键帧ID基于镜头编号
            generated_keyframe_id = f"{shot_number}_KF01" if shot_number else "UNKNOWN_KF01"
            
            keyframe = {
                'id': f"关键帧ID: {generated_keyframe_id}",
                'keyframe_id': generated_keyframe_id,
                'timestamp': timestamp_match.group(1).strip() if timestamp_match else '0.0秒',
                'description': description_match.group(1).strip() if description_match else ai_response[:100] + "..." if len(ai_response) > 100 else ai_response,
                'composition': composition_match.group(1).strip() if composition_match else '未指定',
                'perspective': perspective_match.group(1).strip() if perspective_match else '未指定',
                'character_actions': character_actions_match.group(1).strip() if character_actions_match else '未指定',
                'emotion': emotion_match.group(1).strip() if emotion_match else '未指定',
                'camera_pose': camera_pose_match.group(1).strip() if camera_pose_match else '未指定',
                'lighting_changes': lighting_changes_match.group(1).strip() if lighting_changes_match else '未指定',
                'audio_hint': audio_hint_match.group(1).strip() if audio_hint_match else '未指定',
                'narration': narration_match.group(1).strip() if narration_match else '未指定',
                'music': music_match.group(1).strip() if music_match else '未指定'
            }
            keyframes.append(keyframe)
        
        return keyframes

    def extract_field_value(self, content, field_name):
        """从内容中提取特定字段的值"""
        import re
        
        # 匹配各种格式的字段定义，如：时间戳:值、时间戳：值
        pattern = rf'{field_name}[：:]\s*([^\n\r]+)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            if match:
                # 清理值，移除多余的空白字符
                value = match.strip()
                return value
        
        return '未指定'

    def local_generate_keyframes(self, shot_description, shot_number):
        """本地生成关键帧的方法"""
        # 简单地将内容作为一个关键帧返回
        keyframe_id = f"{shot_number}_KF01" if shot_number else "UNKNOWN_KF01"
        keyframes = [{
            'id': f"关键帧ID: {keyframe_id}",
            'keyframe_id': keyframe_id,
            'timestamp': '0.0秒',
            'description': shot_description[:200] + '...' if len(shot_description) > 200 else shot_description,
            'composition': '未指定',
            'perspective': '未指定',
            'character_actions': '未指定',
            'emotion': '未指定',
            'camera_pose': '固定机位',
            'lighting_changes': '未指定',
            'audio_hint': '未指定',
            'narration': '未指定',
            'music': '未指定'
        }]
        
        return keyframes

    def display_keyframes(self, keyframes):
        """在中间结果显示区域显示关键帧结果"""
        # 清空之前的内容
        self.keyframe_display.delete("1.0", tk.END)
        
        # 显示每个关键帧
        for keyframe in keyframes:
            keyframe_text = f"""{keyframe['id']}

时间戳: {keyframe['timestamp']}

描述: {keyframe['description']}

构图: {keyframe['composition']}

视角：{keyframe['perspective']}

角色动作: {keyframe['character_actions']}

情绪: {keyframe['emotion']}

摄像机姿态: {keyframe['camera_pose']}

光影变化: {keyframe['lighting_changes']}

音效提示: {keyframe['audio_hint']}

旁白：{keyframe['narration']}

配乐：{keyframe['music']}

{'-'*50}

"""
            self.keyframe_display.insert(tk.END, keyframe_text)

    def update_keyframe_list(self):
        """更新右侧关键帧列表"""
        # 清空列表框
        self.keyframe_listbox.delete(0, tk.END)
        
        # 添加关键帧到列表框
        for keyframe in self.current_keyframes:
            self.keyframe_listbox.insert(tk.END, keyframe['id'])

    def on_keyframe_select(self, event):
        """当选中关键帧列表中的项目时触发"""
        selection = self.keyframe_listbox.curselection()
        if selection:
            index = selection[0]
            keyframe_id = self.keyframe_listbox.get(index)
            
            # 在结果显示区域高亮显示选中的关键帧
            self.highlight_keyframe_in_display(keyframe_id)

    def highlight_keyframe_in_display(self, keyframe_id):
        """在结果显示区域高亮显示指定的关键帧"""
        # 清除之前的标记
        self.keyframe_display.tag_remove("highlight", "1.0", tk.END)
        
        # 查找并高亮显示选中的关键帧
        content = self.keyframe_display.get("1.0", tk.END)
        start_idx = content.find(keyframe_id)
        
        if start_idx != -1:
            # 计算结束位置（到下一个关键帧之前）
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
            self.keyframe_display.tag_add("highlight", start_pos, end_pos)
            self.keyframe_display.tag_config("highlight", background="yellow", foreground="black")
            
            # 滚动到高亮位置
            self.keyframe_display.see(start_pos)

    def save_keyframes(self):
        """保存关键帧到数据库"""
        if not self.current_keyframes:
            messagebox.showwarning("警告", "没有可保存的关键帧数据")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查keyframes表是否存在，如果不存在则创建
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keyframes';")
            if not cursor.fetchone():
                # 创建keyframes表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS keyframes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shot_id INTEGER,
                        keyframe_number INTEGER NOT NULL,
                        keyframe_id TEXT,
                        timestamp TEXT,
                        description TEXT,
                        composition TEXT,
                        perspective TEXT,
                        character_actions TEXT,
                        emotion TEXT,
                        camera_pose TEXT,
                        lighting_changes TEXT,
                        audio_hint TEXT,
                        narration TEXT,
                        music TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.log_message("创建了缺失的keyframes表")
            
            # 删除该镜头之前的所有关键帧
            cursor.execute("DELETE FROM keyframes WHERE shot_id = ?", (self.selected_shot_id,))
            
            # 插入新的关键帧数据
            for i, keyframe in enumerate(self.current_keyframes):
                cursor.execute("""
                    INSERT INTO keyframes (
                        shot_id, keyframe_number, keyframe_id, timestamp, 
                        description, composition, perspective, character_actions, 
                        emotion, camera_pose, lighting_changes, audio_hint, 
                        narration, music
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.selected_shot_id,
                    i+1,  # 关键帧序号
                    keyframe['keyframe_id'],
                    keyframe['timestamp'],
                    keyframe['description'],
                    keyframe['composition'],
                    keyframe['perspective'],
                    keyframe['character_actions'],
                    keyframe['emotion'],
                    keyframe['camera_pose'],
                    keyframe['lighting_changes'],
                    keyframe['audio_hint'],
                    keyframe['narration'],
                    keyframe['music']
                ))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", f"成功保存 {len(self.current_keyframes)} 个关键帧")
            self.log_message(f"保存了 {len(self.current_keyframes)} 个关键帧到数据库")
            
        except Exception as e:
            self.log_message(f"保存关键帧时出错: {str(e)}")
            messagebox.showerror("错误", f"保存关键帧时出错: {str(e)}")

    def log_message(self, message):
        """向日志区域添加消息"""
        self.log_display.config(state='normal')
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = "[" + timestamp + "] " + message + "\n"
        self.log_display.insert(tk.END, formatted_message)
        self.log_display.see(tk.END)
        self.log_display.config(state='disabled')