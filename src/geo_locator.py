#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP归属地查询模块
"""

import os
import json
import logging
import threading
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import ipaddress

try:
    import geoip2.database
    import geoip2.errors
    GEOIP2_AVAILABLE = True
except ImportError:
    GEOIP2_AVAILABLE = False

import requests


@dataclass
class LocationInfo:
    """位置信息"""
    ip: str
    country: str = "未知"
    country_code: str = "UN"
    region: str = "未知"
    city: str = "未知"
    latitude: float = 0.0
    longitude: float = 0.0
    isp: str = "未知"
    organization: str = "未知"
    timezone: str = "未知"


class GeoLocator:
    """IP地理位置查询器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.reader = None
        self.cache: Dict[str, LocationInfo] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # 在线API配置（备用）
        self.online_apis = [
            {
                'name': 'ip-api.com',
                'url': 'http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org',
                'rate_limit': 45  # 每分钟45次请求
            }
        ]
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化GeoIP数据库"""
        if not GEOIP2_AVAILABLE:
            self.logger.warning("geoip2库未安装，将只使用在线API查询")
            return
            
        if self.db_path and os.path.exists(self.db_path):
            try:
                self.reader = geoip2.database.Reader(self.db_path)
                self.logger.info(f"成功加载GeoIP数据库: {self.db_path}")
            except Exception as e:
                self.logger.error(f"加载GeoIP数据库失败: {e}")
        else:
            self.logger.warning("GeoIP数据库文件不存在，将只使用在线API查询")
    
    def _is_private_ip(self, ip: str) -> bool:
        """检查是否为私有IP地址"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        except ValueError:
            return True
    
    def _query_local_database(self, ip: str) -> Optional[LocationInfo]:
        """从本地数据库查询IP信息"""
        if not self.reader:
            return None
            
        try:
            response = self.reader.city(ip)
            
            location = LocationInfo(
                ip=ip,
                country=response.country.name if response.country.name else "未知",
                country_code=response.country.iso_code if response.country.iso_code else "UN",
                region=response.subdivisions.most_specific.name if response.subdivisions.most_specific.name else "未知",
                city=response.city.name if response.city.name else "未知",
                latitude=float(response.location.latitude) if response.location.latitude else 0.0,
                longitude=float(response.location.longitude) if response.location.longitude else 0.0,
                timezone=response.location.time_zone if response.location.time_zone else "未知"
            )
            
            return location
            
        except geoip2.errors.AddressNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"本地数据库查询失败: {e}")
            return None
    
    def _query_online_api(self, ip: str) -> Optional[LocationInfo]:
        """从在线API查询IP信息"""
        for api in self.online_apis:
            try:
                url = api['url'].format(ip=ip)
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if api['name'] == 'ip-api.com':
                        if data.get('status') == 'success':
                            location = LocationInfo(
                                ip=ip,
                                country=data.get('country', '未知'),
                                country_code=data.get('countryCode', 'UN'),
                                region=data.get('regionName', '未知'),
                                city=data.get('city', '未知'),
                                latitude=float(data.get('lat', 0.0)),
                                longitude=float(data.get('lon', 0.0)),
                                isp=data.get('isp', '未知'),
                                organization=data.get('org', '未知'),
                                timezone=data.get('timezone', '未知')
                            )
                            return location
                    
            except Exception as e:
                self.logger.warning(f"在线API查询失败 ({api['name']}): {e}")
                continue
        
        return None
    
    def get_location(self, ip: str) -> LocationInfo:
        """获取IP的地理位置信息"""
        with self.lock:
            # 检查缓存
            if ip in self.cache:
                return self.cache[ip]
            
            # 检查是否为私有IP
            if self._is_private_ip(ip):
                location = LocationInfo(
                    ip=ip,
                    country="本地网络",
                    country_code="LO",
                    region="私有网络",
                    city="内网",
                    isp="本地",
                    organization="私有网络"
                )
                self.cache[ip] = location
                return location
            
            # 先尝试从本地数据库查询
            location = self._query_local_database(ip)
            
            # 如果本地数据库查询失败，尝试在线API
            if not location:
                location = self._query_online_api(ip)
            
            # 如果都查询失败，返回默认信息
            if not location:
                location = LocationInfo(ip=ip)
            
            # 缓存结果
            self.cache[ip] = location
            return location
    
    def get_locations_batch(self, ips: list) -> Dict[str, LocationInfo]:
        """批量获取IP的地理位置信息"""
        results = {}
        
        for ip in ips:
            results[ip] = self.get_location(ip)
        
        return results
    
    def clear_cache(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.logger.info("地理位置缓存已清空")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        with self.lock:
            return {
                'cache_size': len(self.cache),
                'database_available': self.reader is not None,
                'geoip2_available': GEOIP2_AVAILABLE
            }
    
    def export_cache(self, filepath: str):
        """导出缓存到文件"""
        with self.lock:
            try:
                cache_data = {}
                for ip, location in self.cache.items():
                    cache_data[ip] = {
                        'country': location.country,
                        'country_code': location.country_code,
                        'region': location.region,
                        'city': location.city,
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'isp': location.isp,
                        'organization': location.organization,
                        'timezone': location.timezone
                    }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"缓存已导出到: {filepath}")
                
            except Exception as e:
                self.logger.error(f"导出缓存失败: {e}")
    
    def import_cache(self, filepath: str):
        """从文件导入缓存"""
        with self.lock:
            try:
                if not os.path.exists(filepath):
                    self.logger.warning(f"缓存文件不存在: {filepath}")
                    return
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                for ip, data in cache_data.items():
                    location = LocationInfo(
                        ip=ip,
                        country=data.get('country', '未知'),
                        country_code=data.get('country_code', 'UN'),
                        region=data.get('region', '未知'),
                        city=data.get('city', '未知'),
                        latitude=data.get('latitude', 0.0),
                        longitude=data.get('longitude', 0.0),
                        isp=data.get('isp', '未知'),
                        organization=data.get('organization', '未知'),
                        timezone=data.get('timezone', '未知')
                    )
                    self.cache[ip] = location
                
                self.logger.info(f"从文件导入了 {len(cache_data)} 条缓存记录")
                
            except Exception as e:
                self.logger.error(f"导入缓存失败: {e}")
    
    def close(self):
        """关闭数据库连接"""
        if self.reader:
            self.reader.close()
            self.reader = None


def download_geoip_database(output_path: str) -> bool:
    """下载GeoIP数据库（需要MaxMind账户）
    
    注意：MaxMind现在需要注册账户才能下载数据库
    这个函数提供了基本框架，实际使用时需要配置API密钥
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 这里需要配置MaxMind的下载链接和API密钥
        # 由于需要注册账户，这里只提供示例代码
        logger.warning("下载GeoIP数据库需要MaxMind账户，请手动下载并配置")
        
        # 示例：手动下载说明
        instructions = """
        请按以下步骤手动下载GeoIP数据库：
        
        1. 访问 https://www.maxmind.com/en/geolite2/signup
        2. 注册免费账户
        3. 下载 GeoLite2-City.mmdb 文件
        4. 将文件放置到: {output_path}
        
        或者使用以下命令（需要配置API密钥）：
        wget "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=YOUR_LICENSE_KEY&suffix=tar.gz"
        """.format(output_path=output_path)
        
        print(instructions)
        return False
        
    except Exception as e:
        logger.error(f"下载GeoIP数据库失败: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 创建地理位置查询器
    locator = GeoLocator()
    
    # 测试IP列表
    test_ips = [
        "8.8.8.8",          # Google DNS
        "114.114.114.114",  # 中国DNS
        "1.1.1.1",          # Cloudflare DNS
        "192.168.1.1",      # 私有IP
        "127.0.0.1"         # 本地回环
    ]
    
    print("=== IP归属地查询测试 ===")
    for ip in test_ips:
        location = locator.get_location(ip)
        print(f"\nIP: {location.ip}")
        print(f"国家: {location.country} ({location.country_code})")
        print(f"地区: {location.region}")
        print(f"城市: {location.city}")
        print(f"坐标: {location.latitude}, {location.longitude}")
        print(f"ISP: {location.isp}")
        print(f"组织: {location.organization}")
        print(f"时区: {location.timezone}")
    
    # 输出缓存统计
    stats = locator.get_cache_stats()
    print(f"\n=== 缓存统计 ===")
    print(f"缓存大小: {stats['cache_size']}")
    print(f"本地数据库可用: {stats['database_available']}")
    print(f"GeoIP2库可用: {stats['geoip2_available']}")
    
    locator.close()