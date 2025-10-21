/**
 * Global game state management using Zustand
 */
import { create } from 'zustand'
import type {
  WorldState,
  WorldUpdate,
  NPC,
  Building,
  ResourceNode,
  Beast,
  GameEvent,
  TimeSystem,
} from '../types'

interface GameStore {
  // Connection
  isConnected: boolean
  error: string | null

  // World state
  world: WorldState | null
  npcs: NPC[]
  buildings: Building[]
  resources: ResourceNode[]
  beasts: Beast[]
  events: GameEvent[]
  time: TimeSystem | null
  globalResources: Record<string, number>

  // UI state
  selectedNPCId: string | null
  selectedResourceId: string | null  // 🔥 新增
  selectedBeastId: string | null     // 🔥 新增
  selectedBuildingId: string | null  // 🏗️ 建筑选择
  focusedNPCId: string | null        // 🎯 聚焦的NPC
  showNPCPanel: boolean
  showCivilizationPanel: boolean

  // Actions
  setConnectionStatus: (status: boolean) => void
  setError: (error: string | null) => void
  setWorld: (world: WorldState) => void
  updateWorld: (update: WorldUpdate) => void
  updateNPC: (id: string, updates: Partial<NPC>) => void
  addBuilding: (building: Building) => void
  addEvent: (event: GameEvent) => void
  selectNPC: (id: string | null) => void
  selectResource: (id: string | null) => void  // 🔥 新增
  selectBeast: (id: string | null) => void     // 🔥 新增
  selectBuilding: (id: string | null) => void  // 🏗️ 建筑选择
  focusNPC: (id: string | null) => void        // 🎯 聚焦NPC
  toggleNPCPanel: () => void
  toggleCivilizationPanel: () => void
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  isConnected: false,
  error: null,
  world: null,
  npcs: [],
  buildings: [],
  resources: [],
  beasts: [],
  events: [],
  time: null,
  globalResources: {},
  selectedNPCId: null,
  selectedResourceId: null,  // 🔥 新增
  selectedBeastId: null,     // 🔥 新增
  selectedBuildingId: null,  // 🏗️ 建筑选择
  focusedNPCId: null,        // 🎯 聚焦的NPC
  showNPCPanel: true,
  showCivilizationPanel: true,

  // Connection actions
  setConnectionStatus: (status) => set({ isConnected: status }),
  
  setError: (error) => set({ error }),

  // World actions
  setWorld: (world) =>
    set({
      world,
      npcs: world.npcs,
      buildings: world.buildings,
      resources: world.resources,
      beasts: world.beasts,
      events: world.events,
      time: world.time,
      globalResources: world.global_resources,
    }),

  updateWorld: (update) => {
    const currentEvents = get().events
    const newEvents = update.events.filter(
      (e) => !currentEvents.some((ce) => ce.id === e.id)
    )

    // 🔥 更新世界状态
    const currentWorld = get().world
    if (currentWorld) {
      currentWorld.weather = update.weather  // 🌦️ 更新天气
      currentWorld.buildings = update.buildings  // 🏗️ 更新建筑
      currentWorld.resources = update.resources  // 📍 更新资源
    }

    set({
      time: update.time,
      npcs: update.npcs,
      buildings: update.buildings,  // 🏗️ 更新建筑状态
      resources: update.resources,  // 📍 更新资源状态
      beasts: update.beasts || get().beasts,
      events: [...currentEvents, ...newEvents].slice(-100), // Keep last 100 events
      globalResources: update.global_resources,
      world: currentWorld,  // 更新world对象
    })
  },

  updateNPC: (id, updates) =>
    set((state) => ({
      npcs: state.npcs.map((npc) =>
        npc.id === id ? { ...npc, ...updates } : npc
      ),
    })),

  addBuilding: (building) =>
    set((state) => ({
      buildings: [...state.buildings, building],
    })),

  addEvent: (event) =>
    set((state) => ({
      events: [...state.events, event].slice(-100),
    })),

  // UI actions
  selectNPC: (id) => set({ selectedNPCId: id, selectedResourceId: null, selectedBeastId: null, selectedBuildingId: null, focusedNPCId: id }),
  
  selectResource: (id) => set({ selectedResourceId: id, selectedNPCId: null, selectedBeastId: null, selectedBuildingId: null, focusedNPCId: null }),  // 🔥 新增
  
  selectBeast: (id) => set({ selectedBeastId: id, selectedNPCId: null, selectedResourceId: null, selectedBuildingId: null, focusedNPCId: null }),     // 🔥 新增
  
  selectBuilding: (id) => set({ selectedBuildingId: id, selectedNPCId: null, selectedResourceId: null, selectedBeastId: null, focusedNPCId: null }),  // 🏗️ 建筑选择
  
  focusNPC: (id) => set({ focusedNPCId: id }),  // 🎯 单独设置聚焦，不改变选择
  
  toggleNPCPanel: () => set((state) => ({ showNPCPanel: !state.showNPCPanel })),
  
  toggleCivilizationPanel: () =>
    set((state) => ({ showCivilizationPanel: !state.showCivilizationPanel })),
}))

