#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络流量监控核心模块
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from scapy.all import sniff, IP, TCP, UDP, ICMP
import netifaces
import psutil


@dataclass
class PacketInfo:
    """数据包信息"""
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    length: int
    flags: str = ""


@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    start_time: float
    last_seen: float
    packets_sent: int
    packets_received: int
    bytes_sent: int
    bytes_received: int
    state: str = "ACTIVE"


class NetworkMonitor:
    """网络流量监控器"""
    
    def __init__(self, interface: str = None, session_timeout: int = 300):
        # 先设置基本属性和日志
        self.interface = interface or self._get_default_interface()
        self.session_timeout = session_timeout
        self.running = False
        
        # 设置日志 (必须在验证接口前设置)
        self.logger = logging.getLogger(__name__)
        
        # 验证网络接口是否存在
        self._validate_interface()
        
        # 数据存储
        self.sessions: Dict[str, SessionInfo] = {}
        self.ip_stats: Dict[str, Dict] = defaultdict(lambda: {
            'bytes_sent': 0,
            'bytes_received': 0,
            'packets_sent': 0,
            'packets_received': 0,
            'sessions': set(),
            'first_seen': None,
            'last_seen': None
        })
        
        # 实时统计
        self.traffic_history = deque(maxlen=3600)  # 保存1小时的流量历史
        self.current_traffic = {'timestamp': time.time(), 'bytes': 0, 'packets': 0}
        
        # 线程锁
        self.lock = threading.Lock()
    
    def _validate_interface(self):
        """验证网络接口是否存在"""
        try:
            available_interfaces = netifaces.interfaces()
            
            if self.interface not in available_interfaces:
                self.logger.warning(f"指定的网络接口 '{self.interface}' 不存在")
                self.logger.info(f"可用接口: {', '.join(available_interfaces)}")
                
                # 自动选择替代接口
                old_interface = self.interface
                self.interface = self._get_default_interface()
                
                self.logger.info(f"自动切换到接口: {self.interface}")
                
                if self.interface not in available_interfaces:
                    raise ValueError(f"无法找到可用的网络接口，可用接口: {available_interfaces}")
            
            self.logger.info(f"使用网络接口: {self.interface}")
            
        except Exception as e:
            self.logger.error(f"接口验证失败: {e}")
            raise
        
    def _get_default_interface(self) -> str:
        """获取默认网络接口"""
        try:
            # 获取默认路由的接口
            gateways = netifaces.gateways()
            default_interface = gateways['default'][netifaces.AF_INET][1]
            return default_interface
        except:
            # 如果获取失败，返回第一个活跃的网络接口
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                if iface != 'lo' and not iface.startswith('docker') and not iface.startswith('br-'):
                    # 排除回环接口、Docker接口和桥接接口
                    return iface
            # 如果还是没找到，返回第一个非回环接口
            for iface in interfaces:
                if iface != 'lo':
                    return iface
            return 'ens33'  # 最后默认返回ens33
    
    def _generate_session_id(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int, protocol: str) -> str:
        """生成会话ID"""
        # 确保会话ID的一致性（不受方向影响）
        if src_ip < dst_ip or (src_ip == dst_ip and src_port < dst_port):
            return f"{src_ip}:{src_port}-{dst_ip}:{dst_port}-{protocol}"
        else:
            return f"{dst_ip}:{dst_port}-{src_ip}:{src_port}-{protocol}"
    
    def _packet_handler(self, packet):
        """数据包处理函数"""
        try:
            if not packet.haslayer(IP):
                return
                
            ip_layer = packet[IP]
            timestamp = time.time()
            
            # 提取基本信息
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            length = len(packet)
            protocol = "OTHER"
            src_port = 0
            dst_port = 0
            flags = ""
            
            # 根据协议提取端口信息
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                protocol = "TCP"
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                flags = str(tcp_layer.flags)
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                protocol = "UDP"
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
            elif packet.haslayer(ICMP):
                protocol = "ICMP"
            
            # 创建数据包信息
            packet_info = PacketInfo(
                timestamp=timestamp,
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol,
                length=length,
                flags=flags
            )
            
            # 处理数据包
            self._process_packet(packet_info)
            
        except Exception as e:
            self.logger.error(f"处理数据包时出错: {e}")
    
    def _process_packet(self, packet_info: PacketInfo):
        """处理数据包信息"""
        with self.lock:
            timestamp = packet_info.timestamp
            
            # 更新实时流量统计
            self.current_traffic['bytes'] += packet_info.length
            self.current_traffic['packets'] += 1
            
            # 每秒保存一次流量历史
            if timestamp - self.current_traffic['timestamp'] >= 1.0:
                self.traffic_history.append({
                    'timestamp': self.current_traffic['timestamp'],
                    'bytes': self.current_traffic['bytes'],
                    'packets': self.current_traffic['packets']
                })
                self.current_traffic = {'timestamp': timestamp, 'bytes': 0, 'packets': 0}
            
            # 更新IP统计
            self._update_ip_stats(packet_info)
            
            # 更新会话信息
            if packet_info.protocol in ['TCP', 'UDP']:
                self._update_session(packet_info)
    
    def _update_ip_stats(self, packet_info: PacketInfo):
        """更新IP统计信息"""
        src_ip = packet_info.src_ip
        dst_ip = packet_info.dst_ip
        length = packet_info.length
        timestamp = packet_info.timestamp
        
        # 更新源IP统计
        src_stats = self.ip_stats[src_ip]
        src_stats['bytes_sent'] += length
        src_stats['packets_sent'] += 1
        if src_stats['first_seen'] is None:
            src_stats['first_seen'] = timestamp
        src_stats['last_seen'] = timestamp
        
        # 更新目标IP统计
        dst_stats = self.ip_stats[dst_ip]
        dst_stats['bytes_received'] += length
        dst_stats['packets_received'] += 1
        if dst_stats['first_seen'] is None:
            dst_stats['first_seen'] = timestamp
        dst_stats['last_seen'] = timestamp
    
    def _update_session(self, packet_info: PacketInfo):
        """更新会话信息"""
        session_id = self._generate_session_id(
            packet_info.src_ip, packet_info.dst_ip,
            packet_info.src_port, packet_info.dst_port,
            packet_info.protocol
        )
        
        if session_id not in self.sessions:
            # 创建新会话
            session = SessionInfo(
                session_id=session_id,
                src_ip=packet_info.src_ip,
                dst_ip=packet_info.dst_ip,
                src_port=packet_info.src_port,
                dst_port=packet_info.dst_port,
                protocol=packet_info.protocol,
                start_time=packet_info.timestamp,
                last_seen=packet_info.timestamp,
                packets_sent=0,
                packets_received=0,
                bytes_sent=0,
                bytes_received=0
            )
            self.sessions[session_id] = session
            
            # 更新IP统计中的会话信息
            self.ip_stats[packet_info.src_ip]['sessions'].add(session_id)
            self.ip_stats[packet_info.dst_ip]['sessions'].add(session_id)
        
        # 更新会话统计
        session = self.sessions[session_id]
        session.last_seen = packet_info.timestamp
        
        # 判断数据包方向
        if (packet_info.src_ip == session.src_ip and 
            packet_info.src_port == session.src_port):
            # 源到目标
            session.packets_sent += 1
            session.bytes_sent += packet_info.length
        else:
            # 目标到源
            session.packets_received += 1
            session.bytes_received += packet_info.length
    
    def _cleanup_sessions(self):
        """清理过期会话"""
        current_time = time.time()
        expired_sessions = []
        
        with self.lock:
            for session_id, session in self.sessions.items():
                if current_time - session.last_seen > self.session_timeout:
                    expired_sessions.append(session_id)
                    session.state = "EXPIRED"
            
            # 删除过期会话
            for session_id in expired_sessions:
                del self.sessions[session_id]
        
        if expired_sessions:
            self.logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
    
    def start(self):
        """启动监控"""
        if self.running:
            return
            
        try:
            # 重新验证接口（防止运行时接口状态变化）
            self._validate_interface()
            
            self.running = True
            self.logger.info(f"开始监控网络接口: {self.interface}")
            
            # 启动清理线程
            cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            cleanup_thread.start()
            
            # 开始捕获数据包
            sniff(
                iface=self.interface,
                prn=self._packet_handler,
                store=False,
                stop_filter=lambda x: not self.running
            )
            
        except PermissionError:
            self.running = False
            error_msg = "权限不足，请以root权限运行或设置CAP_NET_RAW capability"
            self.logger.error(error_msg)
            raise PermissionError(error_msg)
        except Exception as e:
            self.running = False
            if "not found" in str(e).lower():
                # 接口不存在的特殊处理
                available_interfaces = netifaces.interfaces()
                error_msg = f"网络接口 '{self.interface}' 不存在，可用接口: {', '.join(available_interfaces)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                self.logger.error(f"数据包捕获失败: {e}")
                raise
    
    def _cleanup_worker(self):
        """清理工作线程"""
        while self.running:
            time.sleep(60)  # 每分钟清理一次
            self._cleanup_sessions()
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.logger.info("网络监控已停止")
    
    def get_sessions(self) -> List[Dict]:
        """获取当前会话列表"""
        with self.lock:
            sessions = []
            for session in self.sessions.values():
                sessions.append({
                    'session_id': session.session_id,
                    'src_ip': session.src_ip,
                    'dst_ip': session.dst_ip,
                    'src_port': session.src_port,
                    'dst_port': session.dst_port,
                    'protocol': session.protocol,
                    'start_time': datetime.fromtimestamp(session.start_time).isoformat(),
                    'last_seen': datetime.fromtimestamp(session.last_seen).isoformat(),
                    'duration': session.last_seen - session.start_time,
                    'packets_sent': session.packets_sent,
                    'packets_received': session.packets_received,
                    'bytes_sent': session.bytes_sent,
                    'bytes_received': session.bytes_received,
                    'total_packets': session.packets_sent + session.packets_received,
                    'total_bytes': session.bytes_sent + session.bytes_received,
                    'state': session.state
                })
            return sorted(sessions, key=lambda x: x['last_seen'], reverse=True)
    
    def get_ip_stats(self) -> List[Dict]:
        """获取IP统计信息"""
        with self.lock:
            stats = []
            for ip, data in self.ip_stats.items():
                stats.append({
                    'ip': ip,
                    'bytes_sent': data['bytes_sent'],
                    'bytes_received': data['bytes_received'],
                    'total_bytes': data['bytes_sent'] + data['bytes_received'],
                    'packets_sent': data['packets_sent'],
                    'packets_received': data['packets_received'],
                    'total_packets': data['packets_sent'] + data['packets_received'],
                    'session_count': len(data['sessions']),
                    'first_seen': datetime.fromtimestamp(data['first_seen']).isoformat() if data['first_seen'] else None,
                    'last_seen': datetime.fromtimestamp(data['last_seen']).isoformat() if data['last_seen'] else None
                })
            return sorted(stats, key=lambda x: x['total_bytes'], reverse=True)
    
    def get_traffic_history(self) -> List[Dict]:
        """获取流量历史数据"""
        with self.lock:
            history = []
            for data in self.traffic_history:
                history.append({
                    'timestamp': datetime.fromtimestamp(data['timestamp']).isoformat(),
                    'bytes': data['bytes'],
                    'packets': data['packets']
                })
            return history
    
    def get_sessions_dict(self) -> Dict[str, Dict]:
        """获取会话字典（用于数据同步）"""
        with self.lock:
            sessions_dict = {}
            for session_id, session in self.sessions.items():
                sessions_dict[session_id] = {
                    'session_id': session_id,
                    'src_ip': session.src_ip,
                    'dst_ip': session.dst_ip,
                    'src_port': session.src_port,
                    'dst_port': session.dst_port,
                    'protocol': session.protocol,
                    'start_time': session.start_time,
                    'last_seen': session.last_seen,
                    'packets_sent': session.packets_sent,
                    'packets_recv': session.packets_received,
                    'bytes_sent': session.bytes_sent,
                    'bytes_recv': session.bytes_received,
                    'state': session.state
                }
            return sessions_dict
    
    def get_ip_stats_dict(self) -> Dict[str, Dict]:
        """获取IP统计字典（用于数据同步）"""
        with self.lock:
            stats_dict = {}
            for ip, data in self.ip_stats.items():
                stats_dict[ip] = {
                    'ip': ip,
                    'bytes_sent': data['bytes_sent'],
                    'bytes_recv': data['bytes_received'],
                    'packets_sent': data['packets_sent'],
                    'packets_recv': data['packets_received'],
                    'session_count': len(data['sessions']),
                    'first_seen': data['first_seen'] or 0,
                    'last_seen': data['last_seen'] or 0
                }
            return stats_dict
    
    def get_summary(self) -> Dict:
        """获取监控摘要信息"""
        with self.lock:
            total_sessions = len(self.sessions)
            total_ips = len(self.ip_stats)
            
            total_bytes = sum(data['bytes_sent'] + data['bytes_received'] 
                            for data in self.ip_stats.values())
            total_packets = sum(data['packets_sent'] + data['packets_received'] 
                              for data in self.ip_stats.values())
            
            return {
                'interface': self.interface,
                'running': self.running,
                'total_sessions': total_sessions,
                'active_sessions': sum(1 for s in self.sessions.values() if s.state == 'ACTIVE'),
                'total_ips': total_ips,
                'total_bytes': total_bytes,
                'total_packets': total_packets,
                'uptime': time.time() - (min(data['first_seen'] for data in self.ip_stats.values()) 
                                       if self.ip_stats else time.time())
            }


if __name__ == "__main__":
    # 测试代码
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    monitor = NetworkMonitor()
    
    try:
        print(f"开始监控网络接口: {monitor.interface}")
        print("按 Ctrl+C 停止监控")
        
        # 启动监控
        monitor_thread = threading.Thread(target=monitor.start)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 定期输出统计信息
        while True:
            time.sleep(10)
            summary = monitor.get_summary()
            print(f"\n=== 监控摘要 ===")
            print(f"活跃会话: {summary['active_sessions']}")
            print(f"总IP数: {summary['total_ips']}")
            print(f"总流量: {summary['total_bytes']} 字节")
            print(f"总数据包: {summary['total_packets']}")
            
    except KeyboardInterrupt:
        print("\n停止监控...")
        monitor.stop()
        sys.exit(0)