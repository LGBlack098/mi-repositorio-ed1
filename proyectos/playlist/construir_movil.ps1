# Prepare fuentes limpias: no empaquete audios ni datos del usuario.
param([string]$BuildDirectory = '')
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$stageParent = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Sonoteca\Cache\build'
$stage = if ($BuildDirectory) {
    [IO.Path]::GetFullPath($BuildDirectory)
} else {
    Join-Path $stageParent 'android'
}
if (-not $stage.StartsWith(([IO.Path]::GetFullPath($stageParent)) + '\')) {
    throw 'El directorio de compilación móvil debe quedar en la caché de Sonoteca.'
}
New-Item -ItemType Directory -Path $stage -Force | Out-Null
foreach ($file in @('main.py','pyproject.toml')) {
    Copy-Item -LiteralPath (Join-Path $projectRoot $file) -Destination $stage
}
# Limite el proyecto Flutter generado al destino de este script (Android).
Add-Content -LiteralPath (Join-Path $stage 'pyproject.toml') -Value @'

[tool.flet.flutter.pubspec.flutter.config]
enable-windows-desktop = false
enable-linux-desktop = false
enable-macos-desktop = false
'@
foreach ($folder in @('models','controllers','services','views')) {
    $sourceRoot = Join-Path $projectRoot $folder
    Get-ChildItem -LiteralPath $sourceRoot -File -Filter '*.py' -Recurse |
        ForEach-Object {
            $relativeSource = $_.FullName.Substring($projectRoot.Length + 1)
            $targetSource = Join-Path $stage $relativeSource
            New-Item -ItemType Directory -Path (Split-Path $targetSource) -Force |
                Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $targetSource
        }
}
$assetsStage = Join-Path $stage 'assets'
New-Item -ItemType Directory -Path $assetsStage -Force | Out-Null
foreach ($name in @('sonoteca.ico', 'sonoteca.png')) {
    Copy-Item -LiteralPath (Join-Path $projectRoot ('assets\' + $name)) `
        -Destination (Join-Path $stage 'assets')
}
# El destino Android no necesita plugins de escritorio ni sus symlinks.
# Limitar plataformas solo en este proceso evita cambiar ajustes de Windows.
$previousWindows = $env:FLUTTER_WINDOWS
$previousLinux = $env:FLUTTER_LINUX
$previousMacos = $env:FLUTTER_MACOS
try {
    $env:FLUTTER_WINDOWS = 'false'
    $env:FLUTTER_LINUX = 'false'
    $env:FLUTTER_MACOS = 'false'
    & $projectPython -m flet.cli build apk $stage --yes --no-rich-output --arch arm64-v8a `
        --product Sonoteca --build-version 1.3.0 `
        --output (Join-Path $projectRoot 'dist\android')
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el APK. Revise el registro.' }
} finally {
    $env:FLUTTER_WINDOWS = $previousWindows
    $env:FLUTTER_LINUX = $previousLinux
    $env:FLUTTER_MACOS = $previousMacos
}
