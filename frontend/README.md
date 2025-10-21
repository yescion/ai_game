# 原始平原模拟 - 前端

React + TypeScript + PixiJS 2D游戏前端。

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 技术栈

- **React 18** - UI框架
- **TypeScript** - 类型安全
- **PixiJS 7** - 2D渲染引擎
- **Zustand** - 轻量级状态管理
- **Socket.IO Client** - WebSocket通信
- **Vite** - 快速构建工具

## 项目结构

```
src/
├── components/      # React组件
│   ├── GameCanvas.tsx      # 主游戏画布
│   ├── EventTimeline.tsx   # 事件日志
│   ├── NPCPanel.tsx        # NPC面板
│   └── TopBar.tsx          # 顶部栏
├── store/           # 状态管理
│   └── gameStore.ts        # Zustand store
├── services/        # 服务层
│   └── socketService.ts    # WebSocket服务
├── types/           # TypeScript类型
│   └── index.ts
├── App.tsx          # 根组件
└── main.tsx         # 入口文件
```

## 开发

### 添加新组件

1. 在 `src/components/` 创建新的 `.tsx` 文件
2. 导入必要的hooks: `useGameStore` 等
3. 在 `App.tsx` 中引入

### 修改游戏状态

编辑 `src/store/gameStore.ts`：

```typescript
export const useGameStore = create<GameStore>((set) => ({
  // 添加新状态
  myNewState: null,
  
  // 添加新action
  setMyNewState: (value) => set({ myNewState: value }),
}))
```

### 监听服务器事件

编辑 `src/services/socketService.ts`：

```typescript
this.socket.on('my_event', (data) => {
  // 处理事件
  useGameStore.getState().setMyNewState(data)
})
```

## 环境变量

创建 `.env.local` 文件：

```env
VITE_API_URL=http://localhost:8000
```

## 构建部署

```bash
# 构建
npm run build

# 输出目录: dist/
# 可以使用任何静态文件服务器部署
```

## 性能优化

- PixiJS使用WebGL渲染，性能优秀
- 使用 `useMemo` 和 `useCallback` 优化React组件
- WebSocket仅传输必要的数据更新

## 已知问题

- [ ] 资源精灵图未实现，使用文本显示
- [ ] 地图缩放和拖拽未实现
- [ ] 建筑动画未实现

## 许可证

MIT

