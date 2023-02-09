Rem COMMAND LIST TO COMPILE IfcOpenShell

Rem VS environment setup command
set VSenv=D:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat

set slndir=xeokit-metadata\xeokit
set slnfile=xeokit.sln
 
call "%VSenv%"
cd %slndir%
call msbuild %slnfile% 