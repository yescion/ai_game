/**
 * WebSocket service for real-time communication
 */
import { io, Socket } from 'socket.io-client'
import { useGameStore } from '../store/gameStore'
import type { WorldState, WorldUpdate, GameEvent } from '../types'

class SocketService {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private readySent = false  // 🔥 防止重复发送ready信号

  connect() {
    // 🔥 防止重复创建socket（React StrictMode会调用两次）
    if (this.socket) {
      if (this.socket.connected) {
        console.log('✅ Socket already connected')
        return
      } else {
        console.log('⚠️ Socket exists but not connected, reconnecting...')
        this.socket.connect()
        return
      }
    }

    const serverUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    console.log('Connecting to server:', serverUrl)

    // 🔥 修复连接策略：先用polling建立连接，再升级到WebSocket
    this.socket = io(serverUrl, {
      transports: ['polling', 'websocket'],  // 🔥 先polling后websocket
      upgrade: true,  // 🔥 允许升级到WebSocket
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10,  // 增加重试次数
      timeout: 10000,  // 连接超时10秒
      forceNew: false,  // 重用连接
    })

    this.setupEventHandlers()
  }

  private setupEventHandlers() {
    if (!this.socket) return

    this.socket.on('connect', () => {
      console.log('✅ Connected to game server')
      this.reconnectAttempts = 0
      useGameStore.getState().setConnectionStatus(true)
      
      // 🔥 连接成功后，立即发送ready信号（只发送一次）
      if (!this.readySent && this.socket) {
        console.log('📤 Sending client_ready signal to backend...')
        this.socket.emit('client_ready')
        this.readySent = true
      } else if (this.readySent) {
        console.log('ℹ️ Already sent ready signal (reconnection)')
      }
    })

    this.socket.on('disconnect', (reason) => {
      console.log('❌ Disconnected from server:', reason)
      useGameStore.getState().setConnectionStatus(false)
    })

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error)
      this.reconnectAttempts++
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached')
        useGameStore.getState().setError('无法连接到服务器')
      }
    })

    // Game events
    this.socket.on('world_state', (data: WorldState) => {
      console.log('📡 Received world state', data)
      useGameStore.getState().setWorld(data)
    })

    this.socket.on('world_update', (data: WorldUpdate) => {
      console.log('🔄 World update')
      useGameStore.getState().updateWorld(data)
    })

    this.socket.on('npc_action', (data: any) => {
      console.log('🤖 AI Decision:', data)
      console.log(`💭 ${data.npc_name}: ${data.reasoning}`)
      
      const { npc_id, action, reasoning, position } = data
      
      // Update NPC in store
      useGameStore.getState().updateNPC(npc_id, {
        current_action: action,
        reasoning: reasoning,
        position: position || undefined,
      })
      
      // Add AI thinking event to timeline
      if (reasoning) {
        useGameStore.getState().addEvent({
          id: `ai_${Date.now()}_${npc_id}`,
          type: 'npc_action',
          description: `🤖 ${data.npc_name}: ${reasoning}`,
          timestamp: new Date().toISOString(),
          related_npcs: [npc_id],
          importance: 'low'
        })
      }
    })

    this.socket.on('game_event', (event: GameEvent) => {
      console.log('📌 Game event:', event)
      useGameStore.getState().addEvent(event)
    })
    
    this.socket.on('social_interaction', (data: any) => {
      console.log('💬 Social Interaction:', data)
      console.log(`${data.npc1_name} ↔️ ${data.npc2_name}`)
      
      // Already added to events via game_event, but we can log it separately
    })

    // 🔥 上帝指令：NPC更新事件（轻量级更新）
    this.socket.on('npcs_updated', (data: { npcs: any[] }) => {
      console.log('🔮 NPCs updated from god command:', data.npcs.length, 'NPCs')
      
      // 批量更新受影响的NPC
      const store = useGameStore.getState()
      data.npcs.forEach((updatedNpc) => {
        store.updateNPC(updatedNpc.id, updatedNpc)
      })
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      console.log('Disconnected from server')
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }

  // Emit events to server
  emit(event: string, data: any) {
    if (this.socket?.connected) {
      this.socket.emit(event, data)
    } else {
      console.warn('Socket not connected, cannot emit event:', event)
    }
  }

  // Listen to events from server
  on(event: string, callback: (data: any) => void) {
    if (this.socket) {
      this.socket.on(event, callback)
    } else {
      console.warn('Socket not initialized, cannot listen to event:', event)
    }
  }

  // Remove event listener
  off(event: string, callback?: (data: any) => void) {
    if (this.socket) {
      if (callback) {
        this.socket.off(event, callback)
      } else {
        this.socket.off(event)
      }
    }
  }

  // 🔥 通知服务器客户端已准备好（已废弃，改为在connect事件中自动发送）
  sendReady() {
    if (this.socket?.connected) {
      console.log('✅ [Manual] Sending client ready signal to backend...')
      this.socket.emit('client_ready')
    } else {
      console.warn('⚠️ Socket not connected, cannot send ready signal')
    }
  }
}

export const socketService = new SocketService()

