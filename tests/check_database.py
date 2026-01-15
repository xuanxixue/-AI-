import sqlite3
import os

# 检查项目1的数据库
db_path_1 = r"c:\Users\玄曦雪\OneDrive\Desktop\动慢工具\novel_creation_tool\projects\1\project.db"
db_path_2 = r"c:\Users\玄曦雪\OneDrive\Desktop\动慢工具\novel_creation_tool\projects\2\project.db"

print("检查项目1数据库...")
if os.path.exists(db_path_1):
    print(f"数据库文件存在: {db_path_1}")
    try:
        conn = sqlite3.connect(db_path_1)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"数据库中的表: {tables}")
        
        # 检查generated_outlines表的数据
        cursor.execute("SELECT COUNT(*) FROM generated_outlines;")
        count = cursor.fetchone()[0]
        print(f"generated_outlines表中的记录数: {count}")
        
        if count > 0:
            # 获取最新记录
            cursor.execute("SELECT * FROM generated_outlines ORDER BY created_at DESC LIMIT 1;")
            latest_record = cursor.fetchone()
            print(f"最新记录: {latest_record}")
            
            # 显示大纲内容的前200个字符
            if latest_record and len(latest_record) > 1:
                print(f"大纲内容前200字符: {latest_record[1][:200]}...")
        
        conn.close()
    except Exception as e:
        print(f"访问数据库时出错: {e}")
else:
    print(f"数据库文件不存在: {db_path_1}")

print("\n检查项目2数据库...")
if os.path.exists(db_path_2):
    print(f"数据库文件存在: {db_path_2}")
    try:
        conn = sqlite3.connect(db_path_2)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"数据库中的表: {tables}")
        
        # 检查generated_outlines表的数据
        cursor.execute("SELECT COUNT(*) FROM generated_outlines;")
        count = cursor.fetchone()[0]
        print(f"generated_outlines表中的记录数: {count}")
        
        if count > 0:
            # 获取最新记录
            cursor.execute("SELECT * FROM generated_outlines ORDER BY created_at DESC LIMIT 1;")
            latest_record = cursor.fetchone()
            print(f"最新记录: {latest_record}")
            
            # 显示大纲内容的前200个字符
            if latest_record and len(latest_record) > 1:
                print(f"大纲内容前200字符: {latest_record[1][:200]}...")
        
        conn.close()
    except Exception as e:
        print(f"访问数据库时出错: {e}")
else:
    print(f"数据库文件不存在: {db_path_2}")