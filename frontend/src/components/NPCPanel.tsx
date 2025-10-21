/**
 * NPC status panel
 */
import { useGameStore } from '../store/gameStore'
import './NPCPanel.css'

export function NPCPanel() {
  const { npcs, selectedNPCId, focusedNPCId, selectNPC } = useGameStore()

  const selectedNPC = npcs.find(npc => npc.id === selectedNPCId)
  
  // 🎯 NPC排序：选中/聚焦的置顶，然后按存活状态排序
  const sortedNPCs = [...npcs].sort((a, b) => {
    // 选中的NPC最优先
    if (a.id === selectedNPCId || a.id === focusedNPCId) return -1
    if (b.id === selectedNPCId || b.id === focusedNPCId) return 1
    
    // 存活的NPC优先于死亡的
    if (a.is_alive && !b.is_alive) return -1
    if (!a.is_alive && b.is_alive) return 1
    
    return 0
  })
  
  const getActionStateText = (state: string) => {
    const stateMap: Record<string, string> = {
      'idle': '空闲',
      'moving': '移动中',
      'executing': '执行中',
      'cooling': '冷却中',
    }
    return stateMap[state] || state
  }

  return (
    <div className="npc-panel">
      <h3>👥 居民状态</h3>
      
      <div className="npc-list">
        {sortedNPCs.map((npc) => (
          <div
            key={npc.id}
            className={`npc-item ${selectedNPCId === npc.id || focusedNPCId === npc.id ? 'selected' : ''} ${!npc.is_alive ? 'dead' : ''}`}
            onClick={() => selectNPC(npc.id)}
          >
            <div className="npc-name">
              {!npc.is_alive && '💀 '}{npc.name}
            </div>
            <div className="npc-action">
              {npc.is_alive ? (npc.current_action || '思考中...') : '已死亡'}
            </div>
            <div className="npc-stats">
              <div className="stat-bar">
                <span>❤️ {Math.round(npc.attributes.health)}</span>
                <div className="bar">
                  <div
                    className="fill health"
                    style={{ width: `${npc.attributes.health}%` }}
                  />
                </div>
              </div>
              <div className="stat-bar">
                <span>🍖 {Math.round(npc.attributes.hunger)}</span>
                <div className="bar">
                  <div
                    className="fill hunger"
                    style={{ width: `${100 - npc.attributes.hunger}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedNPC && (
        <div className="npc-details">
          <h4>🔍 详细信息 - {selectedNPC.name}</h4>
          
          {/* Position */}
          <div className="detail-section">
            <strong>📍 位置:</strong>
            <div>({selectedNPC.position.x.toFixed(1)}, {selectedNPC.position.y.toFixed(1)})</div>
          </div>
          
          {/* Current Action */}
          <div className="detail-section">
            <strong>⚡ 当前行动:</strong>
            <div className="action-display">
              {selectedNPC.current_action || '空闲中'}
              {selectedNPC.action_state && selectedNPC.action_state !== 'idle' && (
                <span className="action-state"> ({getActionStateText(selectedNPC.action_state)})</span>
              )}
            </div>
            {selectedNPC.action_duration && selectedNPC.action_duration > 0 && (
              <div className="action-duration">
                预计用时: {selectedNPC.action_duration.toFixed(1)}秒
              </div>
            )}
          </div>
          
          {/* AI Reasoning */}
          {selectedNPC.reasoning && (
            <div className="detail-section ai-section">
              <strong>🤖 AI思考过程:</strong>
              <div className="reasoning">{selectedNPC.reasoning}</div>
            </div>
          )}
          
          {/* Attributes */}
          <div className="detail-section">
            <strong>💪 属性:</strong>
            <div className="attributes-grid">
              <div>❤️ 健康: {Math.round(selectedNPC.attributes.health)}/100</div>
              <div>🍖 饥饿: {Math.round(selectedNPC.attributes.hunger)}/100</div>
              <div>⚡ 体力: {Math.round(selectedNPC.attributes.stamina)}/100</div>
            </div>
          </div>
          
          {/* Skills */}
          <div className="detail-section">
            <strong>🎯 技能:</strong>
            {Object.entries(selectedNPC.skills)
              .filter(([_, level]) => level > 0)
              .map(([skill, level]) => (
                <div key={skill} className="skill-item">
                  <span>{skill}</span>
                  <span className="skill-level">{Math.round(level)}</span>
                </div>
              ))}
            {Object.entries(selectedNPC.skills).filter(([_, level]) => level > 0).length === 0 && (
              <div className="empty-text">还未掌握任何技能</div>
            )}
          </div>
          
          {/* Inventory */}
          <div className="detail-section">
            <strong>🎒 背包:</strong>
            {Object.entries(selectedNPC.inventory).length > 0 ? (
              Object.entries(selectedNPC.inventory).map(([item, count]) => (
                <div key={item} className="inventory-item">
                  <span>{item}</span>
                  <span className="item-count">×{count}</span>
                </div>
              ))
            ) : (
              <div className="empty-text">背包是空的</div>
            )}
          </div>
          
          {/* 🔧 Equipment/Tools */}
          {selectedNPC.equipment && Object.keys(selectedNPC.equipment).length > 0 && (
            <div className="detail-section">
              <strong>🔧 装备/工具:</strong>
              {Object.entries(selectedNPC.equipment).map(([toolName, toolData]: [string, any]) => (
                <div key={toolName} className="equipment-item">
                  <span className="tool-name">{toolName}</span>
                  {toolData.durability !== undefined && (
                    <span className="tool-durability">
                      耐久: {Math.round(toolData.durability)}%
                    </span>
                  )}
                  {toolData.description && (
                    <div className="tool-desc">{toolData.description}</div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          {/* Role */}
          {selectedNPC.role && selectedNPC.role.role !== '新手' && (
            <div className="detail-section">
              <strong>👤 职业:</strong>
              <div className="role-display">
                {selectedNPC.role.role}
                <div className="role-desc">{selectedNPC.role.description}</div>
              </div>
            </div>
          )}
          
          {/* 🔥 当前待办事项 */}
          {selectedNPC.current_todo && (
            <div className="detail-section">
              <strong>📋 当前待办:</strong>
              <div className="todo-display">{selectedNPC.current_todo}</div>
              {selectedNPC.todo_steps && selectedNPC.todo_steps.length > 0 && (
                <div className="todo-steps">
                  {selectedNPC.todo_steps.map((step, idx) => (
                    <div key={idx} className="todo-step">• {step}</div>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {/* 🔥 行动日志 */}
          {selectedNPC.action_log && selectedNPC.action_log.length > 0 && (
            <div className="detail-section">
              <strong>📜 行动日志:</strong>
              <div className="log-list">
                {selectedNPC.action_log.slice(-10).reverse().map((log, idx) => (
                  <div key={idx} className="log-item">{log}</div>
                ))}
              </div>
            </div>
          )}
          
          {/* 🔥 记忆 */}
          {selectedNPC.memories && selectedNPC.memories.length > 0 && (
            <div className="detail-section">
              <strong>💭 记忆:</strong>
              <div className="memory-list">
                {selectedNPC.memories.slice(-8).reverse().map((memory, idx) => (
                  <div key={idx} className="memory-item">{memory}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

