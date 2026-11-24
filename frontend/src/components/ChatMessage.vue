
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

    <!-- AVATAR -->
    <div class="message-avatar" :class="message.role">
      <span v-if="message.role === 'assistant'">W</span>
      <span v-else>Y</span>
    </div>

    <div class="message-content">

      <!-- MESSAGE LABEL -->
      <div class="message-meta">
        <strong>
          {{ message.role === 'assistant' ? 'WeatherGPT' : 'You' }}
        </strong>
        <span v-if="message.role === 'assistant'" class="verified">
          ✓
        </span>
      </div>

      <!-- MESSAGE TEXT -->
      <div class="message-bubble">
        <p>{{ message.content }}</p>
      </div>

      <!-- SOURCE REFERENCES -->
      <div
        v-if="message.sources?.length"
        class="sources-panel"
      >
        <div class="sources-title">
          <span>↗</span>
          SOURCES & REFERENCES
        </div>

        <div
          v-for="(source, index) in message.sources"
          :key="`${source.source}-${index}`"
          class="source-item"
        >
          <span class="source-mark">↳</span>

          <span class="source-name">
            {{ source.title || source.source }}
          </span>

          <span
            v-if="typeof source.similarity === 'number'"
            class="source-score"
          >
            {{ Math.round(source.similarity * 100) }}% match
          </span>
        </div>
      </div>

    </div>
  </article>
</template>

<style scoped>
.message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 18px;
  max-width: 100%;
}

.message-avatar {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 10px;
  font-weight: 800;
}

.message-avatar.assistant {
  background: #e8f0fb;
  color: #4c729f;
}

.message-avatar.user {
  background: #eaf3f0;
  color: #4c8b76;
}

.message-content {
  min-width: 0;
  max-width: 85%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-row.user .message-content {
  align-items: flex-end;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
  font-size: 9px;
  color: #7b8da4;
}

.message-meta strong {
  font-weight: 700;
}

.verified {
  background: #e8f2ff;
  color: #6089b5;
  border-radius: 50%;
  height: 12px;
  width: 12px;
  display: grid;
  place-items: center;
  font-size: 8px;
}

.message-bubble {
  max-width: 100%;
  padding: 11px 14px;
  border-radius: 3px 11px 11px 11px;
  background: #f0f4f9;
  color: #526980;
  font-size: 11px;
  line-height: 1.8;
  overflow-wrap: anywhere;
}

.message-bubble p {
  margin: 0;
  white-space: pre-wrap;
}

.message-row.user .message-bubble {
  background: #456f9f;
  color: white;
  border-radius: 11px 3px 11px 11px;
}

.sources-panel {
  margin-top: 10px;
  width: 100%;
  border: 1px solid #e8edf4;
  background: #fafcff;
  border-radius: 8px;
  padding: 10px 12px;
}

.sources-title {
  color: #8b9cb1;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.sources-title span {
  color: #527da9;
  margin-right: 5px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 0;
  font-size: 9px;
  color: #74869d;
  border-top: 1px solid #eff2f6;
}

.source-mark {
  color: #6d94bd;
}

.source-name {
  flex: 1;
  overflow-wrap: anywhere;
}

.source-score {
  white-space: nowrap;
  color: #5c9a80;
  font-size: 8px;
  font-weight: 700;
}

@media (max-width: 480px) {
  .message-content {
    max-width: 88%;
  }

  .message-bubble {
    font-size: 10px;
    padding: 10px 12px;
  }

  .message-row {
    gap: 7px;
    margin-bottom: 14px;
  }
}
</style>
