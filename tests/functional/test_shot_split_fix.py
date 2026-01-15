#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本：验证故事分镜头功能修复
"""

import os
import sqlite3
import sys

def check_database_structure(db_path):
    """
    检查数据库结构是否完整
    """
    print(f"检查数据库: {db_path}")
    
    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查必需的表
    required_tables = ['scenes', 'shots', 'generated_chapters']
    missing_tables = []
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"现有表: {existing_tables}")
    
    for table in required_tables:
        if table not in existing_tables:
            missing_tables.append(table)
    
    if missing_tables:
        print(f"缺少必需的表: {missing_tables}")
        conn.close()
        return False
    else:
        print("所有必需的表都存在")
        
        # 检查scenes表内容
        cursor.execute("SELECT COUNT(*) FROM scenes;")
        scene_count = cursor.fetchone()[0]
        print(f"scenes表中有 {scene_count} 条记录")
        
        if scene_count > 0:
            cursor.execute("SELECT * FROM scenes LIMIT 3;")
            sample_records = cursor.fetchall()
            print("Sample scene records:")
            for record in sample_records:
                print(f"  {record}")
        
        conn.close()
        return True

def main():
    """
    主函数
    """
    print("=" * 60)
    print("故事分镜头功能修复验证脚本")
    print("=" * 60)
    
    # 默认测试项目路径
    project_path = "c:/Users/玄曦雪/OneDrive/Desktop/动慢工具/test_project"
    db_path = os.path.join(project_path, "project.db")
    
    print(f"项目路径: {project_path}")
    
    if os.path.exists(project_path):
        print("项目存在")
        
        # 检查数据库结构
        if check_database_structure(db_path):
            print("\n✓ 数据库结构完整，故事分镜头功能应该可以正常工作")
            print("\n使用说明:")
            print("1. 首先使用'故事分场景'功能生成场景数据")
            print("2. 然后使用'故事分镜头'功能对场景进行分镜头处理")
            print("3. 分镜头结果将显示在右侧列表中并可保存")
        else:
            print("\n✗ 数据库结构不完整")
            print("\n修复步骤:")
            print("1. 使用'故事分场景'功能处理一些章节内容")
            print("2. 确保场景数据被保存到数据库")
            print("3. 然后才能在'故事分镜头'功能中看到场景列表")
    else:
        print(f"项目路径不存在: {project_path}")
        print("请确保您有一个有效的项目")

if __name__ == "__main__":
    main()