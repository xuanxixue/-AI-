"""
使用wxPython运行小说创作辅助工具
包含实体生成窗口的wxPython版本
"""

import wx
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from novel_creation_tool.ui.entity_generation_window_wx import EntityGenerationWindow


def run_entity_generation_app(project_path=None):
    """
    运行实体生成应用程序的wxPython版本
    
    Args:
        project_path (str): 项目路径，如果为None则使用默认测试路径
    """
    if project_path is None:
        # 使用测试项目路径
        project_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_project")
    
    # 检查项目路径是否存在
    if not os.path.exists(project_path):
        print(f"项目路径不存在: {project_path}")
        # 尝试创建测试项目目录
        try:
            os.makedirs(project_path, exist_ok=True)
            config_path = os.path.join(project_path, 'config.json')
            if not os.path.exists(config_path):
                import json
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'name': 'Test Project',
                        'path': project_path,
                        'created_at': '2024-01-01T00:00:00',
                        'updated_at': '2024-01-01T00:00:00',
                        'version': '1.0',
                        'api_config': {
                            'api_url': '',
                            'api_key': '',
                            'model': 'dall-e-3'
                        }
                    }, f, ensure_ascii=False, indent=2)
            print(f"已创建测试项目: {project_path}")
        except Exception as e:
            print(f"创建测试项目失败: {e}")
            return
    
    # 创建并运行实体生成窗口
    print("启动实体生成窗口 (wxPython版本)...")
    app = EntityGenerationWindow(project_path)
    app.show()


def main():
    """主函数"""
    print("启动小说创作辅助工具 (wxPython版本)...")
    
    # 可以从命令行参数获取项目路径
    project_path = None
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    
    run_entity_generation_app(project_path)


if __name__ == "__main__":
    main()