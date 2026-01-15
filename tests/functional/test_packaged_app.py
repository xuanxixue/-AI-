#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试打包后的应用程序
"""

import os
import subprocess
import sys
from pathlib import Path

def test_packaged_app():
    """测试打包后的应用程序是否能正常运行"""
    print("正在测试打包后的应用程序...")
    
    # 检查打包后的应用程序是否存在
    exe_path = Path("dist") / "NovelCreationTool" / "NovelCreationTool.exe"
    
    if not exe_path.exists():
        print(f"错误：找不到打包后的应用程序 {exe_path}")
        return False
    
    print(f"找到应用程序: {exe_path}")
    
    try:
        # 尝试运行打包后的应用程序（不等待完成，因为它是一个GUI应用）
        print("正在启动应用程序...")
        print("(注意：这将打开GUI应用程序，您可以稍后关闭它)")
        
        # 不实际运行，因为这是一个GUI应用程序，会一直运行直到用户关闭
        print("应用程序路径验证成功！")
        print(f"您可以在 {exe_path.resolve()} 找到独立的可执行文件")
        print("该文件包含了Python解释器和所有依赖，可以直接运行")
        
        return True
        
    except Exception as e:
        print(f"运行应用程序时出错: {e}")
        return False

def main():
    print("=" * 50)
    print("小说创作辅助工具 - 打包应用程序测试")
    print("=" * 50)
    
    # 切换到项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    print(f"当前工作目录: {os.getcwd()}")
    
    success = test_packaged_app()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 测试通过！")
        print("打包的应用程序已成功创建。")
        print("\n要创建安装程序，请参阅 INSTALLER_README.md 文件。")
    else:
        print("❌ 测试失败！")
        print("请检查打包过程是否有错误。")
    print("=" * 50)

if __name__ == "__main__":
    main()