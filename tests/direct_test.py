"""
直接测试大纲理解功能
"""

import sqlite3
import os
from ui.outline_understanding_window import OutlineUnderstandingWindow

# 创建测试项目目录
test_project_path = os.path.join(os.getcwd(), 'test_project')
os.makedirs(test_project_path, exist_ok=True)

# 创建测试数据库
test_db_path = os.path.join(test_project_path, 'project.db')
conn = sqlite3.connect(test_db_path)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS outline_understanding (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        input_content TEXT,
        analysis_result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()

# 直接测试大纲理解功能
app = OutlineUnderstandingWindow(test_project_path)

# 模拟输入故事文本
sample_story = """深夜，一个女孩来到一家甜品店，点了一份甜品套餐。身旁的一位男士向她介绍着这份套餐里各个甜品名称的含义，女孩沉浸在甜品的故事里，转头发现刚才的男士不见了。她没多想，准备享用美食。突然她盘子里的一块甜品上出现了一些灰尘，她小心地擦去灰尘，接着整盘甜品都变成灰尘飘散掉。她转过头一看，一位女店员也变成灰尘飘散掉。整个店里只剩下目瞪口呆的女孩一人。这时，这家甜品店开始地动山摇，女孩也晕了过去。"""

# 在文本框中插入测试故事
app.text_input.insert("1.0", sample_story)

# 模拟设置API密钥
app.api_key = "sk-5c447dcdbfdc45319954695e45179a29"

# 直接调用AI分析功能
result = app.mock_ai_analysis(sample_story)
app.update_result_display(result)

# 直接保存到数据库
app.save_outline_data()

print("大纲理解功能测试完成！")

# 验证数据库中是否保存了记录
conn = sqlite3.connect(test_db_path)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM outline_understanding')
count = cursor.fetchone()[0]
print(f"数据库中找到 {count} 条大纲理解记录")

if count > 0:
    cursor.execute('SELECT * FROM outline_understanding')
    record = cursor.fetchone()
    print(f"记录ID: {record[0]}")
    print(f"标题: {record[1]}")
    print(f"输入长度: {len(record[2])}")
    print(f"分析结果长度: {len(record[3])}")

conn.close()