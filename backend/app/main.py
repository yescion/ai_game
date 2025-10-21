"""Main FastAPI application"""
import os
import logging
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.services.game_loop import MainGameLoop, GameConfig

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    load_dotenv()
except Exception as e:
    logger.warning(f"Failed to load .env file: {e}")
    logger.info("Using fallback environment variables")

# Check API key (不阻止服务器启动，但记录警告)
if not os.getenv('DEEPSEEK_API_KEY'):
    logger.warning("=" * 80)
    logger.warning("⚠️  未检测到 DEEPSEEK_API_KEY 环境变量")
    logger.warning("⚠️  游戏将无法正常运行，请配置API密钥后重启服务器")
    logger.warning("=" * 80)
    logger.warning("")
    logger.warning("📝 配置方法：")
    logger.warning("   1. backend目录下编辑或创建 .env 文件")
    logger.warning("   2. 添加以下内容：")
    logger.warning("      DEEPSEEK_API_KEY=your_api_key_here")
    logger.warning("      DEEPSEEK_BASE_URL=https://api.deepseek.com")
    logger.warning("")
    logger.warning("   或者在 backend/app/main.py 中设置硬编码的API密钥")
    logger.warning("=" * 80)

# Create FastAPI app
app = FastAPI(
    title="原始平原模拟 API",
    description="AI驱动的NPC模拟人生游戏后端",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False
)

# Wrap FastAPI app with Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Game instance
game_loop: MainGameLoop = None


@app.on_event("startup")
async def startup_event():
    """Initialize game on startup"""
    global game_loop
    
    logger.info("🚀 Starting game server...")
    
    # ⚠️ 检查API密钥配置
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        logger.error("")
        logger.error("❌" * 40)
        logger.error("❌  致命错误：未配置 DEEPSEEK_API_KEY")
        logger.error("❌" * 40)
        logger.error("")
        logger.error("🔧 请按以下步骤配置API密钥：")
        logger.error("")
        logger.error("方法1：使用 .env 文件（推荐）")
        logger.error("  1. 在项目根目录创建 .env 文件")
        logger.error("  2. 添加以下内容：")
        logger.error("     DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx")
        logger.error("     DEEPSEEK_BASE_URL=https://api.deepseek.com")
        logger.error("  3. 重启后端服务")
        logger.error("")
        logger.error("方法2：直接在代码中设置")
        logger.error("  在 backend/app/main.py 第28行附近添加：")
        logger.error("     os.environ['DEEPSEEK_API_KEY'] = 'sk-xxxxxxxxxxxxxxxx'")
        logger.error("     os.environ['DEEPSEEK_BASE_URL'] = 'https://api.deepseek.com'")
        logger.error("")
        logger.error("🔗 获取API密钥：https://platform.deepseek.com")
        logger.error("")
        logger.error("⚠️  服务器将继续运行，但游戏无法启动")
        logger.error("⚠️  前端将显示详细的配置指引")
        logger.error("❌" * 40)
        logger.error("")
        
        # 不启动游戏循环，但服务器继续运行以便前端显示错误信息
        game_loop = None
        return
    
    # Create game config
    config = GameConfig(
        map_width=100,
        map_height=100,
        initial_npc_count=5,
        time_scale=60.0
    )
    
    # Initialize game loop
    game_loop = MainGameLoop()
    
    # Set broadcast callback
    async def broadcast(event: str, data: dict):
        await sio.emit(event, data)
    
    game_loop.set_broadcast_callback(broadcast)
    
    # 🔥 修复：启动游戏作为后台任务，不阻塞服务器启动
    # 这样Socket.IO可以立即开始接受连接
    asyncio.create_task(game_loop.start_game(config))
    
    logger.info("✅ Game server startup complete! Game initialization running in background...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global game_loop
    
    logger.info("🛑 Shutting down game server...")
    
    if game_loop:
        game_loop.stop()
    
    logger.info("✅ Game server shut down")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "原始平原模拟 API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "game_running": game_loop is not None and game_loop.is_running
    }


@app.get("/api/check")
async def check_api_services():
    """Check if all required services (AI API) are available"""
    import os
    from app.services.ai_service import AIService
    
    result = {
        "backend": "ok",
        "deepseek_configured": False,
        "deepseek_working": False,
        "error": None
    }
    
    # Check if API key is configured
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        result["error"] = "DEEPSEEK_API_KEY 未配置"
        result["deepseek_configured"] = False
        return result
    
    result["deepseek_configured"] = True
    
    # Test AI service
    try:
        ai_service = AIService()
        if not ai_service.client:
            result["error"] = "AI服务未能初始化"
            return result
        
        # Try a simple API call to test
        test_response = ai_service.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个测试助手。"},
                {"role": "user", "content": "回复'OK'"}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        if test_response and test_response.choices:
            result["deepseek_working"] = True
            logger.info("✅ API validation successful")
        else:
            result["error"] = "AI API响应异常"
            
    except Exception as e:
        logger.error(f"❌ API validation failed: {e}")
        result["error"] = f"AI API测试失败: {str(e)}"
        result["deepseek_working"] = False
    
    return result


@app.get("/api/world")
async def get_world_state():
    """Get current world state"""
    if game_loop and game_loop.world_state:
        return game_loop.world_state.model_dump(mode='json')
    return {"error": "Game not started"}


@app.get("/api/npcs")
async def get_npcs():
    """Get all NPCs"""
    if game_loop and game_loop.world_state:
        return {
            "npcs": [npc.model_dump(mode='json') for npc in game_loop.world_state.npcs]
        }
    return {"error": "Game not started"}


@app.get("/api/npcs/{npc_id}")
async def get_npc(npc_id: str):
    """Get specific NPC details"""
    if game_loop and game_loop.world_state:
        npc = game_loop.world_state.get_npc_by_id(npc_id)
        if npc:
            # Get memories
            memories = game_loop.memory_service.get_all_memories(npc_id)
            return {
                "npc": npc.model_dump(mode='json'),
                "memories": memories[-20:]  # Last 20 memories
            }
        return {"error": "NPC not found"}
    return {"error": "Game not started"}


@app.get("/api/resources")
async def get_resources():
    """Get all resources"""
    if game_loop and game_loop.world_state:
        return {
            "resources": [r.model_dump(mode='json') for r in game_loop.world_state.resources],
            "global_resources": game_loop.world_state.global_resources
        }
    return {"error": "Game not started"}


@app.get("/api/buildings")
async def get_buildings():
    """Get all buildings"""
    if game_loop and game_loop.world_state:
        return {
            "buildings": [b.model_dump(mode='json') for b in game_loop.world_state.buildings]
        }
    return {"error": "Game not started"}


@app.get("/api/events")
async def get_events():
    """Get recent events"""
    if game_loop and game_loop.world_state:
        return {
            "events": [e.model_dump(mode='json') for e in game_loop.world_state.events[-50:]]
        }
    return {"error": "Game not started"}


@app.get("/api/admin/dashboard")
async def get_admin_dashboard():
    """Get comprehensive admin dashboard data"""
    if not game_loop or not game_loop.world_state:
        return {"error": "Game not started"}
    
    world = game_loop.world_state
    
    # Collect detailed NPC data with memories
    npcs_data = []
    for npc in world.npcs:
        npc_data = npc.model_dump(mode='json')
        # Add memory service data
        memories = game_loop.memory_service.get_all_memories(npc.id)
        npc_data['memory_service_data'] = memories[-50:] if memories else []
        # Add decision timing
        npc_data['last_decision_time'] = game_loop.npc_last_decision.get(npc.id, 0)
        npcs_data.append(npc_data)
    
    # Collect beast data
    beasts_data = []
    for beast in world.beasts:
        beast_data = beast.model_dump(mode='json')
        beast_data['last_decision_time'] = game_loop.beast_last_decision.get(beast.id, 0)
        beasts_data.append(beast_data)
    
    # Collect conversation data
    conversations_data = []
    for conv_id, conv in game_loop.active_conversations.items():
        conversations_data.append({
            'id': conv_id,
            'conversation': conv.model_dump(mode='json')
        })
    
    # Game configuration
    config_data = {
        'tick_interval': game_loop.tick_interval,
        'time_scale': game_loop.time_scale,
        'npc_decision_interval': game_loop.npc_decision_interval,
        'beast_decision_interval': game_loop.beast_decision_interval,
        'is_running': game_loop.is_running,
        'game_started': game_loop.game_started,
        'waiting_for_client': game_loop.waiting_for_client,
    }
    
    # World statistics
    statistics = {
        'total_npcs': len(world.npcs),
        'alive_npcs': sum(1 for npc in world.npcs if npc.is_alive),
        'total_beasts': len(world.beasts),
        'total_buildings': len(world.buildings),
        'completed_buildings': sum(1 for b in world.buildings if b.is_complete),
        'total_resources': len(world.resources),
        'total_events': len(world.events),
        'active_conversations': len(game_loop.active_conversations),
    }
    
    # Calculate weather countdown
    current_game_time = world.time.get_current_time()
    time_since_last_check = current_game_time - game_loop.last_weather_check
    time_until_next_check = game_loop.weather_check_interval - time_since_last_check
    
    # Calculate in minutes and seconds
    countdown_minutes = int(time_until_next_check // 60)
    countdown_seconds = int(time_until_next_check % 60)
    
    weather_data = {
        'current': world.weather,
        'last_check_time': game_loop.last_weather_check,
        'next_check_time': game_loop.last_weather_check + game_loop.weather_check_interval,
        'check_interval': game_loop.weather_check_interval,
        'time_until_next_check': max(0, time_until_next_check),  # Game time in minutes
        'countdown_minutes': max(0, countdown_minutes),
        'countdown_seconds': max(0, countdown_seconds),
    }
    
    return {
        'timestamp': world.time.format_time(),
        'game_time': world.time.get_current_time(),
        'time': world.time.model_dump(mode='json'),
        'weather': weather_data,
        'world_size': {
            'width': world.width,
            'height': world.height
        },
        'npcs': npcs_data,
        'beasts': beasts_data,
        'buildings': [b.model_dump(mode='json') for b in world.buildings],
        'resources': [r.model_dump(mode='json') for r in world.resources],
        'global_resources': world.global_resources,
        'events': [e.model_dump(mode='json') for e in world.events[-100:]],
        'conversations': conversations_data,
        'config': config_data,
        'statistics': statistics,
    }


# Socket.IO events
@sio.event
async def connect(sid, environ, auth=None):
    """Client connected"""
    logger.info(f"🔌 Client connected: {sid}")
    
    # Send initial world state
    if game_loop and game_loop.world_state:
        # Convert to dict with proper JSON serialization
        world_dict = game_loop.world_state.model_dump(mode='json')
        await sio.emit('world_state', world_dict, room=sid)


@sio.event
async def client_ready(sid):
    """Client is ready (fully loaded)"""
    logger.info(f"✅ Client ready signal received from: {sid}")
    
    # 🔥 通知游戏循环：客户端已完全准备好
    if game_loop:
        logger.info(f"🎮 Notifying game loop that client is ready")
        game_loop.on_client_connected()
    else:
        logger.warning("⚠️ Game loop not initialized yet")
    
    return {"status": "ok"}


@sio.event
async def disconnect(sid):
    """Client disconnected"""
    logger.info(f"🔌 Client disconnected: {sid}")


@sio.event
async def request_world_state(sid):
    """Client requests world state"""
    if game_loop and game_loop.world_state:
        world_dict = game_loop.world_state.model_dump(mode='json')
        await sio.emit('world_state', world_dict, room=sid)


# 🔮 God Commands - 上帝指令系统
@sio.event
async def god_add_memory(sid, data):
    """Add memory to NPC(s)"""
    try:
        target = data.get('target', 'all')  # 'all' or npc_id
        memory_text = data.get('memory', '')
        
        if not memory_text:
            await sio.emit('god_command_result', {
                'success': False,
                'message': '记忆内容不能为空'
            }, room=sid)
            return
        
        if not game_loop.world_state:
            await sio.emit('god_command_result', {
                'success': False,
                'message': '游戏未开始'
            }, room=sid)
            return
        
        affected_npcs = []
        affected_npc_ids = []
        
        if target == 'all':
            # 为所有NPC添加记忆
            for npc in game_loop.world_state.npcs:
                if npc.is_alive:
                    npc.memories.append(memory_text)
                    if len(npc.memories) > 50:
                        npc.memories = npc.memories[-50:]
                    affected_npcs.append(npc.name)
                    affected_npc_ids.append(npc.id)
        else:
            # 为指定NPC添加记忆
            target_npc = None
            for npc in game_loop.world_state.npcs:
                if npc.id == target or npc.name == target:
                    target_npc = npc
                    break
            
            if target_npc and target_npc.is_alive:
                target_npc.memories.append(memory_text)
                if len(target_npc.memories) > 50:
                    target_npc.memories = target_npc.memories[-50:]
                affected_npcs.append(target_npc.name)
                affected_npc_ids.append(target_npc.id)
            else:
                await sio.emit('god_command_result', {
                    'success': False,
                    'message': f'找不到NPC: {target}'
                }, room=sid)
                return
        
        logger.info(f"🔮 [上帝指令] 为 {', '.join(affected_npcs)} 添加记忆: {memory_text}")
        
        # 🔥 立即广播受影响的NPC更新（轻量级）
        if affected_npc_ids:
            affected_npc_data = [
                npc.model_dump(mode='json') 
                for npc in game_loop.world_state.npcs 
                if npc.id in affected_npc_ids
            ]
            await sio.emit('npcs_updated', {
                'npcs': affected_npc_data
            })
        
        await sio.emit('god_command_result', {
            'success': True,
            'message': f'成功为 {", ".join(affected_npcs)} 添加记忆',
            'affected_npcs': affected_npcs
        }, room=sid)
        
    except Exception as e:
        logger.error(f"God command error: {e}")
        await sio.emit('god_command_result', {
            'success': False,
            'message': f'错误: {str(e)}'
        }, room=sid)


@sio.event
async def god_modify_memory(sid, data):
    """Modify specific memory of NPC"""
    try:
        npc_target = data.get('npc', '')
        memory_index = data.get('index', -1)
        new_memory = data.get('new_memory', '')
        
        if not npc_target or not new_memory:
            await sio.emit('god_command_result', {
                'success': False,
                'message': '参数不完整'
            }, room=sid)
            return
        
        if not game_loop.world_state:
            await sio.emit('god_command_result', {
                'success': False,
                'message': '游戏未开始'
            }, room=sid)
            return
        
        # 找到目标NPC
        target_npc = None
        for npc in game_loop.world_state.npcs:
            if npc.id == npc_target or npc.name == npc_target:
                target_npc = npc
                break
        
        if not target_npc:
            await sio.emit('god_command_result', {
                'success': False,
                'message': f'找不到NPC: {npc_target}'
            }, room=sid)
            return
        
        # 修改记忆
        if 0 <= memory_index < len(target_npc.memories):
            old_memory = target_npc.memories[memory_index]
            target_npc.memories[memory_index] = new_memory
            logger.info(f"🔮 [上帝指令] 修改 {target_npc.name} 的记忆 [{memory_index}]: {old_memory} -> {new_memory}")
            
            # 🔥 立即广播受影响的NPC更新（轻量级）
            await sio.emit('npcs_updated', {
                'npcs': [target_npc.model_dump(mode='json')]
            })
            
            await sio.emit('god_command_result', {
                'success': True,
                'message': f'成功修改 {target_npc.name} 的记忆'
            }, room=sid)
        else:
            await sio.emit('god_command_result', {
                'success': False,
                'message': f'记忆索引超出范围: {memory_index}'
            }, room=sid)
        
    except Exception as e:
        logger.error(f"God command error: {e}")
        await sio.emit('god_command_result', {
            'success': False,
            'message': f'错误: {str(e)}'
        }, room=sid)


@sio.event
async def god_clear_memories(sid, data):
    """Clear all memories of NPC(s)"""
    try:
        target = data.get('target', '')
        
        if not target:
            await sio.emit('god_command_result', {
                'success': False,
                'message': '请指定目标'
            }, room=sid)
            return
        
        if not game_loop.world_state:
            await sio.emit('god_command_result', {
                'success': False,
                'message': '游戏未开始'
            }, room=sid)
            return
        
        affected_npcs = []
        affected_npc_ids = []
        
        if target == 'all':
            # 清除所有NPC的记忆
            for npc in game_loop.world_state.npcs:
                if npc.is_alive:
                    npc.memories.clear()
                    affected_npcs.append(npc.name)
                    affected_npc_ids.append(npc.id)
        else:
            # 清除指定NPC的记忆
            target_npc = None
            for npc in game_loop.world_state.npcs:
                if npc.id == target or npc.name == target:
                    target_npc = npc
                    break
            
            if target_npc and target_npc.is_alive:
                target_npc.memories.clear()
                affected_npcs.append(target_npc.name)
                affected_npc_ids.append(target_npc.id)
            else:
                await sio.emit('god_command_result', {
                    'success': False,
                    'message': f'找不到NPC: {target}'
                }, room=sid)
                return
        
        logger.info(f"🔮 [上帝指令] 清除 {', '.join(affected_npcs)} 的记忆")
        
        # 🔥 立即广播受影响的NPC更新（轻量级）
        if affected_npc_ids:
            affected_npc_data = [
                npc.model_dump(mode='json') 
                for npc in game_loop.world_state.npcs 
                if npc.id in affected_npc_ids
            ]
            await sio.emit('npcs_updated', {
                'npcs': affected_npc_data
            })
        
        await sio.emit('god_command_result', {
            'success': True,
            'message': f'成功清除 {", ".join(affected_npcs)} 的记忆',
            'affected_npcs': affected_npcs
        }, room=sid)
        
    except Exception as e:
        logger.error(f"God command error: {e}")
        await sio.emit('god_command_result', {
            'success': False,
            'message': f'错误: {str(e)}'
        }, room=sid)


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting server on port {port}...")
    
    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

