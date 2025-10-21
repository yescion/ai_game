# 技术架构文档

本文档详细说明了原始平原模拟项目的技术架构和设计决策。

---

## 📐 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户浏览器                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              React前端 (TypeScript)                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │ UI组件   │  │ 状态管理  │  │  PixiJS渲染引擎  │  │   │
│  │  │ (React)  │  │ (Zustand) │  │   (WebGL 2D)    │  │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘  │   │
│  └─────────────────┬───────────────────────────────────┘   │
└────────────────────┼───────────────────────────────────────┘
                     │ WebSocket (Socket.IO)
                     │ HTTP/REST API
┌────────────────────┼───────────────────────────────────────┐
│                    │     后端服务器 (Python)                │
│  ┌─────────────────┴───────────────────────────────────┐   │
│  │           FastAPI + Socket.IO Server               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │ REST API │  │ WebSocket │  │  事件广播系统    │  │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘  │   │
│  └─────────────────┬───────────────────────────────────┘   │
│  ┌─────────────────┴───────────────────────────────────┐   │
│  │              游戏主循环 (Game Loop)                  │   │
│  │  - 世界状态管理                                       │   │
│  │  - NPC行动调度                                        │   │
│  │  - 物理引擎                                           │   │
│  │  - 事件系统                                           │   │
│  └─────────────────┬───────────────────────────────────┘   │
│  ┌─────────────────┴───────────────────────────────────┐   │
│  │                   核心服务层                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │AI决策服务│  │记忆服务  │  │  世界生成器      │  │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘  │   │
│  └─────────────────┬───────────────────────────────────┘   │
│  ┌─────────────────┴───────────────────────────────────┐   │
│  │                   数据模型层                          │   │
│  │  - NPC模型  - 世界模型  - 资源模型  - 建筑模型      │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬───────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────┼───────────────────────────────────────┐
│                    │   外部服务                             │
│  ┌─────────────────┴───────────────────────────────────┐   │
│  │              DeepSeek AI API                        │   │
│  │       (或任何OpenAI兼容的API)                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 后端架构

### 技术栈
- **框架**：FastAPI (异步Web框架)
- **WebSocket**：Python-SocketIO (实时双向通信)
- **数据验证**：Pydantic (类型安全的数据模型)
- **AI集成**：OpenAI SDK (调用DeepSeek API)

### 核心组件

#### 1. FastAPI应用 (`app/main.py`)

```python
FastAPI应用
├── CORS中间件 (允许跨域)
├── Socket.IO集成
├── REST API路由
│   ├── GET /api/world
│   ├── GET /api/npcs
│   ├── GET /api/buildings
│   └── ...
└── WebSocket事件处理
    ├── connect/disconnect
    ├── client_ready
    ├── god_add_memory
    └── ...
```

**设计决策**：
- 使用异步编程提高并发性能
- WebSocket用于实时更新，REST API用于状态查询
- 单例模式管理游戏循环

#### 2. 游戏主循环 (`services/game_loop.py`)

```python
MainGameLoop
├── 初始化世界
│   └── 调用 WorldGenerator
├── 游戏循环 (async)
│   ├── 时间推进
│   ├── NPC决策调度
│   │   └── 每个NPC独立决策
│   ├── 行动执行
│   │   ├── 移动系统
│   │   ├── 采集系统
│   │   ├── 建造系统
│   │   └── ...
│   ├── 物理更新
│   │   └── PhysicsEngine
│   ├── 资源再生
│   └── 状态广播
│       └── WebSocket emit
└── 事件处理
```

**关键特性**：
- 非阻塞异步循环
- 客户端连接后才开始主循环（避免浪费资源）
- 增量更新机制（仅广播变化）
- 错误恢复机制

**循环频率**：
- 主循环：每秒10帧（100ms/帧）
- NPC决策：每30-60秒一次（可配置）
- 状态广播：实时（有变化时）

#### 3. AI决策服务 (`services/ai_service.py`)

```python
AIService
├── 生成决策提示词
│   ├── 当前状态（健康、饥饿、体力）
│   ├── 周围环境（资源、建筑、NPC）
│   ├── 个人记忆（最近事件）
│   ├── 性格特质
│   └── 可用行动列表
├── 调用AI API
│   ├── 模型：deepseek-chat
│   ├── Temperature: 0.8
│   └── Max Tokens: 500
├── 解析AI响应
│   └── JSON格式提取
└── 日志记录
    └── logs/npc_decisions/
```

**Prompt设计原则**：
- 结构化信息（易于AI理解）
- 包含约束条件（避免不合理决策）
- 提供上下文（记忆和状态）
- 输出格式规范（JSON）

**容错机制**：
- AI调用失败 → 回退到规则基础决策
- 解析失败 → 使用默认行动（休息）
- 超时处理 → 设置合理的timeout

#### 4. 数据模型 (`models/`)

```python
数据模型层 (Pydantic)
├── NPC2D
│   ├── 基础属性 (id, name, position)
│   ├── 生存需求 (health, hunger, stamina)
│   ├── 技能 (8种技能 0-100)
│   ├── 性格 (6种特质 0-100)
│   ├── 背包 (inventory)
│   ├── 装备 (equipment)
│   ├── 记忆 (memories)
│   └── 关系 (relationships)
├── WorldState2D
│   ├── 地图大小
│   ├── 时间系统
│   ├── 天气
│   ├── NPC列表
│   ├── 建筑列表
│   ├── 资源列表
│   ├── 野兽列表
│   └── 事件列表
├── Building2D
│   ├── 类型和位置
│   ├── 建造进度
│   ├── 功能属性
│   └── 存储空间
└── ResourceNode
    ├── 类型和位置
    ├── 剩余数量
    └── 再生速率
```

**优势**：
- 类型安全（运行时验证）
- 自动JSON序列化
- IDE智能提示
- 文档自动生成

---

## 🎨 前端架构

### 技术栈
- **框架**：React 18 (函数式组件 + Hooks)
- **状态管理**：Zustand (轻量级)
- **渲染引擎**：PixiJS 7 (WebGL)
- **构建工具**：Vite (快速HMR)

### 核心组件

#### 1. 应用结构

```
App.tsx
├── TopBar (顶部状态栏)
│   ├── 游戏时间显示
│   ├── 连接状态
│   └── 资源统计
├── 主内容区
│   ├── EventTimeline (事件时间线)
│   │   └── 滚动事件日志
│   ├── GameCanvas (游戏画布)
│   │   └── PixiJS渲染
│   └── NPCPanel (NPC面板)
│       └── NPC列表和详情
├── ObjectInfoPanel (对象信息面板)
│   └── 点击对象查看详情
└── GodConsole (上帝控制台)
    └── 玩家干预界面
```

#### 2. 状态管理 (`store/gameStore.ts`)

```typescript
Zustand Store
├── 世界状态
│   ├── world (WorldState | null)
│   ├── npcs (NPC[])
│   ├── buildings (Building[])
│   └── resources (Resource[])
├── UI状态
│   ├── selectedNPC (string | null)
│   ├── selectedObject (Object | null)
│   ├── isConnected (boolean)
│   └── error (string | null)
├── Actions
│   ├── setWorld()
│   ├── updateWorld()
│   ├── selectNPC()
│   └── setError()
└── 派生状态 (computed)
```

**设计决策**：
- Zustand而非Redux：更轻量，代码更少
- 单一Store：避免状态分散
- 不可变更新：保证React渲染正确

#### 3. PixiJS渲染 (`components/GameCanvas.tsx`)

```typescript
GameCanvas (PixiJS)
├── 应用初始化
│   └── new Application({...})
├── 舞台层次
│   ├── 地面层 (terrainContainer)
│   ├── 资源层 (resourcesContainer)
│   ├── 建筑层 (buildingsContainer)
│   └── NPC层 (npcsContainer)
├── 渲染对象
│   ├── 地形网格 (Tilemap)
│   ├── 资源节点 (Sprite/Text)
│   ├── 建筑 (Sprite/Graphics)
│   └── NPC (Sprite + HealthBar)
├── 交互
│   ├── 点击选择NPC/对象
│   ├── 鼠标悬停提示
│   └── 拖拽地图 (未来)
└── 动画
    ├── NPC移动补间
    ├── 建造进度条
    └── 资源采集动画
```

**性能优化**：
- 使用Container组织层次（减少遍历）
- 对象池（复用Sprite对象）
- 增量更新（仅更新变化的对象）
- WebGL渲染（GPU加速）

**帧率目标**：60 FPS

#### 4. WebSocket服务 (`services/socketService.ts`)

```typescript
SocketService
├── 连接管理
│   ├── connect()
│   ├── disconnect()
│   └── 重连机制
├── 事件监听
│   ├── world_state (完整状态)
│   ├── world_update (增量更新)
│   ├── npc_action (行动事件)
│   └── game_event (游戏事件)
├── 事件发送
│   ├── client_ready
│   ├── god_add_memory
│   └── ...
└── 状态同步
    └── 更新 gameStore
```

**可靠性保证**：
- 自动重连（断线后尝试重连）
- 心跳检测（检测连接是否活跃）
- 错误处理（网络错误提示用户）

---

## 🔄 数据流

### 游戏状态更新流程

```
1. 后端游戏循环更新状态
   └── MainGameLoop.update()

2. 检测状态变化
   └── 对比上一帧状态

3. 通过WebSocket广播
   └── sio.emit('world_update', data)

4. 前端接收更新
   └── socket.on('world_update', ...)

5. 更新Zustand Store
   └── gameStore.updateWorld(data)

6. React组件重新渲染
   └── useGameStore() -> 组件更新

7. PixiJS渲染新帧
   └── 更新Sprite位置、状态等
```

### NPC决策流程

```
1. 游戏循环检测NPC是否空闲
   └── npc.is_idle(current_time)

2. 调用AI决策服务
   └── ai_service.generate_npc_decision(npc, world, memories)

3. 生成提示词
   └── generate_npc_decision_prompt()
   ├── 包含NPC状态
   ├── 包含周围环境
   ├── 包含记忆
   └── 包含可用行动

4. 调用DeepSeek API
   └── client.chat.completions.create()

5. 解析AI响应
   └── 提取action、target、reasoning

6. 执行行动
   └── game_loop.execute_action(npc, action)

7. 更新NPC状态
   └── 修改position、inventory等

8. 记录到记忆
   └── npc.memories.append()

9. 广播更新
   └── emit('npc_action', {...})
```

---

## 🧩 关键设计模式

### 1. 单例模式
**位置**：`MainGameLoop`

**理由**：整个服务器只需要一个游戏循环实例

### 2. 观察者模式
**位置**：WebSocket事件系统

**理由**：前端订阅后端事件，实现解耦

### 3. 策略模式
**位置**：行动执行系统

**理由**：不同行动类型有不同执行逻辑

### 4. 工厂模式
**位置**：世界生成器

**理由**：批量创建NPC、资源节点、建筑

### 5. 命令模式
**位置**：上帝指令系统

**理由**：封装玩家操作为命令对象

---

## 📊 性能考虑

### 后端性能

| 指标 | 目标 | 实际 |
|------|------|------|
| 游戏循环频率 | 10 FPS | 10 FPS |
| NPC决策延迟 | < 5s | 2-5s (取决于API) |
| WebSocket延迟 | < 50ms | 20-40ms |
| 内存占用 | < 500MB | ~200MB (5 NPC) |

**优化措施**：
- 异步非阻塞IO
- AI调用并发限制（避免过载）
- 事件日志限制数量（防止内存泄漏）
- 增量更新（减少传输数据）

### 前端性能

| 指标 | 目标 | 实际 |
|------|------|------|
| 渲染帧率 | 60 FPS | 55-60 FPS |
| 首次渲染 | < 3s | ~2s |
| 内存占用 | < 200MB | ~150MB |

**优化措施**：
- PixiJS WebGL渲染
- React组件useMemo/useCallback
- 虚拟滚动（事件列表）
- 对象池（Sprite复用）

---

## 🔒 安全考虑

### API密钥保护
- 环境变量存储（不提交到Git）
- 服务器端调用（不暴露给前端）

### 输入验证
- Pydantic模型验证所有输入
- API参数类型检查

### WebSocket安全
- CORS配置（限制来源）
- 连接数限制（防止DDoS）

### 未来计划
- [ ] 用户认证（JWT）
- [ ] 权限系统
- [ ] 速率限制（Rate Limiting）
- [ ] 输入过滤（防XSS）

---

## 🔮 扩展性设计

### 水平扩展
当前设计支持：
- 多个游戏实例（不同房间）
- 负载均衡（Nginx + 多进程）
- Redis共享状态（可选）

### 垂直扩展
- 增加NPC数量（优化算法复杂度）
- 增大地图（分块加载）
- 更多实体类型（扩展模型）

### 模块化
- 插件系统（未来）
- Mod支持（未来）
- 自定义事件（未来）

---

## 📖 参考资料

### 技术文档
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [PixiJS文档](https://pixijs.com/)
- [Zustand文档](https://github.com/pmndrs/zustand)
- [Socket.IO文档](https://socket.io/)

### 设计参考
- 《游戏编程模式》
- 《人工智能游戏编程真言》
- Dwarf Fortress (复杂模拟)
- RimWorld (AI决策)

---

**最后更新**：2024-10-21

