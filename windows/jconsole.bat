
@echo off

call "%~dp0_settings.bat"

prompt $LQ$G$S$P$G
echo %1%
%JSBASE%\bin\console.exe -r "cd %~dp0"


