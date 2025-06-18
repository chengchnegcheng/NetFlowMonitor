# NetFlow 网络流量监控工具

一个基于Python开发的Linux网络流量监控和统计系统，提供实时的网络流量分析、IP会话跟踪、地理位置显示和现代化Web界面。

## ✨ 主要功能

- 🌐 **实时网络监控** - 基于Scapy的高性能数据包捕获和分析
- 📊 **IP会话跟踪** - 自动识别和跟踪TCP/UDP会话连接
- 📈 **流量统计分析** - 详细的IP级别流量统计和TOP排行
- 🗺️ **地理位置显示** - IP地址的地理位置查询和世界地图展示
- 💻 **现代化Web界面** - 响应式设计，支持实时数据更新
- ⚡ **实时数据推送** - 基于WebSocket的实时数据推送
- 💾 **数据持久化** - SQLite数据库存储历史数据和统计信息
- 🛠️ **系统服务支持** - 支持systemd服务管理和后台运行

## 🚀 快速开始

### 系统要求

- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- **Python版本**: 3.7+
- **权限要求**: root权限或CAP_NET_RAW capability
- **内存要求**: 最少512MB，推荐1GB+

### 一键安装

```bash
# 下载项目
git clone https://github.com/your-repo/NetFlowMonitor.git
cd NetFlowMonitor

# 运行安装脚本
sudo chmod +x install.sh
sudo ./install.sh
```

### 手动安装

#### 1. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv python3-dev \
                     tcpdump net-tools libpcap-dev build-essential
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip python3-devel gcc gcc-c++ \
                 tcpdump net-tools libpcap-devel
```

#### 2. 安装Python依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
```

#### 3. 配置文件

```bash
# 创建必要目录
mkdir -p data logs

# 根据需要修改配置文件
vim config/config.yaml
```

### 启动应用

#### 直接启动
```bash
# 基本启动
sudo python3 main.py

# 指定网络接口和端口
sudo python3 main.py -i eth0 -p 8080

# 查看所有选项
python3 main.py --help
```

#### 系统服务方式
```bash
# 启用并启动服务
sudo systemctl enable netflow-monitor
sudo systemctl start netflow-monitor

# 查看服务状态
sudo systemctl status netflow-monitor
```

### 访问Web界面

打开浏览器访问: http://localhost:8080

## 📱 界面截图

### 主控制台
![主控制台](docs/images/dashboard.png)

### 会话监控
![会话监控](docs/images/sessions.png)

### 地理位置地图
![地理位置](docs/images/geomap.png)

## 🛠️ 使用指南

### Web界面操作

1. **启动监控**: 在Web界面点击"开始监控"按钮
2. **查看实时数据**: 
   - 顶部面板显示实时统计信息
   - 流量图表显示历史趋势
   - TOP流量IP列表显示排行
3. **详细分析**:
   - **会话列表**: 查看所有网络连接详情
   - **IP统计**: 查看IP级别流量统计
   - **地理位置**: 在世界地图上查看IP分布
   - **事件日志**: 查看系统事件和操作记录

### 命令行选项

```bash
python3 main.py [选项]

选项:
  -c, --config CONFIG      配置文件路径
  -i, --interface IFACE    网络接口名称 (如: eth0, wlan0)
  -p, --port PORT         Web服务端口 (默认: 8080)  
  --host HOST             监听地址 (默认: 0.0.0.0)
  --debug                 启用调试模式
  --check-deps            检查系统依赖
  --list-interfaces       列出可用网络接口
```

### API接口

系统提供完整的RESTful API接口：

```bash
# 获取监控状态
curl http://localhost:8080/api/status

# 获取会话列表  
curl http://localhost:8080/api/sessions

# 获取IP统计
curl http://localhost:8080/api/ip-stats

# 启动监控
curl -X POST http://localhost:8080/api/start-monitoring

# 停止监控
curl -X POST http://localhost:8080/api/stop-monitoring
```

## ⚙️ 配置说明

主要配置文件: `config/config.yaml`

```yaml
# 网络接口配置
network:
  interface: "eth0"        # 监控的网络接口
  promiscuous_mode: true   # 是否开启混杂模式

# Web服务配置  
web:
  host: "0.0.0.0"         # 监听地址
  port: 8080              # 监听端口
  debug: false            # 调试模式

# 监控配置
monitor:
  session_timeout: 300    # 会话超时时间(秒)
  max_sessions: 10000     # 最大会话数

# IP归属地配置
geolocation:
  enabled: true           # 是否启用地理位置功能
  database_path: "data/GeoLite2-City.mmdb"
```

## 🔧 开发指南

### 项目结构

```
NetFlowMonitor/
├── main.py                 # 主程序入口
├── requirements.txt        # Python依赖
├── install.sh             # 安装脚本
├── config/                # 配置目录
├── src/                   # 核心源码
│   ├── network_monitor.py # 网络监控模块
│   ├── geo_locator.py     # IP归属地模块
│   └── database.py        # 数据库管理
├── web/                   # Web应用
│   ├── app.py            # Flask应用
│   └── templates/        # HTML模板
├── data/                 # 数据目录
├── logs/                 # 日志目录
└── docs/                 # 文档目录
```

### 核心模块

- **NetworkMonitor**: 网络数据包捕获和会话跟踪
- **GeoLocator**: IP地理位置查询和缓存管理  
- **DatabaseManager**: SQLite数据库操作和数据持久化
- **NetFlowWebApp**: Flask Web应用和API服务

### 扩展开发

查看完整的 [开发文档](docs/开发文档.md) 了解:

- 系统架构设计
- 核心模块API
- 扩展开发指南
- 性能优化方案
- 部署最佳实践

## 🐛 故障排除

### 常见问题

**1. 权限不足**
```bash
# 解决方案1: 使用sudo运行
sudo python3 main.py

# 解决方案2: 设置capabilities
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3
```

**2. 端口被占用**
```bash
# 查看端口占用
netstat -tulpn | grep 8080

# 更换端口
python3 main.py -p 8081
```

**3. 网络接口不存在**
```bash
# 列出可用接口
python3 main.py --list-interfaces

# 或使用ip命令
ip addr show
```

### 检查系统依赖

```bash
# 运行依赖检查
python3 main.py --check-deps
```

### 查看日志

```bash
# 应用日志
tail -f logs/netflow.log

# 系统服务日志  
journalctl -u netflow-monitor -f
```

## 📊 性能优化

### 系统调优

1. **网络缓冲区调优**:
```bash
# 增加网络缓冲区大小
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.rmem_default = 67108864' >> /etc/sysctl.conf
sysctl -p
```

2. **文件句柄限制**:
```bash
# 增加文件句柄限制
echo '* soft nofile 65536' >> /etc/security/limits.conf
echo '* hard nofile 65536' >> /etc/security/limits.conf
```

3. **数据库优化**:
```bash
# 定期清理旧数据
sqlite3 data/netflow.db "DELETE FROM sessions WHERE start_time < strftime('%s', 'now', '-7 days');"

# 数据库压缩
sqlite3 data/netflow.db "VACUUM;"
```

## 🔒 安全建议

1. **访问控制**: 使用防火墙限制Web界面访问
2. **HTTPS加密**: 在生产环境使用反向代理配置HTTPS
3. **认证授权**: 添加用户认证和权限控制
4. **数据保护**: 定期备份重要数据
5. **系统更新**: 保持系统和依赖库的最新版本

## 📋 系统要求详情

### 最低配置
- CPU: 1核心
- 内存: 512MB
- 磁盘: 100MB可用空间
- 网络: 1Mbps带宽

### 推荐配置  
- CPU: 2核心+
- 内存: 1GB+
- 磁盘: 1GB+可用空间
- 网络: 10Mbps+带宽

### 支持的操作系统
- Ubuntu 18.04/20.04/22.04
- Debian 9/10/11
- CentOS 7/8
- RHEL 7/8/9
- Rocky Linux 8/9

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解:

- 代码风格规范
- 提交流程
- 问题报告模板
- 功能请求格式

## 📝 许可证

本项目基于 [MIT License](LICENSE) 开源许可证发布。

## 🙏 致谢

感谢以下开源项目的支持:

- [Scapy](https://scapy.net/) - 网络数据包处理
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Chart.js](https://www.chartjs.org/) - 图表库
- [Leaflet](https://leafletjs.com/) - 地图库
- [Bootstrap](https://getbootstrap.com/) - UI框架

## 📞 联系方式

- 📧 邮箱: [your-email@example.com]
- 🐛 问题反馈: [GitHub Issues](https://github.com/your-repo/NetFlowMonitor/issues)
- 📖 文档: [在线文档](https://your-docs-site.com)
- 💬 讨论: [GitHub Discussions](https://github.com/your-repo/NetFlowMonitor/discussions)

## ⭐ Star History

如果这个项目对您有帮助，请给我们一个 ⭐！

[![Star History Chart](https://api.star-history.com/svg?repos=your-repo/NetFlowMonitor&type=Date)](https://star-history.com/#your-repo/NetFlowMonitor&Date)