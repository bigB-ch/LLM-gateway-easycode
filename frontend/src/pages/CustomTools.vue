<template>
  <div class="custom-page">
    <div class="custom-hero">
      <h2>AI 定制服务</h2>
      <p>从需求沟通到方案交付，提供端到端的 AI 系统定制开发服务</p>
    </div>

    <div class="custom-cases" v-if="cases.length">
      <div v-for="c in cases" :key="c.id" class="case-card" @click="$router.push(`/custom/${c.id}`)">
        <div class="case-thumb"></div>
        <div class="case-body">
          <h3>{{ c.name }}</h3>
          <p>{{ c.summary }}</p>
          <div class="case-tags">
            <span v-for="t in c.tags" :key="t">{{ t }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">
      <p>定制案例准备中，敬请期待</p>
      <p class="empty-sub">如需 AI 定制服务，请通过下方入口提交需求</p>
    </div>

    <div class="custom-process">
      <h3>定制流程</h3>
      <div class="process-steps">
        <div class="step"><div class="step-num">1</div><div class="step-text">需求沟通</div></div>
        <div class="step-arrow">&rarr;</div>
        <div class="step"><div class="step-num">2</div><div class="step-text">方案报价</div></div>
        <div class="step-arrow">&rarr;</div>
        <div class="step"><div class="step-num">3</div><div class="step-text">开发交付</div></div>
      </div>
    </div>

    <div class="inquiry-section">
      <h3>提交定制需求</h3>
      <p>描述您的需求，我们会尽快与您联系</p>
      <a href="mailto:contact@easycode.uno" class="inquiry-btn">发送邮件 &rarr;</a>
    </div>
  </div>
</template>

<script setup>
const cases = [
  { id: 'ai-cs', name: 'AI 客服系统', summary: '基于大模型的智能客服系统，支持知识库、多轮对话、工单流转', tags: ['大模型', '客服', '知识库'] },
  { id: 'ai-anime', name: 'AI 动漫制作环境', summary: '从文生图到视频生成，整合 Stable Diffusion、AnimateDiff 等工具链', tags: ['Stable Diffusion', '视频生成', '环境搭建'] },
]
</script>

<style scoped>
.custom-page { max-width: 900px; margin: 0 auto; padding: 40px 24px 64px; }
.custom-hero { text-align: center; margin-bottom: 48px; }
.custom-hero h2 { margin: 0 0 8px; font-size: 1.5rem; }
.custom-hero p { margin: 0; color: var(--text-muted); font-size: 0.9rem; }
.custom-cases { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-bottom: 48px; }
.case-card { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; cursor: pointer; transition: all 0.2s; background: var(--bg); }
.case-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); border-color: var(--primary); }
.case-thumb { height: 140px; background: linear-gradient(135deg, #fef3c7, #fde68a); }
.case-body { padding: 16px; }
.case-body h3 { margin: 0 0 8px; font-size: 1.05rem; }
.case-body p { margin: 0 0 12px; font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; }
.case-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.case-tags span { padding: 2px 10px; border-radius: 10px; font-size: 0.75rem; background: #f0f2f5; color: var(--text-muted); }
.empty-state { text-align: center; padding: 60px 0; color: var(--text-muted); }
.empty-sub { font-size: 0.85rem; margin-top: 8px; }
.custom-process { margin-bottom: 48px; }
.custom-process h3 { text-align: center; margin-bottom: 24px; }
.process-steps { display: flex; justify-content: center; align-items: center; gap: 16px; }
.step { text-align: center; }
.step-num { width: 44px; height: 44px; border-radius: 50%; background: var(--primary); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem; margin: 0 auto 8px; }
.step-text { font-size: 0.85rem; color: var(--text); }
.step-arrow { font-size: 1.3rem; color: var(--text-muted); }
.inquiry-section { text-align: center; padding: 40px; border: 2px dashed var(--border); border-radius: 16px; }
.inquiry-section h3 { margin: 0 0 8px; }
.inquiry-section p { color: var(--text-muted); font-size: 0.85rem; margin: 0 0 20px; }
.inquiry-btn { display: inline-block; padding: 10px 32px; border-radius: 10px; background: var(--primary); color: #fff; text-decoration: none; font-weight: 500; }
@media (max-width: 600px) { .process-steps { flex-wrap: wrap; } .step-arrow { transform: rotate(90deg); } }
</style>
