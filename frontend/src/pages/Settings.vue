<template>
  <div>
    <div class="settings-banner">
      <div style="display:flex;align-items:center;gap:16px">
        <div class="avatar-circle" style="width:52px;height:52px;font-size:22px;background:rgba(255,255,255,0.2);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700">{{ avatarChar }}</div>
        <div>
          <div style="font-size:18px;font-weight:700;color:#fff">{{ userName }}</div>
          <div style="display:flex;gap:10px;margin-top:4px">
            <span style="font-size:12px;color:rgba(255,255,255,0.7)">普通用户</span>
            <span style="font-size:12px;color:rgba(255,255,255,0.5)">ID: {{ userId }}</span>
            <span class="badge" style="background:rgba(255,255,255,0.15);color:#fca5a5;font-size:10px">余额 &yen;{{ balance }}</span>
          </div>
        </div>
      </div>
      <div style="display:flex;gap:32px">
        <div><div style="font-size:10px;color:rgba(255,255,255,0.5);text-transform:uppercase">历史消耗</div><div style="font-size:18px;font-weight:700;color:#fff">&yen;{{ totalCost }}</div></div>
        <div><div style="font-size:10px;color:rgba(255,255,255,0.5);text-transform:uppercase">请求次数</div><div style="font-size:18px;font-weight:700;color:#fff">{{ totalCalls }}</div></div>
        <div><div style="font-size:10px;color:rgba(255,255,255,0.5);text-transform:uppercase">用户分组</div><div style="font-size:18px;font-weight:700;color:#fff">default</div></div>
      </div>
    </div>

    <div class="settings-grid">
      <!-- Card 1: Account -->
      <div class="card">
        <div class="tabs" style="margin:0;padding:0 20px">
          <button :class="'tab ' + (acctTab === 'bind' ? 'active' : '')" @click="acctTab = 'bind'">账户绑定</button>
          <button :class="'tab ' + (acctTab === 'security' ? 'active' : '')" @click="acctTab = 'security'">安全设置</button>
        </div>
        <div class="card-padded" v-if="acctTab === 'bind'">
          <h3 class="section-title mb-16">多渠道账号绑定</h3>
          <div class="bind-list">
            <div class="bind-item done"><span class="bind-icon">&#x2709;</span><div class="bind-info"><div class="bind-name">邮箱</div><div class="bind-detail">{{ userEmail }} <span style="color:var(--success)">已绑定</span></div></div><span class="text-muted" style="font-size:12px">支持修改</span></div>
            <div class="bind-item"><span class="bind-icon">&#x1F419;</span><div class="bind-info"><div class="bind-name">GitHub</div><div class="bind-detail">待绑定</div></div><button class="btn btn-outline btn-xs">绑定</button></div>
            <div class="bind-item"><span class="bind-icon">&#x1F9D1;</span><div class="bind-info"><div class="bind-name">LinuxDO</div><div class="bind-detail">待绑定</div></div><button class="btn btn-outline btn-xs">绑定</button></div>
            <div class="bind-item disabled"><span class="bind-icon">&#x1F4F1;</span><div class="bind-info"><div class="bind-name">微信</div><div class="bind-detail">未启用</div></div></div>
            <div class="bind-item disabled"><span class="bind-icon">&#x1F3AE;</span><div class="bind-info"><div class="bind-name">Discord</div><div class="bind-detail">未启用</div></div></div>
          </div>
        </div>
        <div class="card-padded" v-else>
          <h3 class="section-title mb-16">修改密码</h3>
          <div class="form-group"><label class="form-label">旧密码</label><input v-model="oldPw" type="password" class="form-input" placeholder="输入当前密码" style="max-width:320px" /></div>
          <div class="form-group"><label class="form-label">新密码</label><input v-model="newPw" type="password" class="form-input" placeholder="至少8位，含大小写字母和数字" style="max-width:320px" /><p class="form-hint">至少 8 位，需包含大写字母、小写字母和数字</p></div>
          <div class="form-group"><label class="form-label">确认密码</label><input v-model="confirmPw" type="password" class="form-input" placeholder="再次输入新密码" style="max-width:320px" /></div>
          <div v-if="pwError" class="alert alert-error">{{ pwError }}</div>
          <div v-if="pwSuccess" class="alert alert-success">{{ pwSuccess }}</div>
          <button class="btn btn-primary btn-sm" @click="changePw" :disabled="pwLoading">{{ pwLoading ? '保存中...' : '保存' }}</button>
        </div>
      </div>

      <!-- Card 2: Notification Settings -->
      <div class="card">
        <div class="tabs" style="margin:0;padding:0 20px">
          <button :class="'tab ' + (otherTab === 'notify' ? 'active' : '')" @click="otherTab = 'notify'">通知</button>
          <button :class="'tab ' + (otherTab === 'price' ? 'active' : '')" @click="otherTab = 'price'">价格</button>
          <button :class="'tab ' + (otherTab === 'privacy' ? 'active' : '')" @click="otherTab = 'privacy'">隐私</button>
          <button :class="'tab ' + (otherTab === 'sidebar' ? 'active' : '')" @click="otherTab = 'sidebar'">边栏</button>
        </div>
        <div class="card-padded" v-if="otherTab === 'notify'">
          <h3 class="section-title mb-16">通知配置</h3>
          <div class="form-group"><label class="form-label">通知方式</label><div style="display:flex;gap:12px"><label class="filter-option"><input type="radio" v-model="notifyMethod" value="email" /> 邮件</label><label class="filter-option"><input type="radio" v-model="notifyMethod" value="webhook" /> Webhook</label><label class="filter-option"><input type="radio" v-model="notifyMethod" value="bark" /> Bark</label><label class="filter-option"><input type="radio" v-model="notifyMethod" value="gotify" /> Gotify</label></div></div>
          <div class="form-group"><label class="form-label">额度预警阈值</label><div style="display:flex;align-items:center;gap:8px"><span>等价 &yen;</span><input v-model="alertThreshold" class="form-input" style="width:120px" /><span class="text-muted">余额低于阈值时触发提醒</span></div></div>
          <div class="form-group"><label class="form-label">通知邮箱</label><input class="form-input" placeholder="留空复用绑定邮箱" style="max-width:280px" /></div>
          <div v-if="settingsMsg" :class="settingsMsg.includes('失败') ? 'alert alert-error' : 'alert alert-success'" style="font-size:12px">{{ settingsMsg }}</div>
          <button class="btn btn-primary btn-sm" @click="saveSettings" :disabled="savingSettings">{{ savingSettings ? '保存中...' : '保存设置' }}</button>
        </div>
        <div class="card-padded" v-else><div class="empty-state" style="padding:24px"><div class="empty-state-text">功能开发中</div></div></div>
      </div>

      <!-- Card 3: Preferences -->
      <div class="card card-padded">
        <h3 class="section-title mb-16">偏好设置</h3>
        <div class="form-group"><label class="form-label">语言偏好</label><select class="form-select" style="max-width:200px"><option>简体中文</option><option>English</option></select><p class="form-hint">语言设置将同步到所有设备</p></div>
        <div class="form-group"><label class="form-label">价格显示</label><select class="form-select" style="max-width:200px"><option>人民币 (&yen;)</option><option>美元 ($)</option></select></div>
      </div>

      <!-- Card 4: About -->
      <div class="card card-padded">
        <h3 class="section-title mb-16">关于</h3>
        <div class="text-secondary" style="font-size:13px;line-height:2">
          <div>平台版本：{{ platformVersion }}</div>
          <div>注册时间：{{ registeredAt }}</div>
          <div>上次登录：{{ lastLoginAt }}</div>
        </div>
      </div>
    </div>

    <div class="text-center" style="padding:16px 0;color:var(--text-muted);font-size:12px">&copy;2026 EasyCode 版权所有</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

const userName = ref(''); const userEmail = ref(''); const userId = ref('')
const balance = ref('0.00'); const totalCost = ref('0.00'); const totalCalls = ref(0)
const acctTab = ref('bind'); const otherTab = ref('notify')
const notifyMethod = ref('email'); const alertThreshold = ref(500000)
const oldPw = ref(''); const newPw = ref(''); const confirmPw = ref('')
const pwError = ref(''); const pwSuccess = ref(''); const pwLoading = ref(false)
const platformVersion = ref('v1.0.0'); const registeredAt = ref('-'); const lastLoginAt = ref('-')
const savingSettings = ref(false); const settingsMsg = ref('')
const avatarChar = computed(() => userName.value ? userName.value.charAt(0).toUpperCase() : '?')

async function changePw() {
  pwError.value = ''; pwSuccess.value = ''
  if (!oldPw.value || !newPw.value || !confirmPw.value) { pwError.value = '请填写所有密码字段'; return }
  if (newPw.value !== confirmPw.value) { pwError.value = '两次输入的新密码不一致'; return }
  if (newPw.value.length < 8) { pwError.value = '密码至少 8 位'; return }
  if (!/[A-Z]/.test(newPw.value)) { pwError.value = '密码需包含大写字母'; return }
  if (!/[a-z]/.test(newPw.value)) { pwError.value = '密码需包含小写字母'; return }
  if (!/[0-9]/.test(newPw.value)) { pwError.value = '密码需包含数字'; return }
  pwLoading.value = true
  try {
    await api.changePassword(oldPw.value, newPw.value)
    pwSuccess.value = '密码修改成功'; oldPw.value = ''; newPw.value = ''; confirmPw.value = ''
  } catch (e) { pwError.value = e.message || '修改失败' } finally { pwLoading.value = false }
}

async function saveSettings() {
  savingSettings.value = true; settingsMsg.value = ''
  try {
    await api.saveSettings({ notifyMethod: notifyMethod.value, alertThreshold: alertThreshold.value })
    settingsMsg.value = '设置已保存'; setTimeout(() => { settingsMsg.value = '' }, 3000)
  } catch (e) { settingsMsg.value = '保存失败: ' + (e.message || '错误') } finally { savingSettings.value = false }
}

onMounted(async () => {
  try {
    const user = await api.getMe()
    userName.value = user.username || ''; userEmail.value = user.email || ''
    userId.value = user.id ? user.id.slice(0, 8) : '-'
    balance.value = ((user.balance || 0) / 100).toFixed(2)
    registeredAt.value = user.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '-'
    lastLoginAt.value = user.last_login_at ? new Date(user.last_login_at).toLocaleString('zh-CN') : '-'
  } catch (e) { /* */ }
  try { const d = await api.getDashboard(); totalCalls.value = d.today_calls || 0; totalCost.value = d.today_cost_yuan || '0.00' } catch (e) { /* */ }
  try { const s = await api.getSettings(); if (s.settings.notifyMethod) notifyMethod.value = s.settings.notifyMethod; if (s.settings.alertThreshold) alertThreshold.value = s.settings.alertThreshold } catch (e) { /* */ }
})
</script>

<style scoped>
.settings-banner { background: linear-gradient(135deg, #6366f1, #4f46e5); padding: 28px 32px; border-radius: var(--radius-lg); display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 20px; }
.settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.bind-list { display: flex; flex-direction: column; gap: 4px; }
.bind-item { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: var(--radius-sm); border: 1px solid transparent; }
.bind-item:not(.disabled):hover { background: #f5f5f5; }
.bind-item.disabled { opacity: 0.4; }
.bind-icon { font-size: 20px; width: 32px; text-align: center; }
.bind-info { flex: 1; }
.bind-name { font-size: 13px; font-weight: 500; }
.bind-detail { font-size: 11px; color: var(--text-muted); margin-top: 1px; }
.bind-item.done .bind-name { color: var(--text); }
</style>
