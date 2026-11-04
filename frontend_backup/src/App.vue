<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import ChatMessage from './components/ChatMessage.vue'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const messages = ref([
  {
    id: 1,
    role: 'assistant',
    content: "Hi! I'm WeatherGPT. Ask me about current conditions, hourly or daily forecasts, rainfall, or weather safety. Which city are you interested in?",
    sources: [],
  },
])
const history = ref([])
const draft = ref('')
const sending = ref(false)
const apiOnline = ref(null)
const errorMessage = ref('')
const messageList = ref(null)
const input = ref(null)
let nextId = 2

const canSend = computed(() => draft.value.trim().length > 0 && !sending.value)
const suggestions = [
  "What's the current weather in Bengaluru?",
  'Will it rain in Mumbai tomorrow?',
  'Explain the IMD orange and red warnings.',
]

async function checkApi() {
  try {
    const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) })
    apiOnline.value = response.ok
  } catch {
    apiOnline.value = false
  }
}

async function scrollToLatest() {
  await nextTick()
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight
}

function appendMessage(role, content, sources = []) {
  messages.value.push({ id: nextId++, role, content, sources })
  scrollToLatest()
}

async function sendMessage(text = draft.value) {
  const message = text.trim()
  if (!message || sending.value) return
  if (message.length > 2000) {
    errorMessage.value = 'Please keep your message under 2,000 characters.'
    return
  }

  errorMessage.value = ''
  appendMessage('user', message)
  draft.value = ''
  sending.value = true

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history: history.value.slice(-12) }),
    })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok) {
      const detail = typeof payload.detail === 'string' ? payload.detail : 'The chatbot could not process your request.'
      throw new Error(detail)
    }

    const answer = payload.answer || 'I could not generate an answer. Please try again.'
    appendMessage('assistant', answer, Array.isArray(payload.sources) ? payload.sources : [])
    history.value.push({ role: 'user', content: message }, { role: 'assistant', content: answer })
    apiOnline.value = true
  } catch (error) {
    appendMessage('assistant', `I couldn't reach WeatherGPT. ${error.message || 'Please check your connection and try again.'}`)
    apiOnline.value = false
  } finally {
    sending.value = false
    input.value?.focus()
  }
}

function startNewChat() {
  history.value = []
  messages.value = [{
    id: nextId++,
    role: 'assistant',
    content: 'A new conversation is ready. What would you like to know about the weather?',
    sources: [],
  }]
  draft.value = ''
  errorMessage.value = ''
  input.value?.focus()
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

onMounted(checkApi)
</script>

<template>
  <div class="page-shell">
    <header class="topbar">
      <a class="brand" href="#top" aria-label="WeatherGPT home">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" fill="none"><path d="M9 22.5h14a5 5 0 0 0 .2-10 7.2 7.2 0 0 0-13.8-1.3A5.7 5.7 0 0 0 9 22.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="m12 26 1.5-2m5 2 1.5-2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </span>
        <span class="brand-copy"><strong>WeatherGPT</strong><small>Weather, explained.</small></span>
      </a>
      <div class="api-status" :class="{ online: apiOnline === true, offline: apiOnline === false }">
        <span class="status-dot"></span>
        <span>{{ apiOnline === true ? 'API CONNECTED' : apiOnline === false ? 'API UNAVAILABLE' : 'CHECKING API' }}</span>
      </div>
    </header>

    <main id="top">
      <section class="hero">
        <div class="eyebrow"><span></span> YOUR WEATHER COMPANION</div>
        <h1>Ask the sky.<br /><span>Get clarity.</span></h1>
        <p>Understand the weather with answers grounded in forecast data and trusted weather guidance.</p>
        <div class="suggestions" aria-label="Suggested questions">
          <button v-for="suggestion in suggestions" :key="suggestion" class="suggestion" type="button" @click="sendMessage(suggestion)">
            {{ suggestion }} <span aria-hidden="true">↗</span>
          </button>
        </div>
      </section>

      <section class="chat-card" aria-label="WeatherGPT conversation">
        <div class="chat-header">
          <div class="assistant-identity">
            <span class="assistant-icon">W</span>
            <span><strong>WeatherGPT assistant</strong><small>Ask a question to get started</small></span>
          </div>
          <button class="new-chat" type="button" @click="startNewChat">New chat <span aria-hidden="true">↻</span></button>
        </div>

        <div ref="messageList" class="message-list" aria-live="polite" aria-relevant="additions">
          <ChatMessage v-for="message in messages" :key="message.id" :message="message" />
          <div v-if="sending" class="typing-row">
            <span class="typing-avatar">W</span>
            <span class="typing-indicator"><i></i><i></i><i></i><span>WeatherGPT is thinking</span></span>
          </div>
        </div>

        <form class="composer" @submit.prevent="sendMessage()">
          <label class="sr-only" for="chat-input">Your weather question</label>
          <textarea
            id="chat-input"
            ref="input"
            v-model="draft"
            rows="1"
            maxlength="2000"
            placeholder="Ask about the weather in a city..."
            :disabled="sending"
            @keydown="handleKeydown"
          ></textarea>
          <div class="composer-actions">
            <span class="character-count">{{ draft.length }}/2000</span>
            <button class="send-button" type="submit" :disabled="!canSend" aria-label="Send message">
              <svg viewBox="0 0 24 24" fill="none"><path d="M12 19V5m-6 6 6-6 6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
        </form>
        <p v-if="errorMessage" class="inline-error" role="alert">{{ errorMessage }}</p>
        <p class="disclaimer">WeatherGPT uses available project weather data. Follow official alerts and local authorities during severe weather.</p>
      </section>
    </main>

    <footer class="footer"><span>WEATHERGPT</span><i></i> WEATHER DATA + RETRIEVAL-AUGMENTED AI</footer>
  </div>
</template>
