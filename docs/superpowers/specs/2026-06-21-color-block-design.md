# Color-Block 多彩分区块设计

> 在保留现有 TokenHub 布局和数据逻辑的前提下，为不同功能区块分配不同的浅色背景 + 彩色左边框，提高视觉层次感。

## 配色映射

| 语义 | 浅色背景 | 色条/文字 | CSS 变量 |
|------|----------|----------|----------|
| 余额/财务 | `#eef2ff` | `#4f6ef7` | `--card-blue-bg` / `--card-blue-accent` |
| 用量/请求 | `#ecfdf5` | `#34d399` | `--card-green-bg` / `--card-green-accent` |
| Token/统计 | `#faf5ff` | `#a855f7` | `--card-purple-bg` / `--card-purple-accent` |
| 告警/费率 | `#fefce8` | `#f59e0b` | `--card-yellow-bg` / `--card-yellow-accent` |
| 错误/危险 | `#fef2f2` | `#dc2626` | `--card-red-bg` / `--card-red-accent` |
| 模型图表 | `#eef2ff` | `#4f6ef7` | （复用蓝色系） |
| 接入信息 | `#faf5ff` | `#a855f7` | （复用紫色系） |

## 修改方式

每个页面只需要：
1. 给 stat card 容器加一个 class（如 `stat-group--blue`）
2. 每个 stat card 的模板加 `style` 绑定对应的背景色和左边框色
3. 标题文字（`dsc-label` / `sci-label` 等）颜色跟随区块色

## 改动范围

| 文件 | 变更 |
|------|------|
| `frontend/src/styles/base.css` | 新增 10 个 CSS 变量 |
| `frontend/src/pages/Dashboard.vue` | 4 个摘要卡 + 2 个图表卡加颜色 class |
| `frontend/src/pages/Usage.vue` | 4 个统计卡 + 条形图卡片加颜色 |
| `frontend/src/pages/Keys.vue` | 3 个汇总卡 + API 信息卡加颜色 |
| `frontend/src/pages/Models.vue` | 模型卡片保留现有渐变，不修改 |
| `frontend/src/pages/ModelDetail.vue` | 价格信息卡加颜色 |
