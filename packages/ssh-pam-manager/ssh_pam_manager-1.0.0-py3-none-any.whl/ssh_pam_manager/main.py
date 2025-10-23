"""
SSH PAM管理工具主入口模块
"""

import argparse
import sys
from .cli_interface import CLIInterface
from .pam_manager import PAMManager
from .config_validator import ConfigValidator


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SSH PAM配置管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  ssh-pam-manager                    # 启动交互式界面
  ssh-pam-manager --view             # 查看当前配置
  ssh-pam-manager --config /path/to/pam.d/sshd  # 指定配置文件路径
        """
    )
    
    parser.add_argument(
        '--view', 
        action='store_true',
        help='查看当前PAM配置'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default="/etc/pam.d/sshd",
        help='指定PAM配置文件路径（默认: /etc/pam.d/sshd）'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='验证当前配置的安全性'
    )
    
    parser.add_argument(
        '--version',
        action='store_true',
        help='显示版本信息'
    )
    
    args = parser.parse_args()
    
    # 显示版本信息
    if args.version:
        from . import __version__
        print(f"SSH PAM Manager v{__version__}")
        return
    
    try:
        # 创建PAM管理器实例
        pam_manager = PAMManager(args.config)
        
        # 命令行模式：查看配置
        if args.view:
            configs = pam_manager.read_config()
            
            if not configs:
                print("未找到有效的PAM配置")
                return
            
            print(f"PAM配置文件: {args.config}")
            print("-" * 80)
            print(f"{'行号':<4} {'类型':<8} {'控制标志':<15} {'模块':<20} {'参数'}")
            print("-" * 80)
            
            for config in configs:
                line_num = config.get('line_number', 'N/A')
                print(f"{line_num:<4} {config['type']:<8} {config['control']:<15} {config['module']:<20} {config['args']}")
            
            print("-" * 80)
            return
        
        # 命令行模式：验证配置
        if args.validate:
            configs = pam_manager.read_config()
            validator = ConfigValidator()
            
            print(f"验证PAM配置文件: {args.config}")
            print("=" * 50)
            
            # 验证每个配置项
            all_valid = True
            for config in configs:
                is_valid, errors = validator.validate_config(config)
                
                if not is_valid:
                    all_valid = False
                    print(f"❌ 行 {config.get('line_number', 'N/A')} 配置错误:")
                    for error in errors:
                        print(f"   - {error}")
                else:
                    print(f"✅ 行 {config.get('line_number', 'N/A')} 配置验证通过")
            
            # 检查安全风险
            warnings = validator.check_security_risks(configs)
            if warnings:
                print("\n⚠️  安全警告:")
                for warning in warnings:
                    print(f"   - {warning}")
            
            if all_valid and not warnings:
                print("\n🎉 所有配置验证通过，无安全风险")
            else:
                print("\n🔍 请仔细检查上述问题和警告")
            
            return
        
        # 交互式模式
        if not args.view and not args.validate:
            # 检查配置文件是否存在
            configs = pam_manager.read_config()
            if not configs:
                print(f"文件错误: PAM配置文件不存在: {args.config} 请检查PAM配置文件是否存在")
                print("请使用 --config 参数指定有效的PAM配置文件")
                sys.exit(1)
                
            cli = CLIInterface()
            cli.run()
    
    except PermissionError as e:
        print(f"权限错误: {e}")
        print("请使用sudo或以root用户身份运行此工具")
        sys.exit(1)
    
    except FileNotFoundError as e:
        print(f"文件错误: {e}")
        print("请检查PAM配置文件是否存在")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(0)
    
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()