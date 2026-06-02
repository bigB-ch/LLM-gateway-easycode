<template>
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="32" height="32" rx="7" :fill="bg"/>
    <!-- Left B (full opacity, slightly wider) -->
    <path d="M7 6.5v19" :stroke="fg" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M9.3 7.8c0-1 1-1.8 3-1.8s3 .8 3 1.8v5.4c0 1-1 1.8-3 1.8s-3-.8-3-1.8v-5.4z" :fill="fg"/>
    <path d="M9.3 8.8c0-.5.6-1 2-1s2 .5 2 1v3.4c0 .5-.6 1-2 1s-2-.5-2-1v-3.4z" :fill="bg"/>
    <path d="M9.3 17.8c0-1 1-1.8 3-1.8s3 .8 3 1.8v5.4c0 1-1 1.8-3 1.8s-3-.8-3-1.8v-5.4z" :fill="fg"/>
    <path d="M9.3 18.8c0-.5.6-1 2-1s2 .5 2 1v3.4c0 .5-.6 1-2 1s-2-.5-2-1v-3.4z" :fill="bg"/>
    <!-- Right B (semi-transparent, overlapping left B's right edge) -->
    <path d="M18 8.5v15" :stroke="fg" stroke-width="2.2" stroke-linecap="round" opacity="0.65"/>
    <path d="M20 9.5c0-.8.8-1.5 2.5-1.5s2.5.7 2.5 1.5v3.8c0 .8-.8 1.5-2.5 1.5s-2.5-.7-2.5-1.5v-3.8z" :fill="fg" opacity="0.5"/>
    <path d="M20 10.2c0-.4.5-.8 1.8-.8s1.8.4 1.8.8v2.4c0 .4-.5.8-1.8.8s-1.8-.4-1.8-.8v-2.4z" :fill="bg"/>
    <path d="M20 18.2c0-.8.8-1.5 2.5-1.5s2.5.7 2.5 1.5v3.8c0 .8-.8 1.5-2.5 1.5s-2.5-.7-2.5-1.5v-3.8z" :fill="fg" opacity="0.5"/>
    <path d="M20 18.9c0-.4.5-.8 1.8-.8s1.8.4 1.8.8v2.4c0 .4-.5.8-1.8.8s-1.8-.4-1.8-.8v-2.4z" :fill="bg"/>
  </svg>
</template>

<script setup>
defineProps({
  fg: { type: String, default: '#4f6ef7' },
  bg: { type: String, default: '#eef1fe' },
})
</script>
