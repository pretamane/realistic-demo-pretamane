output "api_gateway_url" {
  value = aws_api_gateway_stage.main.invoke_url
  description = "The URL of the API Gateway"
}

output "api_gateway_id" {
  value = aws_api_gateway_rest_api.main.id
  description = "The ID of the API Gateway"
}

output "lambda_function_arn" {
  value = aws_lambda_function.api_proxy.arn
  description = "The ARN of the Lambda function"
}
