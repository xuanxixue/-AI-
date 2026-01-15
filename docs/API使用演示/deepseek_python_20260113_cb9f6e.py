import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import requests
import json
import time
import io
import base64
from PIL import Image, ImageTk
import os


class ModelScopeImageGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("魔塔社区AI图像生成与编辑工具")
        self.root.geometry("1100x800")

        # 配置
        self.base_url = 'https://api-inference.modelscope.cn/'
        self.api_key = "ms-bfd13a90-db3b-433a-9baa-632cc2e9bbac"

        # 任务队列
        self.task_queue = queue.Queue()
        self.current_task_id = None
        self.is_running = False

        # 当前标签页的模型
        self.current_model = "generation"

        # 图片保存引用
        self.current_image_pil = None

        # 初始化日志缓冲区
        self.log_buffer = []

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # 顶部状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # API状态
        self.api_status_label = ttk.Label(status_frame, text="API状态: 就绪", foreground="green")
        self.api_status_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))

        # 任务状态
        self.task_status_label = ttk.Label(status_frame, text="当前任务: 无", foreground="blue")
        self.task_status_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100, length=200)
        self.progress_bar.grid(row=0, column=2, sticky=tk.W, padx=(0, 20))

        # 任务ID显示
        self.task_id_label = ttk.Label(status_frame, text="任务ID: 无", font=("Arial", 9))
        self.task_id_label.grid(row=0, column=3, sticky=tk.W)

        # 创建标签页容器
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 先创建日志区域（在创建标签页之前）
        log_frame = ttk.LabelFrame(main_frame, text="详细日志", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.generate_btn = ttk.Button(button_frame, text="开始生成", command=self.start_generation, width=15)
        self.generate_btn.grid(row=0, column=0, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="停止任务", command=self.stop_generation, width=15,
                                   state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))

        self.save_btn = ttk.Button(button_frame, text="保存图片", command=self.save_image, width=15, state=tk.DISABLED)
        self.save_btn.grid(row=0, column=2, padx=(0, 10))

        self.clear_btn = ttk.Button(button_frame, text="清空日志", command=self.clear_logs, width=15)
        self.clear_btn.grid(row=0, column=3)

        # 为每个模型创建标签页
        self.create_image_generation_tab()
        self.create_image_edit_tab()

        # 绑定标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # 输出缓冲的日志
        self.flush_log_buffer()

        # 切换到生成标签页
        self.notebook.select(0)

    def create_image_generation_tab(self):
        """创建图像生成标签页"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="图像生成")

        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=2)
        tab.rowconfigure(1, weight=1)

        # 左侧控制面板
        control_frame = ttk.LabelFrame(tab, text="生成参数", padding="10")
        control_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 模型选择
        ttk.Label(control_frame, text="选择模型:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.gen_model_var = tk.StringVar(value="Qwen/Qwen-Image-2512")
        model_combo = ttk.Combobox(control_frame, textvariable=self.gen_model_var,
                                   values=["Qwen/Qwen-Image-2512", "AI-ModelScope/stable-diffusion-xl-base-1.0",
                                           "AI-ModelScope/stable-diffusion-v1-5", "damo/wanx-v1"],
                                   width=30)
        model_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 提示词输入
        ttk.Label(control_frame, text="提示词 (Prompt):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.gen_prompt_text = scrolledtext.ScrolledText(control_frame, height=6, wrap=tk.WORD)
        self.gen_prompt_text.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.gen_prompt_text.insert("1.0", "A golden cat")

        # 负向提示词
        ttk.Label(control_frame, text="负向提示词 (Negative Prompt):").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        self.gen_negative_prompt_text = scrolledtext.ScrolledText(control_frame, height=4, wrap=tk.WORD)
        self.gen_negative_prompt_text.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 图片尺寸滑块
        ttk.Label(control_frame, text="图片宽度:").grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        self.gen_width_var = tk.IntVar(value=1024)
        width_scale = ttk.Scale(control_frame, from_=256, to=2048, variable=self.gen_width_var,
                                orient=tk.HORIZONTAL, length=200)
        width_scale.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.gen_width_label = ttk.Label(control_frame, text=f"当前值: {self.gen_width_var.get()}px")
        self.gen_width_label.grid(row=8, column=0, sticky=tk.W, pady=(0, 10))
        width_scale.configure(command=lambda v: self.gen_width_label.config(text=f"当前值: {int(float(v))}px"))

        ttk.Label(control_frame, text="图片高度:").grid(row=9, column=0, sticky=tk.W, pady=(0, 5))
        self.gen_height_var = tk.IntVar(value=1024)
        height_scale = ttk.Scale(control_frame, from_=256, to=2048, variable=self.gen_height_var,
                                 orient=tk.HORIZONTAL, length=200)
        height_scale.grid(row=10, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.gen_height_label = ttk.Label(control_frame, text=f"当前值: {self.gen_height_var.get()}px")
        self.gen_height_label.grid(row=11, column=0, sticky=tk.W, pady=(0, 10))
        height_scale.configure(command=lambda v: self.gen_height_label.config(text=f"当前值: {int(float(v))}px"))

        # 生成数量滑块
        ttk.Label(control_frame, text="生成数量:").grid(row=12, column=0, sticky=tk.W, pady=(0, 5))
        self.gen_num_images_var = tk.IntVar(value=1)
        num_scale = ttk.Scale(control_frame, from_=1, to=4, variable=self.gen_num_images_var,
                              orient=tk.HORIZONTAL, length=200)
        num_scale.grid(row=13, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.gen_num_label = ttk.Label(control_frame, text=f"当前值: {self.gen_num_images_var.get()}")
        self.gen_num_label.grid(row=14, column=0, sticky=tk.W, pady=(0, 10))
        num_scale.configure(command=lambda v: self.gen_num_label.config(text=f"当前值: {int(float(v))}"))

        # 右侧预览区域
        preview_frame = ttk.LabelFrame(tab, text="图片预览", padding="10")
        preview_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        # 预览图片容器
        self.gen_image_frame = ttk.Frame(preview_frame, relief=tk.SUNKEN, height=400, width=400)
        self.gen_image_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        self.gen_image_frame.grid_propagate(False)

        self.gen_image_label = ttk.Label(self.gen_image_frame, text="等待生成图片...")
        self.gen_image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 图片信息
        self.gen_info_label = ttk.Label(preview_frame, text="", font=("Arial", 9), foreground="gray")
        self.gen_info_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))

    def create_image_edit_tab(self):
        """创建图像编辑标签页"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="图像编辑")

        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)

        # 左侧控制面板
        control_frame = ttk.LabelFrame(tab, text="编辑参数", padding="10")
        control_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 模型固定为编辑模型
        ttk.Label(control_frame, text="模型:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Label(control_frame, text="Qwen/Qwen-Image-Edit-2511", foreground="blue").grid(row=1, column=0, sticky=tk.W,
                                                                                           pady=(0, 10))

        # 图片URL输入
        ttk.Label(control_frame, text="图片URL (必填):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.edit_image_url_var = tk.StringVar(value="https://modelscope.oss-cn-beijing.aliyuncs.com/Dog.png")
        self.edit_image_url_entry = ttk.Entry(control_frame, textvariable=self.edit_image_url_var, width=40)
        self.edit_image_url_entry.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 示例按钮
        ttk.Button(control_frame, text="使用示例图片", command=self.use_example_image, width=15).grid(row=4, column=0,
                                                                                                      sticky=tk.W,
                                                                                                      pady=(0, 10))

        # 编辑指令
        ttk.Label(control_frame, text="编辑指令 (Prompt):").grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        self.edit_prompt_text = scrolledtext.ScrolledText(control_frame, height=10, wrap=tk.WORD)
        self.edit_prompt_text.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.edit_prompt_text.insert("1.0", "给图中的狗戴上一个生日帽")

        # 右侧预览区域
        preview_frame = ttk.LabelFrame(tab, text="图片预览", padding="10")
        preview_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        # 原图预览
        ttk.Label(preview_frame, text="原图:").grid(row=0, column=0, sticky=tk.W)
        self.edit_source_frame = ttk.Frame(preview_frame, relief=tk.SUNKEN, height=250)
        self.edit_source_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 10))
        self.edit_source_frame.grid_propagate(False)

        self.edit_source_label = ttk.Label(self.edit_source_frame, text="未加载图片")
        self.edit_source_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 编辑后预览
        ttk.Label(preview_frame, text="编辑后:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.edit_result_frame = ttk.Frame(preview_frame, relief=tk.SUNKEN, height=250)
        self.edit_result_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        self.edit_result_frame.grid_propagate(False)

        self.edit_result_label = ttk.Label(self.edit_result_frame, text="等待编辑结果...")
        self.edit_result_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 存储变量
        self.image_edit_vars = {
            "image_url": self.edit_image_url_var,
            "prompt": self.edit_prompt_text,
            "source_label": self.edit_source_label,
            "result_label": self.edit_result_label,
            "source_image": None,
            "result_image": None
        }

        # 加载示例图片
        self.load_example_image()

    def flush_log_buffer(self):
        """输出缓冲的日志"""
        for message in self.log_buffer:
            self.log_message(message)
        self.log_buffer.clear()

    def use_example_image(self):
        """使用示例图片"""
        self.edit_image_url_var.set("https://modelscope.oss-cn-beijing.aliyuncs.com/Dog.png")
        self.load_example_image()

    def load_example_image(self):
        """加载示例图片"""
        image_url = self.edit_image_url_var.get().strip()
        if not image_url:
            return

        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))
                self.image_edit_vars["source_image"] = img
                self.display_edit_source_image()
                self.log_message(f"图片加载成功: {image_url}")
            else:
                self.log_message(f"图片加载失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_message(f"加载图片失败: {str(e)}")

    def display_edit_source_image(self):
        """显示编辑标签页的原图"""
        if self.image_edit_vars["source_image"]:
            try:
                img = self.image_edit_vars["source_image"].copy()
                # 调整大小以适应预览区域
                preview_size = (240, 240)
                img.thumbnail(preview_size, Image.Resampling.LANCZOS)

                # 转换为PhotoImage
                photo = ImageTk.PhotoImage(img)
                self.image_edit_vars["source_label"].config(image=photo, text="")
                self.image_edit_vars["source_label"].image = photo
            except Exception as e:
                self.log_message(f"显示原图时出错: {str(e)}")

    def on_tab_changed(self, event):
        """标签页切换事件"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            self.current_model = "generation"
            self.log_message("切换到图像生成标签页")
        elif current_tab == 1:
            self.current_model = "edit"
            self.log_message("切换到图像编辑标签页")
            # 切换到编辑标签页时自动加载URL图片
            self.load_example_image()

    def log_message(self, message):
        """在日志区域显示消息"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        log_entry = f"[{timestamp}] {message}\n"

        # 检查日志组件是否已创建
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        else:
            # 如果日志组件还未创建，先缓冲消息
            self.log_buffer.append(message)

    def update_status(self, message, status_type="info"):
        """更新状态"""
        colors = {
            "info": "blue",
            "success": "green",
            "error": "red",
            "warning": "orange"
        }
        self.task_status_label.config(text=f"当前任务: {message}", foreground=colors.get(status_type, "blue"))
        self.root.update_idletasks()

    def update_progress(self, value, message=None):
        """更新进度条"""
        self.progress_var.set(value)
        if message:
            self.update_status(message)
        self.root.update_idletasks()

    def clear_logs(self):
        """清空日志"""
        self.log_text.delete("1.0", tk.END)
        self.log_message("日志已清空")

    def start_generation(self):
        """开始生成图像"""
        if self.is_running:
            messagebox.showwarning("警告", "已有任务正在运行")
            return

        # 根据当前标签页获取参数
        if self.current_model == "generation":
            self.start_image_generation()
        elif self.current_model == "edit":
            self.start_image_edit()

    def start_image_generation(self):
        """开始图像生成任务"""
        prompt = self.gen_prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("警告", "请输入提示词")
            return

        # 设置按钮状态
        self.generate_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)

        # 启动生成线程
        self.is_running = True
        thread = threading.Thread(target=self.generate_image_thread, daemon=True)
        thread.start()

    def start_image_edit(self):
        """开始图像编辑任务"""
        prompt = self.edit_prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("警告", "请输入编辑指令")
            return

        image_url = self.edit_image_url_var.get().strip()
        if not image_url:
            messagebox.showwarning("警告", "请输入图片URL")
            return

        # 设置按钮状态
        self.generate_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)

        # 启动编辑线程
        self.is_running = True
        thread = threading.Thread(target=self.edit_image_thread, daemon=True)
        thread.start()

    def generate_image_thread(self):
        """图像生成线程"""
        try:
            self.log_message("开始图像生成...")
            self.update_progress(10, "准备生成参数...")

            # 获取参数
            model = self.gen_model_var.get()
            prompt = self.gen_prompt_text.get("1.0", tk.END).strip()
            negative_prompt = self.gen_negative_prompt_text.get("1.0", tk.END).strip()
            width = self.gen_width_var.get()
            height = self.gen_height_var.get()
            num_images = self.gen_num_images_var.get()

            # 准备请求数据
            request_data = {
                "model": model,
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_images_per_prompt": num_images
            }

            if negative_prompt:
                request_data["negative_prompt"] = negative_prompt

            self.log_message(f"使用模型: {model}")
            self.log_message(f"图片尺寸: {width}x{height}")
            self.update_progress(20, "发送生成请求...")

            # 发送请求
            response = self.send_api_request(request_data)
            if not response:
                return

            self.current_task_id = response["task_id"]
            self.root.after(0, lambda: self.task_id_label.config(text=f"任务ID: {self.current_task_id}"))
            self.log_message(f"任务创建成功，ID: {self.current_task_id}")
            self.update_progress(30, "任务已提交，等待处理...")

            # 启动状态检查
            self.check_task_status()

        except Exception as e:
            self.log_message(f"生成请求失败: {str(e)}")
            self.root.after(0, lambda: self.update_status(f"生成失败: {str(e)}", "error"))
            self.root.after(0, self.reset_buttons)
            self.is_running = False

    def edit_image_thread(self):
        """图像编辑线程"""
        try:
            self.log_message("开始图像编辑...")
            self.update_progress(10, "准备编辑参数...")

            # 获取参数
            prompt = self.edit_prompt_text.get("1.0", tk.END).strip()
            image_url = self.edit_image_url_var.get().strip()

            self.log_message(f"编辑指令: {prompt}")
            self.log_message(f"图片URL: {image_url}")
            self.update_progress(20, "发送编辑请求...")

            # 准备请求数据 - 严格按照原始示例代码的格式
            request_data = {
                "model": "Qwen/Qwen-Image-Edit-2511",
                "prompt": prompt,
                "image_url": [image_url]  # 关键：必须是数组格式
            }

            self.log_message("发送图像编辑请求...")

            # 发送请求
            response = self.send_api_request(request_data)
            if not response:
                return

            self.current_task_id = response["task_id"]
            self.root.after(0, lambda: self.task_id_label.config(text=f"任务ID: {self.current_task_id}"))
            self.log_message(f"编辑任务创建成功，ID: {self.current_task_id}")
            self.update_progress(30, "编辑任务已提交，等待处理...")

            # 启动状态检查
            self.check_task_status()

        except Exception as e:
            self.log_message(f"编辑请求失败: {str(e)}")
            self.root.after(0, lambda: self.update_status(f"编辑失败: {str(e)}", "error"))
            self.root.after(0, self.reset_buttons)
            self.is_running = False

    def send_api_request(self, request_data):
        """发送API请求"""
        try:
            # 调试：记录发送的请求数据
            debug_data = {k: v for k, v in request_data.items()}
            # 如果包含图片URL，只显示URL的部分信息
            if "image_url" in debug_data:
                debug_data["image_url"] = [url[:50] + "..." if len(url) > 50 else url for url in
                                           debug_data["image_url"]]

            self.log_message(f"发送请求数据: {json.dumps(debug_data, ensure_ascii=False)[:200]}...")

            response = requests.post(
                f"{self.base_url}v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-ModelScope-Async-Mode": "true"
                },
                data=json.dumps(request_data, ensure_ascii=False).encode('utf-8')
            )

            # 检查响应状态
            if response.status_code != 200:
                self.log_message(f"API返回错误: {response.status_code}")
                self.log_message(f"错误详情: {response.text}")
                response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            self.log_message(f"HTTP请求失败: {str(e)}")
            if hasattr(e.response, 'text'):
                self.log_message(f"详细错误信息: {e.response.text}")
            self.root.after(0, lambda: self.update_status(f"HTTP请求失败", "error"))
            return None
        except Exception as e:
            self.log_message(f"API请求失败: {str(e)}")
            self.root.after(0, lambda: self.update_status(f"请求异常: {str(e)}", "error"))
            return None

    def check_task_status(self):
        """检查任务状态"""
        if not self.is_running or not self.current_task_id:
            return

        def check():
            try:
                while self.is_running and self.current_task_id:
                    result = requests.get(
                        f"{self.base_url}v1/tasks/{self.current_task_id}",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                            "X-ModelScope-Task-Type": "image_generation"
                        }
                    )

                    result.raise_for_status()
                    data = result.json()

                    status = data.get("task_status", "UNKNOWN")
                    self.log_message(f"任务状态: {status}")

                    if status == "SUCCEED":
                        self.handle_success(data)
                        break
                    elif status == "FAILED":
                        self.handle_failure(data)
                        break
                    elif status == "RUNNING":
                        progress = data.get("progress", 0)
                        self.root.after(0,
                                        lambda: self.update_progress(30 + progress * 0.6, f"处理中... ({progress}%)"))
                    elif status == "PENDING":
                        self.root.after(0, lambda: self.update_progress(30, "任务排队中..."))

                    time.sleep(5)

            except Exception as e:
                self.log_message(f"检查状态时出错: {str(e)}")
                self.root.after(0, lambda: self.update_status(f"状态检查失败", "error"))
                self.root.after(0, self.reset_buttons)
                self.is_running = False

        # 在新线程中检查状态
        thread = threading.Thread(target=check, daemon=True)
        thread.start()

    def handle_success(self, data):
        """处理成功结果"""
        self.root.after(0, lambda: self.update_progress(100, "任务完成!"))

        # 获取图片URL
        output_images = data.get("output_images", [])
        if output_images:
            image_url = output_images[0]
            self.log_message(f"获取图片URL: {image_url}")

            # 下载并显示图片
            self.root.after(0, lambda: self.update_status("正在下载图片..."))
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                img_data = response.content

                # 根据当前标签页显示图片
                if self.current_model == "generation":
                    self.display_generated_image(img_data)
                elif self.current_model == "edit":
                    self.display_edited_image(img_data)

                self.root.after(0, lambda: self.update_status("任务完成!", "success"))

            except Exception as e:
                self.log_message(f"下载图片失败: {str(e)}")
                self.root.after(0, lambda: self.update_status("下载图片失败", "error"))

        self.root.after(0, self.reset_buttons)
        self.is_running = False

    def handle_failure(self, data):
        """处理失败结果"""
        error_msg = data.get("error_message", "未知错误")
        self.log_message(f"任务失败: {error_msg}")
        self.root.after(0, lambda: self.update_status(f"任务失败: {error_msg}", "error"))
        self.root.after(0, self.reset_buttons)
        self.is_running = False

    def display_generated_image(self, img_data):
        """显示生成的图片"""
        try:
            img = Image.open(io.BytesIO(img_data))
            # 调整大小以适应预览区域
            img_preview = img.copy()
            img_preview.thumbnail((380, 380), Image.Resampling.LANCZOS)

            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(img_preview)
            self.gen_image_label.config(image=photo, text="")
            self.gen_image_label.image = photo

            # 更新信息标签
            width, height = img.size
            self.gen_info_label.config(text=f"尺寸: {width}x{height} | 格式: {img.format}")

            # 保存图片引用
            self.current_image_pil = img
            self.save_btn.config(state=tk.NORMAL)

            self.log_message("图片加载完成")

        except Exception as e:
            self.log_message(f"显示图片时出错: {str(e)}")

    def display_edited_image(self, img_data):
        """显示编辑后的图片"""
        try:
            img = Image.open(io.BytesIO(img_data))
            # 调整大小以适应预览区域
            img_preview = img.copy()
            img_preview.thumbnail((240, 240), Image.Resampling.LANCZOS)

            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(img_preview)
            self.image_edit_vars["result_label"].config(image=photo, text="")
            self.image_edit_vars["result_label"].image = photo

            # 保存图片引用
            self.current_image_pil = img
            self.image_edit_vars["result_image"] = img
            self.save_btn.config(state=tk.NORMAL)

            self.log_message("编辑结果加载完成")

        except Exception as e:
            self.log_message(f"显示编辑结果时出错: {str(e)}")

    def save_image(self):
        """保存图片到文件"""
        if not hasattr(self, 'current_image_pil') or not self.current_image_pil:
            messagebox.showwarning("警告", "没有图片可保存")
            return

        try:
            # 获取保存路径
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG文件", "*.png"),
                    ("JPEG文件", "*.jpg *.jpeg"),
                    ("所有文件", "*.*")
                ],
                initialfile=f"{self.current_model}_{int(time.time())}.png"
            )

            if filename:
                # 保存图片
                self.current_image_pil.save(filename)
                self.log_message(f"图片已保存到: {filename}")
                messagebox.showinfo("保存成功", f"图片已保存到:\n{filename}")
        except Exception as e:
            messagebox.showerror("保存错误", f"保存图片时出错: {str(e)}")

    def reset_buttons(self):
        """重置按钮状态"""
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def stop_generation(self):
        """停止生成任务"""
        self.is_running = False
        self.update_status("正在停止任务...", "warning")
        self.log_message("用户请求停止任务")
        self.reset_buttons()

    def on_closing(self):
        """关闭窗口时的处理"""
        self.is_running = False
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ModelScopeImageGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()