# Native-command orchestration test. SSH/SCP are mocked; no VPS contacted.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$temporary=Join-Path ([System.IO.Path]::GetTempPath()) ('hrms-deploy-test-'+[guid]::NewGuid().ToString('N'))
$global:HrmsDeploymentTestCalls=[System.Collections.Generic.List[object]]::new()
function ssh { $global:HrmsDeploymentTestCalls.Add(@{kind='ssh';arguments=@($args)}); $global:LASTEXITCODE=0 }
function scp { $global:HrmsDeploymentTestCalls.Add(@{kind='scp';arguments=@($args)}); $global:LASTEXITCODE=0 }
function Assert-Test([bool]$Condition,[string]$Message) { if(-not $Condition){throw $Message} }
try {
    New-Item -ItemType Directory -Path $temporary -Force | Out-Null
    $output=Join-Path $temporary 'render'
    New-Item -ItemType Directory -Path $output -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $output 'stale-secret.env') -Value 'SYNTHETIC_ONLY=do-not-upload'
    $manifest=Get-Content -LiteralPath (Join-Path $root 'deploy/hrms/manifest.example.json') -Raw | ConvertFrom-Json
    $manifest.PSObject.Properties.Remove('tag');$manifest.PSObject.Properties.Remove('appDir')
    $inputFile=Join-Path $temporary 'manifest.json'
    [System.IO.File]::WriteAllText($inputFile,($manifest|ConvertTo-Json -Depth 20),[System.Text.UTF8Encoding]::new($false))
    $entry=Join-Path $root 'scripts/deploy-on-vps.ps1'
    & $entry -Tag synthetic-001 -Manifest $inputFile -OutputDir $output -RenderOnly
    Assert-Test ($global:HrmsDeploymentTestCalls.Count -eq 0) 'RenderOnly contacted remote'
    $rejected=$false
    try { & $entry -Tag synthetic-001 -Manifest $inputFile -OutputDir $output -VpsHost synthetic.invalid -Deploy } catch { $rejected=$true }
    Assert-Test $rejected 'Startup accepted missing registry inventory'
    Assert-Test ($global:HrmsDeploymentTestCalls.Count -eq 0) 'Missing inventory contacted remote'
    $inventory=Join-Path $temporary 'synthetic-inventory.txt'
    Set-Content -LiteralPath $inventory -Value 'Synthetic transport fixture; remote semantics exercised by native Bash tests.'
    & $entry -Tag synthetic-001 -Manifest $inputFile -OutputDir $output -VpsHost synthetic.invalid -Deploy -InventoryReport $inventory
    $uploads=@($global:HrmsDeploymentTestCalls|Where-Object{$_.kind -eq 'scp'})
    $release=Get-Content -LiteralPath (Join-Path $output 'release.json') -Raw|ConvertFrom-Json
    Assert-Test ($uploads.Count -eq ($release.artifacts.Count+5)) 'Unexpected upload inventory'
    Assert-Test (-not (($uploads|ConvertTo-Json -Depth 10).Contains('stale-secret.env'))) 'Reused output secret uploaded'
    $commands=($global:HrmsDeploymentTestCalls|Where-Object{$_.kind -eq 'ssh'}|ForEach-Object{$_.arguments -join ' '}) -join "`n"
    Assert-Test ($commands.Contains("'/opt/apps/hrms/scripts/release.sh'")) 'Canonical release script not called'
    Assert-Test (-not $commands.Contains('/opt/apps/Caddyfile')) 'Application changed shared Caddy'
    Assert-Test (-not $commands.Contains('psql')) 'Application attempted PostgreSQL provisioning'
    $before=$global:HrmsDeploymentTestCalls.Count
    foreach($switch in @('SyncEnvExample','SyncCaddyfile','SyncTenantDatabaseTarget')) {
        $parameters=@{Tag='synthetic-001';Manifest=$inputFile;OutputDir=$output;VpsHost='synthetic.invalid'}
        $parameters[$switch]=$true;$rejected=$false
        try { & $entry @parameters }catch{$rejected=$true}
        Assert-Test $rejected "$switch should reject mixed infrastructure operation"
    }
    Assert-Test ($global:HrmsDeploymentTestCalls.Count -eq $before) 'Rejected operation contacted remote'
    $rejected=$false
    try{& $entry -Tag synthetic-001 -Manifest $inputFile -OutputDir $output -VpsHost 'bad;host' -Deploy -InventoryReport $inventory}catch{$rejected=$true}
    Assert-Test $rejected 'SSH selector injection accepted'
    Assert-Test ($global:HrmsDeploymentTestCalls.Count -eq $before) 'Invalid host contacted remote'
    Write-Host 'PASS: render-only, defaultable manifest, exact artifact allowlist, app-only remote flow and rejected mixed/injected operations.'
}finally {
    $resolved=[System.IO.Path]::GetFullPath($temporary)
    $parent=[System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
    if ((Split-Path -Parent $resolved) -ne $parent -or (Split-Path -Leaf $resolved) -notlike 'hrms-deploy-test-*') { throw 'Unsafe test cleanup path' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
    Remove-Variable -Name HrmsDeploymentTestCalls -Scope Global -ErrorAction SilentlyContinue
}
