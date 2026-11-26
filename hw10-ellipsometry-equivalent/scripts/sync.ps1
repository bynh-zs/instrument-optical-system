# 把本地作业10 目录里的最新截图、数据、结果图同步到课程仓库，重跑数值与绘图，
#
# 用法（PowerShell）：
#   pwsh -File hw10-ellipsometry-equivalent\scripts\sync.ps1
#   pwsh -File hw10-ellipsometry-equivalent\scripts\sync.ps1 -LocalDir "C:\大三上\仪器光学设计\椭圆偏振测量的等效实现"
#
# 说明：
#   1. 只同步「截图 + 数据 CSV + 文本记录」；报告 docx/pdf、57 MB 录屏、含学号的
#      build_final_report.py 不进库。
#   2. 数据与结果图以 build_data.py / draw_results.py 的重跑结果为准，不从本地目录覆盖。
#   3. 本仓库为个人仓库，脚本直接 push（origin/main）。

param(
    [string]$LocalDir = "C:\大三上\仪器光学设计\椭圆偏振测量的等效实现",
    [string]$Python = "",
    [string]$GitExe = "",
    [string]$HwDir = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $HwDir
$prefix = "hw10-ellipsometry-equivalent"
Set-Location $RepoRoot

$changed = 0
foreach ($f in (Get-ChildItem -LiteralPath "$LocalDir\截图" -Filter *.png -File)) {
    $dst = Join-Path $RepoRoot "$prefix\docs\screenshots\$($f.Name)"
    $same = (Test-Path -LiteralPath $dst) -and
            ((Get-FileHash -LiteralPath $f.FullName).Hash -eq (Get-FileHash -LiteralPath $dst).Hash)
    if (-not $same) {
        Copy-Item -LiteralPath $f.FullName -Destination $dst -Force
        Write-Host "已更新 $prefix\docs\screenshots\$($f.Name)"
        $changed++
    }
}

if (-not $Python) {
    $probe = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($probe) { $Python = $probe.Source } else { throw "找不到 python.exe，请用 -Python 指定路径" }
}

# 重跑数值与绘图：文档里的数字与图必须来自这一次输出
Set-Location (Join-Path $HwDir "src")
& $Python "build_data.py"
& $Python "draw_results.py"
Set-Location $RepoRoot

if (-not $GitExe) {
    $probe = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($probe) { $GitExe = $probe.Source }
    elseif (Test-Path "C:\selfstudy\AI\git\Git\cmd\git.exe") { $GitExe = "C:\selfstudy\AI\git\Git\cmd\git.exe" }
    else { throw "找不到 git.exe，请用 -GitExe 指定路径" }
}

$dirty = & $GitExe status --porcelain
if (-not $dirty -and $changed -eq 0) {
    Write-Host "文件无变化（数值与图已重跑且一致），本次不提交。"
    return
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
& $GitExe add -A
& $GitExe -c http.sslBackend=openssl -c http.proxy=http://127.0.0.1:7897 commit -m "sync(hw10): 更新自本地作业目录 ($stamp)"
& $GitExe -c http.sslBackend=openssl -c http.proxy=http://127.0.0.1:7897 push origin main
Write-Host "已提交并推送到 origin/main。" -ForegroundColor Green
