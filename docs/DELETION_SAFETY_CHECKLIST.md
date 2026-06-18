# 删除数据库前必须满足的关键条件

## 🚫 绝对准则

**在执行任何数据库删除、修改或高风险操作之前：**

### ✅ 必须完成以下检查清单

```
┌─────────────────────────────────────────────────────────────────┐
│ 删除数据库中的任何东西之前，必须：                               │
│                                                                  │
│ ☐ 第 1 步：验证最新备份能够成功恢复                             │
│           └─ 如果备份无法恢复，禁止任何操作                     │
│                                                                  │
│ ☐ 第 2 步：对即将删除的数据进行完整导出                         │
│           └─ 保存在离线位置（USB/外部硬盘）                     │
│                                                                  │
│ ☐ 第 3 步：创建"快照"用于恢复测试                              │
│           └─ 必须能够在 4 小时内恢复这些数据                    │
│                                                                  │
│ ☐ 第 4 步：获得技术负责人的明确书面批准                         │
│           └─ 邮件/文档记录，含有风险评估                        │
│                                                                  │
│ ☐ 第 5 步：制定完整的回滚计划                                  │
│           └─ 如果出问题，能在 15 分钟内回滚                     │
│                                                                  │
│ 如果任何一项不满足，禁止执行任何删除操作                         │
└─────────────────────────────────────────────────────────────────┘
```

### 🔍 备份验证清单

删除数据前**必须验证**备份：

```sql
-- 1. 检查最新备份文件
ls -lh /opt/llm-gateway/backups/*.sql.gz | head -1

-- 2. 验证备份完整性（必须通过）
gunzip -t /opt/llm-gateway/backups/llm_gateway_backup_*.sql.gz

-- 3. 测试恢复备份（必须成功）
docker run --rm -e POSTGRES_PASSWORD=test postgres:16-alpine
gunzip -c backup_file.sql.gz | psql -U postgres

-- 4. 验证备份中的数据（必须检查）
SELECT COUNT(*) FROM users;          -- 应该 > 0
SELECT COUNT(*) FROM api_keys;       -- 应该 > 0  
SELECT COUNT(*) FROM recharge_records; -- 应该 > 0

-- 5. 检查数据完整性（必须通过）
SELECT COUNT(*) FROM users WHERE deleted_at IS NULL;
-- 结果应该 > 1000 或符合预期数量
```

### 📋 前置检查脚本

```bash
#!/bin/bash
# 删除前的强制检查

echo "执行删除前的强制检查..."
echo ""

# 1. 检查备份是否存在且有效
echo "[1] 验证备份..."
BACKUP=$(ls -t /opt/llm-gateway/backups/*.sql.gz 2>/dev/null | head -1)

if [ -z "$BACKUP" ]; then
    echo "❌ FATAL: 没有找到备份文件！"
    echo "禁止执行任何删除操作！"
    exit 1
fi

BACKUP_AGE=$(( $(date +%s) - $(stat -c%Y "$BACKUP") ))
echo "最新备份: $BACKUP"
echo "备份年龄: $((BACKUP_AGE / 3600)) 小时前"

if [ "$BACKUP_AGE" -gt 86400 ]; then
    echo "❌ ERROR: 备份超过 24 小时，无法继续"
    exit 1
fi

# 2. 验证备份可以解压
echo "[2] 验证备份文件完整性..."
if ! gunzip -t "$BACKUP" 2>/dev/null; then
    echo "❌ FATAL: 备份文件损坏！"
    echo "禁止执行任何删除操作！"
    exit 1
fi

echo "✓ 备份文件有效"

# 3. 测试恢复备份
echo "[3] 测试恢复备份..."
if ! gunzip -c "$BACKUP" | head -100 | grep -q "CREATE TABLE"; then
    echo "❌ ERROR: 备份似乎不包含有效数据"
    exit 1
fi

echo "✓ 备份可以恢复"

# 4. 检查数据库中的数据量
echo "[4] 检查当前数据库..."
USERS=$(docker compose exec -T postgres psql -U gateway -d llm_gateway -tAc "SELECT COUNT(*) FROM users;" 2>/dev/null)
echo "用户数: $USERS"

if [ -z "$USERS" ] || [ "$USERS" -lt 1 ]; then
    echo "⚠️  WARNING: 用户数异常少，确认删除操作是安全的"
    read -p "继续? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        exit 1
    fi
fi

# 5. 确认管理员批准
echo "[5] 获得管理员批准..."
read -p "技术负责人已批准此删除操作吗? (yes/no): " APPROVED

if [ "$APPROVED" != "yes" ]; then
    echo "❌ 缺少管理员批准，禁止删除"
    exit 1
fi

# 所有检查通过
echo ""
echo "✓ 所有前置检查通过"
echo "现在可以执行删除操作"
```

### 🚨 严格规则

| 情况 | 行为 |
|------|------|
| 备份不存在 | ❌ 禁止一切操作，立即停止 |
| 备份无法解压 | ❌ 禁止一切操作，立即停止 |
| 备份超过 24 小时 | ⚠️ 询问用户，可能拒绝 |
| 无法恢复备份 | ❌ 禁止一切操作，立即停止 |
| 没有书面批准 | ❌ 禁止一切操作，立即停止 |
| 没有回滚计划 | ❌ 禁止一切操作，立即停止 |

### 🎯 删除操作的完整流程

```
第 0 步：前置检查 (自动进行) ← 这是最关键的一步
├─ 备份存在且有效 ✓
├─ 备份可以恢复 ✓
├─ 当前数据正确 ✓
└─ 如果任何检查失败 → 停止，禁止删除

第 1 步：获得批准
├─ 技术负责人邮件批准
├─ 包含风险评估
└─ 记录文档

第 2 步：数据导出
├─ 导出即将删除的数据
├─ 保存到离线存储
└─ 验证导出完整性

第 3 步：最终确认
├─ 再次检查备份
├─ 确认所有检查通过
└─ 要求操作人员最后确认

第 4 步：执行删除
├─ 记录开始时间
├─ 执行删除操作
└─ 记录完成时间

第 5 步：立即验证
├─ 检查数据完整性
├─ 验证删除成功
└─ 确认系统正常

第 6 步：审计
├─ 记录所有操作
├─ 存档所有文档
└─ 通知相关人员
```

### 💾 如何恢复已删除的数据

如果意外删除了数据：

```bash
# 1. 立即停止所有写操作
docker-compose stop

# 2. 从最近备份恢复
gunzip -c /opt/llm-gateway/backups/llm_gateway_backup_*.sql.gz | \
  docker compose exec -i postgres psql -U postgres

# 3. 如果没有备份，尝试从 delete_log 表恢复
SELECT * FROM delete_log WHERE table_name = 'users';

# 4. 如果有导出的数据文件
COPY users FROM '/path/to/exported_users.csv';
```

---

## 结论

**我们的规则很简单：**

> 没有备份，就不能删除任何东西。
> 
> 有备份，也必须能恢复，才能删除。
>
> 能恢复，也必须有批准和计划，才能删除。

这不是建议，这是**强制性的规则**。
