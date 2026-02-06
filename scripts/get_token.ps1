param(
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [Parameter(Mandatory=$true)][string]$Username
)

# Uso:
#   .\scripts\get_token.ps1 -BaseUrl "http://localhost:8025" -Username "administrator"

$PasswordSecure = Read-Host "Senha para $Username" -AsSecureString
$PasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
  [Runtime.InteropServices.Marshal]::SecureStringToBSTR($PasswordSecure)
)

$body = @{
  username = $Username
  password = $PasswordPlain
}

$resp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/auth/token" -Body $body -ContentType "application/x-www-form-urlencoded"
$resp.access_token
