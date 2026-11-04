<script setup>
defineProps({
  message: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <article class="message-row" :class="message.role">
    <div class="message-avatar" aria-hidden="true">{{ message.role === 'assistant' ? 'W' : 'Y' }}</div>
    <div class="message-content">
      <div class="message-meta">{{ message.role === 'assistant' ? 'WEATHERGPT' : 'YOU' }}</div>
      <div class="message-bubble"><p>{{ message.content }}</p></div>
      <div v-if="message.sources?.length" class="sources-panel">
        <div class="sources-title">REFERENCE MATERIAL</div>
        <div v-for="(source, index) in message.sources" :key="`${source.source}-${index}`" class="source-item">
          <span class="source-mark">↳</span>
          <span>{{ source.title || source.source }}</span>
          <span v-if="typeof source.similarity === 'number'" class="source-score">{{ Math.round(source.similarity * 100) }}% match</span>
        </div>
      </div>
    </div>
  </article>
</template>
