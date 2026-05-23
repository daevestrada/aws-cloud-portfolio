#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
BUCKET_NAME="tfstate-${ACCOUNT_ID}"
TABLE_NAME="tfstate-locks"

echo "Account ID : ${ACCOUNT_ID}"
echo "Region     : ${REGION}"
echo "Bucket     : ${BUCKET_NAME}"
echo "Table      : ${TABLE_NAME}"
echo ""

# ── S3 bucket for Terraform state ────────────────────────────────────────────
echo "Creating S3 bucket..."
aws s3api create-bucket \
  --bucket "${BUCKET_NAME}" \
  --region "${REGION}"

aws s3api put-bucket-versioning \
  --bucket "${BUCKET_NAME}" \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket "${BUCKET_NAME}" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

aws s3api put-public-access-block \
  --bucket "${BUCKET_NAME}" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "S3 bucket ready."
echo ""

# ── DynamoDB table for state locking ─────────────────────────────────────────
echo "Creating DynamoDB table..."
aws dynamodb create-table \
  --table-name "${TABLE_NAME}" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "${REGION}"

echo "DynamoDB table ready."
echo ""

echo "Bootstrap complete."
echo "Bucket : ${BUCKET_NAME}"
echo "Table  : ${TABLE_NAME}"
echo "Add these to terraform/envs/prod/backend.tf"
