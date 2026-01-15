import tkinter as tk
from PIL import Image, ImageTk
from io import BytesIO
import requests

# 创建测试窗口
test_root = tk.Tk()
test_root.title("图片显示测试")
test_root.geometry("500x400")

def test_image_display():
    # 下载测试图片
    image_url = "https://modelscope.oss-cn-beijing.aliyuncs.com/Dog.png"
    response = requests.get(image_url)
    if response.status_code == 200:
        # 将字节数据转换为PIL Image
        image_stream = BytesIO(response.content)
        pil_image = Image.open(image_stream)
        
        # 调整图片大小
        canvas_width = 400
        canvas_height = 300
        img_width, img_height = pil_image.size
        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height
        scale = min(scale_w, scale_h, 1.0)  # 不放大原图
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # 调整图片大小
        resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 转换为PhotoImage对象
        photo = ImageTk.PhotoImage(resized_image)
        
        # 创建Canvas显示图片
        canvas = tk.Canvas(test_root, width=canvas_width, height=canvas_height, bg="white")
        canvas.pack(pady=10)
        
        # 在Canvas上显示图片
        x_center = canvas_width // 2
        y_center = canvas_height // 2
        canvas.create_image(x_center, y_center, image=photo, anchor=tk.CENTER)
        
        # 保存对图片的引用，防止被垃圾回收
        if not hasattr(canvas, 'image_ref'):
            canvas.image_ref = []
        canvas.image_ref.append(photo)
        
        print("图片显示成功！")
    else:
        print("下载图片失败")

# 运行测试
test_image_display()

test_root.mainloop()