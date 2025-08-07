@echo off
REM ChaseHound - Frontend-only deployment script

for /F "delims=" %%e in ('echo prompt $E^| cmd') do set "ESC=%%e"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "CYAN=%ESC%[96m"
set "RESET=%ESC%[0m"

setlocal enabledelayedexpansion

REM ---------- CONFIG ---------
set FRONTEND_PROJECT_ID=chasehoundfrontend
set BACKEND_PROJECT_ID=chasehoundbackend  REM used for placeholder substitution
set REGION=asia-northeast1
REM ---------------------------

set "echoClr=for %%# in (1) do if "%%~1"=="INFO" (echo !CYAN![INFO]!RESET! %%~2) else if "%%~1"=="SUCCESS" (echo !GREEN![SUCCESS]!RESET! %%~2) else if "%%~1"=="ERROR" (echo !RED![ERROR]!RESET! %%~2) else if "%%~1"=="WARNING" (echo !YELLOW![WARNING]!RESET! %%~2) else (echo %%~2)"

%echoClr% INFO Starting FRONTEND deployment...

call gcloud config set project %FRONTEND_PROJECT_ID%
if errorlevel 1 (%echoClr% ERROR Failed to set frontend project & exit /b 1)
%echoClr% INFO Project set to %FRONTEND_PROJECT_ID%

call gcloud services enable appengine.googleapis.com cloudbuild.googleapis.com
if errorlevel 1 (%echoClr% ERROR Failed to enable APIs & exit /b 1)
%echoClr% INFO APIs enabled

call gcloud app create --region=%REGION% 2>nul
if errorlevel 1 (%echoClr% WARNING App Engine already exists for frontend) else (%echoClr% INFO App Engine application created)

powershell -Command "(gc src_CD\frontend\frontend_app.yaml) -replace 'BACKEND_PROJECT_ID', '%BACKEND_PROJECT_ID%' | Out-File -encoding ASCII src_CD\frontend\frontend_app.yaml"
if errorlevel 1 (%echoClr% ERROR Failed to update frontend configuration & exit /b 1)
%echoClr% INFO Frontend configuration updated with backend host

call gcloud app deploy src_CD\frontend\frontend_app.yaml --quiet
if errorlevel 1 (%echoClr% ERROR Frontend deployment failed & exit /b 1)

set FRONTEND_URL=https://%FRONTEND_PROJECT_ID%.appspot.com
%echoClr% SUCCESS Frontend deployed: %FRONTEND_URL%

pause 