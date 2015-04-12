@echo off

call "%~dp0_settings.bat"
prompt $LQ$G$S$P$G
rem echo %1%
cd %~dp0
rem %JBASE%\bin\console.exe -r "cd %~dp0;python %~dp0\js.py"
python js.py