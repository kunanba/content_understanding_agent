# Deploy using ACR Build (no local Docker needed)
$ErrorActionPreference = "Stop"

# Configuration
$RESOURCE_GROUP = "demo-ak"
$LOCATION = "westus"
$ACR_NAME = "acrcu2220"
$IMAGE_NAME = "streamlit-app"
$IMAGE_TAG = (Get-Date -Format "yyyyMMddHHmmss")
$CONTAINER_APP_NAME = "content-understanding-app"
$ENVIRONMENT_NAME = "content-understanding-env"

Write-Host "`n=== Azure Container App Deployment (ACR Build) ===" -ForegroundColor Cyan
Write-Host "Resource Group: $RESOURCE_GROUP"
Write-Host "ACR: $ACR_NAME"
Write-Host "Image Tag: $IMAGE_TAG"
Write-Host ""

# Step 1: Build image in ACR (no local Docker needed)
Write-Host "Step 1: Building image in ACR..." -ForegroundColor Yellow
$ACR_SERVER = "${ACR_NAME}.azurecr.io"
$FULL_IMAGE_NAME = "${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"

Write-Host "  Building: $FULL_IMAGE_NAME"
az acr build `
    --registry $ACR_NAME `
    --image "${IMAGE_NAME}:${IMAGE_TAG}" `
    --image "${IMAGE_NAME}:latest" `
    --file Dockerfile `
    .

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ ACR build failed" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Image built in ACR" -ForegroundColor Green

# Step 2: Load environment variables
Write-Host "`nStep 2: Loading environment variables..." -ForegroundColor Yellow
$envVars = @{}
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        $envVars[$matches[1].Trim()] = $matches[2].Trim()
    }
}
Write-Host "  ✓ Loaded $($envVars.Count) variables" -ForegroundColor Green

# Step 3: Create Container Apps Environment
Write-Host "`nStep 3: Checking Container Apps Environment..." -ForegroundColor Yellow
$envExists = az containerapp env show --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP 2>$null
if (!$envExists) {
    Write-Host "  Creating environment..." -ForegroundColor Cyan
    az containerapp env create `
        --name $ENVIRONMENT_NAME `
        --resource-group $RESOURCE_GROUP `
        --location $LOCATION
    Write-Host "  ✓ Environment created" -ForegroundColor Green
} else {
    Write-Host "  ✓ Environment exists" -ForegroundColor Green
}

# Step 4: Get ACR credentials
Write-Host "`nStep 4: Getting ACR credentials..." -ForegroundColor Yellow
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query "username" -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv
Write-Host "  ✓ Credentials retrieved" -ForegroundColor Green

# Step 5: Deploy Container App
Write-Host "`nStep 5: Deploying Container App..." -ForegroundColor Yellow
$appExists = az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP 2>$null

$envArgs = @(
    "PROJECT_ENDPOINT=$($envVars['PROJECT_ENDPOINT'])",
    "MODEL_DEPLOYMENT_NAME=$($envVars['MODEL_DEPLOYMENT_NAME'])",
    "FUNCTION_APP_URL=$($envVars['FUNCTION_APP_URL'])",
    "STORAGE_ACCOUNT_NAME=$($envVars['STORAGE_ACCOUNT_NAME'])",
    "CLASSIFIER_ID=$($envVars.CLASSIFIER_ID)"
)

if (!$appExists) {
    Write-Host "  Creating new container app..." -ForegroundColor Cyan
    az containerapp create `
        --name $CONTAINER_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --environment $ENVIRONMENT_NAME `
        --image $FULL_IMAGE_NAME `
        --registry-server $ACR_SERVER `
        --registry-username $ACR_USERNAME `
        --registry-password $ACR_PASSWORD `
        --target-port 8501 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 3 `
        --cpu 1.0 `
        --memory 2Gi `
        --env-vars $envArgs
} else {
    Write-Host "  Updating existing container app..." -ForegroundColor Cyan
    az containerapp update `
        --name $CONTAINER_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --image $FULL_IMAGE_NAME `
        --set-env-vars $envArgs
}

Write-Host "  ✓ Container app deployed" -ForegroundColor Green

# Step 6: Get app URL
Write-Host "`nStep 6: Getting app URL..." -ForegroundColor Yellow
$APP_URL = az containerapp show `
    --name $CONTAINER_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --query "properties.configuration.ingress.fqdn" -o tsv

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""
Write-Host "App URL: https://$APP_URL" -ForegroundColor Cyan
Write-Host "Image: $FULL_IMAGE_NAME" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow" -ForegroundColor Gray
Write-Host ""
