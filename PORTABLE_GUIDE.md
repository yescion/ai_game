# 🚀 懒人包使用指南 | Portable Edition Guide

本游戏提供了**完全独立的懒人包版本**，无需安装任何软件即可运行！

---

## 📦 两种启动方式

### 🌟 方式一：懒人包启动（推荐）

#### 文件：`一键启动.bat`

**特点**：
- ✅ **零安装** - 无需安装 Python 或 Node.js
- ✅ **开箱即用** - 解压即可运行
- ✅ **完全独立** - 自带所有运行环境
- ✅ **适合分享** - 可以直接分享给朋友

**使用方法**：
```
1. 双击 "一键启动.bat"
2. 等待自动安装前端依赖（首次运行需要几分钟）
3. 浏览器自动打开游戏
```

**内置环境**：
- Python 3.11（位于 `runtime/` 目录）
- Node.js 18+（位于 `node/` 目录）
- 所有必需的Python包
- 所有系统依赖库

---

### 🛠️ 方式二：开发者模式

#### 文件：`start_game.bat`

**特点**：
- ⚙️ **需要系统环境** - 需要已安装 Python 和 Node.js
- 🔧 **适合开发** - 使用系统环境，便于调试
- 📦 **更灵活** - 可以自定义 Python 版本和包

**使用方法**：
```
1. 确保已安装 Python 3.11+ 和 Node.js 18+
2. 双击 "start_game.bat"
3. 自动创建虚拟环境并安装依赖
4. 浏览器自动打开游戏
```

---

## 📂 目录结构说明

```
游戏根目录/
├── 一键启动.bat          # 懒人包启动脚本（推荐）
├── start_game.bat        # 开发者启动脚本
├── start_backend.bat     # 单独启动后端
│
├── runtime/              # 🔥 内置Python环境
│   ├── python.exe       # Python 3.11 解释器
│   ├── python311.dll    # Python DLL
│   ├── Lib/             # Python 标准库
│   └── Scripts/         # Python 工具（pip等）
│
├── node/                 # 🔥 内置Node.js环境
│   ├── node.exe         # Node.js 运行时
│   ├── npm.cmd          # NPM 包管理器
│   └── node_modules/    # NPM 核心模块
│
├── backend/              # 后端代码
│   ├── app/             # 应用代码
│   ├── requirements.txt # Python 依赖
│   └── run.py           # 启动脚本
│
├── frontend/             # 前端代码
│   ├── src/             # 源代码
│   ├── package.json     # Node.js 依赖
│   └── node_modules/    # (首次运行后生成)
│
└── docs/                 # 文档
```

---

## 🎯 首次运行流程

### 懒人包模式（一键启动.bat）

```
[1/5] 检查运行环境
  ✓ 检查 runtime/python.exe
  ✓ 检查 node/node.exe

[2/5] 配置环境变量
  ✓ 设置 NODE_PATH 为本地 node 目录
  ✓ 添加到 PATH 环境变量

[3/5] 检查前端依赖
  ⏳ 首次运行：安装 node_modules（约2-5分钟）
  ✓ 已运行过：跳过

[4/5] 启动后端服务器
  ✓ 使用 runtime/python.exe 运行后端

[5/5] 启动前端服务器
  ✓ 使用 node/node.exe 运行前端

✨ 完成！浏览器自动打开
```

---

## 💡 常见问题

### Q: 为什么首次运行要等很久？
**A:** 首次运行需要安装前端依赖（node_modules），这是正常的。只需等待一次，之后启动只需几秒。

### Q: 可以删除 runtime 或 node 目录吗？
**A:** 
- 使用**懒人包模式**：不能删除，这些是必需的运行环境
- 使用**开发者模式**：可以删除，会使用系统环境

### Q: 如何更新游戏？
**A:** 
1. 保留 `runtime/` 和 `node/` 目录
2. 替换 `backend/` 和 `frontend/` 目录
3. 重新运行 `一键启动.bat`

### Q: 游戏启动失败怎么办？
**A:** 检查以下几点：
1. 是否完整解压了所有文件
2. `runtime/python.exe` 是否存在
3. `node/node.exe` 是否存在
4. 防火墙是否阻止了程序
5. 端口 8000 和 5173 是否被占用

### Q: 可以同时运行多个游戏实例吗？
**A:** 可以，但需要修改端口配置以避免冲突。

### Q: 懒人包的体积有多大？
**A:** 
- Python runtime: ~100MB
- Node.js: ~50MB
- 前端依赖（首次安装后）: ~200MB
- 总计: 约 350MB

### Q: 支持哪些操作系统？
**A:** 
- ✅ Windows 10/11 (x64)
- ⚠️ Windows 7/8（可能需要额外依赖）
- ❌ Linux/Mac（需要使用开发者模式）

---

## 🔧 高级配置

### 修改后端端口
编辑 `backend/.env`:
```
PORT=8000  # 改为其他端口
```

### 修改前端端口
编辑 `frontend/vite.config.ts`:
```typescript
server: {
  port: 5173  // 改为其他端口
}
```

### 使用自己的 API Key
编辑 `backend/.env`:
```
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

---

## 📦 如何制作自己的懒人包

如果你想为其他项目制作类似的懒人包：

### 1. 准备 Python 环境
```bash
# 下载 Python embeddable package
# https://www.python.org/downloads/windows/
# 选择 "Windows embeddable package (64-bit)"

# 解压到 runtime/ 目录
# 安装 pip：下载 get-pip.py
runtime\python.exe get-pip.py

# 安装项目依赖
runtime\python.exe -m pip install -r requirements.txt
```

### 2. 准备 Node.js 环境
```bash
# 下载 Node.js portable
# https://nodejs.org/en/download/

# 解压到 node/ 目录
```

### 3. 修改启动脚本
参考本项目的 `一键启动.bat`，使用绝对路径调用 `runtime\python.exe` 和 `node\node.exe`。

---

## 🌟 使用技巧

### 1. 创建桌面快捷方式
右键 `一键启动.bat` → 发送到 → 桌面快捷方式

### 2. 修改快捷方式图标
右键快捷方式 → 属性 → 更改图标

### 3. 静默启动（不显示命令窗口）
创建 VBS 脚本：
```vbs
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "一键启动.bat" & chr(34), 0
Set WshShell = Nothing
```

### 4. 开机自启动
将快捷方式放到：
```
C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup
```

---

## 📝 更新日志

### v1.0.1 (2024-10-21)
- ✅ 添加完整的懒人包支持
- ✅ 内置 Python 3.11 和 Node.js 18
- ✅ 优化首次运行体验
- ✅ 添加详细的进度提示

### v1.0.0 (2024-10-21)
- 🎉 首次发布

---

## 🙏 感谢

感谢使用本游戏！如果你喜欢这个项目：
- ⭐ 给项目点个 Star
- 📢 分享给朋友
- 🐛 报告 Bug
- 💡 提出建议

---

## 📞 需要帮助？

- 📖 查看完整文档：[README.md](README.md)
- 🚀 启动问题：[START.md](START.md)
- 💻 开发指南：[QUICKSTART.md](QUICKSTART.md)
- 🐛 报告问题：GitHub Issues

---

<div align="center">

**享受游戏！** 🎮✨

Made with ❤️ by Plains Simulation Team

</div>

