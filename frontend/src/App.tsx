/**
 * Main App component
 */
import { useEffect, useState } from 'react'
import { socketService } from './services/socketService'
import { useGameStore } from './store/gameStore'
import { TopBar } from './components/TopBar'
import { GameCanvas } from './components/GameCanvas'
import { EventTimeline } from './components/EventTimeline'
import { NPCPanel } from './components/NPCPanel'
import { ObjectInfoPanel } from './components/ObjectInfoPanel'  // 🔥 新增
import { GodConsole } from './components/GodConsole'  // 🔮 上帝指令控制台
import { AdminDashboard } from './components/AdminDashboard'  // 📊 管理面板
import { HelpModal } from './components/HelpModal'  // ❓ 帮助模态框
import { LoadingScreen } from './components/LoadingScreen'  // 🚀 加载检测屏幕
import './App.css'

function App() {
  const { error } = useGameStore()
  const [showAdminDashboard, setShowAdminDashboard] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [isApiReady, setIsApiReady] = useState(false)  // 🚀 API检测状态

  // 🚀 API检测通过后才启动游戏
  const handleApiReady = () => {
    setIsApiReady(true)
  }

  useEffect(() => {
    // 🚀 只有API检测通过后才启动游戏连接
    if (!isApiReady) return

    // 🔥 延迟连接，等待React完全初始化（避免StrictMode重复创建）
    const timer = setTimeout(() => {
      console.log('🚀 Starting socket connection...')
      socketService.connect()
    }, 100)  // 延迟100ms

    // Cleanup on unmount
    return () => {
      clearTimeout(timer)
      // 🔥 仅在生产环境才真正断开（避免开发模式StrictMode重复断开）
      if (import.meta.env.PROD) {
        socketService.disconnect()
      }
    }
  }, [isApiReady])

  // 🚀 API检测中，显示加载屏幕
  if (!isApiReady) {
    return <LoadingScreen onReady={handleApiReady} />
  }

  return (
    <div className="app">
      <TopBar />
      
      <div className="main-content">
        <EventTimeline />
        
        <div className="game-area">
          <GameCanvas />
          {error && (
            <div className="error-overlay">
              <div className="error-message">
                ⚠️ {error}
              </div>
            </div>
          )}
        </div>
        
        <NPCPanel />
      </div>
      
      {/* 🔥 物体信息面板 */}
      <ObjectInfoPanel />
      
      {/* 🔮 上帝指令控制台 */}
      <GodConsole />
      
      {/* 📊 管理面板 */}
      {showAdminDashboard && (
        <AdminDashboard onClose={() => setShowAdminDashboard(false)} />
      )}
      
      {/* ❓ 帮助模态框 */}
      {showHelp && (
        <HelpModal onClose={() => setShowHelp(false)} />
      )}
      
      {/* 右下角功能按钮组 */}
      <div className="floating-buttons">
        {/* ❓ 帮助按钮 */}
        <button 
          className="help-btn" 
          onClick={() => setShowHelp(true)}
          title="操作帮助"
        >
          ❓
        </button>
        
        {/* 📊 管理面板按钮 */}
        <button 
          className="admin-dashboard-btn" 
          onClick={() => setShowAdminDashboard(true)}
          title="打开管理面板"
        >
          📊
        </button>
      </div>
    </div>
  )
}

export default App

