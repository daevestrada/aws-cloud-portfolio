# ── IAM Role for Lambda ───────────────────────────────────────────────────────
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-${var.environment}-cost-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_cost_explorer" {
  name = "cost-explorer-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ce:GetCostAndUsage"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# ── CloudWatch Log Group ──────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "lambda_cost" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-cost"
  retention_in_days = 14
}

# ── Lambda Function ───────────────────────────────────────────────────────────
resource "aws_lambda_function" "cost" {
  function_name = "${var.project_name}-${var.environment}-cost"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  architectures = ["arm64"]
  timeout       = 10
  memory_size   = 128
  filename      = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)  # add this line	

  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_cost]
}

# ── API Gateway HTTP API ──────────────────────────────────────────────────────
resource "aws_apigatewayv2_api" "cost" {
  name          = "${var.project_name}-${var.environment}-cost-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["https://${var.project_name == "aws-cloud-portfolio" ? "diegoestrada.cloud" : "*"}"]
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["Content-Type"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_integration" "cost" {
  api_id                 = aws_apigatewayv2_api.cost.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.cost.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "cost" {
  api_id    = aws_apigatewayv2_api.cost.id
  route_key = "GET /api/cost"
  target    = "integrations/${aws_apigatewayv2_integration.cost.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.cost.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.cost.execution_arn}/*/*"
}

