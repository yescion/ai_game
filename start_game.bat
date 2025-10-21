@echo off
chcp 65001 >nul 2>&1
cls

cd /d "%~dp0"

echo ================================================
echo Plains Simulation - Developer Mode
echo ================================================
echo.
echo [INFO] Requires Python 3.11+ and Node.js 18+
echo.

echo [1/5] Cleaning old logs...
if exist "logs\npc_decisions\*.log" (
    echo [INFO] Found old NPC decision logs, cleaning...
    del /Q /F "logs\npc_decisions\*.log" >nul 2>&1
    echo [OK] Old logs cleaned
) else (
    echo [OK] No old logs to clean
)
echo.

echo [2/5] Checking system environment...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo [ERROR] Please install Python 3.11+ or use portable edition
    echo.
    echo [HINT] If you dont want to install, use: portable_start.bat
    pause
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    echo [ERROR] Please install Node.js 18+ or use portable edition
    echo.
    echo [HINT] If you dont want to install, use: portable_start.bat
    pause
    exit /b 1
)

echo [OK] System environment check passed
echo.

echo [3/5] Preparing backend environment...
cd backend

WHERE conda >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Conda detected
    
    conda env list | findstr "ai_game" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [INFO] Using existing environment: ai_game
        call conda run -n ai_game pip install -r requirements.txt >nul 2>&1
        
        start "Backend Server" cmd /k "call conda activate ai_game && cd /d "%CD%" && python run.py"
    ) else (
        echo [INFO] Creating Conda environment: ai_game
        call conda create -n ai_game python=3.11 -y
        call conda run -n ai_game pip install -r requirements.txt >nul 2>&1
        
        start "Backend Server" cmd /k "call conda activate ai_game && cd /d "%CD%" && python run.py"
    )
) else (
    echo [INFO] Using Python venv
    
    if not exist "venv\" (
        echo [INFO] Creating virtual environment...
        python -m venv venv
    )
    
    call venv\Scripts\activate.bat
    pip install -r requirements.txt >nul 2>&1
    
    start "Backend Server" cmd /k "cd /d "%CD%" && venv\Scripts\activate.bat && python run.py"
)

cd ..
timeout /t 3 >nul
echo [OK] Backend server started
echo.

echo [4/5] Preparing frontend environment...
cd frontend

if not exist "node_modules\" (
    echo [INFO] Installing frontend dependencies...
    call npm install
)

start "Frontend Server" cmd /k "cd /d "%CD%" && npm run dev"

cd ..
timeout /t 3 >nul
echo [OK] Frontend server started
echo.

echo [5/5] Done!
echo.
echo ================================================
echo Game Started Successfully!
echo ================================================
echo.
echo Web: http://localhost:5173
echo API: http://localhost:8000/docs
echo.
echo Tips:
echo - Two terminal windows opened
echo - Browser will open in 5 seconds
echo - Close terminals to stop servers
echo.
pause

timeout /t 5 >nul
start http://localhost:5173
