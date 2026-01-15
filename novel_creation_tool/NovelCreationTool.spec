# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for Novel Creation Tool
"""

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集所有ui子模块
ui_modules = collect_submodules('ui')
data_files = collect_data_files('ui')

# 收集所有utils子模块
util_modules = collect_submodules('utils')
data_files += collect_data_files('utils')

# 排除不需要的模块以减小包大小
excluded_modules = [
    'matplotlib', 'numpy', 'scipy', 'pandas',  # 数值计算库
    'tensorflow', 'torch',  # 深度学习库
    'pygame',  # 游戏库
    'tkinter.test',  # tkinter测试模块
    'unittest',  # 单元测试模块
    'PyQt5', 'PyQt4', 'PySide2', 'PySide6',  # 排除Qt相关库，因为应用使用tkinter
    'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',  # 具体的Qt模块
]

block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # 包含所有UI模块的数据文件
        ('ui', 'ui'),
        ('utils', 'utils'),
        # 包含可能的配置文件
        ('config.json', '.'),
    ],
    hiddenimports=['ui.main_window', 'ui.function_panel', 'ui.outline_understanding_window', 'ui.idea_extraction_window', 'ui.outline_generation_window', 'ui.chapter_generation_window', 'ui.story_extraction_window', 'ui.entity_generation_window', 'ui.entity_generation_window_wx', 'ui.api_config_dialog', 'ui.story_segmentation_window', 'ui.story_segmentation_window_wx', 'ui.scene_segmentation_window', 'ui.shot_split_window', 'ui.keyframe_split_window', 'ui.keyframe_image_generation_window', 'utils.config_manager'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NovelCreationTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
     # 如果有图标文件的话
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NovelCreationTool',
)