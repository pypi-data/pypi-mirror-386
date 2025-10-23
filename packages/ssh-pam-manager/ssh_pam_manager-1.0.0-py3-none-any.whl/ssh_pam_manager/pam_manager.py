"""
PAM配置文件管理器
负责PAM配置文件的读取、修改和增加操作
"""

import os
import shutil
from typing import List, Dict, Optional
from datetime import datetime
from .pam_parser import PAMParser


class PAMManager:
    """PAM配置文件管理器"""
    
    def __init__(self, config_path: str = "/etc/pam.d/sshd"):
        self.config_path = config_path
        self.parser = PAMParser()
        self.backup_dir = "/var/backup/pam"
    
    def read_config(self) -> List[Dict[str, str]]:
        """读取PAM配置文件"""
        return self.parser.parse_file(self.config_path)
    
    def backup_config(self) -> str:
        """备份当前配置文件"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, mode=0o700, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"sshd_backup_{timestamp}")
        
        shutil.copy2(self.config_path, backup_path)
        return backup_path
    
    def modify_config(self, line_number: int, new_config: Dict[str, str]) -> bool:
        """修改指定行的PAM配置"""
        # 备份原配置
        backup_path = self.backup_config()
        
        try:
            # 读取原文件内容
            with open(self.config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 修改指定行
            if 1 <= line_number <= len(lines):
                new_line = self.parser.format_config(new_config) + '\n'
                lines[line_number - 1] = new_line
            else:
                raise ValueError(f"行号 {line_number} 超出范围")
            
            # 写入新内容
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            # 恢复备份
            shutil.copy2(backup_path, self.config_path)
            raise e
    
    def add_config(self, config: Dict[str, str], position: Optional[int] = None) -> bool:
        """添加新的PAM配置"""
        # 备份原配置
        backup_path = self.backup_config()
        
        try:
            # 读取原文件内容
            with open(self.config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_line = self.parser.format_config(config) + '\n'
            
            if position is None:
                # 添加到文件末尾
                lines.append(new_line)
            else:
                # 插入到指定位置
                if 1 <= position <= len(lines):
                    lines.insert(position - 1, new_line)
                else:
                    raise ValueError(f"位置 {position} 超出范围")
            
            # 写入新内容
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            # 恢复备份
            shutil.copy2(backup_path, self.config_path)
            raise e
    
    def remove_config(self, line_number: int) -> bool:
        """删除指定行的PAM配置"""
        # 备份原配置
        backup_path = self.backup_config()
        
        try:
            # 读取原文件内容
            with open(self.config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 删除指定行
            if 1 <= line_number <= len(lines):
                del lines[line_number - 1]
            else:
                raise ValueError(f"行号 {line_number} 超出范围")
            
            # 写入新内容
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            # 恢复备份
            shutil.copy2(backup_path, self.config_path)
            raise e
    
    def validate_config(self, config: Dict[str, str]) -> bool:
        """验证PAM配置格式是否正确"""
        required_fields = ['type', 'control', 'module']
        
        for field in required_fields:
            if field not in config or not config[field]:
                return False
        
        # 验证type字段
        valid_types = ['auth', 'account', 'password', 'session']
        if config['type'] not in valid_types:
            return False
        
        return True