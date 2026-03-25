@echo off
chcp 65001 > nul
echo ========================================
echo   Advanced Operation Recorder - 调试版
echo ========================================
echo.

echo [1/3] 检查目录...
if not exist data mkdir data
if not exist videos mkdir videos
if not exist logs mkdir logs
echo ✓ 目录已创建或存在
echo.

echo [2/3] 运行GUI测试程序...
echo 提示：录制完毕后，程序会尝试自动打开文件夹显示文件
echo.
python gui.py

echo.
echo [3/3] 程序已关闭
echo 如果需要查看生成的文件，请打开 data 文件夹
echo.
pause
