# Run all tests before packaging
Write-Host "Running all tests..." -ForegroundColor Green

# Set PYTHONPATH for module imports
$env:PYTHONPATH = "."

# Discover and run all test files matching *test*.py pattern across the entire project
python -m unittest discover -s . -p "*test*.py" -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed! Aborting packaging." -ForegroundColor Red
    exit 1
}

Write-Host "All tests passed! Proceeding with packaging..." -ForegroundColor Green

# Build the package
poetry build

# Deploy files
ssh x@139.196.19.116 'mkdir -p /tmp/leap'
scp dist/*.whl x@139.196.19.116:/tmp/leap/
scp .env x@139.196.19.116:/tmp/leap/
scp ./deploy/deploy.sh x@139.196.19.116:/tmp/leap/