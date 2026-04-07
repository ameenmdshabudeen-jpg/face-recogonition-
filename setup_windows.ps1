$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$preferredPython = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe"

if (Test-Path $preferredPython) {
    $pythonExe = $preferredPython
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand -or $pythonCommand.Source -like "*WindowsApps*") {
        throw "Python 3.11 was not found. Install it first, then rerun setup_windows.ps1."
    }
    $pythonExe = $pythonCommand.Source
}

Write-Host "Using Python:" $pythonExe

if (-not (Test-Path $venvPython)) {
    & $pythonExe -m venv (Join-Path $projectRoot ".venv")
}

& $venvPython -m ensurepip --default-pip | Out-Host

# Install the app stack first, then use dlib-bin to avoid a local Visual Studio build.
& $venvPython -m pip install `
    Flask==3.0.3 `
    python-dotenv==1.0.1 `
    numpy==1.26.4 `
    opencv-python==4.10.0.84 `
    waitress==3.0.0 `
    Pillow `
    dlib-bin==20.0.0 `
    face-recognition-models==0.3.0 `
    face-recognition==1.3.0 `
    --no-deps | Out-Host

& $venvPython -m pip install `
    Werkzeug==3.1.8 `
    Jinja2==3.1.6 `
    itsdangerous==2.2.0 `
    click==8.3.2 `
    blinker==1.9.0 `
    MarkupSafe==3.0.3 `
    colorama==0.4.6 | Out-Host

Write-Host ""
Write-Host "Setup complete."
Write-Host "Run the app with: powershell -ExecutionPolicy Bypass -File .\run_localhost.ps1"
