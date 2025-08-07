@echo off
REM ChaseHound - Backend-only deployment script
REM Usage: double-click or run `deploy-backend.bat`

for /F "delims=" %%e in ('echo prompt $E^| cmd') do set "ESC=%%e"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "CYAN=%ESC%[96m"
set "RESET=%ESC%[0m"

setlocal enabledelayedexpansion

REM ---------- CONFIG ---------
set BACKEND_PROJECT_ID=chasehoundbackend
set REGION=asia-northeast1
REM ---------------------------

set "echoClr=for %%# in (1) do if "%%~1"=="INFO" (echo !CYAN![INFO]!RESET! %%~2) else if "%%~1"=="SUCCESS" (echo !GREEN![SUCCESS]!RESET! %%~2) else if "%%~1"=="ERROR" (echo !RED![ERROR]!RESET! %%~2) else if "%%~1"=="WARNING" (echo !YELLOW![WARNING]!RESET! %%~2) else (echo %%~2)"

%echoClr% INFO Starting BACKEND deployment...

call gcloud config set project %BACKEND_PROJECT_ID%
if errorlevel 1 (%echoClr% ERROR Failed to set backend project & exit /b 1)
%echoClr% INFO Project set to %BACKEND_PROJECT_ID%

call gcloud services enable appengine.googleapis.com cloudbuild.googleapis.com
if errorlevel 1 (%echoClr% ERROR Failed to enable APIs & exit /b 1)
%echoClr% INFO APIs enabled

call gcloud app create --region=%REGION% 2>nul
if errorlevel 1 (%echoClr% WARNING App Engine already exists for backend) else (%echoClr% INFO App Engine application created)

call gcloud app deploy backend_app.yaml --quiet
if errorlevel 1 (%echoClr% ERROR Backend deployment failed & exit /b 1)

set BACKEND_URL=https://%BACKEND_PROJECT_ID%.appspot.com
%echoClr% SUCCESS Backend deployed: %BACKEND_URL%

pause 