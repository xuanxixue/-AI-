"""
测试API配置功能
"""
import tkinter as tk
from tkinter import messagebox
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from ui.api_config_dialog import show_api_config_dialog
from utils.config_manager import config_manager

def test_api_config():
    """测试API配置功能"""
    print("开始测试API配置功能...")
    
    # 创建一个简单的Tkinter窗口来测试API配置对话框
    root = tk.Tk()
    root.title("API配置功能测试")
    root.geometry("400x300")
    
    def open_api_config():
        """打开API配置对话框"""
        show_api_config_dialog(root)
        # 显示当前保存的API密钥
        saved_key = config_manager.get_api_key()
        if saved_key:
            print(f"当前保存的API密钥前缀: {saved_key[:10]}..." if len(saved_key) > 10 else f"当前保存的API密钥: {saved_key}")
            messagebox.showinfo("API密钥", f"API密钥已保存（长度: {len(saved_key)} 字符）")
        else:
            print("当前没有保存API密钥")
            messagebox.showinfo("API密钥", "当前没有保存API密钥")
    
    def test_api_connection():
        """测试API连接"""
        api_key = config_manager.get_api_key()
        if not api_key:
            messagebox.showwarning("警告", "请先配置API密钥")
            return
            
        print("正在测试API连接...")
        # 导入并测试API连接
        try:
            import requests
            # 尝试进行一个简单的API请求以验证API密钥是否有效
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送一个简单的请求来测试API连接
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": "Hello, are you available?"}
                ],
                "temperature": 0.7,
                "max_tokens": 10  # 限制响应大小以快速测试
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10  # 10秒超时
            )
            
            if response.status_code == 200:
                # 验证返回的数据是否包含预期内容
                try:
                    response_data = response.json()
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        print("✓ API连接测试成功! API密钥有效")
                        messagebox.showinfo("API连接测试", "API连接成功! API密钥有效")
                    else:
                        print("✗ API密钥可能无效 - 响应格式不正确")
                        messagebox.showerror("API连接测试", "API密钥可能无效 - 响应格式不正确")
                except ValueError:
                    print("✗ API密钥无效 - 无法解析响应")
                    messagebox.showerror("API连接测试", "API密钥无效 - 无法解析响应")
            elif response.status_code == 401:
                print("✗ API密钥无效或已过期")
                messagebox.showerror("API连接测试", "API密钥无效或已过期")
            elif response.status_code == 403:
                print("✗ API密钥已被禁用或超出配额")
                messagebox.showerror("API连接测试", "API密钥已被禁用或超出配额")
            elif response.status_code == 429:
                print("✗ API请求频率过高")
                messagebox.showwarning("API连接测试", "API请求频率过高，请稍后再试")
            else:
                print(f"✗ API连接失败，状态码: {response.status_code}")
                messagebox.showerror("API连接测试", f"API连接失败，状态码: {response.status_code}\n详情: {response.text[:100]}...")
                
        except requests.exceptions.Timeout:
            print("✗ API连接超时")
            messagebox.showerror("API连接测试", "API连接超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            print("✗ 网络连接错误")
            messagebox.showerror("API连接测试", "无法连接到API服务器，请检查网络连接")
        except Exception as e:
            print(f"✗ API连接测试出错: {str(e)}")
            messagebox.showerror("API连接测试", f"API连接测试出错: {str(e)}")
    
    # 创建测试按钮
    tk.Button(root, text="打开API配置", command=open_api_config, height=2, width=20).pack(pady=10)
    tk.Button(root, text="测试API连接", command=test_api_connection, height=2, width=20).pack(pady=10)
    
    # 显示当前API密钥状态
    current_key = config_manager.get_api_key()
    status_text = f"当前API密钥状态: {'已配置' if current_key else '未配置'}"
    if current_key:
        status_text += f"\nAPI密钥长度: {len(current_key)} 字符"
    
    tk.Label(root, text=status_text, font=("Arial", 10)).pack(pady=10)
    
    print("API配置功能测试界面已打开")
    root.mainloop()

if __name__ == "__main__":
    test_api_config()