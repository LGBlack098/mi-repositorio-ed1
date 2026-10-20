# Genere una distribución portable; solo incluye el audio sintético propio.
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$projectFlet = Join-Path $projectRoot '.venv\Scripts\flet.exe'
$portableData = Join-Path $projectRoot 'dist\Sonoteca\SonotecaDatos'
$backup = $null
Push-Location -LiteralPath $projectRoot
try {
    foreach ($relativeTarget in @('build','dist\windows-staging')) {
        $absoluteTarget = [IO.Path]::GetFullPath((Join-Path $projectRoot $relativeTarget))
        if (-not $absoluteTarget.StartsWith($projectRoot + '\')) {
            throw 'El destino de compilación no pertenece al proyecto.'
        }
        if ((Test-Path -LiteralPath $absoluteTarget) -and
            ((Get-Item -LiteralPath $absoluteTarget).Attributes -band
             [IO.FileAttributes]::ReparsePoint)) {
            throw 'El destino de compilación no puede ser un enlace de directorio.'
        }
    }
    if (Test-Path -LiteralPath $portableData) {
        $backup = Join-Path $projectRoot ('data\respaldo-portable-' + [guid]::NewGuid())
        New-Item -ItemType Directory -Path (Split-Path $backup) -Force | Out-Null
        Copy-Item -LiteralPath $portableData -Destination $backup -Recurse
        Write-Output "Respaldo de datos portables: $backup"
    }
    & $projectFlet pack main.py --name Sonoteca --onedir `
        --icon assets/sonoteca.ico `
        --add-data 'assets/audio/demo.wav:assets/audio' 'assets/sonoteca.ico:assets' 'assets/sonoteca.png:assets' 'README.md:.' `
        --hidden-import flet_audio --product-name Sonoteca `
        --pyinstaller-build-args=--collect-data=flet_web `
        --product-version 1.3.0 --file-version 1.3.0.0 `
        --distpath dist/windows-staging -y
    if ($LASTEXITCODE -ne 0) { throw 'Falló el empaquetado.' }
    Copy-Item -LiteralPath (Join-Path $projectRoot 'dist\windows-staging\Sonoteca') `
        -Destination (Join-Path $projectRoot 'dist') -Recurse -Force
    $legacyDocs = Join-Path $projectRoot 'dist\Sonoteca\_internal\docs'
    if (Test-Path -LiteralPath $legacyDocs) {
        $resolvedDocs = (Resolve-Path -LiteralPath $legacyDocs).Path
        $docsBackup = Join-Path $projectRoot ('data\respaldo-documentos-' + [guid]::NewGuid())
        if (-not $resolvedDocs.StartsWith($projectRoot + '\dist\Sonoteca\') -or
            -not ([IO.Path]::GetFullPath($docsBackup)).StartsWith($projectRoot + '\data\')) {
            throw 'Destino de respaldo fuera del proyecto.'
        }
        Move-Item -LiteralPath $resolvedDocs -Destination $docsBackup
    }
    if ($backup) {
        New-Item -ItemType Directory -Path $portableData -Force | Out-Null
        Get-ChildItem -LiteralPath $backup -Force |
            Copy-Item -Destination $portableData -Recurse -Force
    }
    # Conservar fuentes legibles para inspección y distribución portable.
    $internalRoot = Join-Path $projectRoot 'dist\Sonoteca\_internal'
    Get-ChildItem -LiteralPath $projectRoot -Filter '*.py' -File |
        Copy-Item -Destination $internalRoot -Force
    foreach ($folder in @('models','controllers','services','views')) {
        $sourceRoot = Join-Path $projectRoot $folder
        Get-ChildItem -LiteralPath $sourceRoot -Filter '*.py' -File -Recurse |
            ForEach-Object {
                $relativeSource = $_.FullName.Substring($projectRoot.Length + 1)
                $targetSource = Join-Path $internalRoot $relativeSource
                New-Item -ItemType Directory -Path (Split-Path $targetSource) -Force |
                    Out-Null
                Copy-Item -LiteralPath $_.FullName -Destination $targetSource -Force
            }
    }
} finally {
    Pop-Location
}
