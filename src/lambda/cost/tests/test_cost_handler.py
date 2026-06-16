import json
import unittest
from unittest.mock import MagicMock, patch

from lambda_function import lambda_handler


def make_event(method="GET"):
    return {"requestContext": {"http": {"method": method}}}


def mtd_breakdown_response(groups):
    """groups: list of (service, record_type, amount_str) tuples"""
    return {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-06-01"},
                "Groups": [
                    {
                        "Keys": [service, record_type],
                        "Metrics": {"UnblendedCost": {"Amount": amount}},
                    }
                    for service, record_type, amount in groups
                ],
            }
        ]
    }


def credit_status_response(total_amount):
    return {"ResultsByTime": [{"Total": {"UnblendedCost": {"Amount": total_amount}}}]}


class TestCostHandler(unittest.TestCase):

    @patch("lambda_function.boto3.client")
    def test_happy_path_returns_200(self, mock_boto):
        ce = MagicMock()
        mock_boto.return_value = ce
        ce.get_cost_and_usage.side_effect = [
            mtd_breakdown_response([
                ("Amazon Route 53", "Usage", "0.51"),
                ("Amazon Route 53", "Credit", "-0.51"),
            ]),
            credit_status_response("-0.51"),
        ]

        response = lambda_handler(make_event(), {})
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])

        self.assertIn("services", body)
        self.assertIn("credits_remaining", body)
        self.assertEqual(body["services"][0]["service"], "Amazon Route 53")
        self.assertEqual(body["services"][0]["gross_cost"], 0.51)
        self.assertEqual(body["credits_applied_mtd"], -0.51)
        self.assertEqual(body["net_total_mtd"], 0.0)

    @patch("lambda_function.boto3.client")
    def test_access_denied_returns_403(self, mock_boto):
        from botocore.exceptions import ClientError
        ce = MagicMock()
        mock_boto.return_value = ce
        ce.get_cost_and_usage.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
            "GetCostAndUsage",
        )

        response = lambda_handler(make_event(), {})
        self.assertEqual(response["statusCode"], 403)

    @patch("lambda_function.boto3.client")
    def test_unhandled_exception_returns_500(self, mock_boto):
        ce = MagicMock()
        mock_boto.return_value = ce
        ce.get_cost_and_usage.side_effect = Exception("Unexpected error")

        response = lambda_handler(make_event(), {})
        self.assertEqual(response["statusCode"], 500)

    @patch("lambda_function.boto3.client")
    def test_negligible_amounts_filtered_out(self, mock_boto):
        ce = MagicMock()
        mock_boto.return_value = ce
        ce.get_cost_and_usage.side_effect = [
            mtd_breakdown_response([
                ("Amazon Simple Storage Service", "Usage", "1e-10"),
                ("Amazon Route 53", "Usage", "0.51"),
                ("Amazon Route 53", "Credit", "-0.51"),
            ]),
            credit_status_response("-0.51"),
        ]

        response = lambda_handler(make_event(), {})
        body = json.loads(response["body"])
        services = [row["service"] for row in body["services"]]
        self.assertNotIn("Amazon Simple Storage Service", services)
        self.assertIn("Amazon Route 53", services)

    @patch("lambda_function.boto3.client")
    def test_credit_netting_does_not_hide_gross_cost(self, mock_boto):
        """
        Regression test for the Session 08 bug: a Credit record type that
        exactly offsets a Usage record type must NOT make the service
        disappear from the gross 'services' breakdown, even though
        net_total_mtd correctly nets to ~0.
        """
        ce = MagicMock()
        mock_boto.return_value = ce
        ce.get_cost_and_usage.side_effect = [
            mtd_breakdown_response([
                ("Amazon Route 53", "Usage", "0.5135433654"),
                ("Amazon Route 53", "Credit", "-0.5135433657"),
            ]),
            credit_status_response("-0.5135433657"),
        ]

        response = lambda_handler(make_event(), {})
        body = json.loads(response["body"])

        self.assertEqual(len(body["services"]), 1)
        self.assertEqual(body["services"][0]["service"], "Amazon Route 53")
        self.assertAlmostEqual(body["services"][0]["gross_cost"], 0.5135, places=4)
        self.assertAlmostEqual(body["net_total_mtd"], 0.0, places=3)

    @patch("lambda_function.boto3.client")
    def test_credits_remaining_subtracts_consumption_since_baseline(self, mock_boto):
        ce = MagicMock()
        mock_boto.return_value = ce
        ce.get_cost_and_usage.side_effect = [
            mtd_breakdown_response([
                ("Amazon Route 53", "Usage", "0.50"),
                ("Amazon Route 53", "Credit", "-0.50"),
            ]),
            credit_status_response("-2.50"),  # cumulative consumption since baseline
        ]

        with patch("lambda_function.CREDIT_BASELINE_REMAINING", 138.34):
            response = lambda_handler(make_event(), {})

        body = json.loads(response["body"])
        self.assertAlmostEqual(body["credits_remaining"], 135.84, places=2)

    def test_options_request_returns_200(self):
        response = lambda_handler(make_event("OPTIONS"), {})
        self.assertEqual(response["statusCode"], 200)


if __name__ == "__main__":
    unittest.main()
