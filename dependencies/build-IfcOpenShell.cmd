Rem COMMAND LIST TO COMPILE IfcOpenShell

Rem VS environment setup command
set VSenv=D:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat

Rem Temporary directory
set tempdir=C:\Temp\buildtemp

md %tempdir%
rmdir /s /q %tempdir%\IfcOpenShell

xcopy IfcOpenShell %tempdir% /E/H

cd %tempdir%
cd  IfcOpenShell
cd  win

call "%VSenv%"
call build-deps.cmd
call run-cmake.bat