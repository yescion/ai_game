@echo off
chcp 65001 >nul 2>&1
cls

cd /d "%~dp0"

echo ================================================
echo Plains Simulation - Portable Edition
echo ================================================
echo.
echo [INFO] Using built-in runtime, no installation needed
echo.

echo [1/6] Cleaning old logs...
if exist "logs\npc_decisions\*.log" (
    echo [INFO] Found old NPC decision logs, cleaning...
    del /Q /F "logs\npc_decisions\*.log" >nul 2>&1
    echo [OK] Old logs cleaned
) else (
    echo [OK] No old logs to clean
)
echo.

echo [2/6] Checking runtime environment...
if not exist "runtime\python.exe" (
    echo [ERROR] runtime\python.exe not found
    echo [ERROR] Please extract all files completely
    pause
    exit /b 1
)

if not exist "node\node.exe" (
    echo [ERROR] node\node.exe not found
    echo [ERROR] Please extract all files completely
    pause
    exit /b 1
)

echo [OK] Built-in Python and Node.js environment check passed
echo.

echo [3/6] Configuring environment variables...
set "NODE_PATH=%~dp0node"
set "PATH=%NODE_PATH%;%PATH%"
set "NODE_SKIP_PLATFORM_CHECK=1"

echo [OK] Environment variables configured
echo.

echo [4/6] Checking frontend dependencies...
if not exist "frontend\node_modules\" (
    echo [INFO] First run: Installing frontend dependencies...
    echo [INFO] This may take 2-5 minutes, please wait...
    cd frontend
    "%~dp0node\node.exe" "%~dp0node\node_modules\npm\bin\npm-cli.js" install
    if errorlevel 1 (
        echo [ERROR] Frontend dependencies installation failed
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies already exist
)
echo.

echo [5/6] Starting backend server...
start "Backend Server" cmd /k "cd /d "%~dp0" && start_backend.bat"

timeout /t 3 >nul
echo [OK] Backend server started
echo.

echo [6/6] Starting frontend server...
start "Frontend Server" cmd /k "cd /d "%~dp0frontend" && "%~dp0node\node.exe" "%~dp0node\node_modules\npm\bin\npm-cli.js" run dev"

timeout /t 3 >nul
echo [OK] Frontend server started
echo.

echo.
echo ================================================
echo Game Started Successfully!
echo ================================================
echo.
echo Web: http://localhost:5173
echo API: http://localhost:8000/docs
echo.
echo Tips:
echo - Two terminal windows are opened
echo - Browser will open in 5 seconds
echo - Close terminals to stop the game
echo.
echo Help:
echo - START.md for troubleshooting
echo - README.md for game guide
echo.
echo ================================================
echo.


echo [INFO] Opening browser in 5 seconds...
timeout /t 5 >nul
start http://localhost:5173

echo.
echo [INFO] Game opened in browser
echo [INFO] Closing this window will not stop the game
echo.
pause
