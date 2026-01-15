"""
测试API配置对话框的完整功能
"""
import tkinter as tk
from tkinter import messagebox
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from ui.api_config_dialog import show_api_config_dialog
from utils.config_manager import config_manager

def test_api_config_comprehensive():
    """全面测试API配置功能"""
    print("=== 开始全面测试API配置功能 ===")
    
    # 显示当前API密钥
    current_key = config_manager.get_api_key()
    print(f"当前API密钥: {'已保存' if current_key else '未保存'}")
    if current_key:
        print(f"API密钥长度: {len(current_key)} 字符")
        print(f"API密钥前缀: {current_key[:20]}...")
    
    # 创建测试窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口，因为我们只做自动测试
    
    # 测试1: 验证保存和读取功能
    print("\n--- 测试1: 验证保存和读取功能 ---")
    
    # 保存一个测试密钥
    test_api_key = "sk-test1234567890abcdef"
    config_manager.set_api_key(test_api_key)
    
    # 读取刚保存的密钥
    retrieved_key = config_manager.get_api_key()
    if retrieved_key == test_api_key:
        print("✓ 保存和读取功能正常工作")
    else:
        print("✗ 保存和读取功能存在问题")
    
    # 测试2: 验证配置文件是否正确写入
    print("\n--- 测试2: 验证配置文件写入 ---")
    config_file_path = os.path.join(os.getcwd(), 'config.json')
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            if 'api_key' in config_data and config_data['api_key'] == test_api_key:
                print("✓ 配置文件写入正常")
            else:
                print("✗ 配置文件写入存在问题")
        except Exception as e:
            print(f"✗ 读取配置文件时出错: {e}")
    else:
        print("✗ 配置文件不存在")
    
    # 测试3: 验证清空功能
    print("\n--- 测试3: 验证清空功能 ---")
    config_manager.set_api_key("")
    empty_key = config_manager.get_api_key()
    if empty_key == "":
        print("✓ 清空功能正常工作")
    else:
        print("✗ 清空功能存在问题")
    
    # 测试4: 恢复原始API密钥
    print("\n--- 测试4: 恢复原始API密钥 ---")
    if current_key:  # 如果原来有密钥，则恢复
        config_manager.set_api_key(current_key)
        restored_key = config_manager.get_api_key()
        if restored_key == current_key:
            print("✓ 原始API密钥已恢复")
        else:
            print("✗ 原始API密钥恢复失败")
    
    print("\n=== API配置功能全面测试完成 ===")
    
    root.destroy()

if __name__ == "__main__":
    test_api_config_comprehensive()