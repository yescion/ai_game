#!/bin/bash

echo "═══════════════════════════════════════════"
echo "🌾 原始平原模拟 - 启动脚本"
echo "═══════════════════════════════════════════"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ 错误：未找到Python"
    echo "请先安装Python 3.10+"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误：未找到Node.js"
    echo "请先安装Node.js 18+"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 启动后端
echo "📡 启动后端服务器..."
cd backend

# 检测是否有conda
if command -v conda &> /dev/null; then
    echo "检测到 Conda 环境"
    
    # 初始化conda（如果需要）
    eval "$(conda shell.bash hook)" 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
    
    # 检查ai_game环境是否存在
    if conda env list | grep -q "ai_game"; then
        echo "使用现有的 conda 环境: ai_game"
        conda activate ai_game
        pip install -r requirements.txt > /dev/null 2>&1
    else
        echo "创建 conda 环境: ai_game"
        conda create -n ai_game python=3.10 -y
        conda activate ai_game
        pip install -r requirements.txt > /dev/null 2>&1
    fi
    
    # 后台启动后端（使用conda）
    nohup bash -c "source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null; conda activate ai_game; python run.py" > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "后端PID: $BACKEND_PID (conda环境: ai_game)"
else
    echo "使用 Python venv 虚拟环境"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    
    # 后台启动后端
    nohup python run.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "后端PID: $BACKEND_PID (venv)"
fi

cd ..
sleep 3

# 启动前端
echo "🎨 启动前端服务器..."
cd frontend

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 后台启动前端
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端PID: $FRONTEND_PID"

cd ..
sleep 3

echo ""
echo "═══════════════════════════════════════════"
echo "✅ 游戏启动完成！"
echo "═══════════════════════════════════════════"
echo ""
echo "🌐 打开浏览器访问: http://localhost:5173"
echo "📊 后端API文档: http://localhost:8000/docs"
echo ""
echo "💡 进程ID："
echo "   后端: $BACKEND_PID"
echo "   前端: $FRONTEND_PID"
echo ""
echo "🛑 停止游戏："
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📝 查看日志："
echo "   后端: tail -f backend/backend.log"
echo "   前端: tail -f frontend/frontend.log"
echo ""

# 保存PID到文件
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# 在macOS上自动打开浏览器
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 5
    open http://localhost:5173
fi

# 在Linux上自动打开浏览器
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sleep 5
    xdg-open http://localhost:5173 2>/dev/null
fi
