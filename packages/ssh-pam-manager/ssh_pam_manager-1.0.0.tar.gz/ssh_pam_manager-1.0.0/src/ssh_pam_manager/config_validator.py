"""
配置验证模块
负责验证PAM配置的合法性和安全性
"""

import re
from typing import List, Dict, Tuple


class ConfigValidator:
    """PAM配置验证器"""
    
    def __init__(self):
        self.valid_modules = [
            'pam_unix.so', 'pam_deny.so', 'pam_permit.so', 'pam_rootok.so',
            'pam_nologin.so', 'pam_securetty.so', 'pam_env.so', 'pam_mail.so',
            'pam_limits.so', 'pam_lastlog.so', 'pam_motd.so', 'pam_umask.so',
            'pam_shells.so', 'pam_time.so', 'pam_access.so', 'pam_listfile.so',
            'pam_cracklib.so', 'pam_pwquality.so', 'pam_tally2.so', 'pam_faillock.so'
        ]
        
        self.valid_controls = [
            'required', 'requisite', 'sufficient', 'optional',
            'include', 'substack'
        ]
        
        self.dangerous_modules = [
            'pam_deny.so', 'pam_permit.so'
        ]
    
    def validate_module(self, module: str) -> Tuple[bool, str]:
        """验证PAM模块是否有效"""
        if not module:
            return False, "模块名不能为空"
        
        # 检查模块文件是否存在（可选检查）
        module_path = f"/lib/security/{module}"
        module_path64 = f"/lib64/security/{module}"
        
        # 这里我们只检查模块名格式，不检查实际文件存在
        if not re.match(r'^[a-zA-Z0-9_.-]+$', module):
            return False, f"模块名格式不正确: {module}"
        
        return True, "模块验证通过"
    
    def validate_control(self, control: str) -> Tuple[bool, str]:
        """验证控制标志是否有效"""
        if not control:
            return False, "控制标志不能为空"
        
        # 检查是否为简单控制标志
        if control in self.valid_controls:
            return True, "控制标志验证通过"
        
        # 检查是否为复杂控制标志 [value=action]
        if control.startswith('[') and control.endswith(']'):
            control_content = control[1:-1]
            if '=' in control_content:
                key, value = control_content.split('=', 1)
                if key and value:
                    return True, "复杂控制标志验证通过"
        
        return False, f"无效的控制标志: {control}"
    
    def validate_type(self, pam_type: str) -> Tuple[bool, str]:
        """验证PAM类型是否有效"""
        valid_types = ['auth', 'account', 'password', 'session']
        
        if pam_type not in valid_types:
            return False, f"无效的PAM类型: {pam_type}"
        
        return True, "PAM类型验证通过"
    
    def validate_args(self, args: str) -> Tuple[bool, str]:
        """验证参数是否安全"""
        if not args:
            return True, "参数验证通过"
        
        # 检查是否有潜在危险的参数
        dangerous_patterns = [
            r'\s*exec\s*=',  # 执行命令
            r'\s*shell\s*=',  # shell执行
            r'\s*script\s*=',  # 脚本执行
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, args, re.IGNORECASE):
                return False, f"检测到潜在危险的参数: {args}"
        
        return True, "参数验证通过"
    
    def validate_config(self, config: Dict[str, str]) -> Tuple[bool, List[str]]:
        """全面验证PAM配置"""
        errors = []
        
        # 验证必需字段
        required_fields = ['type', 'control', 'module']
        for field in required_fields:
            if field not in config or not config[field].strip():
                errors.append(f"缺少必需字段: {field}")
        
        if errors:
            return False, errors
        
        # 验证各个字段
        validations = [
            (self.validate_type(config['type']), "PAM类型"),
            (self.validate_control(config['control']), "控制标志"),
            (self.validate_module(config['module']), "PAM模块"),
            (self.validate_args(config.get('args', '')), "参数")
        ]
        
        for (is_valid, message), field_name in validations:
            if not is_valid:
                errors.append(f"{field_name}验证失败: {message}")
        
        # 检查是否为危险模块
        if config['module'] in self.dangerous_modules:
            errors.append(f"警告: 使用了危险模块 {config['module']}")
        
        return len(errors) == 0, errors
    
    def check_security_risks(self, configs: List[Dict[str, str]]) -> List[str]:
        """检查安全风险"""
        warnings = []
        
        for config in configs:
            # 检查过于宽松的配置
            if (config['module'] == 'pam_permit.so' and 
                config['control'] in ['required', 'sufficient']):
                warnings.append(f"行 {config.get('line_number', 'N/A')}: 使用pam_permit.so可能过于宽松")
            
            # 检查过于严格的配置
            if (config['module'] == 'pam_deny.so' and 
                config['control'] in ['required', 'requisite']):
                warnings.append(f"行 {config.get('line_number', 'N/A')}: 使用pam_deny.so可能过于严格")
            
            # 检查缺少认证的配置
            if (config['type'] == 'auth' and 
                config['module'] not in ['pam_unix.so', 'pam_sss.so'] and
                'password' not in config.get('args', '')):
                warnings.append(f"行 {config.get('line_number', 'N/A')}: 认证配置可能不完整")
        
        return warnings