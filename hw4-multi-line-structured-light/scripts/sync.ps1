# 把本地作业4 目录里的最新成果同步到课程仓库，重跑算法校验，然后提交并推送
#
# 用法（PowerShell）：
#   pwsh -File hw4-multi-line-structured-light\scripts\sync.ps1
#   pwsh -File hw4-multi-line-structured-light\scripts\sync.ps1 -PackageDir "C:\大三上\仪器光学设计\作业4-提交包\3024206081-周锐-作业4"
#
# 说明：本仓库为个人仓库，脚本会直接 push（origin/main）。提交包里含学号的报告、录屏脚本不会进库。

param(
    [string]$PackageDir = "C:\大三上\仪器光学设计\作业4-提交包\3024206081-周锐-作业4",
    [string]$HwDir = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $HwDir
Set-Location $RepoRoot

$prefix = "hw4-multi-line-structured-light"
$copies = @(
    @{ From = "$PackageDir\04_光条提取算法（加分项）\测试数据_沟槽互反射_相机图像.png"; To = "$prefix\data\groove_render.png" },
    @{ From = "$PackageDir\02_仿真源文件\作业4_多线结构光测量系统.blend";   To = "$prefix\assets\multi_line_scene.blend" },
    @{ From = "$PackageDir\03_仿真图像\图6_三种材质_相机图像.png";         To = "$prefix\docs\images\three_materials.png" },
    @{ From = "$PackageDir\03_仿真图像\图7_沟槽结构布置与截面.png";        To = "$prefix\docs\images\groove_section.png" },
    @{ From = "$PackageDir\03_仿真图像\图8_沟槽互反射_相机图像.png";       To = "$prefix\docs\images\reflection.png" }
)

$changed = 0
foreach ($c in $copies) {
    if (-not (Test-Path -LiteralPath $c.From)) {
        Write-Warning "缺少文件：$($c.From)"
        continue
    }
    $dst = Join-Path $RepoRoot $c.To
    $same = (Test-Path -LiteralPath $dst) -and
            ((Get-FileHash -LiteralPath $c.From).Hash -eq (Get-FileHash -LiteralPath $dst).Hash)
    if (-not $same) {
        Copy-Item -LiteralPath $c.From -Destination $dst -Force
        Write-Host "已更新 $($c.To)"
        $changed++
    }
}

# 每次同步都用最新图像重跑一次算法，保证文档里的数值与输出一致
Set-Location $HwDir
python "src\line_center_extract.py" --outdir "out"
Set-Location $RepoRoot

$dirty = git status --porcelain
if (-not $dirty -and $changed -eq 0) {
    Write-Host "文件无变化（算法输出已刷新并一致），本次不提交。"
    return
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
git add -A
git commit -m "sync(hw4): 更新自本地作业目录 ($stamp)"
git push origin main
Write-Host "已提交并推送到 origin/main。" -ForegroundColor Green
