<template>
  <div>
    <div class="flex-between mb-24">
      <h1 class="page-title">{{ t('planManagement') }}</h1>
      <button class="btn btn-primary" @click="showForm = !showForm">{{ showForm ? '取消' : '+ 新建套餐' }}</button>
    </div>

    <!-- Create plan form -->
    <div v-if="showForm" class="card card-padded mb-24">
      <h3 class="section-title mb-16">新建套餐</h3>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div class="form-group">
          <label class="form-label">套餐名称</label>
          <input v-model="form.name" class="form-input" placeholder="如：基础版" required />
        </div>
        <div class="form-group">
          <label class="form-label">价格 (元)</label>
          <input v-model.number="form.price_yuan" type="number" step="0.01" min="0.01" class="form-input" placeholder="0.00" />
        </div>
        <div class="form-group">
          <label class="form-label">Token 配额</label>
          <input v-model.number="form.token_quota" type="number" min="1000" class="form-input" placeholder="100000" />
        </div>
        <div class="form-group">
          <label class="form-label">有效期 (天)</label>
          <input v-model.number="form.duration_days" type="number" min="1" class="form-input" placeholder="30" />
        </div>
        <div class="form-group" style="grid-column:1/-1">
          <label class="form-label">描述</label>
          <textarea v-model="form.description" class="form-input" rows="2" placeholder="套餐简介..."></textarea>
        </div>
      </div>
      <div v-if="formError" class="alert alert-error" style="margin-top:8px;display:flex;justify-content:space-between">
        <span>{{ formError }}</span>
        <button class="alert-close" @click="formError = ''">&times;</button>
      </div>
      <button class="btn btn-primary mt-16" :disabled="saving" @click="createPlan">
        {{ saving ? t('creatingPlan') : t('createPlanBtn') }}
      </button>
    </div>

    <!-- Plan list -->
    <div class="card">
      <div class="table-wrap" style="border:none">
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('planName') }}</th>
              <th>{{ t('tokenQuotaLabel') }}</th>
              <th>{{ t('priceYuan') }}</th>
              <th>{{ t('validityDays') }}</th>
              <th>{{ t('status') }}</th>
              <th>{{ t('description') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="plans.length === 0">
              <td colspan="6">
                <div class="empty-state" style="padding:40px">
                  <div class="empty-state-icon">&#x1F4E6;</div>
                  <div class="empty-state-text">{{ t('noPlans') }}</div>
                  <div class="empty-state-sub">{{ t('noPlanHint') }}</div>
                </div>
              </td>
            </tr>
            <tr v-for="p in plans" :key="p.id">
              <td><strong>{{ p.name }}</strong></td>
              <td style="font-family:monospace">{{ p.token_quota.toLocaleString() }}</td>
              <td style="font-weight:600;color:var(--primary)">&yen;{{ p.price_yuan }}</td>
              <td>{{ p.duration_days }} {{ t('days') }}</td>
              <td>
                <span :class="'badge ' + (p.status === 'active' ? 'badge-success' : 'badge-default')" style="font-size:10px">
                  {{ p.status === 'active' ? t('planActive') : t('planInactive') }}
                </span>
              </td>
              <td class="text-muted" style="font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                {{ p.description || '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const plans = ref([])
const showForm = ref(false)
const saving = ref(false)
const formError = ref('')

const form = ref({
  name: '',
  price_yuan: 0,
  token_quota: 100000,
  duration_days: 30,
  description: '',
})

async function loadPlans() {
  try {
    plans.value = (await api.getPlans()).items || []
  } catch (e) { /* */ }
}
onMounted(loadPlans)

async function createPlan() {
  if (!form.value.name || !form.value.price_yuan) {
    formError.value = '请填写套餐名称和价格'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    const priceFen = Math.round(form.value.price_yuan * 100)
    await api.createPlan(
      form.value.name,
      form.value.token_quota,
      priceFen,
      form.value.duration_days,
      form.value.description || null
    )
    form.value = { name: '', price_yuan: 0, token_quota: 100000, duration_days: 30, description: '' }
    showForm.value = false
    await loadPlans()
  } catch (e) {
    formError.value = e.message || '创建失败'
  } finally {
    saving.value = false
  }
}
</script>
