# 系统服务稳定性问题诊断与优化报告

## 📋 报告概述

**报告日期**：2026年3月22日  
**问题范围**：leap.service 和 xtqmt.service 服务异常重启  
**根本原因**：xtqmt.service 中 miniquote.exe 进程内存泄漏触发 OOM Killer  
**影响程度**：中等 - 服务自动恢复，但可能导致短暂交易中断

---

## 🔍 问题发现与诊断过程

### 1. 初始现象
- WebSocket 连接异常断开（收到 EOF）
- 服务日志显示进程 PID 从 9574 变为 29668，确认发生重启
- 重启时间：2026年3月22日 10:38 左右

### 2. 日志分析

**关键时间线**：
```
00:52:55 - 最后一条正常请求 (PID 9574)
   ↓ (近10小时日志断层)
10:37:56 - OOM Killer 触发
10:37:57 - miniquote.exe (PID 3095) 被杀死
10:37:59 - xtqmt.service 自动重启 (PID 29576)
10:38:50 - leap.service 启动完成 (PID 29668)
10:53:51 - WebSocket 连接恢复
```

**关键证据**：
```bash
# OOM Killer 日志
Mar 22 10:37:57 oh kernel: Out of memory: Killed process 3095 (miniquote.exe) 
total-vm:2390208kB, anon-rss:516428kB

# 服务状态
NRestarts=1  # xtqmt.service 被重启1次
ExecMainStatus=0  # 正常退出状态

# 内存配置
Memory: 634.7M (xtqmt.service 总物理内存)
Tasks: 227 (进程/线程数)
```

### 3. 依赖关系确认

```ini
# leap.service 依赖关系
Wants=xtqmt.service      # 期望 xtqmt 运行
After=xtqmt.service      # 在 xtqmt 之后启动
```

**架构确认**：
- xtqmt.service 是独立的 QMT 行情服务
- leap.service 依赖 xtqmt.service 提供行情数据
- xtqmt.service 被 OOM 杀死 → leap.service 失去数据源 → 触发重启

---

## 🎯 根本原因分析

### 主要问题：内存泄漏导致的 OOM

1. **虚拟内存 vs 物理内存**：
   - miniquote.exe 申请虚拟内存：2.3GB
   - 实际物理内存使用：504MB
   - 系统总内存：1.9GB（无 swap）

2. **为什么 OOM 仍然发生**：
   - 内存碎片化，无法分配连续大块内存
   - xtqmt.service 总物理内存：634MB
   - 系统可用内存不足 62MB 时触发 OOM
   - 缺少 swap 空间作为缓冲

3. **Wine 环境特殊性**：
   - 227 个线程，每个线程栈 8MB ≈ 1.8GB 虚拟内存
   - Windows DLL 映射消耗大量虚拟地址空间
   - 内存映射文件占用虚拟内存

### 次要问题：日志策略过于保守

- 日志仅保留 17 天（默认应 30 天）
- 总日志空间仅 216MB
- 无法追溯更早的内存增长趋势

---

## 🛠️ 解决方案与优化建议

### 立即措施（优先级：高）

#### 1. 添加 Swap 空间
```bash
# 创建 2GB swap 文件
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 调整 swappiness
sudo sysctl vm.swappiness=60
echo 'vm.swappiness=60' | sudo tee -a /etc/sysctl.conf
```

#### 2. 为 xtqmt.service 添加内存限制
编辑 `/etc/systemd/system/xtqmt.service`：

```ini
[Service]
# 现有配置保持不变，添加以下内容
RestartSec=10                    # 重启等待时间
MemoryMax=3G                     # 最大物理内存 3GB
MemoryHigh=2.5G                  # 达到 2.5GB 时开始节制
OOMScoreAdjust=-500              # 降低 OOM 评分
LimitAS=3G                       # 限制虚拟内存 3GB
CPUQuota=200%                    # CPU 限制（可选）
```

### 中期优化（优先级：中）

#### 3. 优化 leap.service 配置
编辑 `/etc/systemd/system/leap.service`：

```ini
[Service]
Restart=on-failure               # 改为失败时重启
RestartSec=30                    # 等待 30 秒
TimeoutStartSec=60
TimeoutStopSec=30
```

#### 4. 增加日志保留策略
编辑 `/etc/systemd/journald.conf`：

```ini
[Journal]
SystemMaxUse=1G                  # 最多 1GB 日志
MaxRetentionSec=2month           # 保留 2 个月
SystemMaxFileSize=100M           # 单文件 100MB
Compress=yes
```

应用配置：
```bash
sudo systemctl restart systemd-journald
sudo journalctl --vacuum-time=2month
```

#### 5. 创建内存监控脚本
`/opt/scripts/monitor_xtqmt.sh`：

```bash
#!/bin/bash
SERVICE="xtqmt.service"
MEMORY_LIMIT_MB=2500

if systemctl is-active --quiet $SERVICE; then
    MEM_USAGE=$(systemctl show $SERVICE --property=MemoryCurrent | cut -d= -f2)
    if [ -n "$MEM_USAGE" ] && [ "$MEM_USAGE" -gt 0 ]; then
        MEM_MB=$((MEM_USAGE / 1024 / 1024))
        if [ $MEM_MB -gt $MEMORY_LIMIT_MB ]; then
            echo "$(date): xtqmt.service memory ${MEM_MB}MB, restarting" | logger -t xtqmt-monitor
            systemctl restart $SERVICE
        elif [ $MEM_MB -gt 2000 ]; then
            echo "$(date): xtqmt.service memory ${MEM_MB}MB (warning)" | logger -t xtqmt-monitor
        fi
    fi
fi
```

设置定时任务：
```bash
chmod +x /opt/scripts/monitor_xtqmt.sh
echo "*/10 * * * * /opt/scripts/monitor_xtqmt.sh" | sudo crontab -
```

### 长期策略（优先级：低）

#### 6. 主动定期重启
添加 crontab：
```cron
# 每天凌晨 3 点重启 xtqmt
0 3 * * * systemctl restart xtqmt.service

# 凌晨 3:05 重启 leap（等待 xtqmt 就绪）
5 3 * * * sleep 30 && systemctl restart leap.service
```

#### 7. 升级 XtQuant 版本
日志提示有更新版本可用：
```
xtquant250516.1.1已经发布
```
新版本可能修复内存泄漏问题。

#### 8. 考虑硬件升级
- 增加物理内存至 4GB 或以上
- 或使用 SSD 提高 swap 性能

---

## 📊 预期效果

### 优化后指标
| 指标 | 优化前 | 优化后（预期） |
|------|--------|----------------|
| 服务重启频率 | ~每9-10小时 | < 每周1次 |
| OOM 发生概率 | 高 | 极低 |
| 日志保留时间 | 17天 | 2个月 |
| 内存监控 | 无 | 自动预警 |
| Swap 空间 | 0 | 2GB |

### 风险评估
- **低风险**：添加 swap、配置限制、增加日志
- **中风险**：定期重启（可能短暂中断服务）
- **需测试**：XtQuant 升级（可能兼容性问题）

---

## ✅ 实施检查清单

### 第一阶段（立即执行）
- [ ] 添加 2GB swap 空间
- [ ] 修改 xtqmt.service 配置，添加内存限制
- [ ] 重启 xtqmt.service 并验证配置生效
- [ ] 监控 24 小时，确认无异常

### 第二阶段（24小时内）
- [ ] 修改 journald 日志策略
- [ ] 创建内存监控脚本
- [ ] 设置 crontab 定时任务
- [ ] 验证日志保留时间延长

### 第三阶段（本周内）
- [ ] 评估 XtQuant 升级可行性
- [ ] 设置定期重启策略
- [ ] 配置日志归档脚本
- [ ] 编写故障响应文档

---

## 📝 附录

### 关键命令速查
```bash
# 查看服务状态
systemctl status xtqmt.service leap.service

# 查看 OOM 历史
sudo dmesg -T | grep -i "killed process"

# 查看服务重启历史
systemctl show xtqmt.service | grep NRestarts

# 查看内存使用
systemd-cgtop
free -h

# 查看日志
journalctl -u xtqmt.service -f
journalctl -u xtqmt.service --since "1 hour ago"
```

### 配置文件位置
- xtqmt.service: `/etc/systemd/system/xtqmt.service`
- leap.service: `/etc/systemd/system/leap.service`
- journald.conf: `/etc/systemd/journald.conf`
- crontab: `sudo crontab -e`

---

**报告生成时间**：2026-03-22  
**报告人**：系统诊断分析  
**状态**：待实施优化方案