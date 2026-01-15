#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说创作辅助工具打包脚本
用于将Python应用程序打包成独立的exe可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """安装PyInstaller和其他必要依赖"""
    print("正在安装PyInstaller及相关依赖...")
    
    # 检查是否已安装PyInstaller
    try:
        import PyInstaller
        print("PyInstaller 已安装")
    except ImportError:
        print("PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 安装其他必要的依赖
    requirements_path = "requirements.txt"
    if os.path.exists(requirements_path):
        print("正在安装项目依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
    else:
        print("未找到requirements.txt文件")

def create_icon_if_not_exists():
    """如果不存在图标文件，创建一个默认图标或跳过图标设置"""
    icon_path = "icon.ico"
    if not os.path.exists(icon_path):
        print("未找到图标文件 icon.ico，将在打包时跳过图标设置")
        # 修改spec文件以移除图标引用
        spec_file = "NovelCreationTool.spec"
        if os.path.exists(spec_file):
            with open(spec_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 移除图标设置
            content = content.replace(", icon='icon.ico'", "")
            content = content.replace("icon='icon.ico', ", "")
            content = content.replace("icon='icon.ico'", "")
            
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return False
    return True

def build_application():
    """构建应用程序"""
    print("开始构建应用程序...")
    
    # 检查spec文件是否存在
    spec_file = "NovelCreationTool.spec"
    if not os.path.exists(spec_file):
        print("错误：找不到spec文件 NovelCreationTool.spec")
        return False
    
    try:
        # 运行PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", spec_file]
        print(f"执行命令: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        print("应用程序构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建过程中出现错误: {e}")
        return False

def create_installer():
    """创建安装程序（使用Inno Setup）"""
    print("创建安装程序...")
    
    installer_script = """
; 小说创作辅助工具安装脚本
[Setup]
AppName=小说创作辅助工具
AppVersion=1.0.0
DefaultDirName={autopf}\\小说创作辅助工具
DefaultGroupName=小说创作辅助工具
OutputBaseFilename=小说创作辅助工具安装程序
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
OutputDir=.

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\\NovelCreationTool\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\\小说创作辅助工具"; Filename: "{app}\\NovelCreationTool.exe"
Name: "{commondesktop}\\小说创作辅助工具"; Filename: "{app}\\NovelCreationTool.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "在桌面创建快捷方式"; GroupDescription: "附加任务："

[Run]
Filename: "{app}\\NovelCreationTool.exe"; Description: "启动小说创作辅助工具"; Flags: nowait postinstall skipifsilent
"""
    
    with open("setup_script.iss", "w", encoding='utf-8-sig') as f:
        f.write(installer_script)
    
    print("安装程序脚本已创建 (setup_script.iss)")
    print("\n注意：要创建最终的安装程序，请安装Inno Setup后运行:")
    print("  iscc setup_script.iss")
    print("\n或者您可以手动运行Inno Setup编译器来生成安装程序。")

def main():
    """主函数"""
    print("=" * 50)
    print("小说创作辅助工具打包程序")
    print("=" * 50)
    
    # 切换到项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    print(f"当前工作目录: {os.getcwd()}")
    
    # 步骤1: 安装依赖
    print("\n步骤1: 安装依赖")
    install_pyinstaller()
    
    # 步骤2: 处理图标
    print("\n步骤2: 处理图标文件")
    create_icon_if_not_exists()
    
    # 步骤3: 构建应用程序
    print("\n步骤3: 构建应用程序")
    if not build_application():
        print("构建失败，退出。")
        sys.exit(1)
    
    # 步骤4: 创建安装程序脚本
    print("\n步骤4: 创建安装程序")
    create_installer()
    
    print("\n" + "=" * 50)
    print("打包完成！")
    print("\n生成的文件说明:")
    print("- dist/NovelCreationTool/: 可独立运行的exe文件夹")
    print("- NovelCreationTool.exe: 主程序文件")
    print("- setup_script.iss: Inno Setup安装脚本")
    print("\n要创建安装程序，请使用Inno Setup编译setup_script.iss文件")
    print("=" * 50)

if __name__ == "__main__":
    main()