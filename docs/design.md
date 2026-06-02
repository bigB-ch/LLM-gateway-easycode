# LLM Gateway — 大模型接口网关中转平台 设计文档

## 1. 项目概述

面向外部客户的商业 API 中转平台。客户使用标准 OpenAI 兼容接口接入，底层对接国内外主流大模型供应商，提供统一鉴权、限流、计费、监控能力。

### 1.1 核心选型

| 维度 | 选择 |
|------|------|
| 场景 | 对外商业 API 中转服务 |
| 供应商覆盖 | 全接入（OpenAI / Claude / Gemini / DeepSeek / 通义等），逐步扩展 |
| 下游接口 | OpenAI 兼容格式 + Web 管理后台 |
| 技术栈 | Python FastAPI |
| 存储 | PostgreSQL + Redis Sentinel |
| 认证 | API Key (Bearer Token) |
| 计费 | 套餐包 + 按量付费 |
| 部署 | Docker Compose，预留 K8s 扩展 |

### 1.2 架构决策：网关 + 管理服务分离

- **API 网关 (Gateway)**：轻量低延迟热路径，只做认证 → 限流 → 转发。不碰用户管理、不计费。
- **管理服务 (Admin)**：Web 后台 API + Stream Consumer，处理用户、计费、报表。
- 两者共享 PG + Redis，通过 DB 同步配置，Gateway 运行时只读 Redis。

## 2. 整体架构

```
                              ┌──────────────────────┐
                              │   Nginx :443         │
                              │   - SSL终止           │
                              │   - /v1/* → Gateway   │
                              │   - /admin/* → Admin  │
                              │   - least_conn 轮询   │
                              └──────┬───────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
  │  Gateway #1 :8000 │  │  Gateway #N :8000 │  │  Admin #1 :8001   │
  │  - Key认证        │  │  (水平扩展)        │  │  - 用户管理       │
  │  - 限流           │  │                   │  │  - 套餐/计费      │
  │  - 模型路由        │  │                   │  │  - Stream消费     │
  │  - 熔断/重试       │  │                   │  │  - 报表API        │
  │  - 用量日志        │  │                   │  │  - Consumer       │
  └────────┬──────────┘  └────────┬──────────┘  └────────┬──────────┘
           │                      │                      │
           └──────────────────────┼──────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
  ┌───────────────────┐  ┌───────────────────┐  ┌──────────────┐
  │ Redis Sentinel    │  │  PostgreSQL       │  │  Prometheus  │
  │ 1主2从 3哨兵      │  │ - 用户/Key/套餐    │  │  + Grafana   │
  │ - Key缓存         │  │ - 用量聚合表       │  │  - 仪表盘    │
  │ - 限流计数         │  │ - 消费确认表       │  │  - 告警规则   │
  │ - 熔断器状态       │  │ - 订单/充值记录    │  └──────────────┘
  │ - 用量 Stream     │  └───────────────────┘
  │ - Supplier配置    │
  └───────────────────┘
```

### 2.1 可靠性与扩展性

| 风险点 | 方案 |
|--------|------|
| Redis 单点 | Redis Sentinel 一主两从三哨兵，Gateway/Admin 配置 Sentinel 连接 |
| Gateway 单点 | 无状态设计，Nginx `least_conn` 轮询，`docker compose up --scale gateway=N` 扩容 |
| Admin 单点 | 多实例 + Redis Stream Consumer Group，auto-failover，pending 消息自动认领 |
| 日志丢失 | Consumer Group + XACK + 死信队列，PG 写入幂等（`request_id` 唯一约束） |
| 供应商故障 | 独立熔断器 + 指数退避重试 + 降级切换备用供应商 |

## 3. Gateway 详细设计

### 3.1 请求处理流程

```
客户端请求 POST /v1/chat/completions
    │
    ├─→ [中间件层]
    │   1. 提取 Authorization Header → API Key
    │   2. 查 Redis Hash {apikey → user_id, rate_limit, model_allowlist}
    │      Key 不存在 → 401 (统一错误消息，与吊销/封禁相同)
    │   3. 查 Redis 滑动窗口限流
    │      超限 → 429 + Retry-After Header
    │   4. 验证目标模型权限 → 403
    │
    ├─→ [供应商适配层]
    │   5. 根据 model 名称路由到对应 Adapter
    │      gpt-* → OpenAIAdapter
    │      claude-* → ClaudeAdapter
    │      gemini-* → GeminiAdapter
    │   6. Adapter 统一接口：translate → call → translate
    │
    ├─→ [熔断/重试层]
    │   7. 检查 Redis 熔断器状态
    │      OPEN → 检查备用供应商
    │      HALF_OPEN → 允许1个探测请求
    │      CLOSED → 正常请求
    │   8. 调用供应商，超时30s
    │      失败 → 指数退避重试 (1s, 2s, 最多2次)
    │      幂等保证：每次请求带唯一 request_id
    │      重试仍失败 → 熔断器计数器+1
    │      有备用供应商 → 降级切换，无备用 → 503
    │
    ├─→ [日志上报层]
    │   9. 构造日志: {request_id, user_id, model, tokens, cost, latency, status}
    │   10. XADD redis usage_log_stream * {...} (异步，不等待消费)
    │
    └─→ 返回统一格式响应
```

### 3.2 供应商适配器接口

```python
class BaseAdapter(ABC):
    model_patterns: list[str]

    @abstractmethod
    async def chat_completion(self, request: UnifiedRequest) -> UnifiedResponse:
        """统一请求 → 供应商格式 → 调用 → 统一响应"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """连通性检查，供熔断器探测使用"""
        ...
```

新增供应商只需实现一个 Adapter 类，注册 model_patterns 即可。

### 3.3 熔断器配置

```python
CIRCUIT_BREAKER_CONFIG = {
    "openai":       {"failure_threshold": 5, "timeout_seconds": 30, "half_open_ttl": 30},
    "anthropic":    {"failure_threshold": 5, "timeout_seconds": 30, "half_open_ttl": 30},
    "google":       {"failure_threshold": 5, "timeout_seconds": 30, "half_open_ttl": 30},
    "deepseek":     {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 60},
    "qwen":         {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 60},
}
```

熔断器状态存 Redis Hash：`cb:{provider} → {status, failure_count, last_failure_time}`。所有 Gateway 实例共享，全局生效。

### 3.4 滑动窗口限流

Redis Lua 脚本保证原子性：

```lua
-- 每次请求执行
local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local current = redis.call('ZCARD', key)
if current >= limit then
    return 0  -- 拒绝
end
redis.call('ZADD', key, now, now .. ':' .. math.random())
redis.call('EXPIRE', key, window)
return 1  -- 放行
```

## 4. Admin 服务设计

### 4.1 功能模块

```
Admin :8001
├── /admin/api/auth          ← 登录/注册
├── /admin/api/users         ← 用户管理
├── /admin/api/keys          ← API Key 管理
├── /admin/api/plans         ← 套餐管理
├── /admin/api/billing       ← 计费结算
├── /admin/api/reports       ← 用量报表
├── /admin/api/settings      ← 系统配置
├── /admin/api/logs          ← 审计日志
└── Stream Consumer          ← 后台消费 Redis Stream
```

### 4.2 Stream 消费者

```python
GROUP_NAME = "usage_consumers"
STREAM_KEY = "usage_log_stream"

while True:
    messages = redis.xreadgroup(
        GROUP_NAME, CONSUMER_NAME, {STREAM_KEY: ">"},
        count=100, block=5000
    )
    if messages:
        batch_insert_to_pg(messages)         # 批量 INSERT
        for msg_id in message_ids:
            redis.xack(STREAM_KEY, GROUP_NAME, msg_id)

    pending = redis.xpending(STREAM_KEY, GROUP_NAME)
    if pending["pending"] > 100:
        claim_and_retry()                    # 认领超时消息
```

保障机制：批量写入 / XACK 确认 / `request_id` 幂等 / pending 超时认领 / 重试3次后进死信队列。

## 5. 客户端体验设计

### 5.1 API 接入：三行代码零改动

```python
# 原来调用 OpenAI
from openai import OpenAI
client = OpenAI(api_key="sk-xxx")

# 改成调用网关 — 仅改两行
from openai import OpenAI
client = OpenAI(
    api_key="sk-你的Key",
    base_url="https://your-gateway.com/v1"
)
# 其余代码一行不动
```

### 5.2 客户操作流程

```
注册 ────────▶ 创建 Key ────────▶ 充值使用
（用户名/密码/邮箱/验证码）

注册详细流程：
  输入用户名 + 密码 + 邮箱 → 发送6位验证码到邮箱
  ├── 验证码有效期 5 分钟
  ├── 60 秒内不可重发
  ├── 同一邮箱每天最多发 5 次
  └── 验证通过 → 自动登录 → 首页
```

### 5.3 管理后台首页

```
┌─────────────────────────────────────────────────┐
│  用户名                                          │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ 今日调用  │  │ 今日消费  │  │ 账户余额  │       │
│  │  1,234   │  │  ¥12.34  │  │ ¥500.00  │       │
│  └──────────┘  └──────────┘  └──────────┘       │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  API Key: sk-a1b2****            [复制]  │   │
│  │  创建于 2026-06-01 · 最后使用 2分钟前     │   │
│  │  [创建新Key]  [管理Key]                  │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  最近7天消费趋势 ▁▂▃▄▅▆▇                         │
│                                                  │
│  curl https://your-gateway.com/v1/... [一键复制] │
│                                                  │
│  [充值]  [用量明细]  [套餐]  [设置]              │
└─────────────────────────────────────────────────┘
```

## 6. 数据库表设计

### 6.1 核心表

```sql
-- 用户表
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(64) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,          -- bcrypt
    role            VARCHAR(16) NOT NULL DEFAULT 'customer',
    balance         BIGINT NOT NULL DEFAULT 0,       -- 余额，单位：分
    status          VARCHAR(16) NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- API Key 表
CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    key_hash        VARCHAR(64) NOT NULL UNIQUE,     -- SHA256(key)
    key_prefix      VARCHAR(8) NOT NULL,             -- 前8位明文，展示用
    name            VARCHAR(128),
    rate_limit      INT NOT NULL DEFAULT 60,         -- 每分钟最大请求数
    model_allowlist TEXT,                            -- 允许的模型，NULL=全部
    status          VARCHAR(16) NOT NULL DEFAULT 'active',
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,                     -- 默认90天过期
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 套餐表
CREATE TABLE plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(128) NOT NULL,
    description     TEXT,
    token_quota     BIGINT NOT NULL,
    price           BIGINT NOT NULL,                 -- 价格，单位：分
    duration_days   INT NOT NULL DEFAULT 30,
    status          VARCHAR(16) NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 用户已购套餐
CREATE TABLE user_plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    plan_id         UUID NOT NULL REFERENCES plans(id),
    token_remaining BIGINT NOT NULL,
    purchased_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL
);

-- 用量日志表
CREATE TABLE usage_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      VARCHAR(64) NOT NULL UNIQUE,     -- 幂等键
    user_id         UUID NOT NULL REFERENCES users(id),
    api_key_prefix  VARCHAR(8) NOT NULL,
    model           VARCHAR(64) NOT NULL,
    provider        VARCHAR(32) NOT NULL,
    prompt_tokens   INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    cost            BIGINT NOT NULL,                 -- 成本价，单位：分
    bill_cost       BIGINT NOT NULL,                 -- 向用户计费金额，单位：分
    latency_ms      INT NOT NULL,
    status          VARCHAR(16) NOT NULL,
    error_msg       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_usage_logs_user_created ON usage_logs(user_id, created_at DESC);

-- 充值记录
CREATE TABLE recharge_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    amount          BIGINT NOT NULL,
    method          VARCHAR(32) NOT NULL,
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 审计日志
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID,
    action          VARCHAR(64) NOT NULL,
    resource        VARCHAR(128),
    detail          JSONB,
    ip              INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 系统配置
CREATE TABLE system_config (
    key             VARCHAR(128) PRIMARY KEY,
    value           JSONB NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.2 用量日志分区策略

日活 > 10 万时触发按月分区：

```sql
CREATE TABLE usage_logs_202601 PARTITION OF usage_logs
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

超过 6 个月的分区聚合后卸载到冷存储。

## 7. 安全设计

### 7.1 API Key 生命周期安全

```
生成                  存储                   传输                   验证                  吊销
secrets.token_hex(32) → PG只存SHA256 → 仅HTTPS的Header → Redis存hash → 立即删Redis+PG标记
明文仅创建时展示一次                        Bearer Token          不存明文
```

Key 格式：`sk-` + 32字节随机hex。默认90天过期，不活跃自动禁用。

### 7.2 传输层安全

- Nginx TLS 1.3 only，内部 Docker 网络之间走 HTTP
- HSTS Header 强制 HTTPS
- Nginx 统一添加安全 Header：`X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`

### 7.3 上游密钥管理

- 供应商 Key 在 PG 中 AES-256 加密存储
- Gateway 使用 `SecretStr` 包装类型，`__str__` 自动替换为 `****`
- 错误响应不泄露供应商 Key、内部 IP、堆栈信息

### 7.4 认证与授权

| 路径 | 认证方式 | 说明 |
|------|---------|------|
| `/v1/*` | API Key (Bearer Token) | 按 Key 粒度限流、扣费 |
| `/admin/api/*` | JWT (RS256) | RBAC: super_admin / admin / viewer |
| `/admin/login` | 登录页，公开 | 单 IP 60次/分钟限流 |

JWT access_token 15分钟，refresh_token 7天。登出时在 Redis 设黑名单实现主动踢下线。

### 7.5 注入攻击防护

| 攻击类型 | 防护措施 |
|----------|---------|
| SQL 注入 | SQLAlchemy ORM 参数化查询 |
| SSRF | 上游 URL 域名白名单校验 |
| Header 注入 | 仅转发必要的 HTTP Header，其余丢弃 |

### 7.6 信息泄漏防护

**统一错误消息**：所有认证失败返回完全相同的 HTTP 401 和消息体：

```json
{"error": "invalid_api_key"}
```

Key 不存在、Key 已吊销、用户被封禁 → 返回相同消息，攻击者无法枚举。

**时间侧信道防护**：补齐到固定耗时，掩盖 Redis 查询差异。

**API 响应脱敏**：列表接口不返回 total 总数，用 cursor 分页。导出限制每次 10000 条。

### 7.7 爬虫与 DDoS 防御

```
第1层：Nginx
  ├── /v1/* 单 IP 300 req/min
  ├── 无 UA 或爬虫 UA → 403
  ├── 超大 body → 444 直接断开
  └── robots.txt: /admin/ disallow

第2层：Gateway
  ├── 滑动窗口限流 (Key级别)
  ├── 新 Key 24h 内限流减半
  ├── 同一 IP 多 Key → 标记可疑
  └── 连续10次401 → IP封禁1h

第3层：Admin
  ├── /admin/api/* 单 IP 60 req/min
  ├── 登录连续失败5次 → IP封禁15min + 验证码
  └── Key创建限流: 每人5次/小时
```

## 8. 监控告警

### 8.1 监控指标

| 类别 | 指标 | 告警阈值 |
|------|------|---------|
| Gateway | QPS、P50/P95/P99延迟、错误率 | 错误率 > 5%、P99 > 10s |
| Gateway 实例 | 健康检查 `/health` | 连续失败3次 |
| Redis | 内存使用率、Stream 堆积量 | 内存 > 80%、堆积 > 10000 |
| Admin 消费者 | 消费延迟、pending 消息数 | pending > 5000、延迟 > 30s |
| PG | 连接数、写入延迟 | 连接数 > 80%、延迟 > 1s |

### 8.2 实现

- Prometheus 拉取 Gateway/Admin `/metrics` 端点
- Grafana 预置仪表盘 + 告警规则
- 结构化 JSON 日志输出 stdout
- 告警 Webhook 推飞书/钉钉/企业微信

## 9. 服务器容量规划

### 9.1 扩展对照表

| 日活用户 | 日均请求 | 峰值 QPS | Gateway 实例 |
|----------|---------|---------|-------------|
| 100 | 5,000 | ~1 | 1 |
| 1,000 | 50,000 | ~3 | 1 |
| 10,000 | 500,000 | ~18 | 1-2 |
| 100,000 | 5,000,000 | ~175 | 2-3 |

基准：单 Gateway 实例 (4C8G) 保守承载 ~400QPS，瓶颈在 SSE 长连接并发而非 CPU。

### 9.2 部署配置

**起步档 (日活 < 1000)**：单台云服务器跑全部组件。

| 组件 | 部署方式 | 配置 |
|------|---------|------|
| 全部 | 1 台云服务器，Docker Compose 编排 | 4C8G + 100GB SSD |
| Nginx + Gateway + Admin + PG + Redis | 同一宿主机，Docker 内部网络通信 | 仅 Nginx 443 端口对外 |
| 月费估算 | | ~¥100-200 |

Redis 单实例，开 AOF 持久化 + `restart: always`，挂了自动拉起，数据不丢。此阶段可接受短暂不可用。

**成长档 (日活 1000-50000)**：组件拆分到独立服务器。

| 组件 | 配置 | 数量 |
|------|------|------|
| Nginx | 2C2G | 1台 |
| Gateway | 4C8G | 2-3台 |
| Admin | 2C4G | 2台 |
| Redis Sentinel | 2C4G | 3台 |
| PostgreSQL | 4C8G + 200GB SSD | 1台 |
| Prometheus + Grafana | 2C4G | 1台 |

**成熟档 (日活 > 50000)**：迁移到 K8s 集群，云负载均衡替代 Nginx，PG 加只读副本，Redis Cluster 替代 Sentinel。

## 10. 项目结构

```
llm-gateway/
├── docker-compose.yml
├── .env.example
├── nginx/
│   └── nginx.conf
├── gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── middleware/
│   │   ├── auth.py
│   │   ├── ratelimit.py
│   │   └── logging.py
│   ├── adapters/
│   │   ├── base.py
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   ├── google.py
│   │   └── ...
│   ├── circuit_breaker.py
│   └── metrics.py
├── admin/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── consumer.py
│   └── metrics.py
├── frontend/               # 管理后台 SPA
│   └── ...
├── redis/
│   └── sentinel.conf
└── docs/
    └── design.md
```
