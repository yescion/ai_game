/**
 * God Console - 上帝指令控制台
 */
import { useState } from 'react'
import { useGameStore } from '../store/gameStore'
import { socketService } from '../services/socketService'
import './GodConsole.css'

export function GodConsole() {
  const npcs = useGameStore((state) => state.npcs)
  const [isOpen, setIsOpen] = useState(false)
  const [commandType, setCommandType] = useState<'add' | 'modify' | 'clear'>('add')
  const [target, setTarget] = useState('all')
  const [memoryText, setMemoryText] = useState('')
  const [memoryIndex, setMemoryIndex] = useState(0)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)

  const handleAddMemory = () => {
    if (!memoryText.trim()) {
      setResult({ success: false, message: '请输入记忆内容' })
      return
    }

    socketService.emit('god_add_memory', {
      target,
      memory: memoryText
    })

    setMemoryText('')
    setResult({ success: true, message: '正在添加记忆...' })
  }

  const handleModifyMemory = () => {
    if (!memoryText.trim() || target === 'all') {
      setResult({ success: false, message: '请选择特定NPC并输入新记忆' })
      return
    }

    socketService.emit('god_modify_memory', {
      npc: target,
      index: memoryIndex,
      new_memory: memoryText
    })

    setMemoryText('')
    setResult({ success: true, message: '正在修改记忆...' })
  }

  const handleClearMemories = () => {
    if (target === 'all') {
      if (!window.confirm('确定要清除所有NPC的记忆吗？')) return
    } else {
      if (!window.confirm(`确定要清除 ${target} 的记忆吗？`)) return
    }

    socketService.emit('god_clear_memories', { target })
    setResult({ success: true, message: '正在清除记忆...' })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    switch (commandType) {
      case 'add':
        handleAddMemory()
        break
      case 'modify':
        handleModifyMemory()
        break
      case 'clear':
        handleClearMemories()
        break
    }
  }

  // Listen for results
  socketService.on('god_command_result', (data: any) => {
    setResult(data)
    setTimeout(() => setResult(null), 3000)
  })

  return (
    <div className={`god-console ${isOpen ? 'open' : 'closed'}`}>
      <button 
        className="god-toggle"
        onClick={() => setIsOpen(!isOpen)}
        title="上帝指令控制台"
      >
        🔮
      </button>

      {isOpen && (
        <div className="god-panel">
          <div className="god-header">
            <h3>🔮 上帝指令</h3>
            <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
          </div>

          <form className="god-form" onSubmit={handleSubmit}>
            {/* 指令类型 */}
            <div className="form-group">
              <label>指令类型</label>
              <select 
                value={commandType} 
                onChange={(e) => setCommandType(e.target.value as any)}
              >
                <option value="add">添加记忆</option>
                <option value="modify">修改记忆</option>
                <option value="clear">清除记忆</option>
              </select>
            </div>

            {/* 目标NPC */}
            <div className="form-group">
              <label>目标NPC</label>
              <select 
                value={target} 
                onChange={(e) => setTarget(e.target.value)}
              >
                <option value="all">所有NPC</option>
                {npcs.map(npc => (
                  <option key={npc.id} value={npc.id}>
                    {npc.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 修改记忆时需要索引 */}
            {commandType === 'modify' && (
              <div className="form-group">
                <label>记忆索引</label>
                <input 
                  type="number" 
                  min="0"
                  value={memoryIndex}
                  onChange={(e) => setMemoryIndex(parseInt(e.target.value) || 0)}
                  placeholder="0"
                />
              </div>
            )}

            {/* 记忆内容 */}
            {(commandType === 'add' || commandType === 'modify') && (
              <div className="form-group">
                <label>记忆内容</label>
                <textarea
                  value={memoryText}
                  onChange={(e) => setMemoryText(e.target.value)}
                  placeholder={
                    commandType === 'add' 
                      ? '输入要添加的记忆...' 
                      : '输入新的记忆内容...'
                  }
                  rows={3}
                />
              </div>
            )}

            {/* 提交按钮 */}
            <button type="submit" className="god-submit">
              {commandType === 'add' && '添加记忆'}
              {commandType === 'modify' && '修改记忆'}
              {commandType === 'clear' && '清除记忆'}
            </button>
          </form>

          {/* 结果显示 */}
          {result && (
            <div className={`god-result ${result.success ? 'success' : 'error'}`}>
              {result.message}
            </div>
          )}

          {/* 使用说明 */}
          <div className="god-help">
            <h4>💡 使用说明</h4>
            <ul>
              <li><strong>添加记忆</strong>：为NPC添加新的记忆，会影响其决策</li>
              <li><strong>修改记忆</strong>：修改NPC的某条记忆（需要知道索引）</li>
              <li><strong>清除记忆</strong>：清空NPC的所有记忆</li>
            </ul>
            <p className="tip">💡 示例："发现了一片肥沃的土地，适合建立农场"</p>
          </div>
        </div>
      )}
    </div>
  )
}

