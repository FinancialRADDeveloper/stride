# Why We Chose Litestream over EFS for SQLite Persistence on AWS App Runner — and What That Tells You About MVP Infrastructure Decisions

Every hosted product reaches the moment when local development is no longer enough. You want it running somewhere real, accessible from any device, surviving reboots. For Stride — a personal task board built in Python/Dash with SQLite — that moment arrived after the mobile sprint. The board worked well on my laptop. I wanted it working on my phone, from anywhere, with no data loss on container restarts.

The infrastructure decisions I made in this phase are not the ones a platform team would make for a multi-tenant SaaS. They are the right decisions for a single-user MVP that needs to be demonstrably production-grade without becoming a maintenance burden. Understanding why requires being honest about where I drew the line and what I deferred.

---

## What We Built

The deployment pipeline runs across six commits and four AWS services:

1. A CloudFormation bootstrap stack (`infra/bootstrap.cfn.yaml`) that provisions all persistent infrastructure in one atomic deploy: an ECR container registry, an S3 bucket for database replication, a GitHub OIDC provider, and three IAM roles.
2. A `docker-entrypoint.sh` that wraps the container startup — restoring the SQLite database from S3 on cold start, then running the app under Litestream replication in production, and doing nothing extra in local development.
3. A CI workflow (`ci.yml`) that builds and pushes a Docker image to ECR on every main branch merge, tagging each image with both `latest` and `sha-<commit>`.
4. A deploy workflow (`deploy.yml`) that automatically deploys the exact commit SHA to a UAT environment, then pauses for manual approval before promoting that same SHA to production.

The result is a fully automated pipeline where a PR merge triggers build, UAT deploy, and a one-click production promotion — with no long-lived AWS credentials stored anywhere.

---

## The Key Architectural Decisions

### Litestream Instead of EFS

The obvious way to persist a SQLite file across App Runner deployments is EFS — Amazon's managed NFS file system. It mounts into containers as a regular filesystem path and your app writes to it as if it were local disk.

The problem is the operational cost. EFS requires a VPC. A VPC on App Runner requires a VPC connector. A VPC connector requires subnet IDs, security group IDs, and an understanding of your CIDR blocks. For a single-user application where the database is one person's task list, this is infrastructure archaeology that adds no user value.

Litestream is a different model. It is a lightweight binary that intercepts SQLite's write-ahead log (WAL) and streams every frame to S3 in near real time. The `docker-entrypoint.sh` does two things on production startup:

```sh
litestream restore \
  -if-replica-exists \
  -o "${DATA_DIR}/stride.db" \
  "${LITESTREAM_REPLICA_URL}"

exec litestream replicate \
  -exec "uv run stride" \
  "${DATA_DIR}/stride.db" \
  "${LITESTREAM_REPLICA_URL}"
```

On cold start, it restores the database from S3 if a replica exists (the `-if-replica-exists` flag means the first boot is a no-op rather than an error). Then it runs the app as a subprocess under `litestream replicate`, which streams writes to S3 as they happen.

Zero VPC configuration. No EFS mount. No subnet planning. The S3 bucket (`stride-db-<account-id>`) is provisioned by the CloudFormation stack with versioning enabled and a 14-day lifecycle policy on old versions — effectively two weeks of point-in-time recovery.

The cold-start restore adds roughly one to two seconds on first boot. For a personal tool, this is invisible. For a high-traffic service, it would matter more.

### OIDC Instead of IAM Access Keys

The conventional way to give GitHub Actions permission to push to ECR and deploy to App Runner is to create an IAM user, generate access keys, and store them in GitHub Secrets. This works. It is also a permanent credential that, if leaked, gives an attacker access to your AWS account until you notice and rotate it.

OIDC is different. GitHub mints a short-lived JWT for each workflow run. AWS IAM validates the JWT against the registered OIDC provider and issues a temporary session token that expires when the job ends. No long-lived secret is ever stored anywhere. The trust relationship in IAM is scoped to a specific repository:

```yaml
# bootstrap.cfn.yaml
Condition:
  StringLike:
    token.actions.githubusercontent.com:sub:
      - repo:FinancialRADDeveloper/stride:*
```

This means even if someone forked the repository, they could not assume the role. The entire OIDC provider and trust relationship is created by the CloudFormation stack — it runs once, and the GitHub Actions workflow just uses the role ARN from that point on.

### App Runner Instead of ECS/Fargate

App Runner is opinionated managed compute. You give it a container image and it handles TLS, load balancing, scaling, and health checks. There is no cluster to manage, no task definition JSON to maintain, no service discovery configuration.

The trade-off is control. You cannot customise the VPC routing (which is exactly why EFS is awkward), you cannot run scheduled tasks alongside the web process, and the minimum billing unit is higher than a t4g.nano EC2 instance. For a single-user web application that mostly sits idle, scale-to-zero behaviour keeps the bill reasonable.

The deploy scripts (`infra/apprunner-deploy.sh`, `infra/wait-for-service.sh`) handle the create-or-deploy logic — if the service does not exist yet, they create it; if it does, they update the image tag. This means the first push works cleanly without needing a manual console step.

### SHA-Tagged Images

Every ECR image gets two tags: `latest` and `sha-<commit>`. The deploy workflow always references the SHA, not `latest`:

```yaml
run: |
  ./infra/apprunner-deploy.sh \
    stride-uat \
    ${{ secrets.AWS_ACCOUNT_ID }} \
    sha-${{ github.event.workflow_run.head_sha }}
```

This means production always runs exactly the image that passed UAT — not whatever `latest` was when the deployment triggered. If a second commit merges while the first is still waiting for production approval, the approval promotes the correct SHA, not the newer one that may not have been reviewed yet.

---

## The Trade-offs, Honestly

SQLite is a single-writer database. That is fine for one user, and it is fine for App Runner's single-instance model. The moment Stride becomes multi-user or needs horizontal scaling, SQLite becomes the wrong choice and Litestream becomes moot — you would migrate to Postgres (Aurora Serverless or RDS). That migration is acknowledged in the product vision and deferred deliberately.

App Runner auto-deploy is disabled on both services. The deploy workflow controls every deployment explicitly. This is correct — you want traceability over automation — but it does mean a deployment is never completely hands-free. You still need to approve production.

The CloudFormation stack has `DeletionPolicy: Retain` on the S3 bucket. If you ever tear down the stack, the bucket stays — by design, because it contains your data. This means you cannot just delete the stack and start clean without also manually deleting the bucket. Operational debt you accept knowingly.

---

## What the AI-Assisted Workflow Actually Looked Like

The six commits in this feature branch are: bootstrap CloudFormation stack, deploy scripts, Litestream entrypoint, Dockerfile update for the binary, CI ECR push workflow, and deploy workflow. Each is independently reviewable. The CloudFormation template is 230 lines that provision six resources with their dependencies and outputs. The deploy workflow is 117 lines with a clear UAT/production two-stage structure.

I wrote most of this in one session. The AI handled the YAML scaffolding, the IAM trust policy syntax, the Litestream command-line flags, and the `workflow_run` trigger configuration (which is easy to get wrong — the workflow fires on a *run* of CI, not on a push to main, so that it only triggers when the image actually exists in ECR). I made the architectural decisions: Litestream over EFS, OIDC over access keys, App Runner over Fargate. The AI implemented those decisions accurately and quickly.

The session where I would have spent the most time without AI assistance was the OIDC configuration. The IAM trust policy condition syntax, the OIDC thumbprint, the `configure-aws-credentials` action parameters — these are all things you look up repeatedly because you only provision them once per project. Having them generated correctly on the first pass, with the reasoning auditable in the commit message, is a genuine time saving.

---

## What This Unlocks

With this pipeline in place, every PR merge to main produces a reviewable UAT deployment. Production promotion is one click. The database survives container restarts. The entire infrastructure is defined in code and can be recreated from scratch by running one CloudFormation deploy and one push to main.

For a product I intend to open to other users eventually, this pipeline is the foundation. Adding multi-user support, a proper database, and a billing layer are product decisions. The deployment machinery is already in place.

---

## Takeaway for Consultants

Infrastructure decisions at MVP stage are risk management decisions, not technical excellence decisions. EFS is not wrong — it is the right answer for a different set of constraints. Litestream is the right answer when you want durability without VPC complexity and your write volume is low enough that near-real-time S3 replication is sufficient.

Before choosing any infrastructure component, list the constraints that would make you change it. For Litestream, it is multi-writer. For App Runner, it is VPC-dependent services. If those constraints are not in your roadmap for the next six months, pick the simpler option and move on. Document the decision. Revisit it when the constraint arrives.

OIDC is the one place I would not compromise. Long-lived IAM access keys in GitHub Secrets are a security liability that is entirely avoidable. The OIDC setup adds one CloudFormation resource and one IAM role. It is worth doing on every project.
