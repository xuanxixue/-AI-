import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    """
    数据库管理类，负责管理工程文件的元数据
    """
    
    def __init__(self, db_path):
        """
        初始化数据库管理器
        
        Args:
            db_path (str): 数据库文件路径
        """
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """连接到数据库"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    
    def create_tables(self):
        """创建必要的数据表"""
        cursor = self.connection.cursor()
        
        # 创建工程文件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建工程文件设置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                UNIQUE(project_id, setting_key)
            )
        ''')
        
        # 创建大纲信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # 创建章节信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                chapter_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                word_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # 创建故事信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS story_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                info_type TEXT NOT NULL,  -- 如 character, setting, plot 等
                name TEXT NOT NULL,
                description TEXT,
                details TEXT,  -- JSON格式存储详细信息
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        self.connection.commit()
    
    def execute_query(self, query, params=None):
        """
        执行SQL查询
        
        Args:
            query (str): SQL查询语句
            params (tuple): 查询参数
            
        Returns:
            list: 查询结果
        """
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            return cursor.fetchall()
        else:
            self.connection.commit()
            return cursor.lastrowid
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()


class ProjectDatabase:
    """
    工程文件专用数据库，每个工程文件都有一个独立的数据库
    """
    
    def __init__(self, project_db_path):
        """
        初始化工程文件数据库
        
        Args:
            project_db_path (str): 工程文件数据库路径
        """
        self.db_path = project_db_path
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """连接到工程文件数据库"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
    
    def create_tables(self):
        """为工程文件创建特定的数据表"""
        cursor = self.connection.cursor()
        
        # 创建大纲节点表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outline_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                title TEXT NOT NULL,
                content TEXT,
                level INTEGER DEFAULT 0,
                position INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES outline_nodes (id)
            )
        ''')
        
        # 创建想法记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                tags TEXT,  -- 逗号分隔的标签
                importance INTEGER DEFAULT 1,  -- 重要程度 1-5
                status TEXT DEFAULT 'active',  -- active, archived
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建分镜脚本表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scene_id INTEGER,
                shot_number INTEGER NOT NULL,
                description TEXT,
                duration REAL,  -- 持续时间（秒）
                camera_angle TEXT,  -- 镜头角度
                character_actions TEXT,  -- 角色动作
                dialogue TEXT,  -- 对话
                props TEXT,  -- 道具
                notes TEXT,  -- 备注
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建场景表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                segment_id INTEGER,
                scene_number INTEGER NOT NULL,
                title TEXT,
                setting TEXT,  -- 场景设置
                characters TEXT,  -- 出现场景的角色
                duration REAL,  -- 持续时间
                content TEXT,  -- 场景内容
                notes TEXT,  -- 备注
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建分段表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_position INTEGER,  -- 开始位置
                end_position INTEGER,  -- 结束位置
                word_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
    
    def execute_query(self, query, params=None):
        """
        执行SQL查询
        
        Args:
            query (str): SQL查询语句
            params (tuple): 查询参数
            
        Returns:
            list: 查询结果
        """
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            return cursor.fetchall()
        else:
            self.connection.commit()
            return cursor.lastrowid
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()


def init_main_database():
    """
    初始化主数据库
    """
    db_path = os.path.join(os.getcwd(), 'projects.db')
    db_manager = DatabaseManager(db_path)
    return db_manager