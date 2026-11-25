
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import {
  getWeatherDescription,
  getWeatherTheme,
  generateWeatherAlerts,
  getBestTimeToGoOut
} from '../utils/weatherInsights'

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`
).replace(/\/+$/, '')

const loading = ref(false)
const error = ref('')
const location = ref(null)
const current = ref(null)
const hourly = ref([])
const daily = ref([])
const alerts = ref([])
const notificationsEnabled = ref(
  typeof Notification !== 'undefined' &&
  Notification.permission === 'granted'
)

const lastUpdated = ref(null)
const refreshTimer = ref(null)
const notifiedAlerts = new Set()

const theme = computed(() =>
  getWeatherTheme(current.value?.weather_code)
)

const weatherDescription = computed(() =>
  getWeatherDescription(current.value?.weather_code)
)

const bestTime = computed(() =>
  getBestTimeToGoOut(hourly.value)
)

const temperature = computed(() =>
  current.value?.temperature_c != null
    ? Math.round(Number(current.value.temperature_c))
    : '--'
)

const updatedLabel = computed(() => {
  if (!lastUpdated.value) return ''

  return new Date(lastUpdated.value).toLocaleString([], {
    dateStyle: 'medium',
    timeStyle: 'short'
  })
})

function requestLocation() {
  error.value = ''

  if (!navigator.geolocation) {
    error.value = 'Location access is not supported by this browser.'
    return
  }

  loading.value = true

  navigator.geolocation.getCurrentPosition(
    async position => {
      try {
        const { latitude, longitude } = position.coords

        const response = await fetch(
          `${API_BASE}/locations/nearest?latitude=${latitude}&longitude=${longitude}`
        )

        if (!response.ok) {
          throw new Error('Could not find a supported nearby location.')
        }

        location.value = await response.json()

        await loadWeather()
      } catch (err) {
        error.value = err.message || 'Unable to retrieve location weather.'
      } finally {
        loading.value = false
      }
    },
    err => {
      loading.value = false

      if (err.code === 1) {
        error.value = 'Location permission was denied. Please enable it in your browser settings.'
      } else if (err.code === 2) {
        error.value = 'Your current location could not be determined.'
      } else {
        error.value = 'Location request timed out. Please try again.'
      }
    },
    {
      enableHighAccuracy: false,
      timeout: 15000,
      maximumAge: 300000
    }
  )
}

async function fetchJSON(url) {
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`Weather API returned ${response.status}`)
  }

  return response.json()
}

async function loadWeather() {
  if (!location.value) return

  loading.value = true
  error.value = ''

  try {
    const city = encodeURIComponent(location.value.city)

    const [currentData, hourlyData, dailyData] = await Promise.all([
      fetchJSON(`${API_BASE}/weather/current/${city}`),
      fetchJSON(`${API_BASE}/forecast/hourly/${city}?hours=24`),
      fetchJSON(`${API_BASE}/forecast/daily/${city}?days=7`)
    ])

    current.value = currentData
    hourly.value = hourlyData
    daily.value = dailyData

    lastUpdated.value = currentData.recorded_at || new Date().toISOString()

    alerts.value = generateWeatherAlerts(
      currentData,
      hourlyData
    )

    sendBrowserAlerts()
  } catch (err) {
    console.error('Weather dashboard error:', err)
    error.value = 'Unable to load weather information. Please try again.'
  } finally {
    loading.value = false
  }
}

async function enableNotifications() {
  if (!('Notification' in window)) {
    error.value = 'Browser notifications are not supported.'
    return
  }

  const permission = await Notification.requestPermission()

  notificationsEnabled.value = permission === 'granted'

  if (notificationsEnabled.value) {
    new Notification('WeatherGPT notifications enabled', {
      body: 'You will receive weather reminders while this page is active.',
      icon: '/favicon.ico'
    })
  }
}

function sendBrowserAlerts() {
  if (!notificationsEnabled.value || !current.value) return

  alerts.value.forEach(alert => {
    const key = `${location.value?.location_id}-${alert.id}`

    if (notifiedAlerts.has(key)) return

    notifiedAlerts.add(key)

    new Notification(`WeatherGPT: ${alert.title}`, {
      body: alert.message,
      icon: '/favicon.ico',
      tag: key
    })
  })
}

function formatDay(date) {
  return new Date(date).toLocaleDateString([], {
    weekday: 'short'
  })
}

function formatHour(date) {
  return new Date(date).toLocaleTimeString([], {
    hour: 'numeric'
  })
}

function refreshWeather() {
  if (location.value) {
    loadWeather()
  }
}

onMounted(() => {
  if (location.value) {
    loadWeather()
  }

  refreshTimer.value = window.setInterval(
    refreshWeather,
    3 * 60 * 60 * 1000
  )
})

onBeforeUnmount(() => {
  if (refreshTimer.value) {
    window.clearInterval(refreshTimer.value)
  }
})
</script>

<template>
  <section class="weather-dashboard" id="weather-dashboard">
    <div class="dashboard-heading">
      <div>
        <span class="dashboard-label">PERSONALISED WEATHER</span>
        <h2>Your weather, <span>your location.</span></h2>
        <p>Weather insights and practical reminders based on your location.</p>
      </div>

      <button
        class="location-button"
        @click="requestLocation"
        :disabled="loading"
      >
        {{ loading ? 'Finding location...' : 'Detect my location' }}
      </button>
    </div>

    <div v-if="error" class="weather-error">
      {{ error }}
    </div>

    <div v-if="location && current" class="weather-content">

      <div class="current-weather-card" :class="theme">
        <div class="current-top">
          <div>
            <span class="weather-overline">YOUR NEAREST SUPPORTED LOCATION</span>
            <h3>{{ location.city }}</h3>
            <p>{{ location.state }}, {{ location.country }}</p>
          </div>

          <div class="weather-symbol">
            <span v-if="theme === 'storm'">⛈</span>
            <span v-else-if="theme === 'rain' || theme === 'drizzle'">🌧</span>
            <span v-else-if="theme === 'sunny'">☀</span>
            <span v-else-if="theme === 'fog'">☁</span>
            <span v-else>☁</span>
          </div>
        </div>

        <div class="temperature-display">
          {{ temperature }}<span>°C</span>
        </div>

        <p class="weather-description">{{ weatherDescription }}</p>

        <div class="weather-metrics">
          <div>
            <span>Humidity</span>
            <strong>{{ current.humidity_percent ?? '--' }}%</strong>
          </div>

          <div>
            <span>Wind speed</span>
            <strong>{{ current.wind_speed_kmh ?? '--' }} km/h</strong>
          </div>

          <div>
            <span>Feels like</span>
            <strong>{{ current.apparent_temperature_c ?? '--' }}°C</strong>
          </div>
        </div>

        <div class="weather-updated">
          Data recorded: {{ updatedLabel }}
          <span>Nearest location: {{ location.distance_km }} km away</span>
        </div>
      </div>

      <div class="dashboard-section">
        <div class="section-heading">
          <div>
            <span class="dashboard-label">WEATHER ADVISORY</span>
            <h3>What should you prepare for?</h3>
          </div>

          <button
            class="notification-button"
            @click="enableNotifications"
            :disabled="notificationsEnabled"
          >
            {{ notificationsEnabled ? 'Notifications enabled' : 'Enable notifications' }}
          </button>
        </div>

        <div class="alert-grid">
          <article
            v-for="alert in alerts"
            :key="alert.id"
            class="alert-card"
            :class="alert.theme"
          >
            <div class="alert-icon">{{ alert.icon }}</div>
            <span class="alert-severity">{{ alert.severity }}</span>
            <h4>{{ alert.title }}</h4>
            <p>{{ alert.message }}</p>
          </article>
        </div>
      </div>

      <div class="dashboard-section">
        <div class="section-heading">
          <div>
            <span class="dashboard-label">LOOKING AHEAD</span>
            <h3>Next seven days</h3>
          </div>
        </div>

        <div class="daily-forecast">
          <article
            v-for="(day, index) in daily"
            :key="day.forecast_date"
            class="daily-card"
          >
            <span>{{ index === 0 ? 'Today' : formatDay(day.forecast_date) }}</span>

            <strong class="daily-weather">
              {{ getWeatherDescription(day.weather_code) }}
            </strong>

            <div class="daily-temperature">
              {{ Math.round(day.temperature_max_c) }}°
              <span>{{ Math.round(day.temperature_min_c) }}°</span>
            </div>

            <small>
              Rain: {{ day.rain_sum_mm ?? 0 }} mm
            </small>
          </article>
        </div>
      </div>

      <div class="best-time-card">
        <div>
          <span class="dashboard-label">PLAN YOUR DAY</span>
          <h3>Best time to go out</h3>
          <p>{{ bestTime?.message || 'Forecast information is unavailable.' }}</p>
        </div>

        <strong>{{ bestTime?.time || '--' }}</strong>
      </div>

      <div class="dashboard-footer">
        <span>Weather information is based on the latest available database update.</span>
        <button @click="loadWeather" :disabled="loading">
          Refresh weather
        </button>
      </div>
    </div>

    <div v-else-if="!loading && !error" class="location-placeholder">
      <div class="placeholder-symbol">⌖</div>
      <h3>Weather starts with your location.</h3>
      <p>Allow location access to discover the nearest supported weather location and personalised updates.</p>
      <button @click="requestLocation">Find my location</button>
    </div>

  </section>
</template>

<style scoped>
.weather-dashboard {
  width: min(1180px, calc(100% - 40px));
  margin: 70px auto;
  color: #172b42;
}

.dashboard-heading,
.section-heading,
.current-top,
.weather-updated,
.dashboard-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.dashboard-heading {
  margin-bottom: 30px;
}

.dashboard-label,
.weather-overline {
  font-size: 10px;
  letter-spacing: 2px;
  font-weight: 700;
  color: #64809a;
}

.dashboard-heading h2 {
  font-size: clamp(28px, 4vw, 42px);
  margin: 10px 0;
  letter-spacing: -1.5px;
}

.dashboard-heading h2 span {
  color: #397aa7;
}

.dashboard-heading p,
.location-placeholder p {
  color: #718399;
  line-height: 1.7;
}

.location-button,
.location-placeholder button {
  background: #193d5a;
  color: white;
  border: 0;
  padding: 14px 22px;
  border-radius: 8px;
  cursor: pointer;
}

.weather-error {
  padding: 15px;
  border-radius: 9px;
  background: #fff0ed;
  color: #a83e32;
  margin-bottom: 20px;
}

.current-weather-card {
  border-radius: 18px;
  padding: 32px;
  color: white;
  background: linear-gradient(125deg, #244c72, #477d9f);
  box-shadow: 0 15px 45px #294e6b20;
}

.current-weather-card.sunny {
  background: linear-gradient(125deg, #b66e30, #e6b56d);
}

.current-weather-card.rain,
.current-weather-card.drizzle {
  background: linear-gradient(125deg, #203e5b, #456c89);
}

.current-weather-card.storm {
  background: linear-gradient(125deg, #20243d, #514d70);
}

.current-weather-card.fog,
.current-weather-card.cloudy {
  background: linear-gradient(125deg, #536d7d, #91a4af);
}

.current-weather-card.snow {
  background: linear-gradient(125deg, #647e99, #a8c5d9);
}

.current-weather-card h3 {
  font-size: 30px;
  margin: 10px 0 3px;
}

.current-weather-card p {
  margin: 0;
  color: #e2edf5;
}

.weather-overline {
  color: #d5e3ef;
}

.weather-symbol {
  font-size: 60px;
}

.temperature-display {
  font-size: 76px;
  font-weight: 300;
  margin-top: 20px;
  letter-spacing: -4px;
}

.temperature-display span {
  font-size: 32px;
  vertical-align: top;
}

.weather-description {
  font-size: 18px;
  margin-bottom: 26px !important;
}

.weather-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 45px;
  border-top: 1px solid #ffffff40;
  padding-top: 20px;
}

.weather-metrics div {
  display: grid;
  gap: 7px;
}

.weather-metrics span,
.weather-updated {
  color: #d5e3ef;
  font-size: 12px;
}

.weather-metrics strong {
  font-size: 17px;
}

.weather-updated {
  margin-top: 25px;
  flex-wrap: wrap;
}

.dashboard-section {
  margin-top: 48px;
}

.section-heading {
  margin-bottom: 20px;
}

.section-heading h3,
.best-time-card h3 {
  font-size: 23px;
  margin: 8px 0;
}

.notification-button {
  border: 1px solid #d5e0e9;
  padding: 11px 16px;
  background: white;
  border-radius: 7px;
  cursor: pointer;
}

.alert-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.alert-card {
  min-height: 180px;
  border-radius: 13px;
  padding: 22px;
  color: white;
  background: linear-gradient(140deg, #385c78, #6289a5);
}

.alert-card.rain,
.alert-card.drizzle {
  background: linear-gradient(140deg, #203b59, #456f91);
}

.alert-card.storm {
  background: linear-gradient(140deg, #1b1d35, #514969);
}

.alert-card.sunny {
  background: linear-gradient(140deg, #a65c2e, #dfa65e);
}

.alert-card.fog {
  background: linear-gradient(140deg, #647986, #91a7b1);
}

.alert-card.wind {
  background: linear-gradient(140deg, #31566a, #638b98);
}

.alert-icon {
  font-size: 25px;
}

.alert-severity {
  display: block;
  text-transform: uppercase;
  font-size: 9px;
  letter-spacing: 1.5px;
  margin-top: 15px;
  opacity: .8;
}

.alert-card h4 {
  font-size: 17px;
  margin: 9px 0;
}

.alert-card p {
  font-size: 13px;
  line-height: 1.6;
  color: #f0f4f7;
}

.daily-forecast {
  display: grid;
  grid-template-columns: repeat(7, minmax(100px, 1fr));
  gap: 10px;
  overflow-x: auto;
}

.daily-card {
  padding: 18px 12px;
  min-width: 100px;
  border: 1px solid #e5eaf0;
  border-radius: 11px;
  background: #ffffffdc;
  display: flex;
  flex-direction: column;
  gap: 13px;
}

.daily-card > span {
  color: #728499;
  font-size: 13px;
}

.daily-weather {
  font-size: 12px;
  min-height: 32px;
}

.daily-temperature {
  font-size: 21px;
  font-weight: 700;
}

.daily-temperature span {
  font-size: 15px;
  font-weight: 400;
  color: #8192a1;
  margin-left: 5px;
}

.daily-card small {
  color: #718399;
}

.best-time-card {
  margin-top: 30px;
  background: #edf4f8;
  border: 1px solid #dce9f1;
  padding: 26px;
  border-radius: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.best-time-card p {
  color: #647c8f;
  font-size: 14px;
  line-height: 1.6;
}

.best-time-card > strong {
  font-size: 22px;
  color: #285b7b;
  white-space: nowrap;
}

.dashboard-footer {
  margin-top: 25px;
  color: #7c8c9a;
  font-size: 11px;
  flex-wrap: wrap;
}

.dashboard-footer button {
  background: none;
  border: 0;
  color: #356b8d;
  font-weight: 600;
  cursor: pointer;
}

.location-placeholder {
  padding: 55px 20px;
  text-align: center;
  border: 1px solid #e0e9ef;
  background: #ffffffd9;
  border-radius: 17px;
}

.placeholder-symbol {
  font-size: 42px;
  color: #397ba1;
}

.location-placeholder h3 {
  font-size: 23px;
}

.location-placeholder p {
  max-width: 510px;
  margin: 10px auto 22px;
}

button:disabled {
  opacity: .6;
  cursor: not-allowed;
}

@media (max-width: 760px) {
  .dashboard-heading,
  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .weather-dashboard {
    width: calc(100% - 28px);
    margin: 45px auto;
  }

  .current-weather-card {
    padding: 23px;
  }

  .weather-metrics {
    gap: 22px;
  }

  .temperature-display {
    font-size: 64px;
  }

  .best-time-card {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
