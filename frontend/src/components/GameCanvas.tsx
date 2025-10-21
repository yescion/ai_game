/**
 * Main game canvas component using PixiJS
 */
import { useEffect, useRef, useState } from 'react'
import * as PIXI from 'pixi.js'
import { useGameStore } from '../store/gameStore'

// 坐标缩放：100x100逻辑单位 -> 1200x800像素
const SCALE_X = 1200 / 100
const SCALE_Y = 800 / 100

export function GameCanvas() {
  const canvasRef = useRef<HTMLDivElement>(null)
  const appRef = useRef<PIXI.Application | null>(null)
  const npcsRef = useRef<Map<string, PIXI.Container>>(new Map())
  const resourcesRef = useRef<Map<string, PIXI.Container>>(new Map())
  const beastsRef = useRef<Map<string, PIXI.Container>>(new Map())
  const buildingsRef = useRef<Map<string, PIXI.Container>>(new Map())  // 🏗️ 建筑容器
  const npcsDataRef = useRef<typeof npcs>([])  // 存储最新的npcs数据供ticker使用
  
  // 🔥 地图缩放和平移状态
  const [zoom, setZoom] = useState(1.0)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const isDraggingRef = useRef(false)
  const lastMousePosRef = useRef({ x: 0, y: 0 })
  
  const { npcs, resources, beasts, buildings, world, selectBuilding, focusedNPCId, selectedNPCId } = useGameStore()  // 🏗️ 添加buildings、world和selectBuilding、focusedNPCId、selectedNPCId
  
  // 更新npcsDataRef，使ticker能访问最新数据
  useEffect(() => {
    npcsDataRef.current = npcs
  }, [npcs])

  // 初始化PixiJS应用
  useEffect(() => {
    if (!canvasRef.current) return

    // Create PixiJS application
    const app = new PIXI.Application({
      width: 1200,
      height: 800,
      backgroundColor: 0x87CEEB, // Sky blue
      antialias: true,
    })

    canvasRef.current.appendChild(app.view as HTMLCanvasElement)
    appRef.current = app

    // 🔥 ready信号已在socketService的connect事件中自动发送
    console.log('🎮 Canvas fully loaded')

    // 1. 创建草地背景
    const ground = new PIXI.Graphics()
    ground.beginFill(0x7CCD7C) // Grass green
    ground.drawRect(0, 0, 1200, 800)
    ground.endFill()
    app.stage.addChild(ground)

    // 2. 添加网格线（帮助观察）
    const grid = new PIXI.Graphics()
    grid.lineStyle(1, 0x000000, 0.05)
    for (let i = 0; i <= 100; i += 10) {
      const x = i * SCALE_X
      grid.moveTo(x, 0)
      grid.lineTo(x, 800)
    }
    for (let i = 0; i <= 100; i += 10) {
      const y = i * SCALE_Y
      grid.moveTo(0, y)
      grid.lineTo(1200, y)
    }
    app.stage.addChild(grid)

    // 3. 创建图层容器（控制渲染顺序）
    const resourceLayer = new PIXI.Container()
    resourceLayer.name = 'resourceLayer'
    app.stage.addChild(resourceLayer)

    const buildingLayer = new PIXI.Container()  // 🏗️ 建筑层
    buildingLayer.name = 'buildingLayer'
    app.stage.addChild(buildingLayer)

    const beastLayer = new PIXI.Container()
    beastLayer.name = 'beastLayer'
    app.stage.addChild(beastLayer)

    const npcLayer = new PIXI.Container()
    npcLayer.name = 'npcLayer'
    app.stage.addChild(npcLayer)

    // 4. 添加ticker用于平滑移动和碰撞检测
    const lastPositions = new Map<string, {x: number, y: number}>()  // 记录上一帧位置
    
    app.ticker.add((delta: number) => {
      // NPC平滑移动
      npcsRef.current.forEach((container, id) => {
        // 从ref获取最新的npcs数据
        const npc = npcsDataRef.current.find(n => n.id === id)
        if (!npc) return

        const targetX = npc.position.x * SCALE_X
        const targetY = npc.position.y * SCALE_Y
        
        const dx = targetX - container.x
        const dy = targetY - container.y
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        // 记录上一帧位置
        lastPositions.set(id, { x: container.x, y: container.y })
        
        if (distance > 0.5) {
          // 移动速度：每帧移动固定像素
          const speed = 1.5 * delta  // 每帧1.5像素
          const ratio = Math.min(speed / distance, 1)
          container.x += dx * ratio
          container.y += dy * ratio
        }
      })
      
      // 🚫 简化碰撞检测：只处理与建筑的碰撞，避免NPC/野兽卡住
      // 收集所有移动实体（NPC和野兽）
      const movableEntities: Array<{container: PIXI.Container, radius: number, type: string}> = []
      
      // 添加NPC（半径12）
      npcsRef.current.forEach((container) => {
        movableEntities.push({ container, radius: 12, type: 'npc' })
      })
      
      // 添加野兽（半径12）
      beastsRef.current.forEach((container) => {
        movableEntities.push({ container, radius: 12, type: 'beast' })
      })
      
      // 收集建筑（静态障碍物）
      const buildings: Array<{container: PIXI.Container, radius: number}> = []
      buildingsRef.current.forEach((container) => {
        const buildingSize = container.width / 2 || 20
        buildings.push({ container, radius: buildingSize })
      })
      
      // 检测移动实体与建筑的碰撞（只检测建筑，不检测NPC之间）
      movableEntities.forEach(entity => {
        buildings.forEach(building => {
          const dx = building.container.x - entity.container.x
          const dy = building.container.y - entity.container.y
          const distance = Math.sqrt(dx * dx + dy * dy)
          const minDistance = entity.radius + building.radius
          
          // 如果与建筑碰撞，推开移动实体
          if (distance < minDistance && distance > 0) {
            const overlap = minDistance - distance
            const angle = Math.atan2(dy, dx)
            
            // 只推开移动实体（建筑不动）
            entity.container.x -= Math.cos(angle) * overlap
            entity.container.y -= Math.sin(angle) * overlap
          }
        })
      })
      
      // 记录野兽位置（用于下一帧判断）
      beastsRef.current.forEach((container, id) => {
        lastPositions.set('beast_' + id, { x: container.x, y: container.y })
      })
      
      // 🎯 移除NPC/野兽之间的碰撞检测
      // 理由：
      // 1. 资源独占系统已确保不会多个NPC挤在同一资源点
      // 2. NPC之间短暂重叠是可接受的（视觉上不明显）
      // 3. 避免"乒乓效应"导致的持续抖动
      // 4. 提升性能
    })

    return () => {
      app.destroy(true, { children: true, texture: true, baseTexture: true })
    }
  }, [])

  // 🔥 鼠标滚轮缩放
  useEffect(() => {
    if (!appRef.current) return
    const app = appRef.current
    const canvas = app.view as HTMLCanvasElement

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault()
      
      // 缩放因子
      const delta = e.deltaY > 0 ? 0.9 : 1.1
      const newZoom = Math.max(0.5, Math.min(2.0, zoom * delta))
      
      // 以鼠标位置为中心缩放
      const rect = canvas.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top
      
      // 计算新的offset，保持鼠标位置不变
      const newOffsetX = mouseX - (mouseX - offset.x) * (newZoom / zoom)
      const newOffsetY = mouseY - (mouseY - offset.y) * (newZoom / zoom)
      
      setZoom(newZoom)
      setOffset({ x: newOffsetX, y: newOffsetY })
    }

    canvas.addEventListener('wheel', handleWheel, { passive: false })

    return () => {
      canvas.removeEventListener('wheel', handleWheel)
    }
  }, [zoom, offset])

  // 🔥 鼠标拖拽平移 + 点击空白取消焦点
  useEffect(() => {
    if (!appRef.current) return
    const app = appRef.current
    const canvas = app.view as HTMLCanvasElement
    let clickStartPos = { x: 0, y: 0 }

    const handleMouseDown = (e: MouseEvent) => {
      isDraggingRef.current = true
      clickStartPos = { x: e.clientX, y: e.clientY }
      lastMousePosRef.current = { x: e.clientX, y: e.clientY }
      canvas.style.cursor = 'grabbing'
    }

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return

      const dx = e.clientX - lastMousePosRef.current.x
      const dy = e.clientY - lastMousePosRef.current.y

      setOffset(prev => ({
        x: prev.x + dx,
        y: prev.y + dy
      }))

      lastMousePosRef.current = { x: e.clientX, y: e.clientY }
    }

    const handleMouseUp = (e: MouseEvent) => {
      // 检查是否是点击（而不是拖拽）
      const dx = e.clientX - clickStartPos.x
      const dy = e.clientY - clickStartPos.y
      const distance = Math.sqrt(dx * dx + dy * dy)
      
      if (distance < 5) {  // 移动距离小于5px，认为是点击
        // 🎯 点击空白处取消焦点
        useGameStore.getState().focusNPC(null)
        console.log('🎯 点击空白处，取消镜头焦点')
      }
      
      isDraggingRef.current = false
      canvas.style.cursor = 'grab'
    }

    canvas.style.cursor = 'grab'
    canvas.addEventListener('mousedown', handleMouseDown)
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)

    return () => {
      canvas.removeEventListener('mousedown', handleMouseDown)
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [])

  // 🔥 应用缩放和平移到stage
  useEffect(() => {
    if (!appRef.current) return
    const app = appRef.current

    app.stage.scale.set(zoom)
    app.stage.position.set(offset.x, offset.y)
  }, [zoom, offset])

  // 渲染资源节点
  useEffect(() => {
    if (!appRef.current) return

    const app = appRef.current
    const resourceLayer = app.stage.children.find((c: PIXI.DisplayObject) => (c as PIXI.Container).name === 'resourceLayer') as PIXI.Container
    if (!resourceLayer) return

    const currentResourceIds = new Set(resources.map(r => r.id))
    
    // 移除不存在的资源
    resourcesRef.current.forEach((container, id) => {
      if (!currentResourceIds.has(id)) {
        resourceLayer.removeChild(container)
        container.destroy()
        resourcesRef.current.delete(id)
      }
    })

    // 添加或更新资源
    resources.forEach(resource => {
      let resourceContainer = resourcesRef.current.get(resource.id)
      
      if (!resourceContainer) {
        resourceContainer = new PIXI.Container()
        
        const sprite = new PIXI.Graphics()
        
        // 根据资源类型绘制不同的形状和颜色
        switch (resource.type) {
          case 'wood':
            // 树木：深绿色圆形
            sprite.beginFill(0x228B22)
            sprite.drawCircle(0, 0, 10)
            sprite.endFill()
            break
          case 'stone':
            // 石头：灰色方形
            sprite.beginFill(0x808080)
            sprite.drawRect(-8, -8, 16, 16)
            sprite.endFill()
            break
          case 'berry':
            // 浆果：红色小圆点
            sprite.beginFill(0xFF0000)
            sprite.drawCircle(0, 0, 6)
            sprite.endFill()
            break
          case 'water':
            // 水源：蓝色圆形
            sprite.beginFill(0x0000FF)
            sprite.drawCircle(0, 0, 9)
            sprite.endFill()
            break
          default:
            sprite.beginFill(0xFFFFFF)
            sprite.drawCircle(0, 0, 7)
            sprite.endFill()
        }
        
        resourceContainer.addChild(sprite)
        
        // 资源数量标签
        const amountText = new PIXI.Text(`${resource.quantity}`, {
          fontSize: 9,
          fill: 0xFFFFFF,
          stroke: 0x000000,
          strokeThickness: 2,
        })
        amountText.anchor.set(0.5, 0.5)
        resourceContainer.addChild(amountText)
        
        resourceContainer.x = resource.position.x * SCALE_X
        resourceContainer.y = resource.position.y * SCALE_Y
        
        // 🔥 交互：点击选中资源
        resourceContainer.interactive = true
        resourceContainer.cursor = 'pointer'
        resourceContainer.on('pointerdown', (e: PIXI.FederatedPointerEvent) => {
          e.stopPropagation()
          console.log('Resource clicked:', resource)
          useGameStore.getState().selectResource(resource.id)
        })
        
        resourceLayer.addChild(resourceContainer)
        resourcesRef.current.set(resource.id, resourceContainer)
      } else {
        // 更新资源数量
        const amountText = resourceContainer.children[1] as PIXI.Text
        if (amountText) {
          amountText.text = `${resource.quantity}`
        }
      }
    })
  }, [resources])

  // 渲染野兽
  useEffect(() => {
    if (!appRef.current) return

    const app = appRef.current
    const beastLayer = app.stage.children.find((c: PIXI.DisplayObject) => (c as PIXI.Container).name === 'beastLayer') as PIXI.Container
    if (!beastLayer) return

    const currentBeastIds = new Set(beasts.map(b => b.id))
    
    // 移除不存在的野兽
    beastsRef.current.forEach((container, id) => {
      if (!currentBeastIds.has(id)) {
        beastLayer.removeChild(container)
        container.destroy()
        beastsRef.current.delete(id)
      }
    })

    // 添加或更新野兽
    beasts.forEach(beast => {
      let beastContainer = beastsRef.current.get(beast.id)
      
      if (!beastContainer) {
        beastContainer = new PIXI.Container()
        
        // 野兽：三角形
        const triangle = new PIXI.Graphics()
        const color = beast.is_aggressive ? 0xFF4136 : 0xFF851B // 攻击性：红色，温和：橙色
        triangle.beginFill(color)
        triangle.moveTo(0, -10)
        triangle.lineTo(-8, 8)
        triangle.lineTo(8, 8)
        triangle.lineTo(0, -10)
        triangle.endFill()
        beastContainer.addChild(triangle)
        
        // 野兽名称
        const nameText = new PIXI.Text(beast.type, {
          fontSize: 9,
          fill: 0xFFFFFF,
          stroke: 0x000000,
          strokeThickness: 2,
        })
        nameText.anchor.set(0.5, 0)
        nameText.position.set(0, 12)
        beastContainer.addChild(nameText)
        
        beastContainer.x = beast.position.x * SCALE_X
        beastContainer.y = beast.position.y * SCALE_Y
        
        // 🔥 交互：点击选中野兽
        beastContainer.interactive = true
        beastContainer.cursor = 'pointer'
        beastContainer.on('pointerdown', (e: PIXI.FederatedPointerEvent) => {
          e.stopPropagation()
          console.log('Beast clicked:', beast)
          useGameStore.getState().selectBeast(beast.id)
        })
        
        beastLayer.addChild(beastContainer)
        beastsRef.current.set(beast.id, beastContainer)
      } else {
        // 🔥 更新野兽位置（关键修复！）
        beastContainer.x = beast.position.x * SCALE_X
        beastContainer.y = beast.position.y * SCALE_Y
      }
    })
  }, [beasts])

  // 🏗️ 渲染建筑
  useEffect(() => {
    if (!appRef.current) return

    const app = appRef.current
    const buildingLayer = app.stage.children.find((c: PIXI.DisplayObject) => (c as PIXI.Container).name === 'buildingLayer') as PIXI.Container
    if (!buildingLayer) return

    const currentBuildingIds = new Set(buildings.map(b => b.id))
    
    // 移除不存在的建筑
    buildingsRef.current.forEach((container, id) => {
      if (!currentBuildingIds.has(id)) {
        buildingLayer.removeChild(container)
        container.destroy()
        buildingsRef.current.delete(id)
      }
    })

    // 添加或更新建筑
    buildings.forEach(building => {
      let buildingContainer = buildingsRef.current.get(building.id)
      
      if (!buildingContainer) {
        buildingContainer = new PIXI.Container()
        
        // 🏗️ 根据建筑类型绘制不同的形状
        const sprite = new PIXI.Graphics()
        const sizeX = building.size.x * SCALE_X
        const sizeY = building.size.y * SCALE_Y
        
        // 建筑颜色根据类型
        let color = 0x8B4513  // 默认棕色
        switch (building.type) {
          case 'campfire':
            color = 0xFF4500  // 橙红色
            break
          case 'lean_to':
          case 'wooden_hut':
            color = 0x8B4513  // 棕色
            break
          case 'storage_shed':
            color = 0xA0522D  // 赭色
            break
          case 'workshop':
            color = 0x696969  // 深灰色
            break
        }
        
        // 建筑本体（矩形）
        sprite.beginFill(color, building.is_complete ? 1.0 : 0.5)  // 未完成时半透明
        sprite.lineStyle(2, 0x000000, 1)
        sprite.drawRect(-sizeX / 2, -sizeY / 2, sizeX, sizeY)
        sprite.endFill()
        
        // 🏗️ 如果正在建造，显示进度条
        if (!building.is_complete) {
          const progressBg = new PIXI.Graphics()
          progressBg.beginFill(0x000000, 0.5)
          progressBg.drawRect(-sizeX / 2, sizeY / 2 + 5, sizeX, 8)
          progressBg.endFill()
          sprite.addChild(progressBg)
          
          const progressBar = new PIXI.Graphics()
          progressBar.beginFill(0x00FF00)
          progressBar.drawRect(-sizeX / 2, sizeY / 2 + 5, sizeX * building.construction_progress, 8)
          progressBar.endFill()
          progressBar.name = 'progressBar'
          sprite.addChild(progressBar)
        }
        
        buildingContainer.addChild(sprite)
        
        // 建筑名称
        const nameText = new PIXI.Text(building.name, {
          fontSize: 10,
          fill: 0xFFFFFF,
          stroke: 0x000000,
          strokeThickness: 3,
          fontWeight: 'bold',
        })
        nameText.anchor.set(0.5, 1)
        nameText.position.set(0, -sizeY / 2 - 5)
        buildingContainer.addChild(nameText)
        
        // 建筑状态文本
        const statusText = new PIXI.Text(
          building.is_complete ? '✓完成' : `🔨${Math.round(building.construction_progress * 100)}%`,
          {
            fontSize: 9,
            fill: building.is_complete ? 0x00FF00 : 0xFFFF00,
            stroke: 0x000000,
            strokeThickness: 2,
          }
        )
        statusText.name = 'statusText'
        statusText.anchor.set(0.5, 0)
        statusText.position.set(0, sizeY / 2 + 15)
        buildingContainer.addChild(statusText)
        
        buildingContainer.x = building.position.x * SCALE_X
        buildingContainer.y = building.position.y * SCALE_Y
        
        // 🔥 交互：点击选中建筑
        buildingContainer.interactive = true
        buildingContainer.cursor = 'pointer'
        buildingContainer.on('pointerdown', (e: PIXI.FederatedPointerEvent) => {
          e.stopPropagation()
          console.log('Building clicked:', building)
          selectBuilding(building.id)
        })
        
        buildingLayer.addChild(buildingContainer)
        buildingsRef.current.set(building.id, buildingContainer)
      } else {
        // 🔥 更新建筑状态（建造进度）
        const statusText = buildingContainer.children.find((c: PIXI.DisplayObject) => (c as PIXI.Container).name === 'statusText') as PIXI.Text
        if (statusText) {
          statusText.text = building.is_complete ? '✓完成' : `🔨${Math.round(building.construction_progress * 100)}%`
          statusText.style.fill = building.is_complete ? 0x00FF00 : 0xFFFF00
        }
        
        // 更新进度条
        const sprite = buildingContainer.children[0] as PIXI.Graphics
        const progressBar = sprite.children.find((c: PIXI.DisplayObject) => (c as PIXI.Container).name === 'progressBar') as PIXI.Graphics
        if (progressBar && !building.is_complete) {
          progressBar.clear()
          progressBar.beginFill(0x00FF00)
          const sizeX = building.size.x * SCALE_X
          progressBar.drawRect(-sizeX / 2, building.size.y * SCALE_Y / 2 + 5, sizeX * building.construction_progress, 8)
          progressBar.endFill()
        } else if (building.is_complete && progressBar) {
          // 建造完成，移除进度条
          sprite.removeChild(progressBar)
          // 更新建筑透明度
          sprite.alpha = 1.0
        }
      }
    })
  }, [buildings])

  // 渲染NPC
  useEffect(() => {
    if (!appRef.current) return

    const app = appRef.current
    const npcLayer = app.stage.children.find((c: PIXI.DisplayObject) => (c as PIXI.Container).name === 'npcLayer') as PIXI.Container
    if (!npcLayer) return

    const currentNPCIds = new Set(npcs.map(npc => npc.id))
    
    // 移除不存在的NPC
    npcsRef.current.forEach((container, id) => {
      if (!currentNPCIds.has(id)) {
        npcLayer.removeChild(container)
        container.destroy()
        npcsRef.current.delete(id)
      }
    })

    // 添加或更新NPC
    npcs.forEach(npc => {
      let npcContainer = npcsRef.current.get(npc.id)
      
      if (!npcContainer) {
        // 创建新NPC
        npcContainer = new PIXI.Container()
        
        // NPC本体：蓝色圆形
        const circle = new PIXI.Graphics()
        circle.name = 'circle'
        circle.beginFill(0x4169E1)
        circle.drawCircle(0, 0, 10)
        circle.endFill()
        // 边框
        circle.lineStyle(2, 0xFFFFFF, 0.8)
        circle.drawCircle(0, 0, 10)
        npcContainer.addChild(circle)
        
        // 名称标签
        const nameText = new PIXI.Text(npc.name, {
          fontSize: 11,
          fill: 0xFFFFFF,
          stroke: 0x000000,
          strokeThickness: 3,
          fontWeight: 'bold',
        })
        nameText.name = 'nameText'
        nameText.anchor.set(0.5, 1)
        nameText.position.set(0, -15)
        npcContainer.addChild(nameText)
        
        // 行动图标
        const actionIcon = new PIXI.Text('', {
          fontSize: 14,
        })
        actionIcon.name = 'actionIcon'
        actionIcon.anchor.set(0.5, 0)
        actionIcon.position.set(0, -35)
        npcContainer.addChild(actionIcon)
        
        // AI思考气泡
        const reasoningBubble = new PIXI.Text('💭', {
          fontSize: 16,
          fill: 0xFFD700,
        })
        reasoningBubble.name = 'reasoningBubble'
        reasoningBubble.anchor.set(0.5, 0)
        reasoningBubble.position.set(18, -18)
        reasoningBubble.visible = false
        npcContainer.addChild(reasoningBubble)
        
        // 初始位置
        npcContainer.x = npc.position.x * SCALE_X
        npcContainer.y = npc.position.y * SCALE_Y
        
        // 交互
        npcContainer.interactive = true
        npcContainer.cursor = 'pointer'
        npcContainer.on('pointerdown', () => {
          useGameStore.getState().selectNPC(npc.id)
          console.log('✅ Selected NPC:', npc.name, {
            position: npc.position,
            action: npc.current_action,
            reasoning: npc.reasoning
          })
        })
        
        npcLayer.addChild(npcContainer)
        npcsRef.current.set(npc.id, npcContainer)
      }
      
      // 💀 更新死亡状态
      const circle = npcContainer.children.find(c => (c as PIXI.Container).name === 'circle') as PIXI.Graphics
      const nameText = npcContainer.children.find(c => (c as PIXI.Container).name === 'nameText') as PIXI.Text
      if (!npc.is_alive) {
        // NPC死亡：变灰+骷髅头
        if (circle) {
          circle.clear()
          circle.beginFill(0x666666)  // 灰色
          circle.drawCircle(0, 0, 10)
          circle.endFill()
          circle.lineStyle(2, 0x333333, 0.8)
          circle.drawCircle(0, 0, 10)
        }
        if (nameText) {
          nameText.text = `💀 ${npc.name}`
          nameText.style.fill = 0xAAAAAA  // 浅灰色
        }
      } else {
        // NPC存活：正常蓝色
        if (circle) {
          circle.clear()
          circle.beginFill(0x4169E1)  // 蓝色
          circle.drawCircle(0, 0, 10)
          circle.endFill()
          circle.lineStyle(2, 0xFFFFFF, 0.8)
          circle.drawCircle(0, 0, 10)
        }
        if (nameText && nameText.text.startsWith('💀')) {
          nameText.text = npc.name  // 移除骷髅头
          nameText.style.fill = 0xFFFFFF
        }
      }
      
      // 更新行动图标（死亡时隐藏）
      const actionIcon = npcContainer.children.find(c => (c as PIXI.Container).name === 'actionIcon') as PIXI.Text
      if (actionIcon) {
        if (npc.is_alive && npc.current_action) {
          const iconMap: Record<string, string> = {
            gather: '⛏️',
            rest: '😴',
            eat: '🍖',
            explore: '🔍',
            build: '🏗️',
            hunt: '🏹',
            flee: '🏃',
            defend: '🛡️',
          }
          actionIcon.text = iconMap[npc.current_action] || '⚡'
          actionIcon.visible = true
        } else {
          actionIcon.visible = false
        }
      }
      
      // 更新AI思考气泡（死亡时隐藏）
      const reasoningBubble = npcContainer.children.find(c => (c as PIXI.Container).name === 'reasoningBubble') as PIXI.Text
      if (reasoningBubble) {
        reasoningBubble.visible = npc.is_alive && !!npc.reasoning
      }
    })
  }, [npcs])

  // 🎯 平滑镜头跟随NPC
  useEffect(() => {
    if (!focusedNPCId || !appRef.current) return
    
    let animationFrameId: number
    
    const smoothFollow = () => {
      const npc = npcs.find(n => n.id === focusedNPCId)
      if (!npc) return
      
      // 计算NPC在屏幕上的位置
      const npcScreenX = npc.position.x * SCALE_X * zoom
      const npcScreenY = npc.position.y * SCALE_Y * zoom
      
      // 计算目标偏移量，使NPC居中显示
      const canvasWidth = 1200
      const canvasHeight = 800
      const targetOffsetX = canvasWidth / 2 - npcScreenX
      const targetOffsetY = canvasHeight / 2 - npcScreenY
      
      // 平滑插值（lerp）
      setOffset(prev => {
        const lerpFactor = 0.05  // 插值因子，越小越平滑
        const newX = prev.x + (targetOffsetX - prev.x) * lerpFactor
        const newY = prev.y + (targetOffsetY - prev.y) * lerpFactor
        return { x: newX, y: newY }
      })
      
      // 继续下一帧
      animationFrameId = requestAnimationFrame(smoothFollow)
    }
    
    // 开始平滑跟随
    animationFrameId = requestAnimationFrame(smoothFollow)
    console.log(`🎯 镜头开始跟随 ${npcs.find(n => n.id === focusedNPCId)?.name}`)
    
    // 清理函数
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
      }
    }
  }, [focusedNPCId, npcs, zoom])

  // 🔥 高亮选中的NPC
  useEffect(() => {
    if (!appRef.current) return
    
    // 更新所有NPC的高亮状态
    npcsRef.current.forEach((container, id) => {
      const circle = container.children.find(c => (c as PIXI.Container).name === 'circle') as PIXI.Graphics
      const npc = npcs.find(n => n.id === id)
      if (!circle || !npc) return
      
      const isSelected = id === selectedNPCId || id === focusedNPCId
      
      // 重绘圆形以应用高亮效果
      circle.clear()
      if (!npc.is_alive) {
        // 死亡状态：灰色
        circle.beginFill(0x666666)
        circle.drawCircle(0, 0, 10)
        circle.endFill()
        circle.lineStyle(2, isSelected ? 0xFFFF00 : 0x333333, 1)  // 选中时黄色边框
        circle.drawCircle(0, 0, 10)
      } else {
        // 存活状态：蓝色
        circle.beginFill(0x4169E1)
        circle.drawCircle(0, 0, 10)
        circle.endFill()
        circle.lineStyle(isSelected ? 3 : 2, isSelected ? 0xFFFF00 : 0xFFFFFF, 1)  // 选中时加粗黄色边框
        circle.drawCircle(0, 0, 10)
        
        // 添加外圈光晕效果
        if (isSelected) {
          circle.lineStyle(1, 0xFFFF00, 0.5)
          circle.drawCircle(0, 0, 14)
        }
      }
    })
  }, [selectedNPCId, focusedNPCId, npcs])

  // 🔥 重置视图
  const resetView = () => {
    setZoom(1.0)
    setOffset({ x: 0, y: 0 })
  }

  return (
    <div className="game-canvas-wrapper">
      <div ref={canvasRef} className="game-canvas" />
      
      {/* 🔥 相机控制 */}
      <div className="camera-controls">
        <button onClick={resetView} className="reset-button" title="重置视图">
          🔄
        </button>
        <div className="zoom-indicator" title="当前缩放比例">
          {(zoom * 100).toFixed(0)}%
        </div>
      </div>

      <style>{`
        .game-canvas-wrapper {
          position: relative;
          width: 100%;
          height: 100%;
          max-width: 1200px;
          max-height: 800px;
          margin: 0 auto;
          border: 2px solid #333;
          border-radius: 8px;
          overflow: hidden;
          background: #000;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }
        .game-canvas {
          width: 100%;
          height: 100%;
        }
        
        /* 相机控制样式 */
        .camera-controls {
          position: absolute;
          top: 10px;
          right: 10px;
          display: flex;
          gap: 8px;
          z-index: 10;
        }
        
        .reset-button {
          background: rgba(0, 0, 0, 0.7);
          color: white;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-radius: 6px;
          padding: 8px 12px;
          cursor: pointer;
          font-size: 18px;
          transition: all 0.2s;
        }
        
        .reset-button:hover {
          background: rgba(0, 0, 0, 0.85);
          border-color: rgba(255, 255, 255, 0.5);
          transform: scale(1.05);
        }
        
        .zoom-indicator {
          background: rgba(0, 0, 0, 0.7);
          color: white;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-radius: 6px;
          padding: 8px 12px;
          font-size: 14px;
          font-weight: bold;
          min-width: 60px;
          text-align: center;
        }
      `}</style>
    </div>
  )
}
