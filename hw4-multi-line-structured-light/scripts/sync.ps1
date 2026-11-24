# 从本地作业目录同步最新成果到本仓库，并自动提交（不推送）
#
# 用法（PowerShell）：
#   pwsh -File scripts\sync.ps1
#   pwsh -File scripts\sync.ps1 -PackageDir "C:\大三上\仪器光学设计\作业4-提交包\3024206081-周锐-作业4"
#
# 推送仍由你手动执行（见脚本末尾提示），脚本不会自动 push。

param(
    [string]$PackageDir = "C:\大三上\仪器光学设计\作业4-提交包\3024206081-周锐-作业4",
    [string]$RepoDir = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
Set-Location $RepoDir

$copies = @(
    @{ From = "$PackageDir\04_光条提取算法（加分项）\测试数据_沟槽互反射_相机图像.png"; To = "data\groove_render.png" },
    @{ From = "$PackageDir\02_仿真源文件\作业4_多线结构光测量系统.blend";   To = "assets\multi_line_scene.blend" },
    @{ From = "$PackageDir\03_仿真图像\图6_三种材质_相机图像.png";         To = "docs\images\three_materials.png" },
    @{ From = "$PackageDir\03_仿真图像\图7_沟槽结构布置与截面.png";        To = "docs\images\groove_section.png" },
    @{ From = "$PackageDir\03_仿真图像\图8_沟槽互反射_相机图像.png";       To = "docs\images\reflection.png" }
)

$changed = 0
foreach ($c in $copies) {
    if (-not (Test-Path -LiteralPath $c.From)) {
        if (-not $c.Optional) { Write-Warning "缺少文件：$($c.From)" }
        continue
    }
    $dstDir = Split-Path -Parent (Join-Path $RepoDir $c.To)
    if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }
    $dst = Join-Path $RepoDir $c.To
    $same = (Test-Path -LiteralPath $dst) -and
            ((Get-FileHash -LiteralPath $c.From).Hash -eq (Get-FileHash -LiteralPath $dst).Hash)
    if (-not $same) {
        Copy-Item -LiteralPath $c.From -Destination $dst -Force
        Write-Host "已更新 $($c.To)"
        $changed++
    }
}

# 每次同步都用最新图像重跑一次算法，保证文档里的数值与输出一致
python "src\line_center_extract.py" --outdir "out"

if ($changed -eq 0) {
    git status --short
    Write-Host "文件无变化（算法输出已刷新），如需记录请手动改 CHANGELOG。"
} else {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    git add -A
    git commit -m "sync: 更新自本地作业目录 ($stamp)"
    Write-Host "已提交。推送命令（由你手动执行）：" -ForegroundColor Yellow
    Write-Host "  git push origin main"
}
