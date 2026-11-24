
<script setup>
import {
  ref,
  computed,
  nextTick,
  onMounted,
  onBeforeUnmount
} from 'vue'

import ChatMessage from './components/ChatMessage.vue'

const API_BASE = 'http://127.0.0.1:8000'
//const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

const messages = ref([
  {
    id: 1,
    role: 'assistant',
    content:
      'Hello! I am WeatherGPT, your weather intelligence assistant. Ask me about weather conditions, forecasts, rainfall, alerts or weather patterns.'
  }
])

const history = ref([])
const draft = ref('')
const sending = ref(false)
const apiOnline = ref(false)
const errorMessage = ref('')
const voiceError = ref('')
const listening = ref(false)
const chatOpen = ref(false)
const activePage = ref('home')

const messageList = ref(null)
const input = ref(null)

let recognition = null
let finalTranscript = ''

const canSend = computed(() =>
  draft.value.trim().length > 0 && !sending.value
)

const suggestions = [
  'What is the weather forecast for today?',
  'Explain the different types of weather alerts.',
  'How do rainfall patterns affect flooding?',
  'What do humidity and atmospheric pressure indicate?'
]

const features = [
  {
    number: '01',
    category: 'CONDITIONS',
    title: 'Weather Updates',
    description:
      'Understand current weather conditions, temperature, humidity and atmospheric changes.',
    icon: 'cloud-sun',
    question:
      'Explain the important parameters used to understand current weather conditions.'
  },
  {
    number: '02',
    category: 'PREDICTIONS',
    title: 'Weather Forecasting',
    description:
      'Explore upcoming weather conditions, rainfall predictions and changing weather patterns.',
    icon: 'cloud-rain',
    question:
      'Explain how weather forecasting works and how to interpret rainfall predictions.'
  },
  {
    number: '03',
    category: 'WARNINGS',
    title: 'Weather Alerts',
    description:
      'Understand weather warnings, alert levels and precautions during severe conditions.',
    icon: 'alert',
    question:
      'Explain IMD weather warning levels and the precautions associated with them.'
  },
  {
    number: '04',
    category: 'ANALYTICS',
    title: 'Historical Insights',
    description:
      'Understand historical weather information, compare patterns and explore trends.',
    icon: 'chart',
    question:
      'Explain how historical weather data can help us understand climate and rainfall patterns.'
  },
  {
    number: '05',
    category: 'RISK ANALYSIS',
    title: 'Rainfall & Flood Risk',
    description:
      'Learn about heavy rainfall, potential flooding and weather-related risks.',
    icon: 'waves',
    question:
      'Explain heavy rainfall risks, possible flooding and relevant safety precautions.'
  },
  {
    number: '06',
    category: 'AI ASSISTANCE',
    title: 'Weather Conversations',
    description:
      'Ask weather-related questions in everyday language and get understandable explanations.',
    icon: 'message',
    question:
      'How can you help me understand weather information and make better decisions?'
  }
]

// --------------------------------------------------
// NAVIGATION
// --------------------------------------------------

function goToPage(page) {
  activePage.value = page

  if (page === 'assistant') {
    openAssistant()
    return
  }

  closeAssistant()

  nextTick(() => {
    const element = document.getElementById(page)

    element?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  })
}

function openAssistant() {
  chatOpen.value = true
  activePage.value = 'assistant'

  nextTick(() => {
    scrollToBottom()
    input.value?.focus()
  })
}

function closeAssistant() {
  chatOpen.value = false

  if (activePage.value === 'assistant') {
    activePage.value = 'home'
  }
}

// --------------------------------------------------
// BACKEND CONNECTION
// --------------------------------------------------

async function checkAPI() {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET'
    })

    apiOnline.value = response.ok
  } catch {
    apiOnline.value = false
  }
}

// --------------------------------------------------
// CHAT FUNCTIONALITY
// --------------------------------------------------

async function sendMessage(question = null) {
  const content = (question || draft.value).trim()

  if (!content || sending.value) return

  stopListening()

  errorMessage.value = ''
  voiceError.value = ''

  messages.value.push({
    id: Date.now(),
    role: 'user',
    content
  })

  draft.value = ''
  sending.value = true

  await scrollToBottom()

  const previousHistory = history.value.slice(-12)

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: content,
        history: previousHistory
      })
    })

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`)
    }

    const payload = await response.json()

    if (!payload.answer) {
      throw new Error('The server returned an empty response.')
    }

    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: payload.answer,
      sources: Array.isArray(payload.sources)
        ? payload.sources
        : []
    }

    messages.value.push(assistantMessage)

    history.value.push(
      {
        role: 'user',
        content
      },
      {
        role: 'assistant',
        content: payload.answer
      }
    )

    apiOnline.value = true

  } catch (error) {
    console.error('Chat error:', error)

    errorMessage.value =
      'Unable to connect to WeatherGPT. Please check your connection and try again.'

    apiOnline.value = false

  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

function startNewChat() {
  stopListening()

  messages.value = [
    {
      id: Date.now(),
      role: 'assistant',
      content:
        'Hello! I am WeatherGPT. What would you like to know about the weather today?'
    }
  ]

  history.value = []
  draft.value = ''
  errorMessage.value = ''
  voiceError.value = ''

  nextTick(() => {
    input.value?.focus()
    scrollToBottom()
  })
}

function useSuggestion(question) {
  openAssistant()
  sendMessage(question)
}

function handleKeydown(event) {
  if (
    event.key === 'Enter' &&
    !event.shiftKey &&
    !event.isComposing
  ) {
    event.preventDefault()
    sendMessage()
  }
}

async function scrollToBottom() {
  await nextTick()

  if (messageList.value) {
    messageList.value.scrollTo({
      top: messageList.value.scrollHeight,
      behavior: 'smooth'
    })
  }
}

// --------------------------------------------------
// VOICE INPUT
// --------------------------------------------------

function setupSpeechRecognition() {
  const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition

  if (!SpeechRecognition) {
    voiceError.value =
      'Voice input is not supported in this browser. Please use Chrome or Edge.'
    return false
  }

  recognition = new SpeechRecognition()

  recognition.lang = 'en-IN'
  recognition.continuous = false
  recognition.interimResults = true
  recognition.maxAlternatives = 1

  recognition.onstart = () => {
    listening.value = true
    voiceError.value = ''
    finalTranscript = ''
  }

  recognition.onresult = (event) => {
    let interimTranscript = ''

    for (
      let i = event.resultIndex;
      i < event.results.length;
      i++
    ) {
      const transcript = event.results[i][0].transcript

      if (event.results[i].isFinal) {
        finalTranscript += transcript
      } else {
        interimTranscript += transcript
      }
    }

    draft.value = [
      finalTranscript,
      interimTranscript
    ].filter(Boolean).join(' ')
  }

  recognition.onerror = (event) => {
    if (event.error === 'not-allowed') {
      voiceError.value =
        'Please allow microphone access in your browser.'
    } else if (event.error !== 'no-speech' &&
               event.error !== 'aborted') {
      voiceError.value =
        'Voice input could not be completed. Please try again.'
    }
  }

  recognition.onend = () => {
    listening.value = false
    finalTranscript = ''
  }

  return true
}

function toggleListening() {
  if (listening.value) {
    stopListening()
    return
  }

  voiceError.value = ''

  if (!recognition && !setupSpeechRecognition()) {
    return
  }

  try {
    recognition.start()
  } catch (error) {
    voiceError.value = 'Unable to start voice input. Please try again.'
  }
}

function stopListening() {
  if (recognition && listening.value) {
    recognition.stop()
  }

  listening.value = false
}

// --------------------------------------------------
// LIFECYCLE
// --------------------------------------------------

function handleEscape(event) {
  if (event.key === 'Escape' && chatOpen.value) {
    closeAssistant()
  }
}

onMounted(() => {
  checkAPI()

  window.addEventListener('keydown', handleEscape)
})

onBeforeUnmount(() => {
  stopListening()
  window.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <div class="weather-app">

    <!-- BACKGROUND VIDEO -->

    <div class="video-background">
      <video
        autoplay
        muted
        loop
        playsinline
        preload="auto"
      >
        <source src="/sky.mp4" type="video/mp4" />
      </video>
      <div class="video-overlay"></div>
    </div>

    <!-- NAVIGATION -->

    <header class="navbar">
      <div class="nav-inner">

        <button
          class="brand"
          @click="goToPage('home')"
          aria-label="WeatherGPT home"
        >
          <span class="brand-symbol">
            <svg viewBox="0 0 24 24" fill="none">
              <path
                d="M4 15.5a4 4 0 0 1 3.8-4A5.5 5.5 0 0 1 18.5 10a3.5 3.5 0 0 1 .5 7H7.5"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
              />
              <path
                d="M8 20h8"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
              />
            </svg>
          </span>

          <span>WEATHER<span class="brand-light">GPT</span></span>
        </button>

        <nav class="nav-links">
          <button
            :class="{ active: activePage === 'home' }"
            @click="goToPage('home')"
          >
            Home
          </button>

          <button
            :class="{ active: activePage === 'assistant' }"
            @click="openAssistant"
          >
            Assistant
          </button>

          <button
            :class="{ active: activePage === 'explore' }"
            @click="goToPage('explore')"
          >
            Explore
          </button>
        </nav>

        <button
          class="nav-cta"
          @click="openAssistant"
        >
          Open Assistant
          <span>↗</span>
        </button>

      </div>
    </header>

    <main>

      <!-- HOME HERO -->

      <section id="home" class="hero-section">

        <div class="hero-content">

          <div class="hero-eyebrow">
            <span class="eyebrow-line"></span>
            INTELLIGENCE BEYOND THE FORECAST
          </div>

          <h1>
            Understand the weather.
            <span>See what lies ahead.</span>
          </h1>

          <p class="hero-description">
            Weather information, forecasts and insights,
            brought together in one intelligent experience.
            Make sense of changing conditions with WeatherGPT.
          </p>

          <div class="hero-actions">
            <button
              class="primary-button"
              @click="openAssistant"
            >
              Explore WeatherGPT
              <span>↗</span>
            </button>

            <button
              class="secondary-button"
              @click="goToPage('explore')"
            >
              Discover features
            </button>
          </div>

          <div class="hero-status">
            <span
              class="status-dot"
              :class="{ offline: !apiOnline }"
            ></span>

            {{ apiOnline
              ? 'WeatherGPT services connected'
              : 'WeatherGPT services'
            }}
          </div>

        </div>

        <div class="hero-bottom">
          <span>WEATHER INTELLIGENCE PLATFORM</span>
          <span>01 — UNDERSTAND YOUR ENVIRONMENT</span>
        </div>

      </section>

      <!-- INTRODUCTION -->

      <section class="intro-section">

        <div class="intro-left">
          <span class="section-label">A BETTER WAY TO UNDERSTAND WEATHER</span>

          <h2>
            More than just
            <span>a forecast.</span>
          </h2>
        </div>

        <div class="intro-right">
          <p>
            Weather data can be difficult to interpret.
            WeatherGPT brings information together and
            makes it easier to understand through
            conversational intelligence.
          </p>

          <button @click="goToPage('explore')">
            Discover what you can do
            <span>↗</span>
          </button>
        </div>

      </section>

      <!-- EXPLORE -->

      <section id="explore" class="explore-section glass-panel">

        <div class="explore-heading">

          <div>
            <span class="section-label">
              DISCOVER WEATHERGPT
            </span>

            <h2>
              Weather intelligence,
              <span>made simple.</span>
            </h2>

            <p>
              Explore the different ways WeatherGPT helps
              you understand weather information.
            </p>
          </div>

          <button
            class="explore-ask"
            @click="openAssistant"
          >
            Ask WeatherGPT
            <span>↗</span>
          </button>

        </div>

        <div class="feature-grid">

          <article
            v-for="feature in features"
            :key="feature.number"
            class="feature-card"
          >

            <div class="feature-card-top">
              <span class="feature-icon">

                <svg
                  v-if="feature.icon === 'cloud-sun'"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    cx="17" cy="7" r="3"
                    stroke="currentColor" stroke-width="1.5"
                  />
                  <path
                    d="M17 1v2m0 8v2m6-6h-2m-8 0h-2"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                  <path
                    d="M4 17a4 4 0 0 1 3.8-4 5 5 0 0 1 9.7 1.5A3.5 3.5 0 0 1 17 21H7a3 3 0 0 1-3-4Z"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                </svg>

                <svg
                  v-else-if="feature.icon === 'cloud-rain'"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M4 13a4 4 0 0 1 3.8-4 5.5 5.5 0 0 1 10.7 1.5A3.5 3.5 0 0 1 18 17H7a3 3 0 0 1-3-4Z"
                    stroke="currentColor" stroke-width="1.5"
                  />
                  <path
                    d="m8 19-1 2m6-2-1 2m6-2-1 2"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                </svg>

                <svg
                  v-else-if="feature.icon === 'alert'"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M12 3 2.8 20h18.4L12 3Z"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M12 9v5m0 3h.01"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                  />
                </svg>

                <svg
                  v-else-if="feature.icon === 'chart'"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M3 3v18h18"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                  <path
                    d="m6 15 5-5 4 3 6-7"
                    stroke="currentColor"
                    stroke-width="1.7"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>

                <svg
                  v-else-if="feature.icon === 'waves'"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M2 8c3-3 5 3 8 0s5-3 7 0 4 3 5 1M2 14c3-3 5 3 8 0s5-3 7 0 4 3 5 1M2 20c3-3 5 3 8 0s5-3 7 0 4 3 5 1"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                </svg>

                <svg
                  v-else
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>

              </span>

              <span class="feature-number">
                {{ feature.number }}
              </span>
            </div>

            <span class="feature-category">
              {{ feature.category }}
            </span>

            <h3>{{ feature.title }}</h3>

            <p>{{ feature.description }}</p>

            <button
              class="feature-link"
              @click="useSuggestion(feature.question)"
            >
              Explore feature
              <span>↗</span>
            </button>

          </article>

        </div>

        <div class="explore-bottom">
          <span>WEATHERGPT / WEATHER INTELLIGENCE</span>

          <button @click="openAssistant">
            Have a question? Let's talk
            <span>↗</span>
          </button>
        </div>

      </section>

      <!-- BOTTOM CALL TO ACTION -->

      <section class="closing-section">
        <span class="section-label">
          WEATHER INFORMATION, MADE UNDERSTANDABLE
        </span>

        <h2>
          The weather is always changing.
          <span>Stay informed.</span>
        </h2>

        <button
          class="primary-button"
          @click="openAssistant"
        >
          Start a conversation
          <span>↗</span>
        </button>
      </section>

    </main>

    <!-- FOOTER -->

    <footer class="footer">
      <div class="footer-brand">
        WEATHER<span>GPT</span>
      </div>

      <span>
        An intelligent way to understand the weather.
      </span>

      <span class="footer-copy">
        © 2026 WEATHERGPT
      </span>
    </footer>

    <!-- MINIMIZED CHAT LAUNCHER -->

    <Transition name="launcher-transition">
      <button
        v-if="!chatOpen"
        class="floating-chat-launcher"
        @click="openAssistant"
        aria-label="Open WeatherGPT assistant"
      >
        <span class="launcher-icon">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M4 15.5a4 4 0 0 1 3.8-4A5.5 5.5 0 0 1 18.5 10a3.5 3.5 0 0 1 .5 7H7.5"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
            />
            <path
              d="M8 20h8"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
            />
          </svg>
        </span>

        <span class="launcher-text">
          <strong>WeatherGPT</strong>
          <small>Ask your weather assistant</small>
        </span>

        <span class="launcher-arrow">↗</span>
      </button>
    </Transition>

    <!-- CHAT PANEL -->

    <Transition name="chat-drawer">
      <aside
        v-if="chatOpen"
        class="floating-chat-panel"
        aria-label="WeatherGPT chat"
      >

        <!-- CHAT HEADER -->

        <div class="floating-chat-header">

          <div class="chat-title">
            <div class="chat-avatar">W</div>

            <div class="chat-heading-text">
              <strong>WeatherGPT Assistant</strong>

              <span>
                <span
                  class="online-indicator"
                  :class="{ offline: !apiOnline }"
                ></span>

                {{ apiOnline ? 'Connected' : 'Ready to assist' }}
              </span>
            </div>
          </div>

          <div class="floating-header-actions">

            <button
              class="icon-action"
              @click="startNewChat"
              aria-label="New conversation"
              title="New conversation"
            >
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M20 7v5h-5M4 17v-5h5"
                  stroke="currentColor"
                  stroke-width="1.7"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M5.6 9A7 7 0 0 1 18 6l2 6M4 12l2 6a7 7 0 0 0 12.4-3"
                  stroke="currentColor"
                  stroke-width="1.7"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>

            <button
              class="icon-action close-action"
              @click="closeAssistant"
              aria-label="Close assistant"
            >
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="m6 6 12 12M18 6 6 18"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                />
              </svg>
            </button>

          </div>
        </div>

        <!-- MESSAGES -->

        <div
          ref="messageList"
          class="message-list floating-message-list"
          aria-live="polite"
          aria-relevant="additions"
        >

          <div class="chat-date">
            <span></span>
            CONVERSATION
            <span></span>
          </div>

          <ChatMessage
            v-for="message in messages"
            :key="message.id"
            :message="message"
          />

          <div
            v-if="messages.length === 1"
            class="chat-suggestions"
          >
            <span class="suggestion-label">
              YOU CAN ASK
            </span>

            <button
              v-for="suggestion in suggestions"
              :key="suggestion"
              class="suggestion-chip"
              @click="useSuggestion(suggestion)"
            >
              {{ suggestion }}
              <span>↗</span>
            </button>
          </div>

          <div v-if="sending" class="typing-row">
            <div class="typing-avatar">W</div>

            <div class="typing-bubble">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </div>
          </div>

        </div>

        <!-- VOICE STATUS -->

        <div
          v-if="listening"
          class="voice-feedback"
        >
          <span class="voice-pulse"></span>
          Listening
          <button @click="stopListening">Stop</button>
        </div>

        <div
          v-if="voiceError"
          class="inline-error"
        >
          {{ voiceError }}
        </div>

        <!-- COMPOSER -->

        <form
          class="composer floating-composer"
          @submit.prevent="sendMessage()"
        >

          <textarea
            ref="input"
            v-model="draft"
            rows="1"
            maxlength="2000"
            placeholder="Ask WeatherGPT anything..."
            :disabled="sending"
            @keydown="handleKeydown"
          ></textarea>

          <div class="composer-bottom">

            <div class="composer-controls">

              <button
                type="button"
                class="mic-button"
                :class="{ recording: listening }"
                :disabled="sending"
                @click="toggleListening"
                aria-label="Voice input"
                title="Voice input"
              >
                <svg viewBox="0 0 24 24" fill="none">
                  <rect
                    x="9"
                    y="3"
                    width="6"
                    height="12"
                    rx="3"
                    stroke="currentColor"
                    stroke-width="1.8"
                  />
                  <path
                    d="M5 11a7 7 0 0 0 14 0M12 18v3m-4 0h8"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                  />
                </svg>
              </button>

              <button
                type="submit"
                class="send-button"
                :disabled="!canSend"
                aria-label="Send message"
                title="Send message"
              >
                <svg viewBox="0 0 24 24" fill="none">
                  <path
                    d="M12 19V5m-6 6 6-6 6 6"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </button>

            </div>
          </div>

        </form>

        <div
          v-if="errorMessage"
          class="inline-error connection-error"
        >
          {{ errorMessage }}
        </div>

        <div class="chat-disclaimer">
          WeatherGPT may make mistakes. Follow official weather alerts.
        </div>

      </aside>
    </Transition>

  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  font-family: 'DM Sans', sans-serif;
  color: #263c55;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;

  --blue: #527ba5;
  --blue-dark: #355b83;
  --text: #304862;
  --muted: #8194a9;
  --border: rgba(255,255,255,.48);
  --glass: rgba(255,255,255,.86);
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
  scroll-padding-top: 90px;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
  background: #eaf1f8;
}

button,
textarea {
  font: inherit;
}

button {
  cursor: pointer;
}

button:focus-visible,
textarea:focus-visible {
  outline: 2px solid #83a8d1;
  outline-offset: 3px;
}

.weather-app {
  min-height: 100vh;
  position: relative;
  isolation: isolate;
  overflow: clip;
}

/* BACKGROUND VIDEO */

.video-background {
  position: fixed;
  inset: 0;
  z-index: -2;
  overflow: hidden;
  background: #56799e;
}

.video-background video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(
      180deg,
      rgba(13,35,60,.30) 0%,
      rgba(34,66,103,.15) 35%,
      rgba(18,43,71,.38) 100%
    );
}

/* NAVIGATION */

.navbar {
  position: sticky;
  top: 0;
  z-index: 50;
  padding: 0 6%;
  background: rgba(34,65,100,.25);
  border-bottom: 1px solid rgba(255,255,255,.18);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.nav-inner {
  max-width: 1400px;
  min-height: 70px;
  margin: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 25px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 9px;
  border: none;
  background: transparent;
  color: white;
  font-family: 'Manrope', sans-serif;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: -.4px;
}

.brand-symbol {
  display: flex;
  width: 25px;
  height: 25px;
}

.brand-symbol svg {
  width: 100%;
  height: 100%;
}

.brand-light {
  font-weight: 400;
  opacity: .8;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 34px;
}

.nav-links button {
  position: relative;
  background: transparent;
  border: none;
  color: rgba(255,255,255,.76);
  font-size: 11px;
  font-weight: 600;
  padding: 10px 0;
  transition: color .2s;
}

.nav-links button:hover,
.nav-links button.active {
  color: white;
}

.nav-links button.active::after {
  content: '';
  position: absolute;
  height: 2px;
  bottom: 2px;
  left: 0;
  right: 0;
  background: rgba(255,255,255,.85);
  border-radius: 5px;
}

.nav-cta {
  background: rgba(255,255,255,.88);
  border: 1px solid rgba(255,255,255,.5);
  color: #426486;
  border-radius: 25px;
  padding: 10px 17px;
  font-size: 10px;
  font-weight: 700;
  transition: .2s;
}

.nav-cta span {
  margin-left: 7px;
}

.nav-cta:hover {
  background: white;
  transform: translateY(-1px);
}

/* HERO */

.hero-section {
  min-height: 580px;
  max-width: 1400px;
  margin: auto;
  padding: 105px 7% 25px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: white;
}

.hero-content {
  max-width: 700px;
  text-align: center;
  margin: 0 auto;
}

.hero-eyebrow {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 9px;
  color: rgba(255,255,255,.82);
  font-size: 9px;
  letter-spacing: 2px;
  font-weight: 700;
  margin-bottom: 25px;
}

.eyebrow-line {
  width: 24px;
  height: 1px;
  background: rgba(255,255,255,.8);
}

.hero-content h1 {
  font-family: 'Manrope', sans-serif;
  font-size: clamp(38px, 5.2vw, 65px);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -2.5px;
  margin: 0;
  text-shadow: 0 3px 22px rgba(21,45,75,.14);
}

.hero-content h1 span {
  display: block;
  font-weight: 500;
}

.hero-description {
  max-width: 510px;
  margin: 22px auto 28px;
  color: rgba(255,255,255,.88);
  font-size: 13px;
  line-height: 1.9;
}

.hero-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.primary-button,
.secondary-button {
  border-radius: 30px;
  padding: 13px 21px;
  font-size: 11px;
  font-weight: 700;
  transition: .2s;
}

.primary-button {
  background: rgba(255,255,255,.94);
  color: #426789;
  border: 1px solid white;
  box-shadow: 0 5px 20px rgba(20,45,75,.12);
}

.primary-button:hover {
  background: white;
  transform: translateY(-2px);
}

.primary-button span {
  margin-left: 10px;
}

.secondary-button {
  background: rgba(255,255,255,.10);
  border: 1px solid rgba(255,255,255,.48);
  color: white;
  backdrop-filter: blur(10px);
}

.secondary-button:hover {
  background: rgba(255,255,255,.2);
}

.hero-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 28px;
  font-size: 9px;
  color: rgba(255,255,255,.78);
}

.status-dot,
.online-indicator {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #83d5ae;
  flex-shrink: 0;
}

.status-dot.offline,
.online-indicator.offline {
  background: #d6a77c;
}

.hero-bottom {
  display: flex;
  justify-content: space-between;
  color: rgba(255,255,255,.7);
  font-size: 8px;
  font-weight: 600;
  letter-spacing: 1.5px;
}

/* INTRODUCTION */

.intro-section {
  max-width: 1280px;
  margin: 25px auto;
  padding: 45px 7%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 50px;
  color: white;
}

.section-label {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1.8px;
  color: #6f91b2;
}

.intro-section .section-label {
  color: rgba(255,255,255,.78);
}

.intro-left h2,
.closing-section h2 {
  font-family: 'Manrope', sans-serif;
  font-size: clamp(28px, 4vw, 43px);
  line-height: 1.2;
  letter-spacing: -1.5px;
  margin: 15px 0 0;
}

.intro-left h2 span,
.closing-section h2 span {
  display: block;
  font-weight: 400;
  color: rgba(255,255,255,.8);
}

.intro-right {
  padding-top: 15px;
}

.intro-right p {
  max-width: 470px;
  color: rgba(255,255,255,.85);
  font-size: 12px;
  line-height: 2;
}

.intro-right button {
  background: transparent;
  border: none;
  padding: 10px 0;
  color: white;
  font-size: 11px;
  font-weight: 700;
}

.intro-right button span {
  margin-left: 8px;
}

/* EXPLORE GLASS PANEL */

.explore-section {
  max-width: 1280px;
  margin: 25px auto 50px;
  padding: 42px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(247,251,255,.88);
  backdrop-filter: blur(24px) saturate(120%);
  -webkit-backdrop-filter: blur(24px) saturate(120%);
  box-shadow: 0 20px 70px rgba(16,42,75,.17);
  scroll-margin-top: 90px;
}

.explore-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 25px;
  margin-bottom: 30px;
}

.explore-heading h2 {
  font-family: 'Manrope', sans-serif;
  color: #2e4967;
  font-size: clamp(24px, 3vw, 34px);
  letter-spacing: -1.1px;
  margin: 10px 0;
}

.explore-heading h2 span {
  font-weight: 400;
  color: #7894b0;
}

.explore-heading p {
  color: #8193a8;
  font-size: 12px;
  line-height: 1.8;
  margin: 0;
}

.explore-ask {
  flex-shrink: 0;
  background: #426b95;
  color: white;
  border: 1px solid #426b95;
  border-radius: 25px;
  padding: 12px 18px;
  font-size: 10px;
  font-weight: 700;
  transition: .2s;
}

.explore-ask:hover {
  background: #345779;
  transform: translateY(-2px);
}

.explore-ask span {
  margin-left: 8px;
}

/* FEATURE CARDS */

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.feature-card {
  min-width: 0;
  padding: 22px;
  min-height: 215px;
  background: rgba(255,255,255,.75);
  border: 1px solid rgba(209,222,237,.75);
  border-radius: 11px;
  transition:
    transform .2s,
    box-shadow .2s,
    border-color .2s;
}

.feature-card:hover {
  transform: translateY(-3px);
  border-color: #b8cde1;
  box-shadow: 0 10px 28px rgba(43,77,112,.08);
}

.feature-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.feature-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  background: #edf3fa;
  color: #557a9e;
  border-radius: 9px;
}

.feature-icon svg {
  width: 21px;
  height: 21px;
}

.feature-number {
  color: #a3b3c4;
  font-family: 'Manrope', sans-serif;
  font-size: 12px;
  font-weight: 700;
}

.feature-category {
  color: #839ab2;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 1.2px;
}

.feature-card h3 {
  color: #3b5775;
  font-family: 'Manrope', sans-serif;
  font-size: 15px;
  margin: 9px 0;
}

.feature-card p {
  color: #8293a6;
  font-size: 10px;
  line-height: 1.8;
  margin: 0 0 16px;
  min-height: 55px;
}

.feature-link {
  background: transparent;
  border: none;
  padding: 0;
  color: #527ba3;
  font-size: 10px;
  font-weight: 700;
}

.feature-link span {
  margin-left: 7px;
}

.feature-link:hover {
  color: #294d73;
}

.explore-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 28px;
  padding-top: 19px;
  border-top: 1px solid #e7edf4;
  color: #9aaabd;
  font-size: 8px;
  letter-spacing: 1px;
}

.explore-bottom button {
  background: transparent;
  border: none;
  color: #557b9f;
  font-size: 10px;
  font-weight: 700;
}

.explore-bottom button span {
  margin-left: 7px;
}

/* CLOSING SECTION */

.closing-section {
  padding: 70px 20px 80px;
  text-align: center;
  color: white;
}

.closing-section .section-label {
  color: rgba(255,255,255,.75);
}

.closing-section h2 {
  max-width: 700px;
  margin: 17px auto 25px;
  font-size: clamp(27px, 4vw, 42px);
}

.closing-section .primary-button {
  margin-top: 5px;
}

/* FOOTER */

.footer {
  min-height: 75px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  padding: 20px 6%;
  background: rgba(22,48,76,.32);
  border-top: 1px solid rgba(255,255,255,.16);
  color: rgba(255,255,255,.8);
  font-size: 9px;
  backdrop-filter: blur(15px);
}

.footer-brand {
  font-family: 'Manrope', sans-serif;
  font-weight: 800;
  font-size: 12px;
  color: white;
}

.footer-brand span {
  font-weight: 400;
}

.footer-copy {
  letter-spacing: 1px;
}

/* FLOATING CHAT LAUNCHER */

.floating-chat-launcher {
  position: fixed;
  z-index: 1000;
  right: 26px;
  bottom: 25px;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 16px;
  border: 1px solid rgba(255,255,255,.8);
  border-radius: 12px;
  background: rgba(255,255,255,.91);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 8px 35px rgba(19,45,75,.2);
  color: #3d5b7c;
  transition: .2s;
}

.floating-chat-launcher:hover {
  transform: translateY(-3px);
  background: white;
  box-shadow: 0 12px 38px rgba(19,45,75,.25);
}

.launcher-icon {
  display: grid;
  place-items: center;
  width: 37px;
  height: 37px;
  border-radius: 9px;
  background: #eaf1f8;
  color: #52789e;
}

.launcher-icon svg {
  width: 23px;
  height: 23px;
}

.launcher-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.launcher-text strong {
  font-size: 11px;
  font-weight: 700;
}

.launcher-text small {
  font-size: 9px;
  color: #899bb0;
}

.launcher-arrow {
  margin-left: 9px;
  color: #6485a7;
}

/* CHAT DRAWER */

.floating-chat-panel {
  position: fixed;
  z-index: 1001;
  right: 25px;
  bottom: 25px;
  width: min(420px, calc(100vw - 35px));
  height: min(610px, calc(100dvh - 50px));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(255,255,255,.96);
  border: 1px solid rgba(255,255,255,.85);
  border-radius: 15px;
  box-shadow: 0 18px 65px rgba(16,42,75,.27);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
}

.floating-chat-header {
  min-height: 66px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
  border-bottom: 1px solid #e9eff5;
  background: rgba(255,255,255,.65);
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.chat-avatar,
.typing-avatar {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: #e9f0f8;
  color: #4e739a;
  font-family: 'Manrope', sans-serif;
  font-weight: 800;
  font-size: 12px;
}

.chat-heading-text {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.chat-heading-text strong {
  font-size: 11px;
  color: #385471;
}

.chat-heading-text > span {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  color: #91a0b1;
}

.online-indicator {
  width: 6px;
  height: 6px;
}

.floating-header-actions {
  display: flex;
  align-items: center;
  gap: 7px;
}

.icon-action {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 1px solid #e7edf4;
  background: white;
  border-radius: 8px;
  color: #71869d;
  transition: .2s;
}

.icon-action:hover {
  background: #edf3f9;
  color: #3c6288;
}

.icon-action svg {
  width: 16px;
  height: 16px;
}

/* CHAT MESSAGES */

.message-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
  scrollbar-width: thin;
  scrollbar-color: #d6e1ec transparent;
}

.message-list::-webkit-scrollbar {
  width: 4px;
}

.message-list::-webkit-scrollbar-thumb {
  background: #d6e1ec;
  border-radius: 10px;
}

.chat-date {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  color: #a2b0bf;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 1.2px;
  margin-bottom: 20px;
}

.chat-date span {
  width: 35px;
  height: 1px;
  background: #e8edf3;
}

/* SUGGESTIONS */

.chat-suggestions {
  margin: 15px 0 5px 38px;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.suggestion-label {
  font-size: 8px;
  font-weight: 800;
  color: #99a9bb;
  letter-spacing: 1px;
  margin-bottom: 3px;
}

.suggestion-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 9px 11px;
  border-radius: 7px;
  border: 1px solid #e6edf4;
  background: rgba(255,255,255,.8);
  color: #607b98;
  text-align: left;
  font-size: 9px;
  line-height: 1.5;
  transition: .2s;
}

.suggestion-chip:hover {
  background: #edf3f9;
  border-color: #cbd9e8;
}

.suggestion-chip span {
  flex-shrink: 0;
  color: #7695b3;
}

/* TYPING INDICATOR */

.typing-row {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 12px 0;
}

.typing-avatar {
  width: 27px;
  height: 27px;
  font-size: 10px;
}

.typing-bubble {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #f0f4f8;
  border-radius: 10px;
  padding: 11px 13px;
}

.typing-dot {
  width: 5px;
  height: 5px;
  background: #8097b0;
  border-radius: 50%;
  animation: typing 1s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
  animation-delay: .15s;
}

.typing-dot:nth-child(3) {
  animation-delay: .3s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: .45;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

/* COMPOSER */

.composer {
  margin: 0 13px;
  padding: 8px 11px 9px;
  border: 1px solid #dce6ef;
  border-radius: 11px;
  background: rgba(255,255,255,.95);
  box-shadow: 0 3px 12px rgba(37,68,102,.04);
  transition: border-color .2s;
}

.composer:focus-within {
  border-color: #a8bfd8;
}

.composer textarea {
  width: 100%;
  min-height: 40px;
  max-height: 100px;
  display: block;
  padding: 10px 2px;
  resize: vertical;
  outline: none;
  border: none;
  background: transparent;
  color: #385471;
  font-size: 11px;
  line-height: 1.7;
}

.composer textarea::placeholder {
  color: #a2b0bf;
}

.composer textarea:disabled {
  opacity: .6;
}

.composer-bottom {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-height: 32px;
}

.composer-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mic-button,
.send-button {
  width: 31px;
  height: 31px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  transition: .2s;
}

.mic-button {
  border: 1px solid #e4ebf3;
  background: #f6f9fc;
  color: #6684a4;
}

.mic-button:hover {
  background: #eaf1f8;
}

.mic-button svg,
.send-button svg {
  width: 17px;
  height: 17px;
}

.mic-button.recording {
  color: #b65d5d;
  background: #fff0f0;
  border-color: #efcaca;
}

.send-button {
  border: none;
  color: white;
  background: #4b7199;
}

.send-button:hover:not(:disabled) {
  background: #355a80;
}

.send-button:disabled,
.mic-button:disabled {
  opacity: .4;
  cursor: not-allowed;
}

/* VOICE FEEDBACK */

.voice-feedback {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 15px 8px;
  padding: 8px 11px;
  border-radius: 7px;
  background: #f1f5fa;
  color: #63809f;
  font-size: 10px;
}

.voice-pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #bb6e6e;
  box-shadow: 0 0 0 4px rgba(187,110,110,.12);
  animation: pulse 1.3s infinite;
}

.voice-feedback button {
  margin-left: auto;
  border: none;
  background: transparent;
  color: #527ba3;
  font-size: 10px;
  font-weight: 700;
}

@keyframes pulse {
  50% {
    box-shadow: 0 0 0 7px rgba(187,110,110,0);
  }
}

.inline-error {
  margin: 7px 15px;
  color: #ad6666;
  font-size: 9px;
  line-height: 1.6;
}

.connection-error {
  padding: 7px 9px;
  background: #fff5f3;
  border-radius: 6px;
}

.chat-disclaimer {
  flex-shrink: 0;
  padding: 10px 8px 12px;
  text-align: center;
  color: #a0acba;
  font-size: 8px;
}

/* TRANSITIONS */

.chat-drawer-enter-active,
.chat-drawer-leave-active,
.launcher-transition-enter-active,
.launcher-transition-leave-active {
  transition:
    opacity .22s ease,
    transform .22s ease;
}

.chat-drawer-enter-from,
.chat-drawer-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(.98);
}

.launcher-transition-enter-from,
.launcher-transition-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* TABLET */

@media (max-width: 900px) {
  .explore-section {
    margin-left: 20px;
    margin-right: 20px;
    padding: 30px;
  }

  .feature-grid {
    grid-template-columns: repeat(2, minmax(0,1fr));
  }

  .hero-section {
    min-height: 520px;
  }

  .intro-section {
    gap: 25px;
  }
}

/* MOBILE */

@media (max-width: 600px) {
  .navbar {
    padding: 0 17px;
  }

  .nav-inner {
    min-height: 62px;
    gap: 8px;
  }

  .brand {
    font-size: 11px;
    gap: 5px;
  }

  .brand-symbol {
    width: 21px;
    height: 21px;
  }

  .nav-links {
    gap: 13px;
  }

  .nav-links button {
    font-size: 9px;
  }

  .nav-cta {
    padding: 9px 10px;
    font-size: 8px;
  }

  .nav-cta span {
    margin-left: 3px;
  }

  .hero-section {
    min-height: 530px;
    padding: 100px 20px 22px;
  }

  .hero-eyebrow {
    font-size: 7px;
    letter-spacing: 1.3px;
    margin-bottom: 20px;
  }

  .hero-content h1 {
    font-size: clamp(34px, 9vw, 46px);
    letter-spacing: -1.7px;
  }

  .hero-description {
    font-size: 11px;
    margin: 18px auto 24px;
  }

  .hero-bottom {
    font-size: 6px;
    letter-spacing: .7px;
    gap: 10px;
  }

  .intro-section {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 40px 24px;
    margin: 10px auto;
  }

  .intro-left h2 {
    font-size: 33px;
  }

  .intro-right {
    padding-top: 0;
  }

  .intro-right p {
    font-size: 11px;
  }

  .explore-section {
    margin: 12px;
    padding: 22px 15px;
    border-radius: 13px;
  }

  .explore-heading {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 22px;
  }

  .explore-heading h2 {
    font-size: 25px;
  }

  .explore-heading p {
    font-size: 10px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .feature-card {
    min-height: auto;
    padding: 17px;
  }

  .feature-card p {
    min-height: 0;
  }

  .feature-card-top {
    margin-bottom: 13px;
  }

  .explore-bottom {
    font-size: 7px;
  }

  .closing-section {
    padding: 55px 20px 65px;
  }

  .closing-section h2 {
    font-size: 29px;
  }

  .footer {
    justify-content: center;
    text-align: center;
    padding: 20px;
  }

  .footer > * {
    width: 100%;
  }

  /* MOBILE CHAT */

  .floating-chat-launcher {
    right: 14px;
    bottom: 15px;
    padding: 10px 13px;
  }

  .floating-chat-panel {
    inset: 0;
    width: 100%;
    height: 100%;
    max-height: 100dvh;
    border: none;
    border-radius: 0;
    background: rgba(255,255,255,.98);
  }

  .floating-chat-header {
    min-height: calc(65px + env(safe-area-inset-top));
    padding:
      env(safe-area-inset-top)
      15px
      0;
  }

  .message-list {
    padding: 17px 13px;
  }

  .floating-composer {
    margin: 0 12px;
    padding: 8px 11px;
  }

  .floating-composer textarea {
    height: 43px;
    min-height: 43px;
    padding: 10px 2px;
    resize: none;
    line-height: 22px;
  }

  .floating-composer .composer-bottom {
    min-height: 32px;
  }

  .floating-chat-panel .chat-disclaimer {
    padding-bottom:
      max(12px, env(safe-area-inset-bottom));
  }
}

/* SMALL MOBILE */

@media (max-width: 360px) {
  .nav-links {
    gap: 9px;
  }

  .nav-links button {
    font-size: 8px;
  }

  .nav-cta {
    font-size: 7px;
    padding: 8px;
  }

  .hero-content h1 {
    font-size: 33px;
  }
}

/* REDUCED MOTION */

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
</style>
