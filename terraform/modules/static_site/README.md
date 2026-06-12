# static_site module

Provisions the static frontend infrastructure and CloudFront routing
for the AWS Cloud Portfolio.

## What it creates

- Private S3 bucket (versioned, encrypted, Block Public Access ON)
- CloudFront Origin Access Control (OAC) — SigV4 signing
- S3 bucket policy allowing only CloudFront via OAC
- CloudFront distribution with two origins:
  - **S3** — serves the static frontend (`index.html`, `app.js`)
  - **API Gateway** — serves `/api/*` requests
- Two cache behaviors:
  - **Default (`/*`)** — S3 origin, caching enabled (1h TTL)
  - **Ordered (`/api/*`)** — API Gateway origin, `CachingDisabled` managed policy
- CloudFront aliases for both the root domain and `www` subdomain

## Why a separate cache behavior for `/api/*`

CloudFront's default behavior caches responses. Without an override,
`/api/cost` would return stale cost data to every visitor for up to an hour.
The `/api/*` ordered behavior uses the AWS-managed `CachingDisabled` policy
(`4135ea2d-6df8-44a3-9df3-4b5a84be39ad`) so every request is forwarded live
to API Gateway → Lambda → Cost Explorer.

The `AllViewerExceptHostHeader` origin request policy
(`b689b0a8-53d0-40ab-baf2-68738e2966ac`) forwards all viewer headers except
`Host`, which API Gateway requires to route correctly.

## Inputs

| Name | Description | Type |
|---|---|---|
| `project_name` | Project name for resource naming/tagging | string |
| `environment` | Deployment environment (prod, staging) | string |
| `domain_name` | Primary domain (e.g. `diegoestrada.cloud`) | string |
| `acm_certificate_arn` | ACM cert ARN in `us-east-1` (CloudFront requirement) | string |
| `api_gateway_url` | API Gateway invoke URL — hostname extracted via `replace()` | string |

## Outputs

| Name | Description |
|---|---|
| `cloudfront_domain_name` | CloudFront distribution domain (`*.cloudfront.net`) |
| `cloudfront_distribution_id` | Used for cache invalidations |
| `s3_bucket_name` | Target for frontend uploads |

## Why ACM must be in us-east-1

CloudFront is a global service hardcoded to read ACM certificates only
from `us-east-1`, regardless of where other resources live.

## Why an A alias record instead of CNAME

Root domains cannot use CNAME records (RFC restriction). Route 53's alias
extension on an A record resolves dynamically to CloudFront's edge IPs,
which change over time — no fixed IP required.

## DNS (managed outside Terraform)

Route 53 records for `diegoestrada.cloud` and `www.diegoestrada.cloud`
were created manually via AWS CLI, both as A alias records pointing to
the CloudFront distribution (hosted zone ID `Z2FDTNDATAQYW2`, fixed for
all CloudFront distributions).

