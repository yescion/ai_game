/**
 * Top bar with game info and controls
 */
import { useGameStore } from '../store/gameStore'
import './TopBar.css'

export function TopBar() {
  const { time, isConnected, globalResources, world } = useGameStore()

  // 🌦️ 天气图标
  const getWeatherIcon = (weather: string) => {
    switch (weather) {
      case 'clear':
        return '☀️'
      case 'cloudy':
        return '☁️'
      case 'rain':
        return '🌧️'
      case 'storm':
        return '⛈️'
      default:
        return '🌤️'
    }
  }

  const getWeatherName = (weather: string) => {
    switch (weather) {
      case 'clear':
        return '晴天'
      case 'cloudy':
        return '阴天'
      case 'rain':
        return '雨天'
      case 'storm':
        return '暴风雨'
      default:
        return weather
    }
  }

  return (
    <div className="top-bar">
      <div className="game-title">
        <span className="icon">🌾</span>
        <span>原始平原模拟</span>
      </div>

      {time && (
        <div className="game-info">
          <span className="info-item">
            📅 第{time.day}天
          </span>
          <span className="info-item">
            ⏰ {String(time.hour).padStart(2, '0')}:{String(Math.floor(time.minute)).padStart(2, '0')}
          </span>
          <span className="info-item">
            🌸 {time.season}
          </span>
          {world && world.weather && (
            <span className="info-item weather-info">
              {getWeatherIcon(world.weather)} {getWeatherName(world.weather)}
            </span>
          )}
        </div>
      )}

      <div className="resources">
        <span className="resource-item">🌳 {globalResources?.wood || 0}</span>
        <span className="resource-item">⛰️ {globalResources?.stone || 0}</span>
        <span className="resource-item">🍇 {globalResources?.berry || 0}</span>
      </div>

      <div className="connection-status">
        <div className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
        <span>{isConnected ? '已连接' : '未连接'}</span>
      </div>
    </div>
  )
}

