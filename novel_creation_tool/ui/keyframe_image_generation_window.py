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
import tempfile


class KeyframeCard(tk.Frame):
    """
    Keyframe card class, used to display information of a single keyframe
    """
    
    def __init__(self, parent, keyframe_data, api_config, project_path):
        """
        Initialize the keyframe card
        
        Args:
            parent: Parent component
            keyframe_data (dict): Keyframe data, including id and description
            api_config (dict): API configuration
            project_path (str): Project path
        """
        super().__init__(parent, relief="groove", borderwidth=2)
        self.keyframe_data = keyframe_data
        self.api_config = api_config
        self.project_path = project_path
        
        self.image_data = {}  # Store generated images
        
        # Create image cache to prevent garbage collection
        self.image_cache = {}
        
        # Create thread pool for image generation
        self.executor = ThreadPoolExecutor(max_workers=3)  # Max 3 simultaneous image generation tasks
        
        # Store thread pool tasks
        self.futures = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up keyframe card interface"""
        # Set card background color
        self.configure(bg="#ffffff", relief="solid", bd=1)
            
        # Keyframe ID label
        id_label = tk.Label(self, text=f"关键帧: {self.keyframe_data['keyframe_id']}", 
                              font=("Microsoft YaHei", 14, "bold"),
                              bg="#ffffff", fg="#212529", anchor="center")
        id_label.pack(fill=tk.X, padx=10, pady=(10, 15))
        
        # Create main frame, distribute description and images left and right
        main_frame = tk.Frame(self, bg="#ffffff")
        main_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Left description area
        desc_frame = tk.Frame(main_frame, bg="#ffffff", width=600)
        desc_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        desc_frame.pack_propagate(False)  # Fixed width
        
        # Right image display area
        image_area_frame = tk.Frame(main_frame, bg="#f8f9fa", relief="groove", bd=1)
        image_area_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create labels, buttons and image display areas for keyframe description
        # Top row: description label, copy button, generate button
        top_row_frame = tk.Frame(desc_frame, bg="#ffffff")
        top_row_frame.pack(fill=tk.X, pady=(0, 5))
                    
        # Copy button
        copy_btn = tk.Button(top_row_frame, text="复制", 
                             command=lambda d=self.keyframe_data['description']: self.copy_description(d),
                             bg="#007bff", fg="white",
                             font=("Microsoft YaHei", 9),
                             relief="flat", bd=0, padx=6, pady=4)
        copy_btn.pack(side=tk.RIGHT, padx=(0, 5))
                    
        # Description label
        desc_label = tk.Label(top_row_frame, text=f"描述: {self.keyframe_data['description']}",
                                font=("Microsoft YaHei", 10),
                                bg="#ffffff", fg="#495057",
                                wraplength=450, justify=tk.LEFT)
        desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
                    
        # Generate button
        generate_btn = tk.Button(top_row_frame, text="生成", 
                                 command=lambda: self.generate_image(self.keyframe_data['description']),
                                 bg="#28a745", fg="white",
                                 font=("Microsoft YaHei", 9),
                                 relief="flat", bd=0, padx=8, pady=4)
        generate_btn.pack(side=tk.RIGHT)
                    
        # Bottom row: style and ratio controls
        bottom_row_frame = tk.Frame(desc_frame, bg="#ffffff")
        bottom_row_frame.pack(fill=tk.X, pady=(5, 0))
                    
        # Style requirement input area
        style_frame = tk.Frame(bottom_row_frame, bg="#ffffff")
        style_frame.pack(fill=tk.X, pady=(0, 5))
                    
        style_label = tk.Label(style_frame, text="风格要求:",
                               font=("Microsoft YaHei", 9),
                               bg="#ffffff", fg="#6c757d")
        style_label.pack(side=tk.LEFT)
                    
        style_entry = tk.Entry(style_frame, font=("Microsoft YaHei", 9), width=30)
        style_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
                    
        # Store style input box reference
        self.style_entry = style_entry
                    
        # Image ratio selection area
        ratio_frame = tk.Frame(bottom_row_frame, bg="#ffffff")
        ratio_frame.pack(fill=tk.X, pady=(0, 5))
                    
        ratio_label = tk.Label(ratio_frame, text="图片比例:",
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
        self.ratio_var = ratio_var
        
        # Model selection dropdown
        model_label = tk.Label(ratio_frame, text="模型:",
                               font=("Microsoft YaHei", 9),
                               bg="#ffffff", fg="#6c757d")
        model_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Model options - include wan2.6-image model
        model_var = tk.StringVar(value="Auto")
        models = ["Auto", "Text-to-Image", "Image-to-Image", "Image-to-Image-Plus", "Text-to-Image-Plus", "wan2.6-image"]
        
        model_menu = tk.OptionMenu(ratio_frame, model_var, *models)
        model_menu.config(font=("Microsoft YaHei", 9), bg="#ffffff", fg="#495057")
        model_menu.pack(side=tk.LEFT, padx=(5, 0))
        
        # Store model variable reference
        self.model_var = model_var
        
        # Reference image upload button
        ref_upload_btn = tk.Button(ratio_frame, text="参考图上传", 
                                   command=self.upload_reference_images,
                                   bg="#ffc107", fg="#212529",
                                   font=("Microsoft YaHei", 9),
                                   relief="flat", bd=0, padx=6, pady=2)
        ref_upload_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Optimization button
        optimize_btn = tk.Button(ratio_frame, text="优化提示词", 
                                 command=self.optimize_prompt,
                                 bg="#6f42c1", fg="white",
                                 font=("Microsoft YaHei", 9),
                                 relief="flat", bd=0, padx=6, pady=2)
        optimize_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Image display area
        image_frame = tk.Frame(image_area_frame, bg="#f8f9fa", relief="groove", bd=1)
        image_frame.pack(fill=tk.X, padx=5, pady=5, ipadx=5, ipady=5)
            
        image_header = tk.Frame(image_frame, bg="#f8f9fa")
        image_header.pack(fill=tk.X, padx=5, pady=5)
            
        image_label = tk.Label(image_header, text=f"关键帧图片预览:", 
                               font=("Microsoft YaHei", 11, "bold"),
                               bg="#f8f9fa", fg="#495057")
        image_label.pack(side=tk.LEFT)
            
        # Add function buttons
        button_frame = tk.Frame(image_header, bg="#f8f9fa")
        button_frame.pack(side=tk.RIGHT)
        
        # Download button
        download_btn = tk.Button(button_frame, text="下载", 
                                command=self.download_image,
                                bg="#007bff", fg="white",
                                font=("Microsoft YaHei", 9),
                                relief="flat", bd=0, padx=6, pady=2)
        download_btn.pack(side=tk.LEFT, padx=2)
        
        # Fullscreen button
        fullscreen_btn = tk.Button(button_frame, text="全屏", 
                                  command=self.fullscreen_view,
                                  bg="#28a745", fg="white",
                                  font=("Microsoft YaHei", 9),
                                  relief="flat", bd=0, padx=6, pady=2)
        fullscreen_btn.pack(side=tk.LEFT, padx=2)
        
        # Refresh button
        refresh_btn = tk.Button(button_frame, text="刷新", 
                              command=self.redraw_image,
                              bg="#6c757d", fg="white",
                              font=("Microsoft YaHei", 9),
                              relief="flat", bd=0, padx=6, pady=2)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Save button
        save_btn = tk.Button(button_frame, text="保存", 
                            command=self.save_image_to_db,
                            bg="#ffc107", fg="#212529",
                            font=("Microsoft YaHei", 9),
                            relief="flat", bd=0, padx=6, pady=2)
        save_btn.pack(side=tk.LEFT, padx=2)
            
        # Canvas for displaying images
        canvas = tk.Canvas(image_frame, width=500, height=250, bg="#ffffff", relief="flat", bd=1)
        canvas.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
            
        # Store canvas reference for subsequent updates
        self.image_canvas = canvas
        
        # Store image data
        self.image_data_store = None
        
        # Bind more events to canvas to handle scrolling and display issues
        canvas.bind('<Visibility>', lambda e: self.ensure_image_displayed())
        canvas.bind('<Expose>', lambda e: self.ensure_image_displayed())

    def ensure_image_displayed(self):
        """Ensure image is displayed when Canvas becomes visible"""
        try:
            keyframe_id = self.keyframe_data['keyframe_id']
            cache_key = f"{keyframe_id}".replace(' ', '_')
            
            if (hasattr(self, 'image_data_store') and 
                self.image_data_store is not None):
                
                # Redraw the image
                self.redraw_image()
        except Exception as e:
            print(f"Error in ensure_image_displayed: {str(e)}")

    def upload_reference_images(self):
        """Upload reference images (up to 3)"""
        from tkinter import filedialog
        file_paths = filedialog.askopenfilenames(
            title="选择参考图片",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ],
            initialdir=os.getcwd()
        )
        
        if file_paths and len(file_paths) > 3:
            messagebox.showwarning("警告", "最多只能上传3张参考图片")
            return
            
        if file_paths:
            self.reference_images = []
            for file_path in file_paths:
                try:
                    # Load and store the image
                    with open(file_path, 'rb') as f:
                        image_data = f.read()
                    self.reference_images.append({
                        'path': file_path,
                        'data': image_data,
                        'base64': base64.b64encode(image_data).decode('utf-8')
                    })
                    messagebox.showinfo("成功", f"已上传 {len(file_paths)} 张参考图片")
                except Exception as e:
                    messagebox.showerror("错误", f"上传图片失败: {str(e)}")
    
    def optimize_prompt(self):
        """Optimize prompt using DeepSeek API"""
        try:
            # Get current description
            current_description = self.keyframe_data['description']
            
            # Call DeepSeek API to optimize the prompt
            headers = {
                "Authorization": "Bearer sk-5c447dcdbfdc45319954695e45179a29",
                "Content-Type": "application/json"
            }
            
            prompt = f"请优化以下提示词，使其更适合用于图片生成：{current_description}"
            
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
                optimized_prompt = response.json()["choices"][0]["message"]["content"]
                # Update the description label with the optimized prompt
                self.keyframe_data['description'] = optimized_prompt
                self.desc_label.config(text=f"描述: {optimized_prompt}")
                messagebox.showinfo("成功", "提示词已优化")
            else:
                messagebox.showerror("错误", f"优化失败: {response.status_code}")
                
        except Exception as e:
            messagebox.showerror("错误", f"优化提示词时出错: {str(e)}")

    def generate_image(self, description):
        """Generate image"""
        # Execute in new thread to avoid UI blocking
        canvas = self.image_canvas  # Pass canvas object for subsequent processing

        # Get the latest values from UI controls
        style_requirement = self.style_entry.get().strip()
        if style_requirement:
            description = f"{description}, Style requirement: {style_requirement}"

        # Submit task to thread pool
        future = self.executor.submit(self._generate_image_thread, description, canvas)
        # Store the Future object for management
        self.futures.append(future)
    
    def _generate_image_thread(self, description, canvas):
        """Generate image in background thread"""
        try:
            # Show loading status
            canvas.delete("all")
            loading_text = canvas.create_text(200, 100, text="Generating...", font=("Microsoft YaHei", 12), fill="gray")
                
            # Call API to generate image
            response = self.call_image_generation_api(description, canvas, loading_text)
                
            if response:
                # Display image data on Canvas
                self.display_image_on_canvas(response)
            else:
                canvas.delete("all")
                canvas.create_text(200, 100, text="Generation failed", font=("Microsoft YaHei", 12), fill="red")
                    
        except Exception as e:
            canvas.delete("all")
            canvas.create_text(200, 100, text=f"Error: {str(e)}", font=("Microsoft YaHei", 12), fill="red")
    
    def call_image_generation_api(self, description, canvas=None, loading_text=None):
        """Call image generation API - Using DashScope wan2.6-image model"""
        try:
            import requests
            import time
            import json
            from PIL import Image
            from io import BytesIO
            import base64
            import tempfile
            import os

            # Get current image ratio setting
            ratio = self.ratio_var.get()
            
            # Map aspect ratio to appropriate dimensions for DashScope
            dashscope_size_mapping = {
                '1:1': '1024*1024',
                '4:3': '1024*768',
                '3:2': '1024*682',
                '16:9': '1024*576',
                '9:16': '576*1024'
            }
            
            size_param = dashscope_size_mapping.get(ratio, '1024*1024')
            
            # Get the selected model from dropdown
            selected_model = self.model_var.get()

            # Determine which model to use based on user selection
            if selected_model == "wan2.6-image":
                # Use the wan2.6-image model with interleaved text and images
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer sk-912c798157c74fa5bb664325fc47f6eb",
                    "X-DashScope-Async": "enable"
                }
                
                # Prepare the input for the model
                content_list = [{"text": description}]
                
                # Add reference images if available
                if hasattr(self, 'reference_images') and self.reference_images:
                    # Add up to 3 reference images to the input
                    for i, ref_img in enumerate(self.reference_images[:3]):  # Limit to 3
                        content_list.append({"image": f"data:image/png;base64,{ref_img['base64']}"})
                        content_list.append({"text": f"参考图 {i+1}"})

                data = {
                    "model": "wan2.6-image",
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": content_list
                            }
                        ]
                    },
                    "parameters": {
                        "n": 1,
                        "size": size_param,
                        "enable_interleave": True
                    }
                }
                
                response = requests.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    task_id = response_data.get("output", {}).get("task_id")
                    
                    if task_id:
                        # Poll for the result
                        headers_get = {
                            "Authorization": f"Bearer sk-912c798157c74fa5bb664325fc47f6eb"
                        }
                        
                        while True:
                            result = requests.get(
                                f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
                                headers=headers_get
                            )
                            
                            if result.status_code == 200:
                                result_data = result.json()
                                
                                if result_data["output"]["task_status"] == "SUCCEEDED":
                                    # Get the image URL and download the image
                                    if "results" in result_data["output"] and len(result_data["output"]["results"]) > 0:
                                        image_url = result_data["output"]["results"][0]["url"]
                                        image_response = requests.get(image_url)
                                        
                                        if image_response.status_code == 200:
                                            return image_response.content
                                        else:
                                            print("Failed to download image from URL")
                                            return None
                                    else:
                                        print("No image results returned from API")
                                        return None
                                elif result_data["output"]["task_status"] == "FAILED":
                                    print("Image Generation Failed.")
                                    return None
                            
                            time.sleep(5)  # Wait 5 seconds before polling again
                    else:
                        print("No task ID returned from API")
                        return None
                else:
                    print(f"DashScope API Error - Status: {response.status_code}, Message: {response.text}")
                    return None
            else:
                # Use other models or fallback - reference entity generation approach
                # Upload reference images to HelloImg if using image-to-image
                uploaded_image_urls = []
                if hasattr(self, 'reference_images') and self.reference_images:
                    for ref_img in self.reference_images:
                        img_url = self.upload_to_helloimg(ref_img['data'])
                        if img_url:
                            uploaded_image_urls.append(img_url)

                # Use DashScope API for other models (similar to entity generation)
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer sk-912c798157c74fa5bb664325fc47f6eb"
                }
                
                # Map to DashScope size format
                dashscope_size_mapping = {
                    '1:1': '1024*1024',
                    '4:3': '1024*768',
                    '3:2': '1024*682',
                    '16:9': '1024*576',
                    '9:16': '576*1024'
                }
                
                size_param = dashscope_size_mapping.get(ratio, '1024*1024')

                # Determine model based on selection
                if selected_model in ["Text-to-Image", "Auto"]:
                    model_name = "wanx-v1"
                elif selected_model == "Image-to-Image":
                    model_name = "wanx-v1-img2img"  # Updated model for image-to-image
                elif selected_model == "Text-to-Image-Plus":
                    model_name = "wan2.5"
                elif selected_model == "Image-to-Image-Plus":
                    model_name = "wan2.5-img2img"
                else:  # Default to wanx-v1
                    model_name = "wanx-v1"

                # Prepare request data
                request_data = {
                    "model": model_name,
                    "input": {
                        "prompt": description,
                        "n": 1,
                        "size": size_param
                    }
                }
                
                # Add reference image if available and using image-to-image model
                if uploaded_image_urls and "img2img" in model_name:
                    # For image-to-image, we need to send the reference image
                    request_data["input"]["image_url"] = uploaded_image_urls[0]  # Use first reference image

                # Make the API call
                response = requests.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image_synthesis",
                    headers=headers,
                    json=request_data
                )

                if response.status_code == 200:
                    response_data = response.json()
                    
                    if response_data.get("code") == "Success":
                        # Get image from response
                        if "output" in response_data and "results" in response_data["output"]:
                            image_url = response_data["output"]["results"][0]["url"]
                            image_response = requests.get(image_url)
                            
                            if image_response.status_code == 200:
                                return image_response.content
                            else:
                                print("Failed to download image from URL")
                                return None
                        else:
                            print("No image results in response")
                            return None
                    else:
                        print(f"API Error: {response_data.get('message', 'Unknown error')}")
                        return None
                else:
                    print(f"API Request failed: {response.status_code} - {response.text}")
                    return None
                
        except Exception as e:
            print(f"API call exception: {str(e)}")
            return None

    def upload_to_helloimg(self, image_data):
        """Upload image to HelloImg and get URL using temporary token"""
        try:
            # Generate temporary upload token
            headers = {
                "Authorization": "Bearer 1497|DU1zdx63Vx5dsilGElFdD7tyqZ6pNvrDZSJGzbai",
                "Accept": "application/json"
            }
            
            token_data = {
                "num": 1,
                "seconds": 3600  # 1 hour validity
            }
            
            response = requests.post(
                "https://www.helloimg.com/api/v1/images/tokens",
                headers=headers,
                json=token_data
            )
            
            if response.status_code == 200:
                token_response = response.json()
                if token_response.get("status"):
                    temp_token = token_response["data"]["tokens"][0]["token"]
                    
                    # Upload the image using the temporary token
                    upload_headers = {
                        "Authorization": f"Bearer 1497|DU1zdx63Vx5dsilGElFdD7tyqZ6pNvrDZSJGzbai",
                        "Accept": "application/json"
                    }
                    
                    files = {
                        'file': ('reference_image.png', image_data, 'image/png')
                    }
                    
                    upload_response = requests.post(
                        "https://www.helloimg.com/api/v1/upload",
                        headers=upload_headers,
                        files=files,
                        data={'token': temp_token}
                    )
                    
                    if upload_response.status_code == 200:
                        upload_result = upload_response.json()
                        if upload_result.get("status"):
                            return upload_result["data"]["links"]["url"]
                        else:
                            print("Upload failed:", upload_result.get("message"))
                    else:
                        print(f"Upload request failed: {upload_response.status_code}")
                else:
                    print("Token generation failed:", token_response.get("message"))
            else:
                print(f"Token request failed: {response.status_code}")
        except Exception as e:
            print(f"Upload to HelloImg failed: {str(e)}")
        
        return None

    def display_image_on_canvas(self, image_data):
        """Display picture on Canvas - 修复版本 with auto-save and persistent rendering"""
        try:
            # Get current card's unique identifier (using keyframe id)
            keyframe_id = self.keyframe_data['keyframe_id']
            canvas = self.image_canvas
            
            # Update canvas size to ensure proper width and height
            canvas.update_idletasks()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width <= 1:  # If Canvas hasn't rendered, use default size
                canvas_width = 500
                canvas_height = 250
            
            # Create unique temporary filename (including keyframe id)
            temp_file = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                f'temp_image_{keyframe_id}.png'.replace(' ', '_').replace(':', '')
            )
            
            # Save image data to temporary file
            with open(temp_file, 'wb') as f:
                f.write(image_data)
            
            # Load image from file
            photo = ImageTk.PhotoImage(file=temp_file)
            
            # Create unique label (including keyframe id)
            image_tag = f'image_{keyframe_id}'.replace(' ', '_')
            
            # Delete all old images on current Canvas (only delete this Canvas's content)
            canvas.delete(image_tag)
            x_center = canvas_width // 2
            y_center = canvas_height // 2
            
            # Create image on canvas with specific tag
            canvas.create_image(x_center, y_center, image=photo, anchor=tk.CENTER, tags=image_tag)
            
            # Use more specific storage key to avoid cross-card conflicts
            cache_key = f"{keyframe_id}".replace(' ', '_')
            
            # Store image reference to prevent garbage collection
            if not hasattr(self, 'image_cache'):
                self.image_cache = {}
            self.image_cache[cache_key] = photo
            
            # Also store the image in the canvas object to prevent garbage collection
            if not hasattr(canvas, 'images'):
                canvas.images = {}
            canvas.images[cache_key] = photo
            
            # Store image data for download/save functionality
            self.image_data_store = image_data
            
            # Auto-save the image to the project's images folder
            self.auto_save_image(image_data, keyframe_id)
            
            # Bind configure event to re-render image when Canvas size changes
            canvas.bind('<Configure>', lambda e: self.on_canvas_configure())
            
            # Clean up temporary file after displaying
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
        except Exception as e:
            canvas = self.image_canvas
            canvas.delete("all")
            canvas.create_text(200, 100, text=f"Image display error: {str(e)}", font=("Microsoft YaHei", 12), fill="red")

    def on_canvas_configure(self):
        """Handle canvas resize/reconfigure events to maintain image display"""
        try:
            keyframe_id = self.keyframe_data['keyframe_id']
            cache_key = f"{keyframe_id}".replace(' ', '_')
            
            if (hasattr(self, 'image_data_store') and 
                self.image_data_store is not None):
                
                # Redraw the image from stored data
                image_data = self.image_data_store
                canvas = self.image_canvas
                
                # Update canvas size to ensure proper width and height
                canvas.update_idletasks()
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                
                if canvas_width <= 1:  # If Canvas hasn't rendered, use default size
                    canvas_width = 500
                    canvas_height = 250
                
                # Create unique temporary filename (including keyframe id)
                temp_file = os.path.join(
                    os.path.dirname(__file__), 
                    '..', 
                    f'temp_image_{keyframe_id}.png'.replace(' ', '_').replace(':', '')
                )
                
                # Save image data to temporary file
                with open(temp_file, 'wb') as f:
                    f.write(image_data)
                
                # Load image from file
                photo = ImageTk.PhotoImage(file=temp_file)
                
                # Create unique label (including keyframe id)
                image_tag = f'image_{keyframe_id}'.replace(' ', '_')
                
                # Delete all old images on current Canvas (only delete this Canvas's content)
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
            keyframe_id = self.keyframe_data['keyframe_id']
            cache_key = f"{keyframe_id}".replace(' ', '_')
            if (hasattr(self, 'image_data_store') and 
                self.image_data_store is not None):
                
                # Redraw the image from stored data
                image_data = self.image_data_store
                canvas = self.image_canvas
                
                # Update canvas size to ensure proper width and height
                canvas.update_idletasks()
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                
                if canvas_width <= 1:  # If Canvas hasn't rendered, use default size
                    canvas_width = 500
                    canvas_height = 250
                
                # Create unique temporary filename (including keyframe id)
                temp_file = os.path.join(
                    os.path.dirname(__file__), 
                    '..', 
                    f'temp_image_{keyframe_id}.png'.replace(' ', '_').replace(':', '')
                )
                
                # Save image data to temporary file
                with open(temp_file, 'wb') as f:
                    f.write(image_data)
                
                # Load image from file
                photo = ImageTk.PhotoImage(file=temp_file)
                
                # Create unique label (including keyframe id)
                image_tag = f'image_{keyframe_id}'.replace(' ', '_')
                
                # Delete all old images on current Canvas (only delete this Canvas's content)
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

    def auto_save_image(self, image_data, keyframe_id):
        """Auto-save generated image to project folder"""
        try:
            # Create images folder in project directory
            images_dir = os.path.join(self.project_path, 'generated_images')
            os.makedirs(images_dir, exist_ok=True)
            
            # Create unique filename using keyframe id and timestamp
            timestamp = int(time.time() * 1000)  # milliseconds since epoch
            filename = f"{keyframe_id}_{timestamp}.png".replace(' ', '_').replace(':', '')
            filepath = os.path.join(images_dir, filename)
            
            # Save image data to file
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
        except Exception as e:
            print(f"Failed to auto-save image: {str(e)}")

    def copy_description(self, description):
        """Copy description to clipboard"""
        try:
            self.clipboard_clear()  # Clear clipboard
            self.clipboard_append(description)  # Add description to clipboard
            messagebox.showinfo("Copy Success", "Description copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Copy Failed", f"Error occurred while copying description:\n{str(e)}")

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

    def download_image(self):
        """Download image to specified location"""
        # Use unique identifier to get image data
        if self.image_data_store is None:
            messagebox.showwarning("Warning", "No image to download")
            return
        
        from tkinter import filedialog
        # Open file save dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
            initialfile=f"{self.keyframe_data['keyframe_id']}.png"  # Use keyframe id as default filename
        )
        
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(self.image_data_store)
                messagebox.showinfo("Success", f"Image saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")

    def fullscreen_view(self):
        """View image in fullscreen"""
        # Use unique identifier to get image data
        if self.image_data_store is None:
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
            image_stream = io.BytesIO(self.image_data_store)
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

    def save_image_to_db(self):
        """Save image to database"""
        # Use unique identifier to get image data
        if self.image_data_store is None:
            messagebox.showwarning("Warning", "No image to save")
            return
        
        try:
            # Connect to project database
            import sqlite3
            db_path = os.path.join(self.project_path, 'project.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create image storage table (if not exists)
            cursor.execute('''CREATE TABLE IF NOT EXISTS keyframe_images (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                keyframe_id TEXT NOT NULL,
                                image_data BLOB NOT NULL,
                                filename TEXT,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(keyframe_id)
                            )''')
            
            # Generate filename
            filename = f"{self.keyframe_data['keyframe_id']}.png"
            
            # Insert or update image data
            cursor.execute('''INSERT OR REPLACE INTO keyframe_images 
                              (keyframe_id, image_data, filename) 
                              VALUES (?, ?, ?)''', 
                          (self.keyframe_data['keyframe_id'], self.image_data_store, filename))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Image saved to database: {self.keyframe_data['keyframe_id']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image to database: {str(e)}")
    
    def redraw_image(self):
        """Redraw the image on canvas"""
        try:
            keyframe_id = self.keyframe_data['keyframe_id']
            cache_key = f"{keyframe_id}".replace(' ', '_')
            
            if (hasattr(self, 'image_data_store') and 
                self.image_data_store is not None):
                
                # Redraw the image from stored data
                image_data = self.image_data_store
                canvas = self.image_canvas
                
                # Update canvas size to ensure proper width and height
                canvas.update_idletasks()
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                
                if canvas_width <= 1:  # If Canvas hasn't rendered, use default size
                    canvas_width = 500
                    canvas_height = 250
                
                # Create unique temporary filename (including keyframe id)
                temp_file = os.path.join(
                    os.path.dirname(__file__), 
                    '..', 
                    f'temp_image_{keyframe_id}.png'.replace(' ', '_').replace(':', '')
                )
                
                # Save image data to temporary file
                with open(temp_file, 'wb') as f:
                    f.write(image_data)
                
                # Load image from file
                photo = ImageTk.PhotoImage(file=temp_file)
                
                # Create unique label (including keyframe id)
                image_tag = f'image_{keyframe_id}'.replace(' ', '_')
                
                # Delete all old images on current Canvas (only delete this Canvas's content)
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
                    
                messagebox.showinfo("Success", f"Image refreshed for {keyframe_id}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh image: {str(e)}")


class KeyframeImageGenerationWindow:
    """
    Keyframe Image Generation Window
    """
    
    def __init__(self, project_path):
        """Initialize keyframe image generation window"""
        self.project_path = project_path
        self.root = tk.Tk()
        self.root.title("关键帧生图")
        self.root.geometry("1000x800")
        # Set window icon and style
        self.root.configure(bg="#f8f9fa")
        
        # Load API configuration
        self.api_config = self.load_api_config()
        
        # Load keyframe data
        self.keyframes = self.load_keyframes()
        
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
    
    def load_keyframes(self):
        """Load keyframe data from database"""
        keyframes = []
        try:
            # Connect to project database
            db_path = os.path.join(self.project_path, 'project.db')
            if not os.path.exists(db_path):
                print(f"Database file does not exist: {db_path}")
                return self.get_sample_keyframes()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Query keyframes from keyframes table
            cursor.execute("""
                SELECT keyframe_id, timestamp, description, composition, perspective, 
                       character_actions, emotion, camera_pose, lighting_changes, 
                       audio_hint, narration, music
                FROM keyframes
                ORDER BY shot_id, keyframe_number
            """)
            keyframe_rows = cursor.fetchall()
            
            if not keyframe_rows:
                print("No saved keyframe data found")
                conn.close()
                return self.get_sample_keyframes()
            
            # Process each keyframe
            for row in keyframe_rows:
                keyframe_data = {
                    "keyframe_id": row[0],
                    "timestamp": row[1],
                    "description": row[2],
                    "composition": row[3],
                    "perspective": row[4],
                    "character_actions": row[5],
                    "emotion": row[6],
                    "camera_pose": row[7],
                    "lighting_changes": row[8],
                    "audio_hint": row[9],
                    "narration": row[10],
                    "music": row[11]
                }
                
                keyframes.append(keyframe_data)
            
            conn.close()
            
            if not keyframes:
                print("No valid keyframe data found in database")
                return self.get_sample_keyframes()
            
        except Exception as e:
            print(f"Failed to load keyframe data: {str(e)}")
            return self.get_sample_keyframes()
        
        print(f"Loaded {len(keyframes)} keyframes from database")
        return keyframes
    
    def get_sample_keyframes(self):
        """Get sample keyframe data"""
        return [
            {
                "keyframe_id": "EP01_P01_S01_SH01_KF01",
                "timestamp": "0.0秒",
                "description": "镜头起始帧。广角远景展现埃索斯大陆东北荒原全景。灰白天空低垂，风沙在地表形成细微流动轨迹。天然石窟嵌于陡峭岩壁中，入口呈异常规整的长方形，边缘锐利如被巨力切割，与周围自然地貌形成强烈反差。远处稀疏植被在风中轻微摇曳。",
                "composition": "广角远景（焦距≈16mm），画面三分法：石窟位于右下交叉点，天际线压低以强调荒原压迫感。",
                "perspective": "无",
                "character_actions": "无具体人物，仅2–3个模糊人影从石窟入口缓慢进出，呈剪影状，动作迟缓而有序。",
                "emotion": "原始、肃穆、秩序初萌；带有神秘的非自然感。",
                "camera_pose": "固定机位，略带俯角（-5°），模拟\"神之视角\"审视人类早期聚居。",
                "lighting_changes": "自然天光漫射，整体冷调（色温≈7500K），石窟入口因背光形成深邃剪影，但边缘受侧光勾勒出微弱高光。",
                "audio_hint": "风声低鸣，夹杂细沙摩擦岩壁的窸窣声。",
                "narration": "",
                "music": ""
            }
        ]
    
    def setup_ui(self):
        """Set up main interface"""
        # Top frame
        top_frame = tk.Frame(self.root, bg="#f8f9fa", relief="raised", bd=1)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Title
        title_label = tk.Label(top_frame, text="关键帧生图", 
                               font=("Microsoft YaHei", 18, "bold"),
                               bg="#f8f9fa", fg="#495057")
        title_label.pack(pady=10)
        
        # Refresh button
        refresh_btn = tk.Button(top_frame, text="刷新关键帧数据", 
                                command=self.refresh_keyframes,
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
        
        # Create card for each keyframe
        for keyframe_data in self.keyframes:
            card = KeyframeCard(scrollable_frame, keyframe_data, self.api_config, self.project_path)
            card.pack(fill=tk.X, pady=8, padx=5, ipadx=5, ipady=5)
    
    def refresh_keyframes(self):
        """Refresh keyframe data"""
        self.keyframes = self.load_keyframes()
        
        # Rebuild UI
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.setup_ui()
        
        # Redraw existing images on all cards after UI is rebuilt
        self.redraw_all_existing_images()

    def redraw_all_existing_images(self):
        """Redraw all existing images on all keyframe cards"""
        try:
            # Find all KeyframeCard widgets in the scrollable frame
            for child in self.root.winfo_children():
                if isinstance(child, tk.Frame):  # main_frame
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Canvas):  # canvas
                            # Get the scrollable frame
                            for canvas_child in grandchild.winfo_children():
                                if hasattr(canvas_child, 'winfo_children'):
                                    for card_widget in canvas_child.winfo_children():
                                        if 'KeyframeCard' in str(type(card_widget)):
                                            # Redraw existing images on this card
                                            if hasattr(card_widget, 'redraw_existing_images'):
                                                card_widget.redraw_existing_images()
        except Exception as e:
            print(f"Error redrawing all existing images: {str(e)}")

if __name__ == "__main__":
    # Test case - Assuming there is a project path
    project_path = "./test_project"  # Replace with actual project path
    app = KeyframeImageGenerationWindow(project_path)
    app.root.mainloop()