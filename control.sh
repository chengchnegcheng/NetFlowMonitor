#!/bin/bash

# NetFlow监控系统控制脚本
# 支持启动、停止、重启、状态查看功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/netflow_monitor.pid"
LOG_FILE="$SCRIPT_DIR/logs/system.log"
VENV_DIR="$SCRIPT_DIR/venv"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限才能运行（用于网络数据包捕获）"
        echo "请使用: sudo $0 $1"
        exit 1
    fi
}

# 检查虚拟环境
check_virtualenv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_error "虚拟环境不存在，请先运行安装脚本: ./install.sh"
        exit 1
    fi
}

# 激活虚拟环境
activate_venv() {
    source "$VENV_DIR/bin/activate"
}

# 检查进程是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID文件存在但进程不存在，清理PID文件
            rm -f "$PID_FILE"
            return 1
        fi
    else
        return 1
    fi
}

# 获取进程ID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# 启动系统
start_system() {
    print_info "正在启动NetFlow监控系统..."
    
    # 检查是否已经运行
    if is_running; then
        print_warning "系统已经在运行中 (PID: $(get_pid))"
        return 0
    fi
    
    # 检查虚拟环境
    check_virtualenv
    
    # 激活虚拟环境
    activate_venv
    
    # 检查网络接口
    print_info "检查网络接口..."
    python3 "$SCRIPT_DIR/fix_interface.py" --auto-fix
    
    # 检查防火墙端口
    print_info "检查防火墙配置..."
    if command -v firewall-cmd >/dev/null 2>&1; then
        if ! firewall-cmd --list-ports | grep -q "8080/tcp"; then
            print_info "开放防火墙端口8080..."
            firewall-cmd --permanent --add-port=8080/tcp
            firewall-cmd --reload
        fi
    fi
    
    # 启动主程序
    print_info "启动监控程序..."
    cd "$SCRIPT_DIR"
    nohup python3 main.py --daemon > "$LOG_FILE" 2>&1 &
    local main_pid=$!
    
    # 等待一秒确保程序启动
    sleep 2
    
    # 检查程序是否成功启动
    if ps -p "$main_pid" > /dev/null 2>&1; then
        echo "$main_pid" > "$PID_FILE"
        print_success "NetFlow监控系统启动成功!"
        print_info "进程ID: $main_pid"
        print_info "Web界面: http://$(hostname -I | awk '{print $1}'):8080"
        print_info "日志文件: $LOG_FILE"
    else
        print_error "程序启动失败，请检查日志: $LOG_FILE"
        exit 1
    fi
}

# 停止系统
stop_system() {
    print_info "正在停止NetFlow监控系统..."
    
    if ! is_running; then
        print_warning "系统未运行"
        return 0
    fi
    
    local pid=$(get_pid)
    print_info "正在停止进程 (PID: $pid)..."
    
    # 发送TERM信号
    if kill -TERM "$pid" 2>/dev/null; then
        # 等待进程优雅退出
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
            sleep 1
            ((count++))
        done
        
        # 如果进程仍在运行，强制终止
        if ps -p "$pid" > /dev/null 2>&1; then
            print_warning "进程未能优雅退出，强制终止..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
    fi
    
    # 清理PID文件
    rm -f "$PID_FILE"
    
    # 停止相关Python进程
    pkill -f "python3.*main.py" || true
    pkill -f "python3.*network_monitor.py" || true
    pkill -f "python3.*app.py" || true
    
    print_success "NetFlow监控系统已停止"
}

# 重启系统
restart_system() {
    print_info "正在重启NetFlow监控系统..."
    stop_system
    sleep 2
    start_system
}

# 显示系统状态
show_status() {
    echo "======================================"
    echo "      NetFlow监控系统状态"
    echo "======================================"
    
    if is_running; then
        local pid=$(get_pid)
        print_success "系统状态: 运行中"
        echo "进程ID: $pid"
        
        # 显示进程信息
        if ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem --no-headers 2>/dev/null; then
            echo ""
        fi
        
        # 显示网络连接
        echo "监听端口:"
        netstat -tlnp 2>/dev/null | grep ":8080" || echo "  未检测到8080端口监听"
        
        # 显示Web界面地址
        local ip=$(hostname -I | awk '{print $1}')
        echo "Web界面: http://$ip:8080"
        
    else
        print_warning "系统状态: 未运行"
    fi
    
    echo ""
    echo "配置文件: $SCRIPT_DIR/config.yaml"
    echo "日志文件: $LOG_FILE"
    echo "PID文件: $PID_FILE"
    
    # 显示最近的日志
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "最近日志 (最后10行):"
        echo "--------------------------------------"
        tail -n 10 "$LOG_FILE" 2>/dev/null || echo "无法读取日志文件"
    fi
}

# 显示实时日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_info "显示实时日志 (按Ctrl+C退出)..."
        tail -f "$LOG_FILE"
    else
        print_warning "日志文件不存在: $LOG_FILE"
    fi
}

# 显示帮助信息
show_help() {
    echo "NetFlow监控系统控制脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  start     启动系统"
    echo "  stop      停止系统"
    echo "  restart   重启系统"
    echo "  status    显示系统状态"
    echo "  logs      显示实时日志"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  sudo $0 start     # 启动系统"
    echo "  sudo $0 stop      # 停止系统"
    echo "  sudo $0 status    # 查看状态"
    echo ""
    echo "注意: 启动和停止操作需要root权限"
}

# 主函数
main() {
    case "${1:-}" in
        "start")
            check_root "$1"
            start_system
            ;;
        "stop")
            check_root "$1"
            stop_system
            ;;
        "restart")
            check_root "$1"
            restart_system
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 脚本入口
main "$@" 