function Assert-DependencySecurity {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceDirectory,
        [Parameter(Mandatory = $true)]
        [string]$Role
    )

    $mounts = @()
    foreach ($name in @('package.json', 'package-lock.json')) {
        $source = Join-Path $SourceDirectory $name
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "$Role security audit requires $name"
        }
        # Docker --mount uses commas as separators. Refuse ambiguous paths.
        if ($source.Contains(',')) { throw "$Role audit source path cannot contain a comma" }
        $mounts += @('--mount', "type=bind,source=$source,target=/app/$name,readonly")
    }

    Write-Host "==> Auditing $Role dependencies (including development tools)" -ForegroundColor Cyan
    # A fresh container prevents a cached Docker layer from hiding new advisories.
    # Mount only dependency manifests; never source, .env files or registry credentials.
    docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges `
        --memory 512m --cpus 1 --pids-limit 128 --tmpfs /tmp:rw,nosuid,nodev,size=128m `
        --env npm_config_cache=/tmp/npm --workdir /app @mounts `
        --entrypoint npm node:22-bookworm-slim audit --package-lock-only `
        --include=dev --include=optional --include=peer --ignore-scripts --audit-level=low `
        --registry=https://registry.npmjs.org --fetch-retries=1 --fetch-timeout=60000
    if ($LASTEXITCODE -ne 0) {
        throw "$Role dependency audit failed or could not complete (exit $LASTEXITCODE). Release stopped."
    }
}
