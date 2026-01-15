# 项目结构说明

## 整理后的项目结构

```
动慢工具/
├── assets/
│   └── images/                    # 存放所有图片资源
├── docs/                         # 文档目录
│   ├── api/                      # API相关文档
│   ├── guides/                   # 指南和说明文档
│   │   ├── INSTALLER_README.md   # 安装程序说明
│   │   └── 打包总结.txt          # 打包总结报告
│   └── specs/                    # 规范和配置文件
│       ├── config.json           # 主配置文件
│       └── projects.db           # 项目数据库
├── novel_creation_tool/          # 主要源代码目录
│   ├── ui/                      # UI相关模块
│   ├── utils/                   # 工具类模块
│   ├── __init__.py
│   ├── config.json
│   ├── database.py
│   ├── main.py                  # 主程序入口
│   ├── project_manager.py
│   ├── requirements.txt         # 依赖声明
│   ├── simple_gui.py            # GUI实现
│   └── ...                      # 其他源代码文件
├── src/                          # 源代码目录
│   └── app/
│       └── ui/                   # UI组件
├── tests/                        # 测试文件目录
│   ├── integration/             # 集成测试
│   ├── unit/                    # 单元测试
│   └── functional/              # 功能测试
│       ├── test_api_config.py
│       ├── test_api_config_full.py
│       ├── test_entity_generation_from_db.py
│       ├── test_fixed_keyframe_gen.py
│       ├── test_image_display.py
│       ├── test_image_display_final.py
│       ├── test_integration.py
│       ├── test_outline_parsing.py
│       ├── test_outline_understanding.py
│       ├── test_packaged_app.py
│       ├── test_shot_split_fix.py
│       └── ...                  # 其他测试文件
├── temp_files/                   # 临时和缓存文件目录
│   ├── __pycache__/             # Python缓存目录
│   ├── build/                   # 构建产物
│   ├── dist/                    # 打包产物
│   ├── generated_images/        # 生成的图片
│   ├── test_auto_save/          # 自动保存测试目录
│   ├── test_auto_save2/         # 自动保存测试目录2
│   ├── test_project/            # 测试项目目录
│   ├── test_redraw_functionality/  # 重绘功能测试
│   └── test_refresh_functionality/ # 刷新功能测试
├── start_app.bat                # 启动脚本
├── start_wx_app.bat             # WX启动脚本
└── PROJECT_STRUCTURE.md         # 项目结构说明
```

## 整理说明

1. **assets/images/** - 集中存放所有图像资源，便于管理和维护
2. **docs/** - 文档统一存放位置，按类型分为api、guides和specs子目录
3. **novel_creation_tool/** - 保持原有的主要源代码结构不变
4. **src/app/ui/** - 已有的整理好的UI源代码
5. **tests/** - 所有测试文件按类型分类存放
6. **temp_files/** - 临时文件、缓存和生成的文件统一存放

## 特点

- 保持原有项目的核心结构不变
- 将临时和生成的文件集中管理
- 将文档和配置文件分类存放
- 便于后续维护和开发
- 所有文件均保留，无删除操作