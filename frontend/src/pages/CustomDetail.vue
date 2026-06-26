<template>
  <div class="custom-detail">
    <button class="back-btn" @click="$router.back()">&larr; 返回定制工具</button>
    <h1>{{ caseData?.name || '案例详情' }}</h1>
    <p class="case-summary">{{ caseData?.summary }}</p>
    <div class="case-tags" v-if="caseData?.tags">
      <span v-for="t in caseData.tags" :key="t">{{ t }}</span>
    </div>

    <div class="case-placeholder">
      <p>案例详情页开发中，敬请期待</p>
    </div>

    <div class="inquiry-box">
      <p>对该案例感兴趣？</p>
      <a href="mailto:contact@easycode.uno" class="inquiry-link">联系我们定制</a>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const cases = {
  'ai-cs': { name: 'AI 客服系统', summary: '基于大模型的智能客服系统，支持知识库、多轮对话、工单流转', tags: ['大模型', '客服', '知识库'] },
  'ai-anime': { name: 'AI 动漫制作环境', summary: '从文生图到视频生成，整合 Stable Diffusion、AnimateDiff 等工具链', tags: ['Stable Diffusion', '视频生成', '环境搭建'] },
}

const caseData = computed(() => cases[route.params.id] || null)
</script>

<style scoped>
.custom-detail { max-width: 800px; margin: 0 auto; padding: 24px; }
.back-btn { background: none; border: 1px solid var(--border); padding: 6px 16px; border-radius: 8px; cursor: pointer; color: var(--text); font-size: 0.85rem; margin-bottom: 20px; }
.back-btn:hover { border-color: var(--primary); color: var(--primary); }
h1 { margin: 0 0 8px; }
.case-summary { color: var(--text-muted); font-size: 0.9rem; margin: 0 0 16px; }
.case-tags { display: flex; gap: 8px; margin-bottom: 32px; }
.case-tags span { padding: 4px 14px; border-radius: 12px; font-size: 0.8rem; background: #f0f2f5; color: var(--text-muted); }
.case-placeholder { padding: 80px 0; text-align: center; color: var(--text-muted); border: 2px dashed var(--border); border-radius: 12px; margin-bottom: 32px; }
.inquiry-box { text-align: center; padding: 32px; background: var(--bg); border: 1px solid var(--border); border-radius: 12px; }
.inquiry-box p { margin: 0 0 12px; font-weight: 500; }
.inquiry-link { display: inline-block; padding: 8px 24px; border-radius: 8px; background: var(--primary); color: #fff; text-decoration: none; font-weight: 500; }
</style>
