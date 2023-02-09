Rem COMMAND LIST TO COMPILE IfcOpenShell

Rem VS environment setup command
set VSenv=D:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat

Rem Temporary directory
set tempdir=C:\Temp\buildtemp
set ifcname=IfcOpenShell

set ifctmpdir=%tempdir%\%ifcname%\

if exist %tempdir%\ (
    echo Directory %tempdir% already existent
) else (
    md %tempdir%
)

if exist %ifctmpdir%\ (
    rmdir /s /q %ifctmpdir%
)

xcopy %ifcname% %ifctmpdir% /E/H

cd %ifctmpdir%
cd win


call "%VSenv%"
call build-deps.cmd
call run-cmake.bat