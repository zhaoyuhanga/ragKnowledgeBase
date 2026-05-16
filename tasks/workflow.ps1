# Codex-Cursor 协作工作流辅助脚本
$TASKS_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

function New-TaskCard {
    param([string]$Title, [string]$Priority = "P1", [string]$Desc, [string[]]$Files, [string[]]$Checklist, [string]$ExpectedFix)
    $allTasks = @(Get-ChildItem "$TASKS_ROOT\queue","$TASKS_ROOT\feedback","$TASKS_ROOT\done" -Filter "TASK-*.md" -Recurse -ErrorAction SilentlyContinue)
    $seq = $allTasks.Count + 1
    $id = "TASK-{0:D3}" -f $seq
    $safeTitle = $Title -replace '[^\w\-\u4e00-\u9fa5]+','-' -replace '-+','-'
    $fileName = "${id}-${safeTitle}.md"
    $fileList = ($Files | ForEach-Object { "- ``$_``" }) -join "`n"
    $checkList = ($Checklist | ForEach-Object { "- [ ] $_" }) -join "`n"
    $date = Get-Date -Format "yyyy-MM-dd HH:mm"
    $content = @"
# ${id} ${Title}

**状态**: pending
**优先级**: ${Priority}
**指派**: Cursor
**创建时间**: ${date}
**完成时间**: 

---

## 问题描述
${Desc}

## 涉及文件
${fileList}

## 预期修改
${ExpectedFix}

## 验收标准
${checkList}

---

## Codex 验收记录
| 轮次 | 时间 | 结果 | 备注 |
|------|------|------|------|

## Cursor 回复区

"@
    $out = Join-Path "$TASKS_ROOT\queue" $fileName
    $content | Set-Content -Path $out -Encoding UTF8
    Write-Host "Created: queue/$fileName" -ForegroundColor Green
    Write-Host "Open in Cursor: cursor tasks/queue/$fileName" -ForegroundColor Cyan
}

function Show-TaskBoard {
    Write-Host "`n===== PENDING (queue) =====" -ForegroundColor Yellow
    $q = Get-ChildItem "$TASKS_ROOT\queue" -Filter "*.md" -ErrorAction SilentlyContinue
    if ($q) { $q | ForEach-Object { Write-Host "  $($_.Name)" } } else { Write-Host "  (empty)" }
    Write-Host "===== REWORK (feedback) =====" -ForegroundColor Red
    $f = Get-ChildItem "$TASKS_ROOT\feedback" -Filter "*.md" -ErrorAction SilentlyContinue
    if ($f) { $f | ForEach-Object { Write-Host "  $($_.Name)" } } else { Write-Host "  (empty)" }
    Write-Host "===== DONE =====" -ForegroundColor Green
    $d = Get-ChildItem "$TASKS_ROOT\done" -Filter "*.md" -ErrorAction SilentlyContinue
    if ($d) { $d | ForEach-Object { Write-Host "  $($_.Name)" } } else { Write-Host "  (empty)" }
}

function Invoke-CodexVerify {
    param([string]$TaskFile)
    foreach ($dir in @("queue","feedback")) {
        $src = Join-Path "$TASKS_ROOT\$dir" $TaskFile
        if (Test-Path $src) {
            Write-Host "`nVerifying: $TaskFile" -ForegroundColor Cyan
            Write-Host "--- Task Content ---" -ForegroundColor Gray
            Get-Content $src | Write-Host
            Write-Host "`n--- Git Diff ---" -ForegroundColor Gray
            git diff --stat
            return
        }
    }
    Write-Host "Task not found: $TaskFile" -ForegroundColor Red
}

function Move-TaskToDone {
    param([string]$TaskFile)
    foreach ($dir in @("queue","feedback")) {
        $src = Join-Path "$TASKS_ROOT\$dir" $TaskFile
        if (Test-Path $src) {
            $date = Get-Date -Format "yyyy-MM-dd HH:mm"
            $body = Get-Content $src -Raw
            $body = $body -replace '\*\*状态\*\*:.*','**状态**: done'
            $body = $body -replace '\*\*完成时间\*\*:.*',"**完成时间**: ${date}"
            $body | Set-Content -Path $src -Encoding UTF8
            Move-Item $src "$TASKS_ROOT\done\" -Force
            Write-Host "Verified & moved to done: $TaskFile" -ForegroundColor Green
            return
        }
    }
    Write-Host "Task not found: $TaskFile" -ForegroundColor Red
}

function Move-TaskToFeedback {
    param([string]$TaskFile, [string]$Reason)
    foreach ($dir in @("queue","done")) {
        $src = Join-Path "$TASKS_ROOT\$dir" $TaskFile
        if (Test-Path $src) {
            $date = Get-Date -Format "yyyy-MM-dd HH:mm"
            $body = Get-Content $src -Raw
            $body = $body -replace '\*\*状态\*\*:.*','**状态**: rework'
            $body = $body + "`n## Codex 验收反馈 (${date})`n${Reason}`n"
            $body | Set-Content -Path $src -Encoding UTF8
            Move-Item $src "$TASKS_ROOT\feedback\" -Force
            Write-Host "Rework sent to feedback: $TaskFile" -ForegroundColor Red
            return
        }
    }
    Write-Host "Task not found: $TaskFile" -ForegroundColor Red
}

function Invoke-CleanupCheck {
    Write-Host "`n===== Codex Cleanup Check =====" -ForegroundColor Cyan
    Write-Host "Checking for debug statements..." -ForegroundColor Gray
    $debugHits = Select-String -Path (Get-ChildItem -Recurse -Include *.ts,*.js,*.tsx,*.jsx -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch 'node_modules|dist|.git' }) -Pattern 'console\.(log|debug)\(|debugger' -List -ErrorAction SilentlyContinue
    if ($debugHits) {
        Write-Host "  FOUND debug statements:" -ForegroundColor Yellow
        $debugHits | ForEach-Object { Write-Host "    $($_.Path):$($_.LineNumber)" }
    } else {
        Write-Host "  Clean - no debug statements found" -ForegroundColor Green
    }
    Write-Host "Checking for TODO comments..." -ForegroundColor Gray
    $todoHits = Select-String -Path (Get-ChildItem -Recurse -Include *.ts,*.js,*.tsx,*.jsx -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch 'node_modules|dist|.git' }) -Pattern 'TODO|FIXME|HACK' -List -ErrorAction SilentlyContinue
    if ($todoHits) {
        Write-Host "  FOUND TODO/FIXME/HACK:" -ForegroundColor Yellow
        $todoHits | ForEach-Object { Write-Host "    $($_.Path):$($_.LineNumber)" }
    } else {
        Write-Host "  Clean - no TODO/FIXME/HACK" -ForegroundColor Green
    }
    Write-Host "Checking unused imports (summary)..." -ForegroundColor Gray
    Write-Host "  Run 'npx eslint --rule no-unused-vars:error' for full check" -ForegroundColor Gray
}

Write-Host "Codex-Cursor Workflow loaded. Commands:" -ForegroundColor Cyan
Write-Host "  New-TaskCard <params>     - Create new task"
Write-Host "  Show-TaskBoard             - Display all tasks"
Write-Host "  Invoke-CodexVerify <file>  - Verify a completed task"
Write-Host "  Move-TaskToDone <file>    - Mark task as verified done"
Write-Host "  Move-TaskToFeedback <file> -Reason <text> - Send back for rework"
Write-Host "  Invoke-CleanupCheck        - Check for debug logs, TODOs, unused imports"
