# LLM-Gateway 流量日志统计 & 计费审计报告

> 审计日期：2026-06-21  
> 审计范围：流量日志采集 → 存储 → 统计报表 → 余额/套餐扣款 全链路  
> 项目路径：`D:\code\llm-gateway`

---

## 一、整体架构概览

```
用户请求 → Gateway (FastAPI)
              │
              ├─ 1. Auth (API Key + Redis 缓存余额)
              ├─ 2. Rate Limit
              ├─ 3. 转发到上游 LLM Provider
              ├─ 4. 从上游响应提取 token 用量
              ├─ 5. calculate_cost() → cost / bill_cost
              └─ 6. xadd → Redis Stream "usage_log_stream"
                                │
                 Admin Consumer ←┘  (异步消费者)
                     │
                     ├─ batch_insert → PostgreSQL usage_logs
                     ├─ 扣除 user_plans.token_remaining (FOR UPDATE)
                     └─ 扣除 users.balance (FOR UPDATE)
```

### 关键模块文件

| 模块 | 文件 | 职责 |
|------|------|------|
| 网关路由 | `gateway/routes.py` | 接收请求、转发、记录日志到 Redis Stream |
| Token 提取 | `gateway/adapters/openai.py` | 从上游响应提取 prompt/completion tokens |
| Token 提取 | `gateway/adapters/anthropic.py` | 同上，Anthropic 格式 |
| 计费计算 | `gateway/pricing.py` | 根据模型定价计算 cost / bill_cost |
| 认证/余额检查 | `gateway/middleware/auth.py` | API Key 认证 + Redis 缓存余额检查 |
| 异步消费 | `admin/consumer.py` | 消费 Redis Stream，写入 DB + 扣款 |
| 日志模型 | `admin/models/usage_log.py` | usage_logs 表结构 |
| 用户模型 | `admin/models/user.py` | users 表 (含 balance 字段) |
| 套餐模型 | `admin/models/plan.py` | plans / user_plans 表结构 |
| 统计报表 | `admin/routes/reports.py` | dashboard / trend / daily / usage 等统计接口 |
| 审计 SQL | `scripts/audit_usage_logs.sql` | 数据一致性审计脚本 |

---

## 二、数据流详细分析

### 2.1 日志采集流程

```
用户请求
  │
  ├─ verify_api_key()
  │   ├─ 从 Redis 查 API Key (hash)
  │   ├─ 从 Redis 查 user_balance (TTL 1h)
  │   └─ 从 Redis 查 user_has_plans (TTL 24h)
  │
  ├─ check_rate_limit()
  │
  ├─ 转发到上游 LLM Provider
  │   └─ 提取 response.usage (prompt_tokens, completion_tokens)
  │
  ├─ calculate_cost(model, prompt_tokens, completion_tokens)
  │   └─ 根据 PRICING 字典计算 cost_fen, bill_fen
  │
  └─ redis.xadd("usage_log_stream", log_entry)
       ├─ request_id, user_id, api_key_prefix
       ├─ model, provider
       ├─ prompt_tokens, completion_tokens
       ├─ cost, bill_cost    ← 单位：分 (fen)
       ├─ latency_ms, status, error_msg, ip
       └─ 字段全部存为 string 类型
```

### 2.2 异步消费流程

```
Admin Consumer (asyncio 循环)
  │
  ├─ redis.xreadgroup() 每次最多 100 条
  │
  ├─ batch_insert(parsed)
  │   ├─ 拼 SQL → INSERT INTO usage_logs (...) VALUES (...) ON CONFLICT (request_id) DO NOTHING
  │   ├─ 如果 inserted > 0（即有新插入）：
  │   │   ├─ 遍历每条消息
  │   │   ├─ 对 status=success 的消息：
  │   │   │   ├─ SELECT ... FROM user_plans WHERE user_id=:uid AND token_remaining>0 AND expires_at>NOW() ORDER BY expires_at ASC FOR UPDATE
  │   │   │   ├─ 逐条扣减 plan 额度
  │   │   │   ├─ 剩余部分：SELECT balance FROM users WHERE id=:uid FOR UPDATE
  │   │   │   └─ UPDATE users SET balance = balance - :d
  │   │   └─ 更新 Redis 缓存 (user_balance, user_has_plans)
  │   └─ 返回 msg_ids
  │
  ├─ redis.xack() 确认已处理
  │
  └─ 异常处理：重试最多 3 次 → 移入 DLQ（死信队列）
```

---

## 三、发现的问题

### 🔴 严重 (Critical)

#### 1. 批处理双重扣款漏洞

- **位置**: `admin/consumer.py` L64-125
- **严重程度**: 🔴 **严重** — **已修复** (2026-06-23)
- **描述**:
  `inserted = result.rowcount` 被赋值但**从未使用**。`ON CONFLICT (request_id) DO NOTHING` 跳过的重复消息，余额扣减循环（L67-125）仍然会无条件执行所有消息。当消息因 XACK 丢失被重新投递时：
  - 第一次：INSERT 成功，扣款 ✅
  - 第二次：ON CONFLICT 跳过插入（rowcount=0），但扣款循环**仍然执行**，用户被扣两次
- **影响**: 用户被**双重计费**
- **根因**: `inserted` 变量赋值后未用于守卫扣款逻辑
- **修复**: 在扣款循环前加 `if inserted == 0: return msg_ids`

#### 2. DLQ 死代码：格式异常消息永不进入死信队列

- **位置**: `admin/consumer.py` L148-157（旧版 L153-162）
- **严重程度**: 🔴 **严重** — **已修复** (2026-06-23)
- **描述**:
  `batch_insert()` 始终返回完整 `msg_ids` 列表，`if eid not in acked` 永远为 False。DLQ 路由代码**完全不执行**。格式损坏的消息引发 `int()` 转换异常（如非数字的 `prompt_tokens`），被 `except` 捕获后既不 XACK 也不入 DLQ，永远在 pending 列表无限重试——毒丸模式。
- **影响**: 单条坏消息导致整批消息卡住，直到手动清理
- **修复**: DLQ 逻辑移到 `batch_insert` 的异常处理块中

#### 3. DeepSeek 直通路径：xadd 失败日志永久丢失

- **位置**: `gateway/routes.py` L229
- **严重程度**: 🔴 **严重** — **已修复** (2026-06-23)
- **描述**:
  DeepSeek 流式直通路径的 `redis.xadd()` 调用在 try/except 块**之外**。如果 Redis 写入失败，异常从 async generator 未处理逃逸，请求已成功流式返回给客户端，但**没有任何日志写入**——不是错误日志，不是成功日志，完全丢失。
- **影响**: 请求成功但完全丢失计费记录，收入归零
- **修复**: try/except 包装 xadd 调用

#### 4. `/user-daily` 端点带 `date_to` 参数时 NameError 崩溃

- **位置**: `admin/routes/reports.py` L239（旧版）
- **严重程度**: 🔴 **严重** — **已修复** (2026-06-23)
- **描述**:
  `parse_date_end()` 定义在 `usage_details()` 函数**内部**（局部函数），而 `/user-daily` 端点在模块作用域调用它。任何带 `date_to` 参数的请求抛出 `NameError: name 'parse_date_end' is not defined`，**返回 500**。
- **影响**: 管理端用户每日用量页面完全不可用
- **修复**: 提取为模块级函数

#### 5. 并发请求下的余额透支风险

- **位置**: `gateway/middleware/auth.py` L68-92 + `admin/consumer.py` L111-124
- **严重程度**: 🟠 **高危**
- **描述**:
  余额检查发生在请求**入口处**（auth 中间件），此时余额可能已缓存最多**1小时**（Redis TTL=3600s）。真正的扣款是**异步**在消费线程中执行的。如果有两个请求并发到来且余额只够一个：
  - Consumer 事务中 `FOR UPDATE` 锁住了行，先到的请求扣款成功
  - 后到的请求 `FOR UPDATE` 等待，读到余额不足，`user_balance < remaining` 只扣可用余额
  - 用户仍获得了服务但没付足
- **影响**: 用户可**超额使用**服务，产生坏账
- **根因**: auth 的余额检查是准入判断，和实际扣款不是原子的。但 `FOR UPDATE` 行锁防止了**超扣**，所以不是双重扣费风险，而是**赊账风险**。
- **注意**: 这和问题 #6 相关——都属于"余额不足仍提供服务"的范畴

#### 6. 余额不足时部分扣款导致数据不一致

- **位置**: `admin/consumer.py` L110-124
- **严重程度**: 🟡 **中等**
- **描述**:
  在 consumer 的扣款逻辑中，如果 `remaining > 0` 但用户余额不足时：
  ```python
  if user_balance < remaining:
      remaining = user_balance   # 只扣可用余额
  ```
  这意味着即使用户余额为 0，请求也已经成功处理了。上游 API 已经产生了成本，但用户没有付足费用。而且 `usage_logs` 中记录的 `bill_cost` 仍然是全额，造成了**日志和实际扣款不一致**。
- **影响**: 系统承担上游成本，用户免费或低价使用；对账时无法识别哪些订单被部分扣款
- **根因**: 缺少对部分扣款场景的日志标记

---

### 🟠 高危 (High)

#### 7. xadd 写入失败：成功请求的日志被零值错误日志覆盖

- **位置**: `gateway/routes.py` L317, L391（流式路径）
- **严重程度**: 🟠 **高危** — **已修复** (2026-06-23)
- **描述**:
  非 DeepSeek 流式路径中，`redis.xadd()` 在 try 块内部。如果成功流式的 xadd 失败，异常被 `except Exception` 捕获，写入一条全零的错误日志。**成功的 API 调用被记录为失败的零费用调用**。收入从账单中消失。
- **影响**: 请求成功但日志被错误条目覆盖，收入损失
- **修复**: try/except 保护 xadd 写入，失败只记录日志不覆盖成功状态

#### 8. 非流式请求 xadd 失败导致客户端收到 500

- **位置**: `gateway/routes.py` L481, L681
- **严重程度**: 🟠 **高危** — **已修复** (2026-06-23)
- **描述**:
  非流式路径先写 xadd 再 return。如果 Redis 写入失败，异常传播到 FastAPI 返回 HTTP 500，**即使上游 API 调用已经成功完成**。客户端重试可能导致重复扣费。
- **影响**: 上游成功但客户端收到 500，重试产生重复请求
- **修复**: xadd 包 try/except，失败只记录日志不影响响应

#### 9. 未知模型按最低价格计费

- **位置**: `gateway/pricing.py` L41
- **严重程度**: 🟠 **高危**
- **代码**:
  ```python
  pricing = PRICING.get(model, {"prompt": 1, "completion": 1})
  ```
- **描述**: 如果模型名称不在 `PRICING` 字典中（如新增了 `gpt-4-turbo` 但忘记配置），默认按 `prompt=1元/百万token, completion=1元/百万token` 计费。这可能是实际价格的 **1/10 甚至更低**。
- **影响**: 新模型上线后可能数天/数周内都按低价计费，造成**严重收入损失**
- **根因**: 缺乏"未配置价格的模型拒绝服务"机制

#### 10. 无法进行毛利分析：没有上游成本追踪

- **位置**: `gateway/pricing.py` L38-50
- **严重程度**: 🟠 **高危**（产品设计缺陷）
- **描述**: `calculate_cost()` 返回 `(cost_fen, bill_fen)`，但**两者都是基于本地定价表计算的**。`cost_fen` 并不是从上游 API 返回的实际价格，而只是 `bill_fen` 除以 `MARKUP` 得到的。系统实际上不知道每次请求支付给上游多少钱。
- **影响**:
  - 无法计算每笔交易的毛利率
  - 无法判断哪些模型/用户/时段盈利或亏损
  - 无法做精细化成本控制
- **根因**: 设计时没有引入上游真实成本记录

#### 11. 套餐购买后缓存未清除导致服务拒绝

- **位置**: `admin/consumer.py` L106 + `gateway/middleware/auth.py` L89-90
- **严重程度**: 🟠 **高危**
- **描述**:
  当套餐额度用完时，consumer 设置 `user_has_plans:{user_id}` = `"0"` 缓存 24h。如果用户之后购买了新套餐，而购买套餐的接口没有清除该缓存，用户将在**最多24小时内无法使用 API**（即使有新套餐）。
- **影响**: 付费用户在充值后无法使用服务，造成客户投诉

#### 12. nginx：HTTP 端口直接代理内容，无 HTTPS 重定向

- **位置**: `nginx/nginx.conf`
- **严重程度**: 🟠 **高危** — **已修复** (2026-06-23)
- **描述**:
  commit `3542fff`（6月18日 DeepSeek passthrough）误改 nginx 配置：
  - HTTP(80) 删除了 301 重定向，改为直接代理前端页面
  - `ssl_protocols TLSv1.3;` 仅支持 TLS 1.3
  - HSTS 带了 `preload` 标记
- **影响**: 浏览器对 HTTP 页面显示"网页存在安全风险"，部分客户端因 TLS 1.3 only 无法连接
- **根因**: 将生产配置误改为 "dev mode" 并部署
- **修复**: HTTP 301 重定向到 HTTPS、TLSv1.2 + TLSv1.3、移除 preload

---

### 🟡 中等 (Medium)

#### 13. Streaming 场景 Token 计数可能丢失

- **位置**:
  - DeepSeek 直连: `gateway/routes.py` L188-198
  - OpenAI streaming: `gateway/adapters/openai.py` L101-103
  - Anthropic streaming: `gateway/adapters/anthropic.py` L96-98
- **严重程度**: 🟡 **中等**
- **描述**:
  | 适配器 | Token 来源 | 风险 |
  |--------|-----------|------|
  | DeepSeek 直连 | `message_start` → prompt_tokens；`message_delta` → completion_tokens | 如 `message_delta` 因网络中断未到达，completion_tokens 为 0 |
  | OpenAI | 最后一个 chunk 中的 `usage` 字段 | 如果 stream 提前中断，usage 字段未到达 |
  | Anthropic | `message_delta` 事件 | 同样依赖最后一个事件到达 |
- **影响**: 部分成功请求的 token 用量被记录为 0，用户**免费使用了服务**
- **缓解**: `routes.py` 中 `if prompt_tokens or completion_tokens:` 判断，全零则 cost=0，不会误收费但会漏收

#### 14. 前端用量页：自定义日期范围统计不准确

- **位置**: `frontend/src/pages/Usage.vue` L159-161
- **严重程度**: 🟡 **中等**
- **描述**:
  `activeRange === 'custom'` 时硬编码 `days = 30`，始终显示近 30 天数据，与用户选择的自定义日期范围无关。
- **影响**: 用户无法查看任意日期范围的准确统计

#### 15. 前端用量页：错误率永远显示 0%

- **位置**: `frontend/src/pages/Usage.vue` L166
- **严重程度**: 🟡 **中等**
- **描述**:
  `/trend` API 不返回 `errors` 字段，`d.errors` 始终 `undefined` → `0`。错误率统计永远为 `0.0%`，即使有失败请求。
- **影响**: 错误监控完全失效

#### 16. Redis pricing_config 缺乏输入校验

- **位置**: `gateway/pricing.py` L24-28
- **严重程度**: 🟡 **中等**
- **描述**:
  ```python
  cfg = json.loads(data)
  PRICING = cfg.get("models", _DEFAULT_PRICING)
  MARKUP = cfg.get("markup", _DEFAULT_MARKUP)
  ```
  从 Redis 读取的定价配置直接信任并使用。如果管理员设置了负数价格或超大数值，会导致计费异常。
- **影响**: 价格异常可能导致严重财务损失

---

### 🟢 低风险 (Low)

#### 17. 部分报告接口未过滤 error 记录计费

- **位置**: `admin/routes/reports.py` L204 (`admin-daily` 接口)
- **严重程度**: 🟢 **低**
- **描述**: `func.coalesce(func.sum(UsageLog.bill_cost), 0)` 没有 `.filter(UsageLog.status == "success")`。不过 error 记录的 `bill_cost` 网关中已设置为 0，实际影响很小。

#### 18. 套餐没有模型维度限制

- **位置**: `admin/models/plan.py` L13-24
- **严重程度**: 🟢 **低**（设计决策）
- **描述**: `Plan.token_quota` 是全局配额。如果业务需要"GPT-4专用套餐"或"DeepSeek专用套餐"，当前模型无法支持。扣款时按 `expires_at` 升序消耗，不匹配模型。

#### 19. 时序攻击防护无效

- **位置**: `gateway/middleware/auth.py` L25-26, L37-38
- **严重程度**: 🟢 **低**
- **描述**: 代码试图通过 `asyncio.sleep(0.015 - elapsed)` 固定认证时间防时序攻击。但第一次 sleep 在 Redis 查询之前，第二次无法掩盖 DB 回查耗时（>100ms）。鉴于本项目是 LLM API 中转平台而非密码认证系统，实际风险极低。**建议删除此段代码**（无效且增加延迟）。

- **位置**: `gateway/middleware/auth.py` L25-26, L37-38
- **严重程度**: 🟢 **低**
- **描述**: 代码试图固定认证时间为 15ms 来防时序攻击，但第一次 sleep 在 Redis 查询**之前**执行（此时还不知道查询耗时），第二次 sleep 也难以掩盖回查数据库的额外时间（可能 >100ms）。

---

## 四、统计准确性评估汇总

| 指标 | 准确性 | 说明 |
|------|--------|------|
| 请求次数统计 | ✅ **准确** | `COUNT(*)` 按 `request_id` 去重 |
| Token 用量统计（非流式） | ✅ **准确** | 从上游 API 响应中直接获取 |
| Token 用量统计（流式） | ⚠️ **偶有丢失** | 网络中断时最后 chunk 未到达则记为 0 |
| 计费金额统计 | ⚠️ **有偏差** | 未知模型按最低价；部分扣款与 bill_cost 不一致 |
| 余额扣款 | ✅ **已修复双重扣款风险** | `inserted == 0` guard 已添加。`FOR UPDATE` 行锁防止超扣，但余额不足时仍会赊账 |
| 套餐扣款 | ⚠️ **基本准确** | FOR UPDATE 防并发，但缓存可能导致服务被拒 |
| 毛利分析 | 🔴 **完全无法做** | 没有上游真实成本追踪 |
| 日志完整性 | ⚠️ **xadd 失败有丢失风险** | 已修复（try/except 保护），但极端情况下仍可能丢失少量记录 |
| 今日消费统计 | ⚠️ **基本准确** | 基于 DB 聚合，但 DB 与 Redis 可能有短暂延迟 |
| 趋势报表 | ✅ **准确** | 基于 DB 数据直接聚合 |
| 管理端 `/user-daily` | ✅ **已修复** | `parse_date_end` NameError 崩溃已修复 |

---

## 五、修复状态与优先级建议

### ✅ 已修复（2026-06-23）

| 编号 | 问题 | 修复内容 |
|------|------|---------|
| 1 | 批处理双重扣款 | `inserted == 0` guard 跳过重复消息的扣款 |
| 2 | DLQ 死代码 | DLQ 逻辑移到 `batch_insert` 的异常处理块 |
| 3 | DeepSeek xadd 日志丢失 | try/except 保护 xadd 写入 |
| 4 | `/user-daily` NameError 崩溃 | `parse_date_end` 提取为模块级函数 |
| 7 | xadd 失败覆盖成功日志 | try/except 保护，失败只记录日志 |
| 8 | 非流式 xadd 失败返回 500 | try/except 保护，不中断响应 |
| 12 | nginx HTTP→HTTPS 安全修复 | 301 重定向 + TLSv1.2 + 移除 HSTS preload |

### 🔴 P0 — 待修复

| 编号 | 问题 | 建议修复方案 |
|------|------|-------------|
| 5 | 并发余额透支 / 余额不足仍提供服务 | 在 consumer 中增加余额不足时的拒绝处理，记录 `insufficient_balance` 状态；或引入实时余额检查机制 |
| 6 | 部分扣款数据不一致 | 在 `usage_logs` 中增加 `actual_deduction` 字段，记录真实扣款金额；或余额不足时拒绝请求 |

### 🟠 P1 — 尽快修复

| 编号 | 问题 | 建议修复方案 |
|------|------|-------------|
| 9 | 未知模型低价计费 | 在 `calculate_cost` 中增加：如果模型不在 PRICING 中，返回错误而非默认价格 |
| 10 | 无法毛利分析 | 数据库增加 `upstream_cost` 字段，记录真实上游成本 |
| 11 | 缓存未清除 | 在充值/购买套餐接口中，清除 `user_has_plans:{user_id}` 和 `user_balance:{user_id}` 的 Redis 缓存 |
| 14 | 前端日期统计不准确 | 自定义日期范围时用实际 `date_from/date_to` 请求 API，而非硬编码 30 天 |
| 15 | 前端错误率永远 0% | `/trend` API 增加 `errors` 字段返回 |

### 🟡 P2 — 中期修复

| 编号 | 问题 | 建议修复方案 |
|------|------|-------------|
| 13 | Streaming token 丢失 | 增加超时/中断保护；当 stream 异常结束时使用上游提供的 token（如果有）或估算值 |
| 16 | pricing_config 无校验 | 加载时校验价格和 markup 为正数且在合理范围内 |
| 10 | 无法毛利分析 | 引入上游成本追踪，分离 cost（实际成本）和 bill_cost（售价） |

### 🟢 P3 — 优化

| 编号 | 问题 | 建议修复方案 |
|------|------|-------------|
| 17 | 报告接口过滤 | 在 `admin-daily` 的 cost 聚合中增加 `status == "success"` 过滤 |
| 18 | 套餐模型维度 | 在设计层面决定是否需要，如需则增加 `model` 字段 |
| 19 | 时序攻击 | 移除无意义的 sleep 代码（无效且增加延迟） |

---

## 六、现有防护措施评价

| 措施 | 评价 |
|------|------|
| `ON CONFLICT (request_id) DO NOTHING` | ✅ 防止重复入库，已适配（`inserted == 0` guard） |
| `FOR UPDATE` 行锁 | ✅ 正确防止并发扣款冲突 |
| 批量事务（`engine.begin()`） | ✅ insert + 扣款在同一事务中，保证原子性 |
| 死信队列 (DLQ) | ✅ 已修复路由逻辑，异常消息最终进入 DLQ |
| 审计 SQL 脚本 | ✅ `scripts/audit_usage_logs.sql` 覆盖完整性检查 |
| 自动化测试脚本 | ✅ `scripts/test_usage_accuracy.py` 21 个用例覆盖全链路 |
| Redis 缓存加速 | ⚠️ 缓存未随 DB 变更及时失效 |
| 余额准入检查 | ⚠️ 与异步扣款之间的竞态条件未处理 |

---

*审计完成。以上问题建议按优先级逐步修复。*
