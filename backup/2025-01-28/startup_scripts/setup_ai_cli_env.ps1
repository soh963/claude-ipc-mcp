# PowerShell Script to Setup AI CLI Environment Variables
# Run with Administrator privileges

Write-Host "🚀 AI CLI Environment Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Function to add to PATH if not exists
function Add-ToPath {
    param([string]$PathToAdd)

    $currentPath = [Environment]::GetEnvironmentVariable("PATH", [EnvironmentVariableTarget]::User)

    if ($currentPath -notlike "*$PathToAdd*") {
        [Environment]::SetEnvironmentVariable(
            "PATH",
            "$currentPath;$PathToAdd",
            [EnvironmentVariableTarget]::User
        )
        Write-Host "✅ Added to PATH: $PathToAdd" -ForegroundColor Green
    } else {
        Write-Host "⏭️ Already in PATH: $PathToAdd" -ForegroundColor Yellow
    }
}

# 1. Check Node.js/npm
Write-Host "`n📦 Checking Node.js/npm..." -ForegroundColor Blue
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmPath = "$env:APPDATA\npm"
    Add-ToPath $npmPath
    Write-Host "  Claude CLI path: $npmPath" -ForegroundColor Gray
} else {
    Write-Host "❌ npm not found. Please install Node.js first." -ForegroundColor Red
    Write-Host "  Download from: https://nodejs.org/" -ForegroundColor Gray
}

# 2. Check Python
Write-Host "`n🐍 Checking Python..." -ForegroundColor Blue
if (Get-Command python -ErrorAction SilentlyContinue) {
    # Find Python Scripts directory
    $pythonPath = (python -c "import site; print(site.USER_BASE)") 2>$null
    if ($pythonPath) {
        $pythonScripts = "$pythonPath\Scripts"
        Add-ToPath $pythonScripts
        Write-Host "  Gemini CLI path: $pythonScripts" -ForegroundColor Gray
    }

    # Also add standard Python Scripts path
    $pythonVersion = python --version 2>&1 | Select-String -Pattern "\d+\.\d+" | ForEach-Object { $_.Matches[0].Value }
    $standardPath = "$env:USERPROFILE\AppData\Local\Programs\Python\Python$($pythonVersion.Replace('.',''))\Scripts"
    if (Test-Path $standardPath) {
        Add-ToPath $standardPath
    }
} else {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    Write-Host "  Download from: https://python.org/" -ForegroundColor Gray
}

# 3. Check GitHub CLI
Write-Host "`n🔧 Checking GitHub CLI..." -ForegroundColor Blue
if (Get-Command gh -ErrorAction SilentlyContinue) {
    $ghExtPath = "$env:USERPROFILE\.config\gh\extensions"
    if (Test-Path $ghExtPath) {
        Add-ToPath $ghExtPath
        Write-Host "  GitHub Copilot CLI path: $ghExtPath" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ GitHub CLI not found. Please install gh first." -ForegroundColor Red
    Write-Host "  Download from: https://cli.github.com/" -ForegroundColor Gray
}

# 4. Create unified AI CLI wrapper
Write-Host "`n🎯 Creating Unified AI CLI Wrapper..." -ForegroundColor Blue

$wrapperPath = "$env:USERPROFILE\.ai-cli"
if (!(Test-Path $wrapperPath)) {
    New-Item -ItemType Directory -Path $wrapperPath -Force | Out-Null
}

Add-ToPath $wrapperPath

# Create wrapper batch files
$claudeWrapper = @"
@echo off
if exist "%APPDATA%\npm\claude-cli.cmd" (
    "%APPDATA%\npm\claude-cli.cmd" %*
) else (
    npx claude-cli %*
)
"@

$geminiWrapper = @"
@echo off
python -m gemini_cli %*
"@

$codexWrapper = @"
@echo off
gh copilot %*
"@

Set-Content -Path "$wrapperPath\claude-cli.bat" -Value $claudeWrapper
Set-Content -Path "$wrapperPath\gemini-cli.bat" -Value $geminiWrapper
Set-Content -Path "$wrapperPath\codex-cli.bat" -Value $codexWrapper

Write-Host "✅ Wrapper scripts created in: $wrapperPath" -ForegroundColor Green

# 5. Install AI CLI packages
Write-Host "`n📥 Installing AI CLI packages..." -ForegroundColor Blue

$installChoice = Read-Host "Do you want to install AI CLI packages now? (y/n)"
if ($installChoice -eq 'y') {
    # Install Claude CLI
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Host "Installing Claude CLI..." -ForegroundColor Yellow
        npm install -g @anthropic-ai/claude-cli
    }

    # Install Gemini CLI
    if (Get-Command pip -ErrorAction SilentlyContinue) {
        Write-Host "Installing Gemini CLI..." -ForegroundColor Yellow
        pip install google-generativeai-cli
    }

    # Install GitHub Copilot CLI
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        Write-Host "Installing GitHub Copilot CLI..." -ForegroundColor Yellow
        gh extension install github/gh-copilot
    }
}

# 6. Refresh environment
Write-Host "`n🔄 Refreshing environment variables..." -ForegroundColor Blue
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 7. Verify installation
Write-Host "`n✅ Verification:" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Test each CLI
@("claude-cli", "gemini-cli", "codex-cli", "gh") | ForEach-Object {
    if (Get-Command $_ -ErrorAction SilentlyContinue) {
        Write-Host "✅ $_`: Found" -ForegroundColor Green
    } else {
        Write-Host "❌ $_`: Not found" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Setup Complete!" -ForegroundColor Cyan
Write-Host "Please restart your terminal for changes to take effect." -ForegroundColor Yellow
Write-Host "`nUsage examples:" -ForegroundColor Blue
Write-Host "  claude-cli 'Hello Claude!'" -ForegroundColor Gray
Write-Host "  gemini-cli 'Hello Gemini!'" -ForegroundColor Gray
Write-Host "  codex-cli 'Generate Python code'" -ForegroundColor Gray