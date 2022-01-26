locals {
  lambda_path = "cloudwatch_slack_notifier.py"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "aws_iam_role" "iam_for_lambda" {
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_cloudwatch_log_group" "log_group" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.retention_in_days
}

data "aws_iam_policy_document" "lambda" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["*"]
    effect    = "Allow"
  }

  statement {
    actions = [
      "ssm:GetParameter*",
    ]

    resources = ["arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.ssm_slack_webhook}"]
    effect    = "Allow"
  }

  statement {
    actions = [
      "kms:Decrypt",
    ]

    resources = ["arn:aws:kms:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:key/aws/ssm"]
    effect    = "Allow"
  }
}

resource "aws_iam_policy" "lambda" {
  path        = "/"
  description = "IAM policy for logging from a lambda and CloudWatch metric PUT"

  policy = data.aws_iam_policy_document.lambda.json
}

resource "aws_iam_role_policy_attachment" "lambda" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda.arn
}

data "archive_file" "init" {
  type        = "zip"
  source_file = "${path.module}/${local.lambda_path}"
  output_path = "${path.module}/${local.lambda_path}.zip"
}

resource "aws_lambda_function" "cloudwatch_slack_notifier" {
  filename      = "${path.module}/${local.lambda_path}.zip"
  function_name = var.lambda_function_name
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "cloudwatch_slack_notifier.lambda_handler"
  timeout       = var.lambda_timeout

  # The filebase64sha256() function is available in Terraform 0.11.12 and later
  # For Terraform 0.11.11 and earlier, use the base64sha256() function and the file() function:
  # source_code_hash = "${base64sha256(file("lambda_function_payload.zip"))}"
  source_code_hash = data.archive_file.init.output_base64sha256

  runtime = "python3.8"

  environment {
    variables = {
      SLACK_CHANNEL     = var.slack_channel
      SSM_SLACK_WEBHOOK = var.ssm_slack_webhook
      ENVIRONMENT       = var.environment
    }
  }
}
