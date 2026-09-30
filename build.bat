@echo off
chcp 65001 >nul
REM ============================================================
REM OmniCalc 通用运算器 - 一键打包脚本
REM 前置：pip install pyinstaller pillow
REM
REM 换图标：用新图片替换 assets\icon.jpg（jpg/png/webp 均可），
REM         重新运行本脚本即可，图标会自动转换并嵌入 exe。
REM ============================================================

echo [清理] 删除旧 dist / build / spec ...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
del *.spec 2>nul

echo [图标] 由 assets\icon.jpg 生成多尺寸 icon.ico ...
python make_icon.py
if errorlevel 1 (
    echo 图标生成失败，请确认 assets\icon.jpg 存在
    pause
    exit /b 1
)

echo [打包] PyInstaller 构建 OmniCalc.exe ...
python -m PyInstaller --noconfirm --onefile --windowed ^
  --name OmniCalc ^
  --icon "assets\icon.ico" ^
  --add-data "assets\icon.ico;assets" ^
  --hidden-import PIL._tkinter_finder ^
  --hidden-import crop_dialog ^
  main.py

echo.
echo 打包完成：dist\OmniCalc.exe
pause
