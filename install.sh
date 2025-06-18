#!/bin/bash

# NetFlow监控工具安装脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [[ -f /etc/redhat-release ]]; then
        OS="Red Hat Enterprise Linux"
        VER=$(grep -oE '[0-9]+\.[0-9]+' /etc/redhat-release)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    log_info "检测到操作系统: $OS $VER"
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt-get update
        apt-get install -y python3 python3-pip python3-venv python3-dev \
                          tcpdump net-tools libpcap-dev build-essential \
                          sqlite3 curl wget
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Rocky"* ]]; then
        yum update -y
        yum install -y python3 python3-pip python3-devel gcc gcc-c++ \
                      tcpdump net-tools libpcap-devel sqlite curl wget
    elif [[ "$OS" == *"Fedora"* ]]; then
        dnf update -y
        dnf install -y python3 python3-pip python3-devel gcc gcc-c++ \
                      tcpdump net-tools libpcap-devel sqlite curl wget
    else
        log_warning "未识别的操作系统，请手动安装以下依赖:"
        echo "- Python 3.7+"
        echo "- pip3"
        echo "- tcpdump"
        echo "- libpcap-dev"
        echo "- gcc"
        read -p "是否继续安装? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "系统依赖安装完成"
}

# 创建虚拟环境
create_venv() {
    log_info "创建Python虚拟环境..."
    
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        log_success "虚拟环境创建完成"
    else
        log_info "虚拟环境已存在"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖包..."
    
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        log_success "Python依赖包安装完成"
    else
        log_error "requirements.txt文件不存在"
        exit 1
    fi
}

# 下载GeoIP数据库
download_geoip_db() {
    log_info "配置GeoIP数据库..."
    
    mkdir -p data
    
    # 检查是否已存在数据库文件
    if [[ -f "data/GeoLite2-City.mmdb" ]]; then
        log_info "GeoIP数据库已存在"
        return
    fi
    
    log_warning "GeoIP数据库需要从MaxMind下载"
    echo "由于许可证要求，需要手动下载GeoIP数据库："
    echo "1. 访问 https://www.maxmind.com/en/geolite2/signup"
    echo "2. 注册免费账户"
    echo "3. 下载 GeoLite2-City.mmdb 文件"
    echo "4. 将文件放置到 data/GeoLite2-City.mmdb"
    echo ""
    echo "或者程序将使用在线API进行IP归属地查询"
}

# 设置权限
setup_permissions() {
    log_info "设置文件权限..."
    
    # 设置主程序可执行权限
    chmod +x main.py
    chmod +x install.sh
    
    # 设置tcpdump权限（允许非root用户使用）
    if command -v tcpdump >/dev/null 2>&1; then
        setcap cap_net_raw,cap_net_admin=eip $(which tcpdump) 2>/dev/null || true
    fi
    
    log_success "权限设置完成"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."
    
    INSTALL_DIR=$(pwd)
    SERVICE_FILE="/etc/systemd/system/netflow-monitor.service"
    
    cat > $SERVICE_FILE << EOF
[Unit]
Description=NetFlow Network Traffic Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    log_success "systemd服务创建完成"
    
    echo "要启用服务，请运行:"
    echo "  systemctl enable netflow-monitor"
    echo "  systemctl start netflow-monitor"
}

# 运行测试
run_tests() {
    log_info "运行基本测试..."
    
    source venv/bin/activate
    
    # 测试Python模块导入
    python3 -c "
import sys
sys.path.append('src')
try:
    from network_monitor import NetworkMonitor
    from geo_locator import GeoLocator  
    from database import DatabaseManager
    print('✓ 核心模块导入成功')
except ImportError as e:
    print(f'✗ 模块导入失败: {e}')
    sys.exit(1)
"
    
    # 测试依赖检查
    python3 main.py --check-deps
    
    log_success "测试完成"
}

# 显示安装完成信息
show_completion_info() {
    log_success "NetFlow监控工具安装完成！"
    
    echo ""
    echo "启动方式："
    echo "  1. 直接启动: python3 main.py"
    echo "  2. 指定接口: python3 main.py -i eth0 -p 8080"
    echo "  3. 后台服务: systemctl start netflow-monitor"
    echo ""
    echo "Web界面："
    echo "  http://localhost:8080"
    echo ""  
    echo "常用命令："
    echo "  列出网络接口: python3 main.py --list-interfaces"
    echo "  检查依赖: python3 main.py --check-deps"
    echo "  查看帮助: python3 main.py --help"
    echo ""
    
    if [[ ! -f "data/GeoLite2-City.mmdb" ]]; then
        log_warning "请记得下载GeoIP数据库以获得完整的IP归属地功能"
    fi
}

# 主安装流程
main() {
    echo "=================================================="
    echo "    NetFlow 网络流量监控工具 - 安装脚本"
    echo "=================================================="
    echo ""
    
    check_root
    detect_os
    
    log_info "开始安装过程..."
    
    install_system_deps
    create_venv
    install_python_deps
    download_geoip_db
    setup_permissions
    create_systemd_service
    run_tests
    
    show_completion_info
    
    log_success "安装完成！"
}

# 错误处理
trap 'log_error "安装过程中发生错误，请检查输出信息"; exit 1' ERR

# 运行主函数
main "$@"