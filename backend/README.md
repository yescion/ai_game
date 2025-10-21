# 原始平原模拟 - 后端

AI驱动的NPC模拟人生游戏后端服务。

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置你的 API 密钥：

```bash
cp .env.example .env
```

### 3. 运行服务器

```bash
# 开发模式
python run.py

# 或使用 uvicorn 直接运行
uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问API

- API 文档: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/socket.io/

## 项目结构

```
backend/
├── app/
│   ├── models/          # 数据模型
│   │   ├── npc.py      # NPC模型
│   │   ├── world.py    # 世界状态
│   │   ├── resources.py # 资源模型
│   │   └── ...
│   ├── services/        # 核心服务
│   │   ├── ai_service.py        # AI决策服务
│   │   ├── game_loop.py         # 游戏主循环
│   │   ├── world_generator.py   # 世界生成器
│   │   └── memory_service.py    # 记忆服务
│   ├── prompts/         # AI提示词模板
│   └── main.py          # FastAPI应用入口
├── requirements.txt     # Python依赖
├── .env                # 环境变量
└── run.py              # 启动脚本
```

## API端点

### REST API

- `GET /` - 健康检查
- `GET /api/world` - 获取世界状态
- `GET /api/npcs` - 获取所有NPC
- `GET /api/npcs/{npc_id}` - 获取特定NPC
- `GET /api/events` - 获取游戏事件

### WebSocket事件

客户端监听：
- `world_state` - 完整世界状态
- `world_update` - 世界更新
- `npc_action` - NPC行动事件
- `game_event` - 游戏事件

## 开发

### 添加新的NPC行为

1. 在 `app/models/actions.py` 添加新的行动类型
2. 在 `app/services/game_loop.py` 的 `execute_action` 添加处理逻辑
3. 在 `app/prompts/npc_decision_prompt.py` 更新可用行动列表

### 配置AI模型

修改 `app/services/ai_service.py` 中的模型参数：

```python
response = self.client.chat.completions.create(
    model="deepseek-chat",  # 模型名称
    temperature=0.8,         # 创造性 (0-1)
    max_tokens=500          # 最大tokens
)
```

## 许可证

MIT

