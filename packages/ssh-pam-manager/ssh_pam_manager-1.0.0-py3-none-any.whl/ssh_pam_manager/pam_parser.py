"""
PAM配置文件解析模块
负责解析PAM配置文件格式
"""

import re
from typing import List, Dict, Optional


class PAMParser:
    """PAM配置文件解析器"""
    
    def __init__(self):
        self.pam_config_pattern = re.compile(
            r'^\s*(?P<type>auth|account|password|session)\s+'  # PAM类型
            r'(?P<control>\[.*?\]|\S+)\s+'  # 控制标志
            r'(?P<module>\S+)\s*'  # PAM模块
            r'(?P<args>.*)?$'  # 参数
        )
    
    def parse_line(self, line: str) -> Optional[Dict[str, str]]:
        """解析单行PAM配置"""
        line = line.strip()
        
        # 跳过空行和注释
        if not line or line.startswith('#'):
            return None
        
        match = self.pam_config_pattern.match(line)
        if match:
            return {
                'type': match.group('type'),
                'control': match.group('control'),
                'module': match.group('module'),
                'args': match.group('args') or '',
                'original': line
            }
        
        return None
    
    def parse_file(self, file_path: str) -> List[Dict[str, str]]:
        """解析整个PAM配置文件"""
        configs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    parsed = self.parse_line(line)
                    if parsed:
                        parsed['line_number'] = line_num
                        configs.append(parsed)
        except FileNotFoundError:
            raise FileNotFoundError(f"PAM配置文件不存在: {file_path}")
        except PermissionError:
            raise PermissionError(f"没有权限读取PAM配置文件: {file_path}")
        
        return configs
    
    def format_config(self, config: Dict[str, str]) -> str:
        """将配置字典格式化为PAM配置行"""
        parts = [config['type'], config['control'], config['module']]
        if config['args']:
            parts.append(config['args'])
        return '\t'.join(parts)