/**
 * Type definitions for the game
 */

export interface Position2D {
  x: number
  y: number
}

export interface NPCAttributes {
  health: number
  hunger: number
  stamina: number
  temperature?: number
}

export interface NPC {
  id: string
  name: string
  position: Position2D
  direction: string
  sprite: string
  attributes: NPCAttributes
  skills: Record<string, number>
  inventory: Record<string, number>
  equipment?: Record<string, {
    durability: number
    quality?: number
    description?: string
    type?: string
  }>
  current_action?: string
  action_target?: string
  reasoning?: string
  role?: {
    role: string
    description: string
  }
  action_state?: string  // idle, moving, executing, cooling
  action_start_time?: number
  action_duration?: number
  current_todo?: string
  todo_steps?: string[]
  action_log?: string[]
  memories?: string[]
  is_alive?: boolean  // NPC是否存活
}

export interface Building {
  id: string
  type: string
  name: string
  position: Position2D
  size: Position2D
  description: string
  sprite: string
  is_complete: boolean
  construction_progress: number
}

export interface ResourceNode {
  id: string
  type: string
  position: Position2D
  quantity: number
  max_quantity: number
}

export interface Beast {
  id: string
  type: string
  position: Position2D
  health: number
  state: string
  sprite: string
  is_aggressive: boolean
}

export interface TimeSystem {
  day: number
  hour: number
  minute: number
  season: string
}

export interface GameEvent {
  id: string
  type: string
  description: string
  timestamp: string
  importance?: string
  related_npcs?: string[]
}

export interface WorldState {
  width: number
  height: number
  time: TimeSystem
  weather: string
  npcs: NPC[]
  buildings: Building[]
  resources: ResourceNode[]
  beasts: Beast[]
  events: GameEvent[]
  global_resources: Record<string, number>
  spawn_point?: [number, number]
}

export interface WorldUpdate {
  time: TimeSystem
  weather: string  // 🌦️ 天气数据
  npcs: NPC[]
  buildings: Building[]  // 🏗️ 建筑数据
  resources: ResourceNode[]  // 📍 资源点数据
  beasts: Beast[]
  events: GameEvent[]
  global_resources: Record<string, number>
}

