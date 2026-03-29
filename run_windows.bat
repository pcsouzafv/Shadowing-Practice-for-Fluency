@echo off
setlocal

cd /d "%~dp0"

if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo Arquivo .env criado a partir de .env.example
  )
)

if exist ".venv\Scripts\python.exe" (
  set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    where python >nul 2>nul
    if errorlevel 1 (
      echo Python 3.12 nao encontrado. Instale o Python e marque "Add Python to PATH".
      exit /b 1
    )
    python -m venv .venv
  ) else (
    py -3.12 -m venv .venv
  )

  if not exist ".venv\Scripts\python.exe" (
    echo Nao foi possivel criar o ambiente virtual em .venv
    exit /b 1
  )

  set "PYTHON_EXE=.venv\Scripts\python.exe"
)

"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" app.py
