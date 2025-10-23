"""
命令行交互界面模块
提供用户友好的终端交互界面
"""

import sys
from typing import List, Dict
from .pam_manager import PAMManager


class CLIInterface:
    """命令行交互界面"""
    
    def __init__(self):
        self.pam_manager = PAMManager()
        self.menu_options = {
            '1': '查看当前PAM配置',
            '2': '添加PAM配置',
            '3': '修改PAM配置',
            '4': '删除PAM配置',
            '5': '退出'
        }
    
    def display_menu(self):
        """显示主菜单"""
        print("\n" + "="*50)
        print("SSH PAM配置管理工具")
        print("="*50)
        
        for key, value in self.menu_options.items():
            print(f"{key}. {value}")
        
        print("="*50)
    
    def display_configs(self, configs: List[Dict[str, str]]):
        """显示PAM配置列表"""
        if not configs:
            print("未找到有效的PAM配置")
            return
        
        print("\n当前PAM配置:")
        print("-" * 80)
        print(f"{'行号':<4} {'类型':<8} {'控制标志':<15} {'模块':<20} {'参数'}")
        print("-" * 80)
        
        for config in configs:
            line_num = config.get('line_number', 'N/A')
            print(f"{line_num:<4} {config['type']:<8} {config['control']:<15} {config['module']:<20} {config['args']}")
        
        print("-" * 80)
    
    def get_user_input(self, prompt: str, default: str = "") -> str:
        """获取用户输入"""
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        
        return input(prompt).strip() or default
    
    def get_config_from_user(self) -> Dict[str, str]:
        """从用户输入获取PAM配置"""
        print("\n请输入新的PAM配置:")
        print("-" * 60)
        
        config = {}
        
        # 类型说明
        print("\n🔐 PAM类型说明:")
        print("  1. auth     - 认证管理 (验证用户身份)")
        print("  2. account  - 账户管理 (检查账户状态)")
        print("  3. password - 密码管理 (修改密码)")
        print("  4. session  - 会话管理 (设置会话环境)")
        type_choice = self.get_user_input("请选择类型 (1-4)", "1")
        type_map = {"1": "auth", "2": "account", "3": "password", "4": "session"}
        config['type'] = type_map.get(type_choice, "auth")
        
        # 控制标志说明
        print("\n🎛️  控制标志说明:")
        print("  1. required   - 必须成功，失败后继续检查但最终失败")
        print("  2. requisite  - 必须成功，失败立即返回")
        print("  3. sufficient - 成功即返回，失败继续检查")
        print("  4. optional   - 可选，不影响最终结果")
        print("  5. include    - 包含其他配置文件")
        control_choice = self.get_user_input("请选择控制标志 (1-5)", "1")
        control_map = {"1": "required", "2": "requisite", "3": "sufficient", "4": "optional", "5": "include"}
        config['control'] = control_map.get(control_choice, "required")
        
        # 模块说明
        print("\n🔧 常用PAM模块说明:")
        print("  1. pam_unix.so      - 标准Unix认证")
        print("  2. pam_deny.so      - 总是拒绝")
        print("  3. pam_permit.so    - 总是允许")
        print("  4. pam_tally2.so    - 登录失败计数")
        print("  5. pam_limits.so    - 资源限制")
        print("  6. pam_env.so       - 环境变量设置")
        print("  7. pam_motd.so      - 显示登录消息")
        print("  8. 自定义模块")
        module_choice = self.get_user_input("请选择模块 (1-8)", "1")
        module_map = {
            "1": "pam_unix.so", "2": "pam_deny.so", "3": "pam_permit.so", 
            "4": "pam_tally2.so", "5": "pam_limits.so", "6": "pam_env.so", 
            "7": "pam_motd.so"
        }
        if module_choice == "8":
            config['module'] = self.get_user_input("请输入自定义模块名称", "")
        else:
            config['module'] = module_map.get(module_choice, "pam_unix.so")
        
        # 参数说明
        print("\n⚙️  参数示例:")
        print("  1. nullok           - 允许空密码")
        print("  2. try_first_pass   - 尝试使用之前输入的密码")
        print("  3. deny=3           - 失败3次后拒绝")
        print("  4. unlock_time=900  - 锁定15分钟后解锁")
        print("  5. file=/etc/issue  - 指定文件路径")
        print("  6. 自定义参数")
        param_choice = self.get_user_input("请选择参数 (1-6)", "6")
        param_map = {
            "1": "nullok", "2": "try_first_pass", "3": "deny=3", 
            "4": "unlock_time=900", "5": "file=/etc/issue"
        }
        if param_choice == "6":
            config['args'] = self.get_user_input("请输入自定义参数", "")
        else:
            config['args'] = param_map.get(param_choice, "")
        
        print("-" * 60)
        return config
    
    def handle_view_config(self):
        """处理查看配置操作"""
        try:
            configs = self.pam_manager.read_config()
            self.display_configs(configs)
        except Exception as e:
            print(f"错误: {e}")
    
    def handle_add_config(self):
        """处理添加配置操作"""
        try:
            config = self.get_config_from_user()
            
            if not self.pam_manager.validate_config(config):
                print("配置格式不正确，请检查输入")
                return
            
            # 显示预览
            print("\n预览配置:")
            print(self.pam_manager.parser.format_config(config))
            
            confirm = self.get_user_input("确认添加？(y/n)", "n")
            if confirm.lower() == 'y':
                self.pam_manager.add_config(config)
                print("配置添加成功")
            else:
                print("操作已取消")
                
        except Exception as e:
            print(f"错误: {e}")
    
    def handle_modify_config(self):
        """处理修改配置操作"""
        try:
            configs = self.pam_manager.read_config()
            self.display_configs(configs)
            
            if not configs:
                return
            
            line_num = self.get_user_input("请输入要修改的行号")
            if not line_num.isdigit():
                print("请输入有效的行号")
                return
            
            line_num = int(line_num)
            if line_num < 1 or line_num > len(configs):
                print("行号超出范围")
                return
            
            print(f"\n当前配置:")
            current_config = configs[line_num - 1]
            print(self.pam_manager.parser.format_config(current_config))
            
            new_config = self.get_config_from_user()
            
            if not self.pam_manager.validate_config(new_config):
                print("配置格式不正确，请检查输入")
                return
            
            # 显示预览
            print("\n新配置:")
            print(self.pam_manager.parser.format_config(new_config))
            
            confirm = self.get_user_input("确认修改？(y/n)", "n")
            if confirm.lower() == 'y':
                self.pam_manager.modify_config(line_num, new_config)
                print("配置修改成功")
            else:
                print("操作已取消")
                
        except Exception as e:
            print(f"错误: {e}")
    
    def handle_remove_config(self):
        """处理删除配置操作"""
        try:
            configs = self.pam_manager.read_config()
            self.display_configs(configs)
            
            if not configs:
                return
            
            line_num = self.get_user_input("请输入要删除的行号")
            if not line_num.isdigit():
                print("请输入有效的行号")
                return
            
            line_num = int(line_num)
            if line_num < 1 or line_num > len(configs):
                print("行号超出范围")
                return
            
            target_config = configs[line_num - 1]
            print(f"\n要删除的配置:")
            print(self.pam_manager.parser.format_config(target_config))
            
            confirm = self.get_user_input("确认删除？(y/n)", "n")
            if confirm.lower() == 'y':
                self.pam_manager.remove_config(line_num)
                print("配置删除成功")
            else:
                print("操作已取消")
                
        except Exception as e:
            print(f"错误: {e}")
    
    def run(self):
        """运行交互界面"""
        print("SSH PAM配置管理工具启动...")
        
        while True:
            self.display_menu()
            choice = self.get_user_input("请选择操作", "1")
            
            if choice == '1':
                self.handle_view_config()
            elif choice == '2':
                self.handle_add_config()
            elif choice == '3':
                self.handle_modify_config()
            elif choice == '4':
                self.handle_remove_config()
            elif choice == '5':
                print("感谢使用，再见！")
                break
            else:
                print("无效选择，请重新输入")
            
            # 暂停一下让用户看到结果
            input("\n按回车键继续...")