#!/bin/bash
# apprunner-deploy.sh
#
# Creates an App Runner service if it doesn't exist, or triggers a new
# deployment if it does. Called by the GitHub Actions deploy workflow.
#
# Usage: ./infra/apprunner-deploy.sh <service-name> <account-id> <image-tag>
#
# Examples:
#   ./infra/apprunner-deploy.sh stride-uat  138532987568 sha-abc1234
#   ./infra/apprunner-deploy.sh stride-prod 138532987568 sha-abc1234
#
set -euo pipefail

SERVICE_NAME="${1:?service name required}"
ACCOUNT_ID="${2:?account ID required}"
IMAGE_TAG="${3:-latest}"
REGION="${AWS_DEFAULT_REGION:-eu-west-2}"

# Derive environment name (uat or prod) from service name
ENV_NAME="${SERVICE_NAME#stride-}"   # strip leading "stride-"

IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/stride:${IMAGE_TAG}"

ACCESS_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/stride-apprunner-access-role"
INSTANCE_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/stride-apprunner-instance-role"
LITESTREAM_URL="s3://stride-db-${ACCOUNT_ID}/${ENV_NAME}/stride.db"

# Resolve which secret env var to use (STRIDE_SECRET_UAT or STRIDE_SECRET_PROD)
SECRET_VAR="STRIDE_SECRET_$(echo "${ENV_NAME}" | tr '[:lower:]' '[:upper:]')"
STRIDE_SECRET="${!SECRET_VAR:-}"
if [ -z "${STRIDE_SECRET}" ]; then
  echo "WARNING: ${SECRET_VAR} is not set — using placeholder. Set it as a GitHub secret."
  STRIDE_SECRET="please-set-${SECRET_VAR}-in-github-secrets"
fi

echo "=== Deploying ${SERVICE_NAME} ==="
echo "Image:   ${IMAGE_URI}"
echo "Replica: ${LITESTREAM_URL}"

# Check whether the service already exists
SERVICE_ARN=$(
  aws apprunner list-services \
    --region "${REGION}" \
    --query "ServiceSummaryList[?ServiceName=='${SERVICE_NAME}'].ServiceArn | [0]" \
    --output text 2>/dev/null || true
)

if [ -z "${SERVICE_ARN}" ] || [ "${SERVICE_ARN}" = "None" ]; then
  # -----------------------------------------------------------------------
  # First deploy — create the service
  # -----------------------------------------------------------------------
  echo "Service does not exist — creating ..."

  SERVICE_ARN=$(
    aws apprunner create-service \
      --region "${REGION}" \
      --service-name "${SERVICE_NAME}" \
      --source-configuration "{
        \"AuthenticationConfiguration\": {
          \"AccessRoleArn\": \"${ACCESS_ROLE_ARN}\"
        },
        \"AutoDeploymentsEnabled\": false,
        \"ImageRepository\": {
          \"ImageIdentifier\": \"${IMAGE_URI}\",
          \"ImageRepositoryType\": \"ECR\",
          \"ImageConfiguration\": {
            \"Port\": \"8050\",
            \"RuntimeEnvironmentVariables\": {
              \"DATA_DIR\": \"/data\",
              \"LITESTREAM_REPLICA_URL\": \"${LITESTREAM_URL}\",
              \"STRIDE_SECRET\": \"${STRIDE_SECRET}\",
              \"STRIDE_DEBUG\": \"false\"
            }
          }
        }
      }" \
      --instance-configuration "{
        \"Cpu\": \"512\",
        \"Memory\": \"1024\",
        \"InstanceRoleArn\": \"${INSTANCE_ROLE_ARN}\"
      }" \
      --health-check-configuration "{
        \"Protocol\": \"HTTP\",
        \"Path\": \"/health\",
        \"Interval\": 20,
        \"Timeout\": 5,
        \"HealthyThreshold\": 1,
        \"UnhealthyThreshold\": 5
      }" \
      --query "Service.ServiceArn" \
      --output text
  )
  echo "Created: ${SERVICE_ARN}"
else
  # -----------------------------------------------------------------------
  # Subsequent deploys — update image tag then start deployment
  # -----------------------------------------------------------------------
  echo "Service exists (${SERVICE_ARN}) — updating image and deploying ..."

  aws apprunner update-service \
    --region "${REGION}" \
    --service-arn "${SERVICE_ARN}" \
    --source-configuration "{
      \"AuthenticationConfiguration\": {
        \"AccessRoleArn\": \"${ACCESS_ROLE_ARN}\"
      },
      \"AutoDeploymentsEnabled\": false,
      \"ImageRepository\": {
        \"ImageIdentifier\": \"${IMAGE_URI}\",
        \"ImageRepositoryType\": \"ECR\",
        \"ImageConfiguration\": {
          \"Port\": \"8050\",
          \"RuntimeEnvironmentVariables\": {
            \"DATA_DIR\": \"/data\",
            \"LITESTREAM_REPLICA_URL\": \"${LITESTREAM_URL}\",
            \"STRIDE_SECRET\": \"${STRIDE_SECRET}\",
            \"STRIDE_DEBUG\": \"false\"
          }
        }
      }
    }" > /dev/null

  echo "Image updated."
fi

# Emit the ARN so the caller can wait on it
echo "SERVICE_ARN=${SERVICE_ARN}"
echo "${SERVICE_ARN}" > /tmp/service-arn.txt
