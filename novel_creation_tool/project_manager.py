import os
import json
import shutil
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import ProjectDatabase, init_main_database


class ProjectManager:
    """
    工程文件管理类，负责工程文件的创建、删除、读取等操作
    """
    
    def __init__(self, base_path=None):
        """
        初始化工程文件管理器
        
        Args:
            base_path (str): 工程文件基础路径，默认为当前目录下的projects文件夹
        """
        if base_path is None:
            self.base_path = os.path.join(os.getcwd(), 'projects')
        else:
            self.base_path = base_path
        
        # 确保基础路径存在
        os.makedirs(self.base_path, exist_ok=True)
        
        # 初始化主数据库
        self.main_db = init_main_database()
    
    def create_project(self, name):
        """
        创建新工程文件
        
        Args:
            name (str): 工程文件名称
            
        Returns:
            str: 工程文件路径，如果创建失败返回None
        """
        try:
            # 验证工程文件名
            if not name or not isinstance(name, str):
                raise ValueError("工程文件名不能为空且必须为字符串")
            
            # 清理工程文件名，移除不合法字符
            clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            if not clean_name:
                raise ValueError("工程文件名不合法")
            
            # 构建工程文件路径
            project_path = os.path.join(self.base_path, clean_name)
            
            # 如果路径已存在，添加数字后缀
            counter = 1
            original_path = project_path
            while os.path.exists(project_path):
                project_path = f"{original_path}_{counter}"
                counter += 1
            
            # 创建工程文件夹
            os.makedirs(project_path, exist_ok=True)
            
            # 创建工程文件数据库
            project_db_path = os.path.join(project_path, 'project.db')
            project_db = ProjectDatabase(project_db_path)
            project_db.close()  # 立即关闭，后续需要时再打开
            
            # 创建工程文件配置文件
            config_path = os.path.join(project_path, 'config.json')
            config_data = {
                'name': clean_name,
                'path': project_path,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            # 将工程文件信息存入主数据库
            insert_query = '''
                INSERT INTO projects (name, path, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            '''
            project_id = self.main_db.execute_query(
                insert_query,
                (clean_name, project_path, datetime.now(), datetime.now())
            )
            
            print(f"成功创建工程文件: {clean_name}，ID: {project_id}")
            return project_path
            
        except Exception as e:
            print(f"创建工程文件失败: {str(e)}")
            return None
    
    def delete_project(self, project_path):
        """
        删除工程文件及其关联数据
        
        Args:
            project_path (str): 工程文件路径
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if not os.path.exists(project_path):
                print(f"工程文件不存在: {project_path}")
                return False
            
            # 从主数据库中删除工程文件记录
            delete_query = "DELETE FROM projects WHERE path = ?"
            self.main_db.execute_query(delete_query, (project_path,))
            
            # 删除工程文件夹及所有内容
            shutil.rmtree(project_path)
            
            print(f"成功删除工程文件: {project_path}")
            return True
            
        except Exception as e:
            print(f"删除工程文件失败: {str(e)}")
            return False
    
    def list_projects(self):
        """
        获取工程文件列表
        
        Returns:
            list: 工程文件信息列表，每个元素包含id, name, path, created_at, updated_at
        """
        try:
            query = "SELECT * FROM projects ORDER BY updated_at DESC"
            rows = self.main_db.execute_query(query)
            
            projects = []
            for row in rows:
                project_info = {
                    'id': row['id'],
                    'name': row['name'],
                    'path': row['path'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                projects.append(project_info)
            
            return projects
            
        except Exception as e:
            print(f"获取工程文件列表失败: {str(e)}")
            return []
    
    def open_project(self, project_path):
        """
        打开指定工程文件
        
        Args:
            project_path (str): 工程文件路径
            
        Returns:
            dict: 工程文件信息，如果打开失败返回None
        """
        try:
            if not os.path.exists(project_path):
                print(f"工程文件不存在: {project_path}")
                return None
            
            # 检查配置文件是否存在
            config_path = os.path.join(project_path, 'config.json')
            if not os.path.exists(config_path):
                print(f"工程文件配置文件不存在: {config_path}")
                return None
            
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新工程文件更新时间
            update_query = "UPDATE projects SET updated_at = ? WHERE path = ?"
            self.main_db.execute_query(update_query, (datetime.now(), project_path))
            
            return config_data
            
        except Exception as e:
            print(f"打开工程文件失败: {str(e)}")
            return None
    
    def get_project_info(self, project_id):
        """
        根据ID获取工程文件信息
        
        Args:
            project_id (int): 工程文件ID
            
        Returns:
            dict: 工程文件信息
        """
        try:
            query = "SELECT * FROM projects WHERE id = ?"
            rows = self.main_db.execute_query(query, (project_id,))
            
            if rows:
                row = rows[0]
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'path': row['path'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            else:
                return None
                
        except Exception as e:
            print(f"获取工程文件信息失败: {str(e)}")
            return None
    
    def update_project(self, project_id, **kwargs):
        """
        更新工程文件信息
        
        Args:
            project_id (int): 工程文件ID
            **kwargs: 要更新的字段，如 name, path 等
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 构建更新语句
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['name', 'path']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return False
            
            fields.append("updated_at = ?")
            values.append(datetime.now())
            values.append(project_id)
            
            query = f"UPDATE projects SET {', '.join(fields)} WHERE id = ?"
            self.main_db.execute_query(query, tuple(values))
            
            return True
            
        except Exception as e:
            print(f"更新工程文件失败: {str(e)}")
            return False
    
    def close(self):
        """
        关闭数据库连接
        """
        if hasattr(self, 'main_db') and self.main_db:
            self.main_db.close()