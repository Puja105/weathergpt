
const WEATHER_CODES = {
  0: 'Clear sky',
  1: 'Mainly clear',
  2: 'Partly cloudy',
  3: 'Overcast',
  45: 'Foggy',
  48: 'Freezing fog',
  51: 'Light drizzle',
  53: 'Drizzle',
  55: 'Heavy drizzle',
  61: 'Light rain',
  63: 'Moderate rain',
  65: 'Heavy rain',
  71: 'Light snowfall',
  73: 'Snowfall',
  75: 'Heavy snowfall',
  80: 'Rain showers',
  81: 'Moderate rain showers',
  82: 'Violent rain showers',
  95: 'Thunderstorm',
  96: 'Thunderstorm with hail',
  99: 'Severe thunderstorm'
}

export function getWeatherDescription(code) {
  return WEATHER_CODES[Number(code)] || 'Weather conditions'
}

export function getWeatherTheme(code) {
  code = Number(code)

  if ([95, 96, 99].includes(code)) return 'storm'
  if ([61, 63, 65, 80, 81, 82].includes(code)) return 'rain'
  if ([51, 53, 55].includes(code)) return 'drizzle'
  if ([45, 48].includes(code)) return 'fog'
  if ([71, 73, 75].includes(code)) return 'snow'
  if ([0, 1].includes(code)) return 'sunny'

  return 'cloudy'
}

export function generateWeatherAlerts(current, hourly) {
  const alerts = []

  if (!current) return alerts

  const code = Number(current.weather_code)
  const temperature = Number(current.temperature_c)
  const wind = Number(current.wind_speed_kmh)

  const upcoming = (hourly || []).slice(0, 6)

  const hasRain = upcoming.some(item =>
    Number(item.rain_mm || 0) >= 0.5 ||
    Number(item.precipitation_mm || 0) >= 1
  )

  const hasHeavyRain = upcoming.some(item =>
    Number(item.rain_mm || 0) >= 7 ||
    Number(item.precipitation_mm || 0) >= 10
  )

  if ([95, 96, 99].includes(code) ||
      upcoming.some(item => [95, 96, 99].includes(Number(item.weather_code)))) {
    alerts.push({
      id: 'storm',
      severity: 'danger',
      title: 'Thunderstorm alert',
      message: 'Thunderstorms are indicated in the available weather data. Avoid open areas and exposed locations.',
      theme: 'storm',
      icon: '⛈'
    })
  }

  if (hasHeavyRain) {
    alerts.push({
      id: 'heavy-rain',
      severity: 'warning',
      title: 'Heavy rainfall expected',
      message: 'Heavy rainfall is indicated in the upcoming forecast. Plan your travel carefully.',
      theme: 'rain',
      icon: '🌧'
    })
  } else if (hasRain) {
    alerts.push({
      id: 'rain',
      severity: 'info',
      title: 'Rain reminder',
      message: 'Rain is expected in the upcoming hours. Carry an umbrella when heading out.',
      theme: 'rain',
      icon: '☔'
    })
  }

  if (temperature >= 35) {
    alerts.push({
      id: 'heat',
      severity: 'warning',
      title: 'High temperature',
      message: 'It is quite hot. Stay hydrated and avoid prolonged outdoor exposure.',
      theme: 'sunny',
      icon: '☀'
    })
  }

  if (wind >= 40) {
    alerts.push({
      id: 'wind',
      severity: 'warning',
      title: 'Strong winds',
      message: 'Strong winds are recorded. Take care around trees and unsecured outdoor objects.',
      theme: 'wind',
      icon: '💨'
    })
  }

  if ([45, 48].includes(code)) {
    alerts.push({
      id: 'fog',
      severity: 'info',
      title: 'Fog advisory',
      message: 'Foggy conditions are reported. Allow extra time while travelling and maintain visibility.',
      theme: 'fog',
      icon: '🌫'
    })
  }

  if (!alerts.length) {
    alerts.push({
      id: 'pleasant',
      severity: 'success',
      title: 'Weather looks comfortable',
      message: 'No major weather concerns were identified in the available forecast.',
      theme: getWeatherTheme(code),
      icon: '☀'
    })
  }

  return alerts
}

export function getBestTimeToGoOut(hourly) {
  if (!hourly || !hourly.length) return null

  const suitable = hourly.filter(item => {
    const rain = Number(item.rain_mm || 0)
    const precipitation = Number(item.precipitation_mm || 0)
    const temperature = Number(item.temperature_c)
    const wind = Number(item.wind_speed_kmh)

    return (
      rain < 0.5 &&
      precipitation < 1 &&
      temperature >= 18 &&
      temperature <= 34 &&
      wind < 35
    )
  })

  if (!suitable.length) {
    return {
      time: 'No suitable window identified',
      message: 'Check the forecast again before planning outdoor activities.'
    }
  }

  const first = suitable[0]

  const date = new Date(first.forecast_time)

  return {
    time: date.toLocaleTimeString([], {
      hour: 'numeric',
      minute: '2-digit'
    }),
    message: 'This hour has relatively favourable conditions for outdoor activities.'
  }
}
