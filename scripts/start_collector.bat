@echo off
REM Start OpenTelemetry Collector for Windows
REM
REM Prerequisites:
REM   - Download OpenTelemetry Collector from:
REM     https://github.com/open-telemetry/opentelemetry-collector-releases/releases
REM   - Extract to a directory (e.g., C:\otel-collector)
REM   - Update COLLECTOR_PATH below to point to the extracted directory

REM Configuration
set COLLECTOR_PATH=C:\otel-collector
set CONFIG_FILE=%~dp0..\config\otel-collector-config.yaml

REM Check if collector exists
if not exist "%COLLECTOR_PATH%\otelcol.exe" (
    echo ERROR: OpenTelemetry Collector not found at %COLLECTOR_PATH%
    echo.
    echo Please download the collector from:
    echo https://github.com/open-telemetry/opentelemetry-collector-releases/releases
    echo.
    echo Extract it to %COLLECTOR_PATH% or update COLLECTOR_PATH in this script.
    exit /b 1
)

REM Check if config exists
if not exist "%CONFIG_FILE%" (
    echo ERROR: Configuration file not found at %CONFIG_FILE%
    exit /b 1
)

echo Starting OpenTelemetry Collector...
echo Config: %CONFIG_FILE%
echo.

REM Start collector
"%COLLECTOR_PATH%\otelcol.exe" --config "%CONFIG_FILE%"
