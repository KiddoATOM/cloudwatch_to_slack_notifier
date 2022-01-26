variable "lambda_function_name" {
  type        = string
  description = "Lambda function name"
  default     = "slack_notifier"
}

variable "lambda_timeout" {
  type        = string
  description = "Lambda function name"
  default     = "15"
}

variable "retention_in_days" {
  type        = string
  description = "Lambda function logs retention in days."
  default     = "30"
}

variable "ssm_slack_webhook" {
  type        = string
  description = "SSM parameter name to obtain slack webhook."
  default     = "/slack_notifier/webhook"
}

variable "slack_channel" {
  type        = string
  description = "Slack channel."
  default     = "monitoring"
}

variable "environment" {
  type        = string
  description = "Environment name."
}
