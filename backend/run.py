"""Run the backend server"""
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # 🔥 修复：使用 127.0.0.1 而不是 0.0.0.0（Windows兼容性更好）
    host = "127.0.0.1"
    port = int(os.getenv("PORT", 8000))
    
    print("=" * 60)
    print("🚀 Starting Backend Server")
    print(f"📡 HTTP API: http://{host}:{port}/docs")
    print(f"🔌 Socket.IO: http://{host}:{port}/socket.io/")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "app.main:socket_app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )

