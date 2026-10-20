# Shared native SSH/SCP transport. Restrict every interpolated shell argument.
function Assert-RemoteValue([string]$Value,[string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -notmatch '^[a-zA-Z0-9_./:@-]+$' -or $Value.Contains('..')) { throw "Invalid $Name" }
}
function Invoke-Native([string]$Executable,[string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit $LASTEXITCODE" }
}
function Initialize-Remote([string]$HostName,[string]$UserName,[int]$Port,[string]$IdentityFile) {
    if ($HostName -notmatch '^[a-zA-Z0-9][a-zA-Z0-9.-]*$' -or $UserName -notmatch '^[a-zA-Z_][a-zA-Z0-9_-]*$') { throw 'Invalid SSH host/user' }
    if ($Port -lt 1 -or $Port -gt 65535) { throw 'Invalid SSH port' }
    $script:RemoteTarget="${UserName}@${HostName}"
    $script:SshArguments=@('-p',"$Port",'-o','BatchMode=yes')
    $script:ScpArguments=@('-P',"$Port",'-o','BatchMode=yes')
    if ($IdentityFile) { $script:SshArguments+=@('-i',$IdentityFile); $script:ScpArguments+=@('-i',$IdentityFile) }
}
function Invoke-Remote([string]$Command) { Invoke-Native 'ssh' ($script:SshArguments+@($script:RemoteTarget,$Command)) }
function Copy-Remote([string]$Local,[string]$RemotePath) {
    Assert-RemoteValue $RemotePath 'remote path'
    Invoke-Native 'scp' ($script:ScpArguments+@($Local,"${script:RemoteTarget}:$RemotePath"))
}
