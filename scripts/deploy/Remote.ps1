# Shared native SSH/SCP transport. Restrict every interpolated shell argument.
function Assert-RemoteValue([string]$Value,[string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -notmatch '^[a-zA-Z0-9_./:@-]+$' -or $Value.Contains('..')) { throw "Invalid $Name" }
}
function Invoke-Native([string]$Executable,[string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit $LASTEXITCODE" }
}
function Initialize-Remote([string]$HostName,[string]$UserName,[int]$Port,[string]$IdentityFile,[switch]$InteractiveSsh) {
    if ($HostName -notmatch '^[a-zA-Z0-9][a-zA-Z0-9.-]*$' -or $UserName -notmatch '^[a-zA-Z_][a-zA-Z0-9_-]*$') { throw 'Invalid SSH host/user' }
    if ($Port -lt 1 -or $Port -gt 65535) { throw 'Invalid SSH port' }
    $script:RemoteTarget="${UserName}@${HostName}"
    $script:RemoteUserName=$UserName
    $script:RemoteInteractive=[bool]$InteractiveSsh
    # Let native OpenSSH prompt on the terminal. Never collect/store passwords
    # in PowerShell or alter host-key verification/authentication preferences.
    $batchMode=if($InteractiveSsh){'BatchMode=no'}else{'BatchMode=yes'}
    $script:SshArguments=@('-p',"$Port",'-o',$batchMode)
    $script:ScpArguments=@('-P',"$Port",'-o',$batchMode)
    if ($IdentityFile) { $script:SshArguments+=@('-i',$IdentityFile); $script:ScpArguments+=@('-i',$IdentityFile) }
}
function Invoke-Remote([string]$Command,[switch]$AllocateTerminal) {
    # Windows PowerShell here-strings inherit CRLF from their source file.
    # Bash treats CR as part of options/keywords, so normalize at transport.
    $shellCommand=$Command.Replace("`r`n","`n")
    $terminal=if($AllocateTerminal){@('-tt')}else{@()}
    Invoke-Native 'ssh' ($script:SshArguments+$terminal+@($script:RemoteTarget,$shellCommand))
}
function Invoke-RemoteRootScript([string]$ScriptPath,[string[]]$ScriptArguments,[ValidateSet('bash','python3')][string]$Interpreter='bash') {
    Assert-RemoteValue $ScriptPath 'root script path'
    if (-not $ScriptPath.StartsWith('/')) { throw 'Root script path must be absolute.' }
    foreach($argument in $ScriptArguments) { Assert-RemoteValue $argument 'root script argument' }
    # Compose must read root-only environment and secret configuration files.
    # Keep SSH/sudo prompts in the terminal; never collect passwords in code.
    $prefix=if($script:RemoteUserName -eq 'root'){"exec $Interpreter --"}elseif($script:RemoteInteractive){"exec sudo -- $Interpreter --"}else{"exec sudo -n -- $Interpreter --"}
    $quoted=@($ScriptPath)+@($ScriptArguments) | ForEach-Object { "'$_'" }
    Invoke-Remote ($prefix+' '+($quoted -join ' ')) -AllocateTerminal:($script:RemoteInteractive -and $script:RemoteUserName -ne 'root')
}
function Copy-Remote([string]$Local,[string]$RemotePath) {
    Assert-RemoteValue $RemotePath 'remote path'
    Invoke-Native 'scp' ($script:ScpArguments+@($Local,"${script:RemoteTarget}:$RemotePath"))
}
