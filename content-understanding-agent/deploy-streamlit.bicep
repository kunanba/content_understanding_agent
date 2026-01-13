// Parameters
@description('The location for all resources')
param location string = resourceGroup().location

@description('Environment name for resource naming')
param environmentName string

@description('Container image name')
param containerImage string

@description('Container registry server')
param containerRegistryServer string = ''

@description('Container registry username')
@secure()
param containerRegistryUsername string = ''

@description('Container registry password')
@secure()
param containerRegistryPassword string = ''

@description('AI Project endpoint')
@secure()
param projectEndpoint string

@description('Model deployment name')
param modelDeploymentName string = 'gpt-4o'

@description('Storage account name')
param storageAccountName string

@description('Function App URL')
param functionAppUrl string

@description('Minimum replicas')
@minValue(0)
@maxValue(30)
param minReplicas int = 1

@description('Maximum replicas')
@minValue(1)
@maxValue(30)
param maxReplicas int = 3

// Variables
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = {
  'azd-env-name': environmentName
  application: 'content-understanding-agent'
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-${environmentName}-${resourceToken}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Apps Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-${environmentName}-${resourceToken}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-streamlit-${resourceToken}'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: empty(containerRegistryServer) ? [] : [
        {
          server: containerRegistryServer
          username: containerRegistryUsername
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: concat(
        empty(containerRegistryPassword) ? [] : [
          {
            name: 'registry-password'
            value: containerRegistryPassword
          }
        ],
        [
          {
            name: 'project-endpoint'
            value: projectEndpoint
          }
        ]
      )
    }
    template: {
      containers: [
        {
          name: 'streamlit-app'
          image: containerImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'PROJECT_ENDPOINT'
              secretRef: 'project-endpoint'
            }
            {
              name: 'MODEL_DEPLOYMENT_NAME'
              value: modelDeploymentName
            }
            {
              name: 'STORAGE_ACCOUNT_NAME'
              value: storageAccountName
            }
            {
              name: 'FUNCTION_APP_URL'
              value: functionAppUrl
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output containerAppName string = containerApp.name
output containerAppId string = containerApp.id
output containerAppPrincipalId string = containerApp.identity.principalId
output logAnalyticsWorkspaceId string = logAnalytics.id
output environmentId string = containerAppEnvironment.id
