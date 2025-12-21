@echo off
REM Test Runner Batch Script for Cipherdocs Backend (Windows)
REM Convenience script to run tests with various configurations

setlocal enabledelayedexpansion

REM Colors using ANSI codes (Windows 10+)
set "BLUE=[34m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "NC=[0m"

REM Check if pytest.ini exists
if not exist pytest.ini (
    echo Error: pytest.ini not found. Please run this script from the backend directory.
    exit /b 1
)

REM Show help
if "%1%"=="help" goto :show_help
if "%1%"=="" goto :run_all

goto :%1%

:run_all
    echo.
    echo Running All Tests with Coverage...
    echo.
    python -m pytest --cov=app --cov-report=html:htmlcov --cov-report=term-missing -v
    echo.
    echo Tests completed at %date% %time%
    goto :end

:unit
    echo.
    echo Running Unit Tests...
    echo.
    python -m pytest tests/test_*_comprehensive.py -v
    goto :end

:auth
    echo.
    echo Running Authentication Tests...
    echo.
    python -m pytest tests/test_auth_jwt_comprehensive.py -v
    goto :end

:encryption
    echo.
    echo Running Encryption Tests...
    echo.
    python -m pytest tests/test_encryption_comprehensive.py -v
    goto :end

:chunking
    echo.
    echo Running Chunking Tests...
    echo.
    python -m pytest tests/test_chunking_comprehensive.py -v
    goto :end

:embedding
    echo.
    echo Running Embedding Tests...
    echo.
    python -m pytest tests/test_embedding_comprehensive.py -v
    goto :end

:database
    echo.
    echo Running Database Tests...
    echo.
    python -m pytest tests/test_database_ops.py -v
    goto :end

:coverage
    echo.
    echo Running Tests with Detailed Coverage...
    echo.
    python -m pytest --cov=app --cov-report=html:htmlcov --cov-report=term-missing --cov-report=xml --cov-branch -v
    echo.
    echo Coverage report generated in htmlcov/index.html
    echo Opening report...
    start htmlcov/index.html
    goto :end

:fast
    echo.
    echo Running Fast Tests (excluding slow tests)...
    echo.
    python -m pytest -m "not slow" -v
    goto :end

:verbose
    echo.
    echo Running All Tests (Verbose)...
    echo.
    python -m pytest -vv
    goto :end

:report
    echo.
    echo Generating HTML Coverage Report...
    echo.
    python -m pytest --cov=app --cov-report=html:htmlcov --cov-report=term-missing -q
    echo.
    echo Coverage report generated in htmlcov/index.html
    echo Opening report...
    start htmlcov/index.html
    goto :end

:stats
    echo.
    echo Test Suite Statistics
    echo.
    
    REM Count test files
    setlocal
    set count=0
    for /r tests %%f in (test_*.py) do set /a count+=1
    echo Test files: !count!
    
    REM Count test functions (approximate) using findstr
    set count=0
    for /f %%a in ('findstr /R /C:"def test_" tests\*.py ^| find /c "def test_"') do (
        set count=%%a
    )
    echo Test functions: !count!
    
    echo.
    goto :end

:show_help
    echo Usage: run_tests.bat [option]
    echo.
    echo Options:
    echo   all              Run all tests with coverage (default)
    echo   unit             Run unit tests only
    echo   auth             Run authentication tests
    echo   encryption       Run encryption tests
    echo   chunking         Run chunking tests
    echo   embedding        Run embedding tests
    echo   database         Run database tests
    echo   coverage         Run with detailed coverage report
    echo   fast             Run fast tests only (skip slow tests)
    echo   verbose          Run with verbose output
    echo   report           Generate HTML coverage report only
    echo   stats            Show test suite statistics
    echo   help             Show this help message
    echo.
    echo Examples:
    echo   run_tests.bat               - Run all tests
    echo   run_tests.bat auth          - Run auth tests
    echo   run_tests.bat coverage      - Run with coverage report
    goto :end

:unknown
    echo.
    echo Error: Unknown option: %1%
    echo.
    echo Run 'run_tests.bat help' for usage information.
    goto :end

:end
    echo.
    endlocal
