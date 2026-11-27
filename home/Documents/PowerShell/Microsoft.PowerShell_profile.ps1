# PowerShell profile (pwsh)

$env:EDITOR = 'vim'
$env:VISUAL = 'vim'
$env:SRC_DIR = Join-Path $HOME 'src'

# PSReadLine: vi mode + prefix history search matching zsh config
if (Get-Module -ListAvailable -Name PSReadLine) {
    Import-Module PSReadLine
    Set-PSReadLineOption -EditMode Vi
    Set-PSReadLineOption -HistoryNoDuplicates
    Set-PSReadLineKeyHandler -Key UpArrow -Function HistorySearchBackward
    Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward
    Set-PSReadLineKeyHandler -Key Ctrl+r -Function ReverseSearchHistory
    Set-PSReadLineKeyHandler -Key Ctrl+s -Function ForwardSearchHistory
}

# Aliases & helpers matching zsh/rc.d/
function ll {
    Get-ChildItem -Force @args
}

function mktempcd {
    $dir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $dir | Out-Null
    Set-Location $dir
}

function code-remote {
    param(
        [Parameter(Mandatory = $true)][string]$HostName,
        [Parameter(Mandatory = $true)][string]$Path
    )
    code --remote "ssh-remote+$HostName" $Path
}

function re-source {
    . $PROFILE
}

if (Get-Command bazel -ErrorAction SilentlyContinue) {
    Set-Alias -Name blaze -Value bazel
}

# Tool hooks (keep last)
if (Get-Command mise -ErrorAction SilentlyContinue) {
    (& mise activate pwsh) | Out-String | Invoke-Expression
}

if (Get-Command starship -ErrorAction SilentlyContinue) {
    Invoke-Expression (& starship init powershell)
}
