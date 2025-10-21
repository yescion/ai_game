/**
 * Event timeline showing game events
 */
import { useGameStore } from '../store/gameStore'
import { useEffect, useRef, useState } from 'react'
import './EventTimeline.css'

export function EventTimeline() {
  const events = useGameStore((state) => state.events)
  const npcs = useGameStore((state) => state.npcs)
  const containerRef = useRef<HTMLDivElement>(null)
  const [selectedNpc, setSelectedNpc] = useState<string>('all')

  // Auto scroll to bottom when new events arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [events])

  const getEventIcon = (description: string, type: string) => {
    // AI思考相关
    if (description.includes('🤖') || description.includes('💭')) return '🤖'
    if (description.includes('采集')) return '⛏️'
    if (description.includes('建造')) return '🏗️'
    if (description.includes('休息')) return '😴'
    if (description.includes('进食')) return '🍖'
    if (description.includes('探索')) return '🔍'
    if (description.includes('交流') || description.includes('对话')) return '💬'
    if (description.includes('战斗')) return '⚔️'
    
    // 类型相关
    const icons: Record<string, string> = {
      game_start: '🎮',
      npc_action: '⚡',
      building_complete: '🏛️',
      combat: '⚔️',
      death: '💀',
      discovery: '🔍',
      town_meeting: '🏛️',
      milestone: '🎯',
      resource_gathered: '📦',
    }
    return icons[type] || '📌'
  }
  
  const getImportanceClass = (importance?: string) => {
    if (importance === 'high') return 'importance-high'
    if (importance === 'medium') return 'importance-medium'
    return 'importance-low'
  }

  // Filter events by selected NPC
  const filteredEvents = selectedNpc === 'all' 
    ? events 
    : events.filter(event => 
        event.related_npcs && event.related_npcs.some(npcId => {
          const npc = npcs.find(n => n.id === npcId)
          return npc && (npc.id === selectedNpc || npc.name === selectedNpc)
        })
      )

  return (
    <div className="event-timeline">
      <div className="timeline-header">
        <h3>📜 世界事件 ({filteredEvents.length}/{events.length})</h3>
        <select 
          className="npc-filter"
          value={selectedNpc}
          onChange={(e) => setSelectedNpc(e.target.value)}
        >
          <option value="all">所有事件</option>
          {npcs.map(npc => (
            <option key={npc.id} value={npc.id}>
              {npc.name}
            </option>
          ))}
        </select>
      </div>
      <div className="event-list" ref={containerRef}>
        {filteredEvents.length === 0 ? (
          <div className="no-events">
            {selectedNpc === 'all' ? '等待游戏事件...' : '该NPC暂无相关事件'}
          </div>
        ) : (
          filteredEvents.slice(-50).map((event) => (
            <div 
              key={event.id} 
              className={`event-item ${getImportanceClass(event.importance)}`}
              title={`类型: ${event.type} | 时间: ${new Date(event.timestamp).toLocaleString()}`}
            >
              <span className="event-icon">{getEventIcon(event.description, event.type)}</span>
              <div className="event-content">
                <span className="event-description">{event.description}</span>
                <span className="event-time">
                  {new Date(event.timestamp).toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  })}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

