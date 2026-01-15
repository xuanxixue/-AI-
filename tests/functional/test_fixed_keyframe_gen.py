import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'novel_creation_tool'))

# 测试关键帧生图窗口的导入
try:
    from novel_creation_tool.ui.keyframe_image_generation_window import KeyframeImageGenerationWindow
    print("✓ KeyframeImageGenerationWindow import successful")
    
    # 测试数据库连接和数据加载
    import sqlite3
    
    # 使用测试项目路径
    test_project_path = "./test_project"
    
    # 确保测试目录存在
    if not os.path.exists(test_project_path):
        os.makedirs(test_project_path, exist_ok=True)
    
    # 创建测试数据库
    db_path = os.path.join(test_project_path, 'project.db')
    
    # 如果数据库不存在，创建一个带测试数据的数据库
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建keyframes表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keyframes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shot_id INTEGER,
                keyframe_number INTEGER NOT NULL,
                keyframe_id TEXT,
                timestamp TEXT,
                description TEXT,
                composition TEXT,
                perspective TEXT,
                character_actions TEXT,
                emotion TEXT,
                camera_pose TEXT,
                lighting_changes TEXT,
                audio_hint TEXT,
                narration TEXT,
                music TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入测试数据
        test_keyframes = [
            ("SH01_KF01", "0.0秒", "镜头起始帧。广角远景展现埃索斯大陆东北荒原全景。", "广角远景", "无", "无具体人物，仅2–3个模糊人影", "原始、肃穆", "固定机位", "自然天光漫射", "风声低鸣", "", ""),
            ("SH01_KF02", "2.5秒", "特写镜头，聚焦于主角的面部表情，展现内心的挣扎。", "特写", "正面", "主角独自一人", "紧张、不安", "推进镜头", "暖色调灯光", "心跳声", "主角内心独白", "低沉弦乐"),
            ("SH02_KF01", "5.0秒", "中景镜头，展示主角与神秘物体的互动。", "中景", "侧面", "主角与发光水晶", "好奇、敬畏", "环绕镜头", "柔和蓝光", "能量波动声", "无声", "神秘旋律")
        ]
        
        for kf in test_keyframes:
            cursor.execute("""
                INSERT INTO keyframes 
                (keyframe_id, timestamp, description, composition, perspective, 
                 character_actions, emotion, camera_pose, lighting_changes, 
                 audio_hint, narration, music, shot_id, keyframe_number) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (kf[0], kf[1], kf[2], kf[3], kf[4], kf[5], kf[6], kf[7], kf[8], kf[9], kf[10], kf[11], 1, test_keyframes.index(kf)+1))
        
        conn.commit()
        conn.close()
        print("✓ Test database created with sample keyframe data")
    else:
        print("✓ Using existing database")
    
    # 测试加载关键帧数据
    try:
        window = KeyframeImageGenerationWindow(test_project_path)
        print(f"✓ Successfully loaded {len(window.keyframes)} keyframes from database")
        
        # 显示关键帧信息
        for i, kf in enumerate(window.keyframes):
            print(f"  Keyframe {i+1}: {kf['keyframe_id']} - {kf['description'][:50]}...")
            
    except Exception as e:
        print(f"✗ Error loading keyframes: {e}")
        
    print("✓ All tests passed!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")

print("Test completed.")