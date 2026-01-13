# Deploy Streamlit App to Azure Container Apps

This guide walks you through deploying the Content Understanding Agent Streamlit app to Azure Container Apps.

## ✅ Deployment Status

**Current Deployment:**
- **URL:** https://content-understanding-app.yellowgrass-86772be9.westus.azurecontainerapps.io
- **Resource Group:** demo-ak
- **Location:** West US
- **Container Registry:** acrcu2220.azurecr.io
- **Image:** streamlit-app:latest
- **Managed Identity:** Enabled with Storage Blob Data Contributor & Cognitive Services User roles

## Prerequisites

1. **Azure CLI** installed and logged in
2. **Azure Container Registry** (Docker Desktop NOT required - using ACR Build)
3. **Azure subscription** with appropriate permissions

## Quick Redeploy (Existing Setup)

If you've already deployed once and just need to update the app code:

```powershell
cd 'c:\Users\akunanbaeva\OneDrive - Microsoft\Content Understanding Agent\content-understanding-agent'

# Build new image with timestamp tag using ACR Build (no local Docker needed)
$IMAGE_TAG = (Get-Date -Format 'yyyyMMddHHmmss')
az acr build `
  --registry acrcu2220 `
  --image "streamlit-app:$IMAGE_TAG" `
  --image "streamlit-app:latest" `
  --file Dockerfile .

# Update container app with new image
az containerapp update `
  --name content-understanding-app `
  --resource-group demo-ak `
  --image "acrcu2220.azurecr.io/streamlit-app:$IMAGE_TAG"
```

## Quick Start (Fresh Deployment)

### 1. Set Environment Variables

```powershell
$RESOURCE_GROUP = "demo-ak"
$LOCATION = "westus"
$ENVIRONMENT_NAME = "content-understanding-env"
$ACR_NAME = "acrcu2220"  # Must be globally unique, alphanumeric only
$IMAGE_NAME = "streamlit-app"
$CONTAINER_APP_NAME = "content-understanding-app"
```

### 2. Create Resource Group (if needed)

```powershell
# Skip if using existing resource group
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### 3. Create Azure Container Registry

```powershell
az acr create `
  --resource-group $RESOURCE_GROUP `
  --name $ACR_NAME `
  --sku Basic `
  --admin-enabled true `
  --location $LOCATION

# Get ACR credentials
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query "username" -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv
$ACR_SERVER = "${ACR_NAME}.azurecr.io"
```

### 4. Build Image Using ACR Build (No Docker Desktop Required)

```powershell
# Navigate to the app directory
cd content-understanding-agent

# Build using ACR Build - this happens in Azure, not locally
$IMAGE_TAG = (Get-Date -Format 'yyyyMMddHHmmss')
az acr build `
  --registry $ACR_NAME `
  --image "${IMAGE_NAME}:${IMAGE_TAG}" `
  --image "${IMAGE_NAME}:latest" `
  --file Dockerfile .
```

### 5. Create Container Apps Environment

```powershell
az containerapp env create `
  --name $ENVIRONMENT_NAME `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION
```

### 6. Deploy Container App

```powershell
# Load environment variables from .env file
$envVars = @(
  "PROJECT_ENDPOINT=$(Get-Content .env | Select-String 'PROJECT_ENDPOINT' | ForEach-Object { $_.ToString().Split('=')[1] })",
  "MODEL_DEPLOYMENT_NAME=gpt-4.1",
  "FUNCTION_APP_URL=https://func-content-understanding-2220.azurewebsites.net/api",
  "STORAGE_ACCOUNT_NAME=demostorageak",
  "CLASSIFIER_ID=prebuilt-documentAnalyzer"
)

az containerapp create `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $ENVIRONMENT_NAME `
  --image "${ACR_SERVER}/${IMAGE_NAME}:latest" `
  --registry-server $ACR_SERVER `
  --registry-username $ACR_USERNAME `
  --registry-password $ACR_PASSWORD `
  --target-port 8000 `
  --ingress external `
  --min-replicas 0 `
  --max-replicas 1 `
  --cpu 1.0 `
  --memory 2Gi `
  --env-vars $envVars
```

### 7. Enable Managed Identity & Grant Permissions

```powershell
# Enable system-assigned managed identity
$identity = az containerapp identity assign `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --system-assigned `
  --query "principalId" -o tsv

# Grant Storage Blob Data Contributor role
$storageId = az storage account show `
  --name demostorageak `
  --resource-group $RESOURCE_GROUP `
  --query id -o tsv

az role assignment create `
  --assignee $identity `
  --role "Storage Blob Data Contributor" `
  --scope $storageId

# Grant Cognitive Services User role
$cognitiveId = az cognitiveservices account show `
  --name ak-content-understand-resource `
  --resource-group $RESOURCE_GROUP `
  --query id -o tsv

az role assignment create `
  --assignee $identity `
  --role "Cognitive Services User" `
  --scope $cognitiveId

# Restart to apply identity
az containerapp revision restart `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --revision $(az containerapp revision list `
    --name $CONTAINER_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --query '[0].name' -o tsv)
```

### 8. Get the Application URL

```powershell
$CONTAINER_APP_URL = az deployment group show `
  --resource-group $RESOURCE_GROUP `
  --name deploy-streamlit `
```powershell
$APP_URL = az containerapp show `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "properties.configuration.ingress.fqdn" -o tsv

Write-Host "`n✅ Deployment Complete!"
Write-Host "Application URL: https://$APP_URL"
```

## Troubleshooting

### Check Container App Logs

```powershell
az containerapp logs show `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --tail 50
```

### Fix Port Mismatch

If the app runs on port 8000 but ingress is configured for 8501:

```powershell
az containerapp ingress update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --target-port 8000
```

### View Current Configuration

```powershell
az containerapp show `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "properties.template" -o json
```

## Performance Optimizations

### Azure OpenAI Rate Limiting

The app includes:
- **Response caching** - Duplicate queries return cached results
- **Retry logic with exponential backoff** - Auto-retries on rate limit errors
- **User-friendly error messages** - Shows wait times and quota increase links

To increase quota: https://aka.ms/oai/quotaincrease

### Scaling Configuration

Current setup uses 0-1 replicas:
- Scales to zero when idle (saves costs)
- Single replica prevents concurrent quota consumption
- Adjust if needed:

```powershell
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --min-replicas 1 `
  --max-replicas 3
```

## Environment Variables

Required variables in `.env` file:
- `PROJECT_ENDPOINT` - Azure AI Foundry project endpoint
- `MODEL_DEPLOYMENT_NAME` - Azure OpenAI model deployment (e.g., gpt-4.1)
- `FUNCTION_APP_URL` - Azure Functions endpoint
- `STORAGE_ACCOUNT_NAME` - Azure Storage account name
- `CLASSIFIER_ID` - Document analyzer ID (e.g., prebuilt-documentAnalyzer)

## Alternative: Using Bicep Template
az containerapp create `
  --name ca-streamlit-app `
  --resource-group $RESOURCE_GROUP `
  --environment cae-content-understanding `
  --image ${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG} `
  --registry-server $ACR_SERVER `
  --registry-username $ACR_USERNAME `
  --registry-password $ACR_PASSWORD `
  --target-port 8000 `
  --ingress external `
  --cpu 1.0 `
  --memory 2Gi `
  --min-replicas 1 `
  --max-replicas 3 `
  --env-vars `
    "PROJECT_ENDPOINT=secretref:project-endpoint" `
    "MODEL_DEPLOYMENT_NAME=gpt-4o" `
    "STORAGE_ACCOUNT_NAME=YOUR_STORAGE_ACCOUNT" `
    "FUNCTION_APP_URL=https://func-content-understanding-2220.azurewebsites.net/api" `
  --secrets `
    "project-endpoint=YOUR_PROJECT_ENDPOINT"

# Get the app URL
az containerapp show `
  --name ca-streamlit-app `
  --resource-group $RESOURCE_GROUP `
  --query properties.configuration.ingress.fqdn `
  -o tsv
```

## Configure Managed Identity Access

After deployment, grant the Container App's managed identity access to required Azure resources:

```powershell
# Get the Container App's principal ID
$PRINCIPAL_ID = az containerapp show `
  --name ca-streamlit-app `
  --resource-group $RESOURCE_GROUP `
  --query identity.principalId `
  -o tsv

# Grant Storage Blob Data Contributor role
az role assignment create `
  --assignee $PRINCIPAL_ID `
  --role "Storage Blob Data Contributor" `
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/YOUR_STORAGE_ACCOUNT"

# Grant Cognitive Services User role (for AI services)
az role assignment create `
  --assignee $PRINCIPAL_ID `
  --role "Cognitive Services User" `
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"
```

## Update the Application

To deploy updates:

```powershell
# Build and push new image
docker build -t ${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG} .
docker push ${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}

# Update the container app
az containerapp update `
  --name ca-streamlit-app `
  --resource-group $RESOURCE_GROUP `
  --image ${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}
```

## Monitor the Application

```powershell
# View logs
az containerapp logs show `
  --name ca-streamlit-app `
  --resource-group $RESOURCE_GROUP `
  --follow

# View replica status
az containerapp replica list `
  --name ca-streamlit-app `
  --resource-group $RESOURCE_GROUP `
  --output table
```

## Troubleshooting

### Check Container Logs
```powershell
az containerapp logs show `
  --name ca-streamlit-app `
  --resource-group $RESOURCE_GROUP `
  --tail 100
```

### Check Revision Status
```powershell
az containerapp revision list `
  --name ca-streamlit-app `
  --resource-group $RESOURCE_GROUP `
  --output table
```

### Test Locally First
```powershell
cd content-understanding-agent
docker build -t streamlit-test .
docker run -p 8000:8000 `
  -e PROJECT_ENDPOINT="your-endpoint" `
  -e STORAGE_ACCOUNT_NAME="your-storage" `
  streamlit-test
```

Then visit http://localhost:8000

## Cost Optimization

- Set `minReplicas` to 0 for dev/test environments (will scale to zero when idle)
- Use consumption-based pricing for Container Apps
- Consider using Azure Container Registry Basic tier for development

## Security Best Practices

1. **Use Managed Identity** instead of connection strings where possible
2. **Store secrets** in Azure Key Vault and reference them in Container App
3. **Enable HTTPS only** (already configured in Bicep template)
4. **Restrict ingress** to specific IP ranges if needed
5. **Use private networking** for production workloads

## Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
