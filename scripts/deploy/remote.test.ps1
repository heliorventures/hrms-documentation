# Offline SSH argument regression. Never contacts a server or reads credentials.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Remote.ps1')
function Assert-Test([bool]$ok,[string]$message) { if(-not $ok){throw $message} }
Initialize-Remote synthetic.invalid deploy 2222 ''
Assert-Test ($script:SshArguments -contains 'BatchMode=yes') 'Default SSH must remain noninteractive'
Assert-Test ($script:ScpArguments -contains 'BatchMode=yes') 'Default SCP must remain noninteractive'
Initialize-Remote synthetic.invalid deploy 2222 'C:\synthetic key\id_ed25519' -InteractiveSsh
foreach($arguments in @($script:SshArguments,$script:ScpArguments)) {
 Assert-Test ($arguments -contains 'BatchMode=no') 'Interactive transport must allow native password/passphrase prompts'
 Assert-Test ($arguments -notcontains 'BatchMode=yes') 'Conflicting batch setting'
 Assert-Test ($arguments -contains 'C:\synthetic key\id_ed25519') 'Identity path must remain one argument'
 Assert-Test (-not (($arguments -join ' ') -match 'StrictHostKeyChecking|UserKnownHostsFile|PreferredAuthentications|PasswordAuthentication')) 'Do not bypass host trust or force an authentication method'
}
Assert-Test ($script:SshArguments[0] -eq '-p' -and $script:SshArguments[1] -eq '2222') 'SSH port changed'
Assert-Test ($script:ScpArguments[0] -eq '-P' -and $script:ScpArguments[1] -eq '2222') 'SCP port changed'
Initialize-Remote synthetic.invalid deploy 22 ''
Assert-Test ($script:SshArguments -contains 'BatchMode=yes') 'Interactive setting leaked into the next default invocation'
function ssh { $script:CapturedRemoteArguments=@($args); $global:LASTEXITCODE=0 }
$windowsCommand="set -eu`r`numask 077`r`nfor image in 'synthetic.tar'; do`r`n    printf '%s\n' `"`$image`"`r`ndone"
Invoke-Remote $windowsCommand
$expectedCommand=$windowsCommand.Replace("`r`n","`n")
Assert-Test ($script:CapturedRemoteArguments[-1] -ceq $expectedCommand) 'Remote command must use LF while preserving quotes and shell expressions'
Assert-Test (-not $script:CapturedRemoteArguments[-1].Contains("`r")) 'Windows carriage return reached SSH'
Invoke-Remote "set -eu`nprintf '%s\n' 'already LF'"
Assert-Test ($script:CapturedRemoteArguments[-1] -ceq "set -eu`nprintf '%s\n' 'already LF'") 'LF command was altered'
Initialize-Remote synthetic.invalid deploy 22 ''
Invoke-RemoteRootScript '/opt/apps/hrms/scripts/release.sh' @('/opt/apps/hrms','synthetic-001','0')
Assert-Test ($script:CapturedRemoteArguments[-1] -ceq "exec sudo -n -- bash -- '/opt/apps/hrms/scripts/release.sh' '/opt/apps/hrms' 'synthetic-001' '0'") 'Batch release must use noninteractive root execution'
Assert-Test ($script:CapturedRemoteArguments -notcontains '-tt') 'Batch release unexpectedly allocated a terminal'
Initialize-Remote synthetic.invalid deploy 22 '' -InteractiveSsh
Invoke-RemoteRootScript '/opt/apps/hrms/scripts/release.sh' @('/opt/apps/hrms','synthetic-001','0')
Assert-Test ($script:CapturedRemoteArguments -contains '-tt') 'Interactive sudo requires a remote terminal'
Assert-Test ($script:CapturedRemoteArguments[-1].StartsWith('exec sudo -- bash -- ')) 'Interactive release must allow native sudo prompt'
Initialize-Remote synthetic.invalid root 22 '' -InteractiveSsh
Invoke-RemoteRootScript '/opt/apps/hrms/scripts/release.sh' @('/opt/apps/hrms')
Assert-Test ($script:CapturedRemoteArguments[-1] -ceq "exec bash -- '/opt/apps/hrms/scripts/release.sh' '/opt/apps/hrms'") 'Root login must not require sudo'
$rejected=$false
try{Invoke-RemoteRootScript '/opt/apps/hrms/scripts/release.sh' @('bad;argument')}catch{$rejected=$true}
Assert-Test $rejected 'Root script arguments must reject shell syntax'
Write-Host 'PASS: explicit interactive SSH/SCP, default batch mode, identity/port preservation and host trust unchanged.'
Write-Host 'PASS: CRLF remote commands normalized to LF without changing shell syntax.'
Write-Host 'PASS: root release uses explicit sudo/TTY policy and rejects unsafe arguments.'
