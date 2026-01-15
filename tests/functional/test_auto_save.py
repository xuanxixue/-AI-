"""
测试实体生成窗口的自动保存功能
"""
import os
import sys
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_auto_save_feature():
    """测试自动保存功能"""
    print("开始测试自动保存功能...")
    
    # 创建临时项目目录进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"使用临时目录: {temp_dir}")
        
        # 测试tkinter版本
        try:
            from novel_creation_tool.ui.entity_generation_window import EntityCard as TkEntityCard
            import tkinter as tk
            
            tk_root = tk.Tk()
            tk_root.withdraw()  # 隐藏主窗口
            
            tk_entity_data = {
                'name': 'AutoSave Test Entity', 
                'prompts': {'front': 'test prompt for auto save'}
            }
            tk_api_config = {}
            
            # 创建实体卡片
            tk_card = TkEntityCard(tk_root, tk_entity_data, tk_api_config, temp_dir)
            
            # 模拟图片数据
            dummy_image_data = b'dummy image data for testing auto save functionality'
            tk_card.auto_save_image(dummy_image_data, 'front')
            
            # 检查图片是否已保存
            image_dir = os.path.join(temp_dir, 'generated_images')
            expected_file = os.path.join(image_dir, 'AutoSave_Test_Entity_front.png')
            
            if os.path.exists(expected_file):
                print("✓ tkinter版本自动保存功能工作正常")
                # 读取并验证内容
                with open(expected_file, 'rb') as f:
                    saved_data = f.read()
                    if saved_data == dummy_image_data:
                        print("✓ 保存的图片数据正确")
                    else:
                        print("✗ 保存的图片数据不正确")
            else:
                print("✗ tkinter版本自动保存功能未正常工作")
            
            tk_root.destroy()
            
        except Exception as e:
            print(f"✗ tkinter版本测试出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试wxPython版本
        try:
            from novel_creation_tool.ui.entity_generation_window_wx import EntityCard as WxEntityCard
            import wx
            
            wx_app = wx.App()
            wx_frame = wx.Frame(None)
            
            wx_entity_data = {
                'name': 'AutoSave Test Entity', 
                'prompts': {'front': 'test prompt for auto save'}
            }
            wx_api_config = {}
            
            # 创建实体卡片
            wx_card = WxEntityCard(wx_frame, wx_entity_data, wx_api_config, temp_dir)
            
            # 模拟图片数据
            dummy_image_data = b'dummy image data for testing auto save functionality'
            wx_card.auto_save_image(dummy_image_data, 'front')
            
            # 检查图片是否已保存
            image_dir = os.path.join(temp_dir, 'generated_images')
            expected_file = os.path.join(image_dir, 'AutoSave_Test_Entity_front.png')
            
            if os.path.exists(expected_file):
                print("✓ wxPython版本自动保存功能工作正常")
                # 读取并验证内容
                with open(expected_file, 'rb') as f:
                    saved_data = f.read()
                    if saved_data == dummy_image_data:
                        print("✓ 保存的图片数据正确")
                    else:
                        print("✗ 保存的图片数据不正确")
            else:
                print("✗ wxPython版本自动保存功能未正常工作")
            
            wx_frame.Destroy()
            
        except Exception as e:
            print(f"✗ wxPython版本测试出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("自动保存功能测试完成")


if __name__ == "__main__":
    test_auto_save_feature()