"""
测试实体生成窗口的新功能
包括下载、全屏查看、保存到数据库、自动保存、重新绘制、刷新和持久显示功能
"""

import sys
import os

def test_wx_version():
    """测试wxPython版本"""
    print("测试wxPython版本...")
    try:
        from novel_creation_tool.ui.entity_generation_window_wx import EntityCard
        print("✓ wxPython版本导入成功")
        
        # 检查新添加的方法是否存在
        methods = ['download_image', 'fullscreen_view', 'save_image_to_db', 'auto_save_image', 'redraw_existing_images', 'redraw_image', 'ensure_image_displayed', 'on_panel_paint']
        for method in methods:
            if hasattr(EntityCard, method):
                print(f"✓ 方法 {method} 已添加")
            else:
                print(f"✗ 方法 {method} 未找到")
        
        print("wxPython版本测试完成\n")
    except Exception as e:
        print(f"✗ wxPython版本测试失败: {e}\n")


def test_tkinter_version():
    """测试tkinter版本"""
    print("测试tkinter版本...")
    try:
        from novel_creation_tool.ui.entity_generation_window import EntityCard
        print("✓ tkinter版本导入成功")
        
        # 检查新添加的方法是否存在
        methods = ['download_image', 'fullscreen_view', 'save_image_to_db', 'auto_save_image', 'redraw_existing_images', 'redraw_image', 'ensure_image_displayed', 'on_canvas_configure']
        for method in methods:
            if hasattr(EntityCard, method):
                print(f"✓ 方法 {method} 已添加")
            else:
                print(f"✗ 方法 {method} 未找到")
        
        print("tkinter版本测试完成\n")
    except Exception as e:
        print(f"✗ tkinter版本测试失败: {e}\n")


if __name__ == "__main__":
    print("开始测试实体生成窗口的新功能...\n")
    
    test_wx_version()
    test_tkinter_version()
    
    print("所有测试完成！")