# 把本地作业1 目录里的最新图与数据同步到课程仓库，重跑数值模型，然后提交并推送
#
# 用法（PowerShell）：
#   pwsh -File hw1-brewster-angle-microscope\scripts\sync.ps1
#   pwsh -File hw1-brewster-angle-microscope\scripts\sync.ps1 -LocalDir "C:\大三上\仪器光学设计\作业1-布儒斯特角显微镜"
#
# 说明：
#   1. 只同步「图 + CSV」；.blend 与课程报告不进库（含学号/个人信息，且 .blend 由
#      src/bam_build_scene.py 在本仓库内重建）。
#   2. 本仓库为个人仓库，脚本会直接 push（origin/main）。git 不在 PATH 时用 -GitExe 指定。

param(
    [string]$LocalDir = "C:\大三上\仪器光学设计\作业1-布儒斯特角显微镜",
    [string]$GitExe = "",
    [string]$HwDir = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $HwDir
Set-Location $RepoRoot

$prefix = "hw1-brewster-angle-microscope"
$map = @(
    @{ From = "$LocalDir\03_仿真图像\图2_三层膜模型.png";        To = "$prefix\docs\images\film_model.png" },
    @{ From = "$LocalDir\03_仿真图像\图4_反射率随入射角.png";    To = "$prefix\docs\images\refl_vs_angle.png" },
    @{ From = "$LocalDir\03_仿真图像\图5_反射率随膜厚.png";      To = "$prefix\docs\images\refl_vs_thickness.png" },
    @{ From = "$LocalDir\03_仿真图像\图6_十因素反射光强影响.png"; To = "$prefix\docs\images\factors_intensity.png" },
    @{ From = "$LocalDir\03_仿真图像\图7_十因素误差传递.png";    To = "$prefix\docs\images\factors_equiv_thickness.png" },
    @{ From = "$LocalDir\03_仿真图像\图8_对比度与角度消光比.png"; To = "$prefix\docs\images\contrast_vs_er.png" },
    @{ From = "$LocalDir\03_仿真图像\图9_曝光与信噪比.png";      To = "$prefix\docs\images\exposure_vs_snr.png" },
    @{ From = "$LocalDir\03_仿真图像\图10_thetaB漂移.png";       To = "$prefix\docs\images\theta_b_drift.png" },
    @{ From = "$LocalDir\03_仿真图像\图11_对准与对焦示意.png";   To = "$prefix\docs\images\alignment_focus.png" },
    @{ From = "$LocalDir\03_仿真图像\附图A1_俯视布局.png";       To = "$prefix\docs\images\layout_top.png" },
    @{ From = "$LocalDir\03_仿真图像\附图A2_探测臂局部.png";     To = "$prefix\docs\images\detector_arm.png" },
    @{ From = "$LocalDir\04_数值仿真与数据\数据_反射率随入射角.csv"; To = "$prefix\data\refl_vs_angle.csv" },
    @{ From = "$LocalDir\04_数值仿真与数据\数据_反射率随膜厚.csv";   To = "$prefix\data\refl_vs_thickness.csv" },
    @{ From = "$LocalDir\04_数值仿真与数据\数据_十因素扫描与误差传递.csv"; To = "$prefix\data\ten_factors.csv" },
    @{ From = "$LocalDir\04_数值仿真与数据\数据_色散温度对准对焦SNR.csv"; To = "$prefix\data\dispersion_align_focus_snr.csv" }
)

$changed = 0
foreach ($c in $map) {
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

# 每次同步都重跑数值模型，保证文档里的数值与输出一致
Set-Location $HwDir
python "src\bam_model.py" | Out-Null
Set-Location $RepoRoot

if (-not $GitExe) {
    $probe = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($probe) { $GitExe = $probe.Source }
    elseif (Test-Path "C:\selfstudy\AI\git\Git\cmd\git.exe") { $GitExe = "C:\selfstudy\AI\git\Git\cmd\git.exe" }
    else { throw "找不到 git.exe，请用 -GitExe 指定路径" }
}

$dirty = & $GitExe status --porcelain
if (-not $dirty -and $changed -eq 0) {
    Write-Host "文件无变化（数值输出已刷新并一致），本次不提交。"
    return
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
& $GitExe add -A
& $GitExe commit -m "sync(hw1): 更新自本地作业目录 ($stamp)"
& $GitExe push origin main
Write-Host "已提交并推送到 origin/main。" -ForegroundColor Green
