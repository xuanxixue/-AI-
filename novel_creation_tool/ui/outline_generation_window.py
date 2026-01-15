import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading
import sqlite3
import os
import requests
import time
from utils.config_manager import config_manager


class OutlineGenerationWindow:
    """
    大纲生成窗口类
    包含左侧的选择列表功能（显示大纲理解和想法提取中保存的故事基本信息）
    和右侧的生成结果显示区域及运行按钮
    """

    def __init__(self, project_path):
        """
        初始化大纲生成窗口
        
        Args:
            project_path (str): 工程文件路径
        """
        self.project_path = project_path
        self.api_key = config_manager.get_api_key()  # 从全局配置加载API密钥
        
        # 创建工程数据库路径
        self.db_path = os.path.join(project_path, 'project.db')
        
        self.root = tk.Toplevel()
        self.root.title("大纲生成")
        self.root.geometry("1200x800")
        
        self.setup_ui()
        self.load_saved_stories()
    
    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        top_frame = tk.Frame(self.root, bg="#f0f0f0", height=50)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # 页面名字标签
        title_label = tk.Label(top_frame, text="大纲生成", font=("Microsoft YaHei", 12, "bold"), bg="#f0f0f0")
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 运行按钮
        self.run_btn = tk.Button(top_frame, text="运行", command=self.run_outline_generation, 
                           bg="#28a745", fg="white", relief="flat")
        self.run_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 主内容框架 - 左右分栏
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 分割窗口
        paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧 - 故事选择列表区域
        left_frame = tk.Frame(paned_window)
        left_label = tk.Label(left_frame, text="故事基本信息选择", font=("Microsoft YaHei", 10))
        left_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 创建列表框和滚动条
        listbox_frame = tk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 滚动条
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 列表框
        self.story_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, selectmode=tk.SINGLE)
        self.story_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.story_listbox.yview)
        
        # 添加到分割窗口
        paned_window.add(left_frame)
        
        # 右侧 - 生成结果显示区域
        right_frame = tk.Frame(paned_window)
        right_label = tk.Label(right_frame, text="大纲生成结果显示", font=("Microsoft YaHei", 10))
        right_label.pack(anchor=tk.NW, padx=5, pady=5)
        
        # 结果显示区域
        self.result_display = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=50, height=20)
        self.result_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 运行按钮（已在顶部，这里可能不需要）
        # 但可以添加一个额外的按钮或控件
        control_frame = tk.Frame(right_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 保存按钮
        save_btn = tk.Button(control_frame, text="保存大纲", command=self.save_generated_outline, 
                            bg="#ffc107", fg="black", relief="flat")
        save_btn.pack(side=tk.RIGHT, padx=5)
        
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
    
    def load_saved_stories(self):
        """加载已保存的故事基本信息（从大纲理解和想法提取中保存的数据）"""
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 清空列表框
            self.story_listbox.delete(0, tk.END)
            
            # 从大纲理解表获取数据
            cursor.execute('''
                SELECT id, title, input_content, analysis_result, created_at 
                FROM outline_understanding 
                ORDER BY created_at DESC
            ''')
            outline_understanding_records = cursor.fetchall()
            
            # 从想法提取表获取数据
            cursor.execute('''
                SELECT id, title, chat_content, extracted_content, created_at 
                FROM extracted_ideas 
                ORDER BY created_at DESC
            ''')
            extracted_ideas_records = cursor.fetchall()
            
            # 存储记录信息以便后续使用
            self.saved_records = []
            
            # 将大纲理解记录添加到列表
            for record in outline_understanding_records:
                item_id, title, input_content, analysis_result, created_at = record
                display_text = f"[大纲理解] {title} ({created_at})"
                self.story_listbox.insert(tk.END, display_text)
                self.saved_records.append({
                    'type': 'outline_understanding',
                    'data': record
                })
                
            # 将想法提取记录添加到列表
            for record in extracted_ideas_records:
                item_id, title, chat_content, extracted_content, created_at = record
                display_text = f"[想法提取] {title} ({created_at})"
                self.story_listbox.insert(tk.END, display_text)
                self.saved_records.append({
                    'type': 'extracted_ideas',
                    'data': record
                })
                
            # 绑定选择事件
            self.story_listbox.bind("<<ListboxSelect>>", self.on_selection_change)
            
            conn.close()
            
            # 如果有记录，启用运行按钮
            if self.story_listbox.size() > 0:
                self.run_btn.config(state='normal')
            else:
                self.run_btn.config(state='disabled')
                
        except Exception as e:
            self.log_message(f"加载已保存故事时出错: {str(e)}")
            messagebox.showerror("错误", f"加载已保存故事时出错: {str(e)}")
    
    def on_selection_change(self, event):
        """当选择项改变时触发"""
        selection = self.story_listbox.curselection()
        if selection:
            index = selection[0]
            # 这里可以根据选中的项目进行相应处理
            self.log_message(f"选择了第 {index + 1} 个项目")
    
    def run_outline_generation(self):
        """运行大纲生成"""
        selection = self.story_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先从左侧选择一个故事基本信息")
            return
            
        if not self.api_key:
            messagebox.showwarning("警告", "请先配置API密钥")
            return
            
        # 获取选中的项目信息
        index = selection[0]
        selected_item = self.story_listbox.get(index)
        
        # 清空之前的日志并添加新的日志
        self.clear_log()
        self.log_message(f"开始生成大纲，使用选中的项目: {selected_item}")
        
        # 启动进度条
        self.progress.start()
        
        # 禁用运行按钮以防止重复点击
        self.run_btn.config(state='disabled')
        
        # 在新线程中运行大纲生成，避免阻塞UI
        generation_thread = threading.Thread(target=self.perform_outline_generation, args=(index, selected_item))
        generation_thread.daemon = True
        generation_thread.start()
    
    def perform_outline_generation(self, index, selected_item):
        """执行大纲生成"""
        try:
            self.root.after(0, lambda: self.log_message("正在调用AI生成大纲..."))
            
            # 从数据库获取选中的具体数据
            content = self.get_selected_content(index, selected_item)
            
            if not content:
                self.root.after(0, lambda: self.update_result_display("无法获取选中的内容"))
                return
                
            # 调用AI生成大纲
            result = self.generate_outline_with_ai(content)
            
            # 在主线程中更新结果
            self.root.after(0, self.update_result_display, result)
        except Exception as e:
            error_msg = "大纲生成过程中出现错误: " + str(e)
            self.root.after(0, self.update_result_display, error_msg)
    
    def get_selected_content(self, index, selected_item):
        """获取选中项目的具体内容"""
        try:
            if index < len(self.saved_records):
                record_info = self.saved_records[index]
                record_type = record_info['type']
                item_id, title, content1, content2, created_at = record_info['data']
                
                if record_type == 'outline_understanding':
                    # 大纲理解记录：input_content, analysis_result
                    content = f"大纲理解 - 标题: {title}\n\n输入内容: {content1}\n\n分析结果: {content2}"
                elif record_type == 'extracted_ideas':
                    # 想法提取记录：chat_content, extracted_content
                    content = f"想法提取 - 标题: {title}\n\n对话内容: {content1}\n\n提取内容: {content2}"
                else:
                    content = ""
                
                return content
            else:
                return ""
        except Exception as e:
            self.log_message(f"获取选中内容时出错: {str(e)}")
            return ""
    
    def generate_outline_with_ai(self, content):
        """
        使用AI生成大纲
        """
        # 构建提示词，按照指定的格式生成大纲
        prompt = f"""请根据以下故事信息生成一个详细的大纲，必须严格按照以下格式输出，不要添加任何额外的解释或评论：

小说标题（暂定）：《春日长椅没有她》

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

第3章 食堂里的糖醋排骨

林知夏总点糖醋排骨，沈砚悄悄记下，某天"恰好"多打一份推给她："吃不完。"

第4章 图书馆的纸条战争

两人在自习室传纸条斗嘴，从物理题吵到漫画，最后沈砚画了个小太阳送她。

第5章 生病时的温水

林知夏发烧请假，沈砚翻墙进她家院子（她住老城区平房），把笔记和退烧药放在窗台。

第6章 校运会的终点线

林知夏跑三千米体力不支，沈砚冲进跑道背她去医务室，全班起哄，他面无表情却脚步极稳。

第7章 雨夜电话

林知夏做噩梦见家族往事惊醒，拨通沈砚电话。他安静听她哭，只说："我在。"

第8章 摩天轮上的秘密

班级活动坐摩天轮，停电卡在最高点。黑暗中，沈砚轻握她的手："别怕，有我。"

第9章 初雪与围巾

第一场雪，林知夏织了条歪歪扭扭的围巾，硬套在沈砚脖子上。他一整个冬天没摘。

第10章 我们是最好的朋友

两人在天台看星星，林知夏笑着说"我们永远是最好的朋友"。沈砚沉默良久，点头。

✨甜度峰值：日常细节堆砌温暖，双向暗恋未挑明，但陪伴已深入骨髓。

【第二部分：无声裂痕】（第11–20章）

第11章 家族晚宴的对视

林父带知夏出席商业晚宴，首次见到沈父。沈砚想上前，被林父眼神制止。知夏脸色惨白。

第12章 父亲的警告

林父告知知夏：沈家是灭门仇人，当年林氏破产、母亲自杀皆因沈家设局。她必须远离沈砚。

第13章 开始疏远

知夏突然不再回消息，躲着沈砚。他追问，她只说："我们不适合做朋友了。"

第14章 他追到旧巷

沈砚找到知夏家，撞见她与父亲激烈争吵。她哭着喊："你根本不知道我家经历了什么！"

第15章 加入学生会

知夏主动加入与沈砚对立的学生派系（由林家扶持），开始公开反对他的提案。

第16章 辩论赛上的刀

两人在校园辩论赛正面对决。知夏逻辑缜密击败沈砚，台下掌声雷动，他眼中只剩她冷漠的脸。

第17章 他仍留着围巾

寒冬，沈砚依然围着那条旧围巾。知夏远远看见，转身躲进雪里流泪。

第18章 林家的交易

林父以"重启林氏"为条件，要求知夏接近沈砚获取沈氏新能源机密。她被迫答应。

第19章 最后一次温柔

知夏假装和解，约沈砚看樱花。他欣喜赴约，她却偷拍他手机中的文件。离开时，樱花落在他肩头，她没回头。

第20章 信任崩塌

沈砚发现泄密，证据指向知夏。他站在雨中等她解释，她只说："对不起，但我必须这么做。"

💔转折完成：女主为家族大义走向对立，男主不知真相，心碎成冰。

【第三部分：宿命之刃】（第21–29章）

第21章 家族和解

政府介入调查旧案，真相大白：当年陷害林家的是第三方，沈父实为暗中保护林家未果。两家长辈握手言和。

第22章 他来找她了

沈砚得知真相，狂奔向知夏家，想告诉她一切误会解开。却见她正将U盘交给神秘人。

第23章 误解的顶点

沈砚误以为她仍在背叛，怒斥："你到底要毁掉多少？"知夏欲言又止，只苦笑："随你怎么想。"

第24章 终局任务

林父命令知夏完成最后一次行动——引爆沈氏实验室制造事故，逼沈家彻底退出市场。

第25章 她选择牺牲

知夏潜入实验室，却偷偷拆除炸弹，留下自首信："用我的命，换两家和平。"

第26章 他持枪而来

沈砚接到警报，持家族安保权限闯入。黑暗中，他看见人影，本能开枪——

第27章 血染樱花

灯光亮起，倒下的是知夏。她手中攥着拆下的引信，和一张写满"对不起"的纸。

第28章 真相与崩溃

警方还原现场：知夏是阻止爆炸的英雄。沈砚跪在血泊中，撕心裂肺："为什么不说？！"

第29章 葬礼无人知

知夏葬礼低调举行。沈砚站在远处，手中紧握她当年送的樱花标本，已枯成灰。

🔪刀子拉满：误会解除太迟，爱意成绝响。

【终章：庄周梦蝶】（第30章）

第30章 春日长椅没有她

三年后，沈砚重回高中校园。樱花纷飞，长椅上坐着穿校服的林知夏，笑着对他招手："你来啦？"

他狂喜奔去，伸手触碰——

她身影如烟消散，只余一片樱花落在掌心。

长椅空荡，阳光正好。

沈砚缓缓坐下，闭眼微笑："这次…换我等你。"

画面渐暗，现实与梦境交融，不知是梦是真。

🌸终章呼应开头，用《还剩三个月命》的"存在即消逝"+《病娇花卷》的"执念幻影"，达成宿命闭环。

风格说明：

全程无婚姻、无超自然设定（除终章幻觉），纯现实向青春悲剧

甜在细节（共伞、围巾、纸条），虐在沉默（女主不解释、男主不知情）

家族世仇非狗血，而是时代洪流下的误会与牺牲

终章"庄周梦蝶"处理：不明确是否真实复活，留给读者余韵。

请严格按照以上格式生成大纲，使用相同的结构和符号（如【】、章节标题、情感标记如✨💔🔪🌸等）。现在，请根据以下故事信息生成大纲：
{content}"""

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
        self.log_message("大纲生成完成")
    
    def save_generated_outline(self):
        """保存生成的大纲到数据库"""
        try:
            # 获取当前生成的大纲
            result_text = self.result_display.get("1.0", tk.END).strip()
            
            if not result_text or result_text.startswith("API请求失败") or result_text.startswith("API调用过程中出现错误"):
                messagebox.showwarning("警告", "没有有效的大纲内容可供保存")
                return
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建大纲表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generated_outlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    source_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入数据
            title = f"大纲生成_{time.strftime('%Y%m%d_%H%M%S')}"
            selection = self.story_listbox.curselection()
            source_info = ""
            if selection:
                source_info = self.story_listbox.get(selection[0])
            
            cursor.execute('''
                INSERT INTO generated_outlines (title, content, source_info)
                VALUES (?, ?, ?)
            ''', (title, result_text, source_info))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "生成的大纲已保存到数据库")
            
        except Exception as e:
            messagebox.showerror("错误", "保存大纲时出现错误: " + str(e))


def main():
    """测试函数"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    app = OutlineGenerationWindow(r"C:\test\project")  # 测试路径
    root.mainloop()


if __name__ == "__main__":
    main()