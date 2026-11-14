# Build a public-artifact upload bundle. Runtime env/keys/data are never selected.
function Assert-ReleaseArtifact([string]$Relative) {
    $top=@('compose.json','compose-active.json','release.json','release.sha256','required-tenants.txt','finance-checks.txt','private-files.txt','company-configs.txt','startup-services.txt','cutover-inventory.txt')
    $helpers=@('release.sh','reconcile-env.sh','check-inventory.sh','check-shared-config.mjs','startup-scope.mjs','image-archive.py')
    $ok=($Relative -in $top) -or ($Relative -cmatch '^caddy/[a-z][a-z-]*\.caddy$') -or ($Relative -cmatch '^config/(companies/[a-z]+|ui-[a-z0-9-]+)\.json$') -or ($Relative.StartsWith('scripts/') -and $Relative.Substring(8) -in $helpers)
    if(-not $ok -or $Relative.Split('/') -contains '..'){throw 'Unreviewed release artifact path.'}
}
function New-ReleaseBundle([string]$RenderDirectory,[string]$HelperDirectory,[object]$Release,[string]$AppDir,[string]$ImageDir,[string]$Tag,[bool]$SyncCompose,[bool]$LoadImages,[bool]$Up,[bool]$Validate,[string]$InventoryPath) {
    Add-Type -AssemblyName System.IO.Compression
    $sources=[ordered]@{}
    foreach($relative in $Release.artifacts){Assert-ReleaseArtifact $relative;$sources[$relative]=Join-Path $RenderDirectory $relative}
    foreach($name in @('release.sh','reconcile-env.sh','check-inventory.sh','check-shared-config.mjs','startup-scope.mjs','image-archive.py')){$sources["scripts/$name"]=Join-Path $HelperDirectory $name}
    if($Up){$sources['cutover-inventory.txt']=$InventoryPath}
    $contents=[ordered]@{};$files=@()
    foreach($relative in $sources.Keys){
        Assert-ReleaseArtifact $relative
        $file=Get-Item -LiteralPath $sources[$relative]
        if($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Release artifacts must be regular files.'}
        if($file.Length -gt 4MB){throw 'Release artifact exceeds bounded size.'}
        $contents[$relative]=[IO.File]::ReadAllBytes($file.FullName)
        $hasher=[Security.Cryptography.SHA256]::Create()
        try{$digest=([BitConverter]::ToString($hasher.ComputeHash($contents[$relative]))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
        $files+=@{path=$relative;sha256=$digest}
    }
    $manifest=@{version=1;appDir=$AppDir;imageDir=$ImageDir;tag=$Tag;mode='organization';syncCompose=$SyncCompose;loadImages=$LoadImages;startApplications=$Up;validateApplications=$Validate;files=$files}
    $contents['bundle.json']=[Text.Encoding]::UTF8.GetBytes(($manifest|ConvertTo-Json -Depth 8 -Compress))
    $archivePath=Join-Path $RenderDirectory ('release-upload-'+[guid]::NewGuid().ToString('N')+'.zip')
    $stream=[IO.File]::Open($archivePath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    $archive=[IO.Compression.ZipArchive]::new($stream,[IO.Compression.ZipArchiveMode]::Create,$false)
    try{foreach($relative in $contents.Keys){$entry=$archive.CreateEntry($relative);$output=$entry.Open();try{$bytes=$contents[$relative];$output.Write($bytes,0,$bytes.Length)}finally{$output.Dispose()}}}finally{$archive.Dispose();$stream.Dispose()}
    return @{path=$archivePath;sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()}
}
