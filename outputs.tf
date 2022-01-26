output "lambda" {
  value = {
    arn  = aws_lambda_function.cloudwatch_slack_notifier.arn
    name = aws_lambda_function.cloudwatch_slack_notifier.function_name
  }
}
