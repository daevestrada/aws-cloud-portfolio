import json
import unittest
from unittest.mock import MagicMock, patch

from lambda_function import lambda_handler


def make_event(method="GET"):
    return {
        "requestContext": {
            "http": {"method": method}
        }
    }


class TestCostHandler(unittest.TestCase):

    @patch("lambda_function.boto3.client")
    def test_happy_path_returns_200(self, mock_boto):
        ce = MagicMock()
        mock_boto.return_value = ce

        ce.get_cost_and_usage.side_effect = [
            {
                "ResultsByTime": [
                    {
                        "TimePeriod": {"Start": "2026-06-01"},
                        "Groups": [
                            {
                                "Keys": ["Amazon S3"],
                                "Metrics": {"UnblendedCost": {"Amount": "0.50"}},
                            }
                        ],
                    }
                ]
            },
            {
                "ResultsByTime": [
                    {
                        "Total": {"UnblendedCost": {"Amount": "0.50"}},
                        "Groups": [],
                    }
                ]
            },
        ]

        response = lambda_handler(make_event(), {})
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("mtd_total", body)
        self.assertIn("daily_costs", body)
        self.assertEqual(body["mtd_total"], 0.5)

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

    def test_options_request_returns_200(self):
        response = lambda_handler(make_event("OPTIONS"), {})
        self.assertEqual(response["statusCode"], 200)


if __name__ == "__main__":
    unittest.main()
