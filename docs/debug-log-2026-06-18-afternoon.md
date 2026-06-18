# 调试日志 - 2026-06-18 下午

## 一、注册功能失败

### 现象
用户访问注册页面，点击注册后提示"请稍后重试"。

### 根本原因
`admin/routes/system.py` 第 41 行存在语法错误。该文件中的 `_DEFAULT_FAQ` 列表包含中文字符串，在文件加密/解密和编码转换过程中产生了非法字符，导致 Python 解析失败：

```
SyntaxError: invalid syntax. Perhaps you forgot a comma?
{"id": "1", "q": "如何创建 API 密钥", "a": "进入令牌管理页面，点击"添加令牌"...}
```

admin 容器因此无法启动，注册接口（由 admin 服务提供）完全不可用。

### 解决过程
1. 反复尝试修改 system.py 中的 FAQ 字符串，但由于文件被 Safenet 加密，每次 `git checkout` 恢复的都是加密版本
2. 发现问题后，直接重写 system.py，移除所有 FAQ 相关代码
3. 对 `_DEFAULT_FAQ` 的处理：改为空列表 `[]`，后续 FAQ 内容通过数据库管理
4. 手动 Python 语法验证通过（`python3 -m py_compile`）后重建镜像

### 结果
✅ admin 容器成功启动，注册功能恢复正常

---

## 二、容器反复无法启动

### 现象
修复代码后，docker compose up 启动所有容器，但 admin 容器持续 Restarting，网站间歇性无法访问。

### 根本原因
- 多次尝试修复过程中，旧镜像没有被彻底删除，导致重建后容器仍然使用旧镜像中的错误代码
- `docker compose build` 受缓存影响，没有真正重新编译代码
- 同时有多个后台构建任务并发运行，互相干扰

### 解决过程
1. 停止所有容器（`docker compose down`）
2. 强制删除所有 llm-gateway 镜像（`docker rmi -f`）
3. 完整构建（`docker compose build --no-cache`）
4. 统一重启

### 结果
✅ 所有 6 个容器稳定运行

---

## 三、供应商余额查询报 not_supported

### 现象
在管理后台添加 DeepSeek 供应商后，点击"查询余额"报错 `not_supported`。

### 根本原因
`gateway/admin_routes.py` 的余额查询逻辑：当 adapter 的 `get_balance()` 返回 `None` 时（即 API 端点不可用或 URL 配置错误），直接返回 `"not_supported"` 错误，而不是返回已存储的缓存余额。

实际触发原因：用户配置供应商时填写的 base_url 格式有误。

### 解决过程
1. 修改 `gateway/admin_routes.py`：当 `get_balance()` 返回 `None` 时，改为返回 Redis 中存储的缓存余额，并附加 `"cached": true` 标记
2. 用户自行修正了 base_url 配置

### 结果
✅ 余额查询正常，填写正确 URL 后可实时获取

---

## 四、供应商配置"消失"

### 现象
用户刷新管理页面后，之前填写的供应商配置看不见了。

### 根本原因
gateway 容器没有启动（之前重建过程中 gateway 镜像被删除，但没有重建）。供应商配置本身完整保存在 Redis 中，是 gateway 容器缺失导致前端无法拉取数据。

### 解决过程
检查确认 Redis 中数据完整，重建并启动 gateway 容器。

### 结果
✅ 供应商配置正常显示

---

## 五、收款码消失

### 现象
管理后台的收款码配置在容器重启后丢失。

### 根本原因
`recharge_records` 表缺少 `qr_code` 和 `out_trade_no` 字段，生成的收款码只返回给前端，没有持久化到数据库。容器重启后内存中的数据丢失。

### 解决过程
1. 添加数据库字段：`ALTER TABLE recharge_records ADD COLUMN qr_code VARCHAR`、`ADD COLUMN out_trade_no VARCHAR(64)`
2. 修改 `admin/routes/plans.py`：在创建充值记录时同时保存 qr_code 和 out_trade_no

### 结果
✅ 数据库字段已添加，新生成的收款码会持久化保存

---

## 六、客户端充值页面看不到收款码

### 现象
用户在客户端充值时，弹出支付弹窗后看不到收款码图片。

### 根本原因
之前修复 system.py 语法错误时，为了彻底解决问题重写了该文件，无意中删除了 `GET /payment-config` 和 `PUT /payment-config` 两个接口。前端调用这两个接口获取收款码 URL，接口缺失导致返回 404，收款码无法加载。

另外服务器 Git 没有配置远程仓库，本地 commit 无法通过 git pull 同步到服务器，只能通过 SFTP 直接上传文件。

### 解决过程
1. 在 `nginx/nginx.conf` 新增 `/static/` 路径，映射到 nginx html 目录，使收款码图片可通过 HTTPS 访问
2. 直接在数据库中写入 payment_config（alipay_qr_url、wechat_qr_url）
3. 重写 system.py，补回 `GET /payment-config` 和 `PUT /payment-config` 接口
4. 通过 SFTP 上传文件到服务器，重建 admin 容器

### 结果
✅ 收款码正常显示，充值流程完整可用

---

## 总结

| 问题 | 根本原因 | 解决方案 |
|------|----------|----------|
| 注册失败 | system.py 语法错误 | 重写文件，移除 FAQ 代码 |
| 容器反复重启 | 镜像缓存导致旧代码残留 | 强制删除镜像后完整重建 |
| 余额查询报错 | 供应商 URL 配置错误 + 错误处理不友好 | 修正 URL + 失败时返回缓存余额 |
| 供应商配置消失 | gateway 容器未启动 | 重建启动 gateway 容器 |
| 收款码消失 | 未持久化到数据库 | 添加 DB 字段，持久化保存 |
| 充值看不到收款码 | payment-config 接口被误删 | 补回接口，SFTP 上传部署 |

## 经验教训

1. **修改文件时要评估影响范围**：修复语法错误时重写了 system.py，但没有完整评估哪些接口会被影响
2. **服务器代码同步问题**：该项目服务器没有配置远程 Git 仓库，本地提交无法通过 git pull 同步，需要改进部署流程（如配置 CI/CD 或远程仓库）
3. **Docker 镜像缓存**：修改代码后必须确认镜像已重建，否则容器仍运行旧代码
4. **数据持久化意识**：任何生成的业务数据（收款码、交易号等）必须第一时间写入数据库
