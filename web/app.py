#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetFlow监控Web应用
"""

import os
import sys
import json
import yaml
import logging
import threading
from datetime import datetime
from typing import Dict, List

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from network_monitor import NetworkMonitor
from geo_locator import GeoLocator
from database import DatabaseManager


class NetFlowWebApp:
    """NetFlow监控Web应用"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.db_manager = DatabaseManager(self.config['database']['path'])
        self.geo_locator = GeoLocator(self.config['geolocation'].get('database_path'))
        self.network_monitor = NetworkMonitor(
            interface=self.config['network']['interface'],
            session_timeout=self.config['monitor']['session_timeout']
        )
        
        # 创建Flask应用
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.app = Flask(__name__, template_folder=template_dir)
        self.app.config['SECRET_KEY'] = 'netflow-monitor-secret-key'
        
        # 初始化SocketIO
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
            async_mode='threading',
            ping_timeout=60,
            ping_interval=25
        )
        
        # 监控状态
        self.monitoring = False
        self.monitor_thread = None
        
        # 设置路由
        self._setup_routes()
        self._setup_socketio()
        
        # 配置日志
        self._setup_logging()
    
    def _load_config(self, config_path: str = None) -> Dict:
        """加载配置文件"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'config', 'config.yaml'
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 返回默认配置
            return {
                'network': {'interface': 'eth0'},
                'database': {'path': 'data/netflow.db'},
                'web': {'host': '0.0.0.0', 'port': 8080, 'debug': False},
                'monitor': {'session_timeout': 300},
                'geolocation': {'enabled': True, 'database_path': None}
            }
    
    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _setup_routes(self):
        """设置Web路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def api_status():
            """获取监控状态"""
            summary = self.network_monitor.get_summary()
            db_summary = self.db_manager.get_statistics_summary()
            
            return jsonify({
                'monitoring': self.monitoring,
                'interface': summary.get('interface'),
                'uptime': summary.get('uptime', 0),
                'active_sessions': summary.get('active_sessions', 0),
                'total_ips': summary.get('total_ips', 0),
                'total_bytes': summary.get('total_bytes', 0),
                'total_packets': summary.get('total_packets', 0),
                'db_stats': db_summary
            })
        
        @self.app.route('/api/sessions')
        def api_sessions():
            """获取会话列表"""
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            order_by = request.args.get('order_by', 'last_seen')
            order_direction = request.args.get('order_direction', 'desc')
            
            offset = (page - 1) * per_page
            
            # 构建过滤参数
            filter_params = {}
            for key in ['src_ip', 'dst_ip', 'protocol', 'state']:
                value = request.args.get(key)
                if value:
                    filter_params[key] = value
            
            sessions = self.db_manager.get_sessions(
                limit=per_page, 
                offset=offset, 
                filter_params=filter_params,
                order_by=order_by,
                order_direction=order_direction
            )
            
            # 添加地理位置信息
            for session in sessions:
                if self.config['geolocation']['enabled']:
                    src_location = self.geo_locator.get_location(session['src_ip'])
                    dst_location = self.geo_locator.get_location(session['dst_ip'])
                    
                    session['src_location'] = {
                        'country': src_location.country,
                        'city': src_location.city,
                        'latitude': src_location.latitude,
                        'longitude': src_location.longitude
                    }
                    session['dst_location'] = {
                        'country': dst_location.country,
                        'city': dst_location.city,
                        'latitude': dst_location.latitude,
                        'longitude': dst_location.longitude
                    }
            
            return jsonify({
                'sessions': sessions,
                'page': page,
                'per_page': per_page,
                'total': len(sessions),
                'order_by': order_by,
                'order_direction': order_direction
            })
        
        @self.app.route('/api/ip-stats')
        def api_ip_stats():
            """获取IP统计"""
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            order_by = request.args.get('order_by', 'total_bytes')
            order_direction = request.args.get('order_direction', 'desc')
            
            offset = (page - 1) * per_page
            
            ip_stats = self.db_manager.get_ip_statistics(
                limit=per_page, 
                offset=offset, 
                order_by=order_by,
                order_direction=order_direction
            )
            
            # 添加地理位置信息
            for stat in ip_stats:
                if self.config['geolocation']['enabled']:
                    location = self.geo_locator.get_location(stat['ip'])
                    stat['location'] = {
                        'country': location.country,
                        'country_code': location.country_code,
                        'city': location.city,
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'isp': location.isp
                    }
            
            return jsonify({
                'ip_stats': ip_stats,
                'page': page,
                'per_page': per_page,
                'order_by': order_by,
                'order_direction': order_direction
            })
        
        @self.app.route('/api/traffic-history')
        def api_traffic_history():
            """获取流量历史"""
            hours = request.args.get('hours', 24, type=int)
            
            # 从内存获取实时数据
            live_history = self.network_monitor.get_traffic_history()
            
            # 从数据库获取历史数据
            db_history = self.db_manager.get_traffic_history(hours=hours)
            
            return jsonify({
                'live_data': live_history,
                'historical_data': db_history
            })
        
        @self.app.route('/api/top-talkers')
        def api_top_talkers():
            """获取流量TOP统计"""
            limit = request.args.get('limit', 10, type=int)
            
            ip_stats = self.db_manager.get_ip_statistics(
                limit=limit, 
                order_by='total_bytes'
            )
            
            # 添加地理位置信息
            for stat in ip_stats:
                if self.config['geolocation']['enabled']:
                    location = self.geo_locator.get_location(stat['ip'])
                    stat['location'] = {
                        'country': location.country,
                        'city': location.city,
                        'isp': location.isp
                    }
            
            return jsonify(ip_stats)
        
        @self.app.route('/api/geo-map')
        def api_geo_map():
            """获取地理位置地图数据"""
            if not self.config['geolocation']['enabled']:
                return jsonify({'error': '地理位置功能未启用'})
            
            # 获取活跃IP的地理位置
            ip_stats = self.db_manager.get_ip_statistics(limit=100)
            
            geo_data = []
            for stat in ip_stats:
                location = self.geo_locator.get_location(stat['ip'])
                
                if location.latitude != 0 or location.longitude != 0:
                    geo_data.append({
                        'ip': stat['ip'],
                        'country': location.country,
                        'city': location.city,
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'total_bytes': stat['total_bytes'],
                        'total_packets': stat['total_packets']
                    })
            
            return jsonify(geo_data)
        
        @self.app.route('/api/start-monitoring', methods=['POST'])
        def api_start_monitoring():
            """启动监控"""
            if self.monitoring:
                return jsonify({'error': '监控已在运行'})
            
            try:
                self.monitoring = True
                self.monitor_thread = threading.Thread(
                    target=self._run_monitoring, 
                    daemon=True
                )
                self.monitor_thread.start()
                
                self.db_manager.log_event('MONITOR', '监控启动', severity='INFO')
                return jsonify({'message': '监控已启动'})
                
            except Exception as e:
                self.monitoring = False
                self.logger.error(f"启动监控失败: {e}")
                return jsonify({'error': f'启动监控失败: {e}'})
        
        @self.app.route('/api/stop-monitoring', methods=['POST'])
        def api_stop_monitoring():
            """停止监控"""
            if not self.monitoring:
                return jsonify({'error': '监控未在运行'})
            
            self.monitoring = False
            self.network_monitor.stop()
            
            self.db_manager.log_event('MONITOR', '监控停止', severity='INFO')
            return jsonify({'message': '监控已停止'})
        
        @self.app.route('/api/events')
        def api_events():
            """获取事件日志"""
            limit = request.args.get('limit', 50, type=int)
            severity = request.args.get('severity')
            
            events = self.db_manager.get_event_logs(limit=limit, severity=severity)
            return jsonify(events)
    
    def _setup_socketio(self):
        """设置WebSocket事件"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """客户端连接"""
            self.logger.info('客户端已连接')
            emit('status', {'connected': True})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """客户端断开连接"""
            self.logger.info('客户端已断开连接')
        
        @self.socketio.on('request_update')
        def handle_request_update():
            """客户端请求更新数据"""
            self._emit_real_time_data()
    
    def _run_monitoring(self):
        """运行监控"""
        try:
            self.network_monitor.start()
        except Exception as e:
            self.logger.error(f"监控运行异常: {e}")
            self.monitoring = False
    
    def _emit_real_time_data(self):
        """发送实时数据到客户端"""
        if not self.monitoring:
            return
        
        try:
            # 获取实时统计
            summary = self.network_monitor.get_summary()
            sessions = self.network_monitor.get_sessions()[:10]  # 最新10个会话
            ip_stats = self.network_monitor.get_ip_stats()[:10]  # TOP 10 IP
            
            # 发送数据
            self.socketio.emit('real_time_update', {
                'timestamp': datetime.now().isoformat(),
                'summary': summary,
                'latest_sessions': sessions,
                'top_ips': ip_stats
            })
            
        except Exception as e:
            self.logger.error(f"发送实时数据失败: {e}")
    
    def _data_sync_worker(self):
        """数据同步工作线程"""
        import time
        
        while True:  # 持续运行，不依赖monitoring状态
            try:
                # 检查监控器是否有数据
                summary = self.network_monitor.get_summary()
                if summary.get('total_packets', 0) == 0:
                    # 没有数据，等待后继续
                    time.sleep(5)
                    continue
                
                # 自动设置监控状态
                if not self.monitoring and summary.get('active_sessions', 0) > 0:
                    self.monitoring = True
                    self.logger.info("检测到活跃数据，自动设置监控状态为启用")
                
                # 同步内存数据到数据库
                sessions_dict = self.network_monitor.get_sessions_dict()
                for session_id, session in sessions_dict.items():
                    # 将内存会话对象转换为数据库格式
                    session_data = {
                        'session_id': session_id,
                        'src_ip': session.get('src_ip', ''),
                        'dst_ip': session.get('dst_ip', ''),
                        'src_port': session.get('src_port', 0),
                        'dst_port': session.get('dst_port', 0),
                        'protocol': session.get('protocol', 'TCP'),
                        'start_time': session.get('start_time', 0),
                        'last_seen': session.get('last_seen', 0),
                        'packets_sent': session.get('packets_sent', 0),
                        'packets_received': session.get('packets_recv', 0),  # 修复：使用正确的键名
                        'bytes_sent': session.get('bytes_sent', 0),
                        'bytes_received': session.get('bytes_recv', 0),      # 修复：使用正确的键名
                        'state': session.get('state', 'ACTIVE')
                    }
                    self.db_manager.insert_session(session_data)
                
                # 同步IP统计数据
                ip_stats_dict = self.network_monitor.get_ip_stats_dict()
                for ip, stats in ip_stats_dict.items():
                    # 添加地理位置信息
                    location_info = {}
                    if self.config['geolocation']['enabled']:
                        location = self.geo_locator.get_location(ip)
                        location_info = {
                            'country': location.country,
                            'city': location.city,
                            'latitude': location.latitude,
                            'longitude': location.longitude,
                            'isp': location.isp
                        }
                    
                    stat_data = {
                        'ip': ip,
                        'bytes_sent': stats.get('bytes_sent', 0),
                        'bytes_received': stats.get('bytes_recv', 0),        # 修复：使用正确的键名
                        'packets_sent': stats.get('packets_sent', 0),
                        'packets_received': stats.get('packets_recv', 0),    # 修复：使用正确的键名
                        'session_count': stats.get('session_count', 0),
                        'first_seen': stats.get('first_seen', 0),
                        'last_seen': stats.get('last_seen', 0),
                        'location_info': location_info
                    }
                    self.db_manager.insert_ip_statistics(stat_data)
                
                # 记录流量历史
                traffic_data = {
                    'timestamp': datetime.now().timestamp(),
                    'bytes_per_sec': summary.get('total_bytes', 0) / max(summary.get('uptime', 1), 1),
                    'packets_per_sec': summary.get('total_packets', 0) / max(summary.get('uptime', 1), 1),
                    'active_sessions': summary.get('active_sessions', 0),
                    'active_ips': summary.get('total_ips', 0)
                }
                self.db_manager.insert_traffic_history(traffic_data)
                
                # 发送实时数据到客户端
                self._emit_real_time_data()
                
                time.sleep(5)  # 每5秒同步一次
                
            except Exception as e:
                self.logger.error(f"数据同步失败: {e}")
                time.sleep(10)
    
    def run(self):
        """运行Web应用"""
        try:
            # 创建数据目录
            os.makedirs(os.path.dirname(self.config['database']['path']), exist_ok=True)
            
            # 自动启动网络监控
            try:
                self.monitoring = True
                self.monitor_thread = threading.Thread(
                    target=self._run_monitoring, 
                    daemon=True
                )
                self.monitor_thread.start()
                self.logger.info("网络监控已自动启动")
                self.db_manager.log_event('MONITOR', '监控自动启动', severity='INFO')
            except Exception as e:
                self.logger.warning(f"自动启动监控失败: {e}")
                self.monitoring = False
            
            # 启动数据同步线程
            sync_thread = threading.Thread(target=self._data_sync_worker, daemon=True)
            sync_thread.start()
            
            # 记录启动事件
            self.db_manager.log_event('SYSTEM', 'Web应用启动', severity='INFO')
            
            self.logger.info(f"启动Web服务器: {self.config['web']['host']}:{self.config['web']['port']}")
            
            # 运行Flask应用
            # 在生产环境(守护进程模式)下允许unsafe_werkzeug
            run_kwargs = {
                'host': self.config['web']['host'],
                'port': self.config['web']['port'],
                'debug': self.config['web']['debug']
            }
            
            # 检查是否在守护进程模式下运行
            import sys
            is_daemon = any('--daemon' in arg for arg in sys.argv)
            if is_daemon or not self.config['web']['debug']:
                run_kwargs['allow_unsafe_werkzeug'] = True
            
            self.socketio.run(self.app, **run_kwargs)
            
        except Exception as e:
            self.logger.error(f"Web应用运行失败: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        if self.monitoring:
            self.monitoring = False
            self.network_monitor.stop()
        
        self.db_manager.close()
        self.geo_locator.close()
        
        self.logger.info("Web应用已关闭")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='NetFlow监控Web应用')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--interface', '-i', help='网络接口')
    parser.add_argument('--port', '-p', type=int, help='Web服务端口')
    
    args = parser.parse_args()
    
    # 创建Web应用
    app = NetFlowWebApp(config_path=args.config)
    
    # 覆盖配置参数
    if args.interface:
        app.config['network']['interface'] = args.interface
    if args.port:
        app.config['web']['port'] = args.port
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n正在关闭应用...")
        app.cleanup()