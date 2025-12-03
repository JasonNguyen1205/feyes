#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Create desktop shortcuts for Visual AOI System
.DESCRIPTION
    Creates convenient desktop shortcuts to launch the Visual AOI system.
.EXAMPLE
    .\create_shortcuts.ps1
#>

param()

# Set error action preference
$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "`n========================================" "Green"
Write-ColorOutput "Visual AOI Desktop Shortcut Creator" "Green"
Write-ColorOutput "========================================`n" "Green"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopPath = [Environment]::GetFolderPath("Desktop")

# Create WScript Shell object for shortcuts
$WshShell = New-Object -ComObject WScript.Shell

# Shortcut configurations
$shortcuts = @(
    @{
        Name = "Visual AOI - Full System"
        Target = "powershell.exe"
        Arguments = "-ExecutionPolicy Bypass -File `"$ScriptDir\launch_all.ps1`""
        IconLocation = "shell32.dll,13"
        Description = "Launch complete Visual AOI system (server + client)"
    },
    @{
        Name = "Visual AOI - Server Only"
        Target = "powershell.exe"
        Arguments = "-ExecutionPolicy Bypass -File `"$ScriptDir\launch_server.ps1`""
        IconLocation = "shell32.dll,23"
        Description = "Launch Visual AOI server only"
    },
    @{
        Name = "Visual AOI - Client Only"
        Target = "powershell.exe"
        Arguments = "-ExecutionPolicy Bypass -File `"$ScriptDir\launch_client.ps1`""
        IconLocation = "shell32.dll,24"
        Description = "Launch Visual AOI client only"
    }
)

foreach ($shortcut in $shortcuts) {
    $shortcutPath = Join-Path $DesktopPath "$($shortcut.Name).lnk"
    
    Write-ColorOutput "Creating shortcut: $($shortcut.Name)" "Yellow"
    
    try {
        $Shortcut = $WshShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = $shortcut.Target
        $Shortcut.Arguments = $shortcut.Arguments
        $Shortcut.WorkingDirectory = $ScriptDir
        $Shortcut.IconLocation = $shortcut.IconLocation
        $Shortcut.Description = $shortcut.Description
        $Shortcut.Save()
        
        Write-ColorOutput "✓ Created: $shortcutPath" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to create: $($shortcut.Name)" "Red"
        Write-ColorOutput "  Error: $($_.Exception.Message)" "Red"
    }
}

Write-ColorOutput "`n========================================" "Green"
Write-ColorOutput "Shortcuts created on your desktop!" "Green"
Write-ColorOutput "========================================`n" "Green"

Write-ColorOutput "You can now launch Visual AOI from your desktop shortcuts." "Cyan"
