# 🌾 原始平原模拟

[English](README.md) | **简体中文**

---

## 📖 快速导航

- 🚀 [快速开始](#快速开始)
- 📚 [完整文档索引](DOCS_INDEX.md)
- 🏗️ [技术架构](ARCHITECTURE.md)
- 🤝 [贡献指南](CONTRIBUTING.md)
- 📊 [项目状态](PROJECT_STATUS.md)

---

## ✨ 项目简介

原始平原模拟是一个创新的AI驱动生存模拟游戏。游戏中的NPC使用大语言模型（DeepSeek）进行完全自主的决策，他们会：

- 🧠 **独立思考** - 每个NPC使用AI进行决策
- 🏗️ **建造家园** - 从篝火到木屋，逐步建立聚居地
- 🔨 **制作工具** - 制作斧头、镐子提高效率
- 💬 **社交互动** - NPC之间会交流、合作
- 🎭 **独特性格** - 每个NPC有独特的性格特质
- 🧠 **记忆学习** - 记住过去的经验，影响未来决策

---

## 🛠️ 技术栈

### 后端
- Python 3.11+ / FastAPI / Python-SocketIO
- OpenAI SDK (DeepSeek API)
- Pydantic / Uvicorn

### 前端  
- React 18 / TypeScript 5.2
- PixiJS 7 (2D WebGL渲染)
- Zustand (状态管理)
- Socket.IO Client / Vite

---

## 🚀 快速开始

### 💎 方式一：懒人包启动（强烈推荐！）

**🎁 零安装，开箱即用！** 无需安装Python和Node.js！

#### Windows
```bash
# 双击运行
一键启动.bat
```

**核心优势**：
- ✅ **完全独立** - 自带完整Python和Node.js环境
- ✅ **零配置** - 解压后直接双击启动
- ✅ **便于分享** - 可以直接打包给朋友玩

**内置环境**：
- Python 3.11（位于 `runtime/` 目录）
- Node.js 18+（位于 `node/` 目录）
- 所有Python和Node.js依赖已预装

> 💡 **首次运行**需要安装前端依赖（约2-5分钟），之后启动只需几秒！
>
> 📖 详细说明：[PORTABLE_GUIDE.md](PORTABLE_GUIDE.md)

---

### 🛠️ 方式二：开发者模式

**适合已有开发环境的用户**

#### 1️⃣ 克隆项目
```bash
git clone https://github.com/yourusername/plains-simulation.git
cd plains-simulation
```

#### 2️⃣ 配置API密钥
创建 `backend/.env` 文件：
```
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

#### 3️⃣ 启动游戏

**Windows:**
```bash
start_game.bat
```

**Linux/Mac:**
```bash
chmod +x start_game.sh
./start_game.sh
```

#### 4️⃣ 访问游戏
浏览器打开：http://localhost:5173

---

## 📚 文档完整索引

### 新手必读
- 📖 [README.md](README.md) - 完整项目文档（英文）
- 🚀 [START.md](START.md) - 详细启动指南
- 💻 [QUICKSTART.md](QUICKSTART.md) - 5分钟快速开发指南

### 开发者文档  
- 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md) - 技术架构详解
- 🤝 [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南
- 📋 [CHANGELOG.md](CHANGELOG.md) - 版本更新日志

### 其他
- 📊 [PROJECT_STATUS.md](PROJECT_STATUS.md) - 项目当前状态
- 📚 [DOCS_INDEX.md](DOCS_INDEX.md) - 完整文档索引
- 📄 [LICENSE](LICENSE) - MIT开源许可证

---

## 🎮 核心功能

### NPC系统
- ✅ AI驱动的自主决策
- ✅ 8种技能（伐木、采矿、觅食、战斗等）
- ✅ 6种性格特质（勇敢、社交、谨慎等）
- ✅ 生存需求（健康、饥饿、体力）
- ✅ 记忆系统（记住经历）

### 游戏系统
- ✅ 5种资源（木材、石头、浆果、水、肉）
- ✅ 5种建筑（篝火、棚屋、木屋、储物棚、工作台）
- ✅ 5种工具/武器（石斧、石镐、长矛等）
- ✅ 昼夜循环和季节系统
- ✅ 实时2D可视化

### 特色功能
- ✅ 上帝模式（玩家可以干预世界）
- ✅ 实时事件日志
- ✅ NPC社交和对话
- ✅ 合作建造系统

---

## 📸 截图

> 添加游戏截图...

---

## 🤝 参与贡献

我们欢迎所有形式的贡献！

1. 🐛 **报告Bug** - 使用[Bug报告模板](.github/ISSUE_TEMPLATE/bug_report.md)
2. 💡 **建议功能** - 使用[功能建议模板](.github/ISSUE_TEMPLATE/feature_request.md)
3. 💻 **贡献代码** - 查看[贡献指南](CONTRIBUTING.md)
4. 📖 **改进文档** - 文档也是贡献！

---

## 📅 开发路线图

### v1.0.0 ✅ (当前)
- [x] 核心游戏系统
- [x] AI决策系统
- [x] 基础建筑和制作
- [x] 完整文档体系

### v1.1.0 🚧 (进行中)
- [ ] 持久化存储（保存/加载）
- [ ] Redis缓存
- [ ] 性能优化

### v1.2.0 📅 (计划中)
- [ ] 农业系统
- [ ] 种植和收获
- [ ] 更多建筑类型

### v2.0.0 🔮 (未来)
- [ ] 多人协作模式
- [ ] Mod支持
- [ ] 移动端适配

---

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [PixiJS](https://pixijs.com/)
- [DeepSeek](https://www.deepseek.com/)
- [React](https://reactjs.org/)

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。

---

## 📞 联系我们

- 🐛 **问题反馈**: [GitHub Issues](https://github.com/yourusername/plains-simulation/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/yourusername/plains-simulation/discussions)
- 📧 **邮件**: 待添加

---

## 🌟 支持项目

如果你觉得这个项目有趣：
- ⭐ 给项目点个Star
- 🔄 Fork并尝试开发
- 📢 分享给朋友
- 🤝 参与贡献

---

<div align="center">

**用AI创造生命，用代码模拟世界** 🌍✨

Made with ❤️ by the Plains Simulation Team

[完整文档](README.md) | [快速开始](START.md) | [开发指南](QUICKSTART.md)

</div>

