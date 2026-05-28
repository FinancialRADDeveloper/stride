#!/bin/bash
# wait-for-service.sh
#
# Polls an App Runner service until it reaches RUNNING status (or fails).
# App Runner has no native CLI waiter, so we poll on a 15-second interval.
#
# Usage: ./infra/wait-for-service.sh <service-arn> [timeout-seconds]
#
set -euo pipefail

SERVICE_ARN="${1:?service ARN required}"
MAX_WAIT="${2:-600}"    # default 10 minutes
INTERVAL=15
REGION="${AWS_DEFAULT_REGION:-eu-west-2}"

ELAPSED=0
echo "Waiting for ${SERVICE_ARN} to reach RUNNING (timeout: ${MAX_WAIT}s) ..."

while [ "${ELAPSED}" -lt "${MAX_WAIT}" ]; do
  STATUS=$(
    aws apprunner describe-service \
      --region "${REGION}" \
      --service-arn "${SERVICE_ARN}" \
      --query "Service.Status" \
      --output text
  )

  echo "  [${ELAPSED}s] Status: ${STATUS}"

  case "${STATUS}" in
    RUNNING)
      # Also print the service URL so it appears in the Actions log
      URL=$(
        aws apprunner describe-service \
          --region "${REGION}" \
          --service-arn "${SERVICE_ARN}" \
          --query "Service.ServiceUrl" \
          --output text
      )
      echo "Service is RUNNING at https://${URL}"
      exit 0
      ;;
    CREATE_FAILED|UPDATE_FAILED|DELETE_FAILED|OPERATION_IN_PROGRESS)
      if [ "${STATUS}" != "OPERATION_IN_PROGRESS" ]; then
        echo "ERROR: Service entered terminal failure state: ${STATUS}"
        exit 1
      fi
      ;;
  esac

  sleep "${INTERVAL}"
  ELAPSED=$(( ELAPSED + INTERVAL ))
done

echo "ERROR: Timed out after ${MAX_WAIT}s waiting for service to be RUNNING"
exit 1
