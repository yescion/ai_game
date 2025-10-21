# 贡献指南

感谢你考虑为原始平原模拟项目做出贡献！

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交指南](#提交指南)
- [问题报告](#问题报告)

---

## 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

---

## 如何贡献

### 报告Bug

如果你发现了Bug，请创建一个Issue并包含：

1. **清晰的标题**：简要描述问题
2. **重现步骤**：详细的复现步骤
3. **预期行为**：你期望发生什么
4. **实际行为**：实际发生了什么
5. **环境信息**：
   - 操作系统和版本
   - Python版本
   - Node.js版本
   - 浏览器和版本
6. **截图/日志**：如果适用，添加截图或错误日志

### 建议新功能

创建一个Feature Request Issue，包含：

1. **功能描述**：清晰描述建议的功能
2. **使用场景**：说明为什么需要这个功能
3. **可能的实现**：如果有想法，描述如何实现
4. **替代方案**：是否考虑过其他解决方案

### 提交代码

1. **Fork仓库**
2. **创建分支**：从`main`创建功能分支
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **进行更改**：编写代码并测试
4. **提交更改**：使用清晰的提交信息
   ```bash
   git commit -m "Add: 实现某某功能"
   ```
5. **推送分支**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **创建Pull Request**

---

## 开发流程

### 环境设置

#### 后端开发

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 前端开发

```bash
cd frontend
npm install
```

### 运行测试

#### 后端测试
```bash
cd backend
pytest
```

#### 前端测试
```bash
cd frontend
npm run test
```

### 运行Linter

#### Python (后端)
```bash
cd backend
flake8 app/
black app/ --check
mypy app/
```

#### TypeScript (前端)
```bash
cd frontend
npm run lint
```

---

## 代码规范

### Python (后端)

- 遵循 **PEP 8** 规范
- 使用 **Black** 格式化代码
- 使用类型提示（Type Hints）
- 文档字符串使用Google风格

```python
def example_function(param1: str, param2: int) -> bool:
    """简短描述函数功能。

    详细描述（如果需要）。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值描述

    Raises:
        ValueError: 何时抛出异常
    """
    pass
```

### TypeScript (前端)

- 遵循项目的 **ESLint** 配置
- 使用函数式组件和Hooks
- 使用TypeScript类型，避免`any`
- 组件使用命名导出

```tsx
interface MyComponentProps {
  title: string
  count: number
}

export function MyComponent({ title, count }: MyComponentProps) {
  // 组件实现
  return <div>{title}: {count}</div>
}
```

### 通用规范

- **文件命名**：
  - Python: `snake_case.py`
  - TypeScript: `PascalCase.tsx` (组件) 或 `camelCase.ts` (工具)
- **变量命名**：
  - Python: `snake_case`
  - TypeScript: `camelCase`
- **类命名**：`PascalCase`
- **常量命名**：`UPPER_SNAKE_CASE`

---

## 提交指南

### 提交信息格式

使用清晰、描述性的提交信息：

```
<类型>: <简短描述>

<详细描述>（可选）

<关联Issue>（可选）
```

### 类型标签

- `Add`: 添加新功能
- `Fix`: 修复Bug
- `Update`: 更新现有功能
- `Refactor`: 重构代码
- `Docs`: 文档更新
- `Style`: 代码格式化（不影响功能）
- `Test`: 添加或修改测试
- `Chore`: 构建工具、依赖更新等

### 示例

```
Add: 实现NPC疲劳系统

- 添加疲劳值属性到NPC模型
- 实现疲劳值随时间增加
- NPC疲劳时会优先选择休息

Closes #42
```

---

## Pull Request流程

### PR标题

使用与提交信息相同的格式：

```
Add: 实现NPC疲劳系统
```

### PR描述模板

```markdown
## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 代码重构
- [ ] 文档更新

## 变更描述
简要描述你的更改。

## 相关Issue
Closes #issue_number

## 测试
- [ ] 已添加单元测试
- [ ] 已进行手动测试
- [ ] 所有测试通过

## 截图（如适用）
添加截图展示变更效果。

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 已更新相关文档
- [ ] 已添加必要的注释
- [ ] 无Linter错误
- [ ] 已测试所有功能正常
```

### 审查流程

1. 提交PR后，维护者会进行审查
2. 如果需要修改，根据反馈进行调整
3. 所有审查通过后，PR会被合并
4. 你的贡献会被记录在项目历史中

---

## 问题报告

### Bug Report模板

```markdown
**Bug描述**
简要描述Bug。

**重现步骤**
1. 打开...
2. 点击...
3. 看到错误...

**预期行为**
应该发生什么。

**实际行为**
实际发生了什么。

**截图**
如果适用，添加截图。

**环境信息**
- OS: [例如 Windows 10, macOS 12, Ubuntu 22.04]
- Python版本: [例如 3.11.0]
- Node.js版本: [例如 18.16.0]
- 浏览器: [例如 Chrome 120, Firefox 121]

**额外信息**
其他相关信息。
```

### Feature Request模板

```markdown
**功能描述**
清晰简要地描述你想要的功能。

**使用场景**
为什么需要这个功能？它解决什么问题？

**建议的实现**
如果有想法，描述如何实现。

**替代方案**
是否考虑过其他解决方案？

**额外信息**
其他相关信息或截图。
```

---

## 开发建议

### 最佳实践

1. **保持更改小而专注**：每个PR应该解决一个问题或添加一个功能
2. **编写测试**：为新功能添加测试
3. **更新文档**：如果API或功能变更，更新相关文档
4. **保持同步**：经常从主分支拉取最新代码
5. **沟通**：如果有疑问，在Issue或PR中提问

### 有用的命令

#### 格式化代码
```bash
# Python
black app/

# TypeScript
npm run lint -- --fix
```

#### 运行完整测试
```bash
# 后端
cd backend
pytest --cov

# 前端
cd frontend
npm run test -- --coverage
```

---

## 贡献者

感谢所有贡献者！你的名字会出现在这里。

<!-- 贡献者列表会自动生成 -->

---

## 需要帮助？

如果你有任何问题：

1. 查看[文档](README.md)
2. 搜索[已有Issues](../../issues)
3. 在[Discussions](../../discussions)提问
4. 创建新Issue

---

**感谢你的贡献！** 🎉

每一个贡献，无论大小，都让这个项目变得更好。

