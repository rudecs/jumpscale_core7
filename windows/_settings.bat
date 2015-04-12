@echo off
set JSBASE=%~dp0
mode con cp select=437 >nul 2>nul
set path=%~dp0;%~dp0bin;%~dp0Scripts;%PATH%
set PythonPath=%~dp0\Lib;%~dp0\Lib\site-packages

