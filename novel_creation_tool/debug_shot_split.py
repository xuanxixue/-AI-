#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试脚本：验证故事分镜头功能的场景ID解析
"""

import sqlite3
import os

def debug_database_content():
    """
    调试数据库内容
    """
    db_path = "c:/Users/玄曦雪/OneDrive/Desktop/动慢工具/test_project/project.db"
    
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        return
    
    print(f"连接到数据库: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"数据库中的表: {tables}")
    
    if 'scenes' in tables:
        print("\n--- 检查 scenes 表 ---")
        
        # 获取scenes表结构
        cursor.execute("PRAGMA table_info(scenes);")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"scenes表的列: {columns}")
        
        # 获取所有场景记录
        cursor.execute("SELECT * FROM scenes;")
        records = cursor.fetchall()
        print(f"scenes表中的记录数: {len(records)}")
        
        if records:
            print("前5条场景记录:")
            for i, record in enumerate(records[:5]):
                print(f"  记录 {i+1}: {record}")
                
                # 尝试按我们当前的逻辑解析
                if len(record) >= 4:  # id, scene_number, title, segment_id
                    record_id, scene_number, title, segment_id = record[0], record[2], record[3], record[4] if len(record) > 4 else (record[3] if len(record) > 3 else "")
                    print(f"    解析尝试 - segment_id: '{segment_id}', scene_number: {scene_number}")
                    
                    # 模拟我们的解析逻辑
                    if '_' in str(segment_id):
                        last_underscore_pos = str(segment_id).rfind('_')
                        if last_underscore_pos != -1:
                            potential_segment_id = str(segment_id)[:last_underscore_pos]  # EP01_P01
                            potential_scene_part = str(segment_id)[last_underscore_pos+1:]  # S01
                        
                            if potential_scene_part.startswith('S'):
                                try:
                                    extracted_scene_number = int(potential_scene_part[1:])
                                    print(f"    解析成功 - segment_id: '{potential_segment_id}', scene_number: {extracted_scene_number}")
                                except ValueError:
                                    print(f"    解析失败 - 无法将 '{potential_scene_part[1:]}' 转换为整数")
                            else:
                                try:
                                    extracted_scene_number = int(potential_scene_part)
                                    print(f"    解析成功 - segment_id: '{potential_segment_id}', scene_number: {extracted_scene_number}")
                                except ValueError:
                                    print(f"    解析失败 - 无法将 '{potential_scene_part}' 转换为整数")
                        else:
                            print(f"    无法找到下划线分割符")
    
    if 'shots' in tables:
        print("\n--- 检查 shots 表 ---")
        cursor.execute("SELECT COUNT(*) FROM shots;")
        shot_count = cursor.fetchone()[0]
        print(f"shots表中的记录数: {shot_count}")
        
        if shot_count > 0:
            cursor.execute("SELECT * FROM shots LIMIT 3;")
            shot_records = cursor.fetchall()
            print("前3条镜头记录:")
            for record in shot_records:
                print(f"  {record}")
    
    conn.close()

def simulate_parsing_logic():
    """
    模拟解析逻辑
    """
    print("\n--- 模拟解析逻辑测试 ---")
    
    test_cases = [
        "EP01_P01_S01",
        "EP01_P02_S01", 
        "EP01_P01_S02",
        "TEST_CHAPTER_S01",
        "CHAPTER_01_S01"
    ]
    
    for test_case in test_cases:
        print(f"\n测试解析: {test_case}")
        
        # 模拟我们的解析逻辑
        last_underscore_pos = test_case.rfind('_')
        if last_underscore_pos != -1:
            segment_id = test_case[:last_underscore_pos]  # 获取 "EP01_P01"
            scene_num_part = test_case[last_underscore_pos+1:]  # 获取 "S01"
            
            print(f"  segment_id: '{segment_id}', scene_num_part: '{scene_num_part}'")
            
            if scene_num_part.startswith('S'):
                try:
                    scene_number = int(scene_num_part[1:])  # 获取 S 后面的数字
                    print(f"  解析成功 - 最终结果: segment_id='{segment_id}', scene_number={scene_number}")
                except ValueError:
                    print(f"  解析失败 - 无法将 '{scene_num_part[1:]}' 转换为整数")
            else:
                try:
                    scene_number = int(scene_num_part)
                    print(f"  解析成功 - 最终结果: segment_id='{segment_id}', scene_number={scene_number}")
                except ValueError:
                    print(f"  解析失败 - 无法将 '{scene_num_part}' 转换为整数")
        else:
            print(f"  解析失败 - 没有找到下划线")

if __name__ == "__main__":
    print("=" * 60)
    print("故事分镜头功能调试脚本")
    print("=" * 60)
    
    debug_database_content()
    simulate_parsing_logic()
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("如果仍有问题，请检查数据库中scenes表的实际数据格式")
    print("=" * 60)