import os
import wx
import wx.lib.scrolledpanel as scrolled
import threading
from concurrent.futures import ThreadPoolExecutor
import json
import requests
import time
import sqlite3
from PIL import Image as PILImage
from io import BytesIO
import base64

class EntityCard(wx.Panel):
    """
    Entity card class, used to display information of a single entity
    """

    def __init__(self, parent, entity_data, api_config, project_path):
        """
        Initialize the entity card
        
        Args:
            parent: Parent component
            entity_data (dict): Entity data, including name and perspective prompts
            api_config (dict): API configuration
            project_path (str): Project path
        """
        super().__init__(parent, style=wx.BORDER_SUNKEN)
        self.entity_data = entity_data
        self.api_config = api_config
        self.project_path = project_path
        self.image_data = {}  # 存储生成的图片
        
        # 创建存储控件引用的字典
        self.style_entries = {}
        self.ratio_vars = {}
        self.image_panels = {}
        
        # 创建图片缓存以防止垃圾回收
        self.bitmap_cache = {}
        
        # 创建线程池用于图像生成
        self.executor = ThreadPoolExecutor(max_workers=3)  # 最多同时处理3个图像生成任务
        
        # 存储线程池任务
        self.futures = []  # 添加缺失的futures属性
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置实体卡片界面"""
        # 设置卡片背景色
        self.SetBackgroundColour('#ffffff')
        
        # 主布局
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 实体名称标签
        name_text = f"实体: {self.entity_data['name']}"
        name_label = wx.StaticText(self, label=name_text)
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        name_label.SetFont(font)
        name_label.SetForegroundColour('#212529')
        name_label.SetBackgroundColour('#ffffff')
        main_sizer.Add(name_label, 0, wx.ALL | wx.EXPAND, 10)
        
        # 创建主框架，左右分布提示和图片
        main_frame = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左侧提示区域
        prompt_panel = wx.Panel(self)
        prompt_panel.SetBackgroundColour('#ffffff')
        prompt_panel.SetMinSize((600, -1))
        prompt_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 右侧图片显示区域
        image_area_panel = wx.Panel(self)
        image_area_panel.SetBackgroundColour('#f8f9fa')
        image_area_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 为每个视角提示创建控件
        for idx, (perspective, prompt) in enumerate(self.entity_data.get('prompts', {}).items()):
            # 创建此视角的主框架
            perspective_main_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # 上排：提示标签、复制按钮、生成按钮
            top_row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            # 提示标签
            prompt_label = wx.StaticText(prompt_panel, label=f"{perspective}: {prompt}")
            prompt_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            prompt_label.SetForegroundColour('#495057')
            prompt_label.Wrap(450)  # 自动换行
            top_row_sizer.Add(prompt_label, 1, wx.ALIGN_LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
            
            # 复制按钮
            copy_btn = wx.Button(prompt_panel, label="复制", size=(40, -1))
            copy_btn.SetBackgroundColour('#007bff')
            copy_btn.SetForegroundColour('white')
            copy_btn.Bind(wx.EVT_BUTTON, lambda evt, p=prompt: self.copy_prompt(p))
            top_row_sizer.Add(copy_btn, 0, wx.LEFT | wx.RIGHT, 5)
            
            # 生成按钮 - 现在所有视角都可以生成，使用统一的绿色按钮
            generate_btn = wx.Button(prompt_panel, label="生成", size=(40, -1))
            generate_btn.SetBackgroundColour('#28a745')
            generate_btn.SetForegroundColour('white')
            generate_btn.Bind(wx.EVT_BUTTON, lambda evt, p=prompt, ps=perspective: self.generate_image(p, ps))
            top_row_sizer.Add(generate_btn, 0, wx.LEFT, 5)
            
            perspective_main_sizer.Add(top_row_sizer, 0, wx.EXPAND | wx.ALL, 5)
            
            # 下排：样式和比例控制
            bottom_row_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # 样式要求输入区域
            style_sizer = wx.BoxSizer(wx.HORIZONTAL)
            style_label = wx.StaticText(prompt_panel, label="Style requirement:")
            style_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            style_label.SetForegroundColour('#6c757d')
            style_sizer.Add(style_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
            
            style_entry = wx.TextCtrl(prompt_panel, size=(200, -1))
            style_sizer.Add(style_entry, 1, wx.EXPAND)
            
            # 存储样式输入框引用
            self.style_entries[perspective] = style_entry
            
            bottom_row_sizer.Add(style_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)
            
            # 图片比例选择区域
            ratio_sizer = wx.BoxSizer(wx.HORIZONTAL)
            ratio_label = wx.StaticText(prompt_panel, label="Image ratio:")
            ratio_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            ratio_label.SetForegroundColour('#6c757d')
            ratio_sizer.Add(ratio_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
            
            # 图片比例选项
            ratios = ["1:1", "4:3", "3:2", "16:9", "9:16"]
            ratio_choice = wx.Choice(prompt_panel, choices=ratios)
            ratio_choice.SetSelection(0)  # 默认选择第一项
            
            # 存储比例变量引用
            self.ratio_vars[perspective] = ratio_choice
            
            ratio_sizer.Add(ratio_choice, 0, wx.EXPAND)
            
            # 模型选择下拉菜单
            model_label = wx.StaticText(prompt_panel, label="Model:")
            model_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            model_label.SetForegroundColour('#6c757d')
            ratio_sizer.Add(model_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
            
            # 模型选项
            models = ["Auto", "Text-to-Image", "Image-to-Image", "Image-to-Image-Plus", "Text-to-Image-Plus"]
            model_choice = wx.Choice(prompt_panel, choices=models)
            model_choice.SetSelection(0)  # 默认选择Auto
            
            # 存储模型变量引用
            if not hasattr(self, 'model_vars'):
                self.model_vars = {}
            self.model_vars[perspective] = model_choice
            
            ratio_sizer.Add(model_choice, 0, wx.EXPAND)
            bottom_row_sizer.Add(ratio_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
            
            perspective_main_sizer.Add(bottom_row_sizer, 0, wx.EXPAND)
            
            # 图片显示区域
            image_frame = wx.Panel(image_area_panel, style=wx.BORDER_SUNKEN)
            image_frame.SetBackgroundColour('#f8f9fa')
            
            image_frame_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # 图片标题
            image_header = wx.BoxSizer(wx.HORIZONTAL)
            image_label = wx.StaticText(image_frame, label=f"{perspective} Image Preview:", 
                                       style=wx.ALIGN_LEFT)
            font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            image_label.SetFont(font)
            image_label.SetForegroundColour('#495057')
            image_label.SetBackgroundColour('#f8f9fa')
            image_header.Add(image_label, 1, wx.LEFT | wx.TOP | wx.BOTTOM, 5)
            
            # 添加功能按钮
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            # 下载按钮
            download_btn = wx.Button(image_frame, label="下载", size=(60, -1))
            download_btn.SetBackgroundColour('#007bff')
            download_btn.SetForegroundColour('white')
            download_btn.Bind(wx.EVT_BUTTON, lambda evt, ps=perspective: self.download_image(ps))
            button_sizer.Add(download_btn, 0, wx.LEFT | wx.RIGHT, 2)
            
            # 全屏查看按钮
            fullscreen_btn = wx.Button(image_frame, label="全屏", size=(60, -1))
            fullscreen_btn.SetBackgroundColour('#28a745')
            fullscreen_btn.SetForegroundColour('white')
            fullscreen_btn.Bind(wx.EVT_BUTTON, lambda evt, ps=perspective: self.fullscreen_view(ps))
            button_sizer.Add(fullscreen_btn, 0, wx.LEFT | wx.RIGHT, 2)
            
            # 刷新按钮
            refresh_btn = wx.Button(image_frame, label="刷新", size=(60, -1))
            refresh_btn.SetBackgroundColour('#6c757d')
            refresh_btn.SetForegroundColour('white')
            refresh_btn.Bind(wx.EVT_BUTTON, lambda evt, ps=perspective: self.redraw_image(ps))
            button_sizer.Add(refresh_btn, 0, wx.LEFT | wx.RIGHT, 2)
            
            # 保存按钮
            save_btn = wx.Button(image_frame, label="保存", size=(60, -1))
            save_btn.SetBackgroundColour('#ffc107')
            save_btn.SetForegroundColour('#212529')
            save_btn.Bind(wx.EVT_BUTTON, lambda evt, ps=perspective: self.save_image_to_db(ps))
            button_sizer.Add(save_btn, 0, wx.LEFT | wx.RIGHT, 2)
            
            image_header.Add(button_sizer, 0, wx.LEFT, 5)
            image_frame_sizer.Add(image_header, 0, wx.EXPAND)
            
            # 创建用于显示图片的面板
            canvas_panel = wx.Panel(image_frame, size=(500, 250))
            canvas_panel.SetBackgroundColour('#ffffff')
            canvas_panel.SetMinSize((500, 250))
            image_frame_sizer.Add(canvas_panel, 0, wx.ALL | wx.ALIGN_CENTER, 5)
            
            # 存储画布引用以便后续更新
            self.image_panels[perspective] = canvas_panel
            # 存储图片数据
            if not hasattr(self, 'image_data_store'):
                self.image_data_store = {}
            self.image_data_store[perspective] = None
            
            # 为面板绑定更多事件以处理滚动和显示问题
            canvas_panel.Bind(wx.EVT_SHOW, lambda evt, p=perspective: self.ensure_image_displayed(p))
            canvas_panel.Bind(wx.EVT_SIZE, lambda evt, p=perspective: self.ensure_image_displayed(p))

            image_frame.SetSizer(image_frame_sizer)
            image_area_sizer.Add(image_frame, 0, wx.EXPAND | wx.ALL, 5)
            
            prompt_sizer.Add(perspective_main_sizer, 0, wx.EXPAND)
        
        prompt_panel.SetSizer(prompt_sizer)
        image_area_panel.SetSizer(image_area_sizer)
        
        # 添加左右面板到主框架
        main_frame.Add(prompt_panel, 1, wx.EXPAND | wx.RIGHT, 10)
        main_frame.Add(image_area_panel, 1, wx.EXPAND | wx.LEFT, 5)
        
        main_sizer.Add(main_frame, 1, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
    
    def generate_image(self, prompt, perspective):
        """Generate image"""
        canvas_panel = self.image_panels[perspective]  # 获取画布面板

        # 获取UI控件的最新值
        if perspective in self.style_entries:
            style_requirement = self.style_entries[perspective].GetValue().strip()
            if style_requirement:
                prompt = f"{prompt}, Style requirement: {style_requirement}"

        # 使用线程池提交任务
        future = self.executor.submit(self._generate_image_thread, prompt, perspective, canvas_panel)
        # 将Future对象存储起来以便管理
        self.futures.append(future)
    
    def _generate_image_thread(self, prompt, perspective, canvas_panel):
        """Generate image in background thread"""
        try:
            # 显示加载状态
            wx.CallAfter(self.show_loading_status, canvas_panel)
                
            # 调用API生成图片
            response = self.call_image_generation_api(prompt, canvas_panel)
                
            if response:
                # 在Canvas上显示图片数据
                wx.CallAfter(self.display_image_on_canvas, response, perspective)
            else:
                wx.CallAfter(self.show_generation_failed, canvas_panel)
                    
        except Exception as e:
            wx.CallAfter(self.show_error, canvas_panel, str(e))
    
    def show_loading_status(self, canvas_panel):
        """在画布上显示加载状态"""
        dc = wx.ClientDC(canvas_panel)
        dc.SetBackground(wx.Brush('#ffffff'))
        dc.Clear()
        dc.SetTextForeground('gray')
        dc.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        dc.DrawText("Generating...", 200, 100)
    
    def show_generation_failed(self, canvas_panel):
        """在画布上显示生成失败"""
        dc = wx.ClientDC(canvas_panel)
        dc.SetBackground(wx.Brush('#ffffff'))
        dc.Clear()
        dc.SetTextForeground('red')
        dc.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        dc.DrawText("Generation failed", 200, 100)
    
    def show_error(self, canvas_panel, error_msg):
        """在画布上显示错误"""
        dc = wx.ClientDC(canvas_panel)
        dc.SetBackground(wx.Brush('#ffffff'))
        dc.Clear()
        dc.SetTextForeground('red')
        dc.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        dc.DrawText(f"Error: {error_msg}", 200, 100)
    
    def call_image_generation_api(self, prompt, canvas_panel=None):
        """Call image generation API - Using ModelScope API with manual model selection"""
        try:
            # 获取当前视角比例设置
            perspective = None
            for key, canvas_ref in self.image_panels.items():
                if canvas_ref == canvas_panel:
                    perspective = key
                    break
            
            import requests
            import time
            import json
            from PIL import Image
            from io import BytesIO
            import base64
            import tempfile
            import os

            base_url = 'https://api-inference.modelscope.cn/'
            api_key = "ms-bfd13a90-db3b-433a-9baa-632cc2e9bbac"  # ModelScope Token

            common_headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # Map aspect ratio to appropriate dimensions for ModelScope
            size_mapping = {
                '1:1': '1024x1024',
                '4:3': '1024x768',
                '3:2': '1024x682',
                '16:9': '1024x576',
                '9:16': '576x1024'
            }
            
            # For DashScope, use * instead of x
            dashscope_size_mapping = {
                '1:1': '1024*1024',
                '4:3': '1024*768',
                '3:2': '1024*682',
                '16:9': '1024*576',
                '9:16': '576*1024'
            }
            
            # 获取当前视角图片比例设置
            size_param = '1024x1024'  # Default ratio for ModelScope
            dashscope_size_param = '1024*1024'  # Default ratio for DashScope
            if perspective and perspective in self.ratio_vars:
                choice_ctrl = self.ratio_vars[perspective]
                ratio_idx = choice_ctrl.GetSelection()
                if ratio_idx != wx.NOT_FOUND:
                    ratio = choice_ctrl.GetString(ratio_idx)
                    size_param = size_mapping.get(ratio, '1024x1024')
                    dashscope_size_param = dashscope_size_mapping.get(ratio, '1024*1024')

            # Get the selected model from dropdown
            selected_model = "Auto"  # Default
            if (hasattr(self, 'model_vars') and 
                perspective in self.model_vars):
                model_choice = self.model_vars[perspective]
                model_idx = model_choice.GetSelection()
                if model_idx != wx.NOT_FOUND:
                    selected_model = model_choice.GetString(model_idx)

            # Determine which model to use based on user selection
            if selected_model == "Text-to-Image":
                # Use text-to-image model
                model_name = "Qwen/Qwen-Image-2512"
                
                # Make the API call
                response = requests.post(
                    f"{base_url}v1/images/generations",
                    headers={**common_headers, "X-ModelScope-Async-Mode": "true"},
                    data=json.dumps({
                        "model": model_name,  # ModelScope Model-Id
                        "prompt": prompt,
                        "size": size_param  # Add size parameter
                    }, ensure_ascii=False).encode('utf-8')
                )
            elif selected_model == "Text-to-Image-Plus":
                # Use DashScope text-to-image-plus model
                import json
                import os
                import dashscope
                from dashscope import MultiModalConversation
                
                dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
                
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ]
                
                # Use the provided API key
                api_key = "sk-912c798157c74fa5bb664325fc47f6eb"
                
                response = MultiModalConversation.call(
                    api_key=api_key,
                    model="qwen-image-plus-2026-01-09",
                    messages=messages,
                    result_format='message',
                    stream=False,
                    watermark=False,
                    prompt_extend=True,
                    negative_prompt='',
                    size=dashscope_size_param
                )
                
                if response.status_code == 200:
                    # Extract image data from response
                    image_url = response.output.choices[0].message.content[0]['image']
                    image_response = requests.get(image_url)
                    return image_response.content
                else:
                    print(f"DashScope API Error - Status: {response.status_code}, Message: {response.message}")
                    return None
            elif selected_model == "Image-to-Image-Plus":
                # Use DashScope qwen-image-edit-plus model for advanced image editing
                import json
                import os
                import dashscope
                from dashscope import MultiModalConversation
                
                dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
                
                # First, check if there's a reference image
                entity_name = self.entity_data['name']
                
                # Check for various possible front view names
                ref_exists = False
                ref_image_data = None
                
                # Look for any image that can serve as reference
                possible_ref_names = ['front view', 'front', '正面', '正面视角', 'Front View', 'Front', '正面视图', 'front_view', 'front-view']
                
                for ref_perspective in possible_ref_names:
                    ref_cache_key = f"{entity_name}_{ref_perspective}".replace(' ', '_').replace('-', '_')
                    if (hasattr(self, 'image_data_store') and 
                        ref_cache_key in self.image_data_store and 
                        self.image_data_store[ref_cache_key] is not None):
                        ref_exists = True
                        ref_image_data = self.image_data_store[ref_cache_key]
                        break
                
                # If still not found, try any key that contains 'front' or '正面'
                if not ref_exists:
                    for key in self.image_data_store.keys():
                        if (('front' in key.lower() or '正面' in key) and 
                            entity_name in key and 
                            self.image_data_store[key] is not None):
                            ref_exists = True
                            ref_image_data = self.image_data_store[key]
                            break
                
                if not ref_exists:
                    # If no reference image exists, fall back to text-to-image
                    import json
                    import requests
                    
                    model_name = "Qwen/Qwen-Image-2512"
                    response = requests.post(
                        f"{base_url}v1/images/generations",
                        headers={**common_headers, "X-ModelScope-Async-Mode": "true"},
                        data=json.dumps({
                            "model": model_name,  # ModelScope Model-Id
                            "prompt": prompt,
                            "size": size_param  # Add size parameter
                        }, ensure_ascii=False).encode('utf-8')
                    )
                else:
                    # Use DashScope advanced image editing model
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"image": f"data:image/png;base64,{base64.b64encode(ref_image_data).decode('utf-8')}"},
                                {"text": prompt}
                            ]
                        }
                    ]
                    
                    # Use the provided API key
                    api_key = "sk-912c798157c74fa5bb664325fc47f6eb"
                    
                    response = MultiModalConversation.call(
                        api_key=api_key,
                        model="qwen-image-edit-plus",
                        messages=messages,
                        result_format='message',
                        stream=False,
                        n=1,
                        watermark=False,
                        negative_prompt="",
                        size=dashscope_size_param
                    )
                    
                    if response.status_code == 200:
                        # Extract image data from response
                        image_url = response.output.choices[0].message.content[0]['image']
                        image_response = requests.get(image_url)
                        return image_response.content
                    else:
                        print(f"DashScope API Error - Status: {response.status_code}, Message: {response.message}")
                        return None
            elif selected_model == "Image-to-Image":
                # Use image-to-image model
                model_name = "Qwen/Qwen-Image-Edit-2511"
                
                # First, check if there's a reference image
                entity_name = self.entity_data['name']
                
                # Check for various possible front view names
                ref_exists = False
                ref_image_data = None
                
                # Look for any image that can serve as reference
                possible_ref_names = ['front view', 'front', '正面', '正面视角', 'Front View', 'Front', '正面视图', 'front_view', 'front-view']
                
                for ref_perspective in possible_ref_names:
                    ref_cache_key = f"{entity_name}_{ref_perspective}".replace(' ', '_').replace('-', '_')
                    if (hasattr(self, 'image_data_store') and 
                        ref_cache_key in self.image_data_store and 
                        self.image_data_store[ref_cache_key] is not None):
                        ref_exists = True
                        ref_image_data = self.image_data_store[ref_cache_key]
                        break
                
                # If still not found, try any key that contains 'front' or '正面'
                if not ref_exists:
                    for key in self.image_data_store.keys():
                        if (('front' in key.lower() or '正面' in key) and 
                            entity_name in key and 
                            self.image_data_store[key] is not None):
                            ref_exists = True
                            ref_image_data = self.image_data_store[key]
                            break
                
                if not ref_exists:
                    # If no reference image exists, fall back to text-to-image
                    model_name = "Qwen/Qwen-Image-2512"
                    response = requests.post(
                        f"{base_url}v1/images/generations",
                        headers={**common_headers, "X-ModelScope-Async-Mode": "true"},
                        data=json.dumps({
                            "model": model_name,  # ModelScope Model-Id
                            "prompt": prompt,
                            "size": size_param  # Add size parameter
                        }, ensure_ascii=False).encode('utf-8')
                    )
                else:
                    # Use image-to-image model with reference image
                    # If upload failed, fall back to base64 encoding
                    image_base64 = base64.b64encode(ref_image_data).decode('utf-8')
                    
                    # Make the API call with image-to-image model
                    response = requests.post(
                        f"{base_url}v1/images/generations",
                        headers={**common_headers, "X-ModelScope-Async-Mode": "true"},
                        data=json.dumps({
                            "model": model_name,  # ModelScope Model-Id
                            "prompt": prompt,
                            "image_url": [f"data:image/png;base64,{image_base64}"],  # Use base64 encoded image data as URL
                            "size": size_param
                        }, ensure_ascii=False).encode('utf-8')
                    )
            else:  # Auto or default
                # Auto-select based on perspective (front view: text-to-image, others: image-to-image if reference exists)
                if any(keyword in perspective.lower() for keyword in ['front', '正面']):
                    # Use text-to-image model for front view
                    model_name = "Qwen/Qwen-Image-2512"
                    
                    # Make the API call
                    response = requests.post(
                        f"{base_url}v1/images/generations",
                        headers={**common_headers, "X-ModelScope-Async-Mode": "true"},
                        data=json.dumps({
                            "model": model_name,  # ModelScope Model-Id
                            "prompt": prompt,
                            "size": size_param  # Add size parameter
                        }, ensure_ascii=False).encode('utf-8')
                    )
                else:
                    # Use image-to-image model for other perspectives if reference exists
                    entity_name = self.entity_data['name']
                    
                    # Check for various possible front view names
                    front_exists = False
                    front_image_data = None
                    
                    # Look for front view images with different naming conventions
                    possible_front_names = ['front view', 'front', '正面', '正面视角', 'Front View', 'Front', '正面视图', 'front_view', 'front-view']
                    
                    for front_perspective in possible_front_names:
                        front_cache_key = f"{entity_name}_{front_perspective}".replace(' ', '_').replace('-', '_')
                        if (hasattr(self, 'image_data_store') and 
                            front_cache_key in self.image_data_store and 
                            self.image_data_store[front_cache_key] is not None):
                            front_exists = True
                            front_image_data = self.image_data_store[front_cache_key]
                            break
                    
                    # If still not found, try any key that contains 'front' or '正面'
                    if not front_exists:
                        for key in self.image_data_store.keys():
                            if (('front' in key.lower() or '正面' in key) and 
                                entity_name in key and 
                                self.image_data_store[key] is not None):
                                front_exists = True
                                front_image_data = self.image_data_store[key]
                                break
                    
                    if not front_exists:
                        # If front view doesn't exist, use text-to-image model as fallback
                        model_name = "Qwen/Qwen-Image-2512"
                        response = requests.post(
                            f"{base_url}v1/images/generations",
                            headers={**common_headers, "X-ModelScope-Async-Mode": "true"},
                            data=json.dumps({
                                "model": model_name,  # ModelScope Model-Id
                                "prompt": prompt,
                                "size": size_param  # Add size parameter
                            }, ensure_ascii=False).encode('utf-8')
                        )
                    else:
                        # Use image-to-image model with front view as base
                        # If upload failed, fall back to base64 encoding
                        image_base64 = base64.b64encode(front_image_data).decode('utf-8')
                        
                        # Make the API call with image-to-image model
                        response = requests.post(
                            f"{base_url}v1/images/generations",
                            headers={**common_headers, "X-ModelScope-Async-Mode": "true"},
                            data=json.dumps({
                                "model": "Qwen/Qwen-Image-Edit-2511",  # ModelScope Model-Id
                                "prompt": prompt,
                                "image_url": [f"data:image/png;base64,{image_base64}"],  # Use base64 encoded image data as URL
                                "size": size_param
                            }, ensure_ascii=False).encode('utf-8')
                        )

            response.raise_for_status()
            task_id = response.json()["task_id"]

            # Poll for the result
            while True:
                result = requests.get(
                    f"{base_url}v1/tasks/{task_id}",
                    headers={**common_headers, "X-ModelScope-Task-Type": "image_generation"},
                )
                result.raise_for_status()
                data = result.json()

                if data["task_status"] == "SUCCEED":
                    image_response = requests.get(data["output_images"][0])
                    return image_response.content
                elif data["task_status"] == "FAILED":
                    print("Image Generation Failed.")
                    return None

                time.sleep(5)  # Wait 5 seconds before polling again
                
        except Exception as e:
            print(f"API call exception: {str(e)}")
            return None



    def display_image_on_canvas(self, image_data, perspective):
        """Display picture on Canvas - 修复版本 with auto-save and persistent rendering"""
        try:
            # 获取当前卡片的唯一标识（使用实体名称）
            entity_name = self.entity_data['name']
            canvas_panel = self.image_panels[perspective]
            
            # 检查面板是否还存在
            if not canvas_panel or not canvas_panel.IsShownOnScreen():
                return
            
            # 创建唯一的临时文件名（包含实体名称和视角）
            temp_file = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                f'temp_image_{entity_name}_{perspective}.png'.replace(' ', '_').replace(':', '')
            )
            
            # 将图片数据保存到临时文件
            with open(temp_file, 'wb') as f:
                f.write(image_data)
            
            # 从文件加载图片
            pil_image = PILImage.open(temp_file)
            
            # 转换为wxPython可以使用的格式
            width, height = pil_image.size
            image_buffer = pil_image.tobytes()
            wx_image = wx.Image(width, height)
            wx_image.SetData(image_buffer)
            
            # 缩放到适合画布的大小
            panel_width, panel_height = canvas_panel.GetSize()
            img_width, img_height = wx_image.GetSize()
            
            # 计算缩放比例，保持宽高比
            scale = min(panel_width / img_width, panel_height / img_height, 1.0)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # 调整图片大小
            wx_image = wx_image.Scale(new_width, new_height, quality=wx.IMAGE_QUALITY_HIGH)
            
            # 转换为位图
            bitmap = wx.Bitmap(wx_image)
            
            # 使用更具体的存储键，避免跨卡片冲突
            cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
            
            # 保存位图引用到缓存以防止垃圾回收
            self.bitmap_cache[cache_key] = bitmap
            
            # 在画布上绘制图片
            dc = wx.ClientDC(canvas_panel)
            dc.SetBackground(wx.Brush('#ffffff'))
            dc.Clear()
            
            # 居中绘制图片
            x_pos = (panel_width - new_width) // 2
            y_pos = (panel_height - new_height) // 2
            dc.DrawBitmap(bitmap, x_pos, y_pos, True)
            
            # 存储图片数据供后续使用
            self.image_data_store[cache_key] = image_data
            
            # Auto-save the image to the project's images folder
            self.auto_save_image(image_data, entity_name, perspective)
            
            # 绑定重绘事件，确保在窗口大小改变或滚动时图片保持显示
            canvas_panel.Bind(wx.EVT_PAINT, lambda evt, p=perspective: self.on_panel_paint(evt, p))
            
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
        except Exception as e:
            # 检查面板是否存在
            if hasattr(self, 'image_panels') and perspective in self.image_panels:
                canvas_panel = self.image_panels[perspective]
                if canvas_panel and canvas_panel.IsShownOnScreen():
                    dc = wx.ClientDC(canvas_panel)
                    dc.SetBackground(wx.Brush('#ffffff'))
                    dc.Clear()
                    dc.SetTextForeground('red')
                    dc.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                    dc.DrawText(f"Image display error: {str(e)}", 200, 100)
            else:
                print(f"Error in display_image_on_canvas: canvas panel for {perspective} not found")

    def on_panel_paint(self, event, perspective):
        """Handle panel paint events to maintain image display during scrolling/resizing"""
        try:
            entity_name = self.entity_data['name']
            cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
            
            if (hasattr(self, 'image_data_store') and 
                cache_key in self.image_data_store and 
                self.image_data_store[cache_key] is not None):
                
                # Redraw the image from stored data
                image_data = self.image_data_store[cache_key]
                canvas_panel = self.image_panels[perspective]
                
                # 检查面板是否还存在
                if not canvas_panel or not canvas_panel.IsShownOnScreen():
                    return
                
                # 创建唯一的临时文件名（包含实体名称和视角）
                temp_file = os.path.join(
                    os.path.dirname(__file__), 
                    '..', 
                    f'temp_image_{entity_name}_{perspective}.png'.replace(' ', '_').replace(':', '')
                )
                
                # 将图片数据保存到临时文件
                with open(temp_file, 'wb') as f:
                    f.write(image_data)
                
                # 从文件加载图片
                pil_image = PILImage.open(temp_file)
                
                # 转换为wxPython可以使用的格式
                width, height = pil_image.size
                image_buffer = pil_image.tobytes()
                wx_image = wx.Image(width, height)
                wx_image.SetData(image_buffer)
                
                # 缩放到适合画布的大小
                panel_width, panel_height = canvas_panel.GetSize()
                img_width, img_height = wx_image.GetSize()
                
                # 计算缩放比例，保持宽高比
                scale = min(panel_width / img_width, panel_height / img_height, 1.0)
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # 调整图片大小
                wx_image = wx_image.Scale(new_width, new_height, quality=wx.IMAGE_QUALITY_HIGH)
                
                # 转换为位图
                bitmap = wx.Bitmap(wx_image)
                
                # 使用更具体的存储键，避免跨卡片冲突
                cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
                
                # 保存位图引用到缓存以防止垃圾回收
                self.bitmap_cache[cache_key] = bitmap
                
                # 在画布上绘制图片
                dc = wx.PaintDC(canvas_panel)  # 使用PaintDC而不是ClientDC
                dc.SetBackground(wx.Brush('#ffffff'))
                dc.Clear()
                
                # 居中绘制图片
                x_pos = (panel_width - new_width) // 2
                y_pos = (panel_height - new_height) // 2
                dc.DrawBitmap(bitmap, x_pos, y_pos, True)
                
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        except Exception as e:
            print(f"Error in on_panel_paint: {str(e)}")

    def redraw_existing_images(self):
        """Redraw all existing images on panels"""
        try:
            entity_name = self.entity_data['name']
            for perspective in self.image_panels.keys():
                cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
                if (hasattr(self, 'image_data_store') and 
                    cache_key in self.image_data_store and 
                    self.image_data_store[cache_key] is not None):
                    
                    # Redraw the image from stored data
                    image_data = self.image_data_store[cache_key]
                    canvas_panel = self.image_panels[perspective]
                    
                    # 检查面板是否还存在
                    if not canvas_panel or not canvas_panel.IsShownOnScreen():
                        continue  # 跳过这个面板，继续处理其他面板
                    
                    # 创建唯一的临时文件名（包含实体名称和视角）
                    temp_file = os.path.join(
                        os.path.dirname(__file__), 
                        '..', 
                        f'temp_image_{entity_name}_{perspective}.png'.replace(' ', '_').replace(':', '')
                    )
                    
                    # 将图片数据保存到临时文件
                    with open(temp_file, 'wb') as f:
                        f.write(image_data)
                    
                    # 从文件加载图片
                    pil_image = PILImage.open(temp_file)
                    
                    # 转换为wxPython可以使用的格式
                    width, height = pil_image.size
                    image_buffer = pil_image.tobytes()
                    wx_image = wx.Image(width, height)
                    wx_image.SetData(image_buffer)
                    
                    # 缩放到适合画布的大小
                    panel_width, panel_height = canvas_panel.GetSize()
                    img_width, img_height = wx_image.GetSize()
                    
                    # 计算缩放比例，保持宽高比
                    scale = min(panel_width / img_width, panel_height / img_height, 1.0)
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    
                    # 调整图片大小
                    wx_image = wx_image.Scale(new_width, new_height, quality=wx.IMAGE_QUALITY_HIGH)
                    
                    # 转换为位图
                    bitmap = wx.Bitmap(wx_image)
                    
                    # 使用更具体的存储键，避免跨卡片冲突
                    cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
                    
                    # 保存位图引用到缓存以防止垃圾回收
                    self.bitmap_cache[cache_key] = bitmap
                    
                    # 在画布上绘制图片
                    dc = wx.ClientDC(canvas_panel)
                    dc.SetBackground(wx.Brush('#ffffff'))
                    dc.Clear()
                    
                    # 居中绘制图片
                    x_pos = (panel_width - new_width) // 2
                    y_pos = (panel_height - new_height) // 2
                    dc.DrawBitmap(bitmap, x_pos, y_pos, True)
                    
                    # 清理临时文件
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
        except Exception as e:
            print(f"Error redrawing images: {str(e)}")

    def auto_save_image(self, image_data, entity_name, perspective):
        """Auto-save generated image to project folder"""
        try:
            # Create images folder in project directory
            images_dir = os.path.join(self.project_path, 'generated_images')
            os.makedirs(images_dir, exist_ok=True)
            
            # Create unique filename using entity name, perspective and timestamp
            timestamp = int(time.time() * 1000)  # milliseconds since epoch
            filename = f"{entity_name}_{perspective}_{timestamp}.png".replace(' ', '_').replace(':', '')
            filepath = os.path.join(images_dir, filename)
            
            # Save image data to file
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
        except Exception as e:
            print(f"Failed to auto-save image: {str(e)}")

    def copy_prompt(self, prompt):
        """Copy prompt to clipboard"""
        try:
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(prompt))
                wx.TheClipboard.Close()
                dlg = wx.MessageDialog(None, "Prompt copied to clipboard!", "Copy Success", wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                dlg = wx.MessageDialog(None, f"Error occurred while copying prompt:\nFailed to open clipboard", 
                                      "Copy Failed", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
        except Exception as e:
            dlg = wx.MessageDialog(None, f"Error occurred while copying prompt:\n{str(e)}", 
                                  "Copy Failed", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def cleanup(self):
        """清理资源，关闭线程池"""
        if hasattr(self, 'executor'):
            # 等待所有任务完成
            for future in self.futures:
                try:
                    future.result(timeout=10)  # 等待最多10秒
                except:
                    pass  # 忽略超时或其他异常
            self.executor.shutdown(wait=True)

    def download_image(self, perspective):
        """下载图片到指定位置"""
        # 使用唯一标识获取图像数据
        cache_key = f"{self.entity_data['name']}_{perspective}".replace(' ', '_')
        
        if cache_key not in self.image_data_store or self.image_data_store[cache_key] is None:
            wx.MessageBox("没有可下载的图片", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        # 弹出文件保存对话框
        wildcard = "PNG files (*.png)|*.png|JPEG files (*.jpg;*.jpeg)|*.jpg;*.jpeg|All files (*.*)|*.*"
        filename = f"{self.entity_data['name']}_{perspective}.png"  # 使用实体名称+视角作为默认文件名
        dialog = wx.FileDialog(self, "保存图片", os.getcwd(), filename,
                              wildcard, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            try:
                with open(filepath, 'wb') as f:
                    f.write(self.image_data_store[cache_key])
                wx.MessageBox(f"图片已保存到: {filepath}", "保存成功", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"保存图片失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        
        dialog.Destroy()

    def fullscreen_view(self, perspective):
        """全屏查看图片"""
        # 使用唯一标识获取图像数据
        cache_key = f"{self.entity_data['name']}_{perspective}".replace(' ', '_')
        
        if cache_key not in self.image_data_store or self.image_data_store[cache_key] is None:
            wx.MessageBox("没有可查看的图片", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        # 创建全屏窗口
        fullscreen_frame = FullScreenImageFrame(self, self.image_data_store[cache_key], 
                                              f"{self.entity_data['name']} - {perspective}")
        fullscreen_frame.ShowFullScreen(True)
        
    def redraw_image(self, perspective):
        """Redraw a specific image on panel"""
        try:
            entity_name = self.entity_data['name']
            cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
            
            if (hasattr(self, 'image_data_store') and 
                cache_key in self.image_data_store and 
                self.image_data_store[cache_key] is not None):
                
                # Redraw the image from stored data
                image_data = self.image_data_store[cache_key]
                canvas_panel = self.image_panels[perspective]
                
                # 检查面板是否还存在
                if not canvas_panel or not canvas_panel.IsShownOnScreen():
                    return
                
                # 创建唯一的临时文件名（包含实体名称和视角）
                temp_file = os.path.join(
                    os.path.dirname(__file__), 
                    '..', 
                    f'temp_image_{entity_name}_{perspective}.png'.replace(' ', '_').replace(':', '')
                )
                
                # 将图片数据保存到临时文件
                with open(temp_file, 'wb') as f:
                    f.write(image_data)
                
                # 从文件加载图片
                pil_image = PILImage.open(temp_file)
                
                # 转换为wxPython可以使用的格式
                width, height = pil_image.size
                image_buffer = pil_image.tobytes()
                wx_image = wx.Image(width, height)
                wx_image.SetData(image_buffer)
                
                # 缩放到适合画布的大小
                panel_width, panel_height = canvas_panel.GetSize()
                img_width, img_height = wx_image.GetSize()
                
                # 计算缩放比例，保持宽高比
                scale = min(panel_width / img_width, panel_height / img_height, 1.0)
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # 调整图片大小
                wx_image = wx_image.Scale(new_width, new_height, quality=wx.IMAGE_QUALITY_HIGH)
                
                # 转换为位图
                bitmap = wx.Bitmap(wx_image)
                
                # 使用更具体的存储键，避免跨卡片冲突
                cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
                
                # 保存位图引用到缓存以防止垃圾回收
                self.bitmap_cache[cache_key] = bitmap
                
                # 在画布上绘制图片
                dc = wx.ClientDC(canvas_panel)
                dc.SetBackground(wx.Brush('#ffffff'))
                dc.Clear()
                
                # 居中绘制图片
                x_pos = (panel_width - new_width) // 2
                y_pos = (panel_height - new_height) // 2
                dc.DrawBitmap(bitmap, x_pos, y_pos, True)
                
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
                wx.MessageBox(f"图片已刷新: {perspective}", "成功", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"刷新图片失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def save_image_to_db(self, perspective):
        """将图片保存到数据库"""
        # 使用唯一标识获取图像数据
        cache_key = f"{self.entity_data['name']}_{perspective}".replace(' ', '_')
        
        if cache_key not in self.image_data_store or self.image_data_store[cache_key] is None:
            wx.MessageBox("没有可保存的图片", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        try:
            # 连接到项目数据库
            db_path = os.path.join(self.project_path, 'project.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建图片存储表（如果不存在）
            cursor.execute('''CREATE TABLE IF NOT EXISTS entity_images (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                entity_name TEXT NOT NULL,
                                perspective TEXT NOT NULL,
                                image_data BLOB NOT NULL,
                                filename TEXT,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(entity_name, perspective)
                            )''')
            
            # 生成文件名
            filename = f"{self.entity_data['name']}_{perspective}.png"
            
            # 插入或更新图片数据
            cursor.execute('''INSERT OR REPLACE INTO entity_images 
                              (entity_name, perspective, image_data, filename) 
                              VALUES (?, ?, ?, ?)''', 
                          (self.entity_data['name'], perspective, self.image_data_store[cache_key], filename))
            
            conn.commit()
            conn.close()
            
            wx.MessageBox(f"图片已保存到数据库: {self.entity_data['name']}_{perspective}", 
                         "保存成功", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"保存图片到数据库失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def ensure_image_displayed(self, perspective):
        """确保图片在Panel变得可见时显示"""
        try:
            entity_name = self.entity_data['name']
            cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
            
            if (hasattr(self, 'image_data_store') and 
                cache_key in self.image_data_store and 
                self.image_data_store[cache_key] is not None):
                
                # 重新显示图片
                self.redraw_image(perspective)
        except Exception as e:
            print(f"Error in ensure_image_displayed: {str(e)}")


class FullScreenImageFrame(wx.Frame):
    """
    全屏图片查看窗口
    """
    def __init__(self, parent, image_data, title):
        super().__init__(None, title=title, style=wx.NO_BORDER)
        
        self.parent = parent
        self.image_data = image_data
        
        # 设置全屏背景
        self.SetBackgroundColour('black')
        
        # 创建图片显示控件
        self.image_panel = wx.Panel(self)
        self.image_panel.SetBackgroundColour('black')
        
        # 绑定ESC键退出全屏
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.image_panel.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        
        # 显示图片
        self.show_image()
        
        # 绑定鼠标左键单击事件
        self.image_panel.Bind(wx.EVT_LEFT_UP, self.exit_fullscreen)
        
        # 布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.image_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
    def show_image(self):
        """显示图片"""
        try:
            # 将图片数据转换为PIL图像
            image_stream = BytesIO(self.image_data)
            pil_image = PILImage.open(image_stream)
            
            # 获取屏幕尺寸
            screen_width, screen_height = wx.DisplaySize()
            
            # 获取图片原始尺寸
            img_width, img_height = pil_image.size
            
            # 计算缩放比例，适应屏幕大小
            scale = min(screen_width / img_width, screen_height / img_height, 1.0)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # 调整图片大小
            resized_image = pil_image.resize((new_width, new_height), PILImage.LANCZOS)
            
            # 转换为wxPython图像
            width, height = resized_image.size
            image_buffer = resized_image.tobytes()
            wx_image = wx.Image(width, height)
            wx_image.SetData(image_buffer)
            bitmap = wx.Bitmap(wx_image)
            
            # 创建静态位图显示图片
            if hasattr(self, 'static_bitmap'):
                self.static_bitmap.SetBitmap(bitmap)
            else:
                self.static_bitmap = wx.StaticBitmap(self.image_panel, bitmap=bitmap)
            
            # 居中显示
            panel_size = self.image_panel.GetSize()
            x_pos = max(0, (panel_size.width - new_width) // 2)
            y_pos = max(0, (panel_size.height - new_height) // 2)
            self.static_bitmap.SetPosition((x_pos, y_pos))
            
        except Exception as e:
            wx.MessageBox(f"无法显示图片: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            self.exit_fullscreen()
    
    def on_key_down(self, event):
        """处理键盘按键事件"""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.exit_fullscreen()
        else:
            event.Skip()
    
    def exit_fullscreen(self, event=None):
        """退出全屏"""
        self.ShowFullScreen(False)
        self.Destroy()

class EntityGenerationWindow:
    """
    Entity Generation Window
    """
    
    def __init__(self, project_path):
        """Initialize entity generation window"""
        self.project_path = project_path
        self.app = wx.App()
        self.frame = wx.Frame(None, title="Entity Generation", size=(1000, 800))
        self.frame.SetBackgroundColour('#f8f9fa')
        
        # 加载API配置
        self.api_config = self.load_api_config()
        
        # 加载实体数据
        self.entities = self.load_entities()
        
        self.setup_ui()
    
    def load_api_config(self):
        """Load API configuration"""
        try:
            # 从项目配置文件加载API配置
            config_path = os.path.join(self.project_path, 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    project_config = json.load(f)
                return project_config.get('api_config', {})
        except Exception as e:
            print(f"Failed to load API configuration: {str(e)}")
        
        # 返回默认配置
        return {
            "api_url": "",
            "api_key": "",
            "model": "dall-e-3"
        }
    
    def load_entities(self):
        """Load entities and prompts data from database"""
        entities = []
        try:
            # 连接到项目数据库
            db_path = os.path.join(self.project_path, 'project.db')
            if not os.path.exists(db_path):
                print(f"Database file does not exist: {db_path}")
                return self.get_sample_entities()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查找所有包含_prompts的表（这些是故事信息提取生成的提示表）
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_prompts'")
            prompt_tables = cursor.fetchall()
            
            if not prompt_tables:
                print("No saved prompt data found")
                conn.close()
                return self.get_sample_entities()
            
            # 从所有提示表获取数据
            for table_info in prompt_tables:
                table_name = table_info[0]
                # 移除'_prompts'后缀以获取基础表名，通常对应章节名
                base_name = table_name.replace('_prompts', '')
                
                try:
                    # 查询此表中的所有提示
                    cursor.execute(f"SELECT entity_name, perspective, detailed_prompt, usage FROM `{table_name}`")
                    prompt_rows = cursor.fetchall()
                    
                    # 按实体名称组织数据
                    entities_dict = {}
                    for row in prompt_rows:
                        entity_name, perspective, detailed_prompt, usage = row
                        
                        if entity_name not in entities_dict:
                            entities_dict[entity_name] = {
                                "name": entity_name,
                                "prompts": {}
                            }
                        
                        # 使用视角作为键来存储详细提示
                        entities_dict[entity_name]["prompts"][perspective] = detailed_prompt
                    
                    # 添加实体到总列表
                    for entity in entities_dict.values():
                        # 检查是否已在实体列表中存在，以避免重复
                        if not any(e["name"] == entity["name"] for e in entities):
                            entities.append(entity)
                except sqlite3.Error as e:
                    print(f"Error reading table {table_name}: {str(e)}")
                    continue
            
            conn.close()
            
            if not entities:
                print("No valid entity data found in database")
                return self.get_sample_entities()
            
        except Exception as e:
            print(f"Failed to load entity data: {str(e)}")
            return self.get_sample_entities()
        
        return entities
    
    def get_sample_entities(self):
        """Get sample entity data"""
        return [
            {
                "name": "Main Character A",
                "prompts": {
                    "Front View": "High-quality front view of the character, clearly showing facial features and costume details",
                    "Side View": "Character side profile, showing body proportions and posture",
                    "Back View": "Character back view, showing hairstyle and back costume details",
                    "Full Body": "Full body view of the character, showing complete appearance and clothing"
                }
            }
        ]
    
    def setup_ui(self):
        """Set up main interface"""
        # 主面板
        main_panel = wx.Panel(self.frame)
        main_panel.SetBackgroundColour('#f8f9fa')
        
        # 主布局
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 顶部框架
        top_panel = wx.Panel(main_panel, style=wx.BORDER_RAISED)
        top_panel.SetBackgroundColour('#f8f9fa')
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 标题
        title_text = wx.StaticText(top_panel, label="Entity Generation")
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_text.SetFont(font)
        title_text.SetForegroundColour('#495057')
        title_text.SetBackgroundColour('#f8f9fa')
        top_sizer.Add(title_text, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)
        
        # 刷新按钮
        refresh_btn = wx.Button(top_panel, label="Refresh Entity Data", size=(150, -1))
        refresh_btn.SetBackgroundColour('#17a2b8')
        refresh_btn.SetForegroundColour('white')
        refresh_btn.Bind(wx.EVT_BUTTON, self.refresh_entities)
        top_sizer.Add(refresh_btn, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
        
        top_panel.SetSizer(top_sizer)
        main_sizer.Add(top_panel, 0, wx.EXPAND | wx.ALL, 10)
        
        # 主内容区域 - 使用滚动面板
        scroll_panel = scrolled.ScrolledPanel(main_panel, style=wx.VSCROLL)
        scroll_panel.SetBackgroundColour('#f8f9fa')
        
        content_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 为每个实体创建卡片
        for entity_data in self.entities:
            card = EntityCard(scroll_panel, entity_data, self.api_config, self.project_path)
            content_sizer.Add(card, 0, wx.EXPAND | wx.ALL, 8)
        
        scroll_panel.SetSizer(content_sizer)
        scroll_panel.SetupScrolling()
        
        main_sizer.Add(scroll_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        main_panel.SetSizer(main_sizer)
        
        # 设置框架布局
        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(main_panel, 1, wx.EXPAND)
        self.frame.SetSizer(frame_sizer)
        
        # 显示窗口
        self.frame.Show()
    
    def refresh_entities(self, event):
        """Refresh entity data"""
        self.entities = self.load_entities()
        
        # 重新构建UI
        self.frame.DestroyChildren()
        self.setup_ui()
        self.frame.Layout()
        
        # 在UI重建后重新绘制所有现有图片
        self.redraw_all_existing_images()

    def redraw_all_existing_images(self):
        """重新绘制所有实体卡片上的现有图片"""
        try:
            # 获取滚动面板中的所有子控件
            main_panel = self.frame.GetChildren()[0]  # 主面板
            scroll_panel = main_panel.GetChildren()[1]  # 滚动面板
            
            # 遍历滚动面板中的所有实体卡片
            for child in scroll_panel.GetChildren():
                if 'EntityCard' in str(type(child)):
                    # 在此卡片上重新绘制现有图片
                    if hasattr(child, 'redraw_existing_images'):
                        child.redraw_existing_images()
        except Exception as e:
            print(f"重新绘制所有现有图片时出错: {str(e)}")

    def show(self):
        """Show the window"""
        self.app.MainLoop()


if __name__ == "__main__":
    # 测试用例 - 假设有项目路径
    project_path = "./test_project"  # 替换为实际项目路径
    app = EntityGenerationWindow(project_path)
    app.show()