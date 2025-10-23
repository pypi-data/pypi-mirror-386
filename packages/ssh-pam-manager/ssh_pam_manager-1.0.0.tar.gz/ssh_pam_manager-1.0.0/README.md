# SSH PAM Manager

一个用于管理Linux系统SSH PAM配置的Python工具。

## 功能特性

- 📖 **配置读取**: 查看当前SSH PAM配置
- ✏️ **配置修改**: 修改现有的PAM配置项
- ➕ **配置添加**: 添加新的PAM配置规则
- 🗑️ **配置删除**: 删除不需要的PAM配置
- 🔒 **安全验证**: 验证PAM配置的安全性和正确性
- 💾 **自动备份**: 修改前自动备份原配置
- 🖥️ **交互界面**: 友好的命令行交互界面

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://gitee.com/liumou_site/ssh-pam-management.git
cd ssh-pam-management

# 安装到系统
pip3 install .

# 或者使用开发模式
pip3 install -e .
```

### 从PyPI安装（未来版本）

```bash
pip3 install ssh-pam-manager
```

## 使用方法

### 交互式界面

```bash
# 启动交互式界面
ssh-pam-manager
```

### 命令行模式

```bash
# 查看当前配置
ssh-pam-manager --view

# 验证配置安全性
ssh-pam-manager --validate

# 指定自定义配置文件路径
ssh-pam-manager --config /etc/pam.d/sshd --view

# 显示版本信息
ssh-pam-manager --version
```

## 项目结构

```
ssh-pam-manager/
├── src/
│   └── ssh_pam_manager/
│       ├── __init__.py          # 包初始化
│       ├── main.py              # 主入口点
│       ├── pam_parser.py        # PAM配置解析器
│       ├── pam_manager.py       # PAM配置管理器
│       ├── cli_interface.py     # 命令行交互界面
│       └── config_validator.py  # 配置验证器
├── pyproject.toml               # 现代打包配置
├── setup.py                    # 兼容性打包配置
├── README.md                   # 项目文档
└── LICENSE                     # 许可证文件
```

## 模块说明

### pam_parser.py
- **PAMParser类**: 负责解析PAM配置文件格式
- 支持解析标准的PAM配置行格式
- 处理注释和空行

### pam_manager.py  
- **PAMManager类**: 核心配置管理功能
- 提供配置的读取、修改、添加、删除操作
- 自动备份机制确保操作安全

### cli_interface.py
- **CLIInterface类**: 用户交互界面
- 提供菜单驱动的命令行操作
- 支持配置预览和确认

### config_validator.py
- **ConfigValidator类**: 配置验证功能
- 验证PAM配置的合法性和安全性
- 检测潜在的安全风险

## PAM配置格式

工具支持标准的PAM配置格式：

```
类型    控制标志    模块    参数
```

示例：
```
auth    required    pam_unix.so    nullok
auth    optional    pam_echo.so    file=/etc/issue
```

## 权限要求

由于PAM配置文件通常位于`/etc/pam.d/`目录下，需要root权限才能修改：

```bash
sudo ssh-pam-manager
```

或者：

```bash
sudo ssh-pam-manager --view
```

## 开发

### 设置开发环境

```bash
# 克隆项目
git clone https://gitee.com/liumou_site/ssh-pam-management.git
cd ssh-pam-management

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装开发依赖
pip install -e .
```

### 运行测试

```bash
# 运行基本功能测试
python -m pytest tests/

# 运行代码风格检查
flake8 src/

# 运行类型检查
mypy src/
```

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。

## 免责声明

此工具用于系统管理目的。在使用前请确保：

1. 理解PAM配置的工作原理
2. 在测试环境中验证配置更改
3. 备份重要的系统配置文件
4. 了解修改PAM配置可能带来的安全影响

作者对使用此工具造成的任何系统问题不承担责任。
