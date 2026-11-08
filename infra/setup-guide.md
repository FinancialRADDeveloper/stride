# Stride AWS Setup Guide

One-time steps to go from zero to a live UAT + Prod pipeline.
Run these in order. Each step ends with something you paste into GitHub Secrets or the next command.

---

## Prerequisites

- AWS CLI installed and authenticated to the `stride-root` account (`138532987568`, `eu-west-2`)
- GitHub repo: `FinancialRADDeveloper/stride`

```bash
aws configure  # set region = eu-west-2
aws sts get-caller-identity  # confirm you're in the right account
```

---

## Step 1 — Deploy the Bootstrap CloudFormation Stack

This creates ECR, S3, GitHub OIDC provider, and all four IAM roles in one shot.

```bash
aws cloudformation deploy \
  --template-file infra/bootstrap.cfn.yaml \
  --stack-name stride-bootstrap \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-west-2
```

After it completes, grab the outputs — you'll need them in later steps:

```bash
aws cloudformation describe-stacks \
  --stack-name stride-bootstrap \
  --region eu-west-2 \
  --query "Stacks[0].Outputs" \
  --output table
```

Note down:
- `EcrRepositoryUri` — e.g. `138532987568.dkr.ecr.eu-west-2.amazonaws.com/stride`
- `LitestreamBucketName` — e.g. `stride-db-138532987568`
- `AppRunnerInstanceRoleArn`
- `AppRunnerAccessRoleArn`

---

## Step 2 — Push the First Image Manually

The App Runner services need an image to exist in ECR before they can be created.
Trigger CI by merging this PR — or push an image manually:

```bash
aws ecr get-login-password --region eu-west-2 \
  | docker login --username AWS \
    --password-stdin 138532987568.dkr.ecr.eu-west-2.amazonaws.com

docker build -t stride .
docker tag stride:latest 138532987568.dkr.ecr.eu-west-2.amazonaws.com/stride:latest
docker push 138532987568.dkr.ecr.eu-west-2.amazonaws.com/stride:latest
```

---

## Step 3 — Create the App Runner Services

Create UAT and Prod services pointing at the ECR image.
Replace the ARN values from Step 1 as indicated.

```bash
# UAT
aws apprunner create-service \
  --service-name stride-uat \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "138532987568.dkr.ecr.eu-west-2.amazonaws.com/stride:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8050",
        "RuntimeEnvironmentVariables": {
          "DATA_DIR": "/data",
          "LITESTREAM_REPLICA_URL": "s3://stride-db-138532987568/uat"
        }
      }
    },
    "AuthenticationConfiguration": {
      "AccessRoleArn": "<AppRunnerAccessRoleArn from Step 1>"
    },
    "AutoDeploymentsEnabled": false
  }' \
  --instance-configuration '{
    "Cpu": "0.25 vCPU",
    "Memory": "0.5 GB",
    "InstanceRoleArn": "<AppRunnerInstanceRoleArn from Step 1>"
  }' \
  --region eu-west-2

# Prod (same, but different replica path)
aws apprunner create-service \
  --service-name stride-prod \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "138532987568.dkr.ecr.eu-west-2.amazonaws.com/stride:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8050",
        "RuntimeEnvironmentVariables": {
          "DATA_DIR": "/data",
          "LITESTREAM_REPLICA_URL": "s3://stride-db-138532987568/prod"
        }
      }
    },
    "AuthenticationConfiguration": {
      "AccessRoleArn": "<AppRunnerAccessRoleArn from Step 1>"
    },
    "AutoDeploymentsEnabled": false
  }' \
  --instance-configuration '{
    "Cpu": "0.25 vCPU",
    "Memory": "0.5 GB",
    "InstanceRoleArn": "<AppRunnerInstanceRoleArn from Step 1>"
  }' \
  --region eu-west-2
```

After both are created (status will show RUNNING in a couple of minutes), get their ARNs:

```bash
aws apprunner list-services --region eu-west-2 --query "ServiceSummaryList[*].[ServiceName,ServiceArn]" --output table
```

---

## Step 4 — Add GitHub Secrets

In the GitHub repo → Settings → Secrets and variables → Actions, add:

| Secret name | Value |
|---|---|
| `UAT_SERVICE_ARN` | ARN of `stride-uat` from the list above |
| `PROD_SERVICE_ARN` | ARN of `stride-prod` from the list above |
| `STRIDE_SECRET` | A random 32-character secret — `python -c "import secrets; print(secrets.token_hex(32))"` |

---

## Step 5 — Set STRIDE_SECRET on the App Runner Services

The Flask session secret must be set as an environment variable on each service.
Do this via the AWS Console (App Runner → service → Configuration → Environment variables)
or via CLI:

```bash
# Get the current source configuration first, then update with the secret added
# Easiest to do this in the Console: App Runner → stride-uat → Configuration → Update
```

---

## Step 6 — Add GitHub Environments for Approval Gate

In the GitHub repo → Settings → Environments:

1. Create environment `uat` — no protection rules needed
2. Create environment `production` — add Required reviewers (yourself)

The deploy workflow pauses at the `production` environment and emails you to approve before Prod is updated.

---

## Step 7 — Seed Your User Account

Once Prod is running, exec into the container to create your account.
App Runner doesn't support exec — use the CLI against the running app instead:

```bash
# Find the Prod service URL
aws apprunner describe-service \
  --service-arn "<PROD_SERVICE_ARN>" \
  --region eu-west-2 \
  --query "Service.ServiceUrl" --output text
```

Then run `create-user` locally against the production database URL — or temporarily
run the Docker image locally with the production S3 replica URL to restore the DB,
seed the user, and let Litestream replicate the new user record back to S3:

```bash
docker run --rm -it \
  -e LITESTREAM_REPLICA_URL=s3://stride-db-138532987568/prod \
  -e DATA_DIR=/data \
  -e STRIDE_SECRET=<your-secret> \
  138532987568.dkr.ecr.eu-west-2.amazonaws.com/stride:latest \
  python -m stride create-user \
    --email financialraddeveloper@gmail.com \
    --name Alan
```

---

## Step 8 — Point DNS

In Namecheap for `takeitinyourstride.com`:

1. Go to App Runner Prod service → Custom domains → Link domain
2. Follow the CNAME records it shows you — add them in Namecheap
3. Wait for verification (usually 5–30 minutes)

---

## Ongoing — Every PR merge

1. CI builds and pushes `sha-<sha>` + `latest` to ECR
2. Deploy workflow auto-deploys to UAT
3. GitHub emails you: approve to promote to Prod
4. Click Approve → Prod updates to the same SHA

No manual Docker commands needed after initial setup.
