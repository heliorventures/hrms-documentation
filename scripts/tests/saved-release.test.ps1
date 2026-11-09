# Offline transport regression: synthetic archives, real renderer, mocked SSH/SCP.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$temporary=Join-Path ([IO.Path]::GetTempPath()) ('hrms-saved-release-'+[guid]::NewGuid().ToString('N'))
$global:SavedReleaseCalls=[Collections.Generic.List[object]]::new()
$global:SavedReleaseActualNode=(Get-Command node).Source
function node {
 if($args[0] -like '*check-rollout.cjs') {
  $global:SavedReleaseCalls.Add(@{kind='inventory';arguments=@($args)})
  $index=[Array]::IndexOf($args,'--output')
  [IO.File]::WriteAllText($args[$index+1],'Synthetic transport receipt only')
  $global:LASTEXITCODE=0
 } else { & $global:SavedReleaseActualNode @args }
}
function ssh { $global:SavedReleaseCalls.Add(@{kind='ssh';arguments=@($args)}); $global:LASTEXITCODE=0 }
function scp { $global:SavedReleaseCalls.Add(@{kind='scp';arguments=@($args)}); $global:LASTEXITCODE=0 }
function docker { throw 'Saved release must not build, save or inspect local images' }
function Assert-Test([bool]$ok,[string]$message) { if(!$ok){throw $message} }
try {
 New-Item -ItemType Directory $temporary | Out-Null
 $sums=@()
 foreach($image in @('svc','gateway','ui','organization-events')) {
  $name="kabipay-$image-saved-test.tar"; $file=Join-Path $temporary $name
  [IO.File]::WriteAllText($file,"synthetic $image")
  $sums+=((Get-FileHash $file -Algorithm SHA256).Hash.ToLowerInvariant()+"  $name")
 }
 [IO.File]::WriteAllLines((Join-Path $temporary 'SHA256SUMS'),$sums,[Text.UTF8Encoding]::new($false))
 $manifest=Join-Path $root 'deploy/hrms/manifest.example.json'
 $render=Join-Path $temporary 'render'
 $inventory=Join-Path $temporary 'inventory.txt'
 Set-Content $inventory 'Transport fixture only; receipt semantics tested separately.'
 $entry=Join-Path $root 'scripts/build-save-upload-images.ps1'
 $parameters=@{Tag='saved-test';SkipBuild=$true;OutputDir=$temporary;SourceRoot='Z:/absent';VpsHost='synthetic.invalid';Manifest=$manifest;DeployAfterUpload=$true;InventoryReport=$inventory;ReleaseOutputDir=$render}
 & $entry @parameters
 $calls=$global:SavedReleaseCalls|ConvertTo-Json -Depth 8
 Assert-Test ($calls.Contains('SHA256SUMS')) 'Checksum file not uploaded/verified'
 Assert-Test ($calls.Contains('sha256sum --check')) 'Remote archives not verified'
 Assert-Test ($calls.Contains('cutover-inventory.txt')) 'Inventory not forwarded to deployment'
 Assert-Test (Test-Path (Join-Path $render 'release.json')) 'Reviewed output directory not forwarded'
 $parameters.Remove('InventoryReport');$parameters.InventoryService='synthetic_readonly';$parameters.InventoryDatabase='helior'
 $global:SavedReleaseCalls.Clear()
 & $entry @parameters
 $issued=@($global:SavedReleaseCalls|Where-Object{$_.kind -eq 'inventory'})
 Assert-Test ($issued.Count -eq 1) 'Fresh receipt not issued after upload'
 $sequence=@($global:SavedReleaseCalls)
 $issueIndex=[Array]::IndexOf($sequence,$issued[0])
 Assert-Test ($issueIndex -gt 0 -and (($sequence[0..($issueIndex-1)]|ConvertTo-Json -Depth 8).Contains('sha256sum --check'))) 'Receipt issued before upload verification'
 $global:SavedReleaseCalls.Clear()
 Add-Content (Join-Path $temporary 'kabipay-svc-saved-test.tar') 'tampered'
 $rejected=$false
 try { & $entry @parameters } catch { $rejected=$true }
 Assert-Test $rejected 'Corrupt archive accepted'
 Assert-Test ($global:SavedReleaseCalls.Count -eq 0) 'Corrupt archive contacted remote'
 $parameters.Remove('InventoryService');$parameters.Remove('InventoryDatabase');$rejected=$false
 try { & $entry @parameters } catch { $rejected=$true }
 Assert-Test $rejected 'DeployAfterUpload accepted missing inventory'
 Write-Host 'PASS: saved archives skip builds, checksum verification, exact render/inventory forwarding, rejection before remote actions.'
} finally {
 $resolved=[IO.Path]::GetFullPath($temporary)
 if((Split-Path $resolved -Parent) -ne ([IO.Path]::GetTempPath()).TrimEnd('\') -or (Split-Path $resolved -Leaf) -notlike 'hrms-saved-release-*'){throw 'Unsafe cleanup'}
 Remove-Item -LiteralPath $resolved -Recurse -Force
 Remove-Variable SavedReleaseCalls,SavedReleaseActualNode -Scope Global
}
