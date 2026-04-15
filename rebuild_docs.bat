@echo off
setlocal enabledelayedexpansion

REM Check if sphinx-build is available
sphinx-build --version >nul 2>&1
if errorlevel 1 (
    echo Error: sphinx-build not found.
    echo Please install Sphinx using: pip install -r docs/requirements.txt
    exit /b 1
)

echo Setting up documentation directories...

REM Create necessary directories
if not exist docs\build mkdir docs\build
if not exist docs\source\_static mkdir docs\source\_static

echo Cleaning build directory...
pushd docs\build
if exist * (
    for /d %%d in (*) do rmdir /s /q "%%d"
    del /q *
)
popd

echo Building documentation...
cd docs
if not exist make.bat (
    echo Error: make.bat not found in docs directory
    exit /b 1
)

echo Running Sphinx build...
call make.bat html
if errorlevel 1 (
    echo Error building documentation
    cd ..
    exit /b 1
)

cd ..

echo Documentation built successfully!
echo Opening documentation...
start docs\build\html\index.html

exit /b 0