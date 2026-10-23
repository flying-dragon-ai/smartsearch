@echo off
rem Start the xhs-adapter (and the xiaohongshu-mcp service it needs), idempotent.
rem Adapter: http://127.0.0.1:18061  Login page: http://127.0.0.1:18061/login
rem NOTE: keep this file ASCII-only, cmd parses it as GBK.
setlocal
call "%~dp0..\xhs-pipeline\xiaohongshu-mcp\start_xhs_service.bat"

netstat -ano | findstr /c:":18061" | findstr /c:"LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [xhs-adapter] already running on :18061
    exit /b 0
)
start "xhs-adapter" /min cmd /c ""%~dp0adapters\xhs-adapter.cmd""
ping -n 3 127.0.0.1 >nul
netstat -ano | findstr /c:":18061" | findstr /c:"LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [xhs-adapter] started on http://127.0.0.1:18061
) else (
    echo [xhs-adapter] FAILED to start
    exit /b 1
)
endlocal
