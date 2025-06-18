#!/bin/bash

# NetFlow监控工具演示脚本

echo "=================================================="
echo "    NetFlow 网络流量监控工具 - 演示脚本"
echo "=================================================="
echo ""

# 获取当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. 检查系统依赖...${NC}"
python3 main.py --check-deps
echo ""

echo -e "${BLUE}2. 列出可用网络接口...${NC}"
python3 main.py --list-interfaces
echo ""

echo -e "${BLUE}3. 激活虚拟环境...${NC}"
source venv/bin/activate

echo -e "${BLUE}4. 获取主要网络接口...${NC}"
MAIN_INTERFACE=$(python -c "
import netifaces
gateways = netifaces.gateways()
try:
    default_interface = gateways['default'][netifaces.AF_INET][1]
    print(default_interface)
except:
    print('ens33')
")
echo -e "检测到主要网络接口: ${GREEN}$MAIN_INTERFACE${NC}"
echo ""

echo -e "${BLUE}5. 准备启动Web应用...${NC}"
echo "Web界面将在以下地址启动:"
echo -e "  ${GREEN}http://localhost:8080${NC}"
echo -e "  ${GREEN}http://192.168.1.137:8080${NC} (如果从其他设备访问)"
echo ""

echo -e "${YELLOW}使用说明:${NC}"
echo "1. 在Web界面点击 '开始监控' 按钮启动网络监控"
echo "2. 查看实时流量图表和统计信息" 
echo "3. 在 '会话列表' 中查看详细的网络连接"
echo "4. 在 'IP统计' 中查看流量排行"
echo "5. 在 '地理位置' 中查看IP分布地图"
echo "6. 使用 Ctrl+C 停止程序"
echo ""

echo -e "${YELLOW}注意:${NC}"
echo "- 程序需要root权限才能捕获网络数据包"
echo "- 如果没有GeoIP数据库，IP归属地查询将使用在线API"
echo "- 建议在有网络流量的环境中测试以获得最佳效果"
echo ""

read -p "按Enter键启动Web应用，或按Ctrl+C退出..."

echo -e "${GREEN}正在启动NetFlow监控工具...${NC}"
echo "使用接口: $MAIN_INTERFACE"
echo "Web端口: 8080"
echo ""

# 启动应用 (确保使用虚拟环境)
python main.py -i "$MAIN_INTERFACE" -p 8080