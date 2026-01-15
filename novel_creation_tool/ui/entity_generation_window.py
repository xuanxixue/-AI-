import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from concurrent.futures import ThreadPoolExecutor
import json
import requests
import time
import sqlite3
from PIL import Image, ImageTk
from io import BytesIO
import base64

class EntityCard(tk.Frame):
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
        super().__init__(parent, relief="groove", borderwidth=2)
        self.entity_data = entity_data
        self.api_config = api_config
        self.project_path = project_path
        
        self.image_data = {}  # 存储生成的图片
        
        # 创建图片缓存以防止垃圾回收
        self.image_cache = {}
        
        # 创建线程池用于图像生成
        self.executor = ThreadPoolExecutor(max_workers=3)  # 最多同时处理3个图像生成任务
        
        # 存储线程池任务
        self.futures = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置实体卡片界面"""
        # 设置卡片背景色
        self.configure(bg="#ffffff", relief="solid", bd=1)
            
        # 实体名称标签
        name_label = tk.Label(self, text=f"实体: {self.entity_data['name']}", 
                              font=("Microsoft YaHei", 14, "bold"),
                              bg="#ffffff", fg="#212529", anchor="center")
        name_label.pack(fill=tk.X, padx=10, pady=(10, 15))
        
        # Create main frame, distribute prompts and images left and right
        main_frame = tk.Frame(self, bg="#ffffff")
        main_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Left prompt area
        prompt_frame = tk.Frame(main_frame, bg="#ffffff", width=600)
        prompt_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        prompt_frame.pack_propagate(False)  # Fixed width
        
        # Right image display area
        image_area_frame = tk.Frame(main_frame, bg="#f8f9fa", relief="groove", bd=1)
        image_area_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create labels, buttons and image display areas for each perspective prompt
        for idx, (perspective, prompt) in enumerate(self.entity_data.get('prompts', {}).items()):            
            # Create a main frame for this perspective
            perspective_main_frame = tk.Frame(prompt_frame, bg="#ffffff", relief="flat")
            perspective_main_frame.pack(fill=tk.X, pady=5)
                        
            # Top row: prompt label, copy button, generate button
            top_row_frame = tk.Frame(perspective_main_frame, bg="#ffffff")
            top_row_frame.pack(fill=tk.X, pady=(0, 5))
                        
            # Copy button
            copy_btn = tk.Button(top_row_frame, text="复制", 
                                 command=lambda p=prompt: self.copy_prompt(p),
                                 bg="#007bff", fg="white",
                                 font=("Microsoft YaHei", 9),
                                 relief="flat", bd=0, padx=6, pady=4)
            copy_btn.pack(side=tk.RIGHT, padx=(0, 5))
                        
            # Prompt label
            prompt_label = tk.Label(top_row_frame, text=f"{perspective}: {prompt}",
                                    font=("Microsoft YaHei", 10),
                                    bg="#ffffff", fg="#495057",
                                    wraplength=450, justify=tk.LEFT)
            prompt_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
                        
            # Generate button - Now all perspectives can be generated, using unified green button
            generate_btn = tk.Button(top_row_frame, text="生成", 
                                     command=lambda p=prompt, ps=perspective: self.generate_image(p, ps),
                                     bg="#28a745", fg="white",
                                     font=("Microsoft YaHei", 9),
                                     relief="flat", bd=0, padx=8, pady=4)
            generate_btn.pack(side=tk.RIGHT)
                        
            # Bottom row: style and ratio controls
            bottom_row_frame = tk.Frame(perspective_main_frame, bg="#ffffff")
            bottom_row_frame.pack(fill=tk.X, pady=(5, 0))
                        
            # Style requirement input area
            style_frame = tk.Frame(bottom_row_frame, bg="#ffffff")
            style_frame.pack(fill=tk.X, pady=(0, 5))
                        
            style_label = tk.Label(style_frame, text="Style requirement:",
                                   font=("Microsoft YaHei", 9),
                                   bg="#ffffff", fg="#6c757d")
            style_label.pack(side=tk.LEFT)
                        
            style_entry = tk.Entry(style_frame, font=("Microsoft YaHei", 9), width=30)
            style_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
                        
            # Store style input box reference
            if 'style_entries' not in self.__dict__:
                self.style_entries = {}
            self.style_entries[perspective] = style_entry
                        
            # Image ratio selection area
            ratio_frame = tk.Frame(bottom_row_frame, bg="#ffffff")
            ratio_frame.pack(fill=tk.X, pady=(0, 5))
                        
            ratio_label = tk.Label(ratio_frame, text="Image ratio:",
                                   font=("Microsoft YaHei", 9),
                                   bg="#ffffff", fg="#6c757d")
            ratio_label.pack(side=tk.LEFT)
                        
            # Image ratio options
            ratio_var = tk.StringVar(value="1:1")
            ratios = ["1:1", "4:3", "3:2", "16:9", "9:16"]
                        
            ratio_menu = tk.OptionMenu(ratio_frame, ratio_var, *ratios)
            ratio_menu.config(font=("Microsoft YaHei", 9), bg="#ffffff", fg="#495057")
            ratio_menu.pack(side=tk.LEFT, padx=(5, 0))
                        
            # Store ratio variable reference
            if 'ratio_vars' not in self.__dict__:
                self.ratio_vars = {}
            self.ratio_vars[perspective] = ratio_var
            
            # Model selection dropdown
            model_label = tk.Label(ratio_frame, text="Model:",
                                   font=("Microsoft YaHei", 9),
                                   bg="#ffffff", fg="#6c757d")
            model_label.pack(side=tk.LEFT, padx=(10, 0))
            
            # Model options
            model_var = tk.StringVar(value="Auto")
            models = ["Auto", "Text-to-Image", "Image-to-Image", "Image-to-Image-Plus", "Text-to-Image-Plus"]
            
            model_menu = tk.OptionMenu(ratio_frame, model_var, *models)
            model_menu.config(font=("Microsoft YaHei", 9), bg="#ffffff", fg="#495057")
            model_menu.pack(side=tk.LEFT, padx=(5, 0))
            
            # Store model variable reference
            if 'model_vars' not in self.__dict__:
                self.model_vars = {}
            self.model_vars[perspective] = model_var
            
            # Image display area
            image_frame = tk.Frame(image_area_frame, bg="#f8f9fa", relief="groove", bd=1)
            image_frame.pack(fill=tk.X, padx=5, pady=5, ipadx=5, ipady=5)
                
            image_header = tk.Frame(image_frame, bg="#f8f9fa")
            image_header.pack(fill=tk.X, padx=5, pady=5)
                
            image_label = tk.Label(image_header, text=f"{perspective} Image Preview:", 
                                   font=("Microsoft YaHei", 11, "bold"),
                                   bg="#f8f9fa", fg="#495057")
            image_label.pack(side=tk.LEFT)
                
            # Add function buttons
            button_frame = tk.Frame(image_header, bg="#f8f9fa")
            button_frame.pack(side=tk.RIGHT)
            
            # Download button
            download_btn = tk.Button(button_frame, text="下载", 
                                    command=lambda p=perspective: self.download_image(p),
                                    bg="#007bff", fg="white",
                                    font=("Microsoft YaHei", 9),
                                    relief="flat", bd=0, padx=6, pady=2)
            download_btn.pack(side=tk.LEFT, padx=2)
            
            # Fullscreen button
            fullscreen_btn = tk.Button(button_frame, text="全屏", 
                                      command=lambda p=perspective: self.fullscreen_view(p),
                                      bg="#28a745", fg="white",
                                      font=("Microsoft YaHei", 9),
                                      relief="flat", bd=0, padx=6, pady=2)
            fullscreen_btn.pack(side=tk.LEFT, padx=2)
            
            # Refresh button
            refresh_btn = tk.Button(button_frame, text="刷新", 
                                  command=lambda p=perspective: self.redraw_image(p),
                                  bg="#6c757d", fg="white",
                                  font=("Microsoft YaHei", 9),
                                  relief="flat", bd=0, padx=6, pady=2)
            refresh_btn.pack(side=tk.LEFT, padx=2)
            
            # Save button
            save_btn = tk.Button(button_frame, text="保存", 
                                command=lambda p=perspective: self.save_image_to_db(p),
                                bg="#ffc107", fg="#212529",
                                font=("Microsoft YaHei", 9),
                                relief="flat", bd=0, padx=6, pady=2)
            save_btn.pack(side=tk.LEFT, padx=2)
                
            # Canvas for displaying images
            canvas = tk.Canvas(image_frame, width=500, height=250, bg="#ffffff", relief="flat", bd=1)
            canvas.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
                
            # Store canvas reference for subsequent updates
            if 'image_canvases' not in self.__dict__:
                self.image_canvases = {}
            self.image_canvases[perspective] = canvas
            
            # Store image data
            if not hasattr(self, 'image_data_store'):
                self.image_data_store = {}
            self.image_data_store[perspective] = None
            
            # 为Canvas绑定更多事件以处理滚动和显示问题
            canvas.bind('<Visibility>', lambda e, p=perspective: self.ensure_image_displayed(p))
            canvas.bind('<Expose>', lambda e, p=perspective: self.ensure_image_displayed(p))

    def ensure_image_displayed(self, perspective):
        """确保图片在Canvas变得可见时显示"""
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

    def generate_image(self, prompt, perspective):
        """Generate image"""
        # Execute in new thread to avoid UI blocking
        canvas = self.image_canvases[perspective]  # Pass canvas object for subsequent processing

        # Get the latest values from UI controls
        if hasattr(self, 'style_entries') and perspective in self.style_entries:
            style_requirement = self.style_entries[perspective].get().strip()
            if style_requirement:
                prompt = f"{prompt}, Style requirement: {style_requirement}"

        # Submit task to thread pool
        future = self.executor.submit(self._generate_image_thread, prompt, perspective, canvas)
        # Store the Future object for management
        self.futures.append(future)
    
    def _generate_image_thread(self, prompt, perspective, canvas):
        """Generate image in background thread"""
        try:
            # Show loading status
            canvas.delete("all")
            loading_text = canvas.create_text(200, 100, text="Generating...", font=("Microsoft YaHei", 12), fill="gray")
                
            # Call API to generate image
            response = self.call_image_generation_api(prompt, canvas, loading_text)
                
            if response:
                # Display image data on Canvas
                self.display_image_on_canvas(response, perspective)
            else:
                canvas.delete("all")
                canvas.create_text(200, 100, text="Generation failed", font=("Microsoft YaHei", 12), fill="red")
                    
        except Exception as e:
            canvas.delete("all")
            canvas.create_text(200, 100, text=f"Error: {str(e)}", font=("Microsoft YaHei", 12), fill="red")
    
    def call_image_generation_api(self, prompt, canvas=None, loading_text=None):
        """Call image generation API - Using ModelScope API with manual model selection"""
        try:
            # Get current perspective ratio setting
            perspective = None
            for key, canvas_ref in self.image_canvases.items():
                if canvas_ref == canvas:
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
            
            # Get current perspective image ratio setting
            size_param = '1024x1024'  # Default ratio for ModelScope
            dashscope_size_param = '1024*1024'  # Default ratio for DashScope
            if hasattr(self, 'ratio_vars') and perspective in self.ratio_vars:
                ratio = self.ratio_vars[perspective].get()
                size_param = size_mapping.get(ratio, '1024x1024')
                dashscope_size_param = dashscope_size_mapping.get(ratio, '1024*1024')

            # Get the selected model from dropdown
            selected_model = "Auto"  # Default
            if (hasattr(self, 'model_vars') and 
                perspective in self.model_vars):
                selected_model = self.model_vars[perspective].get()

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
            canvas = self.image_canvases[perspective]
            
            # Update canvas size to ensure proper width and height
            canvas.update_idletasks()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width <= 1:  # If Canvas hasn't rendered, use default size
                canvas_width = 500
                canvas_height = 250
            
            # 创建唯一的临时文件名（包含实体名称和视角）
            temp_file = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                f'temp_image_{entity_name}_{perspective}.png'.replace(' ', '_').replace(':', '')
            )
            
            # Save image data to temporary file
            with open(temp_file, 'wb') as f:
                f.write(image_data)
            
            # Load image from file
            photo = ImageTk.PhotoImage(file=temp_file)
            
            # 创建唯一的标签（包含实体名称和视角）
            image_tag = f'image_{entity_name}_{perspective}'.replace(' ', '_')
            
            # 删除当前Canvas上的所有旧图像（只删除本Canvas的内容）
            canvas.delete(image_tag)
            x_center = canvas_width // 2
            y_center = canvas_height // 2
            
            # Create image on canvas with specific tag
            canvas.create_image(x_center, y_center, image=photo, anchor=tk.CENTER, tags=image_tag)
            
            # 使用更具体的存储键，避免跨卡片冲突
            cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
            
            # Store image reference to prevent garbage collection
            if not hasattr(self, 'image_cache'):
                self.image_cache = {}
            self.image_cache[cache_key] = photo
            
            # Also store the image in the canvas object to prevent garbage collection
            if not hasattr(canvas, 'images'):
                canvas.images = {}
            canvas.images[cache_key] = photo
            
            # Store image data for download/save functionality
            self.image_data_store[cache_key] = image_data
            
            # Auto-save the image to the project's images folder
            self.auto_save_image(image_data, entity_name, perspective)
            
            # 绑定配置事件，当Canvas大小改变时重新绘制图片
            canvas.bind('<Configure>', lambda e, p=perspective: self.on_canvas_configure(p))
            
            # Clean up temporary file after displaying
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
        except Exception as e:
            canvas = self.image_canvases[perspective]
            canvas.delete("all")
            canvas.create_text(200, 100, text=f"Image display error: {str(e)}", font=("Microsoft YaHei", 12), fill="red")

    def on_canvas_configure(self, perspective):
        """Handle canvas resize/reconfigure events to maintain image display"""
        try:
            entity_name = self.entity_data['name']
            cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
            
            if (hasattr(self, 'image_data_store') and 
                cache_key in self.image_data_store and 
                self.image_data_store[cache_key] is not None):
                
                # Redraw the image from stored data
                image_data = self.image_data_store[cache_key]
                canvas = self.image_canvases[perspective]
                
                # Update canvas size to ensure proper width and height
                canvas.update_idletasks()
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                
                if canvas_width <= 1:  # If Canvas hasn't rendered, use default size
                    canvas_width = 500
                    canvas_height = 250
                
                # 创建唯一的临时文件名（包含实体名称和视角）
                temp_file = os.path.join(
                    os.path.dirname(__file__), 
                    '..', 
                    f'temp_image_{entity_name}_{perspective}.png'.replace(' ', '_').replace(':', '')
                )
                
                # Save image data to temporary file
                with open(temp_file, 'wb') as f:
                    f.write(image_data)
                
                # Load image from file
                photo = ImageTk.PhotoImage(file=temp_file)
                
                # 创建唯一的标签（包含实体名称和视角）
                image_tag = f'image_{entity_name}_{perspective}'.replace(' ', '_')
                
                # 删除当前Canvas上的所有旧图像（只删除本Canvas的内容）
                canvas.delete(image_tag)
                x_center = canvas_width // 2
                y_center = canvas_height // 2
                
                # Create image on canvas with specific tag
                canvas.create_image(x_center, y_center, image=photo, anchor=tk.CENTER, tags=image_tag)
                
                # Store image reference to prevent garbage collection
                if not hasattr(self, 'image_cache'):
                    self.image_cache = {}
                self.image_cache[cache_key] = photo
                
                # Also store the image in the canvas object to prevent garbage collection
                if not hasattr(canvas, 'images'):
                    canvas.images = {}
                canvas.images[cache_key] = photo
                
                # Clean up temporary file after displaying
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        except Exception as e:
            print(f"Error in on_canvas_configure: {str(e)}")

    def redraw_existing_images(self):
        """Redraw all existing images on canvases"""
        try:
            entity_name = self.entity_data['name']
            for perspective in self.image_canvases.keys():
                cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
                if (hasattr(self, 'image_data_store') and 
                    cache_key in self.image_data_store and 
                    self.image_data_store[cache_key] is not None):
                    
                    # Redraw the image from stored data
                    image_data = self.image_data_store[cache_key]
                    canvas = self.image_canvases[perspective]
                    
                    # Update canvas size to ensure proper width and height
                    canvas.update_idletasks()
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    if canvas_width <= 1:  # If Canvas hasn't rendered, use default size
                        canvas_width = 500
                        canvas_height = 250
                    
                    # 创建唯一的临时文件名（包含实体名称和视角）
                    temp_file = os.path.join(
                        os.path.dirname(__file__), 
                        '..', 
                        f'temp_image_{entity_name}_{perspective}.png'.replace(' ', '_').replace(':', '')
                    )
                    
                    # Save image data to temporary file
                    with open(temp_file, 'wb') as f:
                        f.write(image_data)
                    
                    # Load image from file
                    photo = ImageTk.PhotoImage(file=temp_file)
                    
                    # 创建唯一的标签（包含实体名称和视角）
                    image_tag = f'image_{entity_name}_{perspective}'.replace(' ', '_')
                    
                    # 删除当前Canvas上的所有旧图像（只删除本Canvas的内容）
                    canvas.delete(image_tag)
                    x_center = canvas_width // 2
                    y_center = canvas_height // 2
                    
                    # Create image on canvas with specific tag
                    canvas.create_image(x_center, y_center, image=photo, anchor=tk.CENTER, tags=image_tag)
                    
                    # Store image reference to prevent garbage collection
                    if not hasattr(self, 'image_cache'):
                        self.image_cache = {}
                    self.image_cache[cache_key] = photo
                    
                    # Also store the image in the canvas object to prevent garbage collection
                    if not hasattr(canvas, 'images'):
                        canvas.images = {}
                    canvas.images[cache_key] = photo
                    
                    # Clean up temporary file after displaying
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
            self.clipboard_clear()  # Clear clipboard
            self.clipboard_append(prompt)  # Add prompt to clipboard
            messagebox.showinfo("Copy Success", "Prompt copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Copy Failed", f"Error occurred while copying prompt:\n{str(e)}")

    def cleanup(self):
        """Clean up resources, shut down thread pool"""
        if hasattr(self, 'executor'):
            # Wait for all tasks to complete
            for future in self.futures:
                try:
                    future.result(timeout=10)  # Wait for up to 10 seconds
                except:
                    pass  # Ignore timeout or other exceptions
            self.executor.shutdown(wait=True)

    def download_image(self, perspective):
        """Download image to specified location"""
        # 使用唯一标识获取图像数据
        cache_key = f"{self.entity_data['name']}_{perspective}".replace(' ', '_')
        
        if cache_key not in self.image_data_store or self.image_data_store[cache_key] is None:
            messagebox.showwarning("Warning", "No image to download")
            return
        
        from tkinter import filedialog
        # Open file save dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
            initialfile=f"{self.entity_data['name']}_{perspective}.png"  # Use entity name + perspective as default filename
        )
        
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(self.image_data_store[cache_key])
                messagebox.showinfo("Success", f"Image saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")

    def fullscreen_view(self, perspective):
        """View image in fullscreen"""
        # 使用唯一标识获取图像数据
        cache_key = f"{self.entity_data['name']}_{perspective}".replace(' ', '_')
        
        if cache_key not in self.image_data_store or self.image_data_store[cache_key] is None:
            messagebox.showwarning("Warning", "No image to view")
            return
        
        import tkinter as tk
        from PIL import Image, ImageTk
        import io
        
        # Create fullscreen window
        fullscreen_win = tk.Toplevel(self)
        fullscreen_win.attributes('-fullscreen', True)
        fullscreen_win.configure(bg='black')
        
        # Bind ESC key to exit fullscreen
        fullscreen_win.bind('<Escape>', lambda e: fullscreen_win.destroy())
        
        # Create frame to hold the image
        frame = tk.Frame(fullscreen_win, bg='black')
        frame.pack(expand=True)
        
        try:
            # Convert image data to PIL Image
            image_stream = io.BytesIO(self.image_data_store[cache_key])
            pil_image = Image.open(image_stream)
            
            # Get screen dimensions
            screen_width = fullscreen_win.winfo_screenwidth()
            screen_height = fullscreen_win.winfo_screenheight()
            
            # Get original image dimensions
            img_width, img_height = pil_image.size
            
            # Calculate scale to fit the screen
            scale = min(screen_width / img_width, screen_height / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(resized_image)
            
            # Create label to display image
            img_label = tk.Label(frame, image=photo, bg='black')
            img_label.pack(expand=True)
            
            # Store reference to prevent garbage collection
            img_label.image = photo
            
            # Bind click to exit fullscreen
            img_label.bind('<Button-1>', lambda e: fullscreen_win.destroy())
            
        except Exception as e:
            messagebox.showerror("Error", f"Cannot display image: {str(e)}")
            fullscreen_win.destroy()

    def save_image_to_db(self, perspective):
        """Save image to database"""
        # 使用唯一标识获取图像数据
        cache_key = f"{self.entity_data['name']}_{perspective}".replace(' ', '_')
        
        if cache_key not in self.image_data_store or self.image_data_store[cache_key] is None:
            messagebox.showwarning("Warning", "No image to save")
            return
        
        try:
            # Connect to project database
            import sqlite3
            db_path = os.path.join(self.project_path, 'project.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create image storage table (if not exists)
            cursor.execute('''CREATE TABLE IF NOT EXISTS entity_images (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                entity_name TEXT NOT NULL,
                                perspective TEXT NOT NULL,
                                image_data BLOB NOT NULL,
                                filename TEXT,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(entity_name, perspective)
                            )''')
            
            # Generate filename
            filename = f"{self.entity_data['name']}_{perspective}.png"
            
            # Insert or update image data
            cursor.execute('''INSERT OR REPLACE INTO entity_images 
                              (entity_name, perspective, image_data, filename) 
                              VALUES (?, ?, ?, ?)''', 
                          (self.entity_data['name'], perspective, self.image_data_store[cache_key], filename))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Image saved to database: {self.entity_data['name']}_{perspective}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image to database: {str(e)}")
    
    def show_unsupported_message(self, perspective):
        """Display unsupported generation message - All perspectives can now be generated after API update"""
        # Due to the new Qwen-Image-2512 model, all perspectives can now be generated
        # This method no longer needs to display unsupported messages
        pass

    def redraw_image(self, perspective):
        """Redraw a specific image on canvas"""
        try:
            entity_name = self.entity_data['name']
            cache_key = f"{entity_name}_{perspective}".replace(' ', '_')
            
            if (hasattr(self, 'image_data_store') and 
                cache_key in self.image_data_store and 
                self.image_data_store[cache_key] is not None):
                
                # Redraw the image from stored data
                image_data = self.image_data_store[cache_key]
                canvas = self.image_canvases[perspective]
                
                # Update canvas size to ensure proper width and height
                canvas.update_idletasks()
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                
                if canvas_width <= 1:  # If Canvas hasn't rendered, use default size
                    canvas_width = 500
                    canvas_height = 250
                
                # 创建唯一的临时文件名（包含实体名称和视角）
                temp_file = os.path.join(
                    os.path.dirname(__file__), 
                    '..', 
                    f'temp_image_{entity_name}_{perspective}.png'.replace(' ', '_').replace(':', '')
                )
                
                # Save image data to temporary file
                with open(temp_file, 'wb') as f:
                    f.write(image_data)
                
                # Load image from file
                photo = ImageTk.PhotoImage(file=temp_file)
                
                # 创建唯一的标签（包含实体名称和视角）
                image_tag = f'image_{entity_name}_{perspective}'.replace(' ', '_')
                
                # 删除当前Canvas上的所有旧图像（只删除本Canvas的内容）
                canvas.delete(image_tag)
                x_center = canvas_width // 2
                y_center = canvas_height // 2
                
                # Create image on canvas with specific tag
                canvas.create_image(x_center, y_center, image=photo, anchor=tk.CENTER, tags=image_tag)
                
                # Store image reference to prevent garbage collection
                if not hasattr(self, 'image_cache'):
                    self.image_cache = {}
                self.image_cache[cache_key] = photo
                
                # Also store the image in the canvas object to prevent garbage collection
                if not hasattr(canvas, 'images'):
                    canvas.images = {}
                canvas.images[cache_key] = photo
                
                # Clean up temporary file after displaying
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
                messagebox.showinfo("Success", f"Image refreshed for {perspective}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh image: {str(e)}")


class EntityGenerationWindow:
    """
    Entity Generation Window
    """
    
    def __init__(self, project_path):
        """Initialize entity generation window"""
        self.project_path = project_path
        self.root = tk.Tk()
        self.root.title("Entity Generation")
        self.root.geometry("1000x800")
        # Set window icon and style
        self.root.configure(bg="#f8f9fa")
        
        # Load API configuration
        self.api_config = self.load_api_config()
        
        # Load entity data
        self.entities = self.load_entities()
        
        self.setup_ui()
    
    def load_api_config(self):
        """Load API configuration"""
        try:
            # Load API configuration from project configuration file
            config_path = os.path.join(self.project_path, 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    project_config = json.load(f)
                return project_config.get('api_config', {})
        except Exception as e:
            print(f"Failed to load API configuration: {str(e)}")
        
        # Return default configuration
        return {
            "api_url": "",
            "api_key": "",
            "model": "dall-e-3"
        }
    
    def load_entities(self):
        """Load entities and prompts data from database"""
        entities = []
        try:
            # Connect to project database
            db_path = os.path.join(self.project_path, 'project.db')
            if not os.path.exists(db_path):
                print(f"Database file does not exist: {db_path}")
                return self.get_sample_entities()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Find all tables containing _prompts (these are prompt tables generated by story information extraction)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_prompts'")
            prompt_tables = cursor.fetchall()
            
            if not prompt_tables:
                print("No saved prompt data found")
                conn.close()
                return self.get_sample_entities()
            
            # Get data from all prompt tables
            for table_info in prompt_tables:
                table_name = table_info[0]
                # Remove '_prompts' suffix to get base table name, which usually corresponds to chapter name
                base_name = table_name.replace('_prompts', '')
                
                try:
                    # Query all prompts in this table
                    cursor.execute(f"SELECT entity_name, perspective, detailed_prompt, usage FROM `{table_name}`")
                    prompt_rows = cursor.fetchall()
                    
                    # Organize data by entity name
                    entities_dict = {}
                    for row in prompt_rows:
                        entity_name, perspective, detailed_prompt, usage = row
                        
                        if entity_name not in entities_dict:
                            entities_dict[entity_name] = {
                                "name": entity_name,
                                "prompts": {}
                            }
                        
                        # Use perspective as key to store detailed prompts
                        entities_dict[entity_name]["prompts"][perspective] = detailed_prompt
                    
                    # Add entity to total list
                    for entity in entities_dict.values():
                        # Check if already exists in entities list to avoid duplicates
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
        # Top frame
        top_frame = tk.Frame(self.root, bg="#f8f9fa", relief="raised", bd=1)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Title
        title_label = tk.Label(top_frame, text="Entity Generation", 
                               font=("Microsoft YaHei", 18, "bold"),
                               bg="#f8f9fa", fg="#495057")
        title_label.pack(pady=10)
        
        # Refresh button
        refresh_btn = tk.Button(top_frame, text="Refresh Entity Data", 
                                command=self.refresh_entities,
                                bg="#17a2b8", fg="white",
                                font=("Microsoft YaHei", 10),
                                relief="flat", bd=0, padx=10, pady=5)
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # Main content area - Using scrollable frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create Canvas and scrollbar
        canvas = tk.Canvas(main_frame, bg="#f8f9fa")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Place Canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel event
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        scrollable_frame.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Create card for each entity
        for entity_data in self.entities:
            card = EntityCard(scrollable_frame, entity_data, self.api_config, self.project_path)
            card.pack(fill=tk.X, pady=8, padx=5, ipadx=5, ipady=5)
    
    def refresh_entities(self):
        """Refresh entity data"""
        self.entities = self.load_entities()
        
        # Rebuild UI
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.setup_ui()
        
        # Redraw existing images on all cards after UI is rebuilt
        self.redraw_all_existing_images()

    def redraw_all_existing_images(self):
        """Redraw all existing images on all entity cards"""
        try:
            # Find all EntityCard widgets in the scrollable frame
            for child in self.root.winfo_children():
                if isinstance(child, tk.Frame):  # main_frame
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Canvas):  # canvas
                            # Get the scrollable frame
                            for canvas_child in grandchild.winfo_children():
                                if hasattr(canvas_child, 'winfo_children'):
                                    for card_widget in canvas_child.winfo_children():
                                        if 'EntityCard' in str(type(card_widget)):
                                            # Redraw existing images on this card
                                            if hasattr(card_widget, 'redraw_existing_images'):
                                                card_widget.redraw_existing_images()
        except Exception as e:
            print(f"Error redrawing all existing images: {str(e)}")

if __name__ == "__main__":
    # Test case - Assuming there is a project path
    project_path = "./test_project"  # Replace with actual project path
    app = EntityGenerationWindow(project_path)
    app.root.mainloop()