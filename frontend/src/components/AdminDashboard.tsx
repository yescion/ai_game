/**
 * Admin Dashboard - 游戏管理面板
 * 显示所有游戏数据的详细信息
 */
import { useState, useEffect } from 'react'
import './AdminDashboard.css'

interface AdminData {
  timestamp: string
  game_time: number
  time: {
    day: number
    hour: number
    minute: number
    season: string
  }
  weather: {
    current: string
    last_check_time: number
    next_check_time: number
    check_interval: number
    time_until_next_check: number
    countdown_minutes: number
    countdown_seconds: number
  }
  world_size: {
    width: number
    height: number
  }
  npcs: any[]
  beasts: any[]
  buildings: any[]
  resources: any[]
  global_resources: Record<string, number>
  events: any[]
  conversations: any[]
  config: {
    tick_interval: number
    time_scale: number
    npc_decision_interval: number
    beast_decision_interval: number
    is_running: boolean
    game_started: boolean
    waiting_for_client: boolean
  }
  statistics: {
    total_npcs: number
    alive_npcs: number
    total_beasts: number
    total_buildings: number
    completed_buildings: number
    total_resources: number
    total_events: number
    active_conversations: number
  }
}

interface AdminDashboardProps {
  onClose: () => void
}

export function AdminDashboard({ onClose }: AdminDashboardProps) {
  const [data, setData] = useState<AdminData | null>(null)
  const [selectedTab, setSelectedTab] = useState<'overview' | 'npcs' | 'beasts' | 'resources' | 'buildings' | 'events' | 'config'>('overview')
  const [selectedNPC, setSelectedNPC] = useState<any>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [loading, setLoading] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/admin/dashboard')
      const result = await response.json()
      if (!result.error) {
        setData(result)
      }
    } catch (error) {
      console.error('Failed to fetch admin data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, 5000) // 每5秒刷新
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  if (!data) {
    return (
      <div className="admin-dashboard">
        <div className="admin-header">
          <h2>🎮 游戏管理面板</h2>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>
        <div className="admin-loading">加载中...</div>
      </div>
    )
  }

  const weatherEmoji: Record<string, string> = {
    clear: '☀️',
    cloudy: '☁️',
    rain: '🌧️',
    storm: '⛈️'
  }

  const weatherNames: Record<string, string> = {
    clear: '晴天',
    cloudy: '阴天',
    rain: '雨天',
    storm: '暴风雨'
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <div className="header-left">
          <h2>🎮 游戏管理面板</h2>
          <div className="header-info">
            <span className="time-display">⏰ {data.timestamp}</span>
            <span className="weather-display">
              {weatherEmoji[data.weather.current]} {weatherNames[data.weather.current]}
              <span className="weather-countdown">
                {' '}(变化: {data.weather.countdown_minutes}:{data.weather.countdown_seconds.toString().padStart(2, '0')})
              </span>
            </span>
            <span className={`status-indicator ${data.config.is_running ? 'running' : 'stopped'}`}>
              {data.config.is_running ? '🟢 运行中' : '🔴 已停止'}
            </span>
          </div>
        </div>
        <div className="header-right">
          <label className="auto-refresh">
            <input 
              type="checkbox" 
              checked={autoRefresh} 
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            自动刷新
          </label>
          <button onClick={fetchData} className="refresh-btn" disabled={loading}>
            {loading ? '⟳' : '🔄'} 刷新
          </button>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>
      </div>

      <div className="admin-tabs">
        <button 
          className={selectedTab === 'overview' ? 'active' : ''} 
          onClick={() => setSelectedTab('overview')}
        >
          📊 概览
        </button>
        <button 
          className={selectedTab === 'npcs' ? 'active' : ''} 
          onClick={() => setSelectedTab('npcs')}
        >
          👥 NPC ({data.statistics.alive_npcs}/{data.statistics.total_npcs})
        </button>
        <button 
          className={selectedTab === 'beasts' ? 'active' : ''} 
          onClick={() => setSelectedTab('beasts')}
        >
          🐺 野兽 ({data.statistics.total_beasts})
        </button>
        <button 
          className={selectedTab === 'resources' ? 'active' : ''} 
          onClick={() => setSelectedTab('resources')}
        >
          📦 资源 ({data.statistics.total_resources})
        </button>
        <button 
          className={selectedTab === 'buildings' ? 'active' : ''} 
          onClick={() => setSelectedTab('buildings')}
        >
          🏗️ 建筑 ({data.statistics.completed_buildings}/{data.statistics.total_buildings})
        </button>
        <button 
          className={selectedTab === 'events' ? 'active' : ''} 
          onClick={() => setSelectedTab('events')}
        >
          📜 事件 ({data.statistics.total_events})
        </button>
        <button 
          className={selectedTab === 'config' ? 'active' : ''} 
          onClick={() => setSelectedTab('config')}
        >
          ⚙️ 配置
        </button>
      </div>

      <div className="admin-content">
        {selectedTab === 'overview' && (
          <div className="overview-panel">
            <div className="stats-grid">
              <div className="stat-card">
                <h3>👥 NPC状态</h3>
                <div className="stat-value">{data.statistics.alive_npcs} / {data.statistics.total_npcs}</div>
                <div className="stat-label">存活 / 总数</div>
              </div>
              <div className="stat-card">
                <h3>🐺 野兽</h3>
                <div className="stat-value">{data.statistics.total_beasts}</div>
                <div className="stat-label">当前数量</div>
              </div>
              <div className="stat-card">
                <h3>🏗️ 建筑</h3>
                <div className="stat-value">{data.statistics.completed_buildings} / {data.statistics.total_buildings}</div>
                <div className="stat-label">完成 / 总数</div>
              </div>
              <div className="stat-card">
                <h3>📦 资源点</h3>
                <div className="stat-value">{data.statistics.total_resources}</div>
                <div className="stat-label">可采集</div>
              </div>
              <div className="stat-card">
                <h3>💬 对话</h3>
                <div className="stat-value">{data.statistics.active_conversations}</div>
                <div className="stat-label">进行中</div>
              </div>
              <div className="stat-card">
                <h3>📜 事件</h3>
                <div className="stat-value">{data.statistics.total_events}</div>
                <div className="stat-label">总计</div>
              </div>
            </div>

            <div className="resources-section">
              <h3>🌍 全局资源</h3>
              <div className="resource-list">
                {Object.entries(data.global_resources).map(([key, value]) => (
                  <div key={key} className="resource-item">
                    <span className="resource-name">{key}</span>
                    <span className="resource-value">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="world-info">
              <h3>🗺️ 世界信息</h3>
              <div className="info-grid">
                <div><strong>地图大小:</strong> {data.world_size.width} × {data.world_size.height}</div>
                <div><strong>季节:</strong> {data.time.season}</div>
                <div>
                  <strong>天气:</strong> {weatherEmoji[data.weather.current]} {weatherNames[data.weather.current]}
                  <div className="weather-info-detail">
                    <span className="weather-countdown-detail">
                      🕐 下次检查: {data.weather.countdown_minutes}分{data.weather.countdown_seconds}秒
                    </span>
                    <span className="weather-interval">检查间隔: {(data.weather.check_interval / 60).toFixed(0)}分钟</span>
                  </div>
                </div>
                <div><strong>游戏时间:</strong> Day {data.time.day}, {data.time.hour}:{Math.floor(data.time.minute).toString().padStart(2, '0')}</div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'npcs' && (
          <div className="npcs-panel">
            <div className="npc-list">
              {data.npcs.map((npc) => (
                <div 
                  key={npc.id} 
                  className={`npc-card ${selectedNPC?.id === npc.id ? 'selected' : ''} ${!npc.is_alive ? 'dead' : ''}`}
                  onClick={() => setSelectedNPC(npc)}
                >
                  <div className="npc-header">
                    <span className="npc-sprite">{npc.sprite}</span>
                    <span className="npc-name">{npc.name}</span>
                    {!npc.is_alive && <span className="dead-badge">💀</span>}
                  </div>
                  <div className="npc-status">
                    <div className="status-bar">
                      <span>❤️</span>
                      <div className="bar">
                        <div className="bar-fill health" style={{width: `${npc.attributes.health}%`}}></div>
                      </div>
                      <span>{Math.round(npc.attributes.health)}</span>
                    </div>
                    <div className="status-bar">
                      <span>🍖</span>
                      <div className="bar">
                        <div className="bar-fill hunger" style={{width: `${100 - npc.attributes.hunger}%`}}></div>
                      </div>
                      <span>{Math.round(npc.attributes.hunger)}</span>
                    </div>
                    <div className="status-bar">
                      <span>⚡</span>
                      <div className="bar">
                        <div className="bar-fill stamina" style={{width: `${npc.attributes.stamina}%`}}></div>
                      </div>
                      <span>{Math.round(npc.attributes.stamina)}</span>
                    </div>
                  </div>
                  <div className="npc-action">
                    <strong>行动:</strong> {npc.current_action || 'idle'}
                  </div>
                </div>
              ))}
            </div>

            {selectedNPC && (
              <div className="npc-details">
                <h3>{selectedNPC.sprite} {selectedNPC.name} - 详细信息</h3>
                
                <div className="detail-section">
                  <h4>📍 位置与状态</h4>
                  <div className="detail-content">
                    <p><strong>位置:</strong> ({selectedNPC.position.x.toFixed(1)}, {selectedNPC.position.y.toFixed(1)})</p>
                    <p><strong>方向:</strong> {selectedNPC.direction}</p>
                    <p><strong>状态:</strong> {selectedNPC.action_state}</p>
                    <p><strong>当前行动:</strong> {selectedNPC.current_action}</p>
                    {selectedNPC.action_target && <p><strong>行动目标:</strong> {selectedNPC.action_target}</p>}
                    {selectedNPC.current_todo && <p><strong>待办:</strong> {selectedNPC.current_todo}</p>}
                  </div>
                </div>

                <div className="detail-section">
                  <h4>🎭 角色</h4>
                  <div className="detail-content">
                    {selectedNPC.role ? (
                      <>
                        <p><strong>{selectedNPC.role.role}</strong></p>
                        <p>{selectedNPC.role.description}</p>
                      </>
                    ) : (
                      <p>无角色</p>
                    )}
                  </div>
                </div>

                <div className="detail-section">
                  <h4>💭 决策理由</h4>
                  <div className="detail-content">
                    <p>{selectedNPC.reasoning || '无'}</p>
                  </div>
                </div>

                <div className="detail-section">
                  <h4>🎒 物品栏</h4>
                  <div className="detail-content inventory">
                    {Object.entries(selectedNPC.inventory).length > 0 ? (
                      Object.entries(selectedNPC.inventory).map(([item, count]) => (
                        <div key={item} className="inventory-item">
                          <span>{item}</span>
                          <span className="count">×{count as number}</span>
                        </div>
                      ))
                    ) : (
                      <p>空</p>
                    )}
                  </div>
                </div>

                <div className="detail-section">
                  <h4>⚔️ 装备</h4>
                  <div className="detail-content equipment">
                    {selectedNPC.equipment && Object.entries(selectedNPC.equipment).length > 0 ? (
                      Object.entries(selectedNPC.equipment).map(([slot, item]: [string, any]) => (
                        <div key={slot} className="equipment-item">
                          <span className="slot">{slot}:</span>
                          <span className="item-info">
                            耐久 {item.durability}%
                            {item.quality && ` | 品质 ${item.quality}`}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p>无装备</p>
                    )}
                  </div>
                </div>

                <div className="detail-section">
                  <h4>🎯 技能</h4>
                  <div className="detail-content skills">
                    {Object.entries(selectedNPC.skills).map(([skill, level]) => (
                      <div key={skill} className="skill-item">
                        <span>{skill}</span>
                        <span className="level">Lv.{level as number}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="detail-section">
                  <h4>📋 行动日志</h4>
                  <div className="detail-content action-log">
                    {selectedNPC.action_log && selectedNPC.action_log.length > 0 ? (
                      selectedNPC.action_log.slice(-10).map((log: string, i: number) => (
                        <div key={i} className="log-entry">{log}</div>
                      ))
                    ) : (
                      <p>无日志</p>
                    )}
                  </div>
                </div>

                <div className="detail-section">
                  <h4>🧠 记忆 (NPC内部)</h4>
                  <div className="detail-content memories">
                    {selectedNPC.memories && selectedNPC.memories.length > 0 ? (
                      selectedNPC.memories.map((memory: string, i: number) => (
                        <div key={i} className="memory-entry">{memory}</div>
                      ))
                    ) : (
                      <p>无记忆</p>
                    )}
                  </div>
                </div>

                <div className="detail-section">
                  <h4>💾 记忆服务数据</h4>
                  <div className="detail-content memory-service">
                    {selectedNPC.memory_service_data && selectedNPC.memory_service_data.length > 0 ? (
                      selectedNPC.memory_service_data.map((memory: any, i: number) => (
                        <div key={i} className="memory-service-entry">
                          <div className="memory-header">
                            <span className="memory-type">{memory.type}</span>
                            <span className="memory-importance">重要度: {memory.importance}</span>
                          </div>
                          <div className="memory-content">{memory.content}</div>
                          <div className="memory-time">{memory.timestamp}</div>
                        </div>
                      ))
                    ) : (
                      <p>无服务数据</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'beasts' && (
          <div className="beasts-panel">
            <div className="beast-grid">
              {data.beasts.map((beast) => (
                <div key={beast.id} className="beast-card">
                  <div className="beast-header">
                    <span className="beast-sprite">{beast.sprite}</span>
                    <span className="beast-type">{beast.type}</span>
                    {beast.is_aggressive && <span className="aggressive-badge">⚠️ 攻击性</span>}
                  </div>
                  <div className="beast-info">
                    <p><strong>位置:</strong> ({beast.position.x.toFixed(1)}, {beast.position.y.toFixed(1)})</p>
                    <p><strong>状态:</strong> {beast.state}</p>
                    <p><strong>生命:</strong> {beast.health}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'resources' && (
          <div className="resources-panel">
            <div className="resource-grid">
              {data.resources.map((resource) => (
                <div key={resource.id} className="resource-card">
                  <h4>{resource.type}</h4>
                  <p><strong>位置:</strong> ({resource.position.x.toFixed(1)}, {resource.position.y.toFixed(1)})</p>
                  <p><strong>数量:</strong> {resource.quantity} / {resource.max_quantity}</p>
                  <div className="resource-bar">
                    <div 
                      className="resource-bar-fill" 
                      style={{width: `${(resource.quantity / resource.max_quantity) * 100}%`}}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'buildings' && (
          <div className="buildings-panel">
            <div className="building-grid">
              {data.buildings.map((building) => (
                <div key={building.id} className="building-card">
                  <div className="building-header">
                    <span className="building-sprite">{building.sprite}</span>
                    <span className="building-name">{building.name}</span>
                    {building.is_complete && <span className="complete-badge">✓</span>}
                  </div>
                  <p className="building-type">{building.type}</p>
                  <p className="building-desc">{building.description}</p>
                  <p><strong>位置:</strong> ({building.position.x}, {building.position.y})</p>
                  <p><strong>大小:</strong> {building.size.x} × {building.size.y}</p>
                  {!building.is_complete && (
                    <div className="progress-section">
                      <p><strong>建造进度:</strong> {building.construction_progress.toFixed(1)}%</p>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{width: `${building.construction_progress}%`}}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'events' && (
          <div className="events-panel">
            <div className="event-list">
              {data.events.slice().reverse().map((event) => (
                <div key={event.id} className={`event-entry ${event.importance}`}>
                  <div className="event-header">
                    <span className="event-type">{event.type}</span>
                    <span className="event-time">{new Date(event.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="event-description">{event.description}</div>
                  {event.related_npcs && event.related_npcs.length > 0 && (
                    <div className="event-npcs">
                      相关NPC: {event.related_npcs.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'config' && (
          <div className="config-panel">
            <div className="config-section">
              <h3>⚙️ 游戏配置</h3>
              <div className="config-grid">
                <div className="config-item">
                  <span className="config-label">Tick间隔:</span>
                  <span className="config-value">{data.config.tick_interval}s</span>
                </div>
                <div className="config-item">
                  <span className="config-label">时间缩放:</span>
                  <span className="config-value">{data.config.time_scale}x</span>
                </div>
                <div className="config-item">
                  <span className="config-label">NPC决策间隔:</span>
                  <span className="config-value">{data.config.npc_decision_interval}s (游戏时间)</span>
                </div>
                <div className="config-item">
                  <span className="config-label">野兽决策间隔:</span>
                  <span className="config-value">{data.config.beast_decision_interval}s (游戏时间)</span>
                </div>
                <div className="config-item">
                  <span className="config-label">游戏状态:</span>
                  <span className="config-value">{data.config.is_running ? '🟢 运行中' : '🔴 已停止'}</span>
                </div>
                <div className="config-item">
                  <span className="config-label">游戏已开始:</span>
                  <span className="config-value">{data.config.game_started ? '✓ 是' : '✗ 否'}</span>
                </div>
                <div className="config-item">
                  <span className="config-label">等待客户端:</span>
                  <span className="config-value">{data.config.waiting_for_client ? '⏳ 是' : '✓ 否'}</span>
                </div>
              </div>
            </div>

            <div className="config-section">
              <h3>📊 实时统计</h3>
              <div className="config-grid">
                <div className="config-item">
                  <span className="config-label">当前游戏时间:</span>
                  <span className="config-value">{data.game_time.toFixed(0)} 分钟</span>
                </div>
                <div className="config-item">
                  <span className="config-label">世界大小:</span>
                  <span className="config-value">{data.world_size.width} × {data.world_size.height}</span>
                </div>
              </div>
            </div>

            <div className="config-section">
              <h3>💬 活跃对话</h3>
              {data.conversations.length > 0 ? (
                <div className="conversations-list">
                  {data.conversations.map((conv: any) => (
                    <div key={conv.id} className="conversation-entry">
                      <p><strong>ID:</strong> {conv.id}</p>
                      <p><strong>参与者:</strong> {conv.conversation.participants.join(', ')}</p>
                      <p><strong>消息数:</strong> {conv.conversation.messages.length}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p>当前无活跃对话</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

