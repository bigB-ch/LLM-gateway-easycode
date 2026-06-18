<template>
  <div>
    <n-space align="center" justify="space-between" style="margin-bottom:24px">
      <n-h1 style="margin:0">{{ t('planManagement') }}</n-h1>
      <n-button type="primary" @click="showForm = !showForm">{{ showForm ? t('cancel') : t('createPlan') }}</n-button>
    </n-space>

    <!-- Create plan form -->
    <n-card v-if="showForm" :bordered="true" style="margin-bottom:24px">
      <n-h3 style="margin:0 0 16px">{{ t('newPlan') }}</n-h3>
      <n-form label-placement="top">
        <n-grid :cols="2" :x-gap="16">
          <n-grid-item>
            <n-form-item :label="t('planName')" required>
              <n-input v-model:value="form.name" :placeholder="t('planName')" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item :label="t('priceYuan')" required>
              <n-input-number v-model:value="form.price_yuan" :min="0.01" :step="0.01" placeholder="0.00" style="width:100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item :label="t('tokenQuotaLabel')">
              <n-input-number v-model:value="form.token_quota" :min="1000" placeholder="100000" style="width:100%" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item :label="t('validityDays')">
              <n-input-number v-model:value="form.duration_days" :min="1" placeholder="30" style="width:100%" />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-form-item :label="t('description')">
          <n-input v-model:value="form.description" type="textarea" rows="2" :placeholder="t('description')" />
        </n-form-item>
        <n-alert v-if="formError" type="error" :bordered="true" closable @close="formError = ''" style="margin-bottom:8px">
          {{ formError }}
        </n-alert>
        <n-button type="primary" :loading="saving" @click="createPlan">
          {{ saving ? t('creatingPlan') : t('createPlanBtn') }}
        </n-button>
      </n-form>
    </n-card>

    <!-- Plan list -->
    <n-card :bordered="true">
      <n-data-table :columns="tableColumns" :data="plans" :bordered="false" :min-height="100" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import {
  NCard, NDataTable, NForm, NFormItem, NGrid, NGridItem, NH1, NH3,
  NInput, NInputNumber, NButton, NAlert, NSpace, NTag,
} from 'naive-ui'
import { api } from '../api'
import { useI18n } from '../i18n'
const { t } = useI18n()

const plans = ref([])
const showForm = ref(false)
const saving = ref(false)
const formError = ref('')

const form = ref({ name: '', price_yuan: 0, token_quota: 100000, duration_days: 30, description: '' })

const tableColumns = [
  { title: t('planName'), key: 'name', render: (row) => h('strong', row.name) },
  { title: t('tokenQuotaLabel'), key: 'token_quota', render: (row) => (row.token_quota || 0).toLocaleString() },
  { title: t('priceYuan'), key: 'price_yuan', render: (row) => h('span', { style: 'font-weight:600;color:var(--primary)' }, '¥' + row.price_yuan) },
  { title: t('validityDays'), key: 'duration_days', render: (row) => row.duration_days + ' ' + t('days') },
  { title: t('status'), key: 'status', render: (row) => h(NTag, { type: row.status === 'active' ? 'success' : 'default', size: 'small' }, { default: () => row.status === 'active' ? t('planActive') : t('planInactive') }) },
  { title: t('description'), key: 'description', render: (row) => row.description || '-' },
]

async function loadPlans() {
  try { plans.value = (await api.getPlans()).items || [] } catch (e) { /* */ }
}
onMounted(loadPlans)

async function createPlan() {
  if (!form.value.name || !form.value.price_yuan) { formError.value = '请填写套餐名称和价格'; return }
  saving.value = true; formError.value = ''
  try {
    const priceFen = Math.round(form.value.price_yuan * 100)
    await api.createPlan(form.value.name, form.value.token_quota, priceFen, form.value.duration_days, form.value.description || null)
    form.value = { name: '', price_yuan: 0, token_quota: 100000, duration_days: 30, description: '' }
    showForm.value = false
    await loadPlans()
  } catch (e) { formError.value = e.message || '创建失败' }
  finally { saving.value = false }
}
</script>
