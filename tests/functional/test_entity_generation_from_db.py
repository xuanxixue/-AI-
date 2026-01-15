#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试实体生成窗口 - 从数据库加载数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    from novel_creation_tool.ui.entity_generation_window_wx import EntityGenerationWindow
except ImportError:
    # 如果wxPython版本不可用，则回退到tkinter版本
    from novel_creation_tool.ui.entity_generation_window import EntityGenerationWindow

def main():
    print("启动实体生成窗口测试（从数据库加载数据）...")
    
    # 使用测试项目路径
    project_path = os.path.join(os.path.dirname(__file__), "test_project")
    
    # 检查项目路径是否存在
    if not os.path.exists(project_path):
        print(f"项目路径不存在: {project_path}")
        return
    
    # 创建并启动实体生成窗口
    app = EntityGenerationWindow(project_path)
    print("实体生成窗口已创建，现在启动主循环...")
    
    try:
        # 检查是否是wxPython版本
        if hasattr(app, 'show'):
            # wxPython版本
            app.show()
        else:
            # tkinter版本
            app.root.mainloop()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()