@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=source
set BUILDDIR=build

REM Check if sphinx-build is available
%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.https://www.sphinx-doc.org/
	exit /b 1
)

if "%1" == "" goto help
if "%1" == "help" goto help
if "%1" == "clean" goto clean

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:clean
echo.Cleaning build directory...
if exist "%BUILDDIR%" (
    pushd "%BUILDDIR%"
    for /d %%d in (*) do rmdir /s /q "%%d"
    del /q *
    popd
) else (
    mkdir "%BUILDDIR%"
)
goto end

:help
%SPHINXBUILD% -M help "$(SOURCEDIR)" "$(BUILDDIR)" %SPHINXOPTS% %O%

:end
popd