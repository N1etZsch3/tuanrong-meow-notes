param(
    [Parameter(Mandatory = $true)]
    [string] $EnvFile
)

$ErrorActionPreference = "Stop"

function New-RandomHexSecret {
    $bytes = New-Object byte[] 48
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    }
    finally {
        $generator.Dispose()
    }
    return -join ($bytes | ForEach-Object { $_.ToString("x2") })
}

function Set-EnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Content,
        [Parameter(Mandatory = $true)]
        [string] $Name,
        [Parameter(Mandatory = $true)]
        [string] $Value
    )

    $pattern = "(?m)^$([regex]::Escape($Name))=[^\r\n]*$"
    $matches = [regex]::Matches($Content, $pattern)
    if ($matches.Count -gt 1) {
        throw "Development EnvFile must not define $Name more than once."
    }
    if ($matches.Count -eq 1) {
        return [regex]::Replace($Content, $pattern, "$Name=$Value")
    }

    $separator = if ($Content.EndsWith("`n")) { "" } else { "`r`n" }
    return "$Content$separator$Name=$Value`r`n"
}

function Get-OptionalEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Content,
        [Parameter(Mandatory = $true)]
        [string] $Name
    )

    $matches = [regex]::Matches(
        $Content,
        "(?m)^$([regex]::Escape($Name))=(?<value>[^\r\n]*)\s*$"
    )
    if ($matches.Count -gt 1) {
        throw "Development EnvFile must not define $Name more than once."
    }
    if ($matches.Count -eq 0) {
        return ""
    }
    return $matches[0].Groups["value"].Value.Trim()
}

if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Development EnvFile not found: $EnvFile"
}

$resolvedEnvFile = (Resolve-Path -LiteralPath $EnvFile).Path
$content = Get-Content -LiteralPath $resolvedEnvFile -Raw -Encoding UTF8
$insecureValues = @(
    "dev-only-change-me-with-at-least-32-bytes",
    "dev-captcha-secret-change-me",
    "replace-with-at-least-32-random-bytes",
    "replace-with-another-32-byte-secret"
)

foreach ($name in @("CATMAP_JWT_SECRET_KEY", "CATMAP_CAPTCHA_SECRET_KEY")) {
    $currentValue = Get-OptionalEnvValue -Content $content -Name $name
    if ($currentValue.Length -lt 32 -or $insecureValues -contains $currentValue) {
        $content = Set-EnvValue -Content $content -Name $name -Value (New-RandomHexSecret)
    }
}

$content = Set-EnvValue `
    -Content $content `
    -Name "CATMAP_WECHAT_CONTENT_SECURITY_MODE" `
    -Value "off"

$utf8NoBom = New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText($resolvedEnvFile, $content, $utf8NoBom)

Write-Host "Development backend environment prepared with isolated runtime secrets."
