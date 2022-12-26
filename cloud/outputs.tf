output "gcp_workload_identity_provider" {
  description = "The full identifier of the GitHub workload identity pool provider"
  value = module.gcp_github_auth.workload_identity_provider
}

output "gcp_service_account" {
  description = "The email of the Google Cloud service account used for running tests"
  value = module.gcp_github_auth.service_account_emails["testing"]
}

output "aws_role" {
  description = "The ARN of the AWS role used for running tests"
  value = module.aws_github_auth.iam_role_arns["testing"]
}

output "gcs_test_bucket_url" {
  description = "The Gogle Cloud Storage test data bucket URL"
  value = module.gcs_test_data_bucket.url
}

output "aws_s3_test_bucket_url" {
  description = "The AWS S3 test data bucket URL"
  value = "s3://${module.s3_test_data_bucket.name}"
}
