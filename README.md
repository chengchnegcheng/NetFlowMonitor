# NetFlow 网络流量监控系统

[![GitHub stars](https://img.shields.io/github/stars/chengchnegcheng/NetFlowMonitor.svg)](https://github.com/chengchnegcheng/NetFlowMonitor/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/chengchnegcheng/NetFlowMonitor.svg)](https://github.com/chengchnegcheng/NetFlowMonitor/network)
[![GitHub issues](https://img.shields.io/github/issues/chengchnegcheng/NetFlowMonitor.svg)](https://github.com/chengchnegcheng/NetFlowMonitor/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个基于Python开发的专业Linux网络流量监控和分析系统，提供实时的网络数据包捕获、IP会话跟踪、地理位置可视化和现代化Web管理界面。

## ✨ 核心功能

### 🌐 实时网络监控
- **高性能数据包捕获** - 基于Scapy实现的专业级网络数据包分析
- **智能网络接口检测** - 自动识别和配置最佳网络接口
- **多协议支持** - 支持TCP、UDP、ICMP等多种网络协议

### 📊 智能会话管理
- **实时会话跟踪** - 自动识别和跟踪网络连接会话
- **会话状态监控** - 动态监控连接建立、传输、关闭过程
- **会话统计分析** - 详细的会话时长、流量、状态统计

### 📈 流量分析与统计
- **实时流量统计** - 按IP、端口、协议进行实时流量统计
- **TOP排行榜** - 流量TOP IP、活跃会话排行
- **历史数据分析** - 支持历史流量趋势分析和报表生成

### 🗺️ IP地理位置服务
- **全球IP定位** - 基于GeoIP2的精准地理位置查询
- **世界地图可视化** - 在交互式地图上展示IP分布
- **ISP信息显示** - 显示IP对应的网络服务提供商信息

### 💻 现代化Web界面
- **响应式设计** - 支持桌面和移动设备访问
- **实时数据更新** - 基于WebSocket的实时数据推送
- **交互式图表** - 动态图表展示流量趋势和统计数据
- **暗黑主题支持** - 现代化的用户界面设计

### ⚡ 一键管理系统
- **智能控制脚本** - `control.sh`提供完整的系统生命周期管理
- **自动环境检测** - 自动检测网络接口、防火墙配置
- **进程管理** - 支持启动、停止、重启、状态监控
- **系统服务支持** - 支持systemd服务管理和开机自启动

### 💾 数据持久化
- **SQLite数据库** - 轻量级数据库存储历史数据
- **数据同步机制** - 内存和数据库数据实时同步
- **数据清理策略** - 自动清理过期数据，优化存储空间

## 🚀 快速开始

### 系统要求

- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+, AlmaLinux 8+, Debian 9+)
- **Python版本**: 3.7+
- **权限要求**: root权限（用于网络数据包捕获）
- **内存要求**: 最少512MB，推荐1GB+
- **网络要求**: 需要能够访问网络接口进行数据包捕获

### 一键安装部署

```bash
# 1. 克隆项目
git clone https://github.com/chengchnegcheng/NetFlowMonitor.git
cd NetFlowMonitor

# 2. 运行自动安装脚本
sudo chmod +x install.sh
sudo ./install.sh

# 3. 启动系统
sudo ./control.sh start
```

### 使用一键控制脚本

我们提供了功能强大的 `control.sh` 脚本来管理整个系统：

```bash
# 显示帮助信息
./control.sh help

# 启动系统（自动检测环境、配置防火墙）
sudo ./control.sh start

# 停止系统
sudo ./control.sh stop

# 重启系统
sudo ./control.sh restart

# 查看系统状态（进程、端口、日志）
./control.sh status

# 查看实时日志
./control.sh logs
```

**控制脚本特色功能：**
- ✅ 自动检测和修复网络接口配置
- ✅ 智能防火墙端口管理
- ✅ 进程状态监控和清理
- ✅ 优雅的启停控制
- ✅ 详细的状态报告

### 手动安装（高级用户）

#### 1. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv python3-dev \
                     tcpdump net-tools libpcap-dev build-essential
```

**CentOS/RHEL/AlmaLinux:**
```bash
sudo yum install python3 python3-pip python3-devel gcc gcc-c++ \
                 tcpdump net-tools libpcap-devel
```

#### 2. 创建Python虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
```

#### 3. 网络接口配置

```bash
# 查看可用网络接口
python3 fix_interface.py --list

# 自动配置网络接口
python3 fix_interface.py --auto-fix

# 手动指定网络接口
python3 main.py -i ens33
```

### 访问系统

启动成功后，打开浏览器访问: **http://localhost:8080**

默认会显示：
- 实时网络监控仪表板
- 流量统计图表
- IP会话列表
- 地理位置地图
- 系统状态信息

## 📱 界面展示

### 主控制台
- 实时流量监控面板
- 网络统计概览
- TOP流量IP排行
- 系统运行状态

### 会话监控页面
- 详细的网络连接会话列表
- 会话状态、时长、流量统计
- 实时会话更新
- 高级过滤和排序功能

### IP统计分析
- IP级别流量统计
- 地理位置信息
- ISP服务商信息
- 流量趋势分析

### 地理位置地图
- 全球IP分布可视化
- 交互式世界地图
- 流量热力图
- 地理统计信息

## 🛠️ 详细使用指南

### Web界面操作

1. **启动监控**:
   - 访问Web界面后，系统会自动开始监控
   - 或点击"开始监控"按钮手动启动

2. **实时数据查看**:
   - **仪表板**: 查看实时统计概览
   - **会话列表**: 查看详细的网络连接
   - **IP统计**: 查看IP级别流量排行
   - **地理位置**: 在地图上查看IP分布
   - **事件日志**: 查看系统操作记录

3. **高级功能**:
   - **数据过滤**: 按IP、协议、状态过滤数据
   - **排序功能**: 多维度数据排序
   - **实时更新**: WebSocket实时数据推送
   - **数据导出**: 支持数据导出功能

### 命令行操作

```bash
# 基本启动
sudo python3 main.py

# 指定网络接口
sudo python3 main.py -i eth0

# 指定Web端口
sudo python3 main.py -p 8080

# 守护进程模式
sudo python3 main.py --daemon

# 检查系统依赖
python3 main.py --check-deps

# 列出网络接口
python3 main.py --list-interfaces

# 查看帮助
python3 main.py --help
```

### API接口使用

系统提供完整的RESTful API：

```bash
# 获取监控状态
curl http://localhost:8080/api/status

# 获取会话列表（支持分页和过滤）
curl "http://localhost:8080/api/sessions?page=1&per_page=50"

# 获取IP统计
curl "http://localhost:8080/api/ip-stats?order_by=total_bytes"

# 获取流量历史
curl "http://localhost:8080/api/traffic-history?hours=24"

# 获取地理位置数据
curl http://localhost:8080/api/geo-map

# 控制监控（需要POST请求）
curl -X POST http://localhost:8080/api/start-monitoring
curl -X POST http://localhost:8080/api/stop-monitoring
```

## ⚙️ 配置说明

### 主配置文件

编辑 `config/config.yaml`:

```yaml
# 网络监控配置
network:
  interface: "ens33"           # 监控的网络接口
  promiscuous_mode: true       # 混杂模式
  buffer_size: 65536          # 缓冲区大小

# Web服务配置
web:
  host: "0.0.0.0"            # 监听地址
  port: 8080                 # 监听端口
  debug: false               # 调试模式

# 数据库配置
database:
  path: "data/netflow.db"    # 数据库文件路径
  cleanup_days: 7            # 数据保留天数

# 地理位置配置
geolocation:
  enabled: true              # 启用地理位置功能
  database_path: "data/GeoLite2-City.mmdb"
  api_key: ""               # API密钥（可选）
  cache_size: 1000          # 缓存大小

# 监控参数
monitoring:
  session_timeout: 300       # 会话超时时间（秒）
  max_sessions: 10000       # 最大会话数
  update_interval: 5        # 更新间隔（秒）
```

### 网络接口管理

使用 `fix_interface.py` 工具管理网络接口：

```bash
# 列出所有可用接口
python3 fix_interface.py --list

# 检查指定接口
python3 fix_interface.py --check eth0

# 自动修复接口配置
python3 fix_interface.py --auto-fix
```

## 🔧 项目结构说明

```
NetFlowMonitor/
├── control.sh              # 一键控制脚本
├── main.py                 # 主程序入口
├── fix_interface.py        # 网络接口管理工具
├── install.sh              # 自动安装脚本
├── demo.sh                 # 快速演示脚本
├── requirements.txt        # Python依赖列表
├── .gitignore             # Git忽略规则
├── config/                # 配置文件目录
│   └── config.yaml        # 主配置文件
├── src/                   # 核心源代码
│   ├── network_monitor.py # 网络监控核心模块
│   ├── geo_locator.py     # IP地理位置模块
│   └── database.py        # 数据库管理模块
├── web/                   # Web应用
│   ├── app.py            # Flask Web应用
│   ├── templates/        # HTML模板
│   │   └── index.html    # 主页面模板
│   └── static/           # 静态资源（CSS、JS）
├── data/                 # 数据目录
├── logs/                 # 日志目录
└── docs/                 # 项目文档
    ├── 开发文档.md        # 详细开发文档
    ├── 项目总结.md        # 项目总结报告
    ├── UI界面优化说明.md   # 界面设计说明
    ├── 界面效果演示.md     # 功能演示文档
    └── 排序功能说明.md     # 功能特性说明
```

### 核心模块介绍

- **NetworkMonitor** (`src/network_monitor.py`)
  - 网络数据包捕获和解析
  - TCP/UDP会话跟踪和管理
  - 实时流量统计和分析

- **GeoLocator** (`src/geo_locator.py`)
  - IP地理位置查询服务
  - 支持离线GeoIP2数据库
  - 在线API查询备用方案
  - 智能缓存管理

- **DatabaseManager** (`src/database.py`)
  - SQLite数据库操作
  - 数据结构管理
  - 历史数据查询和统计
  - 数据清理和优化

- **NetFlowWebApp** (`web/app.py`)
  - Flask Web应用框架
  - RESTful API接口
  - WebSocket实时通信
  - 模板渲染和静态文件服务

## 🐛 故障排除

### 常见问题及解决方案

**1. 权限不足错误**
```bash
# 问题：Permission denied
# 解决：使用sudo运行
sudo ./control.sh start

# 或者设置capabilities
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
```

**2. 网络接口错误**
```bash
# 问题：Interface 'eth0' not found
# 解决：自动检测和修复
python3 fix_interface.py --auto-fix

# 或手动指定接口
python3 main.py -i ens33
```

**3. 端口被占用**
```bash
# 检查端口占用
netstat -tlnp | grep 8080

# 更换端口
python3 main.py -p 8081
```

**4. 依赖包问题**
```bash
# 检查依赖
python3 main.py --check-deps

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

**5. 防火墙阻止访问**
```bash
# 手动开放端口（CentOS/RHEL）
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# Ubuntu/Debian
sudo ufw allow 8080/tcp
```

### 系统诊断

```bash
# 检查系统状态
./control.sh status

# 查看详细日志
./control.sh logs

# 检查进程
ps aux | grep python3

# 检查网络
netstat -tlnp | grep 8080
```

## 📊 性能优化建议

### 系统层面优化

1. **网络缓冲区调优**:
```bash
# 增加接收缓冲区
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.rmem_default = 67108864' >> /etc/sysctl.conf
sysctl -p
```

2. **文件描述符限制**:
```bash
# 增加文件句柄数
echo '* soft nofile 65536' >> /etc/security/limits.conf
echo '* hard nofile 65536' >> /etc/security/limits.conf
```

3. **进程优先级**:
```bash
# 提高进程优先级
sudo nice -n -10 python3 main.py
```

### 应用层面优化

1. **数据库优化**:
```bash
# 定期清理旧数据
sqlite3 data/netflow.db "DELETE FROM sessions WHERE last_seen < strftime('%s', 'now', '-7 days');"

# 数据库真空
sqlite3 data/netflow.db "VACUUM;"
```

2. **内存管理**:
```yaml
# 在config.yaml中调整
monitoring:
  max_sessions: 5000      # 减少最大会话数
  session_timeout: 180    # 降低超时时间
```

3. **缓存优化**:
```yaml
geolocation:
  cache_size: 2000       # 增加地理位置缓存
```

## 🔒 安全建议

### 网络安全
1. **访问控制**: 使用防火墙限制Web界面访问范围
2. **HTTPS部署**: 生产环境建议使用Nginx反向代理配置HTTPS
3. **认证机制**: 考虑添加用户认证和权限控制
4. **IP白名单**: 限制特定IP访问管理界面

### 数据安全
1. **数据备份**: 定期备份重要数据和配置文件
2. **日志管理**: 定期清理和归档日志文件
3. **敏感信息**: 避免在日志中记录敏感信息
4. **权限控制**: 合理设置文件和目录权限

### 系统安全
1. **系统更新**: 保持操作系统和Python依赖的最新版本
2. **最小权限**: 仅授予必要的系统权限
3. **监控审计**: 启用系统级别的安全审计和监控
4. **入侵检测**: 部署入侵检测系统监控异常行为

## 📋 部署建议

### 生产环境部署

**推荐配置：**
- CPU: 4核心以上
- 内存: 4GB以上
- 磁盘: 100GB以上SSD
- 网络: 千兆网卡

**部署步骤：**
```bash
# 1. 创建专用用户
sudo useradd -r -s /bin/false netflow

# 2. 安装到系统目录
sudo mkdir -p /opt/netflow
sudo cp -r NetFlowMonitor/* /opt/netflow/
sudo chown -R netflow:netflow /opt/netflow

# 3. 创建systemd服务
sudo cp scripts/netflow-monitor.service /etc/systemd/system/
sudo systemctl enable netflow-monitor
sudo systemctl start netflow-monitor

# 4. 配置日志轮转
sudo cp scripts/netflow-logrotate /etc/logrotate.d/netflow
```

### 监控和维护

1. **服务监控**:
```bash
# 检查服务状态
sudo systemctl status netflow-monitor

# 查看服务日志
sudo journalctl -u netflow-monitor -f
```

2. **资源监控**:
```bash
# 监控CPU和内存使用
top -p $(pgrep -f netflow)

# 监控网络统计
ss -tuln | grep 8080
```

3. **数据维护**:
```bash
# 定期备份数据库
cp data/netflow.db backup/netflow_$(date +%Y%m%d).db

# 清理日志文件
find logs/ -name "*.log" -mtime +30 -delete
```

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

### 开发环境设置
```bash
# 1. Fork项目到您的GitHub账户
# 2. 克隆您的fork
git clone https://github.com/yourusername/NetFlowMonitor.git
cd NetFlowMonitor

# 3. 创建开发分支
git checkout -b feature/your-feature-name

# 4. 设置开发环境
python3 -m venv venv-dev
source venv-dev/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 代码规范
- 遵循PEP 8 Python代码风格
- 添加必要的注释和文档字符串
- 编写单元测试覆盖新功能
- 确保代码通过所有测试

### 提交流程
```bash
# 1. 运行测试
python -m pytest tests/

# 2. 检查代码风格
flake8 src/ web/ main.py

# 3. 提交更改
git add .
git commit -m "feat: 添加新功能描述"

# 4. 推送到您的fork
git push origin feature/your-feature-name

# 5. 创建Pull Request
```

## 📝 更新日志

### v1.0.0 (2025-06-18)
- ✨ 首次发布完整的NetFlow监控系统
- 🚀 实现一键控制脚本（control.sh）
- 📊 完整的Web界面和实时数据展示
- 🗺️ IP地理位置查询和地图可视化
- 💾 SQLite数据库数据持久化
- 🛠️ 自动安装和配置工具
- 📚 完整的中文文档和使用指南

### 后续计划
- [ ] 添加更多网络协议支持
- [ ] 实现数据导出功能
- [ ] 添加告警和通知机制
- [ ] 支持分布式部署
- [ ] 实现用户认证和权限控制
- [ ] 添加更多图表和报表功能

## 📞 支持与联系

### 获取帮助
- 🐛 **问题反馈**: [GitHub Issues](https://github.com/chengchnegcheng/NetFlowMonitor/issues)
- 💬 **功能讨论**: [GitHub Discussions](https://github.com/chengchnegcheng/NetFlowMonitor/discussions)
- 📖 **详细文档**: 查看 [docs/](docs/) 目录下的文档文件
- ⭐ **项目支持**: 如果项目对您有帮助，请给我们一个Star！

### 社区资源
- 📚 在线文档：项目wiki页面
- 💻 示例代码：examples目录
- 🎥 视频教程：即将发布
- 📊 性能基准：benchmark目录

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

```
MIT License

Copyright (c) 2025 NetFlow Monitor Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙏 致谢

特别感谢以下优秀的开源项目，没有它们就没有NetFlow监控系统：

- **[Scapy](https://scapy.net/)** - 强大的网络数据包处理库
- **[Flask](https://flask.palletsprojects.com/)** - 轻量级Web应用框架
- **[SQLite](https://www.sqlite.org/)** - 嵌入式SQL数据库引擎
- **[Chart.js](https://www.chartjs.org/)** - 现代化图表可视化库
- **[Leaflet](https://leafletjs.com/)** - 开源交互式地图库
- **[Bootstrap](https://getbootstrap.com/)** - 响应式前端UI框架
- **[MaxMind GeoIP2](https://dev.maxmind.com/geoip/geoip2/)** - IP地理位置数据库

同时感谢所有为项目贡献代码、文档、建议和反馈的开发者和用户！

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐ Star！**

[🏠 项目主页](https://github.com/chengchnegcheng/NetFlowMonitor) • 
[📖 使用文档](docs/) • 
[🐛 问题反馈](https://github.com/chengchnegcheng/NetFlowMonitor/issues) • 
[💬 讨论区](https://github.com/chengchnegcheng/NetFlowMonitor/discussions)

</div>