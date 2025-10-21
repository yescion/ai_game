# 🚀 启动游戏 - 快速指南

## 方法一：使用脚本自动启动（推荐）

### Windows

双击运行 `start_game.bat`

或在命令行中：
```bash
start_game.bat
```

### Linux/Mac

```bash
chmod +x start_game.sh
./start_game.sh
```

## 方法二：手动启动

### 1. 启动后端

```bash
# 进入后端目录
cd backend

# 激活虚拟环境（如果已创建）
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 如果是第一次运行，需要安装依赖
pip install -r requirements.txt

# 启动后端服务器
python run.py
```

**后端启动成功标志：**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
🎮 游戏启动成功！
```

### 2. 启动前端

**新开一个终端窗口**，然后：

```bash
# 进入前端目录
cd frontend

# 如果是第一次运行，需要安装依赖
npm install

# 启动前端开发服务器
npm run dev
```

**前端启动成功标志：**
```
  VITE v5.0.8  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

### 3. 打开游戏

在浏览器中访问：http://localhost:5173

## 🎮 开始游戏

### 首次运行

1. 后端会自动生成一个原始平原世界
2. 5个NPC会在平原中心出生
3. 他们会开始自主行动、采集资源、建立聚居地

### 游戏界面

- **顶部栏**: 游戏时间、资源统计、连接状态
- **左侧**: 事件时间轴 - 查看所有发生的事件
- **中央**: 游戏世界 - 2D可视化
- **右侧**: NPC状态面板 - 查看每个NPC的详情

### 操作

- **点击NPC**: 查看详细信息（技能、背包、AI思考过程）
- **观察**: 观察NPC如何自主生存、建造、合作

## ✅ 检查清单

### 后端正常运行

- [ ] 能访问 http://localhost:8000
- [ ] 能访问 http://localhost:8000/docs (API文档)
- [ ] 控制台显示"游戏启动成功"
- [ ] 没有报错信息

### 前端正常运行

- [ ] 能访问 http://localhost:5173
- [ ] 页面显示"原始平原模拟"标题
- [ ] 右上角显示"已连接"（绿点）
- [ ] 能看到5个NPC在地图上
- [ ] 事件日志有内容

## ❌ 常见问题

### 后端启动失败

**问题**: `ModuleNotFoundError: No module named 'fastapi'`

**解决**:
```bash
cd backend
pip install -r requirements.txt
```

---

**问题**: `AttributeError: module 'socketio' has no attribute 'AsyncServer'`

**解决**:
```bash
pip uninstall socketio python-socketio
pip install python-socketio==5.10.0
```

---

**问题**: API调用失败 / AI不工作

**解决**: 检查 `backend/.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确

### 前端启动失败

**问题**: `npm command not found`

**解决**: 安装 Node.js (https://nodejs.org/)

---

**问题**: 依赖安装失败

**解决**:
```bash
cd frontend
npm cache clean --force
npm install
```

---

**问题**: 前端显示"未连接"

**解决**:
1. 确保后端正在运行
2. 检查后端是否在 http://localhost:8000
3. 刷新页面

### 游戏运行问题

**问题**: NPC不动 / 没有事件

**解决**:
1. 打开浏览器开发者工具（F12）查看Console
2. 检查是否有WebSocket连接错误
3. 重启后端和前端

---

**问题**: AI决策很慢

**解决**: 这是正常的，AI调用需要时间。可以：
- 检查网络连接
- DeepSeek API可能响应较慢

## 🛑 停止游戏

### 停止后端
在后端终端按 `Ctrl+C`

### 停止前端
在前端终端按 `Ctrl+C`

## 📝 开发模式

### 后端热重载
后端使用 `--reload` 参数，修改代码会自动重启

### 前端热重载
前端使用 Vite，保存文件会自动刷新浏览器

### 查看日志

**后端日志**: 在后端终端查看
**前端日志**: 按F12打开浏览器控制台


**祝你游戏愉快！** 🎮✨

如果遇到其他问题，请查看完整文档或提交Issue。

