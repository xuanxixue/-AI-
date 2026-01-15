import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'novel_creation_tool'))

from novel_creation_tool.ui.keyframe_image_generation_window import KeyframeImageGenerationWindow

# 测试关键帧生图窗口
if __name__ == "__main__":
    # 使用测试项目路径
    test_project_path = "./test_project"
    
    # 确保测试目录存在
    if not os.path.exists(test_project_path):
        os.makedirs(test_project_path, exist_ok=True)
    
    # 创建关键帧生图窗口
    app = KeyframeImageGenerationWindow(test_project_path)
    
    print("关键帧生图窗口已启动")
    app.root.mainloop()