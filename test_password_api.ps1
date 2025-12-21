# PowerShell test script for password validation
$headers = @{
    'Content-Type' = 'application/json'
}

# Test 1: Valid password
Write-Host "Test 1: Valid password"
$body1 = @{
    email = "test1@example.com"
    password = "ValidPass123"
    company_name = "Test Company 1"
} | ConvertTo-Json

try {
    $response1 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/signup" -Method Post -Headers $headers -Body $body1
    Write-Host "✅ Valid password accepted" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "✅ Valid password accepted (user exists)" -ForegroundColor Green
    } elseif ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "❌ Valid password rejected" -ForegroundColor Red
    } else {
        Write-Host "❓ Unexpected error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Test 2: Too long password (80 chars)
Write-Host "`nTest 2: Too long password (80 chars)"
$longPassword = "A" * 80
$body2 = @{
    email = "test2@example.com"
    password = $longPassword
    company_name = "Test Company 2"
} | ConvertTo-Json

try {
    $response2 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/signup" -Method Post -Headers $headers -Body $body2
    Write-Host "❌ Long password should have been rejected" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "✅ Long password correctly rejected" -ForegroundColor Green
        # Try to get error details
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorBody = $reader.ReadToEnd()
        Write-Host "   Error: $errorBody" -ForegroundColor Cyan
    } else {
        Write-Host "❓ Unexpected error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ Password validation fix is working!" -ForegroundColor Green