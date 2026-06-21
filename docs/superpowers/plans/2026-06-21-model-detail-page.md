# Model Detail Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/models/:id` detail page showing model pricing, code examples, and metadata, and wire up card clicks on the Models page to navigate to it.

**Architecture:** New `ModelDetail.vue` page under `frontend/src/pages/`. Data comes from `gatewayApi.listModelCatalog()` — find the model by ID client-side (no new API endpoint needed). Route added as a child of the UserLayout at `models/:id`. Models.vue cards get `@click` restored.

**Tech Stack:** Vue 3.5 (Composition API), Naive UI 2.44.1, existing `gatewayApi.js`, CSS variables from `base.css`.

---

## How to verify

```bash
cd D:/code/llm-gateway/frontend
npm run dev
# navigate to http://localhost:5173/models, click any card
# should land on http://localhost:5173/models/deepseek-v4-flash (or similar)
```

No automated tests — verification is manual in browser.

---

### Task 1: Create ModelDetail.vue + add route

**Files:**
- Create: `frontend/src/pages/ModelDetail.vue`
- Modify: `frontend/src/router.js` (add child route at line 49)

- [ ] **Step 1: Add the route to `router.js`**

In `frontend/src/router.js`, find the user portal children array. Currently line 49 has `{ path: 'models', component: Models }`. Add the detail route immediately after it:

```js
// at the top, add import:
import ModelDetail from './pages/ModelDetail.vue'

// in children array, after { path: 'models', component: Models }:
{ path: 'models/:id', component: ModelDetail },
```

The full children block after the change:
```js
children: [
  { path: '', component: Dashboard },
  { path: 'keys', component: Keys },
  { path: 'plans', component: Plans },
  { path: 'usage', component: Usage },
  { path: 'playground', component: Playground },
  { path: 'settings', component: Settings },
  { path: 'models', component: Models },
  { path: 'models/:id', component: ModelDetail },
],
```

- [ ] **Step 2: Create `frontend/src/pages/ModelDetail.vue`**

```vue
<template>
  <div>
    <!-- Back link -->
    <div style="margin-bottom:20px">
      <a @click.prevent="$router.push('/models')" class="back-link">← 返回模型广场</a>
    </div>

    <div v-if="model">
      <!-- Header -->
      <div class="detail-header">
        <div :class="['detail-icon', 'icon-' + colorKey(model.provider)]">
          {{ providerInitial(model.provider) }}
        </div>
        <div>
          <h1 class="detail-title">{{ displayName(model.id) }}</h1>
          <div class="detail-meta">
            <span class="detail-provider">{{ model.provider }}</span>
            <span v-for="tg in splitTags(model.tags)" :key="tg" class="mtag">{{ tg }}</span>
          </div>
        </div>
      </div>

      <p v-if="model.description" class="detail-desc">{{ model.description }}</p>

      <!-- Two-column layout -->
      <div class="detail-grid">
        <!-- Left: Pricing -->
        <div class="detail-card">
          <div class="detail-card-title">价格</div>
          <div v-if="model.per_use > 0" class="price-block price-block--amber">
            <div class="price-label">按次计费</div>
            <div class="price-value">¥{{ model.per_use_fmt }}<span class="price-unit"> / 次</span></div>
          </div>
          <template v-else>
            <div class="price-block">
              <div class="price-label">输入 (Prompt)</div>
              <div class="price-value">¥{{ model.input_fmt }}<span class="price-unit"> / 1M tokens</span></div>
            </div>
            <div class="price-block">
              <div class="price-label">输出 (Completion)</div>
              <div class="price-value">¥{{ model.output_fmt }}<span class="price-unit"> / 1M tokens</span></div>
            </div>
            <div v-if="model.cache_price > 0" class="price-block price-block--green">
              <div class="price-label">缓存读取 (Cache Read)</div>
              <div class="price-value">¥{{ model.cache_fmt }}<span class="price-unit"> / 1M tokens</span></div>
            </div>
          </template>
        </div>

        <!-- Right: Model ID + limits -->
        <div class="detail-card">
          <div class="detail-card-title">模型信息</div>
          <div class="info-row">
            <span class="info-label">Model ID</span>
            <div class="info-value-row">
              <code class="model-id-code">{{ model.id }}</code>
              <button class="copy-btn" @click="copyId(model.id)">复制</button>
            </div>
          </div>
          <div class="info-row">
            <span class="info-label">供应商</span>
            <span class="info-value">{{ PROVIDER_LABELS[model.provider] || model.provider }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">计费方式</span>
            <span class="info-value">{{ model.per_use > 0 ? '按次计费' : '按 Token 计费' }}</span>
          </div>
          <div v-if="model.tags" class="info-row">
            <span class="info-label">标签</span>
            <span class="info-value">{{ model.tags }}</span>
          </div>
        </div>
      </div>

      <!-- Code examples -->
      <div class="detail-card" style="margin-top:16px">
        <div class="detail-card-title">调用示例</div>
        <div class="code-tabs">
          <button v-for="tab in CODE_TABS" :key="tab.key"
            :class="['code-tab-btn', activeTab === tab.key && 'active']"
            @click="activeTab = tab.key">{{ tab.label }}</button>
        </div>
        <div style="position:relative">
          <button class="copy-btn copy-btn--abs" @click="copyCode">复制代码</button>
          <pre class="code-block">{{ codeExample }}</pre>
        </div>
      </div>
    </div>

    <!-- Not found -->
    <div v-else-if="loaded" class="not-found">
      <div style="font-size:48px;margin-bottom:12px">🔍</div>
      <div style="font-size:16px;font-weight:600;margin-bottom:8px">找不到模型 "{{ $route.params.id }}"</div>
      <a @click.prevent="$router.push('/models')" class="back-link">← 返回模型广场</a>
    </div>

    <!-- Loading -->
    <div v-else class="not-found" style="color:var(--text-muted)">加载中...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { gatewayApi } from '../gatewayApi'

const route = useRoute()
const message = useMessage()

const model = ref(null)
const loaded = ref(false)
const activeTab = ref('curl')

const CODE_TABS = [
  { key: 'curl', label: 'cURL' },
  { key: 'python', label: 'Python' },
  { key: 'node', label: 'Node.js' },
]

const PROVIDER_LABELS = {
  anthropic: 'Anthropic', openai: 'OpenAI', deepseek: 'DeepSeek',
  google: 'Google', mistral: 'Mistral',
}
const DISPLAY_NAMES = {
  'deepseek-v4-flash': 'DeepSeek V4 Flash',
  'deepseek-v4-pro': 'DeepSeek V4 Pro',
  'deepseek-r1': 'DeepSeek R1',
  'claude-sonnet-4-5': 'Claude Sonnet 4.5',
  'claude-opus-4-5': 'Claude Opus 4.5',
  'gpt-4o': 'GPT-4o',
  'gpt-4o-mini': 'GPT-4o Mini',
  'gemini-1.5-pro': 'Gemini 1.5 Pro',
}
const COLOR_KEYS = {
  anthropic: 'purple', openai: 'mint', deepseek: 'blue',
  google: 'yellow', mistral: 'orange',
}

function displayName(id) {
  return DISPLAY_NAMES[id] || id.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
}
function colorKey(provider) { return COLOR_KEYS[provider] || 'pink' }
function providerInitial(provider) { return (PROVIDER_LABELS[provider] || provider).charAt(0).toUpperCase() }
function splitTags(tags) { return (tags || '').split(',').map(t => t.trim()).filter(Boolean) }

const codeExample = computed(() => {
  const id = model.value?.id || 'deepseek-v4-flash'
  if (activeTab.value === 'curl') {
    return `curl -X POST https://easycode.uno/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -d '{
    "model": "${id}",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'`
  }
  if (activeTab.value === 'python') {
    return `from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://easycode.uno/v1"
)

response = client.chat.completions.create(
    model="${id}",
    messages=[{"role": "user", "content": "你好"}]
)

print(response.choices[0].message.content)`
  }
  return `import OpenAI from 'openai';

const client = new OpenAI({
    apiKey: "YOUR_API_KEY",
    baseURL: "https://easycode.uno/v1"
});

const response = await client.chat.completions.create({
    model: "${id}",
    messages: [{ role: "user", content: "你好" }]
});

console.log(response.choices[0].message.content);`
})

function copyId(id) {
  navigator.clipboard.writeText(id).then(() => message.success('已复制 Model ID'))
}

function copyCode() {
  navigator.clipboard.writeText(codeExample.value).then(() => message.success('已复制代码'))
}

onMounted(async () => {
  try {
    const data = await gatewayApi.listModelCatalog()
    const id = route.params.id
    const found = (data.data || []).find(m => m.model === id)
    if (found) {
      model.value = {
        ...found,
        id: found.model,
        input_fmt: (found.input_price || 0).toFixed(2),
        output_fmt: (found.output_price || 0).toFixed(2),
        cache_fmt: (found.cache_price || 0).toFixed(2),
        per_use_fmt: (found.per_use || 0).toFixed(2),
        per_use: found.per_use || 0,
        cache_price: found.cache_price || 0,
      }
    }
  } catch (e) {
    console.error('loadModel failed', e)
  } finally {
    loaded.value = true
  }
})
</script>

<style scoped>
.back-link {
  font-size: 13px; color: var(--primary); cursor: pointer; text-decoration: none;
}
.back-link:hover { text-decoration: underline; }

.detail-header {
  display: flex; align-items: center; gap: 16px; margin-bottom: 16px;
}
.detail-icon {
  width: 56px; height: 56px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 700; color: #fff; flex-shrink: 0;
}
.icon-purple { background: linear-gradient(135deg,#7c3aed,#4f46e5); }
.icon-mint   { background: linear-gradient(135deg,#059669,#0891b2); }
.icon-blue   { background: linear-gradient(135deg,#2563eb,#4f46e5); }
.icon-yellow { background: linear-gradient(135deg,#d97706,#dc2626); }
.icon-orange { background: linear-gradient(135deg,#ea580c,#d97706); }
.icon-pink   { background: linear-gradient(135deg,#db2777,#7c3aed); }

.detail-title { font-size: 22px; font-weight: 700; margin: 0 0 6px; }
.detail-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.detail-provider { font-size: 13px; color: var(--text-secondary); }
.mtag {
  font-size: 11px; padding: 2px 8px; border-radius: 10px;
  background: var(--primary-light); color: var(--primary);
}
.detail-desc {
  font-size: 14px; color: var(--text-secondary); line-height: 1.6;
  margin: 0 0 20px; max-width: 680px;
}

.detail-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 0;
}
@media (max-width: 700px) { .detail-grid { grid-template-columns: 1fr; } }

.detail-card {
  background: var(--surface); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 20px;
}
.detail-card-title {
  font-size: 13px; font-weight: 600; color: var(--text);
  margin-bottom: 16px; padding-bottom: 10px;
  border-bottom: 1px solid var(--border-light);
}

.price-block {
  padding: 12px 14px; border-radius: var(--radius-sm);
  background: #f8fafc; border: 1px solid var(--border-light);
  margin-bottom: 8px;
}
.price-block--amber { background: #fffbeb; border-color: #fde68a; }
.price-block--green { background: #f0fdf4; border-color: #bbf7d0; }
.price-label { font-size: 11px; color: var(--text-secondary); margin-bottom: 4px; }
.price-value { font-size: 20px; font-weight: 700; color: var(--text); }
.price-unit { font-size: 12px; font-weight: 400; color: var(--text-secondary); }

.info-row {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid var(--border-light);
}
.info-row:last-child { border-bottom: none; }
.info-label { font-size: 12px; color: var(--text-secondary); width: 80px; flex-shrink: 0; padding-top: 2px; }
.info-value { font-size: 13px; color: var(--text); }
.info-value-row { display: flex; align-items: center; gap: 8px; flex: 1; }
.model-id-code {
  font-family: var(--font-mono); font-size: 12px;
  background: var(--primary-light); color: var(--primary);
  padding: 2px 8px; border-radius: 4px;
}

.copy-btn {
  font-size: 11px; padding: 3px 10px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text-secondary); cursor: pointer;
}
.copy-btn:hover { border-color: var(--primary); color: var(--primary); }
.copy-btn--abs {
  position: absolute; top: 10px; right: 10px; z-index: 1;
}

.code-tabs { display: flex; gap: 4px; margin-bottom: 12px; }
.code-tab-btn {
  padding: 5px 14px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text-secondary); font-size: 12px; cursor: pointer;
}
.code-tab-btn:hover { border-color: var(--primary); color: var(--primary); }
.code-tab-btn.active { background: var(--primary); border-color: var(--primary); color: #fff; }

.code-block {
  background: #f8fafc; border: 1px solid var(--border-light);
  border-radius: var(--radius-sm); padding: 16px;
  font-family: var(--font-mono); font-size: 12px; line-height: 1.7;
  overflow-x: auto; margin: 0; white-space: pre;
}

.not-found {
  text-align: center; padding: 80px 0;
  color: var(--text-secondary); font-size: 14px;
}
</style>
```

- [ ] **Step 3: Verify**

Navigate to http://localhost:5173/models, click any model card — should redirect to `/models/deepseek-v4-flash` (or whatever model was clicked).

Check on the detail page:
1. Model name, provider icon, tags visible in header
2. Price card shows input/output prices (or per-use price for flat-rate models)
3. Model ID shown with copy button — clicking copies to clipboard
4. Code tabs switch between cURL / Python / Node.js
5. "← 返回模型广场" navigates back to `/models`
6. Visiting `/models/nonexistent-id` shows "找不到模型" message

- [ ] **Step 4: No git commit** (not a git repo)

---

### Task 2: Restore click navigation in Models.vue

**Files:**
- Modify: `frontend/src/pages/Models.vue` (restore `@click` on featured card and model card)

- [ ] **Step 1: Read current Models.vue to find the card divs**

The featured card div is around line 19–23, the model card div is around line 52–57. Both currently have no `@click`.

- [ ] **Step 2: Add `@click` to the featured card**

Find:
```html
          class="featured-card"
        >
```

Replace with:
```html
          class="featured-card"
          style="cursor:pointer"
          @click="$router.push('/models/' + m.id)"
        >
```

- [ ] **Step 3: Add `@click` to the model card**

Find:
```html
        class="model-card"
      >
```

Replace with:
```html
        class="model-card"
        @click="$router.push('/models/' + m.id)"
      >
```

Note: `$router` is available in the template via Vue's global instance — no `useRouter()` import needed in `<script setup>` since we're only using it in the template.

- [ ] **Step 4: Verify**

Navigate to http://localhost:5173/models. Click a featured card and a grid card — both should navigate to `/models/:id`.

- [ ] **Step 5: No git commit** (not a git repo)

---

## Self-Review

**Spec coverage:**
- ✅ 模型价格（input/output/cache/per_use）— Task 1 价格卡片
- ✅ 调用方式（cURL / Python / Node.js 代码示例）— Task 1 代码示例区
- ✅ 模型限制/信息（Model ID, 供应商, 计费方式, 标签）— Task 1 模型信息卡片
- ✅ 点击模型跳转详情 — Task 2

**Placeholder scan:** 无占位符，所有步骤含完整代码。

**Type consistency:** `model.value` 字段 (`id`, `input_fmt`, `output_fmt`, `cache_fmt`, `per_use_fmt`, `per_use`, `cache_price`, `tags`, `description`, `provider`) 在 `onMounted` 中全部定义，template 中全部引用这些字段。`codeExample` computed 引用 `model.value?.id`，在 `model` 为 null 时有 fallback。
