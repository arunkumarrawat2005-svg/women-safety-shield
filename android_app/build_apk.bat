@echo off
setlocal
echo ============================================================
echo   Building Women Safety Shield Android Release APK
echo ============================================================
powershell -ExecutionPolicy Bypass -File "%~dp0build_apk.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
echo.
echo [DONE] Build finished!
pause
