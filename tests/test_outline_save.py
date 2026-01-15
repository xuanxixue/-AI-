import sqlite3
import os
from ui.outline_generation_window import OutlineGenerationWindow
import tkinter as tk

def check_generated_outlines_table(project_path):
    """
    检查项目数据库中是否存在生成的大纲数据
    """
    db_path = os.path.join(project_path, 'project.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='generated_outlines'
        """)
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("表 'generated_outlines' 不存在")
            conn.close()
            return False
        
        print("表 'generated_outlines' 存在")
        
        # 查询表中的数据
        cursor.execute("SELECT COUNT(*) FROM generated_outlines")
        count = cursor.fetchone()[0]
        print(f"表中包含 {count} 条大纲记录")
        
        if count > 0:
            # 获取所有大纲记录
            cursor.execute("SELECT id, title, content, source_info, created_at FROM generated_outlines ORDER BY created_at DESC")
            records = cursor.fetchall()
            
            for i, record in enumerate(records):
                record_id, title, content, source_info, created_at = record
                print(f"\n--- 记录 {i+1} ---")
                print(f"ID: {record_id}")
                print(f"标题: {title}")
                print(f"来源信息: {source_info}")
                print(f"创建时间: {created_at}")
                print(f"内容长度: {len(content) if content else 0} 字符")
                if content:
                    print(f"内容预览: {content[:100]}...")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"检查数据库时出错: {str(e)}")
        return False

def check_all_project_dbs():
    """
    检查所有项目中的数据库文件
    """
    base_path = r"c:\Users\玄曦雪\OneDrive\Desktop\动慢工具\novel_creation_tool"
    
    # 查找所有项目文件夹
    import glob
    project_dirs = glob.glob(os.path.join(base_path, "projects", "*"))
    
    for project_dir in project_dirs:
        if os.path.isdir(project_dir):
            print(f"\n检查项目: {os.path.basename(project_dir)}")
            check_generated_outlines_table(project_dir)

if __name__ == "__main__":
    print("检查大纲生成保存功能...")
    check_all_project_dbs()
    
    # 如果没有找到项目，则检查默认位置
    print("\n检查默认项目位置...")
    default_project_path = r"c:\Users\玄曦雪\OneDrive\Desktop\动慢工具\novel_creation_tool\projects\1"
    if os.path.exists(default_project_path):
        check_generated_outlines_table(default_project_path)
    else:
        print(f"默认项目路径不存在: {default_project_path}")