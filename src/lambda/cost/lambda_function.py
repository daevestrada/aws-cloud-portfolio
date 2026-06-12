import json
import logging
import os
from datetime import date, timedelta

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# ── Logging setup ─────────────────────────────────────────────────────────────
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "https://diegoestrada.cloud")

def get_cost_data(ce_client):
    today = date.today()
    month_start = today.replace(day=1)
    yesterday = today - timedelta(days=1)

    response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": month_start.isoformat(),
            "End": today.isoformat(),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    daily_costs = []
    for result in response["ResultsByTime"]:
        for group in result["Groups"]:
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amount > 0.0001:
                daily_costs.append({
                    "date": result["TimePeriod"]["Start"],
                    "service": group["Keys"][0],
                    "amount": round(amount, 4),
                })

    mtd_response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": month_start.isoformat(),
            "End": today.isoformat(),
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )

    mtd_total = float(
        mtd_response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
    )

    return {
        "mtd_total": round(mtd_total, 4),
        "daily_costs": daily_costs,
        "period_start": month_start.isoformat(),
        "period_end": today.isoformat(),
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
        logger.info(json.dumps({"message": "Cost data retrieved", "mtd_total": data["mtd_total"]}))
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
