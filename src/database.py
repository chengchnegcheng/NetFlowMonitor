#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
"""

import sqlite3
import logging
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    src_ip TEXT NOT NULL,
                    dst_ip TEXT NOT NULL,
                    src_port INTEGER NOT NULL,
                    dst_port INTEGER NOT NULL,
                    protocol TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    last_seen REAL NOT NULL,
                    packets_sent INTEGER DEFAULT 0,
                    packets_received INTEGER DEFAULT 0,
                    bytes_sent INTEGER DEFAULT 0,
                    bytes_received INTEGER DEFAULT 0,
                    state TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建IP统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_statistics (
                    ip TEXT PRIMARY KEY,
                    bytes_sent INTEGER DEFAULT 0,
                    bytes_received INTEGER DEFAULT 0,
                    packets_sent INTEGER DEFAULT 0,
                    packets_received INTEGER DEFAULT 0,
                    session_count INTEGER DEFAULT 0,
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    location_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建流量历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    bytes_per_sec INTEGER DEFAULT 0,
                    packets_per_sec INTEGER DEFAULT 0,
                    active_sessions INTEGER DEFAULT 0,
                    active_ips INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建事件日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS event_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    details TEXT,
                    severity TEXT DEFAULT 'INFO',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configurations (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_time ON sessions(start_time, end_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_ip ON sessions(src_ip, dst_ip)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_stats_bytes ON ip_statistics(bytes_sent + bytes_received DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_traffic_history_time ON traffic_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_logs_time ON event_logs(timestamp)')
            
            conn.commit()
        
        self.logger.info(f"数据库初始化完成: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    def insert_session(self, session_data: Dict) -> bool:
        """插入会话数据"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO sessions (
                            session_id, src_ip, dst_ip, src_port, dst_port, protocol,
                            start_time, last_seen, packets_sent, packets_received,
                            bytes_sent, bytes_received, state
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        session_data['session_id'],
                        session_data['src_ip'],
                        session_data['dst_ip'],
                        session_data['src_port'],
                        session_data['dst_port'],
                        session_data['protocol'],
                        session_data['start_time'],
                        session_data['last_seen'],
                        session_data['packets_sent'],
                        session_data['packets_received'],
                        session_data['bytes_sent'],
                        session_data['bytes_received'],
                        session_data['state']
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            self.logger.error(f"插入会话数据失败: {e}")
            return False
    
    def update_session(self, session_id: str, session_data: Dict) -> bool:
        """更新会话数据"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        UPDATE sessions SET
                            last_seen = ?, packets_sent = ?, packets_received = ?,
                            bytes_sent = ?, bytes_received = ?, state = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE session_id = ?
                    ''', (
                        session_data['last_seen'],
                        session_data['packets_sent'],
                        session_data['packets_received'],
                        session_data['bytes_sent'],
                        session_data['bytes_received'],
                        session_data['state'],
                        session_id
                    ))
                    
                    conn.commit()
                    return cursor.rowcount > 0
                    
        except Exception as e:
            self.logger.error(f"更新会话数据失败: {e}")
            return False
    
    def insert_ip_statistics(self, ip_data: Dict) -> bool:
        """插入或更新IP统计数据"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # 序列化位置信息
                    location_json = json.dumps(ip_data.get('location_info', {}))
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO ip_statistics (
                            ip, bytes_sent, bytes_received, packets_sent, packets_received,
                            session_count, first_seen, last_seen, location_info
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ip_data['ip'],
                        ip_data['bytes_sent'],
                        ip_data['bytes_received'],
                        ip_data['packets_sent'],
                        ip_data['packets_received'],
                        ip_data['session_count'],
                        ip_data['first_seen'],
                        ip_data['last_seen'],
                        location_json
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            self.logger.error(f"插入IP统计数据失败: {e}")
            return False
    
    def insert_traffic_history(self, traffic_data: Dict) -> bool:
        """插入流量历史数据"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO traffic_history (
                            timestamp, bytes_per_sec, packets_per_sec,
                            active_sessions, active_ips
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        traffic_data['timestamp'],
                        traffic_data['bytes_per_sec'],
                        traffic_data['packets_per_sec'],
                        traffic_data['active_sessions'],
                        traffic_data['active_ips']
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            self.logger.error(f"插入流量历史数据失败: {e}")
            return False
    
    def log_event(self, event_type: str, description: str, details: str = None, severity: str = 'INFO') -> bool:
        """记录事件日志"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO event_logs (
                            timestamp, event_type, description, details, severity
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        datetime.now().timestamp(),
                        event_type,
                        description,
                        details,
                        severity
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            self.logger.error(f"记录事件日志失败: {e}")
            return False
    
    def get_sessions(self, limit: int = 100, offset: int = 0, 
                    filter_params: Dict = None, order_by: str = 'last_seen', 
                    order_direction: str = 'desc') -> List[Dict]:
        """获取会话列表"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                where_conditions = []
                params = []
                
                if filter_params:
                    if 'src_ip' in filter_params:
                        where_conditions.append('src_ip = ?')
                        params.append(filter_params['src_ip'])
                    
                    if 'dst_ip' in filter_params:
                        where_conditions.append('dst_ip = ?')
                        params.append(filter_params['dst_ip'])
                    
                    if 'protocol' in filter_params:
                        where_conditions.append('protocol = ?')
                        params.append(filter_params['protocol'])
                    
                    if 'state' in filter_params:
                        where_conditions.append('state = ?')
                        params.append(filter_params['state'])
                    
                    if 'start_time_from' in filter_params:
                        where_conditions.append('start_time >= ?')
                        params.append(filter_params['start_time_from'])
                    
                    if 'start_time_to' in filter_params:
                        where_conditions.append('start_time <= ?')
                        params.append(filter_params['start_time_to'])
                
                where_clause = ' WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
                
                # 验证排序字段
                valid_order_fields = ['src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol', 
                                    'start_time', 'last_seen', 'bytes_sent', 'bytes_received', 
                                    'packets_sent', 'packets_received', 'state', 'total_bytes', 
                                    'total_packets', 'duration']
                
                if order_by not in valid_order_fields:
                    order_by = 'last_seen'
                
                # 验证排序方向
                if order_direction.lower() not in ['asc', 'desc']:
                    order_direction = 'desc'
                
                # 构建排序子句
                if order_by == 'total_bytes':
                    order_clause = f'ORDER BY (bytes_sent + bytes_received) {order_direction.upper()}'
                elif order_by == 'total_packets':
                    order_clause = f'ORDER BY (packets_sent + packets_received) {order_direction.upper()}'
                elif order_by == 'duration':
                    order_clause = f'ORDER BY (last_seen - start_time) {order_direction.upper()}'
                else:
                    order_clause = f'ORDER BY {order_by} {order_direction.upper()}'
                
                query = f'''
                    SELECT * FROM sessions
                    {where_clause}
                    {order_clause}
                    LIMIT ? OFFSET ?
                '''
                
                params.extend([limit, offset])
                cursor.execute(query, params)
                
                sessions = []
                for row in cursor.fetchall():
                    session = dict(row)
                    # 添加计算字段
                    session['total_bytes'] = session['bytes_sent'] + session['bytes_received']
                    session['total_packets'] = session['packets_sent'] + session['packets_received']
                    session['duration'] = session['last_seen'] - session['start_time']
                    sessions.append(session)
                
                return sessions
                
        except Exception as e:
            self.logger.error(f"获取会话列表失败: {e}")
            return []
    
    def get_ip_statistics(self, limit: int = 100, offset: int = 0,
                         order_by: str = 'total_bytes', order_direction: str = 'desc') -> List[Dict]:
        """获取IP统计列表"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 验证排序字段
                valid_order_fields = ['ip', 'bytes_sent', 'bytes_received', 'total_bytes', 
                                    'packets_sent', 'packets_received', 'total_packets',
                                    'session_count', 'first_seen', 'last_seen']
                
                if order_by not in valid_order_fields:
                    order_by = 'total_bytes'
                
                # 验证排序方向
                if order_direction.lower() not in ['asc', 'desc']:
                    order_direction = 'desc'
                
                # 构建查询
                if order_by == 'total_bytes':
                    order_clause = f'ORDER BY (bytes_sent + bytes_received) {order_direction.upper()}'
                elif order_by == 'total_packets':
                    order_clause = f'ORDER BY (packets_sent + packets_received) {order_direction.upper()}'
                else:
                    order_clause = f'ORDER BY {order_by} {order_direction.upper()}'
                
                query = f'''
                    SELECT *, (bytes_sent + bytes_received) as total_bytes,
                           (packets_sent + packets_received) as total_packets
                    FROM ip_statistics
                    {order_clause}
                    LIMIT ? OFFSET ?
                '''
                
                cursor.execute(query, [limit, offset])
                
                ip_stats = []
                for row in cursor.fetchall():
                    stat = dict(row)
                    # 解析位置信息
                    if stat['location_info']:
                        try:
                            stat['location_info'] = json.loads(stat['location_info'])
                        except:
                            stat['location_info'] = {}
                    ip_stats.append(stat)
                
                return ip_stats
                
        except Exception as e:
            self.logger.error(f"获取IP统计列表失败: {e}")
            return []
    
    def get_traffic_history(self, hours: int = 24) -> List[Dict]:
        """获取流量历史数据"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 计算时间范围
                end_time = datetime.now().timestamp()
                start_time = end_time - (hours * 3600)
                
                cursor.execute('''
                    SELECT * FROM traffic_history
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp ASC
                ''', [start_time, end_time])
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"获取流量历史数据失败: {e}")
            return []
    
    def get_event_logs(self, limit: int = 100, severity: str = None) -> List[Dict]:
        """获取事件日志"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if severity:
                    cursor.execute('''
                        SELECT * FROM event_logs
                        WHERE severity = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', [severity, limit])
                else:
                    cursor.execute('''
                        SELECT * FROM event_logs
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', [limit])
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"获取事件日志失败: {e}")
            return []
    
    def get_statistics_summary(self) -> Dict:
        """获取统计摘要"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 基本统计
                cursor.execute('SELECT COUNT(*) as total_sessions FROM sessions')
                total_sessions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) as active_sessions FROM sessions WHERE state = "ACTIVE"')
                active_sessions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) as total_ips FROM ip_statistics')
                total_ips = cursor.fetchone()[0]
                
                # 流量统计
                cursor.execute('''
                    SELECT SUM(bytes_sent + bytes_received) as total_bytes,
                           SUM(packets_sent + packets_received) as total_packets
                    FROM ip_statistics
                ''')
                traffic_stats = cursor.fetchone()
                
                # 最近24小时流量
                end_time = datetime.now().timestamp()
                start_time = end_time - 86400  # 24小时
                
                cursor.execute('''
                    SELECT SUM(bytes_per_sec) as bytes_24h,
                           SUM(packets_per_sec) as packets_24h
                    FROM traffic_history
                    WHERE timestamp >= ?
                ''', [start_time])
                recent_traffic = cursor.fetchone()
                
                return {
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'total_ips': total_ips,
                    'total_bytes': traffic_stats[0] or 0,
                    'total_packets': traffic_stats[1] or 0,
                    'bytes_24h': recent_traffic[0] or 0,
                    'packets_24h': recent_traffic[1] or 0
                }
                
        except Exception as e:
            self.logger.error(f"获取统计摘要失败: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """清理旧数据"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # 计算清理时间点
                    cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
                    
                    # 清理旧会话
                    cursor.execute('DELETE FROM sessions WHERE start_time < ?', [cutoff_time])
                    deleted_sessions = cursor.rowcount
                    
                    # 清理旧流量历史
                    cursor.execute('DELETE FROM traffic_history WHERE timestamp < ?', [cutoff_time])
                    deleted_traffic = cursor.rowcount
                    
                    # 清理旧事件日志
                    cursor.execute('DELETE FROM event_logs WHERE timestamp < ?', [cutoff_time])
                    deleted_events = cursor.rowcount
                    
                    conn.commit()
                    
                    self.logger.info(f"清理完成: 会话 {deleted_sessions}, 流量历史 {deleted_traffic}, 事件日志 {deleted_events}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """压缩数据库"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    conn.execute('VACUUM')
                    self.logger.info("数据库压缩完成")
                    return True
                    
        except Exception as e:
            self.logger.error(f"数据库压缩失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        # SQLite连接在上下文管理器中自动关闭
        self.logger.info("数据库管理器已关闭")


if __name__ == "__main__":
    # 测试代码
    import os
    import tempfile
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 创建临时数据库文件
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db_path = f.name
    
    try:
        # 创建数据库管理器
        db_manager = DatabaseManager(test_db_path)
        
        # 测试插入会话数据
        session_data = {
            'session_id': 'test-session-1',
            'src_ip': '192.168.1.100',
            'dst_ip': '8.8.8.8',
            'src_port': 12345,
            'dst_port': 53,
            'protocol': 'UDP',
            'start_time': datetime.now().timestamp(),
            'last_seen': datetime.now().timestamp(),
            'packets_sent': 10,
            'packets_received': 5,
            'bytes_sent': 1024,
            'bytes_received': 512,
            'state': 'ACTIVE'
        }
        
        print("测试插入会话数据...")
        result = db_manager.insert_session(session_data)
        print(f"插入结果: {result}")
        
        # 测试查询会话
        print("\n测试查询会话...")
        sessions = db_manager.get_sessions(limit=10)
        for session in sessions:
            print(f"会话: {session['session_id']} - {session['src_ip']}:{session['src_port']} -> {session['dst_ip']}:{session['dst_port']}")
        
        # 测试统计摘要
        print("\n测试统计摘要...")
        summary = db_manager.get_statistics_summary()
        print(f"统计摘要: {summary}")
        
        # 测试事件日志
        print("\n测试事件日志...")
        db_manager.log_event('TEST', '测试事件', '这是一个测试事件')
        events = db_manager.get_event_logs(limit=5)
        for event in events:
            print(f"事件: {event['event_type']} - {event['description']}")
        
        db_manager.close()
        print("\n测试完成")
        
    finally:
        # 清理测试文件
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)