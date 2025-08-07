@echo off
REM ChaseHound - Google App Engine Deployment (Backend + Frontend) from root

REM Enable ANSI escape sequences in Windows CMD and define color constants
for /F "delims=" %%e in ('echo prompt $E^| cmd') do set "ESC=%%e"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "CYAN=%ESC%[96m"
set "RESET=%ESC%[0m"

setlocal enabledelayedexpansion

set BACKEND_PROJECT_ID=chasehoundbackend
set FRONTEND_PROJECT_ID=chasehoundfrontend
set REGION=asia-northeast1

:: Helper macro for colored output: %1 = LEVEL (INFO|SUCCESS|ERROR|WARNING), %2 = message
@REM set "echoClr=for %%# in (1) do if "%%~1"=="INFO" (echo !CYAN![INFO]!RESET! %%~2) else if "%%~1"=="SUCCESS" (echo !GREEN![SUCCESS]!RESET! %%~2) else if "%%~1"=="ERROR" (echo !RED![ERROR]!RESET! %%~2) else if "%%~1"=="WARNING" (echo !YELLOW![WARNING]!RESET! %%~2) else (echo %%~2)"

@REM %echoClr% INFO Starting ChaseHound deployment process...

REM ------------------------------------------------------------------------------
REM Backend
REM ------------------------------------------------------------------------------
echo [BACKEND] Step 1: Setting up backend project...
call gcloud config set project %BACKEND_PROJECT_ID%
if errorlevel 1 (
    echo [ERROR] Failed to set backend project
    pause
    exit /b 1
)
echo INFO Backend project set to: %BACKEND_PROJECT_ID%

echo [BACKEND] Step 2: Enabling required APIs...
call gcloud services enable appengine.googleapis.com cloudbuild.googleapis.com
if errorlevel 1 (
    echo [ERROR] Failed to enable APIs
    pause
    exit /b 1
)
echo INFO APIs enabled successfully

echo [BACKEND] Step 3: Creating App Engine application...
call gcloud app create --region=%REGION% 2>nul
if errorlevel 1 (
    echo [WARNING] App Engine already exists for backend
) else (
    echo INFO App Engine application created successfully
)

echo [BACKEND] Step 4: Deploying backend service...
call gcloud app deploy backend_app.yaml --quiet
if errorlevel 1 (
    echo [ERROR] Backend deployment failed
    pause
    exit /b 1
)
echo INFO Backend deployment completed successfully
set BACKEND_URL=https://%BACKEND_PROJECT_ID%.appspot.com

echo.
echo [BACKEND] Backend deployment summary:
echo [INFO] - Project ID: %BACKEND_PROJECT_ID%
echo [INFO] - Region: %REGION%
echo [INFO] - URL: %BACKEND_URL%
echo.

REM ------------------------------------------------------------------------------
REM Frontend
REM ------------------------------------------------------------------------------
echo [FRONTEND] Step 1: Setting up frontend project...
call gcloud config set project %FRONTEND_PROJECT_ID%
if errorlevel 1 (
    echo [ERROR] Failed to set frontend project
    pause
    exit /b 1
)
echo INFO Frontend project set to: %FRONTEND_PROJECT_ID%

echo [FRONTEND] Step 2: Enabling required APIs...
call gcloud services enable appengine.googleapis.com cloudbuild.googleapis.com
if errorlevel 1 (
    echo [ERROR] Failed to enable APIs
    pause
    exit /b 1
)
echo INFO APIs enabled successfully

echo [FRONTEND] Step 3: Creating App Engine application...
call gcloud app create --region=%REGION% 2>nul
if errorlevel 1 (
    echo [WARNING] App Engine already exists for frontend
) else (
    echo INFO App Engine application created successfully
)

echo [FRONTEND] Step 4: Updating frontend configuration...
powershell -Command "(gc src_CD\frontend\frontend_app.yaml) -replace 'BACKEND_PROJECT_ID', '%BACKEND_PROJECT_ID%' | Out-File -encoding ASCII src_CD\frontend\frontend_app.yaml"
if errorlevel 1 (
    echo [ERROR] Failed to update frontend configuration
    pause
    exit /b 1
)
echo INFO Frontend configuration updated with backend URL

echo [FRONTEND] Step 5: Deploying frontend service...
call gcloud app deploy src_CD\frontend\frontend_app.yaml --quiet
if errorlevel 1 (
    echo [ERROR] Frontend deployment failed
    pause
    exit /b 1
)
echo INFO Frontend deployment completed successfully
set FRONTEND_URL=https://%FRONTEND_PROJECT_ID%.appspot.com

echo.
echo [FRONTEND] Frontend deployment summary:
echo [INFO] - Project ID: %FRONTEND_PROJECT_ID%
echo [INFO] - Region: %REGION%
echo [INFO] - URL: %FRONTEND_URL%
echo.

REM ------------------------------------------------------------------------------
REM Final Summary
REM ------------------------------------------------------------------------------
echo ================================================================================
echo SUCCESS ChaseHound deployment completed successfully!
echo ================================================================================
echo SUCCESS Backend URL:  %BACKEND_URL%
echo SUCCESS Frontend URL: %FRONTEND_URL%
echo ================================================================================
echo INFO Your ChaseHound application is now live and accessible worldwide!
echo INFO Share the Frontend URL with your users.
echo INFO The Frontend will automatically connect to the Backend.
echo.
pause 