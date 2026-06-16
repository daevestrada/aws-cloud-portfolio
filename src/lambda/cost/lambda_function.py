import json
import logging
import os
from datetime import date, timedelta

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# ── Logging setup ─────────────────────────────────────────────────────────────
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
# force=True is required: the Lambda runtime pre-attaches a handler to the
# root logger before this module runs, which makes basicConfig() a no-op
# without it — this is why LOG_LEVEL was being silently ignored.
logging.basicConfig(level=log_level, force=True)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "https://diegoestrada.cloud")
COST_THRESHOLD = 0.0001  # filters float-noise allocations (e.g. 1e-9 S3/CloudFront splits)

# AWS does not expose a "credits remaining" API. This is calibrated from a
# manual reading of the Billing Console's Credits page, then tracked forward
# via Cost Explorer's RECORD_TYPE=Credit drawdown. Recalibrate (update these
# three env vars) whenever a new credit is earned — e.g. an "Explore AWS"
# bonus — since the total pool can grow, not just shrink.
# See docs/adr/0004-credit-balance-calibration.md
CREDIT_BASELINE_REMAINING = float(os.environ.get("CREDIT_BASELINE_REMAINING", "138.34"))
CREDIT_BASELINE_DATE = date.fromisoformat(os.environ.get("CREDIT_BASELINE_DATE", "2026-06-16"))
CREDIT_EXPIRATION_DATE = date.fromisoformat(os.environ.get("CREDIT_EXPIRATION_DATE", "2026-09-14"))


def _query_end(today):
    """CE's TimePeriod.End is EXCLUSIVE — add a day so 'today' is included."""
    return today + timedelta(days=1)


def get_mtd_breakdown(ce_client, month_start, today):
    """
    One Cost Explorer call grouped by SERVICE + RECORD_TYPE.
    Separates gross usage cost per service from Credit/Tax/Refund record
    types, so promotional credits stop silently netting real charges to zero.
    """
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": month_start.isoformat(),
            "End": _query_end(today).isoformat(),
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"},
            {"Type": "DIMENSION", "Key": "RECORD_TYPE"},
        ],
    )

    gross_by_service = {}
    credits_applied = 0.0
    tax_total = 0.0
    refund_total = 0.0

    for result in response["ResultsByTime"]:
        for group in result["Groups"]:
            service, record_type = group["Keys"]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])

            if record_type == "Usage":
                gross_by_service[service] = gross_by_service.get(service, 0.0) + amount
            elif record_type == "Credit":
                credits_applied += amount  # negative
            elif record_type == "Tax":
                tax_total += amount
            elif record_type == "Refund":
                refund_total += amount

    services = [
        {"service": service, "gross_cost": round(amount, 4)}
        for service, amount in sorted(gross_by_service.items(), key=lambda kv: -kv[1])
        if amount > COST_THRESHOLD
    ]

    gross_total = sum(s["gross_cost"] for s in services)
    net_total = gross_total + credits_applied + tax_total + refund_total

    return {
        "services": services,
        "gross_total_mtd": round(gross_total, 4),
        "credits_applied_mtd": round(credits_applied, 4),
        "tax_mtd": round(tax_total, 4),
        "net_total_mtd": round(net_total, 4),
    }


def get_credit_status(ce_client, today):
    """
    Tracks credit drawdown since CREDIT_BASELINE_DATE to derive a current
    remaining balance, since AWS has no direct "remaining credits" API.
    """
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": CREDIT_BASELINE_DATE.isoformat(),
            "End": _query_end(today).isoformat(),
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        Filter={"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Credit"]}},
    )

    consumed_since_baseline = sum(
        abs(float(result["Total"]["UnblendedCost"]["Amount"]))
        for result in response["ResultsByTime"]
    )

    return {
        "credits_remaining": round(CREDIT_BASELINE_REMAINING - consumed_since_baseline, 2),
        "credit_expiration_date": CREDIT_EXPIRATION_DATE.isoformat(),
        "days_until_expiration": (CREDIT_EXPIRATION_DATE - today).days,
        "credit_baseline_date": CREDIT_BASELINE_DATE.isoformat(),
    }


def get_cost_data(ce_client):
    today = date.today()
    month_start = today.replace(day=1)

    return {
        "period_start": month_start.isoformat(),
        "period_end": today.isoformat(),
        **get_mtd_breakdown(ce_client, month_start, today),
        **get_credit_status(ce_client, today),
    }


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": CORS_ORIGIN,
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    logger.info(json.dumps({"message": "Request received", "event": event}))

    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return build_response(200, {})

    try:
        ce_client = boto3.client("ce", region_name="us-east-1")
        data = get_cost_data(ce_client)
        logger.info(json.dumps({
            "message": "Cost data retrieved",
            "net_total_mtd": data["net_total_mtd"],
            "credits_remaining": data["credits_remaining"],
        }))
        return build_response(200, data)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(json.dumps({"message": "AWS ClientError", "error_code": error_code}))
        if error_code == "AccessDeniedException":
            return build_response(403, {"error": "Access denied to Cost Explorer"})
        return build_response(500, {"error": "AWS service error"})

    except BotoCoreError as e:
        logger.error(json.dumps({"message": "BotoCoreError", "error": str(e)}))
        return build_response(500, {"error": "AWS connection error"})

    except Exception as e:
        logger.error(json.dumps({"message": "Unhandled exception", "error": str(e)}))
        return build_response(500, {"error": "Internal server error"})
