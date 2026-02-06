$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
$env:WIN_CSC_LINK = ""

Write-Host "Environment variables set: CSC_IDENTITY_AUTO_DISCOVERY=false" -ForegroundColor Green
Write-Host "start building..." -ForegroundColor Yellow

npm run build
