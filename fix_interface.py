#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络接口自动检测和修复工具
"""

import os
import sys
import yaml
import argparse
import netifaces
from pathlib import Path


def get_available_interfaces():
    """获取可用的网络接口"""
    interfaces = []
    
    try:
        all_interfaces = netifaces.interfaces()
        
        for interface in all_interfaces:
            # 跳过回环接口
            if interface == 'lo':
                continue
                
            # 获取接口地址信息
            addrs = netifaces.ifaddresses(interface)
            
            # 检查是否有IPv4地址
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get('addr')
                    if ip and ip != '127.0.0.1':
                        interfaces.append({
                            'name': interface,
                            'ip': ip,
                            'netmask': addr.get('netmask', ''),
                            'active': True
                        })
                        break
            else:
                # 没有IPv4地址的接口也记录
                interfaces.append({
                    'name': interface,
                    'ip': '',
                    'netmask': '',
                    'active': False
                })
                
    except Exception as e:
        print(f"获取网络接口失败: {e}")
        return []
    
    return interfaces


def get_primary_interface():
    """获取主要网络接口"""
    interfaces = get_available_interfaces()
    
    # 过滤活跃的接口
    active_interfaces = [iface for iface in interfaces if iface['active']]
    
    if not active_interfaces:
        return None
    
    # 优先选择以太网接口
    for iface in active_interfaces:
        if iface['name'].startswith(('eth', 'ens', 'enp')):
            return iface['name']
    
    # 然后选择无线接口
    for iface in active_interfaces:
        if iface['name'].startswith(('wlan', 'wlp')):
            return iface['name']
    
    # 最后选择第一个活跃接口
    return active_interfaces[0]['name']


def load_config(config_path):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"配置文件不存在: {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"配置文件格式错误: {e}")
        return None


def save_config(config, config_path):
    """保存配置文件"""
    try:
        # 确保配置目录存在
        config_dir = os.path.dirname(config_path)
        os.makedirs(config_dir, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False


def check_interface_exists(interface_name):
    """检查指定的网络接口是否存在"""
    try:
        interfaces = netifaces.interfaces()
        return interface_name in interfaces
    except Exception:
        return False


def create_default_config():
    """创建默认配置"""
    return {
        'network': {
            'interface': 'auto',
            'promiscuous_mode': True,
            'buffer_size': 65536
        },
        'web': {
            'host': '0.0.0.0',
            'port': 8080,
            'debug': False
        },
        'database': {
            'path': 'data/netflow.db',
            'cleanup_days': 7
        },
        'geolocation': {
            'enabled': True,
            'database_path': 'data/GeoLite2-City.mmdb',
            'api_key': '',
            'cache_size': 1000
        },
        'monitoring': {
            'session_timeout': 300,
            'max_sessions': 10000,
            'update_interval': 5
        }
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='网络接口检测和修复工具')
    parser.add_argument('--list', action='store_true', help='列出所有可用的网络接口')
    parser.add_argument('--check', help='检查指定接口是否存在')
    parser.add_argument('--auto-fix', action='store_true', help='自动修复配置文件中的接口设置')
    parser.add_argument('--config', default='config/config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 列出所有接口
    if args.list:
        print("可用的网络接口:")
        print("-" * 50)
        interfaces = get_available_interfaces()
        
        if not interfaces:
            print("未找到任何网络接口")
            return
        
        for iface in interfaces:
            status = "活跃" if iface['active'] else "非活跃"
            ip_info = f" ({iface['ip']})" if iface['ip'] else ""
            print(f"  {iface['name']:<15} {status}{ip_info}")
        
        primary = get_primary_interface()
        if primary:
            print(f"\n推荐使用: {primary}")
        return
    
    # 检查指定接口
    if args.check:
        if check_interface_exists(args.check):
            print(f"接口 '{args.check}' 存在")
        else:
            print(f"接口 '{args.check}' 不存在")
            print("\n可用接口:")
            interfaces = get_available_interfaces()
            for iface in interfaces:
                if iface['active']:
                    print(f"  {iface['name']}")
        return
    
    # 自动修复配置
    if args.auto_fix:
        config_path = args.config
        
        # 加载现有配置或创建默认配置
        config = load_config(config_path)
        if config is None:
            print("创建默认配置文件...")
            config = create_default_config()
        
        # 获取当前配置的接口
        current_interface = config.get('network', {}).get('interface', 'auto')
        
        # 检查当前接口是否存在
        if current_interface != 'auto' and check_interface_exists(current_interface):
            print(f"当前接口 '{current_interface}' 正常")
            return
        
        # 自动选择接口
        primary_interface = get_primary_interface()
        
        if primary_interface:
            if current_interface != primary_interface:
                print(f"将接口从 '{current_interface}' 更改为 '{primary_interface}'")
                config['network']['interface'] = primary_interface
                
                if save_config(config, config_path):
                    print(f"配置已更新并保存到 {config_path}")
                else:
                    print("保存配置失败")
                    return 1
            else:
                print(f"接口配置正常: {primary_interface}")
        else:
            print("未找到可用的网络接口")
            return 1
        
        return 0
    
    # 默认显示帮助
    parser.print_help()


if __name__ == "__main__":
    sys.exit(main() or 0) 