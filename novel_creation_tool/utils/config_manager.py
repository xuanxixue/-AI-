import json
import os
from typing import Dict, Optional


class ConfigManager:
    """
    全局配置管理器
    负责管理API密钥等全局配置信息
    """
    
    def __init__(self, config_file_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_file_path (str): 配置文件路径，默认为项目根目录下的config.json
        """
        if config_file_path is None:
            self.config_file_path = os.path.join(os.getcwd(), 'config.json')
        else:
            self.config_file_path = config_file_path
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def save_config(self, config_data: Dict = None):
        """保存配置文件"""
        if config_data is not None:
            self.config = config_data
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
        
        with open(self.config_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get_api_key(self) -> str:
        """获取API密钥"""
        return self.config.get('api_key', '')
    
    def set_api_key(self, api_key: str):
        """设置API密钥"""
        self.config['api_key'] = api_key
        self.save_config()
    
    def get_setting(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set_setting(self, key: str, value):
        """设置配置项"""
        self.config[key] = value
        self.save_config()
    
    def get_modelscope_api_key(self) -> str:
        """获取ModelScope API密钥"""
        return self.config.get('modelscope_api_key', '')
    
    def set_modelscope_api_key(self, api_key: str):
        """设置ModelScope API密钥"""
        self.config['modelscope_api_key'] = api_key
        self.save_config()


# 全局配置管理器实例
config_manager = ConfigManager()