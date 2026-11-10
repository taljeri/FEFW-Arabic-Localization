@echo off
echo Copying Arabic MSBT files from USen to EUen for European Region compatibility...
if not exist "romfs\Msg\EUen" mkdir "romfs\Msg\EUen"
xcopy /Y /Q "romfs\Msg\USen\*.msbt.zst" "romfs\Msg\EUen\"
echo Done! Both USen and EUen now have the Arabic translation.
pause
