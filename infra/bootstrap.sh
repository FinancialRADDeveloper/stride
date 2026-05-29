#!/bin/bash
# bootstrap.sh
#
# One-shot AWS setup for Stride. Run this ONCE from a machine with the
# AWS CLI configured (or from AWS CloudShell).
#
# What it does:
#   1. Deploys the CloudFormation bootstrap stack (ECR, S3, IAM, OIDC)
#   2. Prints exactly which GitHub secrets to set
#
# Prerequisites:
#   - AWS CLI v2 installed and configured (aws configure) or run in CloudShell
#   - IAM user/role with permissions to create: ECR, S3, IAM, CloudFormation
#
set -euo pipefail

ACCOUNT_ID="138532987568"
REGION="eu-west-2"
STACK_NAME="stride-bootstrap"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║       Stride — AWS Bootstrap           ║"
echo "╠════════════════════════════════════════╣"
echo "║  Account : ${ACCOUNT_ID}              ║"
echo "║  Region  : ${REGION}               ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Sanity-check: AWS CLI configured and pointing at the right account
CALLER_ACCOUNT=$(aws sts get-caller-identity --query "Account" --output text 2>/dev/null || echo "")
if [ -z "${CALLER_ACCOUNT}" ]; then
  echo "ERROR: AWS CLI is not configured. Run 'aws configure' or open AWS CloudShell."
  exit 1
fi
if [ "${CALLER_ACCOUNT}" != "${ACCOUNT_ID}" ]; then
  echo "ERROR: AWS CLI is configured for account ${CALLER_ACCOUNT}, expected ${ACCOUNT_ID}."
  echo "       Check your credentials / profile."
  exit 1
fi

echo "✓  Authenticated as account ${CALLER_ACCOUNT}"
echo ""
echo "Deploying CloudFormation stack '${STACK_NAME}' ..."
echo "(This takes ~60 seconds on first run.)"
echo ""

aws cloudformation deploy \
  --template-file "${SCRIPT_DIR}/bootstrap.cfn.yaml" \
  --stack-name "${STACK_NAME}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "${REGION}" \
  --no-fail-on-empty-changeset

echo ""
echo "✓  Stack deployed."
echo ""

# Print outputs for reference
echo "Stack outputs:"
aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" \
  --output table

echo ""
echo "════════════════════════════════════════════════"
echo "  Next: set these GitHub Actions secrets        "
echo "  (repo Settings → Secrets → Actions)          "
echo "════════════════════════════════════════════════"
echo ""
echo "  Name               Value"
echo "  ──────────────────────────────────────────────"
echo "  AWS_ACCOUNT_ID     ${ACCOUNT_ID}"
echo ""
echo "  STRIDE_SECRET_UAT  (generate one:)"
echo "     python3 -c \"import secrets; print(secrets.token_hex(32))\""
echo ""
echo "  STRIDE_SECRET_PROD (generate a DIFFERENT one:)"
echo "     python3 -c \"import secrets; print(secrets.token_hex(32))\""
echo ""
echo "════════════════════════════════════════════════"
echo "  Then: create a GitHub environment 'production'"
echo "  (repo Settings → Environments → New)          "
echo "  Add yourself as a required reviewer.          "
echo "════════════════════════════════════════════════"
echo ""
echo "  Finally: push to main — the pipeline takes it from there."
echo ""
