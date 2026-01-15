import sqlite3
import os

def verify_outline_format(project_path):
    """
    验证生成的大纲是否符合指定格式
    """
    db_path = os.path.join(project_path, 'project.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询最新的大纲记录
        cursor.execute("SELECT id, title, content, source_info, created_at FROM generated_outlines ORDER BY created_at DESC LIMIT 1")
        record = cursor.fetchone()
        
        if not record:
            print("没有找到生成的大纲记录")
            conn.close()
            return False
        
        record_id, title, content, source_info, created_at = record
        print(f"找到大纲记录:")
        print(f"ID: {record_id}")
        print(f"标题: {title}")
        print(f"来源: {source_info}")
        print(f"创建时间: {created_at}")
        print("-" * 50)
        
        # 验证大纲格式是否符合要求
        print("验证大纲格式是否符合要求...")
        
        # 检查是否包含关键部分
        checks = {
            "包含小说标题": "小说标题" in content,
            "包含核心设定": "核心设定" in content,
            "包含背景信息": "背景：" in content,
            "包含男女主角": "男主：" in content or "女主：" in content,
            "包含关键意象": "关键意象" in content,
            "包含分部分结构": "【第一部分" in content or "【第二部分" in content or "【第三部分" in content,
            "包含章节划分": "第1章" in content or "第" in content and "章" in content,
            "包含情感标记": "✨" in content or "💔" in content or "🔪" in content or "🌸" in content,
            "包含风格说明": "风格说明" in content
        }
        
        print("\n格式验证结果:")
        all_passed = True
        for check_desc, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"{status} {check_desc}: {passed}")
            if not passed:
                all_passed = False
        
        print("-" * 50)
        print(f"总体结果: {'✓ 全部符合' if all_passed else '⚠ 部分符合'}")
        
        # 显示大纲的开头部分以供人工检查
        print("\n大纲内容预览:")
        print("=" * 50)
        lines = content.split('\n')[:30]  # 显示前30行
        for i, line in enumerate(lines, 1):
            print(f"{i:2d}: {line}")
        if len(content.split('\n')) > 30:
            print("... (内容较长，仅显示前30行)")
        
        conn.close()
        return all_passed
        
    except Exception as e:
        print(f"验证大纲格式时出错: {str(e)}")
        return False

def check_all_projects():
    """
    检查所有项目中的大纲格式
    """
    base_path = r"c:\Users\玄曦雪\OneDrive\Desktop\动慢工具\novel_creation_tool"
    
    # 查找所有项目文件夹
    import glob
    project_dirs = glob.glob(os.path.join(base_path, "projects", "*"))
    
    for project_dir in project_dirs:
        if os.path.isdir(project_dir):
            print(f"\n{'='*60}")
            print(f"检查项目: {os.path.basename(project_dir)}")
            print('='*60)
            verify_outline_format(project_dir)

if __name__ == "__main__":
    print("验证大纲生成格式...")
    check_all_projects()
    
    # 检查默认项目位置
    print(f"\n{'='*60}")
    print("检查默认项目位置...")
    print('='*60)
    default_project_path = r"c:\Users\玄曦雪\OneDrive\Desktop\动慢工具\novel_creation_tool\projects\1"
    if os.path.exists(default_project_path):
        verify_outline_format(default_project_path)
    else:
        print(f"默认项目路径不存在: {default_project_path}")