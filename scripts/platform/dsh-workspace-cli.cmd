@echo off
setlocal DisableDelayedExpansion
for %%I in ("%~dp0..\..") do set "DSH_WORKSPACE_ROOT=%%~fI"
set "DSH_WORKSPACE_PYTHON=python"
if exist "%WINDIR%\System32\OpenSSH\ssh.exe" set "GIT_SSH=%WINDIR%\System32\OpenSSH\ssh.exe"
pushd "%DSH_WORKSPACE_ROOT%"
if errorlevel 1 (
  >&2 echo Workspace root is unavailable: "%DSH_WORKSPACE_ROOT%"
  exit /b 1
)
call "%DSH_WORKSPACE_ROOT%\scripts\platform\dsh.cmd" --profile headless --permission-mode workspace-write %*
set "DSH_EXIT=%ERRORLEVEL%"
popd
exit /b %DSH_EXIT%
