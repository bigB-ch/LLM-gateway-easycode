# LLM Gateway 企业级数据保护体系

> 本文档规定了 LLM Gateway 平台的数据保护措施，确保客户数据的绝对安全。
> 这是一份强制执行的指导文件，所有操作人员必须遵循。

---

## 目录

1. [核心原则](#核心原则)
2. [多层备份体系](#多层备份体系)
3. [操作权限管理](#操作权限管理)
4. [破坏性操作保护](#破坏性操作保护)
5. [监控告警系统](#监控告警系统)
6. [灾难恢复计划](#灾难恢复计划)
7. [日常维护清单](#日常维护清单)
8. [事件响应流程](#事件响应流程)

---

## 核心原则

```
1. 数据安全 > 功能完整性
   - 任何时候都不能为了加快功能开发而牺牲数据安全
   - 当数据安全与其他目标冲突时，数据安全优先

2. 多重备份 > 单点防护
   - 不相信单一的备份或保护机制
   - 至少采用 3 种不同的备份方式

3. 定期测试 > 相信备份
   - 从不假设备份是有效的
   - 定期验证备份的可恢复性

4. 完整审计 > 事后追查
   - 所有操作都必须留下审计日志
   - 发生问题时能够快速定位根因

5. 故障转移 > 手动恢复
   - 尽量采用自动化的故障转移
   - 最小化人工干预，减少错误
```

---

## 多层备份体系

### 第 1 层：本地备份（日常）

**配置**:
- 位置: `/opt/llm-gateway/backups/`
- 频率: 每天凌晨 2:00 UTC+8
- 保留: 7 天轮转
- 文件格式: `llm_gateway_backup_YYYYMMDD_HHMMSS.sql.gz`

**脚本**: `/opt/llm-gateway/backup_database.sh`

**验证**: 每日 03:30 自动运行 `backup_verify.sh`

### 第 2 层：云端备份（中期）

**推荐方案**:

#### 方案 A：AWS S3
```bash
# 配置
- 目标: s3://llm-gateway-backups/
- 频率: 每日 02:15 UTC+8 上传
- 保留: 30 天
- 加密: AES-256
- 成本: ~$1-2/月

# 设置步骤
1. 创建 AWS IAM 用户
2. 配置 AWS CLI
3. 使用 s3cmd 上传脚本
4. 配置 cron 定时任务
```

#### 方案 B：阿里云 OSS
```bash
# 配置
- 目标: oss://llm-gateway-backup/
- 频率: 每日 02:15 UTC+8 上传
- 保留: 30 天
- 加密: OSS 服务端加密
- 成本: ~¥5-10/月

# 设置步骤
1. 创建 OSS bucket
2. 配置 AliyunCLI
3. 使用 ossutil 上传脚本
4. 配置 cron 定时任务
```

#### 方案 C：异地服务器（推荐）
```bash
# 配置
- 目标: 合作伙伴数据中心
- 频率: 每日 02:15 UTC+8 通过 SSH 传输
- 保留: 60 天
- 加密: SSH + GPG
- 成本: 根据合作方案

# 设置步骤
1. 配置 SSH 公钥对
2. 创建备份传输脚本
3. 配置 cron 定时任务
4. 测试 SSH 连接
```

### 第 3 层：冷备份（长期）

**配置**:
- 位置: 离线存储（如光盘、磁带）
- 频率: 每月一次
- 保留: 2 年

---

## 操作权限管理

### 权限分级

```
┌─────────────────────────────────────────────┐
│  级别 1: 查看权限 (任何员工)                  │
│  ├─ 权限: 查看备份日志、监控数据              │
│  └─ 限制: 不能执行任何修改操作                │
├─────────────────────────────────────────────┤
│  级别 2: 操作权限 (运维工程师)                │
│  ├─ 权限: 启动/停止容器、重启服务、查看日志   │
│  ├─ 限制: 不能删除数据卷、不能修改配置        │
│  └─ 确认: 无需额外确认                       │
├─────────────────────────────────────────────┤
│  级别 3: 管理权限 (技术负责人)                │
│  ├─ 权限: 所有操作权限                       │
│  ├─ 限制: 删除操作需要双重确认、2FA 验证      │
│  └─ 审核: 所有破坏性操作需要邮件确认          │
├─────────────────────────────────────────────┤
│  级别 4: 超级权限 (创始人)                    │
│  ├─ 权限: 所有权限                           │
│  ├─ 限制: 所有操作需要邮件/SMS 确认           │
│  └─ 审核: 所有操作都有完整审计日志            │
└─────────────────────────────────────────────┘
```

### 权限配置

```bash
# 创建用户组
groupadd llm-gateway-ops
groupadd llm-gateway-admin

# 分配权限
# 运维: 只读容器操作
usermod -aG docker llm-gateway-ops-user
echo "llm-gateway-ops-user ALL=(ALL) NOPASSWD: /usr/bin/docker" | visudo

# 管理员: 完整操作权限 + 需要确认
usermod -aG docker llm-gateway-admin-user
echo "llm-gateway-admin-user ALL=(ALL) /opt/llm-gateway/*.sh" | visudo
```

---

## 破坏性操作保护

### 禁止的命令

以下命令**绝对禁止**在生产环境执行：

```bash
# ❌ 删除数据卷
docker compose down -v
docker volume rm llm-gateway_pg_data

# ❌ 删除容器文件
rm -rf /var/lib/docker/volumes/llm-gateway_pg_data/

# ❌ 删除数据库
DROP DATABASE llm_gateway;

# ❌ 其他危险操作
docker system prune -a
```

### 保护机制

#### 1. 文件系统级别保护

```bash
# 使数据卷不可删除（追加模式）
chattr +a /var/lib/docker/volumes/llm-gateway_pg_data/_data

# 验证属性
lsattr -d /var/lib/docker/volumes/llm-gateway_pg_data/_data
# 应该显示: ----a------  或类似

# 使配置文件不可修改
chattr +i /opt/llm-gateway/.env
chattr +i /opt/llm-gateway/.env.prod
```

#### 2. 命令拦截器

```bash
# 创建安全的 docker-compose 包装
ln -sf /opt/llm-gateway/safe-docker-compose.sh /usr/local/bin/docker-compose
```

#### 3. 操作确认机制

```bash
# 对于 docker-compose down，要求确认
# 对于 docker volume rm，要求 2FA
# 对于删除操作，要求邮件通知管理员
```

### 恢复被删除文件的方法

如果不幸发生了数据卷删除，可以使用以下方法：

```bash
# 1. 立即停止所有容器，防止数据覆盖
docker-compose stop

# 2. 查看删除前的最近备份
ls -lh /opt/llm-gateway/backups/ | head -5

# 3. 恢复备份到临时容器
docker run -d --name restore-temp -e POSTGRES_PASSWORD=temp postgres:16-alpine
gunzip -c /opt/llm-gateway/backups/llm_gateway_backup_YYYYMMDD.sql.gz | \
  docker exec -i restore-temp psql -U postgres

# 4. 验证数据完整性
docker exec restore-temp psql -U postgres -c "SELECT COUNT(*) FROM users;"

# 5. 重建数据卷
docker volume create llm-gateway_pg_data

# 6. 恢复到新卷
# ... (具体步骤见灾难恢复计划)
```

---

## 监控告警系统

### 监控项

| 监控项 | 阈值 | 告警级别 | 响应 |
|--------|------|--------|------|
| 备份成功率 | < 100% | CRITICAL | 立即调查 |
| 备份文件大小异常 | > 50% 变化 | WARNING | 人工检查 |
| 备份延迟 | > 30min | WARNING | 检查备份脚本 |
| 数据库磁盘使用 | > 80% | WARNING | 扩容评估 |
| 数据行数异常 | > 10% 变化 | WARNING | 数据审计 |
| 主键冲突 | 任何 | CRITICAL | 立即修复 |

### 告警渠道

```
🚨 CRITICAL (立即响应):
   - SMS 短信
   - 紧急邮件
   - PagerDuty 页面
   - Slack @channel

🟡 WARNING (小时内响应):
   - 邮件
   - Slack 通知
   - 日志记录

🟢 INFO (日常记录):
   - 日志文件
   - 监控仪表板
```

---

## 灾难恢复计划

### RTO & RPO

```
RTO (Recovery Time Objective): < 4 小时
RPO (Recovery Point Objective): < 1 小时
```

### 恢复步骤

#### 场景 1：数据库崩溃（常见）

```bash
# 第 1 步：检查问题（5 分钟）
docker-compose logs postgres | tail -50

# 第 2 步：尝试重启（5 分钟）
docker-compose restart postgres

# 第 3 步：验证连接（5 分钟）
docker-compose exec postgres psql -U gateway -d llm_gateway -c "SELECT 1;"

# 第 4 步：如果仍然失败，使用备份恢复
# ... (见下方详细步骤)
```

#### 场景 2：数据卷丢失（严重）

```bash
# 第 1 步：停止所有容器（立即）
docker-compose down

# 第 2 步：准备恢复环境（30 分钟）
- 确保有足够的磁盘空间
- 下载最新备份文件（从云端或异地）

# 第 3 步：启动临时恢复容器（10 分钟）
docker run -d --name restore-db \
  -e POSTGRES_PASSWORD=temp \
  -v recovery_data:/var/lib/postgresql/data \
  postgres:16-alpine

# 第 4 步：恢复数据（20 分钟）
gunzip -c backup_file.sql.gz | docker exec -i restore-db psql -U postgres

# 第 5 步：验证数据（10 分钟）
docker exec restore-db psql -U postgres llm_gateway -c "SELECT COUNT(*) FROM users;"

# 第 6 步：重建生产容器（5 分钟）
# 使用恢复的数据卷启动生产环境

# 总耗时: ~1.5 小时
```

#### 场景 3：数据被破坏（严重）

```bash
# 第 1 步：隔离受污染的数据库（立即）
docker-compose stop

# 第 2 步：启动只读副本做诊断（15 分钟）
# 使用 Redis 缓存或日志中的最后已知状态

# 第 3 步：识别破坏发生的时间点（15 分钟）
# 查看审计日志，定位哪个备份是最后一个完好的

# 第 4 步：从最近的完好备份恢复（30 分钟）

# 第 5 步：重放未恢复的操作日志（30 分钟）
# 从恢复时间点到当前时间的所有操作
```

---

## 日常维护清单

### 每天

- [ ] 检查备份是否按时完成（03:05 UTC+8 前）
- [ ] 检查是否有告警邮件
- [ ] 验证 PostgreSQL 容器状态
- [ ] 检查磁盘空间使用率

### 每周（周一）

- [ ] 运行备份验证脚本 (自动)
- [ ] 运行恢复测试 (自动)
- [ ] 查看监控仪表板
- [ ] 检查告警日志

### 每月

- [ ] 完整的灾难恢复演练
- [ ] 审查权限设置
- [ ] 更新文档
- [ ] 分析备份统计

### 每季度

- [ ] 数据一致性全量检查
- [ ] 安全审计
- [ ] 恢复流程培训
- [ ] 更新 DRP 文档

---

## 事件响应流程

### 发生数据问题时的处理步骤

```
第 1 分钟：
├─ 确认问题的严重程度
├─ 立即通知技术负责人
└─ 停止相关操作（防止进一步破坏）

第 5 分钟：
├─ 启动灾难恢复计划
├─ 通知所有利益相关者
└─ 记录详细的事件时间线

第 30 分钟：
├─ 完成数据恢复
├─ 验证数据完整性
└─ 恢复服务可用性

第 2 小时：
├─ 完整的事后分析
├─ 识别根本原因
└─ 提出改进措施

第 24 小时：
├─ 编写完整的事件报告
├─ 更新相关文档
└─ 开展复盘会议
```

### 通知模板

**邮件标题**: `[URGENT] Data Issue - Action Required`

```
Subject: Data Issue Detected - Immediate Action Required

Timeline:
- Detection: [时间]
- Impact: [受影响的用户数、数据范围]
- Status: [恢复中/已恢复/未恢复]

Actions Taken:
- [操作 1]
- [操作 2]

Next Steps:
- [下一步 1]
- [下一步 2]

Contact: [负责人电话和邮箱]
```

---

## 结论

> **所有人员必须记住：我们的客户信任我们保护他们的数据。**
> **这是我们最核心的责任，没有任何功能或时间压力可以优先于数据安全。**

本文档将持续更新，所有更改都将通知所有相关人员。

最后修改: 2026-06-18
审批者: [技术负责人名字]
