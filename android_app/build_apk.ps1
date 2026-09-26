# Build script for Women Safety Shield Android APK
$ErrorActionPreference = "Stop"

$AndroidSdk = "$env:LOCALAPPDATA\Android\Sdk"
$BuildTools = "$AndroidSdk\build-tools\34.0.0"
$PlatformJar = "$AndroidSdk\platforms\android-34\android.jar"
$Javac = "C:\Program Files\Java\jdk-25.0.2\bin\javac.exe"
$Keytool = "C:\Program Files\Java\jdk-25.0.2\bin\keytool.exe"

$Aapt2 = "$BuildTools\aapt2.exe"
$D8 = "$BuildTools\d8.bat"
$Zipalign = "$BuildTools\zipalign.exe"
$Apksigner = "$BuildTools\apksigner.bat"

$AppDir = "$PSScriptRoot\app"
$SrcDir = "$AppDir\src\main"
$BuildDir = "$AppDir\build"
$PythonExe = "$PSScriptRoot\..\.venv\Scripts\python.exe"

Write-Host "=== Building Women Safety Shield Android APK ===" -ForegroundColor Cyan

# 0. Bundle the full rendered website into assets/www
Write-Host "-> Packaging full website into assets/www..." -ForegroundColor Yellow
& $PythonExe "$PSScriptRoot\prepare_assets.py"

# 1. Clean build directory
if (Test-Path $BuildDir) {
    Remove-Item -Recurse -Force $BuildDir
}
New-Item -ItemType Directory -Path "$BuildDir\compiled_res" | Out-Null
New-Item -ItemType Directory -Path "$BuildDir\gen" | Out-Null
New-Item -ItemType Directory -Path "$BuildDir\classes" | Out-Null
New-Item -ItemType Directory -Path "$BuildDir\dex" | Out-Null

# 2. Compile Android Resources with aapt2
Write-Host "-> Compiling resources with aapt2..." -ForegroundColor Yellow
& $Aapt2 compile --dir "$SrcDir\res" -o "$BuildDir\compiled_res\res.zip"

# 3. Link resources and generate R.java and initial APK
Write-Host "-> Linking resources and generating R.java..." -ForegroundColor Yellow
& $Aapt2 link `
    -I $PlatformJar `
    --manifest "$SrcDir\AndroidManifest.xml" `
    -o "$BuildDir\app_unaligned.apk" `
    --java "$BuildDir\gen" `
    -A "$SrcDir\assets" `
    "$BuildDir\compiled_res\res.zip" `
    --auto-add-overlay

# 4. Compile Java sources (including generated R.java)
Write-Host "-> Compiling Java sources with javac..." -ForegroundColor Yellow
$JavaFiles = Get-ChildItem -Path "$SrcDir\java", "$BuildDir\gen" -Filter "*.java" -Recurse | Select-Object -ExpandProperty FullName
& $Javac --release 8 -g:lines,source -cp "`"$PlatformJar`"" -d "$BuildDir\classes" $JavaFiles

# 5. Convert compiled class files to classes.dex with d8 using argfile
Write-Host "-> Converting to classes.dex with d8..." -ForegroundColor Yellow
$ClassFiles = Get-ChildItem -Path "$BuildDir\classes" -Filter "*.class" -Recurse | Select-Object -ExpandProperty FullName
$D8ArgsFile = "$BuildDir\d8_inputs.txt"
Set-Content -Path $D8ArgsFile -Value $ClassFiles

& $D8 --lib "$PlatformJar" --min-api 21 --output "$BuildDir\dex" "@$D8ArgsFile"
if ($LASTEXITCODE -ne 0) {
    throw "d8 failed with exit code $LASTEXITCODE"
}

# 6. Add classes.dex into app_unaligned.apk using Python zipfile
Write-Host "-> Injecting classes.dex into APK..." -ForegroundColor Yellow
$DexFile = "$BuildDir\dex\classes.dex"
$ApkFile = "$BuildDir\app_unaligned.apk"
& $PythonExe -c "import zipfile; z = zipfile.ZipFile(r'$ApkFile', 'a'); z.write(r'$DexFile', 'classes.dex'); z.close()"

# 7. Zipalign the APK
Write-Host "-> 4-byte zip aligning APK..." -ForegroundColor Yellow
& $Zipalign -f -p 4 "$BuildDir\app_unaligned.apk" "$BuildDir\app_aligned.apk"

# 8. Generate keystore if not exists
$Keystore = "$AppDir\shield-release.keystore"
if (-not (Test-Path $Keystore)) {
    Write-Host "-> Generating release signing keystore..." -ForegroundColor Yellow
    & $Keytool -genkeypair -v -keystore $Keystore -storepass "shield123456" -alias "shieldkey" -keypass "shield123456" -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Women Safety Shield, OU=Shield Matrix, O=Safety Corp, L=Delhi, ST=Delhi, C=IN"
}

# 9. Sign APK with apksigner
Write-Host "-> Signing APK with apksigner..." -ForegroundColor Yellow
$FinalApk = "$BuildDir\WomenSafetyShield.apk"
& $Apksigner sign --ks "$Keystore" --ks-pass "pass:shield123456" --key-pass "pass:shield123456" --ks-key-alias "shieldkey" --out "$FinalApk" "$BuildDir\app_aligned.apk"
if ($LASTEXITCODE -ne 0) {
    throw "apksigner sign failed with exit code $LASTEXITCODE"
}

# 10. Verify signature
Write-Host "-> Verifying APK signature..." -ForegroundColor Yellow
& $Apksigner verify "$FinalApk"
if ($LASTEXITCODE -ne 0) {
    throw "apksigner verify failed"
}

# 11. Copy to output and static download directory
$TargetDir = "$PSScriptRoot\..\static\downloads"
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}
Copy-Item $FinalApk "$TargetDir\women-safety-shield.apk" -Force
Copy-Item $FinalApk "$TargetDir\women-safety-shield-v2.4.apk" -Force
Copy-Item $FinalApk "$PSScriptRoot\WomenSafetyShield.apk" -Force

$ApkItem = Get-Item "$TargetDir\women-safety-shield.apk"
$ApkSizeMb = [math]::Round($ApkItem.Length / 1MB, 2)
$ApkSizeKb = [math]::Round($ApkItem.Length / 1KB, 1)

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "  SUCCESS! Women Safety Shield APK Built & Signed!" -ForegroundColor Green
Write-Host "  File Path: $TargetDir\women-safety-shield.apk" -ForegroundColor Green
Write-Host "  Size: $ApkSizeKb KB ($ApkSizeMb MB)" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Green
