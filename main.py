#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetFlow网络流量监控工具主程序
"""

import os
import sys
import signal
import logging
import argparse
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))
sys.path.append(str(project_root / 'web'))

from web.app import NetFlowWebApp


def signal_handler(sig, frame):
    """信号处理器"""
    print("\n正在关闭NetFlow监控工具...")
    sys.exit(0)


def setup_directories():
    """创建必要的目录"""
    directories = [
        'data',
        'logs',
        'config'
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)


def check_permissions():
    """检查运行权限"""
    if os.geteuid() != 0:
        print("警告: 建议以root权限运行以获得最佳的网络监控功能")
        response = input("是否继续运行? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='NetFlow网络流量监控工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                          # 使用默认配置启动
  %(prog)s -i eth0 -p 8080         # 指定网络接口和端口
  %(prog)s -c config/custom.yaml   # 使用自定义配置文件
  %(prog)s --check-deps            # 检查依赖
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        help='配置文件路径',
        default=str(project_root / 'config' / 'config.yaml')
    )
    
    parser.add_argument(
        '--interface', '-i',
        help='网络接口名称 (例如: eth0, wlan0)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        help='Web服务端口 (默认: 8080)'
    )
    
    parser.add_argument(
        '--host',
        help='Web服务监听地址 (默认: 0.0.0.0)',
        default='0.0.0.0'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='检查系统依赖'
    )
    
    parser.add_argument(
        '--list-interfaces',
        action='store_true',
        help='列出可用的网络接口'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='以守护进程模式运行'
    )
    
    args = parser.parse_args()
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建必要目录
    setup_directories()
    
    # 检查依赖
    if args.check_deps:
        check_dependencies()
        return
    
    # 列出网络接口
    if args.list_interfaces:
        list_network_interfaces()
        return
    
    # 检查运行权限 (守护进程模式跳过交互式检查)
    if not args.debug and not args.daemon:
        check_permissions()
    
    try:
        # 在守护进程模式下设置日志
        if args.daemon:
            # 配置日志到文件
            log_file = project_root / 'logs' / 'system.log'
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
            # 重定向标准输出到日志文件
            sys.stdout = open(log_file, 'a')
            sys.stderr = open(log_file, 'a')
        
        # 创建Web应用
        app = NetFlowWebApp(config_path=args.config)
        
        # 覆盖配置参数
        if args.interface:
            app.config['network']['interface'] = args.interface
        if args.port:
            app.config['web']['port'] = args.port
        if args.host:
            app.config['web']['host'] = args.host
        if args.debug:
            app.config['web']['debug'] = True
        
        # 显示启动信息 (非守护进程模式)
        if not args.daemon:
            print_startup_info(app.config)
        else:
            logging.info("NetFlow监控系统已启动 (守护进程模式)")
            logging.info(f"网络接口: {app.config['network']['interface']}")
            logging.info(f"Web服务: http://{app.config['web']['host']}:{app.config['web']['port']}")
        
        # 运行应用
        app.run()
        
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
    except Exception as e:
        print(f"启动失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def check_dependencies():
    """检查系统依赖"""
    print("检查系统依赖...")
    
    dependencies = {
        'Python模块': [
            ('flask', 'Flask Web框架'),
            ('flask_socketio', 'WebSocket支持'),
            ('scapy', '网络数据包处理'),
            ('psutil', '系统信息获取'),
            ('requests', 'HTTP请求'),
            ('yaml', 'YAML配置文件'),
            ('netifaces', '网络接口信息')
        ],
        '可选模块': [
            ('geoip2', 'IP地理位置查询'),
            ('maxminddb', 'MaxMind数据库')
        ]
    }
    
    all_ok = True
    
    for category, modules in dependencies.items():
        print(f"\n{category}:")
        for module, description in modules:
            try:
                __import__(module)
                print(f"  ✓ {module} - {description}")
            except ImportError:
                print(f"  ✗ {module} - {description} (未安装)")
                if category == 'Python模块':
                    all_ok = False
    
    # 检查系统工具
    print("\n系统工具:")
    system_tools = [
        ('tcpdump', '数据包捕获工具'),
        ('netstat', '网络连接状态'),
        ('ss', '套接字统计')
    ]
    
    import shutil
    for tool, description in system_tools:
        if shutil.which(tool):
            print(f"  ✓ {tool} - {description}")
        else:
            print(f"  ✗ {tool} - {description} (未安装)")
    
    if all_ok:
        print("\n✓ 所有必需依赖都已安装")
    else:
        print("\n✗ 存在缺失的必需依赖，请先安装:")
        print("  pip install -r requirements.txt")
    
    # 检查权限
    print("\n权限检查:")
    if os.geteuid() == 0:
        print("  ✓ 以root权限运行 (推荐)")
    else:
        print("  ⚠ 未以root权限运行 (可能影响网络监控功能)")


def list_network_interfaces():
    """列出可用的网络接口"""
    print("可用的网络接口:")
    
    try:
        import netifaces
        
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            print(f"\n接口: {interface}")
            
            # 获取接口地址
            addrs = netifaces.ifaddresses(interface)
            
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    print(f"  IPv4: {addr.get('addr', 'N/A')}")
            
            if netifaces.AF_INET6 in addrs:
                for addr in addrs[netifaces.AF_INET6]:
                    print(f"  IPv6: {addr.get('addr', 'N/A')}")
    
    except ImportError:
        print("需要安装netifaces模块: pip install netifaces")
    except Exception as e:
        print(f"获取网络接口失败: {e}")


def print_startup_info(config):
    """打印启动信息"""
    print("\n" + "="*60)
    print("   NetFlow 网络流量监控工具")
    print("="*60)
    print(f"网络接口: {config['network']['interface']}")
    print(f"Web服务: http://{config['web']['host']}:{config['web']['port']}")
    print(f"数据库: {config['database']['path']}")
    
    if config['geolocation']['enabled']:
        print("IP归属地: 已启用")
        if config['geolocation'].get('database_path'):
            print(f"GeoIP数据库: {config['geolocation']['database_path']}")
    else:
        print("IP归属地: 已禁用")
    
    print("="*60)
    print("使用说明:")
    print("1. 在Web界面点击'开始监控'按钮启动网络监控")
    print("2. 查看实时流量图表和统计信息")
    print("3. 在'会话列表'中查看详细的网络连接")
    print("4. 在'IP统计'中查看流量排行")
    print("5. 在'地理位置'中查看IP分布地图")
    print("6. 使用Ctrl+C停止程序")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()