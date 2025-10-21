# 🚀 快速开发指南

5分钟快速上手开发原始平原模拟。

---

## 📋 前置清单

确保你已安装：
- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ Git
- ✅ VS Code（推荐）或其他IDE

---

## 1️⃣ 克隆并启动（3分钟）

### 克隆仓库
```bash
git clone https://github.com/yourusername/plains-simulation.git
cd plains-simulation
```

### 配置API密钥
创建 `backend/.env` 文件：
```bash
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 一键启动
**Windows:**
```bash
一键启动.bat
```

**Linux/Mac:**
```bash
chmod +x start_game.sh
./start_game.sh
```

### 访问游戏
打开浏览器：http://localhost:5173

---

## 2️⃣ 开发环境设置（5分钟）

### 后端开发环境

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器（支持热重载）
python run.py
```

### 前端开发环境

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（支持HMR）
npm run dev
```

---

## 3️⃣ 你的第一个功能（10分钟）

### 示例：添加新的NPC行动 "跳舞"

#### Step 1: 定义行动类型
`backend/app/models/actions.py`:
```python
class ActionType:
    # ... 现有行动
    DANCE = "dance"  # 新增
```

#### Step 2: 更新AI提示词
`backend/app/prompts/npc_decision_prompt.py`:
```python
available_actions.append({
    "action": "dance",
    "description": "跳舞娱乐自己和他人",
    "when_to_use": "当体力充足且心情好时",
    "parameters": {}
})
```

#### Step 3: 实现行动逻辑
`backend/app/services/game_loop.py` 中的 `execute_action()`:
```python
elif action.action == ActionType.DANCE:
    # 消耗体力
    npc.attributes.stamina -= 5
    
    # 增加社交经验
    npc.skills['social'] = min(100, npc.skills['social'] + 0.5)
    
    # 记录事件
    self.log_event(
        f"💃 {npc.name}开心地跳起了舞！",
        importance="low",
        related_npcs=[npc.id]
    )
    
    # 记录到NPC记忆
    npc.memories.append(f"我跳了一支舞，心情很好！")
```

#### Step 4: 测试
1. 重启后端（自动重载）
2. 等待NPC执行"跳舞"行动
3. 在事件日志中查看

#### Step 5: 前端显示（可选）
在 `frontend/src/components/GameCanvas.tsx` 添加特效：
```typescript
if (npc.current_action === 'dance') {
  // 添加跳舞动画或特效
}
```

---

## 4️⃣ 常用开发任务

### 修改AI模型参数
`backend/app/services/ai_service.py`:
```python
response = self.client.chat.completions.create(
    model="deepseek-chat",
    temperature=0.8,  # 调整这个值改变创造性
    max_tokens=500
)
```

### 调整游戏速度
`backend/app/main.py`:
```python
config = GameConfig(
    time_scale=60.0  # 越小游戏越快
)
```

### 增加初始资源
`backend/app/services/world_generator.py`:
```python
# 修改资源生成数量
for _ in range(50):  # 增加到50个树
    self._create_tree(world)
```

### 修改NPC初始技能
`backend/app/services/world_generator.py` 中的 `_create_npc()`:
```python
skills = {
    "woodcutting": random.randint(10, 30),  # 提高初始值
    # ...
}
```

### 添加新UI组件
```bash
cd frontend/src/components
# 创建新组件
touch MyNewComponent.tsx
```

```tsx
// MyNewComponent.tsx
import { useGameStore } from '../store/gameStore'

export function MyNewComponent() {
  const { world } = useGameStore()
  
  return (
    <div className="my-component">
      {/* 你的UI */}
    </div>
  )
}
```

---

## 5️⃣ 调试技巧

### 查看后端日志
后端终端会显示所有日志。

### 查看NPC决策详情
文件位置：`backend/logs/npc_decisions/{npc_name}.log`

### 前端调试
```javascript
// 在浏览器Console中
console.log(window.__gameStore.getState())
```

### 测试WebSocket连接
```javascript
// 浏览器Console
io("http://localhost:8000")
```

### 强制NPC执行特定行动（临时测试）
在 `game_loop.py` 中：
```python
# 临时测试代码
action = NPCAction(
    action="dance",
    description="测试跳舞",
    reasoning="开发测试"
)
await self.execute_action(npc, action)
```

---

## 6️⃣ 代码风格

### Python
```python
# 好的命名
def calculate_movement_distance(npc: NPC2D, target: Position2D) -> float:
    """计算移动距离。
    
    Args:
        npc: NPC对象
        target: 目标位置
        
    Returns:
        float: 距离值
    """
    pass
```

### TypeScript
```typescript
// 好的命名
interface NPCData {
  id: string
  name: string
  position: Position2D
}

function calculateDistance(a: Position2D, b: Position2D): number {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
}
```

---

## 7️⃣ 常见错误

### ❌ 模块导入错误
```
ModuleNotFoundError: No module named 'fastapi'
```
**解决**：确保激活了虚拟环境并安装了依赖
```bash
pip install -r requirements.txt
```

### ❌ WebSocket连接失败
```
前端显示"未连接"
```
**解决**：
1. 检查后端是否在运行
2. 检查端口8000是否被占用
3. 清除浏览器缓存

### ❌ AI调用失败
```
AI decision failed: Unauthorized
```
**解决**：检查 `.env` 中的 API Key 是否正确

### ❌ 前端白屏
**解决**：
1. 打开浏览器Console查看错误
2. 检查Node版本是否 >= 18
3. 删除 `node_modules` 重新安装

---

## 8️⃣ 有用的快捷键

### VS Code
- `Ctrl + P` - 快速打开文件
- `Ctrl + Shift + P` - 命令面板
- `F5` - 启动调试
- `Ctrl + ~` - 打开终端

### 浏览器
- `F12` - 开发者工具
- `Ctrl + Shift + R` - 硬刷新
- `F5` - 刷新页面

---

## 9️⃣ 推荐VS Code插件

- **Python** - Python语言支持
- **Pylance** - Python智能提示
- **ESLint** - TypeScript/JavaScript Linting
- **Prettier** - 代码格式化
- **GitLens** - Git增强
- **Thunder Client** - API测试

---

## 🔟 下一步

- 📖 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解架构
- 🤝 阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献流程
- 💬 加入讨论区提问
- 🐛 在Issues中报告Bug

---

## 📚 学习资源

### Python/FastAPI
- [FastAPI官方教程](https://fastapi.tiangolo.com/tutorial/)
- [Python异步编程](https://docs.python.org/3/library/asyncio.html)

### React/TypeScript
- [React官方文档](https://react.dev/)
- [TypeScript手册](https://www.typescriptlang.org/docs/)

### PixiJS
- [PixiJS教程](https://pixijs.io/guides/)
- [PixiJS示例](https://pixijs.io/examples/)

### AI集成
- [DeepSeek文档](https://www.deepseek.com/)
- [OpenAI API文档](https://platform.openai.com/docs/)

---

## 🎉 恭喜！

你现在已经掌握了开发的基础！开始创造属于你的功能吧！

有问题？在 [GitHub Issues](https://github.com/yourusername/plains-simulation/issues) 提问。

---

**Happy Coding!** 🚀✨

