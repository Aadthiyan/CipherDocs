# Test script to search and view sources
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0ZW5hbnRfaWQiOiI1ZDEzZDMyYS0wMzM0LTQ3M2MtYTRlZC0xYmRkNmYyZjAxNTgiLCJ1c2VyX2lkIjoiNjQ1YWYyMTAtMDk2Ny00YmRiLTlhODQtNmNiYTZjZTdhNDRkIiwic3ViIjoiNjQ1YWYyMTAtMDk2Ny00YmRiLTlhODQtNmNiYTZjZTdhNDRkIn0.1pUBpBGrfvD4hJ08H-s60TW5t2YnLNpC8U5dIyNvvzY"

$body = @{
    query = "data protection"
    use_advanced = $true
} | ConvertTo-Json

Write-Host "Sending search query..."
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/search/advanced" `
    -Method Post `
    -Headers @{"Authorization" = "Bearer $token"; "Content-Type" = "application/json"} `
    -Body $body | Select-Object -ExpandProperty Content | ConvertFrom-Json

Write-Host ""
Write-Host "=== LLM Answer ==="
Write-Host $response.llm_answer
Write-Host ""
Write-Host "=== LLM Sources ==="
$response.llm_sources | ConvertTo-Json
Write-Host ""
Write-Host "=== Confidence ==="
Write-Host $response.llm_confidence
